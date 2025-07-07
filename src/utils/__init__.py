"""
Utilities Module

Common utilities and helpers for the CellSorter application.
"""

from .error_handler import ErrorHandler, error_handler
from .logging_config import setup_logging, LoggerMixin
from .exceptions import CellSorterError, ImageLoadError, CSVParseError, CalibrationError, DataValidationError
from .design_tokens import DesignTokens
from .style_converter import convert_css_to_qt
from .accessibility import (
    AccessibilityRole, 
    AccessibilityState,
    set_accessibility_properties,
    update_loading_state,
    set_focus_properties,
    set_error_state,
    announce_to_screen_reader,
    create_keyboard_shortcut_text,
    get_accessibility_summary,
    setup_button_accessibility,
    setup_input_accessibility
)

__all__ = [
    'ErrorHandler',
    'error_handler',
    'setup_logging',
    'LoggerMixin',
    'CellSorterError',
    'ImageLoadError',
    'CSVParseError',
    'CalibrationError',
    'DataValidationError',
    'DesignTokens',
    'convert_css_to_qt',
    # Accessibility utilities
    'AccessibilityRole',
    'AccessibilityState', 
    'set_accessibility_properties',
    'update_loading_state',
    'set_focus_properties',
    'set_error_state',
    'announce_to_screen_reader',
    'create_keyboard_shortcut_text',
    'get_accessibility_summary',
    'setup_button_accessibility',
    'setup_input_accessibility',
]