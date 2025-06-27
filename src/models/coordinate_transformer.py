"""
CellSorter Coordinate Transformer

Two-point calibration system for pixel-to-stage coordinate transformation
using affine transformation matrices.
"""

from typing import Optional, List, Tuple, Dict, Any, NamedTuple
from dataclasses import dataclass
import numpy as np
from PySide6.QtCore import QObject, Signal

from config.settings import COORDINATE_ACCURACY_MICROMETERS
from utils.exceptions import CalibrationError, TransformationError
from utils.error_handler import error_handler
from utils.logging_config import LoggerMixin


class CalibrationPoint(NamedTuple):
    """Calibration point with pixel and stage coordinates."""
    pixel_x: int
    pixel_y: int
    stage_x: float  # micrometers
    stage_y: float  # micrometers
    label: str = ""


@dataclass
class TransformationResult:
    """Result of coordinate transformation."""
    stage_x: float
    stage_y: float
    confidence: float  # 0.0 to 1.0
    error_estimate_um: float  # estimated error in micrometers


class CoordinateTransformer(QObject, LoggerMixin):
    """
    Two-point calibration system for pixel-to-stage coordinate transformation.
    
    Features:
    - Two-point calibration with affine transformation
    - Real-time coordinate transformation
    - Accuracy estimation and validation
    - Error checking and quality metrics
    """
    
    # Signals
    calibration_updated = Signal(bool)  # is_valid
    transformation_ready = Signal()
    calibration_cleared = Signal()
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        
        # Calibration data
        self.calibration_points: List[CalibrationPoint] = []
        self.transform_matrix: Optional[np.ndarray] = None
        self.inverse_transform_matrix: Optional[np.ndarray] = None
        
        # Quality metrics
        self.calibration_quality: Dict[str, float] = {}
        self._is_calibrated = False
        
        # Configuration
        self.min_distance_pixels = 50  # Minimum distance between calibration points
        self.max_error_micrometers = COORDINATE_ACCURACY_MICROMETERS * 10  # 1.0 um max error
        
        self.log_info("Coordinate transformer initialized")
    
    @error_handler("Adding calibration point")
    def add_calibration_point(self, pixel_x: int, pixel_y: int, 
                            stage_x: float, stage_y: float, 
                            label: str = "") -> bool:
        """
        Add a calibration point.
        
        Args:
            pixel_x: Pixel X coordinate
            pixel_y: Pixel Y coordinate
            stage_x: Stage X coordinate in micrometers
            stage_y: Stage Y coordinate in micrometers
            label: Optional label for the point
        
        Returns:
            True if point added successfully, False otherwise
        """
        # Validate input
        if not self._validate_coordinates(pixel_x, pixel_y, stage_x, stage_y):
            return False
        
        # Check if we already have maximum points (2 for linear transformation)
        if len(self.calibration_points) >= 2:
            self.log_warning("Maximum calibration points reached, replacing oldest")
            self.calibration_points.pop(0)
        
        # Create calibration point
        point = CalibrationPoint(pixel_x, pixel_y, stage_x, stage_y, label)
        
        # Check minimum distance from existing points
        for existing_point in self.calibration_points:
            distance = np.sqrt((pixel_x - existing_point.pixel_x)**2 + 
                             (pixel_y - existing_point.pixel_y)**2)
            if distance < self.min_distance_pixels:
                self.log_warning(f"Calibration point too close to existing point (distance: {distance:.1f} pixels)")
                return False
        
        # Add point
        self.calibration_points.append(point)
        
        # Recalculate transformation if we have enough points
        if len(self.calibration_points) == 2:
            success = self._calculate_transformation()
            if success:
                self.transformation_ready.emit()
        
        self.calibration_updated.emit(self.is_calibrated())
        
        self.log_info(f"Added calibration point {len(self.calibration_points)}: "
                     f"pixel({pixel_x}, {pixel_y}) -> stage({stage_x:.2f}, {stage_y:.2f})")
        
        return True
    
    def _validate_coordinates(self, pixel_x: int, pixel_y: int, 
                            stage_x: float, stage_y: float) -> bool:
        """
        Validate coordinate inputs.
        
        Args:
            pixel_x, pixel_y: Pixel coordinates
            stage_x, stage_y: Stage coordinates
        
        Returns:
            True if valid, False otherwise
        """
        # Check pixel coordinates (should be non-negative)
        if pixel_x < 0 or pixel_y < 0:
            self.log_error(f"Invalid pixel coordinates: ({pixel_x}, {pixel_y})")
            return False
        
        # Check stage coordinates (reasonable range check)
        if abs(stage_x) > 100000 or abs(stage_y) > 100000:  # 100mm max range
            self.log_error(f"Stage coordinates out of range: ({stage_x}, {stage_y})")
            return False
        
        return True
    
    @error_handler("Calculating transformation matrix")
    def _calculate_transformation(self) -> bool:
        """
        Calculate affine transformation matrix from calibration points.
        
        Returns:
            True if successful, False otherwise
        """
        if len(self.calibration_points) < 2:
            self.log_error("Need at least 2 calibration points for transformation")
            return False
        
        try:
            # Extract coordinates
            pixel_coords = np.array([[p.pixel_x, p.pixel_y, 1] for p in self.calibration_points])
            stage_coords = np.array([[p.stage_x, p.stage_y] for p in self.calibration_points])
            
            # For 2-point calibration, solve the linear system
            # [x'] = [a b c] [x]
            # [y']   [d e f] [y]
            #                [1]
            
            if len(self.calibration_points) == 2:
                # Linear interpolation/extrapolation case
                p1, p2 = self.calibration_points
                
                # Calculate scale and translation
                pixel_diff = np.array([p2.pixel_x - p1.pixel_x, p2.pixel_y - p1.pixel_y])
                stage_diff = np.array([p2.stage_x - p1.stage_x, p2.stage_y - p1.stage_y])
                
                # Avoid division by zero
                if np.allclose(pixel_diff, 0):
                    self.log_error("Calibration points have identical pixel coordinates")
                    return False
                
                # Simple linear transformation (assumes uniform scaling)
                pixel_distance = np.linalg.norm(pixel_diff)
                stage_distance = np.linalg.norm(stage_diff)
                scale = stage_distance / pixel_distance if pixel_distance > 0 else 1.0
                
                # Calculate rotation angle
                angle = np.arctan2(stage_diff[1], stage_diff[0]) - np.arctan2(pixel_diff[1], pixel_diff[0])
                cos_angle = np.cos(angle)
                sin_angle = np.sin(angle)
                
                # Build transformation matrix
                # [a b c]   [scale*cos  -scale*sin  tx]
                # [d e f] = [scale*sin   scale*cos  ty]
                a = scale * cos_angle
                b = -scale * sin_angle
                d = scale * sin_angle
                e = scale * cos_angle
                
                # Calculate translation to map first point correctly
                c = p1.stage_x - (a * p1.pixel_x + b * p1.pixel_y)
                f = p1.stage_y - (d * p1.pixel_x + e * p1.pixel_y)
                
                self.transform_matrix = np.array([
                    [a, b, c],
                    [d, e, f]
                ])
            
            # Calculate inverse transformation
            # For 2x3 matrix, we need to extend to 3x3 and invert
            extended_matrix = np.vstack([self.transform_matrix, [0, 0, 1]])
            self.inverse_transform_matrix = np.linalg.inv(extended_matrix)[:2, :]
            
            # Validate transformation
            self._validate_transformation()
            
            self._is_calibrated = True
            self.log_info("Transformation matrix calculated successfully")
            return True
            
        except Exception as e:
            self.log_error(f"Failed to calculate transformation: {e}")
            self._is_calibrated = False
            return False
    
    def _validate_transformation(self) -> None:
        """Validate the calculated transformation matrix."""
        if self.transform_matrix is None:
            return
        
        # Test transformation accuracy with calibration points
        total_error = 0.0
        max_error = 0.0
        
        for point in self.calibration_points:
            # Transform pixel to stage
            transformed = self.pixel_to_stage(point.pixel_x, point.pixel_y)
            
            if transformed:
                error_x = abs(transformed.stage_x - point.stage_x)
                error_y = abs(transformed.stage_y - point.stage_y)
                error = np.sqrt(error_x**2 + error_y**2)
                
                total_error += error
                max_error = max(max_error, error)
        
        # Calculate quality metrics
        avg_error = total_error / len(self.calibration_points) if self.calibration_points else 0
        
        self.calibration_quality = {
            'average_error_um': avg_error,
            'max_error_um': max_error,
            'meets_accuracy_target': max_error <= self.max_error_micrometers,
            'transformation_confidence': max(0.0, 1.0 - (max_error / self.max_error_micrometers))
        }
        
        if not self.calibration_quality['meets_accuracy_target']:
            self.log_warning(f"Calibration accuracy below target: {max_error:.3f} µm > {self.max_error_micrometers:.3f} µm")
        else:
            self.log_info(f"Calibration meets accuracy target: max error {max_error:.3f} µm")
    
    def pixel_to_stage(self, pixel_x: int, pixel_y: int) -> Optional[TransformationResult]:
        """
        Transform pixel coordinates to stage coordinates.
        
        Args:
            pixel_x: Pixel X coordinate
            pixel_y: Pixel Y coordinate
        
        Returns:
            TransformationResult or None if transformation not available
        """
        if not self.is_calibrated() or self.transform_matrix is None:
            return None
        
        try:
            # Apply transformation
            pixel_coords = np.array([pixel_x, pixel_y, 1])
            stage_coords = self.transform_matrix @ pixel_coords
            
            # Get quality metrics
            confidence = self.calibration_quality.get('transformation_confidence', 0.0)
            error_estimate = self.calibration_quality.get('max_error_um', 0.0)
            
            return TransformationResult(
                stage_x=float(stage_coords[0]),
                stage_y=float(stage_coords[1]),
                confidence=confidence,
                error_estimate_um=error_estimate
            )
            
        except Exception as e:
            self.log_error(f"Transformation failed: {e}")
            return None
    
    def stage_to_pixel(self, stage_x: float, stage_y: float) -> Optional[Tuple[int, int]]:
        """
        Transform stage coordinates to pixel coordinates (inverse transformation).
        
        Args:
            stage_x: Stage X coordinate in micrometers
            stage_y: Stage Y coordinate in micrometers
        
        Returns:
            Tuple of (pixel_x, pixel_y) or None if transformation not available
        """
        if not self.is_calibrated() or self.inverse_transform_matrix is None:
            return None
        
        try:
            # Apply inverse transformation
            stage_coords = np.array([stage_x, stage_y, 1])
            pixel_coords = self.inverse_transform_matrix @ stage_coords
            
            return (int(round(pixel_coords[0])), int(round(pixel_coords[1])))
            
        except Exception as e:
            self.log_error(f"Inverse transformation failed: {e}")
            return None
    
    def transform_bounding_boxes(self, bounding_boxes: List[Tuple[int, int, int, int]]) -> List[Tuple[float, float, float, float]]:
        """
        Transform a list of pixel bounding boxes to stage coordinates.
        
        Args:
            bounding_boxes: List of (min_x, min_y, max_x, max_y) in pixels
        
        Returns:
            List of (min_x, min_y, max_x, max_y) in stage coordinates
        """
        if not self.is_calibrated():
            return []
        
        transformed_boxes = []
        
        for min_x, min_y, max_x, max_y in bounding_boxes:
            # Transform corners
            min_result = self.pixel_to_stage(min_x, min_y)
            max_result = self.pixel_to_stage(max_x, max_y)
            
            if min_result and max_result:
                transformed_boxes.append((
                    min_result.stage_x,
                    min_result.stage_y,
                    max_result.stage_x,
                    max_result.stage_y
                ))
        
        return transformed_boxes
    
    def clear_calibration(self) -> None:
        """Clear all calibration data."""
        self.calibration_points.clear()
        self.transform_matrix = None
        self.inverse_transform_matrix = None
        self.calibration_quality = {}
        self._is_calibrated = False
        
        self.calibration_cleared.emit()
        self.calibration_updated.emit(False)
        
        self.log_info("Calibration cleared")
    
    def remove_calibration_point(self, index: int) -> bool:
        """
        Remove a calibration point by index.
        
        Args:
            index: Index of point to remove
        
        Returns:
            True if removed successfully, False otherwise
        """
        if 0 <= index < len(self.calibration_points):
            removed_point = self.calibration_points.pop(index)
            
            # Recalculate transformation if we still have enough points
            if len(self.calibration_points) >= 2:
                self._calculate_transformation()
            else:
                self._is_calibrated = False
                self.transform_matrix = None
                self.inverse_transform_matrix = None
                self.calibration_quality = {}
            
            self.calibration_updated.emit(self.is_calibrated())
            
            self.log_info(f"Removed calibration point {index}: {removed_point}")
            return True
        
        return False
    
    def get_calibration_info(self) -> Dict[str, Any]:
        """
        Get information about current calibration state.
        
        Returns:
            Dictionary with calibration information
        """
        info = {
            'is_calibrated': self.is_calibrated(),
            'point_count': len(self.calibration_points),
            'points': [
                {
                    'pixel': (p.pixel_x, p.pixel_y),
                    'stage': (p.stage_x, p.stage_y),
                    'label': p.label
                }
                for p in self.calibration_points
            ],
            'quality_metrics': self.calibration_quality.copy(),
            'has_transformation_matrix': self.transform_matrix is not None
        }
        
        return info
    
    def export_calibration(self) -> Dict[str, Any]:
        """
        Export calibration data for saving.
        
        Returns:
            Dictionary with all calibration data
        """
        data = {
            'calibration_points': [
                {
                    'pixel_x': p.pixel_x,
                    'pixel_y': p.pixel_y,
                    'stage_x': p.stage_x,
                    'stage_y': p.stage_y,
                    'label': p.label
                }
                for p in self.calibration_points
            ],
            'transform_matrix': self.transform_matrix.tolist() if self.transform_matrix is not None else None,
            'calibration_quality': self.calibration_quality.copy(),
            'is_calibrated': self.is_calibrated()
        }
        
        return data
    
    def import_calibration(self, data: Dict[str, Any]) -> bool:
        """
        Import calibration data from saved data.
        
        Args:
            data: Calibration data dictionary
        
        Returns:
            True if imported successfully, False otherwise
        """
        try:
            # Clear current calibration
            self.clear_calibration()
            
            # Import calibration points
            for point_data in data.get('calibration_points', []):
                point = CalibrationPoint(
                    pixel_x=point_data['pixel_x'],
                    pixel_y=point_data['pixel_y'],
                    stage_x=point_data['stage_x'],
                    stage_y=point_data['stage_y'],
                    label=point_data.get('label', '')
                )
                self.calibration_points.append(point)
            
            # Import transformation matrix
            if data.get('transform_matrix'):
                self.transform_matrix = np.array(data['transform_matrix'])
                
                # Recalculate inverse matrix
                extended_matrix = np.vstack([self.transform_matrix, [0, 0, 1]])
                self.inverse_transform_matrix = np.linalg.inv(extended_matrix)[:2, :]
            
            # Import quality metrics
            self.calibration_quality = data.get('calibration_quality', {})
            self._is_calibrated = data.get('is_calibrated', False)
            
            # Emit signals
            self.calibration_updated.emit(self.is_calibrated())
            if self.is_calibrated():
                self.transformation_ready.emit()
            
            self.log_info(f"Imported calibration with {len(self.calibration_points)} points")
            return True
            
        except Exception as e:
            self.log_error(f"Failed to import calibration: {e}")
            self.clear_calibration()
            return False

    def is_calibrated(self) -> bool:
        """
        Check if the coordinate transformer is calibrated.
        
        Returns:
            True if calibrated, False otherwise
        """
        return self._is_calibrated