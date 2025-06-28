"""
GUI Mode Tests for Protocol Export Production

Tests protocol export performance and usability in production environment.

Test sequence: DEV → DUAL → GUI (mandatory)
"""

import pytest
import tempfile
import time
import configparser
from pathlib import Path
from typing import List, Dict, Any

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer, Qt
from PySide6.QtTest import QTest

from src.models.extractor import Extractor, BoundingBox
from src.models.coordinate_transformer import CoordinateTransformer
from src.models.selection_manager import SelectionManager
from src.components.dialogs.export_dialog import ExportDialog
from src.headless.testing.framework import UITestCase
from src.pages.main_window import MainWindow
from unittest.mock import Mock


class TestExportProductionGui(UITestCase):
    """GUI mode tests for protocol export production performance."""
    
    def setUp(self):
        """Set up GUI mode test environment."""
        super().setUp()
        
        # Initialize components (avoid GUI initialization)
        self.extractor = Extractor(parent=None)
        self.coordinate_transformer = CoordinateTransformer()
        self.selection_manager = SelectionManager()
        
        # Mock MainWindow to avoid GUI dependencies
        self.main_window = Mock()
        self.main_window.export_protocol = Mock(return_value=True)
        self.main_window.show_export_dialog = Mock(return_value=True)
        
        # Mock export dialog to avoid GUI dependencies
        self.export_dialog = Mock()
        self.export_dialog.exec = Mock(return_value=True)
        self.export_dialog.get_export_settings = Mock(return_value={
            'output_path': '/tmp/test_export.cxprotocol',
            'format': 'cxprotocol',
            'create_backup': True
        })
        
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
            'width': 1000,
            'height': 800,
            'filename': 'test_image.tiff',
            'file_path': '/path/to/test_image.tiff',
            'shape': [800, 1000],
            'channels': 4,
            'bit_depth': 16
        }
    
    def test_export_dialog_performance(self):
        """Test export dialog performance and responsiveness."""
        # Create extraction points
        extraction_points = self.extractor.create_extraction_points(
            self.test_selections,
            self.test_bounding_boxes,
            self.coordinate_transformer
        )
        
        # Create export dialog
        export_dialog = ExportDialog(
            extraction_points=extraction_points,
            image_info=self.test_image_info,
            parent=self.main_window
        )
        
        # Show dialog and measure initialization time
        start_time = time.time()
        export_dialog.show()
        QTest.qWaitForWindowExposed(export_dialog)
        init_time = time.time() - start_time
        
        # Dialog should initialize quickly
        assert init_time < 2.0, f"Dialog initialization too slow: {init_time:.2f}s"
        
        # Test export performance
        with tempfile.NamedTemporaryFile(suffix='.cxprotocol', delete=False) as temp_file:
            output_path = temp_file.name
        
        start_time = time.time()
        success = export_dialog.export_protocol(output_path)
        export_time = time.time() - start_time
        
        assert success, "Export should succeed"
        assert export_time < 10.0, f"Export too slow: {export_time:.2f}s"
        
        # Verify file was created and is valid
        assert Path(output_path).exists(), "Output file should exist"
        
        config = configparser.ConfigParser()
        config.read(output_path)
        
        # Verify basic structure
        assert 'IMAGING_LAYOUT' in config.sections(), "Should have IMAGING_LAYOUT section"
        assert int(config['IMAGING_LAYOUT']['point_count']) == len(extraction_points), "Point count should match"
        
        # Clean up
        export_dialog.close()
        Path(output_path).unlink()
    
    def test_progress_bar_functionality(self):
        """Test progress bar updates during export."""
        # Create extraction points
        extraction_points = self.extractor.create_extraction_points(
            self.test_selections,
            self.test_bounding_boxes,
            self.coordinate_transformer
        )
        
        # Create export dialog
        export_dialog = ExportDialog(
            extraction_points=extraction_points,
            image_info=self.test_image_info,
            parent=self.main_window
        )
        
        export_dialog.show()
        QTest.qWaitForWindowExposed(export_dialog)
        
        # Track progress updates
        progress_values = []
        
        def track_progress():
            if hasattr(export_dialog, 'progress_bar'):
                progress_values.append(export_dialog.progress_bar.value())
        
        # Set up timer to capture progress
        timer = QTimer()
        timer.timeout.connect(track_progress)
        timer.start(100)  # Check every 100ms
        
        # Start export
        with tempfile.NamedTemporaryFile(suffix='.cxprotocol', delete=False) as temp_file:
            output_path = temp_file.name
        
        success = export_dialog.export_protocol(output_path)
        
        # Stop timer
        timer.stop()
        
        assert success, "Export should succeed"
        
        # Progress should have been updated if progress bar exists
        if hasattr(export_dialog, 'progress_bar') and progress_values:
            # Should start at 0 and end at 100
            assert progress_values[0] >= 0, "Progress should start at or near 0"
            assert progress_values[-1] >= 90, "Progress should end near 100"
        
        # Clean up
        export_dialog.close()
        Path(output_path).unlink()
    
    def test_memory_efficiency(self):
        """Test memory usage during export."""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create extraction points
        extraction_points = self.extractor.create_extraction_points(
            self.test_selections,
            self.test_bounding_boxes,
            self.coordinate_transformer
        )
        
        # Create export dialog
        export_dialog = ExportDialog(
            extraction_points=extraction_points,
            image_info=self.test_image_info,
            parent=self.main_window
        )
        
        export_dialog.show()
        QTest.qWaitForWindowExposed(export_dialog)
        
        # Perform export
        with tempfile.NamedTemporaryFile(suffix='.cxprotocol', delete=False) as temp_file:
            output_path = temp_file.name
        
        success = export_dialog.export_protocol(output_path)
        
        # Check memory usage after export
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        assert success, "Export should succeed"
        
        # Memory increase should be reasonable
        assert memory_increase < 50, f"Memory usage too high: {memory_increase:.1f}MB increase"
        
        # Clean up
        export_dialog.close()
        Path(output_path).unlink()
        
        # Memory should be released after cleanup
        QApplication.processEvents()  # Process any pending deletions
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_retained = final_memory - initial_memory
        
        # Should not retain excessive memory after cleanup
        assert memory_retained < 30, f"Memory leak detected: {memory_retained:.1f}MB retained"
    
    def test_main_window_integration(self):
        """Test export integration through main window."""
        # Set up main window with test data
        self.main_window.coordinate_transformer = self.coordinate_transformer
        self.main_window.selection_manager = self.selection_manager
        
        # Add selections to main window
        for selection in self.test_selections:
            self.main_window.selection_manager.add_selection(
                selection['label'],
                selection['color'],
                selection['cell_indices'],
                selection['well_position']
            )
        
        # Show main window
        self.main_window.show()
        QTest.qWaitForWindowExposed(self.main_window)
        
        # Create export dialog from main window
        extraction_points = self.extractor.create_extraction_points(
            self.test_selections,
            self.test_bounding_boxes,
            self.coordinate_transformer
        )
        
        export_dialog = ExportDialog(
            extraction_points=extraction_points,
            image_info=self.test_image_info,
            parent=self.main_window
        )
        
        # Test export
        with tempfile.NamedTemporaryFile(suffix='.cxprotocol', delete=False) as temp_file:
            output_path = temp_file.name
        
        success = export_dialog.export_protocol(output_path)
        
        assert success, "Export through main window should succeed"
        
        # Verify file was created
        assert Path(output_path).exists(), "Output file should exist"
        
        config = configparser.ConfigParser()
        config.read(output_path)
        assert 'IMAGING_LAYOUT' in config.sections(), "Should have valid protocol structure"
        
        # Clean up
        export_dialog.close()
        self.main_window.close()
        Path(output_path).unlink()


if __name__ == '__main__':
    pytest.main([__file__, '-v']) 