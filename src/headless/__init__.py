"""
Headless GUI Development System for CellSorter

This module provides infrastructure for developing and maintaining PySide6 GUIs 
in headless environments, enabling AI agents and developers to work with UI 
purely through structured text formats.
"""

from .display_detector import DisplayDetector, has_display, get_display_info
from .mode_manager import ModeManager, is_dev_mode, set_dev_mode, get_mode_info
from .ui_model import UIModel, Widget, Layout

__all__ = [
    'DisplayDetector',
    'has_display',
    'get_display_info',
    'ModeManager',
    'is_dev_mode',
    'set_dev_mode',
    'get_mode_info',
    'UIModel',
    'Widget',
    'Layout',
]

__version__ = '1.0.0' 