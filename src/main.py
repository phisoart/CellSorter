#  TODO
# 프로젝트 설정 파일들:
# pyproject.toml - 모던 Python 프로젝트 설정 (권장)
# setup.py - 전통적인 Python 패키지 설정
# Makefile - 개발 명령어 단축키
# 빌드 스크립트들:
# build_scripts/build_windows.bat - Windows용 빌드 스크립트
# build_scripts/build_mac.sh - macOS용 빌드 스크립트

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

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

class CellSorterMainWindow(QMainWindow):
    """
    Main window for the CellSorter application.
    """
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("🧬 CellSorter - Cell Sorting and Analysis Tool")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Add welcome content
        welcome_label = QLabel("Welcome to CellSorter")
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                margin: 40px;
            }
        """)
        
        description_label = QLabel(
            "Advanced cell sorting software for CosmoSort hardware integration\n\n"
            "• Multi-format image support (TIFF, JPG, PNG)\n"
            "• CellProfiler integration\n"
            "• Interactive visualization\n"
            "• Coordinate calibration\n"
            "• Protocol generation"
        )
        description_label.setAlignment(Qt.AlignCenter)
        description_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #34495e;
                line-height: 1.6;
                margin: 20px;
            }
        """)
        
        status_label = QLabel("🟢 Application initialized successfully")
        status_label.setAlignment(Qt.AlignCenter)
        status_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #27ae60;
                margin: 20px;
            }
        """)
        
        main_layout.addWidget(welcome_label)
        main_layout.addWidget(description_label)
        main_layout.addWidget(status_label)

def main():
    """
    Main application entry point.
    """
    print("Starting CellSorter application...")
    
    # Create QApplication instance
    app = QApplication(sys.argv)
    app.setApplicationName("CellSorter")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("CellSorter Team")
    
    # Apply basic styling
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f8f9fa;
        }
    """)
    
    # Create and show main window
    main_window = CellSorterMainWindow()
    main_window.show()
    
    print("CellSorter application window opened.")
    print("Close the window to exit the application.")
    
    # Start the application event loop
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())