"""
Protocol Export Dialog for CellSorter

Provides interface for exporting protocol files from selections.
"""

from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np
from PySide6.QtWidgets import QApplication

try:
    from PySide6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
        QPushButton, QLabel, QHeaderView, QFileDialog, QMessageBox, QProgressBar,
        QFrame, QAbstractItemView, QSizePolicy, QWidget
    )
    from PySide6.QtCore import Qt, Signal, QThread, QObject, QTimer
    from PySide6.QtGui import QPixmap, QIcon, QColor, QFont
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
    QSizePolicy = object
    QFont = object
    QWidget = object

from utils.logging_config import LoggerMixin
from utils.error_handler import error_handler


class ProtocolExportDialog(QDialog, LoggerMixin):
    """
    Dialog for exporting protocol files from selections.
    
    Shows list of selections with individual extract buttons for each.
    """
    
    def __init__(self, selections_data: Dict[str, Dict[str, Any]], 
                 image_data: np.ndarray, bounding_boxes: List[Tuple[int, int, int, int]], 
                 coordinate_transformer, image_info: Dict[str, Any],
                 parent=None):
        super().__init__(parent)
        self.selections_data = selections_data
        self.image_data = image_data
        self.bounding_boxes = bounding_boxes
        self.coordinate_transformer = coordinate_transformer
        self.image_info = image_info
        
        self.setWindowTitle("Export Protocol")
        self.setModal(True)
        self.resize(700, 500)
        
        self.setup_ui()
        self.populate_table()
    
    def setup_ui(self):
        """Setup the dialog UI."""
        self.setWindowTitle("Export Protocol")
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
        
        # Auto-size rows to content
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        
        # Ensure compact font globally within table
        self.table.setStyleSheet("QTableWidget { font-size: 12px; }")
        
        for row, (selection_id, data) in enumerate(self.selections_data.items()):
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
            color_item.setFont(QFont("Arial", 10))
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
            
            # Extract button
            extract_button = QPushButton("Export")
            extract_button.setStyleSheet("padding: 2px 8px;")
            
            # Connect button to extract function (placeholder for now)
            extract_button.clicked.connect(lambda checked, sid=selection_id: self.extract_selection(sid))

            # Use a container to center the button in the cell
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addStretch()
            layout.addWidget(extract_button)
            layout.addStretch()
            self.table.setCellWidget(row, 5, container)
        
        self.log_info(f"Populated table with {len(self.selections_data)} selections")
    
    @error_handler("Exporting selection protocol")
    def extract_selection(self, selection_id: str):
        """Extract protocol for a specific selection."""
        if selection_id not in self.selections_data:
            QMessageBox.warning(self, "Error", "Selection not found")
            return

        selection_data = self.selections_data[selection_id]
        cell_indices = selection_data.get('cell_indices', [])

        if not cell_indices:
            QMessageBox.information(self, "No Cells", "This selection contains no cells to extract")
            return

        # Check calibration
        if not self.coordinate_transformer.is_calibrated():
            QMessageBox.warning(self, "Calibration Required", 
                              "Coordinate calibration is required for protocol export")
            return

        # Let user choose output file
        default_filename = f"{selection_data.get('label', 'Selection')}.cxprotocol"
        output_file, _ = QFileDialog.getSaveFileName(
            self, 
            f"Save Protocol for {selection_data.get('label', 'Selection')}", 
            str(Path.home() / default_filename),
            "CellXpress Protocol Files (*.cxprotocol);;All Files (*)"
        )

        if not output_file:
            return  # User cancelled

        try:
            # Generate protocol content
            protocol_content = self._generate_protocol_content(selection_data)
            
            # Write to file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(protocol_content)
            
            QMessageBox.information(
                self, 
                "Protocol Exported", 
                f"Protocol successfully exported to:\n{output_file}"
            )
            self.log_info(f"Protocol exported: {output_file}")
            
        except Exception as e:
            error_msg = f"Failed to export protocol: {e}"
            QMessageBox.critical(self, "Export Failed", error_msg)
            self.log_error(error_msg)

    def _generate_protocol_content(self, selection_data: Dict[str, Any]) -> str:
        """Generate .cxprotocol file content."""
        lines = []
        
        # [IMAGE] section
        lines.append("[IMAGE]")
        lines.append(f'FILE = "{self.image_info["filename"]}"')
        lines.append(f'WIDTH = {self.image_info["width"]}')
        lines.append(f'HEIGHT = {self.image_info["height"]}')
        lines.append(f'FORMAT = "{self.image_info["format"]}"')
        lines.append("")
        
        # [IMAGING_LAYOUT] section
        lines.append("[IMAGING_LAYOUT]")
        lines.append("PositionOnly = 1")
        lines.append('AfterBefore = "01"')
        
        # Get cells for this selection
        cell_indices = selection_data.get('cell_indices', [])
        lines.append(f"Points = {len(cell_indices)}")
        
        # Debug logging
        self.log_info(f"Generating protocol for {len(cell_indices)} cells")
        self.log_info(f"Available bounding boxes: {len(self.bounding_boxes)}")
        self.log_info(f"Cell indices: {cell_indices[:10]}...")  # Show first 10
        
        # Generate points
        point_count = 0
        for i, cell_index in enumerate(cell_indices, 1):
            if cell_index < len(self.bounding_boxes):
                bbox = self.bounding_boxes[cell_index]
                min_x, min_y, max_x, max_y = bbox
                
                # Convert rectangle to square while preserving center
                square_bbox = self._convert_to_square_bbox(min_x, min_y, max_x, max_y)
                sq_min_x, sq_min_y, sq_max_x, sq_max_y = square_bbox
                
                # Convert pixel coordinates to stage coordinates
                try:
                    stage_min = self.coordinate_transformer.pixel_to_stage(sq_min_x, sq_min_y)
                    stage_max = self.coordinate_transformer.pixel_to_stage(sq_max_x, sq_max_y)
                    # 항상 x_min < x_max, y_min < y_max 보장
                    final_min_x = min(stage_min.stage_x, stage_max.stage_x)
                    final_max_x = max(stage_min.stage_x, stage_max.stage_x)
                    final_min_y = min(stage_min.stage_y, stage_max.stage_y)
                    final_max_y = max(stage_min.stage_y, stage_max.stage_y)
                    
                    # Get selection info
                    color_code = selection_data.get('color', '#FF0000')
                    color_name = self._rgb_to_color_name(color_code)
                    well = selection_data.get('well_position', 'A01')
                    # Use actual selection label instead of Cell_XXX
                    selection_label = selection_data.get('label', 'Selection')
                    note = f"{selection_label}_{i:03d}"
                    
                    # Format: "X_min; Y_min; X_max; Y_max; color; well; note"
                    point_line = f'P_{i} = "{final_min_x:.4f}; {final_min_y:.4f}; {final_max_x:.4f}; {final_max_y:.4f}; {color_name}; {well}; {note}"'
                    lines.append(point_line)
                    point_count += 1
                    self.log_info(f"Added point {i}: cell_index={cell_index}, stage_coords=({final_min_x:.4f},{final_min_y:.4f})-({final_max_x:.4f},{final_max_y:.4f})")
                    
                except Exception as e:
                    self.log_error(f"Failed to convert coordinates for cell {cell_index}: {e}")
                    # Skip this cell if coordinate conversion fails
                    continue
            else:
                self.log_error(f"Cell index {cell_index} out of bounds (max: {len(self.bounding_boxes)})")
        
        self.log_info(f"Generated {point_count} points for protocol")
        
        return '\n'.join(lines)

    def _convert_to_square_bbox(self, min_x: int, min_y: int, max_x: int, max_y: int) -> Tuple[int, int, int, int]:
        """
        Convert rectangular bounding box to square, preserving center.
        
        Args:
            min_x, min_y, max_x, max_y: Original bounding box coordinates
            
        Returns:
            Tuple of (sq_min_x, sq_min_y, sq_max_x, sq_max_y) for square bbox
        """
        # Calculate current dimensions
        width = max_x - min_x
        height = max_y - min_y
        
        # Use the longer side as the square size
        square_size = max(width, height)
        
        # Calculate center of original bbox
        center_x = (min_x + max_x) // 2
        center_y = (min_y + max_y) // 2
        
        # Calculate square bbox centered on the original center
        half_size = square_size // 2
        sq_min_x = center_x - half_size
        sq_min_y = center_y - half_size
        sq_max_x = sq_min_x + square_size
        sq_max_y = sq_min_y + square_size
        
        # Get image dimensions for boundary checking
        img_height, img_width = self.image_data.shape[:2]
        
        # Adjust if square goes outside image boundaries
        if sq_min_x < 0:
            # Shift right
            offset = -sq_min_x
            sq_min_x = 0
            sq_max_x = square_size
        elif sq_max_x > img_width:
            # Shift left
            offset = sq_max_x - img_width
            sq_max_x = img_width
            sq_min_x = img_width - square_size
            
        if sq_min_y < 0:
            # Shift down
            offset = -sq_min_y
            sq_min_y = 0
            sq_max_y = square_size
        elif sq_max_y > img_height:
            # Shift up
            offset = sq_max_y - img_height
            sq_max_y = img_height
            sq_min_y = img_height - square_size
        
        # Final boundary check - ensure coordinates are within image
        sq_min_x = max(0, min(sq_min_x, img_width - 1))
        sq_min_y = max(0, min(sq_min_y, img_height - 1))
        sq_max_x = max(0, min(sq_max_x, img_width - 1))
        sq_max_y = max(0, min(sq_max_y, img_height - 1))
        
        return (sq_min_x, sq_min_y, sq_max_x, sq_max_y)
    
    def _rgb_to_color_name(self, rgb_color: str) -> str:
        """
        Convert RGB color code to readable color name.
        
        Args:
            rgb_color: Color string like '#FF0000' or 'ff0000'
            
        Returns:
            Color name like 'red', 'blue', etc.
        """
        # Remove # if present and convert to uppercase
        color_code = rgb_color.replace('#', '').upper()
        
        # Color mapping from RGB codes to names
        color_map = {
            'FF0000': 'red',
            '00FF00': 'green', 
            '0000FF': 'blue',
            'FFFF00': 'yellow',
            'FF00FF': 'magenta',
            '00FFFF': 'cyan',
            'C0C0C0': 'lightgray',
            '800000': 'darkred',
            '008000': 'darkgreen',
            '000080': 'darkblue',
            '808000': 'darkyellow',
            '800080': 'darkmagenta',
            '008080': 'darkcyan',
            '808080': 'darkgray',
            'FFFFFF': 'white',
            '000000': 'black'
            
        }
        
        # Return mapped color name or default to original if not found
        return color_map.get(color_code, color_code.lower())

    def closeEvent(self, event):
        """Handle dialog close event."""
        event.accept() 