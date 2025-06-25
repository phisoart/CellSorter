"""
Test Image Handler

Tests for models.image_handler module to ensure compliance with
PRODUCT_REQUIREMENTS.md specifications for image processing.
"""

import pytest
import time
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QThread, QTimer
from PySide6.QtGui import QImage, QPixmap

from models.image_handler import ImageHandler, ImageLoadWorker
from utils.exceptions import ImageLoadError, PerformanceError


@pytest.mark.unit
class TestImageLoadWorker:
    """Test ImageLoadWorker for asynchronous image loading."""
    
    def test_worker_creation(self, sample_tiff_file):
        """Test ImageLoadWorker instantiation."""
        worker = ImageLoadWorker(str(sample_tiff_file))
        assert worker.file_path == str(sample_tiff_file)
        assert worker.is_cancelled is False
    
    def test_worker_cancellation(self, sample_tiff_file):
        """Test worker cancellation functionality."""
        worker = ImageLoadWorker(str(sample_tiff_file))
        worker.cancel()
        assert worker.is_cancelled is True
    
    @pytest.mark.slow
    def test_load_tiff_image(self, sample_tiff_file):
        """Test loading TIFF image format."""
        worker = ImageLoadWorker(str(sample_tiff_file))
        
        # Connect signals to capture results
        results = {'image': None, 'metadata': None, 'error': None}
        
        def capture_success(image, metadata):
            results['image'] = image
            results['metadata'] = metadata
        
        def capture_error(error):
            results['error'] = error
        
        worker.loading_finished.connect(capture_success)
        worker.loading_failed.connect(capture_error)
        
        # Load image
        worker.load_image()
        
        # Verify successful loading
        assert results['error'] is None, f"Loading failed: {results['error']}"
        assert results['image'] is not None
        assert results['metadata'] is not None
        
        # Verify image properties
        image = results['image']
        assert isinstance(image, np.ndarray)
        assert len(image.shape) in [2, 3]  # Grayscale or color
        
        # Verify metadata
        metadata = results['metadata']
        assert metadata['format'] == 'TIFF'
        assert 'shape' in metadata
        assert 'load_time_seconds' in metadata
        assert 'file_size_mb' in metadata
    
    def test_load_jpg_image(self, sample_jpg_file):
        """Test loading JPG image format."""
        worker = ImageLoadWorker(str(sample_jpg_file))
        
        results = {'image': None, 'metadata': None, 'error': None}
        
        def capture_success(image, metadata):
            results['image'] = image
            results['metadata'] = metadata
        
        worker.loading_finished.connect(capture_success)
        worker.loading_failed.connect(capture_error)
        
        worker.load_image()
        
        assert results['error'] is None
        assert results['image'] is not None
        assert results['metadata']['format'] == 'JPG'
    
    def test_load_png_image(self, sample_png_file):
        """Test loading PNG image format."""
        worker = ImageLoadWorker(str(sample_png_file))
        
        results = {'image': None, 'metadata': None, 'error': None}
        
        def capture_success(image, metadata):
            results['image'] = image
            results['metadata'] = metadata
        
        worker.loading_finished.connect(capture_success)
        worker.loading_failed.connect(capture_error)
        
        worker.load_image()
        
        assert results['error'] is None
        assert results['image'] is not None
        assert results['metadata']['format'] == 'PNG'
    
    def test_load_nonexistent_file(self, temp_dir):
        """Test error handling for nonexistent files."""
        nonexistent_file = temp_dir / "nonexistent.jpg"
        worker = ImageLoadWorker(str(nonexistent_file))
        
        error_message = None
        
        def capture_error(error):
            nonlocal error_message
            error_message = error
        
        worker.loading_failed.connect(capture_error)
        worker.load_image()
        
        assert error_message is not None
        assert "File not found" in error_message
    
    def test_load_unsupported_format(self, temp_dir):
        """Test error handling for unsupported file formats."""
        # Create a text file with image extension
        unsupported_file = temp_dir / "fake.bmp"
        unsupported_file.write_text("Not an image")
        
        worker = ImageLoadWorker(str(unsupported_file))
        
        error_message = None
        
        def capture_error(error):
            nonlocal error_message
            error_message = error
        
        worker.loading_failed.connect(capture_error)
        worker.load_image()
        
        assert error_message is not None


@pytest.mark.gui
class TestImageHandler:
    """Test ImageHandler GUI component."""
    
    def test_image_handler_creation(self, qapp):
        """Test ImageHandler widget creation."""
        handler = ImageHandler()
        
        assert handler.image_data is None
        assert handler.current_file_path is None
        assert handler.zoom_level == 1.0
        assert handler.pan_offset == (0, 0)
        assert len(handler.overlays) == 0
        assert handler.show_overlays is True
    
    def test_image_handler_ui_setup(self, qapp):
        """Test UI component setup."""
        handler = ImageHandler()
        
        # Check that UI elements exist
        assert handler.image_label is not None
        assert handler.progress_bar is not None
        
        # Check initial state
        assert handler.progress_bar.isVisible() is False
        assert "No image loaded" in handler.image_label.text()
    
    @pytest.mark.slow
    def test_load_image_async(self, qapp, sample_tiff_file):
        """Test asynchronous image loading."""
        handler = ImageHandler()
        
        # Track signals
        signals_received = {'loaded': False, 'failed': False}
        
        def on_loaded(file_path):
            signals_received['loaded'] = True
        
        def on_failed(error):
            signals_received['failed'] = True
        
        handler.image_loaded.connect(on_loaded)
        handler.image_load_failed.connect(on_failed)
        
        # Start loading
        handler.load_image(str(sample_tiff_file))
        
        # Wait for loading to complete (with timeout)
        timeout = 5000  # 5 seconds
        start_time = time.time()
        
        while not (signals_received['loaded'] or signals_received['failed']):
            qapp.processEvents()
            if (time.time() - start_time) * 1000 > timeout:
                break
            time.sleep(0.01)
        
        # Verify successful loading
        assert signals_received['loaded'] is True
        assert signals_received['failed'] is False
        assert handler.image_data is not None
        assert handler.current_file_path == str(sample_tiff_file)
    
    def test_zoom_functionality(self, qapp, sample_image_data):
        """Test zoom in/out/fit functionality."""
        handler = ImageHandler()
        
        # Simulate loaded image
        handler.image_data = sample_image_data
        handler._update_display()
        
        # Test zoom in
        original_zoom = handler.zoom_level
        handler.zoom_in()
        assert handler.zoom_level > original_zoom
        
        # Test zoom out
        handler.zoom_out()
        assert handler.zoom_level < handler.zoom_level  # Should be less than after zoom in
        
        # Test zoom limits
        handler.set_zoom(0.05)  # Below minimum
        assert handler.zoom_level >= 0.1
        
        handler.set_zoom(15.0)  # Above maximum
        assert handler.zoom_level <= 10.0
    
    def test_overlay_functionality(self, qapp, sample_image_data):
        """Test overlay add/clear/toggle functionality."""
        handler = ImageHandler()
        handler.image_data = sample_image_data
        
        # Test adding overlay
        handler.add_overlay('rectangle', 100, 100, 50, 50, '#FF0000', 0.3)
        assert len(handler.overlays) == 1
        
        overlay = handler.overlays[0]
        assert overlay['type'] == 'rectangle'
        assert overlay['x'] == 100
        assert overlay['y'] == 100
        assert overlay['color'] == '#FF0000'
        
        # Test toggle overlays
        handler.toggle_overlays(False)
        assert handler.show_overlays is False
        
        handler.toggle_overlays(True)
        assert handler.show_overlays is True
        
        # Test clear overlays
        handler.clear_overlays()
        assert len(handler.overlays) == 0
    
    def test_numpy_to_qimage_conversion(self, qapp, sample_image_data, sample_grayscale_image):
        """Test numpy array to QImage conversion."""
        handler = ImageHandler()
        
        # Test RGB image conversion
        qimage_rgb = handler._numpy_to_qimage(sample_image_data)
        assert isinstance(qimage_rgb, QImage)
        assert qimage_rgb.width() == sample_image_data.shape[1]
        assert qimage_rgb.height() == sample_image_data.shape[0]
        
        # Test grayscale image conversion
        qimage_gray = handler._numpy_to_qimage(sample_grayscale_image)
        assert isinstance(qimage_gray, QImage)
        assert qimage_gray.width() == sample_grayscale_image.shape[1]
        assert qimage_gray.height() == sample_grayscale_image.shape[0]
    
    def test_get_image_info(self, qapp, sample_image_data):
        """Test image information retrieval."""
        handler = ImageHandler()
        
        # Test empty state
        info = handler.get_image_info()
        assert info == {}
        
        # Test with loaded image
        handler.image_data = sample_image_data
        handler.current_file_path = "/test/path.jpg"
        handler.zoom_level = 1.5
        handler.add_overlay('rectangle', 0, 0, 10, 10)
        
        info = handler.get_image_info()
        assert info['file_path'] == "/test/path.jpg"
        assert info['shape'] == sample_image_data.shape
        assert info['zoom_level'] == 1.5
        assert info['overlay_count'] == 1
        assert info['overlays_visible'] is True
    
    def test_cleanup(self, qapp):
        """Test resource cleanup."""
        handler = ImageHandler()
        
        # Set up some state
        handler.image_data = np.zeros((100, 100, 3))
        handler.add_overlay('rectangle', 0, 0, 10, 10)
        
        # Cleanup
        handler.cleanup()
        
        assert handler.image_data is None
        assert len(handler.overlays) == 0
        assert len(handler.image_metadata) == 0


@pytest.mark.performance
class TestImageHandlerPerformance:
    """Test image handler performance requirements."""
    
    @pytest.mark.slow
    def test_large_image_loading_performance(self, qapp, large_test_image, performance_thresholds):
        """Test loading performance for large images."""
        handler = ImageHandler()
        
        # Track loading time
        start_time = time.time()
        loading_completed = {'done': False, 'error': None}
        
        def on_loaded(file_path):
            loading_completed['done'] = True
            loading_completed['load_time'] = time.time() - start_time
        
        def on_failed(error):
            loading_completed['done'] = True
            loading_completed['error'] = error
        
        handler.image_loaded.connect(on_loaded)
        handler.image_load_failed.connect(on_failed)
        
        # Start loading
        handler.load_image(str(large_test_image))
        
        # Wait for completion with generous timeout
        timeout = 30000  # 30 seconds
        start_wait = time.time()
        
        while not loading_completed['done']:
            qapp.processEvents()
            if (time.time() - start_wait) * 1000 > timeout:
                pytest.fail("Image loading timed out")
            time.sleep(0.01)
        
        # Verify performance requirement
        if loading_completed.get('error'):
            pytest.fail(f"Image loading failed: {loading_completed['error']}")
        
        load_time = loading_completed.get('load_time', float('inf'))
        
        # Get file size for scaled performance target
        file_size_mb = large_test_image.stat().st_size / (1024 * 1024)
        target_time = performance_thresholds['image_load_time_500mb'] * (file_size_mb / 500)
        
        # Allow some tolerance for test environment
        tolerance_factor = 2.0
        assert load_time <= target_time * tolerance_factor, \
            f"Image loading too slow: {load_time:.2f}s > {target_time * tolerance_factor:.2f}s for {file_size_mb:.1f}MB"
    
    def test_zoom_performance(self, qapp, sample_image_data):
        """Test zoom operation performance."""
        handler = ImageHandler()
        handler.image_data = sample_image_data
        
        # Test multiple zoom operations
        zoom_levels = [0.5, 1.0, 1.5, 2.0, 0.25, 4.0]
        
        start_time = time.time()
        
        for zoom in zoom_levels:
            handler.set_zoom(zoom)
            qapp.processEvents()  # Process any UI updates
        
        elapsed_time = time.time() - start_time
        
        # Should complete all zoom operations quickly
        assert elapsed_time < 1.0, f"Zoom operations too slow: {elapsed_time:.2f}s"
    
    def test_overlay_rendering_performance(self, qapp, sample_image_data):
        """Test overlay rendering performance."""
        handler = ImageHandler()
        handler.image_data = sample_image_data
        
        # Add many overlays
        num_overlays = 100
        start_time = time.time()
        
        for i in range(num_overlays):
            x = (i * 5) % (sample_image_data.shape[1] - 20)
            y = (i * 3) % (sample_image_data.shape[0] - 20)
            handler.add_overlay('rectangle', x, y, 10, 10, '#FF0000', 0.3)
        
        # Update display with all overlays
        handler._update_display()
        qapp.processEvents()
        
        elapsed_time = time.time() - start_time
        
        # Should handle 100 overlays quickly
        assert elapsed_time < 2.0, f"Overlay rendering too slow: {elapsed_time:.2f}s for {num_overlays} overlays"
    
    def test_memory_usage_large_image(self, qapp):
        """Test memory usage with large images."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / (1024 * 1024)  # MB
        
        handler = ImageHandler()
        
        # Create large image in memory (approximately 100MB)
        large_image = np.random.randint(0, 256, (4096, 4096, 3), dtype=np.uint8)
        handler.image_data = large_image
        handler._update_display()
        
        current_memory = process.memory_info().rss / (1024 * 1024)  # MB
        memory_increase = current_memory - initial_memory
        
        # Memory increase should be reasonable (less than 4x the image size)
        image_size_mb = large_image.nbytes / (1024 * 1024)
        max_acceptable_increase = image_size_mb * 4  # Allow 4x for Qt conversion overhead
        
        assert memory_increase < max_acceptable_increase, \
            f"Memory usage too high: {memory_increase:.1f}MB > {max_acceptable_increase:.1f}MB"
        
        # Cleanup
        handler.cleanup()


@pytest.mark.integration
class TestImageHandlerIntegration:
    """Test image handler integration with other components."""
    
    def test_error_handler_integration(self, qapp, temp_dir):
        """Test integration with error handling system."""
        handler = ImageHandler()
        
        # Mock error handler
        error_handler_mock = Mock()
        handler.error_handler = error_handler_mock
        
        # Try to load nonexistent file
        nonexistent_file = temp_dir / "nonexistent.jpg"
        
        error_occurred = {'error': None}
        
        def capture_error(error_msg):
            error_occurred['error'] = error_msg
        
        handler.image_load_failed.connect(capture_error)
        handler.load_image(str(nonexistent_file))
        
        # Wait for error
        start_time = time.time()
        while error_occurred['error'] is None and (time.time() - start_time) < 5:
            qapp.processEvents()
            time.sleep(0.01)
        
        assert error_occurred['error'] is not None
        assert "File not found" in error_occurred['error']
    
    def test_thread_safety(self, qapp, sample_tiff_file):
        """Test thread safety of image loading."""
        handler = ImageHandler()
        
        # Start multiple load operations (second should cancel first)
        handler.load_image(str(sample_tiff_file))
        
        # Immediately start another load
        handler.load_image(str(sample_tiff_file))
        
        # Should not crash or cause issues
        results = {'loaded': 0, 'failed': 0}
        
        def on_loaded(path):
            results['loaded'] += 1
        
        def on_failed(error):
            results['failed'] += 1
        
        handler.image_loaded.connect(on_loaded)
        handler.image_load_failed.connect(on_failed)
        
        # Wait for completion
        start_time = time.time()
        while (results['loaded'] + results['failed']) == 0 and (time.time() - start_time) < 10:
            qapp.processEvents()
            time.sleep(0.01)
        
        # Should have at least one result
        assert (results['loaded'] + results['failed']) > 0


def capture_error(error):
    pass  # Helper function for tests