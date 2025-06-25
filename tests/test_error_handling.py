"""
Test Error Handling Framework

Tests for utils.exceptions and utils.error_handler modules to ensure
robust error handling according to TESTING_STRATEGY.md specifications.
"""

import pytest
import logging
import time
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from PySide6.QtWidgets import QMessageBox, QWidget

from utils.exceptions import (
    CellSorterError, ImageLoadError, CSVParseError, DataValidationError,
    CoordinateTransformError, CalibrationError, ExportError, ERROR_CODES
)
from utils.error_handler import ErrorHandler, error_handler, safe_execute
from utils.logging_config import setup_logging, get_logger


@pytest.mark.unit
class TestCustomExceptions:
    """Test custom exception hierarchy."""
    
    def test_base_exception_creation(self):
        """Test CellSorterError base exception."""
        message = "Test error message"
        error_code = "TEST_ERROR"
        details = {"key": "value"}
        
        error = CellSorterError(message, error_code, details)
        
        assert str(error) == f"[{error_code}] {message}"
        assert error.message == message
        assert error.error_code == error_code
        assert error.details == details
    
    def test_base_exception_without_code(self):
        """Test CellSorterError without error code."""
        message = "Simple error message"
        error = CellSorterError(message)
        
        assert str(error) == message
        assert error.message == message
        assert error.error_code is None
        assert error.details == {}
    
    def test_specific_exception_inheritance(self):
        """Test that specific exceptions inherit from base."""
        exceptions_to_test = [
            ImageLoadError, CSVParseError, DataValidationError,
            CoordinateTransformError, CalibrationError, ExportError
        ]
        
        for exception_class in exceptions_to_test:
            error = exception_class("Test message")
            assert isinstance(error, CellSorterError)
            assert isinstance(error, Exception)
    
    def test_error_codes_defined(self):
        """Test that error codes are properly defined."""
        required_codes = [
            "FILE_NOT_FOUND", "UNSUPPORTED_FORMAT", "FILE_TOO_LARGE",
            "INVALID_CSV_FORMAT", "MISSING_REQUIRED_COLUMNS",
            "CALIBRATION_POINTS_TOO_CLOSE", "COORDINATE_OUT_OF_BOUNDS"
        ]
        
        for code in required_codes:
            assert code in ERROR_CODES
            assert isinstance(ERROR_CODES[code], str)
            assert len(ERROR_CODES[code]) > 0


@pytest.mark.unit
class TestErrorHandler:
    """Test ErrorHandler class functionality."""
    
    def test_error_handler_creation(self):
        """Test ErrorHandler instantiation."""
        handler = ErrorHandler()
        assert handler.parent_widget is None
        assert handler.error_count == 0
        
        # Test with parent widget
        parent = Mock(spec=QWidget)
        handler_with_parent = ErrorHandler(parent)
        assert handler_with_parent.parent_widget == parent
    
    def test_handle_custom_exception(self):
        """Test handling of custom CellSorter exceptions."""
        handler = ErrorHandler()
        
        # Mock the message box to avoid GUI display during tests
        with patch('utils.error_handler.QMessageBox') as mock_msgbox:
            mock_box = Mock()
            mock_msgbox.return_value = mock_box
            mock_box.exec.return_value = QMessageBox.Ok
            
            error = ImageLoadError("Test image error", "IMG_ERROR", {"file": "test.jpg"})
            handler.handle_exception(error, "Loading test image")
            
            # Verify message box was created and configured correctly
            mock_msgbox.assert_called_once()
            mock_box.setIcon.assert_called_with(QMessageBox.Critical)
            mock_box.setWindowTitle.assert_called_with("CellSorter Error")
            mock_box.setText.assert_called_with("Test image error")
            mock_box.exec.assert_called_once()
            
            assert handler.error_count == 1
    
    def test_handle_standard_exception(self):
        """Test handling of standard Python exceptions."""
        handler = ErrorHandler()
        
        with patch('utils.error_handler.QMessageBox') as mock_msgbox:
            mock_box = Mock()
            mock_msgbox.return_value = mock_box
            mock_box.exec.return_value = QMessageBox.Ok
            
            error = ValueError("Standard Python error")
            handler.handle_exception(error, "Test operation")
            
            mock_box.setWindowTitle.assert_called_with("Unexpected Error")
            mock_box.setText.assert_called_with("Standard Python error")
            assert handler.error_count == 1
    
    def test_help_functionality(self):
        """Test help dialog functionality."""
        handler = ErrorHandler()
        
        with patch('utils.error_handler.QMessageBox') as mock_msgbox:
            # Setup mock for main error dialog
            mock_error_box = Mock()
            mock_error_box.exec.return_value = QMessageBox.Help
            
            # Setup mock for help dialog
            mock_help_box = Mock()
            
            # Configure the mock to return different instances
            mock_msgbox.side_effect = [mock_error_box, mock_help_box]
            
            error = CellSorterError("Test error")
            handler.handle_exception(error)
            
            # Verify both dialogs were created
            assert mock_msgbox.call_count == 2
            mock_help_box.exec.assert_called_once()


@pytest.mark.unit
class TestErrorDecorator:
    """Test error_handler decorator functionality."""
    
    def test_decorator_success_case(self):
        """Test decorator when method succeeds."""
        class TestClass:
            def __init__(self):
                self.error_handler = Mock(spec=ErrorHandler)
            
            @error_handler("Test operation")
            def test_method(self, value):
                return value * 2
        
        obj = TestClass()
        result = obj.test_method(5)
        
        assert result == 10
        obj.error_handler.handle_exception.assert_not_called()
    
    def test_decorator_error_case(self):
        """Test decorator when method raises exception."""
        class TestClass:
            def __init__(self):
                self.error_handler = Mock(spec=ErrorHandler)
            
            @error_handler("Test operation")
            def test_method(self):
                raise ValueError("Test error")
        
        obj = TestClass()
        result = obj.test_method()
        
        assert result is None
        obj.error_handler.handle_exception.assert_called_once()
        
        # Check that the correct exception was passed
        call_args = obj.error_handler.handle_exception.call_args[0]
        assert isinstance(call_args[0], ValueError)
        assert str(call_args[0]) == "Test error"
        assert call_args[1] == "Test operation"
    
    def test_decorator_without_error_handler(self):
        """Test decorator fallback when no error_handler attribute."""
        class TestClass:
            @error_handler("Test operation")
            def test_method(self):
                raise ValueError("Test error")
        
        obj = TestClass()
        
        # Should re-raise the exception when no error_handler available
        with pytest.raises(ValueError, match="Test error"):
            obj.test_method()


@pytest.mark.unit
class TestSafeExecute:
    """Test safe_execute utility function."""
    
    def test_safe_execute_success(self):
        """Test safe_execute with successful function."""
        def test_func(x, y):
            return x + y
        
        result = safe_execute(test_func, 3, 4)
        assert result == 7
    
    def test_safe_execute_with_error(self):
        """Test safe_execute with failing function."""
        def test_func():
            raise ValueError("Test error")
        
        result = safe_execute(test_func)
        assert result is None
    
    def test_safe_execute_with_error_handler(self):
        """Test safe_execute with custom error handler."""
        mock_handler = Mock(spec=ErrorHandler)
        
        def test_func():
            raise ValueError("Test error")
        
        result = safe_execute(test_func, error_handler=mock_handler, context="Test context")
        
        assert result is None
        mock_handler.handle_exception.assert_called_once()


@pytest.mark.unit
class TestLoggingConfiguration:
    """Test logging configuration and setup."""
    
    def test_logging_setup(self, temp_dir):
        """Test logging setup with custom log file."""
        log_file = temp_dir / "test.log"
        logger = setup_logging(str(log_file))
        
        assert logger.name == "cellsorter"
        assert len(logger.handlers) >= 2  # File and console handlers
        
        # Test that log file is created
        logger.info("Test log message")
        assert log_file.exists()
    
    def test_get_logger(self):
        """Test get_logger function."""
        logger = get_logger("test_module")
        assert logger.name == "cellsorter.test_module"
        assert isinstance(logger, logging.Logger)
    
    def test_logger_mixin(self):
        """Test LoggerMixin functionality."""
        from utils.logging_config import LoggerMixin
        
        class TestClass(LoggerMixin):
            def test_logging(self):
                self.log_info("Test info message")
                self.log_warning("Test warning message")
                self.log_error("Test error message")
                self.log_debug("Test debug message")
        
        obj = TestClass()
        
        # Test that logger property works
        logger = obj.logger
        assert isinstance(logger, logging.Logger)
        
        # Test logging methods (should not raise exceptions)
        obj.test_logging()


@pytest.mark.integration
class TestErrorHandlingIntegration:
    """Test error handling integration across components."""
    
    def test_file_not_found_error_flow(self, temp_dir):
        """Test complete error flow for file not found scenario."""
        handler = ErrorHandler()
        nonexistent_file = temp_dir / "nonexistent.jpg"
        
        with patch('utils.error_handler.QMessageBox') as mock_msgbox:
            mock_box = Mock()
            mock_msgbox.return_value = mock_box
            mock_box.exec.return_value = QMessageBox.Ok
            
            # Simulate file not found error
            error = ImageLoadError(
                f"File not found: {nonexistent_file}",
                "FILE_NOT_FOUND",
                {"file_path": str(nonexistent_file)}
            )
            
            handler.handle_exception(error, "Loading image file")
            
            # Verify proper error dialog configuration
            mock_box.setText.assert_called_with(f"File not found: {nonexistent_file}")
            mock_box.setDetailedText.assert_called()
            
            # Check that detailed text contains error code
            detailed_text_call = mock_box.setDetailedText.call_args[0][0]
            assert "FILE_NOT_FOUND" in detailed_text_call
            assert ERROR_CODES["FILE_NOT_FOUND"] in detailed_text_call
    
    def test_validation_error_with_details(self):
        """Test data validation error with detailed information."""
        handler = ErrorHandler()
        
        missing_columns = ["Column1", "Column2"]
        error = DataValidationError(
            "Missing required columns",
            "MISSING_REQUIRED_COLUMNS",
            {
                "missing_columns": missing_columns,
                "total_columns": 5,
                "file_path": "/path/to/file.csv"
            }
        )
        
        with patch('utils.error_handler.QMessageBox') as mock_msgbox:
            mock_box = Mock()
            mock_msgbox.return_value = mock_box
            mock_box.exec.return_value = QMessageBox.Ok
            
            handler.handle_exception(error, "Validating CSV data")
            
            # Verify detailed information is included
            detailed_text_call = mock_box.setDetailedText.call_args[0][0]
            assert "missing_columns" in detailed_text_call
            assert "total_columns" in detailed_text_call
            assert "file_path" in detailed_text_call


@pytest.mark.performance
class TestErrorHandlingPerformance:
    """Test error handling performance requirements."""
    
    def test_error_handling_overhead(self):
        """Test that error handling doesn't add significant overhead."""
        import time
        
        class TestClass:
            def __init__(self):
                self.error_handler = Mock(spec=ErrorHandler)
            
            @error_handler("Test operation")
            def fast_method(self):
                return 42
        
        obj = TestClass()
        
        # Time multiple calls to check overhead
        start_time = time.time()
        for _ in range(1000):
            result = obj.fast_method()
            assert result == 42
        
        elapsed_time = time.time() - start_time
        
        # Should complete 1000 calls in well under 1 second
        assert elapsed_time < 1.0, f"Error handling overhead too high: {elapsed_time}s"
    
    def test_large_error_message_handling(self):
        """Test handling of large error messages."""
        handler = ErrorHandler()
        
        # Create a large error message
        large_message = "X" * 10000  # 10KB message
        large_details = {f"key_{i}": f"value_{i}" * 100 for i in range(100)}
        
        error = CellSorterError(large_message, "LARGE_ERROR", large_details)
        
        start_time = time.time()
        
        with patch('utils.error_handler.QMessageBox'):
            handler.handle_exception(error)
        
        elapsed_time = time.time() - start_time
        
        # Should handle large errors quickly (< 100ms)
        assert elapsed_time < 0.1, f"Large error handling too slow: {elapsed_time}s"