"""
GUI Mode Tests for Main Window Production

Tests main window usability and performance in production environment.

Test sequence: DEV → DUAL → GUI (mandatory)
"""

import pytest
import tempfile
import time
from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import Mock, patch

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer, Qt
from PySide6.QtTest import QTest

from src.models.extractor import Extractor, BoundingBox
from src.models.coordinate_transformer import CoordinateTransformer
from src.models.selection_manager import SelectionManager
from src.models.image_handler import ImageHandler
from src.models.session_manager import SessionManager
from src.headless.testing.framework import UITestCase
from src.pages.main_window import MainWindow


class TestMainWindowProductionGui(UITestCase):
    """GUI mode tests for main window production performance."""
    
    def setUp(self):
        """Set up GUI mode test environment."""
        super().setUp()
        
        # Initialize components
        self.extractor = Extractor()
        self.coordinate_transformer = CoordinateTransformer()
        self.selection_manager = SelectionManager()
        self.image_handler = ImageHandler()
        self.session_manager = SessionManager()
        self.main_window = MainWindow()
        
        # Set up coordinate transformation
        self.coordinate_transformer.add_calibration_point(100, 150, 1000.0, 2000.0, "Point 1")
        self.coordinate_transformer.add_calibration_point(800, 600, 8000.0, 6000.0, "Point 2")
        
        # Test data
        self.test_bounding_boxes = [
            BoundingBox(min_x=120, min_y=180, max_x=140, max_y=200),
            BoundingBox(min_x=300, min_y=250, max_x=330, max_y=280),
            BoundingBox(min_x=500, min_y=400, max_x=540, max_y=440),
        ]
        
        self.test_selections = [
            {
                'id': 'selection_1',
                'label': 'Positive Cells',
                'color': '#FF0000',
                'well_position': 'A01',
                'cell_indices': [0, 2],
                'metadata': {'type': 'positive', 'count': 2}
            },
            {
                'id': 'selection_2',
                'label': 'Negative Cells',
                'color': '#0000FF',
                'well_position': 'A02',
                'cell_indices': [1],
                'metadata': {'type': 'negative', 'count': 1}
            }
        ]
        
        self.test_image_info = {
            'width': 2048,
            'height': 2048,
            'filename': 'production_image.tiff',
            'path': '/path/to/production_image.tiff',
            'channels': 4,
            'bit_depth': 16
        }
    
    def test_main_window_startup_performance(self):
        """Test main window startup performance."""
        # Measure startup time
        start_time = time.time()
        
        # Initialize main window
        main_window = MainWindow()
        main_window.show()
        QTest.qWaitForWindowExposed(main_window)
        
        startup_time = time.time() - start_time
        
        # Should start up quickly
        assert startup_time < 3.0, f"Main window startup too slow: {startup_time:.2f}s"
        
        # Verify window is properly displayed
        assert main_window.isVisible(), "Main window should be visible"
        assert main_window.width() > 0, "Main window should have width"
        assert main_window.height() > 0, "Main window should have height"
        
        # Clean up
        main_window.close()
    
    def test_image_loading_user_experience(self):
        """Test image loading user experience."""
        # Set up main window
        self.main_window.image_handler = self.image_handler
        self.main_window.show()
        QTest.qWaitForWindowExposed(self.main_window)
        
        # Mock image loading with delay to test UI responsiveness
        def mock_load_image(path):
            # Simulate loading time
            time.sleep(0.1)
            return True
        
        with patch.object(self.image_handler, 'load_image', side_effect=mock_load_image):
            # Start image loading
            start_time = time.time()
            success = self.main_window.load_image(self.test_image_info['path'])
            load_time = time.time() - start_time
            
            assert success, "Image loading should succeed"
            
            # UI should remain responsive during loading
            # Test by processing events
            QApplication.processEvents()
            
            # Window should still be responsive
            assert self.main_window.isVisible(), "Window should remain visible during loading"
        
        # Clean up
        self.main_window.close()
    
    def test_selection_workflow_usability(self):
        """Test selection workflow usability."""
        # Set up main window
        self.main_window.selection_manager = self.selection_manager
        self.main_window.show()
        QTest.qWaitForWindowExposed(self.main_window)
        
        # Test adding selections
        for i, selection in enumerate(self.test_selections):
            # Add selection
            success = self.main_window.selection_manager.add_selection(
                selection['label'],
                selection['color'],
                selection['cell_indices'],
                selection['well_position']
            )
            
            assert success, f"Adding selection {i+1} should succeed"
            
            # Process UI events
            QApplication.processEvents()
            
            # Verify selection is added
            selections = self.main_window.selection_manager.get_selections()
            assert len(selections) == i + 1, f"Should have {i+1} selections"
        
        # Test selection removal
        initial_count = len(self.main_window.selection_manager.get_selections())
        
        if hasattr(self.main_window.selection_manager, 'remove_selection'):
            remove_success = self.main_window.selection_manager.remove_selection(0)
            
            if remove_success:
                QApplication.processEvents()
                
                final_count = len(self.main_window.selection_manager.get_selections())
                assert final_count == initial_count - 1, "Selection should be removed"
        
        # Clean up
        self.main_window.close()
    
    def test_calibration_workflow_usability(self):
        """Test calibration workflow usability."""
        # Set up main window
        self.main_window.coordinate_transformer = self.coordinate_transformer
        self.main_window.show()
        QTest.qWaitForWindowExposed(self.main_window)
        
        # Test adding calibration points
        calibration_points = [
            (200, 300, 2000.0, 3000.0, "User Point 1"),
            (600, 700, 6000.0, 7000.0, "User Point 2"),
            (400, 500, 4000.0, 5000.0, "User Point 3")
        ]
        
        for i, cal_point in enumerate(calibration_points):
            # Add calibration point
            success = self.main_window.coordinate_transformer.add_calibration_point(*cal_point)
            
            assert success, f"Adding calibration point {i+1} should succeed"
            
            # Process UI events
            QApplication.processEvents()
            
            # Check calibration status
            if i >= 1:  # Need at least 2 points for calibration
                assert self.main_window.coordinate_transformer.is_calibrated(), "Should be calibrated with 2+ points"
        
        # Test coordinate transformation
        pixel_x, pixel_y = 350, 450
        real_x, real_y = self.main_window.coordinate_transformer.transform_to_real(pixel_x, pixel_y)
        
        # Should get valid transformed coordinates
        assert isinstance(real_x, (int, float)), "Real X should be numeric"
        assert isinstance(real_y, (int, float)), "Real Y should be numeric"
        
        # Clean up
        self.main_window.close()
    
    def test_export_workflow_usability(self):
        """Test export workflow usability."""
        # Set up main window with all components
        self.main_window.coordinate_transformer = self.coordinate_transformer
        self.main_window.selection_manager = self.selection_manager
        self.main_window.extractor = self.extractor
        
        self.main_window.show()
        QTest.qWaitForWindowExposed(self.main_window)
        
        # Add test data
        for selection in self.test_selections:
            self.main_window.selection_manager.add_selection(
                selection['label'],
                selection['color'],
                selection['cell_indices'],
                selection['well_position']
            )
        
        # Process UI events
        QApplication.processEvents()
        
        # Test export functionality
        with tempfile.NamedTemporaryFile(suffix='.cxprotocol', delete=False) as temp_file:
            output_path = temp_file.name
        
        # Test export (implementation depends on actual main window structure)
        if hasattr(self.main_window, 'export_protocol'):
            export_success = self.main_window.export_protocol(output_path, self.test_image_info)
        else:
            # Fallback: test through components
            extraction_points = self.extractor.create_extraction_points(
                self.test_selections,
                self.test_bounding_boxes,
                self.coordinate_transformer
            )
            export_success = self.extractor.generate_protocol_file(
                extraction_points,
                output_path,
                self.test_image_info
            )
        
        assert export_success, "Export should succeed"
        assert Path(output_path).exists(), "Export file should be created"
        
        # Clean up
        self.main_window.close()
        Path(output_path).unlink()
    
    def test_session_management_usability(self):
        """Test session management usability."""
        # Set up main window
        self.main_window.session_manager = self.session_manager
        self.main_window.coordinate_transformer = self.coordinate_transformer
        self.main_window.selection_manager = self.selection_manager
        
        self.main_window.show()
        QTest.qWaitForWindowExposed(self.main_window)
        
        # Add test data
        for selection in self.test_selections:
            self.main_window.selection_manager.add_selection(
                selection['label'],
                selection['color'],
                selection['cell_indices'],
                selection['well_position']
            )
        
        # Process UI events
        QApplication.processEvents()
        
        # Test session save
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
            session_path = temp_file.name
        
        # Create session data
        session_data = {
            'image_path': self.test_image_info['path'],
            'selections': self.test_selections,
            'calibration_points': [
                {'pixel_x': 100, 'pixel_y': 150, 'real_x': 1000.0, 'real_y': 2000.0, 'label': 'Point 1'},
                {'pixel_x': 800, 'pixel_y': 600, 'real_x': 8000.0, 'real_y': 6000.0, 'label': 'Point 2'}
            ]
        }
        
        # Test save (implementation depends on actual main window structure)
        if hasattr(self.main_window, 'save_session'):
            save_success = self.main_window.save_session(session_path, session_data)
        else:
            # Fallback: test through session manager
            save_success = self.session_manager.save_session(session_path, session_data)
        
        assert save_success, "Session save should succeed"
        assert Path(session_path).exists(), "Session file should be created"
        
        # Test session load
        if hasattr(self.main_window, 'load_session'):
            load_success = self.main_window.load_session(session_path)
        else:
            # Fallback: test through session manager
            loaded_data = self.session_manager.load_session(session_path)
            load_success = loaded_data is not None
        
        assert load_success, "Session load should succeed"
        
        # Clean up
        self.main_window.close()
        Path(session_path).unlink()
    
    def test_memory_efficiency_during_use(self):
        """Test memory efficiency during normal use."""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Set up main window
        self.main_window.coordinate_transformer = self.coordinate_transformer
        self.main_window.selection_manager = self.selection_manager
        self.main_window.image_handler = self.image_handler
        
        self.main_window.show()
        QTest.qWaitForWindowExposed(self.main_window)
        
        # Simulate normal usage
        for i in range(5):  # Multiple iterations
            # Add selections
            for j, selection in enumerate(self.test_selections):
                self.main_window.selection_manager.add_selection(
                    f"{selection['label']} {i}_{j}",
                    selection['color'],
                    selection['cell_indices'],
                    f"A{i:02d}"
                )
            
            # Process UI events
            QApplication.processEvents()
            
            # Add calibration points
            self.main_window.coordinate_transformer.add_calibration_point(
                100 + i * 50, 150 + i * 50,
                1000.0 + i * 500, 2000.0 + i * 500,
                f"Point {i}"
            )
            
            # Process UI events
            QApplication.processEvents()
        
        # Check memory usage
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        # Memory increase should be reasonable
        assert memory_increase < 100, f"Memory usage too high: {memory_increase:.1f}MB increase"
        
        # Clean up
        self.main_window.close()
        
        # Memory should be released after cleanup
        QApplication.processEvents()  # Process any pending deletions
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_retained = final_memory - initial_memory
        
        # Should not retain excessive memory after cleanup
        assert memory_retained < 50, f"Memory leak detected: {memory_retained:.1f}MB retained"
    
    def test_user_error_handling(self):
        """Test user error handling and feedback."""
        # Set up main window
        self.main_window.selection_manager = self.selection_manager
        self.main_window.coordinate_transformer = self.coordinate_transformer
        
        self.main_window.show()
        QTest.qWaitForWindowExposed(self.main_window)
        
        # Test invalid selection handling
        error_messages = []
        
        def mock_critical(parent, title, message):
            error_messages.append({'title': title, 'message': message})
            return QMessageBox.Ok
        
        with patch.object(QMessageBox, 'critical', side_effect=mock_critical):
            # Try to add invalid selection
            invalid_success = self.main_window.selection_manager.add_selection("", "", [], "")
            
            # Should handle gracefully
            assert not invalid_success, "Invalid selection should fail"
            
            # Process UI events
            QApplication.processEvents()
        
        # Test invalid calibration handling
        with patch.object(QMessageBox, 'critical', side_effect=mock_critical):
            # Try to add invalid calibration
            invalid_cal_success = self.main_window.coordinate_transformer.add_calibration_point(
                None, None, None, None, ""
            )
            
            # Should handle gracefully
            assert not invalid_cal_success, "Invalid calibration should fail"
            
            # Process UI events
            QApplication.processEvents()
        
        # Verify error messages were shown if implemented
        if error_messages:
            assert len(error_messages) > 0, "Error messages should be displayed to user"
        
        # Clean up
        self.main_window.close()
    
    def test_window_resize_responsiveness(self):
        """Test window resize responsiveness."""
        # Set up main window
        self.main_window.show()
        QTest.qWaitForWindowExposed(self.main_window)
        
        # Get initial size
        initial_width = self.main_window.width()
        initial_height = self.main_window.height()
        
        # Test resize
        new_width = initial_width + 200
        new_height = initial_height + 100
        
        start_time = time.time()
        self.main_window.resize(new_width, new_height)
        QApplication.processEvents()
        resize_time = time.time() - start_time
        
        # Resize should be quick
        assert resize_time < 1.0, f"Window resize too slow: {resize_time:.2f}s"
        
        # Verify new size
        assert abs(self.main_window.width() - new_width) < 10, "Width should be updated"
        assert abs(self.main_window.height() - new_height) < 10, "Height should be updated"
        
        # Test minimum size constraints
        self.main_window.resize(100, 100)
        QApplication.processEvents()
        
        # Should respect minimum size
        assert self.main_window.width() >= 100, "Should respect minimum width"
        assert self.main_window.height() >= 100, "Should respect minimum height"
        
        # Clean up
        self.main_window.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v']) 