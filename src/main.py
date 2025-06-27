#!/usr/bin/env python3
"""
CellSorter Application Entry Point

Main entry point for the CellSorter application with design system integration.
"""

import sys
from pathlib import Path
import logging
from config.settings import APP_NAME, APP_VERSION, APP_ORGANIZATION, LOG_LEVEL
from utils.logging_config import setup_logging
from services.theme_manager import ThemeManager

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QFont

from pages.main_window import MainWindow
from utils.update_checker import UpdateChecker

def main() -> None:
    """Main application entry point."""
    # Set up logging
    setup_logging(console_level=LOG_LEVEL)
    logger = logging.getLogger(__name__)
    logger.info(f"Starting {APP_NAME} v{APP_VERSION}")

    try:
        # High DPI attributes must be set before QApplication instantiation
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

        # Create QApplication instance
        app = QApplication(sys.argv)
        app.setApplicationName(APP_NAME)
        app.setApplicationVersion(APP_VERSION)
        app.setOrganizationName(APP_ORGANIZATION)
        app.setApplicationDisplayName(f"{APP_NAME} - Cell Sorting and Analysis")

        # Initialize theme manager before creating main window
        theme_manager = ThemeManager(app)
        theme_manager.apply_theme("light")  # Default theme

        # Initialize update checker
        update_checker = UpdateChecker(APP_VERSION)

        # Create and show main window, injecting the theme manager and update checker
        from pages.main_window import MainWindow
        window = MainWindow(theme_manager=theme_manager, update_checker=update_checker)
        window.show()
        
        # Start periodic update checking after window is shown
        update_checker.start_periodic_check()

        # Start event loop
        sys.exit(app.exec())

    except Exception as e:
        logger.critical(f"Critical error during application startup: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()