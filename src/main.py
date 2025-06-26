#!/usr/bin/env python3
"""
CellSorter Application Entry Point

Main entry point for the CellSorter application with design system integration.
"""

import sys
from pathlib import Path
import logging

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QFont

from pages.main_window import MainWindow
from config.settings import APP_NAME, APP_VERSION, LOG_LEVEL
from utils.logging_config import setup_logging
from utils.theme_manager import ThemeManager
from utils.design_tokens import DesignTokens


def setup_application() -> QApplication:
    """
    Set up and configure the Qt application.
    
    Returns:
        Configured QApplication instance
    """
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("CellSorter")
    
    # Set default font
    tokens = DesignTokens()
    font = QFont()
    font.setFamily(tokens.get_font_string('sans'))
    font.setPixelSize(tokens.TYPOGRAPHY['text_base'])
    app.setFont(font)
    
    # Initialize theme manager and apply default theme
    theme_manager = ThemeManager(app)
    theme_manager.apply_theme(theme_manager.THEME_LIGHT)
    
    return app


def main() -> None:
    """Main application entry point."""
    # Set up logging
    setup_logging(LOG_LEVEL)
    logger = logging.getLogger(__name__)
    logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
    
    try:
        # Create and configure application
        app = setup_application()
        
        # Create and show main window
        window = MainWindow()
        window.show()
        
        # Start event loop
        sys.exit(app.exec())
        
    except Exception as e:
        logger.critical(f"Critical error during application startup: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()