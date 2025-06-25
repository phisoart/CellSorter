"""
CellSorter Error Handler

This module provides centralized error handling and user feedback mechanisms.
"""

import traceback
from typing import Optional, Callable, Any
from functools import wraps

from PySide6.QtWidgets import QMessageBox, QWidget
from PySide6.QtCore import QTimer

from utils.exceptions import CellSorterError, ERROR_CODES
from utils.logging_config import get_logger

logger = get_logger(__name__)


class ErrorHandler:
    """
    Centralized error handling for the CellSorter application.
    """
    
    def __init__(self, parent_widget: Optional[QWidget] = None):
        self.parent_widget = parent_widget
        self.error_count = 0
        self.last_error_time = None
    
    def handle_exception(self, exception: Exception, context: str = "") -> None:
        """
        Handle an exception with appropriate logging and user feedback.
        
        Args:
            exception: The exception to handle
            context: Additional context about where the error occurred
        """
        self.error_count += 1
        
        # Log the error
        error_msg = f"{context}: {str(exception)}" if context else str(exception)
        logger.error(error_msg, exc_info=True)
        
        # Show user-friendly error dialog
        self._show_error_dialog(exception, context)
    
    def _show_error_dialog(self, exception: Exception, context: str = "") -> None:
        """
        Show an error dialog to the user.
        
        Args:
            exception: The exception to display
            context: Additional context information
        """
        if isinstance(exception, CellSorterError):
            title = "CellSorter Error"
            message = exception.message
            error_code = exception.error_code
            details = exception.details
        else:
            title = "Unexpected Error"
            message = str(exception)
            error_code = None
            details = {}
        
        # Create error dialog
        msg_box = QMessageBox(self.parent_widget)
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        
        # Add context if provided
        if context:
            msg_box.setInformativeText(f"Context: {context}")
        
        # Add error code if available
        if error_code:
            detailed_text = f"Error Code: {error_code}\n"
            if error_code in ERROR_CODES:
                detailed_text += f"Description: {ERROR_CODES[error_code]}\n"
            
            # Add technical details
            if details:
                detailed_text += "\nTechnical Details:\n"
                for key, value in details.items():
                    detailed_text += f"  {key}: {value}\n"
            
            # Add stack trace for debugging
            detailed_text += f"\nStack Trace:\n{traceback.format_exc()}"
            msg_box.setDetailedText(detailed_text)
        
        # Add standard buttons
        msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Help)
        msg_box.setDefaultButton(QMessageBox.Ok)
        
        # Show dialog
        result = msg_box.exec()
        
        if result == QMessageBox.Help:
            self._show_help_for_error(exception, error_code)
    
    def _show_help_for_error(self, exception: Exception, error_code: Optional[str]) -> None:
        """
        Show help information for specific errors.
        
        Args:
            exception: The exception that occurred
            error_code: Error code if available
        """
        # TODO: Implement context-specific help
        help_msg = QMessageBox(self.parent_widget)
        help_msg.setIcon(QMessageBox.Information)
        help_msg.setWindowTitle("Error Help")
        help_msg.setText("For additional help, please:")
        help_msg.setInformativeText(
            "• Check the user documentation\n"
            "• Verify your input data format\n"
            "• Contact support if the issue persists"
        )
        help_msg.exec()


def error_handler(context: str = ""):
    """
    Decorator for automatic error handling in methods.
    
    Args:
        context: Context description for the error
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs) -> Any:
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                # Get error handler from self if available
                if hasattr(self, 'error_handler'):
                    self.error_handler.handle_exception(e, context or func.__name__)
                else:
                    # Fallback to basic logging
                    logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
                    raise
                return None
        return wrapper
    return decorator


def safe_execute(func: Callable, *args, error_handler: Optional[ErrorHandler] = None, 
                context: str = "", **kwargs) -> Any:
    """
    Safely execute a function with error handling.
    
    Args:
        func: Function to execute
        *args: Function arguments
        error_handler: Error handler instance
        context: Context description
        **kwargs: Function keyword arguments
    
    Returns:
        Function result or None if error occurred
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if error_handler:
            error_handler.handle_exception(e, context)
        else:
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
        return None


def validate_and_execute(validator: Callable[[], bool], executor: Callable,
                        error_message: str = "Validation failed") -> Any:
    """
    Validate conditions before executing a function.
    
    Args:
        validator: Function that returns True if validation passes
        executor: Function to execute if validation passes
        error_message: Error message if validation fails
    
    Returns:
        Function result or raises ValidationError
    """
    if not validator():
        from utils.exceptions import DataValidationError
        raise DataValidationError(error_message)
    
    return executor()


class RecoveryStrategy:
    """
    Base class for error recovery strategies.
    """
    
    def can_recover(self, exception: Exception) -> bool:
        """Check if this strategy can recover from the given exception."""
        return False
    
    def recover(self, exception: Exception) -> bool:
        """Attempt to recover from the exception."""
        return False


class AutoSaveRecovery(RecoveryStrategy):
    """
    Recovery strategy that attempts to restore from auto-save.
    """
    
    def can_recover(self, exception: Exception) -> bool:
        """Check if auto-save recovery is possible."""
        # TODO: Implement auto-save detection
        return False
    
    def recover(self, exception: Exception) -> bool:
        """Restore from auto-save."""
        # TODO: Implement auto-save recovery
        return False