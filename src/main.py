#!/usr/bin/env python3
"""
CellSorter - Cell Sorting and Analysis Application

Main entry point for the CellSorter application.
"""

import sys
import os
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from config.settings import APP_NAME, APP_VERSION, APP_ORGANIZATION
from utils.logging_config import setup_logging
from pages.main_window import MainWindow

def main():
    """
    Main application entry point.
    """
    print("Starting CellSorter application...")
    
    # Set up logging
    logger = setup_logging()
    logger.info("CellSorter application starting...")
    
    try:
        # Create QApplication instance
        app = QApplication(sys.argv)
        app.setApplicationName(APP_NAME)
        app.setApplicationVersion(APP_VERSION)
        app.setOrganizationName(APP_ORGANIZATION)
        
        # Set application properties
        app.setApplicationDisplayName(f"{APP_NAME} - Cell Sorting and Analysis")
        # Enable high DPI support for better display on high-resolution screens
        
        # Apply basic styling
        app.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QToolBar {
                border: none;
                spacing: 4px;
            }
            QStatusBar {
                border-top: 1px solid #dee2e6;
            }
        """)
        
        # Create and show main window
        main_window = MainWindow()
        main_window.show()
        
        logger.info("CellSorter main window displayed")
        print("CellSorter application window opened.")
        print("Close the window to exit the application.")
        
        # Start the application event loop
        result = app.exec()
        logger.info("CellSorter application shutting down")
        return result
        
    except Exception as e:
        logger.error(f"Failed to start CellSorter: {e}", exc_info=True)
        print(f"Error starting CellSorter: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())