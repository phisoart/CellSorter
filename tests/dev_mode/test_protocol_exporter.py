"""
DEV Mode Tests for Protocol Exporter System

Tests protocol generation logic in headless environment without GUI.
Validates INI format generation and crop calculation algorithms.

Test sequence: DEV → DUAL → GUI (mandatory)
"""

import pytest
import tempfile
import configparser
from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import Mock, patch

from src.models.extractor import Extractor, BoundingBox, CropRegion, ExtractionPoint
from src.models.coordinate_transformer import CoordinateTransformer, CalibrationPoint
from src.models.selection_manager import SelectionManager
from src.utils.exceptions import ExportError
from src.headless.testing.framework import UITestCase


class TestProtocolExporterDev(UITestCase):
    """DEV mode tests for protocol exporter system."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        
        self.extractor = Extractor()
        self.coordinate_transformer = CoordinateTransformer()
        self.selection_manager = SelectionManager()
        
        # Set up coordinate transformation
        self.coordinate_transformer.add_calibration_point(100, 150, 1000.0, 2000.0, "Point 1")
        self.coordinate_transformer.add_calibration_point(800, 600, 8000.0, 6000.0, "Point 2")
        
        # Test data - realistic cell bounding boxes
        self.test_bounding_boxes = [
            BoundingBox(min_x=120, min_y=180, max_x=140, max_y=200),  # Cell 1: 20x20 pixels
            BoundingBox(min_x=300, min_y=250, max_x=330, max_y=280),  # Cell 2: 30x30 pixels
            BoundingBox(min_x=500, min_y=400, max_x=540, max_y=440),  # Cell 3: 40x40 pixels
            BoundingBox(min_x=700, min_y=550, max_x=720, max_y=570),  # Cell 4: 20x20 pixels
        ]
        
        # Test selections data
        self.test_selections = [
            {
                'id': 'selection_1',
                'label': 'Positive Cells',
                'color': '#FF0000',
                'well_position': 'A01',
                'cell_indices': [0, 2],  # Cells 1 and 3
                'metadata': {'type': 'positive', 'count': 2}
            },
            {
                'id': 'selection_2', 
                'label': 'Negative Cells',
                'color': '#0000FF',
                'well_position': 'A02',
                'cell_indices': [1, 3],  # Cells 2 and 4
                'metadata': {'type': 'negative', 'count': 2}
            }
        ]
        
        # Image metadata
        self.image_info = {
            'width': 1000,
            'height': 800,
            'filename': 'test_image.tiff',
            'path': '/path/to/test_image.tiff',
            'channels': 4,
            'bit_depth': 16
        }
    
    def test_square_crop_calculation(self):
        """Test square crop calculation from bounding boxes."""
        # Test basic square crop calculation
        bbox = BoundingBox(min_x=100, min_y=150, max_x=120, max_y=170)  # 20x20 box
        
        crop_region = self.extractor.calculate_square_crop(bbox)
        
        assert crop_region is not None, "Crop region should be calculated"
        
        # Verify center point
        expected_center_x = (100 + 120) / 2  # 110
        expected_center_y = (150 + 170) / 2  # 160
        
        assert crop_region.center_x == expected_center_x, f"Center X mismatch: {crop_region.center_x} != {expected_center_x}"
        assert crop_region.center_y == expected_center_y, f"Center Y mismatch: {crop_region.center_y} != {expected_center_y}"
        
        # Verify size with padding
        base_size = min(20, 20)  # Both dimensions are 20
        expected_size = base_size * self.extractor.crop_padding_factor  # 20 * 1.2 = 24
        
        assert crop_region.size == expected_size, f"Size mismatch: {crop_region.size} != {expected_size}"
        
        # Verify calculated bounds
        half_size = expected_size / 2  # 12
        assert crop_region.min_x == expected_center_x - half_size, "Min X calculation incorrect"
        assert crop_region.min_y == expected_center_y - half_size, "Min Y calculation incorrect"
        assert crop_region.max_x == expected_center_x + half_size, "Max X calculation incorrect"
        assert crop_region.max_y == expected_center_y + half_size, "Max Y calculation incorrect"
    
    def test_rectangular_bounding_box_crop(self):
        """Test crop calculation for rectangular (non-square) bounding boxes."""
        # Test with wide rectangle
        wide_bbox = BoundingBox(min_x=100, min_y=150, max_x=160, max_y=170)  # 60x20 box
        
        crop_region = self.extractor.calculate_square_crop(wide_bbox)
        
        assert crop_region is not None, "Should handle rectangular bounding box"
        
        # Should use shorter dimension (20) as base
        expected_size = 20 * self.extractor.crop_padding_factor  # 24
        assert crop_region.size == expected_size, f"Should use shorter dimension: {crop_region.size} != {expected_size}"
        
        # Test with tall rectangle
        tall_bbox = BoundingBox(min_x=200, min_y=250, max_x=220, max_y=310)  # 20x60 box
        
        crop_region = self.extractor.calculate_square_crop(tall_bbox)
        
        assert crop_region is not None, "Should handle tall bounding box"
        assert crop_region.size == expected_size, "Should use shorter dimension for tall rectangle"
    
    def test_image_boundary_constraints(self):
        """Test crop calculation with image boundary constraints."""
        image_bounds = (1000, 800)  # 1000x800 image
        
        # Test crop near left edge
        edge_bbox = BoundingBox(min_x=5, min_y=100, max_x=25, max_y=120)  # Near left edge
        
        crop_region = self.extractor.calculate_square_crop(edge_bbox, image_bounds)
        
        assert crop_region is not None, "Should handle edge case"
        assert crop_region.min_x >= 0, "Crop should not extend beyond left edge"
        assert crop_region.min_y >= 0, "Crop should not extend beyond top edge"
        assert crop_region.max_x <= image_bounds[0], "Crop should not extend beyond right edge"
        assert crop_region.max_y <= image_bounds[1], "Crop should not extend beyond bottom edge"
        
        # Test crop near corner (worst case)
        corner_bbox = BoundingBox(min_x=990, min_y=790, max_x=995, max_y=795)  # Near bottom-right corner
        
        crop_region = self.extractor.calculate_square_crop(corner_bbox, image_bounds)
        
        if crop_region is not None:  # May be None if impossible to fit
            assert crop_region.min_x >= 0, "Corner crop should not extend beyond boundaries"
            assert crop_region.min_y >= 0, "Corner crop should not extend beyond boundaries"
            assert crop_region.max_x <= image_bounds[0], "Corner crop should not extend beyond boundaries"
            assert crop_region.max_y <= image_bounds[1], "Corner crop should not extend beyond boundaries"
    
    def test_minimum_maximum_crop_size_constraints(self):
        """Test minimum and maximum crop size constraints."""
        # Test tiny bounding box (should enforce minimum size)
        tiny_bbox = BoundingBox(min_x=100, min_y=150, max_x=102, max_y=152)  # 2x2 box
        
        crop_region = self.extractor.calculate_square_crop(tiny_bbox)
        
        assert crop_region is not None, "Should handle tiny bounding box"
        assert crop_region.size >= self.extractor.min_crop_size_pixels, "Should enforce minimum crop size"
        
        # Test huge bounding box (should enforce maximum size)
        huge_bbox = BoundingBox(min_x=100, min_y=150, max_x=1100, max_y=1150)  # 1000x1000 box
        
        crop_region = self.extractor.calculate_square_crop(huge_bbox)
        
        assert crop_region is not None, "Should handle huge bounding box"
        assert crop_region.size <= self.extractor.max_crop_size_pixels, "Should enforce maximum crop size"
    
    def test_extraction_points_creation(self):
        """Test creation of extraction points from selections and bounding boxes."""
        extraction_points = self.extractor.create_extraction_points(
            self.test_selections,
            self.test_bounding_boxes,
            self.coordinate_transformer,
            (self.image_info['width'], self.image_info['height'])
        )
        
        # Should create one extraction point per cell
        total_cells = sum(len(sel['cell_indices']) for sel in self.test_selections)
        assert len(extraction_points) == total_cells, f"Should create {total_cells} extraction points"
        
        # Verify extraction point data
        for point in extraction_points:
            assert isinstance(point, ExtractionPoint), "Should create ExtractionPoint objects"
            assert point.id is not None and point.id != "", "Should have valid ID"
            assert point.label is not None and point.label != "", "Should have valid label"
            assert point.color.startswith('#'), "Should have valid color format"
            assert point.well_position is not None, "Should have well position"
            assert isinstance(point.crop_region, CropRegion), "Should have crop region"
            assert isinstance(point.metadata, dict), "Should have metadata dictionary"
        
        # Verify coordinate transformation was applied
        for point in extraction_points:
            crop = point.crop_region
            # Crop coordinates should be in stage coordinates (micrometers)
            assert crop.center_x > 100, "Stage X coordinates should be in micrometers"
            assert crop.center_y > 100, "Stage Y coordinates should be in micrometers"
    
    def test_protocol_file_generation(self):
        """Test .cxprotocol file generation in INI format."""
        # Create extraction points
        extraction_points = self.extractor.create_extraction_points(
            self.test_selections,
            self.test_bounding_boxes,
            self.coordinate_transformer,
            (self.image_info['width'], self.image_info['height'])
        )
        
        # Generate protocol file
        with tempfile.NamedTemporaryFile(suffix='.cxprotocol', delete=False) as temp_file:
            output_path = temp_file.name
        
        success = self.extractor.generate_protocol_file(
            extraction_points,
            output_path,
            self.image_info
        )
        
        assert success, "Protocol file generation should succeed"
        
        # Verify file was created
        protocol_file = Path(output_path)
        assert protocol_file.exists(), "Protocol file should be created"
        
        # Parse and validate INI format
        config = configparser.ConfigParser()
        config.read(output_path)
        
        # Verify required sections exist
        assert 'IMAGE' in config.sections(), "Should have IMAGE section"
        assert 'IMAGING_LAYOUT' in config.sections(), "Should have IMAGING_LAYOUT section"
        
        # Verify IMAGE section content (using actual implementation keys)
        image_section = config['IMAGE']
        assert 'FILE' in image_section, "Should have FILE in IMAGE section"
        assert 'WIDTH' in image_section, "Should have WIDTH in IMAGE section"
        assert 'HEIGHT' in image_section, "Should have HEIGHT in IMAGE section"
        assert 'FORMAT' in image_section, "Should have FORMAT in IMAGE section"
        
        # Verify IMAGING_LAYOUT section content
        layout_section = config['IMAGING_LAYOUT']
        assert 'PositionOnly' in layout_section, "Should have PositionOnly"
        assert 'AfterBefore' in layout_section, "Should have AfterBefore"
        assert 'Points' in layout_section, "Should have Points count"
        
        # Verify point count matches extraction points
        point_count = int(layout_section['Points'])
        assert point_count == len(extraction_points), "Point count should match extraction points"
        
        # Verify point entries exist
        for i in range(1, point_count + 1):
            point_key = f'P_{i}'
            assert point_key in layout_section, f"Should have point entry {point_key}"
            
            # Verify point data format
            point_data = layout_section[point_key]
            parts = [p.strip() for p in point_data.split(';')]
            assert len(parts) >= 6, f"Point {i} should have at least 6 data fields"
            
            # Verify coordinates are numeric
            try:
                float(parts[0])  # min_x
                float(parts[1])  # min_y
                float(parts[2])  # max_x
                float(parts[3])  # max_y
            except ValueError:
                assert False, f"Point {i} coordinates should be numeric"
        
        # Clean up
        protocol_file.unlink()
    
    def test_protocol_file_validation(self):
        """Test protocol file validation functionality."""
        # Create a valid protocol file first
        extraction_points = self.extractor.create_extraction_points(
            self.test_selections,
            self.test_bounding_boxes,
            self.coordinate_transformer,
            (self.image_info['width'], self.image_info['height'])
        )
        
        with tempfile.NamedTemporaryFile(suffix='.cxprotocol', delete=False) as temp_file:
            output_path = temp_file.name
        
        self.extractor.generate_protocol_file(extraction_points, output_path, self.image_info)
        
        # Validate the generated file
        validation_result = self.extractor.validate_protocol_file(output_path)
        
        assert validation_result['is_valid'], "Generated protocol file should be valid"
        assert len(validation_result['errors']) == 0, "Should have no validation errors"
        assert validation_result['point_count'] == len(extraction_points), "Point count should match"
        assert validation_result['file_size_bytes'] > 0, "File should have content"
        
        # Test validation with non-existent file
        invalid_path = "/path/that/does/not/exist.cxprotocol"
        invalid_result = self.extractor.validate_protocol_file(invalid_path)
        
        assert not invalid_result['is_valid'], "Non-existent file should be invalid"
        assert len(invalid_result['errors']) > 0, "Should have validation errors"
        assert "File does not exist" in invalid_result['errors'][0], "Should report missing file"
        
        # Test validation with malformed file
        with tempfile.NamedTemporaryFile(suffix='.cxprotocol', delete=False, mode='w') as temp_file:
            malformed_path = temp_file.name
            temp_file.write("This is not a valid INI file\n")
            temp_file.write("Missing sections and structure\n")
        
        malformed_result = self.extractor.validate_protocol_file(malformed_path)
        
        assert not malformed_result['is_valid'], "Malformed file should be invalid"
        assert len(malformed_result['errors']) > 0, "Should have validation errors"
        
        # Clean up
        Path(output_path).unlink()
        Path(malformed_path).unlink()
    
    def test_extraction_statistics(self):
        """Test extraction statistics calculation."""
        extraction_points = self.extractor.create_extraction_points(
            self.test_selections,
            self.test_bounding_boxes,
            self.coordinate_transformer,
            (self.image_info['width'], self.image_info['height'])
        )
        
        stats = self.extractor.get_extraction_statistics(extraction_points)
        
        # Verify statistics structure
        assert 'total_points' in stats, "Should have total points count"
        assert 'unique_wells' in stats, "Should have unique wells count"
        assert 'unique_colors' in stats, "Should have unique colors count"
        assert 'average_crop_size' in stats, "Should have average crop size"
        assert 'crop_size_range' in stats, "Should have crop size range"
        assert 'crop_size_std' in stats, "Should have crop size standard deviation"
        assert 'wells_used' in stats, "Should have wells used list"
        assert 'colors_used' in stats, "Should have colors used list"
        
        # Verify statistics values
        assert stats['total_points'] > 0, "Should have positive point count"
        assert stats['unique_colors'] > 0, "Should have at least one color"
        assert stats['average_crop_size'] > 0, "Should have positive average crop size"
        
        # Verify crop size range
        min_size, max_size = stats['crop_size_range']
        assert min_size <= max_size, "Min crop size should be <= max crop size"
        assert stats['average_crop_size'] >= min_size, "Average should be >= minimum"
        assert stats['average_crop_size'] <= max_size, "Average should be <= maximum"
        
        # Verify colors are from test selections
        expected_colors = {sel['color'] for sel in self.test_selections}
        assert set(stats['colors_used']).issubset(expected_colors), "Colors should match test selections"
        
        # Test with empty extraction points
        empty_stats = self.extractor.get_extraction_statistics([])
        assert empty_stats['total_points'] == 0, "Empty list should have zero points"
        assert empty_stats['average_crop_size'] == 0.0, "Empty list should have zero average"
    
    def test_error_handling(self):
        """Test error handling in various scenarios."""
        # Test with empty selections
        empty_extraction_points = self.extractor.create_extraction_points(
            [],  # Empty selections
            self.test_bounding_boxes,
            self.coordinate_transformer
        )
        
        assert len(empty_extraction_points) == 0, "Should handle empty selections gracefully"
        
        # Test with invalid bounding box
        invalid_bbox = BoundingBox(min_x=100, min_y=150, max_x=90, max_y=140)  # Invalid (min > max)
        
        crop_region = self.extractor.calculate_square_crop(invalid_bbox)
        assert crop_region is None, "Should return None for invalid bounding box"
        
        # Test with out-of-range cell indices
        invalid_selections = [{
            'id': 'invalid_selection',
            'label': 'Invalid',
            'color': '#FF0000',
            'well_position': 'A01',
            'cell_indices': [999],  # Out of range
            'metadata': {}
        }]
        
        invalid_extraction_points = self.extractor.create_extraction_points(
            invalid_selections,
            self.test_bounding_boxes,
            self.coordinate_transformer
        )
        
        assert len(invalid_extraction_points) == 0, "Should handle out-of-range indices gracefully"
        
        # Test protocol generation with empty points - should fail
        with tempfile.NamedTemporaryFile(suffix='.cxprotocol', delete=False) as temp_file:
            output_path = temp_file.name
        
        success = self.extractor.generate_protocol_file([], output_path, self.image_info)
        
        # Should fail with empty extraction points
        assert not success, "Should fail with empty extraction points"
        
        # Test with valid points to ensure success case works
        valid_extraction_points = self.extractor.create_extraction_points(
            self.test_selections,
            self.test_bounding_boxes,
            self.coordinate_transformer,
            (self.image_info['width'], self.image_info['height'])
        )
        
        success = self.extractor.generate_protocol_file(valid_extraction_points, output_path, self.image_info)
        assert success, "Should succeed with valid extraction points"
        
        # Clean up
        Path(output_path).unlink()
    
    def test_coordinate_transformation_integration(self):
        """Test integration with coordinate transformation system."""
        # Test without calibrated transformer - should not create points
        uncalibrated_transformer = CoordinateTransformer()
        
        extraction_points = self.extractor.create_extraction_points(
            self.test_selections,
            self.test_bounding_boxes,
            uncalibrated_transformer
        )
        
        # Should not create extraction points without calibration
        assert len(extraction_points) == 0, "Should not create points without calibration"
        
        # Test with calibrated transformer - should create points
        calibrated_extraction_points = self.extractor.create_extraction_points(
            self.test_selections,
            self.test_bounding_boxes,
            self.coordinate_transformer,
            (self.image_info['width'], self.image_info['height'])
        )
        
        # Should create extraction points with calibration
        assert len(calibrated_extraction_points) > 0, "Should create points with calibration"
        
        # Verify coordinates are transformed (should be in micrometers, not pixels)
        for point in calibrated_extraction_points:
            # Stage coordinates should be much larger than pixel coordinates
            assert point.crop_region.center_x > 100, "Stage X coordinates should be in micrometers"
            assert point.crop_region.center_y > 100, "Stage Y coordinates should be in micrometers"
            
        # Test with None transformer - should use pixel coordinates
        pixel_extraction_points = self.extractor.create_extraction_points(
            self.test_selections,
            self.test_bounding_boxes,
            None,  # No transformer
            (self.image_info['width'], self.image_info['height'])
        )
        
        # Should create extraction points using pixel coordinates
        assert len(pixel_extraction_points) > 0, "Should create points with pixel coordinates"
        
        # Verify coordinates are in pixel range
        for point in pixel_extraction_points:
            # Pixel coordinates should be smaller than stage coordinates
            assert point.crop_region.center_x < 1000, "Pixel X coordinates should be in pixel range"
            assert point.crop_region.center_y < 1000, "Pixel Y coordinates should be in pixel range"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])