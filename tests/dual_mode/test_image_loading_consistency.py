"""
DUAL Mode Tests for Image Loading Consistency
Tests GUI-headless synchronization for image loading operations.
"""

import pytest
import numpy as np
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtCore import QThread
from PySide6.QtGui import QImage

from src.models.image_handler import ImageHandler
from src.headless.testing.framework import UITestCase


class TestImageLoadingConsistencyDual(UITestCase):
    """DUAL mode tests for image loading consistency between GUI and headless."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.temp_dir = tempfile.mkdtemp()
        
        # Create GUI and headless handlers
        self.gui_handler = ImageHandler()
        self.headless_handler = ImageHandler()
        
    def tearDown(self):
        """Clean up test environment."""
        super().tearDown()
        self.gui_handler.cleanup()
        self.headless_handler.cleanup()
        
        # Clean up temp directory
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_image_processing_consistency(self):
        """Test that GUI and headless modes process images identically."""
        # Create test image
        test_array = np.random.randint(0, 256, (256, 256, 3), dtype=np.uint8)
        
        # Process in both modes
        gui_qimage = self.gui_handler._numpy_to_qimage(test_array)
        headless_qimage = self.headless_handler._numpy_to_qimage(test_array)
        
        # Verify consistency
        self.assertEqual(gui_qimage.width(), headless_qimage.width())
        self.assertEqual(gui_qimage.height(), headless_qimage.height())
        self.assertEqual(gui_qimage.format(), headless_qimage.format())
        
        # Verify both are valid
        self.assertFalse(gui_qimage.isNull())
        self.assertFalse(headless_qimage.isNull())
    
    def test_zoom_operation_synchronization(self):
        """Test zoom operations synchronization between modes."""
        test_array = np.random.randint(0, 256, (200, 200, 3), dtype=np.uint8)
        
        # Set same image data
        self.gui_handler.image_data = test_array.copy()
        self.headless_handler.image_data = test_array.copy()
        
        # Perform same zoom operations
        self.gui_handler.zoom_in()
        self.headless_handler.zoom_in()
        
        # Verify zoom levels match
        self.assertEqual(self.gui_handler.zoom_level, self.headless_handler.zoom_level)
        
        # Test zoom out
        self.gui_handler.zoom_out()
        self.headless_handler.zoom_out()
        
        self.assertEqual(self.gui_handler.zoom_level, self.headless_handler.zoom_level)
        
        # Test set zoom
        target_zoom = 2.5
        self.gui_handler.set_zoom(target_zoom)
        self.headless_handler.set_zoom(target_zoom)
        
        self.assertEqual(self.gui_handler.zoom_level, self.headless_handler.zoom_level)
    
    def test_overlay_management_consistency(self):
        """Test overlay management consistency between modes."""
        test_array = np.random.randint(0, 256, (150, 150, 3), dtype=np.uint8)
        
        # Set same image data
        self.gui_handler.image_data = test_array.copy()
        self.headless_handler.image_data = test_array.copy()
        
        # Add same overlays
        overlay_params = ('rectangle', 25, 25, 50, 50, '#FF0000', 0.7)
        self.gui_handler.add_overlay(*overlay_params)
        self.headless_handler.add_overlay(*overlay_params)
        
        # Verify overlay count
        self.assertEqual(len(self.gui_handler.overlays), len(self.headless_handler.overlays))
        
        # Verify overlay properties
        gui_overlay = self.gui_handler.overlays[0]
        headless_overlay = self.headless_handler.overlays[0]
        
        self.assertEqual(gui_overlay['type'], headless_overlay['type'])
        self.assertEqual(gui_overlay['x'], headless_overlay['x'])
        self.assertEqual(gui_overlay['y'], headless_overlay['y'])
        self.assertEqual(gui_overlay['width'], headless_overlay['width'])
        self.assertEqual(gui_overlay['height'], headless_overlay['height'])
        self.assertEqual(gui_overlay['color'], headless_overlay['color'])
        self.assertEqual(gui_overlay['alpha'], headless_overlay['alpha'])
        
        # Test overlay visibility toggle
        self.gui_handler.toggle_overlays(False)
        self.headless_handler.toggle_overlays(False)
        
        self.assertEqual(self.gui_handler.show_overlays, self.headless_handler.show_overlays)
        
        # Test clear overlays
        self.gui_handler.clear_overlays()
        self.headless_handler.clear_overlays()
        
        self.assertEqual(len(self.gui_handler.overlays), len(self.headless_handler.overlays))
        self.assertEqual(len(self.gui_handler.overlays), 0)
    
    def test_image_info_consistency(self):
        """Test image information consistency between modes."""
        test_array = np.random.randint(0, 256, (180, 240, 3), dtype=np.uint8)
        test_path = "/test/path/image.tiff"
        
        # Set same image data and path
        self.gui_handler.image_data = test_array.copy()
        self.gui_handler.file_path = test_path
        
        self.headless_handler.image_data = test_array.copy()
        self.headless_handler.file_path = test_path
        
        # Get image info from both
        gui_info = self.gui_handler.get_image_info()
        headless_info = self.headless_handler.get_image_info()
        
        # Verify consistency
        self.assertEqual(gui_info.get('width'), headless_info.get('width'))
        self.assertEqual(gui_info.get('height'), headless_info.get('height'))
        
        # Both should report correct dimensions
        self.assertEqual(gui_info.get('width'), 240)  # numpy shape is (height, width, channels)
        self.assertEqual(gui_info.get('height'), 180)
    
    def test_different_format_processing_consistency(self):
        """Test consistency across different image formats."""
        formats_to_test = [
            # (array_shape, description)
            ((100, 100, 3), "RGB"),
            ((100, 100, 4), "RGBA"),
            ((100, 100), "Grayscale"),
        ]
        
        for array_shape, description in formats_to_test:
            with self.subTest(format=description):
                # Generate test data
                if len(array_shape) == 2:  # Grayscale
                    test_array = np.random.randint(0, 256, array_shape, dtype=np.uint8)
                else:  # RGB/RGBA
                    test_array = np.random.randint(0, 256, array_shape, dtype=np.uint8)
                
                # Process in both modes
                gui_qimage = self.gui_handler._numpy_to_qimage(test_array)
                headless_qimage = self.headless_handler._numpy_to_qimage(test_array)
                
                # Verify consistency
                self.assertEqual(gui_qimage.width(), headless_qimage.width(), 
                               f"Width mismatch for {description}")
                self.assertEqual(gui_qimage.height(), headless_qimage.height(),
                               f"Height mismatch for {description}")
                
                # Both should be valid
                self.assertFalse(gui_qimage.isNull(), f"GUI QImage null for {description}")
                self.assertFalse(headless_qimage.isNull(), f"Headless QImage null for {description}")
    
    def test_error_handling_consistency(self):
        """Test error handling consistency between modes."""
        # Test with invalid array
        invalid_array = np.array([1, 2, 3, 4], dtype=np.uint8)
        
        gui_result = self.gui_handler._numpy_to_qimage(invalid_array)
        headless_result = self.headless_handler._numpy_to_qimage(invalid_array)
        
        # Both should handle error the same way
        self.assertEqual(gui_result.isNull(), headless_result.isNull())
        self.assertTrue(gui_result.isNull())  # Should be null for invalid input
        
        # Test with unsupported channel count
        invalid_5ch = np.random.randint(0, 256, (10, 10, 5), dtype=np.uint8)
        
        gui_result_5ch = self.gui_handler._numpy_to_qimage(invalid_5ch)
        headless_result_5ch = self.headless_handler._numpy_to_qimage(invalid_5ch)
        
        self.assertEqual(gui_result_5ch.isNull(), headless_result_5ch.isNull())
        self.assertTrue(gui_result_5ch.isNull())
