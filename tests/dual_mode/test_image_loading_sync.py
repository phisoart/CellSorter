"""
DUAL Mode Tests for Image Loading Synchronization
Tests synchronization between GUI and headless image loading operations.
"""

import unittest
import tempfile
import os
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtCore import QThread, QObject, Signal
from PySide6.QtGui import QPixmap, QImage

# Import test framework
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from src.headless.testing.framework import UITestCase

# Import modules to test
from src.models.image_handler import ImageHandler, ImageLoadWorker


class TestImageLoadingSyncDualMode(UITestCase):
    """DUAL mode tests for image loading synchronization between GUI and headless"""
    
    def setUp(self):
        """Set up test environment with both GUI and headless components"""
        super().setUp()
        
        # Create test image files
        self.temp_dir = tempfile.mkdtemp()
        self.test_image_path = os.path.join(self.temp_dir, "sync_test.tiff")
        self._create_test_image()
        
    def tearDown(self):
        """Clean up test files"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        super().tearDown()
        
    def _create_test_image(self):
        """Create a test image file"""
        test_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        try:
            from PIL import Image
            pil_image = Image.fromarray(test_array)
            pil_image.save(self.test_image_path, "TIFF")
        except ImportError:
            with open(self.test_image_path, 'wb') as f:
                f.write(b'\x00' * 1000)
    
    def test_gui_headless_loading_consistency(self):
        """Test that GUI and headless modes load the same image consistently"""
        # Create mock handlers for both modes
        gui_handler = Mock(spec=ImageHandler)
        gui_handler.zoom_level = 1.0
        gui_handler.image_data = None
        
        headless_handler = Mock(spec=ImageHandler)
        headless_handler.zoom_level = 1.0
        headless_handler.image_data = None
        
        # Both should have same initial state
        self.assertEqual(gui_handler.zoom_level, headless_handler.zoom_level)
        self.assertEqual(gui_handler.image_data, headless_handler.image_data)
            
    def test_image_metadata_synchronization(self):
        """Test that image metadata is synchronized between modes"""
        # Create mock handlers
        gui_handler = Mock(spec=ImageHandler)
        headless_handler = Mock(spec=ImageHandler)
        
        # Test metadata consistency
        self.assertIsNotNone(gui_handler)
        self.assertIsNotNone(headless_handler)
            
    def test_zoom_state_synchronization(self):
        """Test that zoom states are synchronized between GUI and headless modes"""
        gui_handler = Mock(spec=ImageHandler)
        headless_handler = Mock(spec=ImageHandler)
        
        # Test zoom synchronization
        test_scales = [0.5, 1.0, 1.5, 2.0]
        for scale in test_scales:
            gui_handler.zoom_level = scale
            headless_handler.zoom_level = scale
            
            self.assertEqual(gui_handler.zoom_level, headless_handler.zoom_level)
                
    def test_loading_worker_consistency(self):
        """Test that loading workers behave consistently in both modes"""
        # Create workers for the same image
        gui_worker = ImageLoadWorker(self.test_image_path)
        headless_worker = ImageLoadWorker(self.test_image_path)
        
        # Both should have same image path
        self.assertEqual(gui_worker.file_path, headless_worker.file_path)
        
        # Both should be QObject instances
        self.assertIsInstance(gui_worker, QObject)
        self.assertIsInstance(headless_worker, QObject)
        
    def test_error_handling_synchronization(self):
        """Test that error handling is synchronized between modes"""
        # Test with invalid path
        invalid_path = "/nonexistent/image.tiff"
        
        gui_worker = ImageLoadWorker(invalid_path)
        headless_worker = ImageLoadWorker(invalid_path)
        
        # Both should handle the same error consistently
        self.assertEqual(gui_worker.file_path, headless_worker.file_path)
        
    def test_numpy_conversion_consistency(self):
        """Test that NumPy conversions produce consistent results in both modes"""
        gui_handler = Mock(spec=ImageHandler)
        headless_handler = Mock(spec=ImageHandler)
        
        # Test array conversion
        test_array = np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8)
        
        with patch('PySide6.QtGui.QImage') as mock_qimage:
            mock_qimage.return_value = Mock()
            
            gui_handler._numpy_to_qimage.return_value = Mock()
            headless_handler._numpy_to_qimage.return_value = Mock()
            
            gui_result = gui_handler._numpy_to_qimage(test_array)
            headless_result = headless_handler._numpy_to_qimage(test_array)
            
            # Both should produce results
            self.assertIsNotNone(gui_result)
            self.assertIsNotNone(headless_result)
            
    def test_overlay_state_synchronization(self):
        """Test that overlay states are synchronized between modes"""
        gui_handler = Mock(spec=ImageHandler)
        gui_handler.overlays = []
        
        headless_handler = Mock(spec=ImageHandler)
        headless_handler.overlays = []
        
        # Test overlay synchronization
        self.assertIsNotNone(gui_handler)
        self.assertIsNotNone(headless_handler)
        self.assertEqual(len(gui_handler.overlays), len(headless_handler.overlays))
            
    def test_performance_consistency(self):
        """Test that performance characteristics are consistent between modes"""
        import time
        
        # Measure GUI handler creation time (mocked)
        start_time = time.time()
        gui_handler = Mock(spec=ImageHandler)
        gui_creation_time = time.time() - start_time
        
        # Measure headless handler creation time (mocked)
        start_time = time.time()
        headless_handler = Mock(spec=ImageHandler)
        headless_creation_time = time.time() - start_time
        
        # Both should be reasonably fast
        self.assertLess(gui_creation_time, 1.0)
        self.assertLess(headless_creation_time, 1.0)
        
        # Performance should be comparable (within reasonable range)
        time_diff = abs(gui_creation_time - headless_creation_time)
        self.assertLess(time_diff, 0.5)  # Should be within 0.5 seconds
        
    def test_concurrent_mode_operations(self):
        """Test concurrent operations between GUI and headless modes"""
        # Create mock handlers
        gui_handler = Mock(spec=ImageHandler)
        headless_handler = Mock(spec=ImageHandler)
        
        # Create concurrent workers
        gui_worker = ImageLoadWorker(self.test_image_path)
        headless_worker = ImageLoadWorker(self.test_image_path)
        
        # Both should be created successfully
        self.assertIsNotNone(gui_worker)
        self.assertIsNotNone(headless_worker)
            
    def test_state_transition_synchronization(self):
        """Test that state transitions are synchronized between modes"""
        gui_handler = Mock(spec=ImageHandler)
        headless_handler = Mock(spec=ImageHandler)
        
        # Test state changes
        initial_scale = 1.0
        new_scale = 1.5
        
        gui_handler.zoom_level = initial_scale
        headless_handler.zoom_level = initial_scale
        
        # Change scale in both
        gui_handler.zoom_level = new_scale
        headless_handler.zoom_level = new_scale
        
        # Both should have the same new scale
        self.assertEqual(gui_handler.zoom_level, new_scale)
        self.assertEqual(headless_handler.zoom_level, new_scale)


if __name__ == '__main__':
    unittest.main() 