"""
Batch Processing Dialog for CellSorter

This dialog allows users to process multiple image/CSV pairs
with consistent analysis criteria and settings.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import time
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QPushButton,
    QDialogButtonBox, QGroupBox, QListWidget, QListWidgetItem, QTextEdit,
    QProgressBar, QTabWidget, QWidget, QCheckBox, QSpinBox, QDoubleSpinBox,
    QComboBox, QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QIcon


class BatchProcessor(QThread):
    """Worker thread for batch processing operations."""
    
    progress_updated = Signal(int)  # percentage
    status_updated = Signal(str)    # status message
    file_processed = Signal(str, bool, str)  # file_path, success, message
    batch_finished = Signal(bool, str)  # success, summary_message
    
    def __init__(self, file_pairs: List[Dict[str, str]], processing_options: Dict[str, Any]):
        super().__init__()
        self.file_pairs = file_pairs
        self.processing_options = processing_options
        self.is_cancelled = False
        self.processed_count = 0
        self.success_count = 0
        self.failed_files = []
        
    def run(self) -> None:
        """Execute batch processing operations."""
        try:
            total_files = len(self.file_pairs)
            self.status_updated.emit(f"Starting batch processing of {total_files} file pairs...")
            
            for i, file_pair in enumerate(self.file_pairs):
                if self.is_cancelled:
                    break
                
                image_path = file_pair.get('image_path', '')
                csv_path = file_pair.get('csv_path', '')
                
                # Update progress
                progress = int((i / total_files) * 100)
                self.progress_updated.emit(progress)
                self.status_updated.emit(f"Processing {Path(image_path).name}...")
                
                # Process file pair
                success, message = self._process_file_pair(image_path, csv_path)
                
                # Update counters
                self.processed_count += 1
                if success:
                    self.success_count += 1
                else:
                    self.failed_files.append({
                        'image': image_path,
                        'csv': csv_path,
                        'error': message
                    })
                
                # Emit file completion signal
                self.file_processed.emit(f"{Path(image_path).name} + {Path(csv_path).name}", success, message)
                
                # Small delay to prevent overwhelming the UI
                time.sleep(0.1)
            
            # Final progress
            self.progress_updated.emit(100)
            
            # Generate summary
            if self.is_cancelled:
                summary = f"Batch processing cancelled. Processed {self.processed_count}/{total_files} files."
            else:
                summary = f"Batch processing completed. Success: {self.success_count}/{total_files} files."
                if self.failed_files:
                    summary += f" Failed: {len(self.failed_files)} files."
            
            self.batch_finished.emit(not bool(self.failed_files), summary)
            
        except Exception as e:
            self.batch_finished.emit(False, f"Batch processing failed: {str(e)}")
    
    def _process_file_pair(self, image_path: str, csv_path: str) -> tuple[bool, str]:
        """
        Process a single image/CSV pair.
        
        Args:
            image_path: Path to image file
            csv_path: Path to CSV file
        
        Returns:
            Tuple of (success, message)
        """
        try:
            # Validate files exist
            if not Path(image_path).exists():
                return False, f"Image file not found: {image_path}"
            
            if not Path(csv_path).exists():
                return False, f"CSV file not found: {csv_path}"
            
            # Simulate processing (in real implementation, this would load and process the files)
            # For now, we'll just validate file sizes and formats
            image_size = Path(image_path).stat().st_size / (1024 * 1024)  # MB
            csv_size = Path(csv_path).stat().st_size / (1024 * 1024)  # MB
            
            # Check file size limits
            max_image_size = self.processing_options.get('max_image_size_mb', 500)
            max_csv_size = self.processing_options.get('max_csv_size_mb', 100)
            
            if image_size > max_image_size:
                return False, f"Image file too large: {image_size:.1f}MB > {max_image_size}MB"
            
            if csv_size > max_csv_size:
                return False, f"CSV file too large: {csv_size:.1f}MB > {max_csv_size}MB"
            
            # Check file formats
            image_ext = Path(image_path).suffix.lower()
            if image_ext not in ['.tiff', '.tif', '.jpg', '.jpeg', '.png']:
                return False, f"Unsupported image format: {image_ext}"
            
            if not Path(csv_path).suffix.lower() == '.csv':
                return False, f"Not a CSV file: {csv_path}"
            
            # Simulate processing time
            processing_time = self.processing_options.get('simulated_processing_time', 0.5)
            time.sleep(processing_time)
            
            return True, "Processing completed successfully"
            
        except Exception as e:
            return False, f"Processing error: {str(e)}"
    
    def cancel(self) -> None:
        """Cancel batch processing operation."""
        self.is_cancelled = True


class BatchProcessDialog(QDialog):
    """
    Dialog for batch processing multiple image/CSV file pairs.
    
    Allows users to:
    - Select multiple image and CSV file pairs
    - Configure processing parameters
    - Monitor processing progress
    - Review results and failures
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.file_pairs: List[Dict[str, str]] = []
        self.processing_options: Dict[str, Any] = {}
        self.processor: Optional[BatchProcessor] = None
        
        self.setup_ui()
        self.load_default_settings()
        
    def setup_ui(self) -> None:
        """Set up the dialog UI."""
        self.setWindowTitle("Batch Process Files")
        self.setModal(True)
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Batch Process Multiple Files")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(14)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Tab widget for different sections
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # File selection tab
        self.setup_file_selection_tab()
        
        # Processing options tab
        self.setup_processing_options_tab()
        
        # Progress and results tab
        self.setup_progress_tab()
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.add_files_button = QPushButton("Add File Pairs")
        self.add_files_button.clicked.connect(self.add_file_pairs)
        
        self.remove_files_button = QPushButton("Remove Selected")
        self.remove_files_button.clicked.connect(self.remove_selected_files)
        self.remove_files_button.setEnabled(False)
        
        self.start_button = QPushButton("Start Processing")
        self.start_button.clicked.connect(self.start_processing)
        self.start_button.setEnabled(False)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_processing)
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        
        button_layout.addWidget(self.add_files_button)
        button_layout.addWidget(self.remove_files_button)
        button_layout.addStretch()
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
    
    def setup_file_selection_tab(self) -> None:
        """Set up the file selection tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Instructions
        instructions = QLabel("Select image and CSV file pairs for batch processing:")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # File list table
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(3)
        self.file_table.setHorizontalHeaderLabels(["Image File", "CSV File", "Status"])
        self.file_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.file_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.file_table.itemSelectionChanged.connect(self.on_file_selection_changed)
        layout.addWidget(self.file_table)
        
        # File statistics
        self.file_stats_label = QLabel("No files selected")
        layout.addWidget(self.file_stats_label)
        
        self.tab_widget.addTab(tab, "File Selection")
    
    def setup_processing_options_tab(self) -> None:
        """Set up the processing options tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Performance options
        perf_group = QGroupBox("Performance Settings")
        perf_layout = QFormLayout(perf_group)
        
        self.max_image_size_spinbox = QSpinBox()
        self.max_image_size_spinbox.setRange(10, 2000)
        self.max_image_size_spinbox.setValue(500)
        self.max_image_size_spinbox.setSuffix(" MB")
        perf_layout.addRow("Max Image Size:", self.max_image_size_spinbox)
        
        self.max_csv_size_spinbox = QSpinBox()
        self.max_csv_size_spinbox.setRange(1, 500)
        self.max_csv_size_spinbox.setValue(100)
        self.max_csv_size_spinbox.setSuffix(" MB")
        perf_layout.addRow("Max CSV Size:", self.max_csv_size_spinbox)
        
        self.processing_timeout_spinbox = QSpinBox()
        self.processing_timeout_spinbox.setRange(30, 600)
        self.processing_timeout_spinbox.setValue(120)
        self.processing_timeout_spinbox.setSuffix(" seconds")
        perf_layout.addRow("Processing Timeout:", self.processing_timeout_spinbox)
        
        layout.addWidget(perf_group)
        
        # Error handling options
        error_group = QGroupBox("Error Handling")
        error_layout = QVBoxLayout(error_group)
        
        self.continue_on_error_checkbox = QCheckBox("Continue processing on errors")
        self.continue_on_error_checkbox.setChecked(True)
        error_layout.addWidget(self.continue_on_error_checkbox)
        
        self.save_error_log_checkbox = QCheckBox("Save detailed error log")
        self.save_error_log_checkbox.setChecked(True)
        error_layout.addWidget(self.save_error_log_checkbox)
        
        layout.addWidget(error_group)
        
        # Output options
        output_group = QGroupBox("Output Options")
        output_layout = QFormLayout(output_group)
        
        self.output_format_combo = QComboBox()
        self.output_format_combo.addItems(["CosmoSort Protocol", "CSV Export", "Both"])
        output_layout.addRow("Output Format:", self.output_format_combo)
        
        self.output_naming_combo = QComboBox()
        self.output_naming_combo.addItems(["Use Original Names", "Add Timestamp", "Sequential Numbering"])
        self.output_naming_combo.setCurrentText("Add Timestamp")
        output_layout.addRow("Output Naming:", self.output_naming_combo)
        
        layout.addWidget(output_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Processing Options")
    
    def setup_progress_tab(self) -> None:
        """Set up the progress and results tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Progress section
        progress_group = QGroupBox("Processing Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_status_label = QLabel("Ready to start processing")
        
        progress_layout.addWidget(self.progress_status_label)
        progress_layout.addWidget(self.progress_bar)
        layout.addWidget(progress_group)
        
        # Results section
        results_group = QGroupBox("Processing Results")
        results_layout = QVBoxLayout(results_group)
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMaximumHeight(200)
        results_layout.addWidget(self.results_text)
        
        layout.addWidget(results_group)
        
        # Summary section
        self.summary_label = QLabel("")
        self.summary_label.setStyleSheet("QLabel { font-weight: bold; }")
        layout.addWidget(self.summary_label)
        
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Progress & Results")
    
    def add_file_pairs(self) -> None:
        """Add image/CSV file pairs for processing."""
        # Select multiple image files
        image_files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Image Files",
            "",
            "Image Files (*.tiff *.tif *.jpg *.jpeg *.png)"
        )
        
        if not image_files:
            return
        
        # For each image, ask for corresponding CSV
        added_count = 0
        for image_file in image_files:
            # Suggest CSV file with same base name
            image_path = Path(image_file)
            suggested_csv = image_path.with_suffix('.csv')
            
            csv_file, _ = QFileDialog.getOpenFileName(
                self,
                f"Select CSV file for {image_path.name}",
                str(suggested_csv),
                "CSV Files (*.csv)"
            )
            
            if csv_file:
                # Add to file pairs
                file_pair = {
                    'image_path': image_file,
                    'csv_path': csv_file
                }
                self.file_pairs.append(file_pair)
                added_count += 1
        
        if added_count > 0:
            self.update_file_table()
            self.update_file_statistics()
            QMessageBox.information(self, "Files Added", f"Added {added_count} file pairs for processing.")
    
    def remove_selected_files(self) -> None:
        """Remove selected file pairs."""
        selected_rows = set()
        for item in self.file_table.selectedItems():
            selected_rows.add(item.row())
        
        # Remove in reverse order to maintain indices
        for row in sorted(selected_rows, reverse=True):
            if 0 <= row < len(self.file_pairs):
                del self.file_pairs[row]
        
        self.update_file_table()
        self.update_file_statistics()
    
    def update_file_table(self) -> None:
        """Update the file table display."""
        self.file_table.setRowCount(len(self.file_pairs))
        
        for i, file_pair in enumerate(self.file_pairs):
            # Image file
            image_item = QTableWidgetItem(Path(file_pair['image_path']).name)
            image_item.setToolTip(file_pair['image_path'])
            self.file_table.setItem(i, 0, image_item)
            
            # CSV file
            csv_item = QTableWidgetItem(Path(file_pair['csv_path']).name)
            csv_item.setToolTip(file_pair['csv_path'])
            self.file_table.setItem(i, 1, csv_item)
            
            # Status
            status_item = QTableWidgetItem("Ready")
            self.file_table.setItem(i, 2, status_item)
        
        # Update button states
        self.start_button.setEnabled(len(self.file_pairs) > 0)
    
    def update_file_statistics(self) -> None:
        """Update file statistics display."""
        count = len(self.file_pairs)
        if count == 0:
            self.file_stats_label.setText("No files selected")
        else:
            self.file_stats_label.setText(f"{count} file pair(s) ready for processing")
    
    def on_file_selection_changed(self) -> None:
        """Handle file selection changes."""
        has_selection = len(self.file_table.selectedItems()) > 0
        self.remove_files_button.setEnabled(has_selection)
    
    def load_default_settings(self) -> None:
        """Load default processing settings."""
        self.processing_options = {
            'max_image_size_mb': 500,
            'max_csv_size_mb': 100,
            'processing_timeout': 120,
            'continue_on_error': True,
            'save_error_log': True,
            'output_format': 'CosmoSort Protocol',
            'output_naming': 'Add Timestamp',
            'simulated_processing_time': 0.5  # For demo purposes
        }
    
    def start_processing(self) -> None:
        """Start batch processing."""
        if not self.file_pairs:
            QMessageBox.warning(self, "No Files", "Please add file pairs before starting.")
            return
        
        # Collect current processing options
        self.processing_options.update({
            'max_image_size_mb': self.max_image_size_spinbox.value(),
            'max_csv_size_mb': self.max_csv_size_spinbox.value(),
            'processing_timeout': self.processing_timeout_spinbox.value(),
            'continue_on_error': self.continue_on_error_checkbox.isChecked(),
            'save_error_log': self.save_error_log_checkbox.isChecked(),
            'output_format': self.output_format_combo.currentText(),
            'output_naming': self.output_naming_combo.currentText()
        })
        
        # Switch to progress tab
        self.tab_widget.setCurrentIndex(2)
        
        # Reset progress display
        self.progress_bar.setValue(0)
        self.results_text.clear()
        self.summary_label.setText("")
        
        # Disable controls
        self.start_button.setEnabled(False)
        self.add_files_button.setEnabled(False)
        self.remove_files_button.setEnabled(False)
        self.tab_widget.setTabEnabled(0, False)
        self.tab_widget.setTabEnabled(1, False)
        
        # Start processing
        self.processor = BatchProcessor(self.file_pairs, self.processing_options)
        self.processor.progress_updated.connect(self.progress_bar.setValue)
        self.processor.status_updated.connect(self.progress_status_label.setText)
        self.processor.file_processed.connect(self.on_file_processed)
        self.processor.batch_finished.connect(self.on_batch_finished)
        self.processor.start()
    
    def cancel_processing(self) -> None:
        """Cancel ongoing processing."""
        if self.processor and self.processor.isRunning():
            self.processor.cancel()
            self.progress_status_label.setText("Cancelling processing...")
        else:
            self.reject()
    
    def on_file_processed(self, file_name: str, success: bool, message: str) -> None:
        """Handle individual file processing completion."""
        status = "✅ SUCCESS" if success else "❌ FAILED"
        result_line = f"{status}: {file_name} - {message}"
        self.results_text.append(result_line)
        
        # Scroll to bottom
        cursor = self.results_text.textCursor()
        cursor.movePosition(cursor.End)
        self.results_text.setTextCursor(cursor)
    
    def on_batch_finished(self, success: bool, summary: str) -> None:
        """Handle batch processing completion."""
        self.progress_status_label.setText("Processing completed")
        self.summary_label.setText(summary)
        
        # Re-enable controls
        self.start_button.setEnabled(True)
        self.add_files_button.setEnabled(True)
        self.remove_files_button.setEnabled(True)
        self.tab_widget.setTabEnabled(0, True)
        self.tab_widget.setTabEnabled(1, True)
        
        # Show completion message
        if success:
            QMessageBox.information(self, "Processing Complete", summary)
        else:
            QMessageBox.warning(self, "Processing Issues", summary)
    
    def reject(self) -> None:
        """Handle dialog cancellation."""
        if self.processor and self.processor.isRunning():
            reply = QMessageBox.question(
                self,
                "Cancel Processing",
                "Processing is still running. Do you want to cancel it?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.processor.cancel()
                self.processor.wait()
            else:
                return
        
        super().reject()