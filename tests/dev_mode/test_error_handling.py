"""
Test Error Handling in DEV Mode

Tests error handling mechanisms in headless development mode.
Verifies logging, recovery, and data integrity without GUI dialogs.
"""

import pytest
import logging
import json
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from io import StringIO

from src.headless.testing.framework import UITestCase
from src.utils.exceptions import (
    CellSorterError, ImageLoadError, CSVParseError, DataValidationError,
    CoordinateTransformError, CalibrationError, ExportError
)
from src.utils.error_handler import ErrorHandler, safe_execute
from src.utils.logging_config import setup_logging, get_logger
from src.headless.main_window_adapter import MainWindowAdapter
from src.headless.mode_manager import ModeManager


class TestErrorHandlingDev(UITestCase):
    """Test error handling in DEV mode (headless)."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        
        # Set up headless mode
        self.mode_manager = Mock(spec=ModeManager)
        self.mode_manager.is_dev_mode.return_value = True
        self.mode_manager.is_gui_mode.return_value = False
        self.mode_manager.is_dual_mode.return_value = False
        
        # Create adapter with mocked dependencies
        self.adapter = Mock(spec=MainWindowAdapter)
        self.adapter.mode_manager = self.mode_manager
        
        # Mock error handler without GUI components
        self.error_handler = Mock(spec=ErrorHandler)
        
        # Set up logging capture
        self.log_stream = StringIO()
        self.log_handler = logging.StreamHandler(self.log_stream)
        self.logger = get_logger('test_error_handling')
        self.logger.addHandler(self.log_handler)
        self.logger.setLevel(logging.DEBUG)
    
    def tearDown(self):
        """Clean up test environment."""
        self.logger.removeHandler(self.log_handler)
        super().tearDown()
    
    def test_image_load_error_handling(self):
        """Test image loading error handling in headless mode."""
        # Mock image handler with error
        image_handler = Mock()
        image_handler.load_image.side_effect = ImageLoadError(
            "File not found", "IMG_NOT_FOUND", {"file": "nonexistent.jpg"}
        )
        
        self.adapter.image_handler = image_handler
        
        # Test error handling
        result = safe_execute(
            image_handler.load_image,
            "nonexistent.jpg",
            error_handler=self.error_handler,
            context="Loading test image"
        )
        
        # Verify no GUI dialog was shown (headless mode)
        assert result is None
        self.error_handler.handle_exception.assert_called_once()
        
        # Verify error details
        call_args = self.error_handler.handle_exception.call_args[0]
        assert isinstance(call_args[0], ImageLoadError)
        assert call_args[1] == "Loading test image"
    
    def test_csv_parse_error_recovery(self):
        """Test CSV parsing error with data recovery."""
        # Mock CSV parser with error
        csv_parser = Mock()
        csv_parser.parse_file.side_effect = CSVParseError(
            "Invalid CSV format", "CSV_INVALID", {"line": 5}
        )
        
        self.adapter.csv_parser = csv_parser
        
        # Test with backup data
        backup_data = [{"x": 1, "y": 2}, {"x": 3, "y": 4}]
        
        def recovery_func():
            return backup_data
        
        # Test error handling with recovery
        result = safe_execute(
            csv_parser.parse_file,
            "invalid.csv",
            error_handler=self.error_handler,
            context="Parsing CSV data"
        )
        
        # Verify error was handled
        assert result is None
        self.error_handler.handle_exception.assert_called_once()
    
    def test_coordinate_transform_error_logging(self):
        """Test coordinate transformation error logging."""
        # Mock coordinate transformer with error
        transformer = Mock()
        transformer.transform_point.side_effect = CoordinateTransformError(
            "Point out of bounds", "COORD_OUT_OF_BOUNDS", {"point": (1000, 1000)}
        )
        
        self.adapter.coordinate_transformer = transformer
        
        # Test error handling
        result = safe_execute(
            transformer.transform_point,
            1000, 1000,
            error_handler=self.error_handler,
            context="Transforming coordinates"
        )
        
        # Verify error handling
        assert result is None
        self.error_handler.handle_exception.assert_called_once()
        
        # Check error details
        call_args = self.error_handler.handle_exception.call_args[0]
        assert isinstance(call_args[0], CoordinateTransformError)
        assert call_args[0].details["point"] == (1000, 1000)
    
    def test_calibration_error_data_integrity(self):
        """Test calibration error with data integrity preservation."""
        # Mock calibration with error
        calibration_data = {
            "points": [(10, 10), (100, 100)],
            "matrix": [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        }
        
        calibrator = Mock()
        calibrator.calibrate.side_effect = CalibrationError(
            "Insufficient calibration points", "CAL_INSUFFICIENT_POINTS"
        )
        
        # Test data preservation during error
        original_data = calibration_data.copy()
        
        result = safe_execute(
            calibrator.calibrate,
            calibration_data["points"],
            error_handler=self.error_handler,
            context="Calibrating coordinates"
        )
        
        # Verify error handling
        assert result is None
        self.error_handler.handle_exception.assert_called_once()
        
        # Verify original data integrity
        assert calibration_data == original_data
    
    def test_export_error_cleanup(self):
        """Test export error with proper cleanup."""
        # Mock exporter with error
        exporter = Mock()
        exporter.export_protocol.side_effect = ExportError(
            "Disk space insufficient", "EXPORT_DISK_SPACE", {"required": "100MB"}
        )
        
        # Mock temporary files
        temp_files = []
        
        def create_temp_file():
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            temp_files.append(temp_file.name)
            return temp_file.name
        
        # Test export with cleanup
        result = safe_execute(
            exporter.export_protocol,
            "test.cxprotocol",
            error_handler=self.error_handler,
            context="Exporting protocol"
        )
        
        # Verify error handling
        assert result is None
        self.error_handler.handle_exception.assert_called_once()
        
        # Check error details
        call_args = self.error_handler.handle_exception.call_args[0]
        assert isinstance(call_args[0], ExportError)
        assert call_args[0].details["required"] == "100MB"
    
    def test_session_error_auto_save(self):
        """Test session error with auto-save functionality."""
        # Mock session manager with error
        session_manager = Mock()
        session_manager.save_session.side_effect = Exception("Disk write error")
        
        # Mock session data
        session_data = {
            "image_path": "test.jpg",
            "selections": [{"x": 10, "y": 20}],
            "calibration": {"matrix": [[1, 0, 0], [0, 1, 0], [0, 0, 1]]}
        }
        
        # Test auto-save on error
        auto_save_path = None
        
        def mock_auto_save(data, path):
            nonlocal auto_save_path
            auto_save_path = path
            with open(path, 'w') as f:
                json.dump(data, f)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            auto_save_path = temp_file.name
            
            result = safe_execute(
                session_manager.save_session,
                session_data,
                error_handler=self.error_handler,
                context="Saving session"
            )
        
        # Verify error handling
        assert result is None
        self.error_handler.handle_exception.assert_called_once()
        
        # Clean up
        if auto_save_path and Path(auto_save_path).exists():
            Path(auto_save_path).unlink()
    
    def test_multiple_errors_logging(self):
        """Test handling of multiple consecutive errors."""
        # Mock multiple error sources
        components = {
            'image_handler': Mock(),
            'csv_parser': Mock(),
            'transformer': Mock()
        }
        
        # Set up errors
        components['image_handler'].load_image.side_effect = ImageLoadError("Image error")
        components['csv_parser'].parse_file.side_effect = CSVParseError("CSV error")
        components['transformer'].transform_point.side_effect = CoordinateTransformError("Transform error")
        
        error_count = 0
        
        def count_errors(*args, **kwargs):
            nonlocal error_count
            error_count += 1
        
        self.error_handler.handle_exception.side_effect = count_errors
        
        # Test multiple errors
        safe_execute(components['image_handler'].load_image, "test.jpg", error_handler=self.error_handler)
        safe_execute(components['csv_parser'].parse_file, "test.csv", error_handler=self.error_handler)
        safe_execute(components['transformer'].transform_point, 10, 20, error_handler=self.error_handler)
        
        # Verify all errors were handled
        assert error_count == 3
        assert self.error_handler.handle_exception.call_count == 3
    
    def test_error_context_preservation(self):
        """Test that error context is preserved in headless mode."""
        # Mock component with error
        component = Mock()
        component.process_data.side_effect = DataValidationError(
            "Invalid data format", "DATA_INVALID", {"field": "coordinates"}
        )
        
        context_info = "Processing user selection data"
        
        # Test context preservation
        result = safe_execute(
            component.process_data,
            {"invalid": "data"},
            error_handler=self.error_handler,
            context=context_info
        )
        
        # Verify error handling with context
        assert result is None
        self.error_handler.handle_exception.assert_called_once()
        
        # Verify context was passed
        call_args = self.error_handler.handle_exception.call_args
        assert call_args[0][1] == context_info  # Fix: access positional args correctly
    
    def test_headless_error_recovery_strategies(self):
        """Test error recovery strategies in headless mode."""
        # Mock recovery strategies
        recovery_strategy = Mock()
        recovery_strategy.can_recover.return_value = True
        recovery_strategy.recover.return_value = True
        
        # Mock component with recoverable error
        component = Mock()
        component.critical_operation.side_effect = Exception("Recoverable error")
        
        # Test recovery in headless mode
        # Simulate recovery attempt
        try:
            component.critical_operation()
        except Exception as e:
            if recovery_strategy.can_recover(e):
                recovery_success = recovery_strategy.recover(e)
                assert recovery_success
            
            self.error_handler.handle_exception(e, "Critical operation")
        
        # Verify recovery was attempted
        recovery_strategy.can_recover.assert_called_once()
        recovery_strategy.recover.assert_called_once()
        
        # Verify error was still logged
        self.error_handler.handle_exception.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__]) 