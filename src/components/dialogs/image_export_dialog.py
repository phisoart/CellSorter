"""
Image Export Dialog for CellSorter

Provides interface for exporting individual cell images from selections.
"""

from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

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


class ImageExportWorker(QObject, LoggerMixin):
    """Worker thread for exporting individual cell images."""
    
    # Signals
    progress_updated = Signal(int, str)  # percentage, status
    export_finished = Signal(bool, str)  # success, message
    
    def __init__(self, image_data: np.ndarray, selection_data: Dict[str, Any], 
                 bounding_boxes: List[Tuple[int, int, int, int]], output_dir: str):
        super().__init__()
        self.image_data = image_data
        self.selection_data = selection_data
        self.bounding_boxes = bounding_boxes
        self.output_dir = Path(output_dir)
        self.should_cancel = False
    
    def cancel(self):
        """Cancel the export operation."""
        self.should_cancel = True
    
    def export_selection_images(self):
        """Export individual cell images and marked overlay image."""
        try:
            if self.should_cancel:
                return
                
            self.progress_updated.emit(0, "Preparing export...")
            
            # Get selection info
            label = self.selection_data.get('label', 'Selection')
            cell_indices = self.selection_data.get('cell_indices', [])
            color = self.selection_data.get('color', '#FF0000')
            
            if not cell_indices:
                self.export_finished.emit(False, "No cells in selection")
                return
            
            # Create output directory if it doesn't exist
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            total_steps = len(cell_indices) + 1  # +1 for overlay image
            
            # Export individual cell images
            for i, cell_index in enumerate(cell_indices):
                if self.should_cancel:
                    return
                    
                progress = int((i / total_steps) * 100)
                self.progress_updated.emit(progress, f"Exporting cell {i+1}/{len(cell_indices)}")
                
                # Get bounding box for this cell
                if cell_index < len(self.bounding_boxes):
                    bbox = self.bounding_boxes[cell_index]
                    min_x, min_y, max_x, max_y = bbox
                    
                    # Crop cell region from image
                    cell_image = self.image_data[min_y:max_y, min_x:max_x]
                    
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
                        filepath = self.output_dir / filename
                        pil_image.save(filepath, 'JPEG', quality=95)
                        
                        self.log_info(f"Exported cell image: {filename}")
            
            if self.should_cancel:
                return
            
            # Create and save overlay image
            self.progress_updated.emit(90, "Creating overlay image...")
            overlay_success = self._create_overlay_image(label, cell_indices, color)
            
            if overlay_success:
                self.progress_updated.emit(100, "Export completed")
                message = f"Exported {len(cell_indices)} cell images and overlay to {self.output_dir}"
                self.export_finished.emit(True, message)
            else:
                self.export_finished.emit(False, "Failed to create overlay image")
                
        except Exception as e:
            self.log_error(f"Export failed: {e}")
            self.export_finished.emit(False, f"Export failed: {e}")
    
    def _create_overlay_image(self, label: str, cell_indices: List[int], color: str) -> bool:
        """Create overlay image with marked selection areas."""
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
            overlay_filepath = self.output_dir / overlay_filename
            overlay_image.save(overlay_filepath, 'JPEG', quality=95)
            
            self.log_info(f"Created overlay image: {overlay_filename}")
            return True
            
        except Exception as e:
            self.log_error(f"Failed to create overlay image: {e}")
            return False


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
        self.export_workers: Dict[str, ImageExportWorker] = {}
        self.export_threads: Dict[str, QThread] = {}
        
        self.setWindowTitle("Export Selection Images")
        self.setModal(True)
        self.resize(600, 400)
        
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
            export_button.setStyleSheet("""
                QPushButton {
                    background-color: #007bff;
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #0056b3;
                }
                QPushButton:disabled {
                    background-color: #e9ecef;
                    color: #6c757d;
                }
            """)
            
            # Connect button to export function
            export_button.clicked.connect(lambda checked, sid=selection_id: self.export_selection(sid))
            
            self.table.setCellWidget(row, 5, export_button)
        
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
        
        # Show progress
        self.progress_frame.setVisible(True)
        self.progress_label.setText(f"Exporting {selection_data.get('label', 'Selection')}")
        self.progress_bar.setValue(0)
        self.progress_status.setText("Starting export...")
        
        # Disable all export buttons during export
        self._set_export_buttons_enabled(False)
        
        # Create worker and thread
        worker = ImageExportWorker(self.image_data, selection_data, self.bounding_boxes, output_dir)
        thread = QThread()
        
        # Store references
        self.export_workers[selection_id] = worker
        self.export_threads[selection_id] = thread
        
        # Connect signals
        worker.moveToThread(thread)
        thread.started.connect(worker.export_selection_images)
        worker.progress_updated.connect(self._on_export_progress)
        worker.export_finished.connect(lambda success, msg, sid=selection_id: self._on_export_finished(success, msg, sid))
        
        # Ensure thread cleanup when worker finishes
        worker.export_finished.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        
        # Start export
        thread.start()
        
        self.log_info(f"Started export for selection {selection_id}")
    
    def _on_export_progress(self, percentage: int, status: str):
        """Handle export progress updates."""
        self.progress_bar.setValue(percentage)
        self.progress_status.setText(status)
    
    def _on_export_finished(self, success: bool, message: str, selection_id: str):
        """Handle export completion."""
        # Note: Don't clean up immediately here - let the automatic cleanup handle it
        # This prevents race conditions and threading issues
        
        # Hide progress
        self.progress_frame.setVisible(False)
        
        # Re-enable export buttons
        self._set_export_buttons_enabled(True)
        
        # Show result
        if success:
            QMessageBox.information(self, "Export Complete", message)
            self.log_info(f"Export completed successfully: {message}")
        else:
            QMessageBox.critical(self, "Export Failed", message)
            self.log_error(f"Export failed: {message}")
    
    def _set_export_buttons_enabled(self, enabled: bool):
        """Enable or disable all export buttons."""
        for row in range(self.table.rowCount()):
            button = self.table.cellWidget(row, 5)
            if button:
                button.setEnabled(enabled)
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        # Cancel any running exports
        for worker in self.export_workers.values():
            worker.cancel()
        
        # Wait for threads to finish properly
        for thread in self.export_threads.values():
            if thread.isRunning():
                thread.quit()
                # Don't wait too long to avoid blocking the UI
                thread.wait(1000)  # Wait up to 1 second only
        
        # Let Qt handle the cleanup automatically through deleteLater
        # This is safer and prevents the "QThread: Destroyed while thread is still running" warning
        
        event.accept()
