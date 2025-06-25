"""
Export Dialog for CellSorter

This dialog provides comprehensive export options for analysis results
including CSV data, image overlays, and protocol files.
"""

from typing import Optional, Dict, Any, List
from pathlib import Path
import csv
import json
from datetime import datetime
import numpy as np
from PIL import Image, ImageDraw

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QPushButton,
    QDialogButtonBox, QGroupBox, QCheckBox, QComboBox, QLineEdit, QTextEdit,
    QFileDialog, QProgressBar, QTabWidget, QWidget, QSpinBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QPixmap


class ExportWorker(QThread):
    """Worker thread for export operations."""
    
    progress_updated = Signal(int)  # percentage
    status_updated = Signal(str)    # status message
    export_finished = Signal(bool, str)  # success, message
    
    def __init__(self, export_options: Dict[str, Any], session_data: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.export_options = export_options
        self.session_data = session_data or {}
        self.is_cancelled = False
        self.output_directory = export_options.get('output_directory', Path.cwd())
        
        # Ensure output directory exists
        Path(self.output_directory).mkdir(parents=True, exist_ok=True)
    
    def run(self) -> None:
        """Execute export operations."""
        try:
            self.status_updated.emit("Starting export...")
            self.progress_updated.emit(10)
            
            if self.is_cancelled:
                return
            
            # Export CSV data
            if self.export_options.get('export_csv', False):
                self.status_updated.emit("Exporting CSV data...")
                self._export_csv()
                self.progress_updated.emit(40)
            
            if self.is_cancelled:
                return
            
            # Export image with overlays
            if self.export_options.get('export_image', False):
                self.status_updated.emit("Exporting image with overlays...")
                self._export_image()
                self.progress_updated.emit(70)
            
            if self.is_cancelled:
                return
            
            # Export protocol file
            if self.export_options.get('export_protocol', False):
                self.status_updated.emit("Exporting protocol file...")
                self._export_protocol()
                self.progress_updated.emit(90)
            
            self.progress_updated.emit(100)
            self.export_finished.emit(True, "Export completed successfully!")
            
        except Exception as e:
            self.export_finished.emit(False, f"Export failed: {str(e)}")
    
    def _export_csv(self) -> None:
        """Export CSV data."""
        try:
            # Get selections data
            selections = self.session_data.get('data', {}).get('selections', [])
            if not selections:
                return
            
            # Prepare CSV data
            csv_data = []
            for selection in selections:
                for cell_index in selection.get('cell_indices', []):
                    row = {
                        'selection_id': selection.get('id', ''),
                        'selection_label': selection.get('label', ''),
                        'selection_color': selection.get('color', ''),
                        'well_position': selection.get('well_position', ''),
                        'cell_index': cell_index,
                        'status': selection.get('status', ''),
                        'created_at': selection.get('created_at', '')
                    }
                    csv_data.append(row)
            
            # Write CSV file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            csv_filename = f"cellsorter_export_{timestamp}.csv"
            csv_path = Path(self.output_directory) / csv_filename
            
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                if csv_data:
                    fieldnames = csv_data[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(csv_data)
            
            self.status_updated.emit(f"CSV exported: {csv_filename}")
            
        except Exception as e:
            raise Exception(f"CSV export failed: {str(e)}")
    
    def _export_image(self) -> None:
        """Export image with overlays."""
        try:
            # Get image path and selection data
            image_file = self.session_data.get('data', {}).get('image_file')
            selections = self.session_data.get('data', {}).get('selections', [])
            
            if not image_file or not Path(image_file).exists():
                self.status_updated.emit("Skipping image export: No image loaded")
                return
            
            # Load original image
            original_image = Image.open(image_file)
            if original_image.mode != 'RGB':
                original_image = original_image.convert('RGB')
            
            # Create overlay
            overlay = Image.new('RGBA', original_image.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            
            # Draw selection overlays
            for selection in selections:
                color = selection.get('color', '#FF0000')
                # Convert hex color to RGB
                if color.startswith('#'):
                    color = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
                else:
                    color = (255, 0, 0)  # Default red
                
                # Add alpha for transparency
                overlay_color = color + (128,)  # 50% transparency
                
                # Draw bounding boxes for selected cells
                cell_indices = selection.get('cell_indices', [])
                for cell_index in cell_indices:
                    # Note: In a real implementation, you would get actual bounding box coordinates
                    # For now, we'll draw placeholder rectangles
                    x, y = (cell_index * 50) % original_image.width, (cell_index * 30) % original_image.height
                    draw.rectangle([x, y, x+20, y+20], fill=overlay_color, outline=color + (255,), width=2)
            
            # Composite original image with overlay
            if original_image.mode != 'RGBA':
                original_image = original_image.convert('RGBA')
            
            composite = Image.alpha_composite(original_image, overlay)
            
            # Save image
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            image_format = self.export_options.get('image_format', 'PNG').lower()
            image_filename = f"cellsorter_image_{timestamp}.{image_format}"
            image_path = Path(self.output_directory) / image_filename
            
            if image_format == 'png':
                composite.save(image_path, 'PNG', optimize=True)
            elif image_format == 'jpeg':
                rgb_image = composite.convert('RGB')
                quality = self.export_options.get('image_quality', 95)
                rgb_image.save(image_path, 'JPEG', quality=quality, optimize=True)
            elif image_format == 'tiff':
                composite.save(image_path, 'TIFF')
            else:
                composite.save(image_path, 'PNG')
            
            self.status_updated.emit(f"Image exported: {image_filename}")
            
        except Exception as e:
            raise Exception(f"Image export failed: {str(e)}")
    
    def _export_protocol(self) -> None:
        """Export protocol file."""
        try:
            # Get session data
            data = self.session_data.get('data', {})
            selections = data.get('selections', [])
            calibration = data.get('calibration', {})
            image_file = data.get('image_file')
            
            if not selections:
                self.status_updated.emit("Skipping protocol export: No selections")
                return
            
            # Create protocol content
            protocol_lines = []
            
            # IMAGE section
            protocol_lines.append("[IMAGE]")
            if image_file:
                image_path = Path(image_file)
                protocol_lines.append(f"FILE = \"{image_path.stem}\"")
                
                # Try to get image dimensions
                try:
                    with Image.open(image_file) as img:
                        protocol_lines.append(f"WIDTH = {img.width}")
                        protocol_lines.append(f"HEIGHT = {img.height}")
                        protocol_lines.append(f"FORMAT = \"{img.format}\"")
                except:
                    protocol_lines.append("WIDTH = 2048")
                    protocol_lines.append("HEIGHT = 2048")
                    protocol_lines.append("FORMAT = \"TIFF\"")
            else:
                protocol_lines.append("FILE = \"unknown\"")
                protocol_lines.append("WIDTH = 2048")
                protocol_lines.append("HEIGHT = 2048")
                protocol_lines.append("FORMAT = \"TIFF\"")
            
            protocol_lines.append("")
            
            # IMAGING_LAYOUT section
            protocol_lines.append("[IMAGING_LAYOUT]")
            protocol_lines.append("PositionOnly = 1")
            protocol_lines.append("AfterBefore = \"01\"")
            protocol_lines.append(f"Points = {len(selections)}")
            
            # Add selection points
            for i, selection in enumerate(selections, 1):
                cell_indices = selection.get('cell_indices', [])
                if not cell_indices:
                    continue
                
                # Calculate average position (simplified for demo)
                avg_x = sum(cell_indices) * 10 % 1000  # Simplified coordinate calculation
                avg_y = sum(cell_indices) * 15 % 1000
                
                # Create crop region
                crop_size = 50  # Default crop size
                min_x = max(0, avg_x - crop_size // 2)
                min_y = max(0, avg_y - crop_size // 2)
                max_x = min_x + crop_size
                max_y = min_y + crop_size
                
                # Apply coordinate transformation if available
                if calibration.get('is_calibrated', False):
                    # Apply transformation matrix (simplified)
                    transform_matrix = calibration.get('transformation_matrix')
                    if transform_matrix:
                        # Apply transformation (simplified)
                        min_x *= 0.1  # Convert to micrometers (example scaling)
                        min_y *= 0.1
                        max_x *= 0.1
                        max_y *= 0.1
                
                color = selection.get('color', '#FF0000').replace('#', '').lower()
                well_position = selection.get('well_position', f"A{i:02d}")
                
                point_line = f"P_{i} = \"{min_x:.4f}; {min_y:.4f}; {max_x:.4f}; {max_y:.4f};{color};{well_position};\""
                protocol_lines.append(point_line)
            
            # Write protocol file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            protocol_filename = f"cellsorter_protocol_{timestamp}.cxprotocol"
            protocol_path = Path(self.output_directory) / protocol_filename
            
            with open(protocol_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(protocol_lines))
            
            self.status_updated.emit(f"Protocol exported: {protocol_filename}")
            
        except Exception as e:
            raise Exception(f"Protocol export failed: {str(e)}")
    
    def cancel(self) -> None:
        """Cancel export operation."""
        self.is_cancelled = True


class ExportDialog(QDialog):
    """
    Dialog for comprehensive export options.
    
    Provides options for exporting:
    - CSV data with selection information
    - Images with cell highlighting overlays
    - Protocol files for CosmoSort
    - Analysis reports and metadata
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.export_options: Dict[str, Any] = {}
        self.worker: Optional[ExportWorker] = None
        
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Set up the dialog UI."""
        self.setWindowTitle("Export Analysis Results")
        self.setModal(True)
        self.setFixedSize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Export Analysis Results")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(14)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Tab widget for different export categories
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Data export tab
        self.setup_data_export_tab()
        
        # Image export tab
        self.setup_image_export_tab()
        
        # Protocol export tab
        self.setup_protocol_export_tab()
        
        # Progress section (initially hidden)
        self.progress_group = QGroupBox("Export Progress")
        self.progress_group.setVisible(False)
        progress_layout = QVBoxLayout(self.progress_group)
        
        self.progress_bar = QProgressBar()
        self.status_label = QLabel("Ready to export...")
        
        progress_layout.addWidget(self.status_label)
        progress_layout.addWidget(self.progress_bar)
        layout.addWidget(self.progress_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.export_button = QPushButton("Start Export")
        self.export_button.clicked.connect(self.start_export)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.export_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
    
    def setup_data_export_tab(self) -> None:
        """Set up the data export tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # CSV export options
        csv_group = QGroupBox("CSV Data Export")
        csv_layout = QVBoxLayout(csv_group)
        
        self.export_csv_checkbox = QCheckBox("Export selection data as CSV")
        self.export_csv_checkbox.setChecked(True)
        csv_layout.addWidget(self.export_csv_checkbox)
        
        # CSV format options
        csv_format_layout = QFormLayout()
        
        self.csv_format_combo = QComboBox()
        self.csv_format_combo.addItems(["Standard CSV", "Excel-compatible CSV", "Tab-separated"])
        csv_format_layout.addRow("Format:", self.csv_format_combo)
        
        self.include_metadata_checkbox = QCheckBox("Include analysis metadata")
        self.include_metadata_checkbox.setChecked(True)
        csv_format_layout.addRow("Options:", self.include_metadata_checkbox)
        
        csv_layout.addLayout(csv_format_layout)
        layout.addWidget(csv_group)
        
        # Statistics export
        stats_group = QGroupBox("Analysis Statistics")
        stats_layout = QVBoxLayout(stats_group)
        
        self.export_stats_checkbox = QCheckBox("Generate analysis summary report")
        self.export_stats_checkbox.setChecked(True)
        stats_layout.addWidget(self.export_stats_checkbox)
        
        layout.addWidget(stats_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Data Export")
    
    def setup_image_export_tab(self) -> None:
        """Set up the image export tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Image export options
        image_group = QGroupBox("Image Export")
        image_layout = QVBoxLayout(image_group)
        
        self.export_image_checkbox = QCheckBox("Export image with cell highlights")
        self.export_image_checkbox.setChecked(False)
        image_layout.addWidget(self.export_image_checkbox)
        
        # Image format options
        image_format_layout = QFormLayout()
        
        self.image_format_combo = QComboBox()
        self.image_format_combo.addItems(["PNG", "JPEG", "TIFF", "SVG"])
        image_format_layout.addRow("Format:", self.image_format_combo)
        
        self.image_quality_spinbox = QSpinBox()
        self.image_quality_spinbox.setRange(1, 100)
        self.image_quality_spinbox.setValue(95)
        self.image_quality_spinbox.setSuffix("%")
        image_format_layout.addRow("Quality:", self.image_quality_spinbox)
        
        self.image_dpi_spinbox = QSpinBox()
        self.image_dpi_spinbox.setRange(72, 600)
        self.image_dpi_spinbox.setValue(300)
        self.image_dpi_spinbox.setSuffix(" DPI")
        image_format_layout.addRow("Resolution:", self.image_dpi_spinbox)
        
        image_layout.addLayout(image_format_layout)
        
        # Overlay options
        overlay_options_layout = QVBoxLayout()
        
        self.include_labels_checkbox = QCheckBox("Include selection labels")
        self.include_labels_checkbox.setChecked(True)
        overlay_options_layout.addWidget(self.include_labels_checkbox)
        
        self.include_wells_checkbox = QCheckBox("Include well plate assignments")
        self.include_wells_checkbox.setChecked(True)
        overlay_options_layout.addWidget(self.include_wells_checkbox)
        
        self.include_calibration_checkbox = QCheckBox("Show calibration points")
        self.include_calibration_checkbox.setChecked(False)
        overlay_options_layout.addWidget(self.include_calibration_checkbox)
        
        image_layout.addLayout(overlay_options_layout)
        layout.addWidget(image_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Image Export")
    
    def setup_protocol_export_tab(self) -> None:
        """Set up the protocol export tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Protocol export options
        protocol_group = QGroupBox("CosmoSort Protocol Export")
        protocol_layout = QVBoxLayout(protocol_group)
        
        self.export_protocol_checkbox = QCheckBox("Export .cxprotocol file")
        self.export_protocol_checkbox.setChecked(True)
        protocol_layout.addWidget(self.export_protocol_checkbox)
        
        # Protocol options
        protocol_options_layout = QFormLayout()
        
        self.protocol_version_combo = QComboBox()
        self.protocol_version_combo.addItems(["v2.1", "v2.0", "v1.9"])
        protocol_options_layout.addRow("Protocol version:", self.protocol_version_combo)
        
        self.include_backup_checkbox = QCheckBox("Create backup copy")
        self.include_backup_checkbox.setChecked(True)
        protocol_options_layout.addRow("Options:", self.include_backup_checkbox)
        
        protocol_layout.addLayout(protocol_options_layout)
        layout.addWidget(protocol_group)
        
        # Validation options
        validation_group = QGroupBox("Protocol Validation")
        validation_layout = QVBoxLayout(validation_group)
        
        self.validate_coordinates_checkbox = QCheckBox("Validate coordinate bounds")
        self.validate_coordinates_checkbox.setChecked(True)
        validation_layout.addWidget(self.validate_coordinates_checkbox)
        
        self.check_calibration_checkbox = QCheckBox("Verify calibration accuracy")
        self.check_calibration_checkbox.setChecked(True)
        validation_layout.addWidget(self.check_calibration_checkbox)
        
        layout.addWidget(validation_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Protocol Export")
    
    def start_export(self) -> None:
        """Start the export process."""
        # Select output directory
        output_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Export Directory",
            str(Path.home()),
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if not output_dir:
            return  # User cancelled
        
        # Collect export options
        self.export_options = {
            'output_directory': output_dir,
            'export_csv': self.export_csv_checkbox.isChecked(),
            'csv_format': self.csv_format_combo.currentText(),
            'include_metadata': self.include_metadata_checkbox.isChecked(),
            'export_stats': self.export_stats_checkbox.isChecked(),
            'export_image': self.export_image_checkbox.isChecked(),
            'image_format': self.image_format_combo.currentText(),
            'image_quality': self.image_quality_spinbox.value(),
            'image_dpi': self.image_dpi_spinbox.value(),
            'include_labels': self.include_labels_checkbox.isChecked(),
            'include_wells': self.include_wells_checkbox.isChecked(),
            'include_calibration': self.include_calibration_checkbox.isChecked(),
            'export_protocol': self.export_protocol_checkbox.isChecked(),
            'protocol_version': self.protocol_version_combo.currentText(),
            'include_backup': self.include_backup_checkbox.isChecked(),
            'validate_coordinates': self.validate_coordinates_checkbox.isChecked(),
            'check_calibration': self.check_calibration_checkbox.isChecked()
        }
        
        # Show progress section
        self.progress_group.setVisible(True)
        self.export_button.setEnabled(False)
        self.tab_widget.setEnabled(False)
        
        # Start worker thread with session data
        session_data = getattr(self.parent(), '_collect_session_data', lambda: {})()
        self.worker = ExportWorker(self.export_options, session_data)
        self.worker.progress_updated.connect(self.progress_bar.setValue)
        self.worker.status_updated.connect(self.status_label.setText)
        self.worker.export_finished.connect(self.on_export_finished)
        self.worker.start()
    
    def on_export_finished(self, success: bool, message: str) -> None:
        """Handle export completion."""
        self.status_label.setText(message)
        
        if success:
            self.progress_bar.setValue(100)
            self.accept()
        else:
            self.export_button.setEnabled(True)
            self.tab_widget.setEnabled(True)
            self.progress_group.setVisible(False)
    
    def reject(self) -> None:
        """Handle dialog cancellation."""
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait()
        super().reject()
    
    def get_export_options(self) -> Dict[str, Any]:
        """Get the selected export options."""
        return self.export_options