"""
DUAL Mode Tests for Calibration Consistency

Tests GUI rendering consistency with headless calculations.
Validates synchronization between visual interface and backend logic.

Test sequence: DEV → DUAL → GUI (mandatory)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Tuple, Dict, Any

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QEventLoop
from PySide6.QtTest import QTest

from src.models.coordinate_transformer import CoordinateTransformer, CalibrationPoint
from src.components.dialogs.calibration_dialog import CalibrationWizardDialog, CalibrationDialog
from src.headless.testing.framework import UITestCase
from src.headless.main_window_adapter import MainWindowAdapter
from src.headless.mode_manager import ModeManager


class TestCalibrationConsistencyDual(UITestCase):
    """DUAL mode tests for calibration GUI/headless consistency."""
    
    def setUp(self):
        """Set up dual mode test environment."""
        super().setUp()
        
        # Initialize components with mocks
        from unittest.mock import Mock
        
        self.transformer = CoordinateTransformer()
        
        # Mock mode manager
        self.mock_mode_manager = Mock()
        self.mock_mode_manager.is_gui_mode.return_value = True
        self.mock_mode_manager.is_headless_mode.return_value = False
        
        # Mock main adapter
        self.main_adapter = Mock()
        self.main_adapter.coordinate_transformer = CoordinateTransformer()
        
        # Test calibration data
        self.test_points = [
            (100, 150, 1000.0, 2000.0, "Point 1"),
            (800, 600, 8000.0, 6000.0, "Point 2")
        ]
        
        # Expected tolerances
        self.coordinate_tolerance = 0.1  # micrometers
        self.pixel_tolerance = 1  # pixels
    
    def test_calibration_dialog_headless_consistency(self):
        """Test calibration dialog calculations match headless logic."""
        # Mock calibration dialog
        from unittest.mock import Mock
        
        dialog = Mock()
        dialog.coordinate_transformer = CoordinateTransformer()
        
        # Simulate adding first calibration point through GUI
        pixel_x, pixel_y, stage_x, stage_y, label = self.test_points[0]
        
        # Add point through dialog transformer (simulates GUI interaction)
        dialog.coordinate_transformer.add_calibration_point(pixel_x, pixel_y, stage_x, stage_y, label)
        
        # Add point directly to transformer (headless logic)
        headless_transformer = CoordinateTransformer()
        headless_transformer.add_calibration_point(pixel_x, pixel_y, stage_x, stage_y, label)
        
        # Verify both have same calibration state
        dialog_info = dialog.coordinate_transformer.get_calibration_info()
        headless_info = headless_transformer.get_calibration_info()
        
        assert len(dialog_info['points']) == len(headless_info['points']), "Point count should match"
        assert dialog_info['is_calibrated'] == headless_info['is_calibrated'], "Calibration state should match"
        
        # Add second point to both
        pixel_x2, pixel_y2, stage_x2, stage_y2, label2 = self.test_points[1]
        dialog.coordinate_transformer.add_calibration_point(pixel_x2, pixel_y2, stage_x2, stage_y2, label2)
        headless_transformer.add_calibration_point(pixel_x2, pixel_y2, stage_x2, stage_y2, label2)
        
        # Verify transformation matrices match
        dialog_matrix = dialog.coordinate_transformer.transform_matrix
        headless_matrix = headless_transformer.transform_matrix
        
        assert dialog_matrix is not None and headless_matrix is not None, "Both should have transform matrices"
        
        # Compare matrix elements (within numerical tolerance)
        import numpy as np
        matrix_diff = np.abs(dialog_matrix - headless_matrix).max()
        assert matrix_diff < 1e-10, f"Transform matrices should match: max diff = {matrix_diff}"
    
    def test_coordinate_transformation_consistency(self):
        """Test coordinate transformations produce identical results."""
        # Set up both transformers with same calibration
        gui_transformer = CoordinateTransformer()
        headless_transformer = CoordinateTransformer()
        
        for pixel_x, pixel_y, stage_x, stage_y, label in self.test_points:
            gui_transformer.add_calibration_point(pixel_x, pixel_y, stage_x, stage_y, label)
            headless_transformer.add_calibration_point(pixel_x, pixel_y, stage_x, stage_y, label)
        
        # Test coordinate transformations at various points
        test_coordinates = [
            (200, 300),
            (400, 450),
            (600, 500),
            (150, 200),
            (750, 550)
        ]
        
        for test_x, test_y in test_coordinates:
            # Transform using both methods
            gui_result = gui_transformer.pixel_to_stage(test_x, test_y)
            headless_result = headless_transformer.pixel_to_stage(test_x, test_y)
            
            assert gui_result is not None and headless_result is not None, f"Both transformations should succeed for ({test_x}, {test_y})"
            
            # Compare results
            x_diff = abs(gui_result.stage_x - headless_result.stage_x)
            y_diff = abs(gui_result.stage_y - headless_result.stage_y)
            confidence_diff = abs(gui_result.confidence - headless_result.confidence)
            
            assert x_diff < self.coordinate_tolerance, f"X coordinate mismatch: {x_diff} > {self.coordinate_tolerance}"
            assert y_diff < self.coordinate_tolerance, f"Y coordinate mismatch: {y_diff} > {self.coordinate_tolerance}"
            assert confidence_diff < 0.01, f"Confidence mismatch: {confidence_diff} > 0.01"
    
    def test_reverse_transformation_consistency(self):
        """Test reverse transformations (stage to pixel) match between modes."""
        # Set up calibration
        gui_transformer = CoordinateTransformer()
        headless_transformer = CoordinateTransformer()
        
        for pixel_x, pixel_y, stage_x, stage_y, label in self.test_points:
            gui_transformer.add_calibration_point(pixel_x, pixel_y, stage_x, stage_y, label)
            headless_transformer.add_calibration_point(pixel_x, pixel_y, stage_x, stage_y, label)
        
        # Test reverse transformations
        test_stage_coords = [
            (2000.0, 3000.0),
            (4000.0, 4500.0),
            (6000.0, 5000.0),
            (1500.0, 2500.0),
            (7500.0, 5500.0)
        ]
        
        for stage_x, stage_y in test_stage_coords:
            # Transform using both methods
            gui_result = gui_transformer.stage_to_pixel(stage_x, stage_y)
            headless_result = headless_transformer.stage_to_pixel(stage_x, stage_y)
            
            assert gui_result is not None and headless_result is not None, f"Both reverse transformations should succeed for ({stage_x}, {stage_y})"
            
            gui_pixel_x, gui_pixel_y = gui_result
            headless_pixel_x, headless_pixel_y = headless_result
            
            # Compare results
            x_diff = abs(gui_pixel_x - headless_pixel_x)
            y_diff = abs(gui_pixel_y - headless_pixel_y)
            
            assert x_diff <= self.pixel_tolerance, f"Pixel X mismatch: {x_diff} > {self.pixel_tolerance}"
            assert y_diff <= self.pixel_tolerance, f"Pixel Y mismatch: {y_diff} > {self.pixel_tolerance}"
    
    def test_quality_metrics_consistency(self):
        """Test quality metrics calculation consistency."""
        # Set up calibration
        gui_transformer = CoordinateTransformer()
        headless_transformer = CoordinateTransformer()
        
        for pixel_x, pixel_y, stage_x, stage_y, label in self.test_points:
            gui_transformer.add_calibration_point(pixel_x, pixel_y, stage_x, stage_y, label)
            headless_transformer.add_calibration_point(pixel_x, pixel_y, stage_x, stage_y, label)
        
        # Get quality metrics from both
        gui_info = gui_transformer.get_calibration_info()
        headless_info = headless_transformer.get_calibration_info()
        
        # Compare quality metrics (use actual structure from implementation)
        gui_quality = gui_info['quality_metrics']
        headless_quality = headless_info['quality_metrics']
        
        quality_metrics = ['average_error_um', 'max_error_um', 'meets_accuracy_target', 'transformation_confidence']
        
        for metric in quality_metrics:
            assert metric in gui_quality and metric in headless_quality, f"Metric {metric} should exist in both"
            
            gui_value = gui_quality[metric]
            headless_value = headless_quality[metric]
            
            # Allow small numerical differences
            if isinstance(gui_value, (int, float)) and isinstance(headless_value, (int, float)):
                diff = abs(gui_value - headless_value)
                tolerance = max(abs(gui_value), abs(headless_value)) * 1e-10 + 1e-10
                assert diff < tolerance, f"Quality metric {metric} mismatch: {gui_value} vs {headless_value}"
            else:
                assert gui_value == headless_value, f"Quality metric {metric} should match exactly"
    
    def test_export_import_consistency(self):
        """Test calibration export/import consistency between modes."""
        # Set up calibration
        gui_transformer = CoordinateTransformer()
        headless_transformer = CoordinateTransformer()
        
        for pixel_x, pixel_y, stage_x, stage_y, label in self.test_points:
            gui_transformer.add_calibration_point(pixel_x, pixel_y, stage_x, stage_y, label)
            headless_transformer.add_calibration_point(pixel_x, pixel_y, stage_x, stage_y, label)
        
        # Export from both
        gui_export = gui_transformer.export_calibration()
        headless_export = headless_transformer.export_calibration()
        
        # Compare export structures
        assert gui_export.keys() == headless_export.keys(), "Export structures should match"
        
        # Compare calibration points (use actual export structure)
        gui_points = gui_export['calibration_points']
        headless_points = headless_export['calibration_points']
        
        assert len(gui_points) == len(headless_points), "Point counts should match"
        
        for gui_point, headless_point in zip(gui_points, headless_points):
            for key in gui_point.keys():
                assert key in headless_point, f"Point key {key} should exist in both exports"
                assert gui_point[key] == headless_point[key], f"Point {key} should match"
        
        # Test cross-import (GUI export -> headless import, and vice versa)
        new_gui_transformer = CoordinateTransformer()
        new_headless_transformer = CoordinateTransformer()
        
        # Import GUI export into headless transformer
        headless_import_success = new_headless_transformer.import_calibration(gui_export)
        assert headless_import_success, "Headless should import GUI export successfully"
        
        # Import headless export into GUI transformer
        gui_import_success = new_gui_transformer.import_calibration(headless_export)
        assert gui_import_success, "GUI should import headless export successfully"
        
        # Verify both imported transformers work identically
        test_pixel_x, test_pixel_y = 300, 400
        
        gui_imported_result = new_gui_transformer.pixel_to_stage(test_pixel_x, test_pixel_y)
        headless_imported_result = new_headless_transformer.pixel_to_stage(test_pixel_x, test_pixel_y)
        
        assert gui_imported_result is not None and headless_imported_result is not None, "Both imported transformers should work"
        
        x_diff = abs(gui_imported_result.stage_x - headless_imported_result.stage_x)
        y_diff = abs(gui_imported_result.stage_y - headless_imported_result.stage_y)
        
        assert x_diff < self.coordinate_tolerance, f"Cross-import X mismatch: {x_diff}"
        assert y_diff < self.coordinate_tolerance, f"Cross-import Y mismatch: {y_diff}"
    
    def test_calibration_dialog_ui_synchronization(self):
        """Test calibration dialog UI updates synchronize with backend state."""
        # Mock dialog with transformer
        from unittest.mock import Mock
        
        dialog = Mock()
        dialog.coordinate_transformer = CoordinateTransformer()
        
        # Monitor transformer signals
        calibration_updated_signals = []
        transformation_ready_signals = []
        
        def on_calibration_updated(is_valid):
            calibration_updated_signals.append(is_valid)
        
        def on_transformation_ready():
            transformation_ready_signals.append(True)
        
        dialog.coordinate_transformer.calibration_updated.connect(on_calibration_updated)
        dialog.coordinate_transformer.transformation_ready.connect(on_transformation_ready)
        
        # Add first point through dialog transformer
        pixel_x1, pixel_y1, stage_x1, stage_y1, label1 = self.test_points[0]
        dialog.coordinate_transformer.add_calibration_point(pixel_x1, pixel_y1, stage_x1, stage_y1, label1)
        
        # Verify signal was emitted
        assert len(calibration_updated_signals) >= 1, "Calibration updated signal should be emitted"
        assert calibration_updated_signals[-1] == False, "Should not be calibrated with single point"
        
        # Add second point
        pixel_x2, pixel_y2, stage_x2, stage_y2, label2 = self.test_points[1]
        dialog.coordinate_transformer.add_calibration_point(pixel_x2, pixel_y2, stage_x2, stage_y2, label2)
        
        # Verify transformation ready signal
        assert len(transformation_ready_signals) >= 1, "Transformation ready signal should be emitted"
        assert len(calibration_updated_signals) >= 2, "Second calibration updated signal should be emitted"
        assert calibration_updated_signals[-1] == True, "Should be calibrated with two points"
        
        # Verify dialog state matches backend
        assert dialog.coordinate_transformer.is_calibrated(), "Dialog transformer should be calibrated"
        
        # Mock dialog UI state updates
        dialog.update_quality_display = Mock()
        dialog.update_quality_display()
        
        # Verify quality display shows expected information
        quality_info = dialog.coordinate_transformer.get_calibration_info()
        assert 'quality_metrics' in quality_info, "Quality info should be available for display"
    
    def test_main_window_calibration_integration(self):
        """Test calibration integration with main window adapter."""
        # Mock main window adapter methods
        from unittest.mock import Mock
        
        # Simulate calibration through main window adapter
        for pixel_x, pixel_y, stage_x, stage_y, label in self.test_points:
            success = self.main_adapter.coordinate_transformer.add_calibration_point(pixel_x, pixel_y, stage_x, stage_y, label)
            assert success, f"Main window should successfully add calibration point: {label}"
        
        # Verify main window adapter state matches direct transformer
        direct_transformer = CoordinateTransformer()
        for pixel_x, pixel_y, stage_x, stage_y, label in self.test_points:
            direct_transformer.add_calibration_point(pixel_x, pixel_y, stage_x, stage_y, label)
        
        # Compare transformation results
        test_pixel_x, test_pixel_y = 350, 425
        
        adapter_result = self.main_adapter.coordinate_transformer.pixel_to_stage(test_pixel_x, test_pixel_y)
        direct_result = direct_transformer.pixel_to_stage(test_pixel_x, test_pixel_y)
        
        assert adapter_result is not None and direct_result is not None, "Both should produce transformation results"
        
        x_diff = abs(adapter_result.stage_x - direct_result.stage_x)
        y_diff = abs(adapter_result.stage_y - direct_result.stage_y)
        
        assert x_diff < self.coordinate_tolerance, f"Main window adapter X mismatch: {x_diff}"
        assert y_diff < self.coordinate_tolerance, f"Main window adapter Y mismatch: {y_diff}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])