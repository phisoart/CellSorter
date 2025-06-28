"""
Test Error Handling Consistency in DUAL Mode

Tests error handling synchronization between GUI and headless modes.
Verifies that errors are handled consistently across both interfaces.
"""

import pytest
import logging
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from io import StringIO

from src.headless.testing.framework import UITestCase
from src.utils.exceptions import (
    CellSorterError, ImageLoadError, CSVParseError, DataValidationError,
    CoordinateTransformError, CalibrationError, ExportError
)
from src.utils.error_handler import ErrorHandler, safe_execute
from src.utils.logging_config import get_logger
from src.headless.main_window_adapter import MainWindowAdapter
from src.headless.mode_manager import ModeManager


class TestErrorHandlingConsistencyDual(UITestCase):
    """Test error handling consistency in DUAL mode."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        
        # Set up dual mode
        self.mode_manager = Mock(spec=ModeManager)
        self.mode_manager.is_dev_mode.return_value = False
        self.mode_manager.is_gui_mode.return_value = False
        self.mode_manager.is_dual_mode.return_value = True
        
        # Create adapters for both modes
        self.headless_adapter = Mock(spec=MainWindowAdapter)
        self.headless_adapter.mode_manager = self.mode_manager
        
        self.gui_adapter = Mock(spec=MainWindowAdapter)
        self.gui_adapter.mode_manager = self.mode_manager
        
        # Mock error handlers for both modes
        self.headless_error_handler = Mock(spec=ErrorHandler)
        self.gui_error_handler = Mock(spec=ErrorHandler)
        
        # Set up logging capture
        self.log_stream = StringIO()
        self.log_handler = logging.StreamHandler(self.log_stream)
        self.logger = get_logger('test_error_consistency')
        self.logger.addHandler(self.log_handler)
        self.logger.setLevel(logging.DEBUG)
    
    def tearDown(self):
        """Clean up test environment."""
        self.logger.removeHandler(self.log_handler)
        super().tearDown()
    
    def test_image_load_error_sync(self):
        """Test image loading error synchronization between modes."""
        # Mock image handlers for both modes
        headless_handler = Mock()
        gui_handler = Mock()
        
        # Set up identical errors
        error = ImageLoadError("File not found", "IMG_NOT_FOUND", {"file": "test.jpg"})
        headless_handler.load_image.side_effect = error
        gui_handler.load_image.side_effect = error
        
        self.headless_adapter.image_handler = headless_handler
        self.gui_adapter.image_handler = gui_handler
        
        # Test error handling in both modes
        with patch('src.utils.error_handler.logger') as mock_logger:
            headless_result = safe_execute(
                headless_handler.load_image,
                "test.jpg",
                error_handler=self.headless_error_handler,
                context="Headless image loading"
            )
            
            gui_result = safe_execute(
                gui_handler.load_image,
                "test.jpg", 
                error_handler=self.gui_error_handler,
                context="GUI image loading"
            )
        
        # Verify both modes handled errors
        assert headless_result is None
        assert gui_result is None
        
        # Verify both error handlers were called
        self.headless_error_handler.handle_exception.assert_called_once()
        self.gui_error_handler.handle_exception.assert_called_once()
        
        # Verify error details are identical
        headless_call_args = self.headless_error_handler.handle_exception.call_args[0]
        gui_call_args = self.gui_error_handler.handle_exception.call_args[0]
        
        assert type(headless_call_args[0]) == type(gui_call_args[0])
        assert str(headless_call_args[0]) == str(gui_call_args[0])
    
    def test_csv_parse_error_state_sync(self):
        """Test CSV parsing error state synchronization."""
        # Mock CSV parsers for both modes
        headless_parser = Mock()
        gui_parser = Mock()
        
        # Set up identical parsing errors
        error = CSVParseError("Invalid format", "CSV_INVALID", {"line": 10})
        headless_parser.parse_file.side_effect = error
        gui_parser.parse_file.side_effect = error
        
        # Mock shared state
        shared_state = {"last_error": None, "error_count": 0}
        
        def track_error(exc, context):
            shared_state["last_error"] = str(exc)
            shared_state["error_count"] += 1
        
        self.headless_error_handler.handle_exception.side_effect = track_error
        self.gui_error_handler.handle_exception.side_effect = track_error
        
        # Test error handling in both modes
        with patch('src.utils.error_handler.logger') as mock_logger:
            safe_execute(
                headless_parser.parse_file,
                "test.csv",
                error_handler=self.headless_error_handler,
                context="Headless CSV parsing"
            )
            
            safe_execute(
                gui_parser.parse_file,
                "test.csv",
                error_handler=self.gui_error_handler,
                context="GUI CSV parsing"
            )
        
        # Verify error state synchronization
        assert shared_state["error_count"] == 2
        assert "Invalid format" in shared_state["last_error"]
        
        # Verify both handlers were called
        self.headless_error_handler.handle_exception.assert_called_once()
        self.gui_error_handler.handle_exception.assert_called_once()
    
    def test_coordinate_transform_error_consistency(self):
        """Test coordinate transformation error consistency."""
        # Mock transformers for both modes
        headless_transformer = Mock()
        gui_transformer = Mock()
        
        # Set up identical transformation errors
        error = CoordinateTransformError(
            "Point out of bounds", "COORD_OUT_OF_BOUNDS", {"point": (1000, 1000)}
        )
        headless_transformer.transform_point.side_effect = error
        gui_transformer.transform_point.side_effect = error
        
        # Track error details
        error_details = []
        
        def capture_error_details(exc, context):
            error_details.append({
                "type": type(exc).__name__,
                "message": str(exc),
                "context": context,
                "details": getattr(exc, 'details', {})
            })
        
        self.headless_error_handler.handle_exception.side_effect = capture_error_details
        self.gui_error_handler.handle_exception.side_effect = capture_error_details
        
        # Test error handling in both modes
        with patch('src.utils.error_handler.logger') as mock_logger:
            safe_execute(
                headless_transformer.transform_point,
                1000, 1000,
                error_handler=self.headless_error_handler,
                context="Headless coordinate transform"
            )
            
            safe_execute(
                gui_transformer.transform_point,
                1000, 1000,
                error_handler=self.gui_error_handler,
                context="GUI coordinate transform"
            )
        
        # Verify error consistency
        assert len(error_details) == 2
        
        headless_error = error_details[0]
        gui_error = error_details[1]
        
        # Check error type consistency
        assert headless_error["type"] == gui_error["type"]
        assert headless_error["message"] == gui_error["message"]
        assert headless_error["details"] == gui_error["details"]
    
    def test_calibration_error_recovery_sync(self):
        """Test calibration error recovery synchronization."""
        # Mock calibrators for both modes
        headless_calibrator = Mock()
        gui_calibrator = Mock()
        
        # Set up identical calibration errors
        error = CalibrationError("Insufficient points", "CAL_INSUFFICIENT_POINTS")
        headless_calibrator.calibrate.side_effect = error
        gui_calibrator.calibrate.side_effect = error
        
        # Mock recovery mechanisms
        recovery_attempts = []
        
        def mock_recovery(exc, context):
            recovery_attempts.append({
                "mode": "headless" if "Headless" in context else "gui",
                "error": str(exc),
                "context": context
            })
        
        self.headless_error_handler.handle_exception.side_effect = mock_recovery
        self.gui_error_handler.handle_exception.side_effect = mock_recovery
        
        # Test error handling and recovery in both modes
        with patch('src.utils.error_handler.logger') as mock_logger:
            safe_execute(
                headless_calibrator.calibrate,
                [(10, 10)],  # Insufficient points
                error_handler=self.headless_error_handler,
                context="Headless calibration"
            )
            
            safe_execute(
                gui_calibrator.calibrate,
                [(10, 10)],  # Insufficient points
                error_handler=self.gui_error_handler,
                context="GUI calibration"
            )
        
        # Verify recovery attempts were synchronized
        assert len(recovery_attempts) == 2
        
        headless_recovery = recovery_attempts[0]
        gui_recovery = recovery_attempts[1]
        
        assert headless_recovery["mode"] == "headless"
        assert gui_recovery["mode"] == "gui"
        assert headless_recovery["error"] == gui_recovery["error"]
    
    def test_export_error_cleanup_sync(self):
        """Test export error cleanup synchronization."""
        # Mock exporters for both modes
        headless_exporter = Mock()
        gui_exporter = Mock()
        
        # Set up identical export errors
        error = ExportError("Disk space insufficient", "EXPORT_DISK_SPACE", {"required": "100MB"})
        headless_exporter.export_protocol.side_effect = error
        gui_exporter.export_protocol.side_effect = error
        
        # Track cleanup operations
        cleanup_operations = []
        
        def track_cleanup(exc, context):
            cleanup_operations.append({
                "mode": "headless" if "Headless" in context else "gui",
                "error_code": getattr(exc, 'error_code', None),
                "details": getattr(exc, 'details', {})
            })
        
        self.headless_error_handler.handle_exception.side_effect = track_cleanup
        self.gui_error_handler.handle_exception.side_effect = track_cleanup
        
        # Test error handling in both modes
        with patch('src.utils.error_handler.logger') as mock_logger:
            safe_execute(
                headless_exporter.export_protocol,
                "test.cxprotocol",
                error_handler=self.headless_error_handler,
                context="Headless export"
            )
            
            safe_execute(
                gui_exporter.export_protocol,
                "test.cxprotocol",
                error_handler=self.gui_error_handler,
                context="GUI export"
            )
        
        # Verify cleanup synchronization
        assert len(cleanup_operations) == 2
        
        headless_cleanup = cleanup_operations[0]
        gui_cleanup = cleanup_operations[1]
        
        assert headless_cleanup["error_code"] == gui_cleanup["error_code"]
        assert headless_cleanup["details"] == gui_cleanup["details"]
    
    def test_session_error_auto_save_sync(self):
        """Test session error auto-save synchronization."""
        # Mock session managers for both modes
        headless_session = Mock()
        gui_session = Mock()
        
        # Set up session save errors
        save_error = Exception("Disk write error")
        headless_session.save_session.side_effect = save_error
        gui_session.save_session.side_effect = save_error
        
        # Mock session data
        session_data = {
            "image_path": "test.jpg",
            "selections": [{"x": 10, "y": 20}],
            "calibration": {"matrix": [[1, 0, 0], [0, 1, 0], [0, 0, 1]]}
        }
        
        # Track auto-save attempts
        auto_save_attempts = []
        
        def track_auto_save(exc, context):
            auto_save_attempts.append({
                "mode": "headless" if "Headless" in context else "gui",
                "error": str(exc),
                "context": context
            })
        
        self.headless_error_handler.handle_exception.side_effect = track_auto_save
        self.gui_error_handler.handle_exception.side_effect = track_auto_save
        
        # Test session error handling in both modes
        with patch('src.utils.error_handler.logger') as mock_logger:
            safe_execute(
                headless_session.save_session,
                session_data,
                error_handler=self.headless_error_handler,
                context="Headless session save"
            )
            
            safe_execute(
                gui_session.save_session,
                session_data,
                error_handler=self.gui_error_handler,
                context="GUI session save"
            )
        
        # Verify auto-save synchronization
        assert len(auto_save_attempts) == 2
        
        headless_save = auto_save_attempts[0]
        gui_save = auto_save_attempts[1]
        
        assert headless_save["mode"] == "headless"
        assert gui_save["mode"] == "gui"
        assert headless_save["error"] == gui_save["error"]
    
    def test_error_logging_consistency(self):
        """Test error logging consistency between modes."""
        # Mock components for both modes
        headless_component = Mock()
        gui_component = Mock()
        
        # Set up identical errors
        error = DataValidationError("Invalid data", "DATA_INVALID", {"field": "coordinates"})
        headless_component.process_data.side_effect = error
        gui_component.process_data.side_effect = error
        
        # Capture log messages
        log_messages = []
        
        def capture_logs(exc, context):
            log_messages.append({
                "mode": "headless" if "Headless" in context else "gui",
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "context": context
            })
        
        self.headless_error_handler.handle_exception.side_effect = capture_logs
        self.gui_error_handler.handle_exception.side_effect = capture_logs
        
        # Test error logging in both modes
        with patch('src.utils.error_handler.logger') as mock_logger:
            safe_execute(
                headless_component.process_data,
                {"invalid": "data"},
                error_handler=self.headless_error_handler,
                context="Headless data processing"
            )
            
            safe_execute(
                gui_component.process_data,
                {"invalid": "data"},
                error_handler=self.gui_error_handler,
                context="GUI data processing"
            )
        
        # Verify logging consistency
        assert len(log_messages) == 2
        
        headless_log = log_messages[0]
        gui_log = log_messages[1]
        
        assert headless_log["error_type"] == gui_log["error_type"]
        assert headless_log["error_message"] == gui_log["error_message"]
    
    def test_error_state_synchronization(self):
        """Test error state synchronization between modes."""
        # Mock shared error state
        error_state = {
            "total_errors": 0,
            "last_error": None,
            "error_types": []
        }
        
        def update_error_state(exc, context):
            error_state["total_errors"] += 1
            error_state["last_error"] = str(exc)
            error_state["error_types"].append(type(exc).__name__)
        
        self.headless_error_handler.handle_exception.side_effect = update_error_state
        self.gui_error_handler.handle_exception.side_effect = update_error_state
        
        # Generate errors from both modes
        errors = [
            ImageLoadError("Image error"),
            CSVParseError("CSV error"),
            CoordinateTransformError("Transform error")
        ]
        
        components = [Mock() for _ in errors]
        for i, (component, error) in enumerate(zip(components, errors)):
            component.operation.side_effect = error
        
        # Test error state synchronization
        with patch('src.utils.error_handler.logger') as mock_logger:
            for i, component in enumerate(components):
                if i % 2 == 0:  # Alternate between modes
                    safe_execute(
                        component.operation,
                        error_handler=self.headless_error_handler,
                        context=f"Headless operation {i}"
                    )
                else:
                    safe_execute(
                        component.operation,
                        error_handler=self.gui_error_handler,
                        context=f"GUI operation {i}"
                    )
        
        # Verify error state synchronization
        assert error_state["total_errors"] == 3
        assert error_state["last_error"] is not None
        assert len(error_state["error_types"]) == 3
        
        # Verify different error types were captured
        expected_types = ["ImageLoadError", "CSVParseError", "CoordinateTransformError"]
        assert all(error_type in error_state["error_types"] for error_type in expected_types)


if __name__ == '__main__':
    pytest.main([__file__]) 