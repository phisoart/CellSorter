"""
CellSorter Extractor

Square crop calculation and .cxprotocol file generation for CosmoSort hardware.
Handles coordinate transformation and protocol file export.
"""

from typing import Optional, List, Tuple, Dict, Any, NamedTuple
from dataclasses import dataclass
from pathlib import Path
import configparser
import time
import numpy as np
from PySide6.QtCore import QObject, Signal

from utils.error_handler import error_handler
from utils.logging_config import LoggerMixin
from utils.exceptions import ExportError


class BoundingBox(NamedTuple):
    """Bounding box coordinates."""
    min_x: float
    min_y: float
    max_x: float
    max_y: float


@dataclass
class CropRegion:
    """Square crop region data."""
    center_x: float
    center_y: float
    size: float
    min_x: float = 0.0
    min_y: float = 0.0
    max_x: float = 0.0
    max_y: float = 0.0
    
    def __post_init__(self):
        """Calculate min/max coordinates from center and size."""
        half_size = self.size / 2
        self.min_x = self.center_x - half_size
        self.min_y = self.center_y - half_size
        self.max_x = self.center_x + half_size
        self.max_y = self.center_y + half_size


@dataclass
class ExtractionPoint:
    """Single extraction point for protocol file."""
    id: str
    label: str
    color: str
    well_position: str
    crop_region: CropRegion
    metadata: Dict[str, Any]


class Extractor(QObject, LoggerMixin):
    """
    Extractor for generating square crop regions and .cxprotocol files.
    
    Features:
    - Square crop calculation from bounding boxes
    - Stage coordinate transformation
    - .cxprotocol file generation for CosmoSort
    - Validation and quality control
    """
    
    # Signals
    extraction_completed = Signal(str)  # file_path
    extraction_failed = Signal(str)  # error_message
    progress_updated = Signal(int)  # percentage
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        
        # Configuration
        self.min_crop_size_pixels = 10  # Minimum crop size
        self.max_crop_size_pixels = 1000  # Maximum crop size
        self.crop_padding_factor = 1.2  # Add 20% padding around bounding box
        
        self.log_info("Extractor initialized")
    
    @error_handler("Calculating square crop")
    def calculate_square_crop(self, bounding_box: BoundingBox, 
                            image_bounds: Optional[Tuple[int, int]] = None) -> Optional[CropRegion]:
        """
        Calculate square crop region from bounding box.
        
        Args:
            bounding_box: Input bounding box coordinates
            image_bounds: Optional image bounds (width, height) for boundary checking
        
        Returns:
            CropRegion object or None if invalid
        """
        # Calculate bounding box dimensions
        width = bounding_box.max_x - bounding_box.min_x
        height = bounding_box.max_y - bounding_box.min_y
        
        # Validate bounding box
        if width <= 0 or height <= 0:
            self.log_warning(f"Invalid bounding box dimensions: {width}x{height}")
            return None
        
        # Calculate square size (use shorter dimension with padding)
        base_size = min(width, height)
        crop_size = base_size * self.crop_padding_factor
        
        # Ensure minimum crop size
        crop_size = max(crop_size, self.min_crop_size_pixels)
        
        # Ensure maximum crop size
        crop_size = min(crop_size, self.max_crop_size_pixels)
        
        # Calculate center point
        center_x = (bounding_box.min_x + bounding_box.max_x) / 2
        center_y = (bounding_box.min_y + bounding_box.max_y) / 2
        
        # Create crop region
        crop_region = CropRegion(
            center_x=center_x,
            center_y=center_y,
            size=crop_size
        )
        
        # Check image boundaries if provided
        if image_bounds:
            img_width, img_height = image_bounds
            
            # Adjust crop region to stay within image bounds
            if crop_region.min_x < 0:
                offset = -crop_region.min_x
                crop_region.center_x += offset
                crop_region.__post_init__()  # Recalculate bounds
            
            if crop_region.min_y < 0:
                offset = -crop_region.min_y
                crop_region.center_y += offset
                crop_region.__post_init__()
            
            if crop_region.max_x > img_width:
                offset = crop_region.max_x - img_width
                crop_region.center_x -= offset
                crop_region.__post_init__()
            
            if crop_region.max_y > img_height:
                offset = crop_region.max_y - img_height
                crop_region.center_y -= offset
                crop_region.__post_init__()
            
            # Final validation - ensure crop is still within bounds
            if (crop_region.min_x < 0 or crop_region.min_y < 0 or 
                crop_region.max_x > img_width or crop_region.max_y > img_height):
                
                # Reduce crop size to fit
                max_size_x = min(center_x * 2, (img_width - center_x) * 2)
                max_size_y = min(center_y * 2, (img_height - center_y) * 2)
                adjusted_size = min(max_size_x, max_size_y, crop_size)
                
                if adjusted_size < self.min_crop_size_pixels:
                    self.log_warning(f"Cannot create valid crop region within image bounds")
                    return None
                
                crop_region.size = adjusted_size
                crop_region.__post_init__()
        
        return crop_region
    
    def create_extraction_points(self, selections_data: List[Dict[str, Any]], 
                               bounding_boxes: List[BoundingBox],
                               coordinate_transformer, 
                               image_bounds: Optional[Tuple[int, int]] = None) -> List[ExtractionPoint]:
        """
        Create extraction points from selections and bounding boxes.
        
        Args:
            selections_data: List of selection data dictionaries
            bounding_boxes: List of bounding box coordinates (in pixels)
            coordinate_transformer: CoordinateTransformer instance
            image_bounds: Optional image bounds for boundary checking
        
        Returns:
            List of ExtractionPoint objects
        """
        extraction_points = []
        
        for selection_data in selections_data:
            cell_indices = selection_data.get('cell_indices', [])
            
            if not cell_indices:
                continue
            
            # Process each cell in the selection
            for cell_index in cell_indices:
                if cell_index >= len(bounding_boxes):
                    self.log_warning(f"Cell index {cell_index} out of range")
                    continue
                
                bbox = bounding_boxes[cell_index]
                
                # Calculate crop region in pixel coordinates
                crop_region_pixels = self.calculate_square_crop(bbox, image_bounds)
                if not crop_region_pixels:
                    continue
                
                # Transform to stage coordinates if transformer is available
                if coordinate_transformer and coordinate_transformer.is_calibrated:
                    # Transform crop corners to stage coordinates
                    min_result = coordinate_transformer.pixel_to_stage(
                        int(crop_region_pixels.min_x), int(crop_region_pixels.min_y)
                    )
                    max_result = coordinate_transformer.pixel_to_stage(
                        int(crop_region_pixels.max_x), int(crop_region_pixels.max_y)
                    )
                    
                    if min_result and max_result:
                        # Create crop region in stage coordinates
                        crop_region_stage = CropRegion(
                            center_x=(min_result.stage_x + max_result.stage_x) / 2,
                            center_y=(min_result.stage_y + max_result.stage_y) / 2,
                            size=max(abs(max_result.stage_x - min_result.stage_x),
                                   abs(max_result.stage_y - min_result.stage_y))
                        )
                        crop_region = crop_region_stage
                    else:
                        self.log_warning(f"Failed to transform coordinates for cell {cell_index}")
                        continue
                else:
                    # Use pixel coordinates if no transformation available
                    crop_region = crop_region_pixels
                
                # Create extraction point
                point = ExtractionPoint(
                    id=f"{selection_data['id']}_{cell_index}",
                    label=f"{selection_data.get('label', 'Selection')}_{cell_index}",
                    color=selection_data.get('color', '#FF0000'),
                    well_position=selection_data.get('well_position', ''),
                    crop_region=crop_region,
                    metadata={
                        'selection_id': selection_data['id'],
                        'cell_index': cell_index,
                        'original_bbox': bbox,
                        'selection_metadata': selection_data.get('metadata', {})
                    }
                )
                
                extraction_points.append(point)
        
        self.log_info(f"Created {len(extraction_points)} extraction points")
        return extraction_points
    
    @error_handler("Generating protocol file")
    def generate_protocol_file(self, extraction_points: List[ExtractionPoint], 
                             output_path: str, image_info: Dict[str, Any]) -> bool:
        """
        Generate .cxprotocol file for CosmoSort hardware.
        
        Args:
            extraction_points: List of extraction points
            output_path: Output file path
            image_info: Image metadata dictionary
        
        Returns:
            True if successful, False otherwise
        """
        if not extraction_points:
            self.log_error("No extraction points to export")
            return False
        
        try:
            # Create ConfigParser for INI format
            config = configparser.ConfigParser()
            config.optionxform = str  # Preserve case sensitivity
            
            # IMAGE section
            config.add_section('IMAGE')
            config.set('IMAGE', 'FILE', Path(image_info.get('file_path', 'unknown')).stem)
            config.set('IMAGE', 'WIDTH', str(image_info.get('shape', [0, 0])[1]))
            config.set('IMAGE', 'HEIGHT', str(image_info.get('shape', [0, 0])[0]))
            
            # Determine format from file extension
            file_path = image_info.get('file_path', '')
            if file_path:
                ext = Path(file_path).suffix.lower()
                format_map = {'.tiff': 'TIF', '.tif': 'TIF', '.jpg': 'JPG', 
                            '.jpeg': 'JPG', '.png': 'PNG'}
                img_format = format_map.get(ext, 'TIF')
            else:
                img_format = 'TIF'
            
            config.set('IMAGE', 'FORMAT', img_format)
            
            # IMAGING_LAYOUT section
            config.add_section('IMAGING_LAYOUT')
            config.set('IMAGING_LAYOUT', 'PositionOnly', '1')
            config.set('IMAGING_LAYOUT', 'AfterBefore', '01')
            config.set('IMAGING_LAYOUT', 'Points', str(len(extraction_points)))
            
            # Add extraction points
            for i, point in enumerate(extraction_points, 1):
                # Format: "min_x; min_y; max_x; max_y; color; well; label"
                point_data = f"{point.crop_region.min_x:.4f}; {point.crop_region.min_y:.4f}; " \
                           f"{point.crop_region.max_x:.4f}; {point.crop_region.max_y:.4f}; " \
                           f"{point.color.lstrip('#').lower()}; {point.well_position}; {point.label};"
                
                config.set('IMAGING_LAYOUT', f'P_{i}', point_data)
            
            # Write to file
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                config.write(f, space_around_delimiters=True)
            
            # Create backup
            backup_path = output_file.with_suffix(f'.backup_{int(time.time())}.cxprotocol')
            with open(backup_path, 'w', encoding='utf-8') as f:
                config.write(f, space_around_delimiters=True)
            
            self.log_info(f"Generated protocol file: {output_path} ({len(extraction_points)} points)")
            self.log_info(f"Backup created: {backup_path}")
            
            # Emit signal
            self.extraction_completed.emit(str(output_path))
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to generate protocol file: {e}"
            self.log_error(error_msg)
            self.extraction_failed.emit(error_msg)
            return False
    
    def validate_protocol_file(self, file_path: str) -> Dict[str, Any]:
        """
        Validate a generated protocol file.
        
        Args:
            file_path: Path to protocol file
        
        Returns:
            Validation result dictionary
        """
        validation_result = {
            'is_valid': False,
            'errors': [],
            'warnings': [],
            'point_count': 0,
            'file_size_bytes': 0
        }
        
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                validation_result['errors'].append("File does not exist")
                return validation_result
            
            validation_result['file_size_bytes'] = file_path.stat().st_size
            
            # Parse the file
            config = configparser.ConfigParser()
            config.read(file_path, encoding='utf-8')
            
            # Check required sections
            required_sections = ['IMAGE', 'IMAGING_LAYOUT']
            for section in required_sections:
                if not config.has_section(section):
                    validation_result['errors'].append(f"Missing required section: {section}")
            
            if validation_result['errors']:
                return validation_result
            
            # Validate IMAGE section
            image_section = config['IMAGE']
            required_image_keys = ['FILE', 'WIDTH', 'HEIGHT', 'FORMAT']
            for key in required_image_keys:
                if key not in image_section:
                    validation_result['errors'].append(f"Missing IMAGE key: {key}")
            
            # Validate IMAGING_LAYOUT section
            layout_section = config['IMAGING_LAYOUT']
            if 'Points' not in layout_section:
                validation_result['errors'].append("Missing Points in IMAGING_LAYOUT")
                return validation_result
            
            try:
                point_count = int(layout_section['Points'])
                validation_result['point_count'] = point_count
            except ValueError:
                validation_result['errors'].append("Invalid Points value")
                return validation_result
            
            # Validate point entries
            for i in range(1, point_count + 1):
                point_key = f'P_{i}'
                if point_key not in layout_section:
                    validation_result['errors'].append(f"Missing point entry: {point_key}")
                    continue
                
                # Parse point data
                point_data = layout_section[point_key]
                parts = [p.strip() for p in point_data.split(';')]
                
                if len(parts) < 6:
                    validation_result['warnings'].append(f"Point {i} has incomplete data")
                    continue
                
                # Validate coordinate format
                try:
                    float(parts[0])  # min_x
                    float(parts[1])  # min_y
                    float(parts[2])  # max_x
                    float(parts[3])  # max_y
                except ValueError:
                    validation_result['errors'].append(f"Point {i} has invalid coordinates")
            
            # Final validation
            validation_result['is_valid'] = len(validation_result['errors']) == 0
            
            if validation_result['is_valid']:
                self.log_info(f"Protocol file validation passed: {file_path}")
            else:
                self.log_warning(f"Protocol file validation failed: {validation_result['errors']}")
            
        except Exception as e:
            validation_result['errors'].append(f"Validation error: {e}")
            self.log_error(f"Protocol file validation error: {e}")
        
        return validation_result
    
    def get_extraction_statistics(self, extraction_points: List[ExtractionPoint]) -> Dict[str, Any]:
        """
        Get statistics about extraction points.
        
        Args:
            extraction_points: List of extraction points
        
        Returns:
            Statistics dictionary
        """
        if not extraction_points:
            return {
                'total_points': 0,
                'unique_wells': 0,
                'unique_colors': 0,
                'average_crop_size': 0.0,
                'crop_size_range': (0.0, 0.0)
            }
        
        crop_sizes = [point.crop_region.size for point in extraction_points]
        wells = set(point.well_position for point in extraction_points if point.well_position)
        colors = set(point.color for point in extraction_points)
        
        stats = {
            'total_points': len(extraction_points),
            'unique_wells': len(wells),
            'unique_colors': len(colors),
            'average_crop_size': np.mean(crop_sizes),
            'crop_size_range': (min(crop_sizes), max(crop_sizes)),
            'crop_size_std': np.std(crop_sizes),
            'wells_used': sorted(list(wells)),
            'colors_used': sorted(list(colors))
        }
        
        return stats