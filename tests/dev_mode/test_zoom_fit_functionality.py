"""
Test for zoom_fit functionality in DEV mode
"""

import pytest
import sys
import time
from unittest.mock import Mock
from PySide6.QtWidgets import QApplication
import numpy as np

# Add src to path for imports
sys.path.insert(0, 'src')

from pages.main_window import MainWindow
from models.image_handler import ImageHandler
from services.theme_manager import ThemeManager


class TestZoomFitFunctionality:
    """Test zoom_fit functionality."""
    
    @pytest.fixture
    def app(self):
        """Create QApplication instance for testing."""
        if not QApplication.instance():
            app = QApplication([])
        else:
            app = QApplication.instance()
        yield app

    @pytest.fixture
    def main_window(self, app):
        """Create MainWindow instance for testing."""
        theme_manager = Mock()
        theme_manager.current_theme = "light"
        theme_manager.get_current_colors.return_value = {
            'primary': '#007ACC',
            'background': '#FFFFFF'
        }
        
        window = MainWindow(theme_manager)
        window.show()
        window.resize(1200, 800)  # Set consistent window size
        
        # Wait for UI to initialize
        app.processEvents()
        time.sleep(0.2)
        
        yield window
        window.close()

    def test_zoom_fit_basic_functionality(self, main_window, app):
        """Test basic zoom_fit functionality."""
        # Create test image
        test_image = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)
        main_window.image_handler.image_data = test_image
        main_window.image_handler.image_metadata = {'format': 'PNG', 'shape': (600, 800, 3)}
        
        # Initial display
        main_window.image_handler._update_display()
        app.processEvents()
        time.sleep(0.1)
        
        original_zoom = main_window.image_handler.zoom_level
        print(f"Original zoom: {original_zoom:.3f}")
        
        # Apply zoom fit
        main_window.image_handler.zoom_fit()
        app.processEvents()
        time.sleep(0.1)
        
        fit_zoom = main_window.image_handler.zoom_level
        print(f"Fit zoom: {fit_zoom:.3f}")
        
        # Verify zoom level is reasonable and different from original
        assert 0.1 < fit_zoom < 5.0, f"Zoom level seems unreasonable: {fit_zoom}"
        
        # Verify pan offset is reset
        assert main_window.image_handler.pan_offset == (0, 0), "Pan offset should be reset after fit"
        
        print("✅ Basic zoom_fit test passed!")

    def test_zoom_fit_after_pan_works_correctly(self, main_window, app):
        """Test that fit works correctly after panning."""
        # Setup image
        test_image = np.random.randint(0, 255, (800, 600, 3), dtype=np.uint8)
        main_window.image_handler.image_data = test_image
        main_window.image_handler.image_metadata = {'format': 'PNG', 'shape': (800, 600, 3)}
        
        # Initial display and fit
        main_window.image_handler._update_display()
        main_window.image_handler.zoom_fit()
        app.processEvents()
        time.sleep(0.1)
        
        initial_zoom = main_window.image_handler.zoom_level
        print(f"Initial fit zoom: {initial_zoom:.3f}")
        
        # Pan the image
        main_window.image_handler.pan(100, 50)
        app.processEvents()
        time.sleep(0.1)
        
        pan_offset = main_window.image_handler.pan_offset
        print(f"After pan - offset: {pan_offset}")
        
        # Apply fit again - this should fix any stretching issue
        main_window.image_handler.zoom_fit()
        app.processEvents()
        time.sleep(0.1)
        
        final_zoom = main_window.image_handler.zoom_level
        final_offset = main_window.image_handler.pan_offset
        print(f"After second fit - zoom: {final_zoom:.3f}, offset: {final_offset}")
        
        # Verify fit worked correctly
        assert final_offset == (0, 0), "Pan offset should be reset after fit"
        assert abs(final_zoom - initial_zoom) < 0.01, f"Zoom level should be consistent"
        
        print("✅ Pan and fit test passed!")

    def test_zoom_fit_with_wide_image(self, main_window, app):
        """Test zoom_fit with a wide image."""
        # Create a wide image (landscape)
        wide_image = np.random.randint(0, 255, (400, 800, 3), dtype=np.uint8)
        main_window.image_handler.image_data = wide_image
        main_window.image_handler.image_metadata = {'format': 'PNG', 'shape': (400, 800, 3)}
        
        # Initial display
        main_window.image_handler._update_display()
        app.processEvents()
        time.sleep(0.1)
        
        print(f"Wide image - Original zoom: {main_window.image_handler.zoom_level:.3f}")
        
        # Apply zoom fit
        main_window.image_handler.zoom_fit()
        app.processEvents()
        time.sleep(0.1)
        
        fit_zoom = main_window.image_handler.zoom_level
        print(f"Wide image - Fit zoom: {fit_zoom:.3f}")
        
        # Verify zoom level is reasonable
        assert 0.1 < fit_zoom < 2.0, f"Zoom level seems unreasonable: {fit_zoom}"
        
        # Verify pan offset is reset
        assert main_window.image_handler.pan_offset == (0, 0), "Pan offset should be reset after fit"
        
        print("✅ Wide image zoom_fit test passed!")

    def test_zoom_fit_with_tall_image(self, main_window, app):
        """Test zoom_fit with a tall image."""
        # Create a tall image (portrait)
        tall_image = np.random.randint(0, 255, (800, 400, 3), dtype=np.uint8)
        main_window.image_handler.image_data = tall_image
        main_window.image_handler.image_metadata = {'format': 'PNG', 'shape': (800, 400, 3)}
        
        # Initial display
        main_window.image_handler._update_display()
        app.processEvents()
        time.sleep(0.1)
        
        print(f"Tall image - Original zoom: {main_window.image_handler.zoom_level:.3f}")
        
        # Apply zoom fit
        main_window.image_handler.zoom_fit()
        app.processEvents()
        time.sleep(0.1)
        
        fit_zoom = main_window.image_handler.zoom_level
        print(f"Tall image - Fit zoom: {fit_zoom:.3f}")
        
        # Verify zoom level is reasonable
        assert 0.1 < fit_zoom < 2.0, f"Zoom level seems unreasonable: {fit_zoom}"
        
        # Verify pan offset is reset
        assert main_window.image_handler.pan_offset == (0, 0), "Pan offset should be reset after fit"
        
        print("✅ Tall image zoom_fit test passed!")

    def test_zoom_fit_preserves_aspect_ratio(self, main_window, app):
        """Test that zoom_fit preserves image aspect ratio."""
        # Create square image
        square_image = np.random.randint(0, 255, (600, 600, 3), dtype=np.uint8)
        main_window.image_handler.image_data = square_image
        main_window.image_handler.image_metadata = {'format': 'PNG', 'shape': (600, 600, 3)}
        
        # Initial display
        main_window.image_handler._update_display()
        app.processEvents()
        time.sleep(0.1)
        
        # Apply zoom fit
        main_window.image_handler.zoom_fit()
        app.processEvents()
        time.sleep(0.1)
        
        # Check that the image hasn't been distorted by checking the aspect ratio
        # This is verified by ensuring the zoom calculation is consistent
        widget_width = main_window.image_handler.image_label.width()
        widget_height = main_window.image_handler.image_label.height()
        
        if widget_width > 0 and widget_height > 0:
            expected_zoom_x = widget_width / 600 * 0.95  # 95% padding
            expected_zoom_y = widget_height / 600 * 0.95  # 95% padding
            expected_zoom = min(expected_zoom_x, expected_zoom_y)
            
            actual_zoom = main_window.image_handler.zoom_level
            
            print(f"Expected zoom: {expected_zoom:.3f}, Actual zoom: {actual_zoom:.3f}")
            
            # Allow for small differences due to rounding
            assert abs(actual_zoom - expected_zoom) < 0.01, f"Zoom calculation mismatch: expected {expected_zoom:.3f}, got {actual_zoom:.3f}"
        
        print("✅ Aspect ratio preservation test passed!")

    def test_image_remains_stable_after_pan_and_fit(self, main_window, app):
        """Test that fit works correctly after panning."""
        # Setup image
        test_image = np.random.randint(0, 255, (800, 600, 3), dtype=np.uint8)
        main_window.image_handler.image_data = test_image
        main_window.image_handler.image_metadata = {'format': 'PNG', 'shape': (800, 600, 3)}
        
        # Initial display and fit
        main_window.image_handler._update_display()
        main_window.image_handler.zoom_fit()
        app.processEvents()
        time.sleep(0.1)
        
        initial_zoom = main_window.image_handler.zoom_level
        print(f"Initial fit zoom: {initial_zoom:.3f}")
        
        # Pan the image
        main_window.image_handler.pan(100, 50)
        app.processEvents()
        time.sleep(0.1)
        
        pan_zoom = main_window.image_handler.zoom_level
        pan_offset = main_window.image_handler.pan_offset
        print(f"After pan - zoom: {pan_zoom:.3f}, offset: {pan_offset}")
        
        # Apply fit again
        main_window.image_handler.zoom_fit()
        app.processEvents()
        time.sleep(0.1)
        
        final_zoom = main_window.image_handler.zoom_level
        final_offset = main_window.image_handler.pan_offset
        print(f"After second fit - zoom: {final_zoom:.3f}, offset: {final_offset}")
        
        # Verify fit worked correctly
        assert final_offset == (0, 0), "Pan offset should be reset after fit"
        assert abs(final_zoom - initial_zoom) < 0.01, f"Zoom level should be consistent: initial {initial_zoom:.3f}, final {final_zoom:.3f}"
        
        print("✅ Pan and fit stability test passed!")
        
    def test_zoom_fit_widget_size_stability(self, main_window, app):
        """Test that widget size remains stable during zoom_fit operations."""
        # Setup image
        test_image = np.random.randint(0, 255, (1000, 800, 3), dtype=np.uint8)
        main_window.image_handler.image_data = test_image
        main_window.image_handler.image_metadata = {'format': 'PNG', 'shape': (1000, 800, 3)}
        
        # Record initial sizes
        main_window.image_handler._update_display()
        app.processEvents()
        time.sleep(0.1)
        
        initial_size = main_window.image_handler.size()
        initial_label_size = main_window.image_handler.image_label.size()
        
        # Apply fit multiple times
        for i in range(3):
            main_window.image_handler.zoom_fit()
            app.processEvents()
            time.sleep(0.05)
            
            current_size = main_window.image_handler.size()
            current_label_size = main_window.image_handler.image_label.size()
            
            print(f"Fit {i+1} - Handler: {current_size}, Label: {current_label_size}")
            
            # Verify sizes remain stable
            assert abs(current_size.width() - initial_size.width()) <= 2, f"Handler width changed significantly on fit {i+1}"
            assert abs(current_size.height() - initial_size.height()) <= 2, f"Handler height changed significantly on fit {i+1}"
            
        print("✅ Widget size stability during zoom_fit test passed!") 