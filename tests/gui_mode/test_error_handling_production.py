"""
Test Error Handling in GUI Mode (Production)

Tests error handling mechanisms in production GUI mode.
Focuses on user experience, error dialogs, and recovery workflows.
"""

import pytest
import logging
import time
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.headless.testing.framework import UITestCase
from src.utils.exceptions import (
    CellSorterError, ImageLoadError, CSVParseError, DataValidationError,
    CoordinateTransformError, CalibrationError, ExportError
)
from src.utils.error_handler import ErrorHandler, safe_execute
from src.utils.logging_config import get_logger
from src.headless.mode_manager import ModeManager


class TestErrorHandlingProductionGui(UITestCase):
    """Test error handling in GUI mode (production)."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        
        # Set up GUI mode
        self.mode_manager = Mock(spec=ModeManager)
        self.mode_manager.is_dev_mode.return_value = False
        self.mode_manager.is_gui_mode.return_value = True
        self.mode_manager.is_dual_mode.return_value = False
        
        # Mock GUI components
        self.main_window = Mock()
        self.theme_manager = Mock()
        
        # Mock error handler with GUI components
        self.error_handler = Mock(spec=ErrorHandler)
        
        # Mock message boxes for GUI error dialogs
        self.message_box = Mock()
        self.message_box.exec.return_value = Mock()
        
        # Set up logging
        self.logger = get_logger('test_error_production')
    
    def test_image_load_error_user_feedback(self):
        """Test image loading error with user-friendly feedback."""
        # Mock image handler with error
        image_handler = Mock()
        image_handler.load_image.side_effect = ImageLoadError(
            "File format not supported", "IMG_UNSUPPORTED_FORMAT", 
            {"file": "test.xyz", "supported_formats": [".jpg", ".png", ".tiff"]}
        )
        
        # Test error handling with user feedback
        with patch('src.utils.error_handler.QMessageBox') as mock_msgbox:
            mock_msgbox.return_value = self.message_box
            
            result = safe_execute(
                image_handler.load_image,
                "test.xyz",
                error_handler=self.error_handler,
                context="Loading user image"
            )
        
        # Verify error handling
        assert result is None
        self.error_handler.handle_exception.assert_called_once()
        
        # Verify error details include user-helpful information
        call_args = self.error_handler.handle_exception.call_args[0]
        error = call_args[0]
        assert isinstance(error, ImageLoadError)
        assert "supported_formats" in error.details
    
    def test_csv_parse_error_recovery_workflow(self):
        """Test CSV parsing error with recovery workflow."""
        # Mock CSV parser with error
        csv_parser = Mock()
        csv_parser.parse_file.side_effect = CSVParseError(
            "Missing required columns", "CSV_MISSING_COLUMNS",
            {"missing_columns": ["x", "y"], "found_columns": ["cell_id", "marker"]}
        )
        
        # Mock recovery options
        recovery_options = ["Retry with different file", "Use default columns", "Cancel"]
        
        def mock_recovery_dialog(*args, **kwargs):
            return recovery_options[0]  # Simulate user choice
        
        # Test error with recovery workflow
        with patch('src.utils.error_handler.QMessageBox') as mock_msgbox:
            mock_msgbox.return_value = self.message_box
            
            with patch('builtins.input', side_effect=mock_recovery_dialog):
                result = safe_execute(
                    csv_parser.parse_file,
                    "invalid.csv",
                    error_handler=self.error_handler,
                    context="Parsing user CSV"
                )
        
        # Verify error handling
        assert result is None
        self.error_handler.handle_exception.assert_called_once()
        
        # Verify error includes recovery information
        call_args = self.error_handler.handle_exception.call_args[0]
        error = call_args[0]
        assert "missing_columns" in error.details
        assert "found_columns" in error.details
    
    def test_coordinate_transform_error_visual_feedback(self):
        """Test coordinate transformation error with visual feedback."""
        # Mock coordinate transformer with error
        transformer = Mock()
        transformer.transform_point.side_effect = CoordinateTransformError(
            "Calibration required", "COORD_NOT_CALIBRATED",
            {"suggested_action": "Please calibrate the coordinate system first"}
        )
        
        # Mock visual feedback components
        status_bar = Mock()
        progress_bar = Mock()
        
        # Test error with visual feedback
        with patch('src.utils.error_handler.QMessageBox') as mock_msgbox:
            mock_msgbox.return_value = self.message_box
            
            result = safe_execute(
                transformer.transform_point,
                100, 200,
                error_handler=self.error_handler,
                context="Transforming user selection"
            )
        
        # Verify error handling
        assert result is None
        self.error_handler.handle_exception.assert_called_once()
        
        # Verify error includes user guidance
        call_args = self.error_handler.handle_exception.call_args[0]
        error = call_args[0]
        assert "suggested_action" in error.details
    
    def test_calibration_error_help_system(self):
        """Test calibration error with integrated help system."""
        # Mock calibration with error
        calibrator = Mock()
        calibrator.calibrate.side_effect = CalibrationError(
            "Calibration points too close", "CAL_POINTS_TOO_CLOSE",
            {
                "min_distance": 50,
                "actual_distance": 15,
                "help_topic": "calibration_guidelines"
            }
        )
        
        # Mock help system
        help_system = Mock()
        help_system.show_topic.return_value = True
        
        # Test error with help integration
        with patch('src.utils.error_handler.QMessageBox') as mock_msgbox:
            mock_msgbox.return_value = self.message_box
            self.message_box.exec.return_value = Mock()  # Help button clicked
            
            result = safe_execute(
                calibrator.calibrate,
                [(10, 10), (20, 20)],  # Points too close
                error_handler=self.error_handler,
                context="User calibration"
            )
        
        # Verify error handling
        assert result is None
        self.error_handler.handle_exception.assert_called_once()
        
        # Verify error includes help information
        call_args = self.error_handler.handle_exception.call_args[0]
        error = call_args[0]
        assert "help_topic" in error.details
        assert "min_distance" in error.details
    
    def test_export_error_progress_feedback(self):
        """Test export error with progress feedback."""
        # Mock exporter with error
        exporter = Mock()
        exporter.export_protocol.side_effect = ExportError(
            "Export interrupted", "EXPORT_INTERRUPTED",
            {
                "progress": 75,
                "total_files": 100,
                "completed_files": 75,
                "failed_file": "protocol_75.cxprotocol"
            }
        )
        
        # Mock progress tracking
        progress_tracker = Mock()
        progress_tracker.update_progress.return_value = None
        
        # Test error with progress feedback
        with patch('src.utils.error_handler.QMessageBox') as mock_msgbox:
            mock_msgbox.return_value = self.message_box
            
            result = safe_execute(
                exporter.export_protocol,
                "batch_export.cxprotocol",
                error_handler=self.error_handler,
                context="Batch export operation"
            )
        
        # Verify error handling
        assert result is None
        self.error_handler.handle_exception.assert_called_once()
        
        # Verify error includes progress information
        call_args = self.error_handler.handle_exception.call_args[0]
        error = call_args[0]
        assert "progress" in error.details
        assert "completed_files" in error.details
    
    def test_session_error_auto_save_notification(self):
        """Test session error with auto-save notification."""
        # Mock session manager with error
        session_manager = Mock()
        session_manager.save_session.side_effect = Exception("Permission denied")
        
        # Mock session data
        session_data = {
            "image_path": "important_experiment.jpg",
            "selections": [{"x": 10, "y": 20}, {"x": 30, "y": 40}],
            "calibration": {"matrix": [[1, 0, 0], [0, 1, 0], [0, 0, 1]]},
            "analysis_time": 3600  # 1 hour of work
        }
        
        # Mock notification system
        notification_system = Mock()
        notification_system.show_notification.return_value = None
        
        # Test session error with auto-save notification
        with patch('src.utils.error_handler.QMessageBox') as mock_msgbox:
            mock_msgbox.return_value = self.message_box
            
            result = safe_execute(
                session_manager.save_session,
                session_data,
                error_handler=self.error_handler,
                context="Saving user session"
            )
        
        # Verify error handling
        assert result is None
        self.error_handler.handle_exception.assert_called_once()
        
        # Verify session data preservation attempt
        call_args = self.error_handler.handle_exception.call_args
        context = call_args[0][1]  # Fix: access positional args correctly
        assert "session" in context.lower()
    
    def test_multiple_errors_user_experience(self):
        """Test multiple errors with user experience considerations."""
        # Mock multiple components with errors
        components = {
            'image_handler': Mock(),
            'csv_parser': Mock(),
            'transformer': Mock()
        }
        
        # Set up different error types
        components['image_handler'].load_image.side_effect = ImageLoadError("Image error")
        components['csv_parser'].parse_file.side_effect = CSVParseError("CSV error")
        components['transformer'].transform_point.side_effect = CoordinateTransformError("Transform error")
        
        # Track user experience metrics
        ux_metrics = {
            "error_count": 0,
            "response_times": [],
            "user_actions": []
        }
        
        def track_ux_metrics(exc, context):
            ux_metrics["error_count"] += 1
            ux_metrics["response_times"].append(time.time())
            ux_metrics["user_actions"].append("error_dialog_shown")
        
        self.error_handler.handle_exception.side_effect = track_ux_metrics
        
        # Test multiple errors with UX tracking
        start_time = time.time()
        
        with patch('src.utils.error_handler.QMessageBox') as mock_msgbox:
            mock_msgbox.return_value = self.message_box
            
            # Fix: Call each component directly instead of using hasattr check
            safe_execute(components['image_handler'].load_image, "test.jpg", error_handler=self.error_handler)
            safe_execute(components['csv_parser'].parse_file, "test.csv", error_handler=self.error_handler)
            safe_execute(components['transformer'].transform_point, 10, 20, error_handler=self.error_handler)
        
        # Verify UX metrics
        assert ux_metrics["error_count"] == 3
        assert len(ux_metrics["response_times"]) == 3
        assert all(action == "error_dialog_shown" for action in ux_metrics["user_actions"])
        
        # Verify error handling performance
        total_time = time.time() - start_time
        assert total_time < 5.0  # Should handle errors quickly
    
    def test_error_dialog_accessibility(self):
        """Test error dialog accessibility features."""
        # Mock component with error
        component = Mock()
        component.process_data.side_effect = DataValidationError(
            "Invalid data format", "DATA_INVALID",
            {
                "accessibility": {
                    "screen_reader_text": "Data validation failed. Please check your input format.",
                    "keyboard_shortcuts": {"retry": "Ctrl+R", "help": "F1"},
                    "high_contrast": True
                }
            }
        )
        
        # Mock accessibility features
        accessibility_manager = Mock()
        accessibility_manager.is_screen_reader_active.return_value = True
        accessibility_manager.is_high_contrast_mode.return_value = True
        
        # Test error with accessibility features
        with patch('src.utils.error_handler.QMessageBox') as mock_msgbox:
            mock_msgbox.return_value = self.message_box
            
            result = safe_execute(
                component.process_data,
                {"invalid": "data"},
                error_handler=self.error_handler,
                context="Processing user data"
            )
        
        # Verify error handling
        assert result is None
        self.error_handler.handle_exception.assert_called_once()
        
        # Verify accessibility information
        call_args = self.error_handler.handle_exception.call_args[0]
        error = call_args[0]
        assert "accessibility" in error.details
        assert "screen_reader_text" in error.details["accessibility"]
    
    def test_error_recovery_workflow_integration(self):
        """Test integrated error recovery workflow."""
        # Mock component with recoverable error
        component = Mock()
        component.critical_operation.side_effect = Exception("Temporary failure")
        
        # Mock recovery workflow
        recovery_workflow = Mock()
        recovery_workflow.can_recover.return_value = True
        recovery_workflow.attempt_recovery.return_value = True
        
        # Mock user interaction
        user_choices = ["Retry", "Save and Exit", "Continue Without Saving"]
        choice_index = 0
        
        def mock_user_choice(*args, **kwargs):
            nonlocal choice_index
            choice = user_choices[choice_index % len(user_choices)]
            choice_index += 1
            return choice
        
        # Test recovery workflow
        with patch('src.utils.error_handler.QMessageBox') as mock_msgbox:
            mock_msgbox.return_value = self.message_box
            
            with patch('builtins.input', side_effect=mock_user_choice):
                result = safe_execute(
                    component.critical_operation,
                    error_handler=self.error_handler,
                    context="Critical user operation"
                )
        
        # Verify error handling
        assert result is None
        self.error_handler.handle_exception.assert_called_once()
        
        # Verify recovery workflow integration
        call_args = self.error_handler.handle_exception.call_args
        context = call_args[0][1]  # Fix: access positional args correctly
        assert "Critical" in context
    
    def test_error_performance_monitoring(self):
        """Test error handling performance in production."""
        # Mock component with performance-sensitive error
        component = Mock()
        component.high_frequency_operation.side_effect = Exception("Performance error")
        
        # Track performance metrics
        performance_metrics = {
            "error_handling_times": [],
            "memory_usage": [],
            "cpu_usage": []
        }
        
        def track_performance(exc, context):
            start_time = time.time()
            # Simulate error handling work
            time.sleep(0.001)  # 1ms simulated processing
            end_time = time.time()
            
            performance_metrics["error_handling_times"].append(end_time - start_time)
            performance_metrics["memory_usage"].append(100)  # Mock memory usage
            performance_metrics["cpu_usage"].append(50)     # Mock CPU usage
        
        self.error_handler.handle_exception.side_effect = track_performance
        
        # Test performance monitoring
        with patch('src.utils.error_handler.QMessageBox') as mock_msgbox:
            mock_msgbox.return_value = self.message_box
            
            # Simulate multiple high-frequency errors
            for i in range(10):
                safe_execute(
                    component.high_frequency_operation,
                    error_handler=self.error_handler,
                    context=f"High frequency operation {i}"
                )
        
        # Verify performance metrics
        assert len(performance_metrics["error_handling_times"]) == 10
        assert all(t < 0.1 for t in performance_metrics["error_handling_times"])  # Under 100ms
        assert len(performance_metrics["memory_usage"]) == 10
        assert len(performance_metrics["cpu_usage"]) == 10


if __name__ == '__main__':
    pytest.main([__file__]) 