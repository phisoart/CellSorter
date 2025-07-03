"""
Image Export Dialog for CellSorter

Provides interface for exporting individual cell images from selections.
"""

from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from PySide6.QtWidgets import QApplication

try:
    from PySide6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
        QPushButton, QLabel, QHeaderView, QFileDialog, QMessageBox, QProgressBar,
        QFrame, QAbstractItemView, QWidget
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
    QWidget = object

from utils.logging_config import LoggerMixin
from utils.error_handler import error_handler


class ImageExportDialog(QDialog, LoggerMixin):
    """
    Dialog for exporting individual cell images from selections.
    
    Shows list of selections with individual export buttons for each.
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
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("Export Individual Cell Images")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header_label)
        
        info_label = QLabel("Select a selection to export individual cell images and overlay image.")
        info_label.setStyleSheet("color: #666; margin-bottom: 15px;")
        layout.addWidget(info_label)
        
        # Selection table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["#", "Label", "Color", "Well", "Cells", "Export"])
        
        # Configure table
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # #
        header.setSectionResizeMode(1, QHeaderView.Stretch)           # Label
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Color
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Well
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Cells
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Export
        
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        
        layout.addWidget(self.table)
        
        # Progress section (initially hidden)
        self.progress_frame = QFrame()
        self.progress_frame.setVisible(False)
        self.progress_frame.setFrameStyle(QFrame.StyledPanel)
        
        progress_layout = QVBoxLayout(self.progress_frame)
        
        self.progress_label = QLabel("Exporting...")
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
        
        # Compact font for table rows
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
            
            # Export button
            export_button = QPushButton("Export")
            export_button.setStyleSheet("padding: 2px 8px;")
            
            # Connect button to export function
            export_button.clicked.connect(lambda checked, sid=selection_id: self.export_selection(sid))
            
            # Use a container to center the button in the cell
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addStretch()
            layout.addWidget(export_button)
            layout.addStretch()
            self.table.setCellWidget(row, 5, container)
        
        self.log_info(f"Populated table with {len(self.selections_data)} selections")
    
    @error_handler("Exporting selection images")
    def export_selection(self, selection_id: str):
        """Export images for a specific selection."""
        if selection_id not in self.selections_data:
            QMessageBox.warning(self, "Error", "Selection not found")
            return

        selection_data = self.selections_data[selection_id]
        cell_indices = selection_data.get('cell_indices', [])

        if not cell_indices:
            QMessageBox.information(self, "No Cells", "This selection contains no cells to export")
            return

        # Let user choose output directory
        output_dir = QFileDialog.getExistingDirectory(
            self, 
            f"Select Export Directory for {selection_data.get('label', 'Selection')}", 
            str(Path.home())
        )

        if not output_dir:
            return  # User cancelled

        # Show progress and disable buttons
        self.progress_frame.setVisible(True)
        self.progress_label.setText(f"Exporting {selection_data.get('label', 'Selection')}")
        self.progress_bar.setValue(0)
        self.progress_status.setText("Starting export...")
        self._set_export_buttons_enabled(False)
        
        # Process events to update UI
        QApplication.processEvents()

        try:
            # Perform export synchronously
            success, message = self._export_selection_sync(selection_data, output_dir)
            
            # Hide progress and re-enable buttons
            self.progress_frame.setVisible(False)
            self._set_export_buttons_enabled(True)
            
            # Show result
            if success:
                QMessageBox.information(self, "Export Complete", message)
                self.log_info(f"Export completed successfully: {message}")
            else:
                QMessageBox.critical(self, "Export Failed", message)
                self.log_error(f"Export failed: {message}")
                
        except Exception as e:
            # Hide progress and re-enable buttons
            self.progress_frame.setVisible(False)
            self._set_export_buttons_enabled(True)
            
            error_msg = f"Export failed: {e}"
            QMessageBox.critical(self, "Export Failed", error_msg)
            self.log_error(error_msg)

    def _export_selection_sync(self, selection_data: Dict[str, Any], output_dir: str) -> Tuple[bool, str]:
        """Synchronously export selection images."""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            label = selection_data.get('label', 'Selection')
            cell_indices = selection_data.get('cell_indices', [])
            color = selection_data.get('color', '#FF0000')
            
            total_steps = len(cell_indices) + 1  # +1 for overlay image
            
            # Export individual cell images
            for i, cell_index in enumerate(cell_indices):
                progress = int((i / total_steps) * 90)  # Reserve 10% for overlay
                self.progress_bar.setValue(progress)
                self.progress_status.setText(f"Exporting cell {i+1}/{len(cell_indices)}")
                QApplication.processEvents()  # Update UI
                
                # Get bounding box for this cell
                if cell_index < len(self.bounding_boxes):
                    bbox = self.bounding_boxes[cell_index]
                    min_x, min_y, max_x, max_y = bbox
                    
                    # Convert rectangle to square while preserving center
                    square_bbox = self._convert_to_square_bbox(min_x, min_y, max_x, max_y)
                    sq_min_x, sq_min_y, sq_max_x, sq_max_y = square_bbox
                    
                    # Crop cell region from image using square bbox
                    cell_image = self.image_data[sq_min_y:sq_max_y, sq_min_x:sq_max_x]
                    
                    # Convert to PIL Image and save
                    if cell_image.size > 0:  # Ensure valid crop
                        # Convert numpy to PIL
                        if len(cell_image.shape) == 3:
                            # RGB image
                            pil_image = Image.fromarray(cell_image.astype(np.uint8))
                        else:
                            # Grayscale image
                            pil_image = Image.fromarray(cell_image.astype(np.uint8), mode='L')
                        
                        # Save with sequential numbering
                        filename = f"{label}_{i+1:03d}.jpg"
                        filepath = output_path / filename
                        pil_image.save(filepath, 'JPEG', quality=95)
                        
                        self.log_info(f"Exported cell image: {filename}")
            
            # Create and save overlay image
            self.progress_bar.setValue(90)
            self.progress_status.setText("Creating overlay image...")
            QApplication.processEvents()
            
            overlay_success = self._create_overlay_image_sync(label, cell_indices, color, output_path)
            
            self.progress_bar.setValue(100)
            self.progress_status.setText("Export completed")
            QApplication.processEvents()
            
            if overlay_success:
                message = f"Exported {len(cell_indices)} cell images and overlay to {output_path}"
                return True, message
            else:
                return False, "Failed to create overlay image"
                
        except Exception as e:
            return False, f"Export failed: {e}"

    def _create_overlay_image_sync(self, label: str, cell_indices: List[int], color: str, output_path: Path) -> bool:
        """Create overlay image with marked selection areas synchronously."""
        try:
            # Convert original image to PIL
            if len(self.image_data.shape) == 3:
                # RGB image
                overlay_image = Image.fromarray(self.image_data.astype(np.uint8))
            else:
                # Grayscale - convert to RGB for colored overlays
                gray_array = self.image_data.astype(np.uint8)
                rgb_array = np.stack([gray_array, gray_array, gray_array], axis=2)
                overlay_image = Image.fromarray(rgb_array)
            
            # Create drawing context
            draw = ImageDraw.Draw(overlay_image)
            
            # Parse color (remove # if present)
            color_hex = color.replace('#', '')
            color_rgb = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
            
            # Draw bounding boxes for selected cells
            for cell_index in cell_indices:
                if cell_index < len(self.bounding_boxes):
                    bbox = self.bounding_boxes[cell_index]
                    min_x, min_y, max_x, max_y = bbox
                    
                    # Draw rectangle outline
                    draw.rectangle([min_x, min_y, max_x, max_y], 
                                 outline=color_rgb, width=3)
            
            # Save overlay image
            overlay_filename = f"{label}.jpg"
            overlay_filepath = output_path / overlay_filename
            overlay_image.save(overlay_filepath, 'JPEG', quality=95)
            
            self.log_info(f"Created overlay image: {overlay_filename}")
            return True
            
        except Exception as e:
            self.log_error(f"Failed to create overlay image: {e}")
            return False
    
    def _set_export_buttons_enabled(self, enabled: bool):
        """Enable or disable all export buttons."""
        for row in range(self.table.rowCount()):
            button = self.table.cellWidget(row, 5)
            if button:
                button.setEnabled(enabled)
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        # No threads to cleanup anymore - just close
        event.accept()

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
        sq_min_x = max(0, sq_min_x)
        sq_min_y = max(0, sq_min_y)
        sq_max_x = min(img_width, sq_max_x)
        sq_max_y = min(img_height, sq_max_y)
        
        return (sq_min_x, sq_min_y, sq_max_x, sq_max_y)
