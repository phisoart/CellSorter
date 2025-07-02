"""
Protocol Export Dialog for CellSorter

Provides interface for exporting protocol from selections.
"""

from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np

try:
    from PySide6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
        QPushButton, QLabel, QHeaderView, QFileDialog, QMessageBox, QProgressBar,
        QFrame, QAbstractItemView
    )
    from PySide6.QtCore import Qt, Signal, QThread, QObject, QTimer
    from PySide6.QtGui import QPixmap, QIcon, QColor
except ImportError:
    # Fallback for development
    QDialog = object
    QVBoxLayout = object
    QHBoxLayout = object
    QTableWidget = object
    QTableWidgetItem = object
    QPushButton = object
    QLabel = object
    QHeaderView = object
    QFileDialog = object
    QMessageBox = object
    QProgressBar = object
    QFrame = object
    QAbstractItemView = object
    Qt = object
    Signal = lambda x: lambda: None
    QThread = object
    QObject = object
    QTimer = object
    QPixmap = object
    QIcon = object
    QColor = object

from utils.logging_config import LoggerMixin
from utils.error_handler import error_handler


class ProtocolExportDialog(QDialog, LoggerMixin):
    """
    Dialog for exporting protocol from selections.
    
    Shows list of selections with individual extract buttons for each.
    """
    
    def __init__(self, selections_data: Dict[str, Dict[str, Any]], 
                 image_data: np.ndarray, bounding_boxes: List[Tuple[int, int, int, int]], 
                 parent=None):
        super().__init__(parent)
        self.selections_data = selections_data
        self.image_data = image_data
        self.bounding_boxes = bounding_boxes
        
        self.setup_ui()
        self.populate_table()
    
    def setup_ui(self):
        """Setup the dialog UI."""
        self.setWindowTitle("Export Selection Protocol")
        self.setMinimumSize(700, 500)
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Header
        header_label = QLabel("Export Protocol")
        header_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 8px;")
        layout.addWidget(header_label)
        
        # Subtitle
        subtitle_label = QLabel("Select a selection to extract protocol data.")
        subtitle_label.setStyleSheet("color: #6c757d; margin-bottom: 16px;")
        layout.addWidget(subtitle_label)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["#", "Label", "Color", "Well", "Cells", "Extract"])
        
        # Configure table headers
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # #
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Label
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Color
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Well
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Cells
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Extract
        
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        
        layout.addWidget(self.table)
        
        # Progress section (initially hidden)
        self.progress_frame = QFrame()
        self.progress_frame.setVisible(False)
        self.progress_frame.setFrameStyle(QFrame.StyledPanel)
        
        progress_layout = QVBoxLayout(self.progress_frame)
        
        self.progress_label = QLabel("Extracting...")
        self.progress_bar = QProgressBar()
        self.progress_status = QLabel("Ready")
        
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_status)
        
        layout.addWidget(self.progress_frame)
        
        # Button bar
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
    
    def populate_table(self):
        """Populate the table with selection data."""
        self.table.setRowCount(len(self.selections_data))
        
        # Set row height for consistent button sizing
        row_height = 32
        
        for row, (selection_id, data) in enumerate(self.selections_data.items()):
            # Set row height
            self.table.setRowHeight(row, row_height)
            
            # Number
            number_item = QTableWidgetItem(str(row + 1))
            number_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, number_item)
            
            # Label
            label_item = QTableWidgetItem(data.get('label', f'Selection {row + 1}'))
            self.table.setItem(row, 1, label_item)
            
            # Color (colored square)
            color_item = QTableWidgetItem()
            color_hex = data.get('color', '#FF0000')
            color_item.setBackground(QColor(color_hex))
            color_item.setTextAlignment(Qt.AlignCenter)
            color_item.setText("●")
            self.table.setItem(row, 2, color_item)
            
            # Well
            well_item = QTableWidgetItem(data.get('well_position', ''))
            well_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, well_item)
            
            # Cell count
            cell_count = len(data.get('cell_indices', []))
            count_item = QTableWidgetItem(str(cell_count))
            count_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 4, count_item)
            
            # Extract button - matched to row height
            extract_button = QPushButton("Extract")
            extract_button.setMaximumHeight(row_height - 4)  # Slightly smaller than row
            extract_button.setMinimumHeight(row_height - 4)
            extract_button.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border: none;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-weight: 500;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
                QPushButton:disabled {
                    background-color: #e9ecef;
                    color: #6c757d;
                }
            """)
            
            # Connect button to extract function (placeholder for now)
            extract_button.clicked.connect(lambda checked, sid=selection_id: self.extract_protocol(sid))
            
            self.table.setCellWidget(row, 5, extract_button)
        
        self.log_info(f"Populated table with {len(self.selections_data)} selections")
    
    @error_handler("Extracting protocol")
    def extract_protocol(self, selection_id: str):
        """Extract protocol for a specific selection (placeholder)."""
        if selection_id not in self.selections_data:
            QMessageBox.warning(self, "Error", "Selection not found")
            return
        
        selection_data = self.selections_data[selection_id]
        
        # Placeholder functionality - just show info message
        QMessageBox.information(
            self, 
            "Protocol Extract", 
            f"Protocol extraction for '{selection_data.get('label', 'Selection')}' will be implemented in future updates."
        )
        
        self.log_info(f"Protocol extract requested for selection {selection_id}")
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        event.accept() 