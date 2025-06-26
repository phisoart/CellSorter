"""
Enhanced Calibration Dialog for CellSorter (TASK-022)
"""

from typing import Optional, Tuple, Dict, Any
from enum import Enum
from pathlib import Path
from datetime import datetime
import json

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QPushButton,
    QDoubleSpinBox, QDialogButtonBox, QGroupBox, QTextEdit, QProgressBar,
    QStackedWidget, QWidget, QFrame, QGridLayout, QSpacerItem, QSizePolicy,
    QCheckBox, QComboBox, QLineEdit, QMessageBox, QFileDialog, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor, QPen, QIcon

from models.coordinate_transformer import CoordinateTransformer, CalibrationPoint
from utils.logging_config import LoggerMixin


class CalibrationStep(Enum):
    """Calibration wizard steps."""
    INTRODUCTION = 0
    FIRST_POINT = 1
    SECOND_POINT = 2
    QUALITY_CHECK = 3
    SAVE_TEMPLATE = 4


class CalibrationWizardDialog(QDialog, LoggerMixin):
    """Enhanced calibration dialog with step-by-step wizar interface."""
    
    # Signals
    calibration_completed = Signal(bool)
    point_added = Signal(int, int, float, float, str)
    
    def __init__(self, coordinate_transformer: CoordinateTransformer, 
                 initial_pixel_x: int = 0, initial_pixel_y: int = 0, 
                 initial_label: str = "Point 1", parent=None):
        super().__init__(parent)
        
        self.coordinate_transformer = coordinate_transformer
        self.initial_pixel_x = initial_pixel_x
        self.initial_pixel_y = initial_pixel_y
        self.initial_label = initial_label
        
        # Wizard state
        self.current_step = CalibrationStep.INTRODUCTION
        
        # UI components
        self.stacked_widget: Optional[QStackedWidget] = None
        self.progress_bar: Optional[QProgressBar] = None
        self.next_button: Optional[QPushButton] = None
        self.back_button: Optional[QPushButton] = None
        self.finish_button: Optional[QPushButton] = None
        self.status_label: Optional[QLabel] = None
        
        self.setup_ui()
        self.update_ui_state()
        
        self.log_info("Enhanced calibration wizard dialog initialized")
        
    def setup_ui(self) -> None:
        """Set up the enhanced wizard UI."""
        self.setWindowTitle("Calibration Wizard - CellSorter")
        self.setModal(True)
        self.setFixedSize(600, 500)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        
        # Header with progress
        header_frame = self.create_header()
        main_layout.addWidget(header_frame)
        
        # Stacked widget for different steps
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)
        
        # Create basic step widgets
        self.create_basic_steps()
        
        # Footer with navigation buttons
        footer_frame = self.create_footer()
        main_layout.addWidget(footer_frame)
        
        # Status area
        self.status_label = QLabel("Ready to start calibration")
        self.status_label.setStyleSheet("QLabel { color: #666; font-style: italic; }")
        main_layout.addWidget(self.status_label)
    
    def create_header(self) -> QFrame:
        """Create header with title and progress bar."""
        header = QFrame()
        header.setFrameStyle(QFrame.StyledPanel)
        header.setStyleSheet("QFrame { background-color: #f8f9fa; border: 1px solid #dee2e6; }")
        
        layout = QVBoxLayout(header)
        
        # Title
        title = QLabel("Coordinate Calibration Wizard")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(14)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Step %v of 5")
        layout.addWidget(self.progress_bar)
        
        return header
    
    def create_footer(self) -> QFrame:
        """Create footer with navigation buttons."""
        footer = QFrame()
        layout = QHBoxLayout(footer)
        
        # Back button
        self.back_button = QPushButton("�� Back")
        self.back_button.clicked.connect(self.go_back)
        self.back_button.setEnabled(False)
        layout.addWidget(self.back_button)
        
        # Spacer
        layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        # Next button
        self.next_button = QPushButton("Next ��")
        self.next_button.clicked.connect(self.go_next)
        layout.addWidget(self.next_button)
        
        # Finish button
        self.finish_button = QPushButton("Finish")
        self.finish_button.clicked.connect(self.finish_calibration)
        self.finish_button.setVisible(False)
        layout.addWidget(self.finish_button)
        
        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        layout.addWidget(cancel_button)
        
        return footer
    
    def create_basic_steps(self) -> None:
        """Create basic step widgets."""
        # Introduction step
        self.create_introduction_step()
        
        # First point step
        self.create_first_point_step()
        
        # Second point step
        self.create_second_point_step()
        
        # Quality check step
        self.create_quality_step()
        
        # Template step
        self.create_template_step()
    
    def create_introduction_step(self) -> None:
        """Create introduction step widget."""
        intro_widget = QWidget()
        intro_layout = QVBoxLayout(intro_widget)
        
        welcome = QLabel("Welcome to the Coordinate Calibration Wizard")
        welcome_font = QFont()
        welcome_font.setBold(True)
        welcome_font.setPointSize(12)
        welcome.setFont(welcome_font)
        intro_layout.addWidget(welcome)
        
        instructions = QTextEdit()
        instructions.setReadOnly(True)
        instructions.setMaximumHeight(300)
        instructions.setHtml("""
        <h4>What is coordinate calibration?</h4>
        <p>Coordinate calibration establishes the relationship between pixel coordinates 
        in your microscopy image and real-world stage coordinates in micrometers.</p>
        
        <h4>What you'll need:</h4>
        <ul>
        <li>Two reference points that are clearly visible in your image</li>
        <li>The corresponding XY stage coordinates for these points</li>
        <li>Points should be far apart for better accuracy (minimum 50 pixels)</li>
        </ul>
        
        <h4>The calibration process:</h4>
        <ol>
        <li>Click two reference points on your image</li>
        <li>Enter the corresponding stage coordinates for each point</li>
        <li>Review the calibration quality and accuracy</li>
        <li>Optionally save the calibration as a template</li>
        </ol>
        """)
        intro_layout.addWidget(instructions)
        
        # Current calibration status
        if len(self.coordinate_transformer.calibration_points) > 0:
            status_group = QGroupBox("Current Calibration Status")
            status_layout = QVBoxLayout(status_group)
            
            status_text = f"Existing calibration with {len(self.coordinate_transformer.calibration_points)} points"
            if self.coordinate_transformer.is_calibrated:
                status_text += " (Active)"
            else:
                status_text += " (Incomplete)"
            
            status_layout.addWidget(QLabel(status_text))
            intro_layout.addWidget(status_group)
        
        self.stacked_widget.addWidget(intro_widget)
    
    def create_first_point_step(self) -> None:
        """Create first point calibration step."""
        point1_widget = QWidget()
        layout = QVBoxLayout(point1_widget)
        
        # Step title
        title = QLabel("Step 1: First Calibration Point")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(11)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Instructions
        instructions = QLabel(
            "Click on a clearly visible reference point in your image, then enter "
            "the corresponding stage coordinates below."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("QLabel { color: #495057; margin: 10px 0; }")
        layout.addWidget(instructions)
        
        # Pixel coordinates (display only)
        pixel_group = QGroupBox("Image Coordinates (Read-Only)")
        pixel_layout = QFormLayout(pixel_group)
        
        self.pixel1_x_label = QLabel(str(self.initial_pixel_x))
        self.pixel1_y_label = QLabel(str(self.initial_pixel_y))
        
        for label in [self.pixel1_x_label, self.pixel1_y_label]:
            label.setStyleSheet("QLabel { font-family: monospace; font-weight: bold; background: #f8f9fa; padding: 5px; border: 1px solid #dee2e6; }")
        
        pixel_layout.addRow("X (pixels):", self.pixel1_x_label)
        pixel_layout.addRow("Y (pixels):", self.pixel1_y_label)
        layout.addWidget(pixel_group)
        
        # Stage coordinates input
        stage_group = QGroupBox("Stage Coordinates (Required)")
        stage_layout = QFormLayout(stage_group)
        
        self.point1_x_input = QDoubleSpinBox()
        self.point1_x_input.setRange(-999999.999, 999999.999)
        self.point1_x_input.setDecimals(3)
        self.point1_x_input.setSuffix(" µm")
        self.point1_x_input.setMinimumWidth(150)
        self.point1_x_input.valueChanged.connect(self.validate_point1)
        
        self.point1_y_input = QDoubleSpinBox()
        self.point1_y_input.setRange(-999999.999, 999999.999)
        self.point1_y_input.setDecimals(3)
        self.point1_y_input.setSuffix(" µm")
        self.point1_y_input.setMinimumWidth(150)
        self.point1_y_input.valueChanged.connect(self.validate_point1)
        
        stage_layout.addRow("X (µm):", self.point1_x_input)
        stage_layout.addRow("Y (µm):", self.point1_y_input)
        layout.addWidget(stage_group)
        
        # Validation status
        self.point1_status = QLabel("⚠️ Please enter stage coordinates")
        self.point1_status.setStyleSheet("QLabel { color: #856404; background: #fff3cd; padding: 8px; border: 1px solid #ffeaa7; border-radius: 4px; }")
        layout.addWidget(self.point1_status)
        
        # Tips
        tips = QLabel("""
        💡 <strong>Tips:</strong><br>
        • Get coordinates from your microscope's stage position display<br>
        • Choose a distinctive feature (cell corner, fiducial marker, etc.)<br>
        • Record coordinates precisely to the nearest micrometer
        """)
        tips.setWordWrap(True)
        tips.setStyleSheet("QLabel { background: #e7f3ff; padding: 10px; border-left: 4px solid #0066cc; margin: 10px 0; }")
        layout.addWidget(tips)
        
        self.stacked_widget.addWidget(point1_widget)
    
    def create_second_point_step(self) -> None:
        """Create second point calibration step."""
        point2_widget = QWidget()
        layout = QVBoxLayout(point2_widget)
        
        # Step title
        title = QLabel("Step 2: Second Calibration Point")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(11)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Instructions
        instructions = QLabel(
            "Click on a second reference point that is far from the first point "
            "(minimum 50 pixels apart), then enter its stage coordinates."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("QLabel { color: #495057; margin: 10px 0; }")
        layout.addWidget(instructions)
        
        # Distance indicator
        self.distance_label = QLabel("Distance from first point: Not set")
        self.distance_label.setStyleSheet("QLabel { font-weight: bold; }")
        layout.addWidget(self.distance_label)
        
        # Pixel coordinates (display only)
        pixel_group = QGroupBox("Image Coordinates (Read-Only)")
        pixel_layout = QFormLayout(pixel_group)
        
        self.pixel2_x_label = QLabel("Click on image")
        self.pixel2_y_label = QLabel("Click on image")
        
        for label in [self.pixel2_x_label, self.pixel2_y_label]:
            label.setStyleSheet("QLabel { font-family: monospace; font-weight: bold; background: #f8f9fa; padding: 5px; border: 1px solid #dee2e6; }")
        
        pixel_layout.addRow("X (pixels):", self.pixel2_x_label)
        pixel_layout.addRow("Y (pixels):", self.pixel2_y_label)
        layout.addWidget(pixel_group)
        
        # Stage coordinates input
        stage_group = QGroupBox("Stage Coordinates (Required)")
        stage_layout = QFormLayout(stage_group)
        
        self.point2_x_input = QDoubleSpinBox()
        self.point2_x_input.setRange(-999999.999, 999999.999)
        self.point2_x_input.setDecimals(3)
        self.point2_x_input.setSuffix(" µm")
        self.point2_x_input.setMinimumWidth(150)
        self.point2_x_input.valueChanged.connect(self.validate_point2)
        
        self.point2_y_input = QDoubleSpinBox()
        self.point2_y_input.setRange(-999999.999, 999999.999)
        self.point2_y_input.setDecimals(3)
        self.point2_y_input.setSuffix(" µm")
        self.point2_y_input.setMinimumWidth(150)
        self.point2_y_input.valueChanged.connect(self.validate_point2)
        
        stage_layout.addRow("X (µm):", self.point2_x_input)
        stage_layout.addRow("Y (µm):", self.point2_y_input)
        layout.addWidget(stage_group)
        
        # Validation status
        self.point2_status = QLabel("⚠️ Please click second point and enter coordinates")
        self.point2_status.setStyleSheet("QLabel { color: #856404; background: #fff3cd; padding: 8px; border: 1px solid #ffeaa7; border-radius: 4px; }")
        layout.addWidget(self.point2_status)
        
        self.stacked_widget.addWidget(point2_widget)
    
    def create_quality_step(self) -> None:
        """Create calibration quality assessment step."""
        quality_widget = QWidget()
        layout = QVBoxLayout(quality_widget)
        
        # Step title
        title = QLabel("Step 3: Calibration Quality Assessment")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(11)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Quality overview
        quality_group = QGroupBox("Calibration Quality")
        quality_layout = QGridLayout(quality_group)
        
        # Overall quality indicator
        quality_layout.addWidget(QLabel("Overall Quality:"), 0, 0)
        self.quality_progress = QProgressBar()
        self.quality_progress.setRange(0, 100)
        self.quality_progress.setTextVisible(True)
        self.quality_progress.setFormat("%p%")
        quality_layout.addWidget(self.quality_progress, 0, 1)
        
        # Quality metrics
        self.avg_error_label = QLabel("Average Error: --")
        self.max_error_label = QLabel("Maximum Error: --")
        self.confidence_label = QLabel("Confidence: --")
        self.accuracy_status_label = QLabel("Accuracy: --")
        
        quality_layout.addWidget(self.avg_error_label, 1, 0, 1, 2)
        quality_layout.addWidget(self.max_error_label, 2, 0, 1, 2)
        quality_layout.addWidget(self.confidence_label, 3, 0, 1, 2)
        quality_layout.addWidget(self.accuracy_status_label, 4, 0, 1, 2)
        
        layout.addWidget(quality_group)
        
        # Point summary
        points_group = QGroupBox("Calibration Points Summary")
        points_layout = QVBoxLayout(points_group)
        
        self.points_summary = QTextEdit()
        self.points_summary.setReadOnly(True)
        self.points_summary.setMaximumHeight(120)
        points_layout.addWidget(self.points_summary)
        
        layout.addWidget(points_group)
        
        # Recommendations
        self.recommendations_label = QLabel("")
        self.recommendations_label.setWordWrap(True)
        self.recommendations_label.setStyleSheet("QLabel { background: #e7f3ff; padding: 10px; border-left: 4px solid #0066cc; margin: 10px 0; }")
        layout.addWidget(self.recommendations_label)
        
        # Actions
        actions_group = QGroupBox("Options")
        actions_layout = QHBoxLayout(actions_group)
        
        self.recalibrate_button = QPushButton("🔄 Recalibrate")
        self.recalibrate_button.clicked.connect(self.restart_calibration)
        actions_layout.addWidget(self.recalibrate_button)
        
        self.test_button = QPushButton("🧪 Test Calibration")
        self.test_button.clicked.connect(self.test_calibration)
        actions_layout.addWidget(self.test_button)
        
        actions_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        layout.addWidget(actions_group)
        
        self.stacked_widget.addWidget(quality_widget)
    
    def create_template_step(self) -> None:
        """Create template save/load step."""
        template_widget = QWidget()
        layout = QVBoxLayout(template_widget)
        
        # Step title
        title = QLabel("Step 4: Save Calibration Template (Optional)")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(11)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Save template
        save_group = QGroupBox("Save Current Calibration")
        save_layout = QFormLayout(save_group)
        
        self.template_name_input = QLineEdit()
        self.template_name_input.setPlaceholderText("Enter template name (e.g., '10x_objective_setup')")
        save_layout.addRow("Template Name:", self.template_name_input)
        
        self.save_template_button = QPushButton("💾 Save Template")
        self.save_template_button.clicked.connect(self.save_template)
        save_layout.addRow("", self.save_template_button)
        
        layout.addWidget(save_group)
        
        # Load existing template
        load_group = QGroupBox("Load Existing Template")
        load_layout = QFormLayout(load_group)
        
        self.template_combo = QComboBox()
        self.refresh_templates()
        load_layout.addRow("Available Templates:", self.template_combo)
        
        load_buttons_layout = QHBoxLayout()
        self.load_template_button = QPushButton("📂 Load Template")
        self.load_template_button.clicked.connect(self.load_template)
        self.delete_template_button = QPushButton("🗑️ Delete Template")
        self.delete_template_button.clicked.connect(self.delete_template)
        
        load_buttons_layout.addWidget(self.load_template_button)
        load_buttons_layout.addWidget(self.delete_template_button)
        load_layout.addRow("", load_buttons_layout)
        
        layout.addWidget(load_group)
        
        # Final actions
        final_group = QGroupBox("Completion")
        final_layout = QVBoxLayout(final_group)
        
        self.apply_calibration_checkbox = QCheckBox("Apply this calibration to current session")
        self.apply_calibration_checkbox.setChecked(True)
        final_layout.addWidget(self.apply_calibration_checkbox)
        
        completion_info = QLabel("""
        ✅ Calibration completed successfully!<br>
        Click 'Finish' to apply the calibration and close this dialog.
        """)
        completion_info.setStyleSheet("QLabel { color: #155724; background: #d4edda; padding: 10px; border: 1px solid #c3e6cb; border-radius: 4px; }")
        final_layout.addWidget(completion_info)
        
        layout.addWidget(final_group)
        
        self.stacked_widget.addWidget(template_widget)
    
    def update_ui_state(self) -> None:
        """Update UI state based on current step."""
        step_index = self.current_step.value
        self.progress_bar.setValue((step_index + 1) * 20)
        self.stacked_widget.setCurrentIndex(step_index)
        
        # Update navigation buttons
        self.back_button.setEnabled(step_index > 0)
        
        if step_index == CalibrationStep.SAVE_TEMPLATE.value:
            self.next_button.setVisible(False)
            self.finish_button.setVisible(True)
        else:
            self.next_button.setVisible(True)
            self.finish_button.setVisible(False)
        
        # Update next button text and state
        if step_index == CalibrationStep.INTRODUCTION.value:
            self.next_button.setText("Start Calibration →")
            self.next_button.setEnabled(True)
        elif step_index == CalibrationStep.FIRST_POINT.value:
            self.next_button.setText("Next Point →")
            self.next_button.setEnabled(self.is_point1_valid())
        elif step_index == CalibrationStep.SECOND_POINT.value:
            self.next_button.setText("Check Quality →")
            self.next_button.setEnabled(self.is_point2_valid())
        elif step_index == CalibrationStep.QUALITY_CHECK.value:
            self.next_button.setText("Save Template →")
            self.next_button.setEnabled(True)
        
        self.update_status_message()
    
    def update_status_message(self) -> None:
        """Update status message based on current state."""
        step = self.current_step
        
        if step == CalibrationStep.INTRODUCTION:
            self.status_label.setText("Ready to start calibration process")
        elif step == CalibrationStep.FIRST_POINT:
            if self.is_point1_valid():
                self.status_label.setText("✅ First point configured correctly")
            else:
                self.status_label.setText("⚠️ Please enter valid stage coordinates for first point")
        elif step == CalibrationStep.SECOND_POINT:
            if self.is_point2_valid():
                self.status_label.setText("✅ Second point configured correctly")
            else:
                self.status_label.setText("⚠️ Please click second point and enter stage coordinates")
        elif step == CalibrationStep.QUALITY_CHECK:
            self.status_label.setText("Calibration quality assessment completed")
        elif step == CalibrationStep.SAVE_TEMPLATE:
            self.status_label.setText("Ready to finish calibration")
    
    def is_point1_valid(self) -> bool:
        """Check if first point is valid."""
        if not self.point1_x_input or not self.point1_y_input:
            return False
        
        # Check if coordinates are not zero (assuming user entered something)
        x_val = self.point1_x_input.value()
        y_val = self.point1_y_input.value()
        
        return x_val != 0.0 or y_val != 0.0
    
    def is_point2_valid(self) -> bool:
        """Check if second point is valid."""
        if not self.point2_x_input or not self.point2_y_input:
            return False
        
        # Check coordinates
        x_val = self.point2_x_input.value()
        y_val = self.point2_y_input.value()
        
        # Pixel coordinates must be set before validation
        if not (hasattr(self, 'pixel2_x') and hasattr(self, 'pixel2_y')):
            return False
        
        # Check minimum distance
        pixel_distance = ((self.pixel2_x - self.initial_pixel_x)**2 + 
                        (self.pixel2_y - self.initial_pixel_y)**2)**0.5
        
        return (x_val != 0.0 or y_val != 0.0) and pixel_distance >= 50
    
    def validate_point1(self) -> None:
        """Validate first point input."""
        if self.is_point1_valid():
            self.point1_status.setText("✅ Valid stage coordinates entered")
            self.point1_status.setStyleSheet("QLabel { color: #155724; background: #d4edda; padding: 8px; border: 1px solid #c3e6cb; border-radius: 4px; }")
        else:
            self.point1_status.setText("⚠️ Please enter stage coordinates")
            self.point1_status.setStyleSheet("QLabel { color: #856404; background: #fff3cd; padding: 8px; border: 1px solid #ffeaa7; border-radius: 4px; }")
        
        self.update_ui_state()
    
    def validate_point2(self) -> None:
        """Validate second point input."""
        if not (hasattr(self, 'pixel2_x') and hasattr(self, 'pixel2_y')):
            self.distance_label.setText("Distance from first point: Click on image to set second point")
            self.point2_status.setText("⚠️ Please click second point on the image first")
            self.point2_status.setStyleSheet("QLabel { color: #856404; background: #fff3cd; padding: 8px; border: 1px solid #ffeaa7; border-radius: 4px; }")
        else:
            pixel_distance = ((self.pixel2_x - self.initial_pixel_x)**2 + 
                            (self.pixel2_y - self.initial_pixel_y)**2)**0.5
            
            self.distance_label.setText(f"Distance from first point: {pixel_distance:.1f} pixels")
            
            if pixel_distance < 50:
                self.point2_status.setText("❌ Points too close! Minimum 50 pixels required")
                self.point2_status.setStyleSheet("QLabel { color: #721c24; background: #f8d7da; padding: 8px; border: 1px solid #f5c6cb; border-radius: 4px; }")
            elif self.is_point2_valid():
                self.point2_status.setText("✅ Valid second point configured")
                self.point2_status.setStyleSheet("QLabel { color: #155724; background: #d4edda; padding: 8px; border: 1px solid #c3e6cb; border-radius: 4px; }")
            else:
                self.point2_status.setText("⚠️ Please enter stage coordinates")
                self.point2_status.setStyleSheet("QLabel { color: #856404; background: #fff3cd; padding: 8px; border: 1px solid #ffeaa7; border-radius: 4px; }")
        
        self.update_ui_state()
    
    def go_next(self) -> None:
        """Go to next step."""
        current_index = self.current_step.value
        
        if current_index == CalibrationStep.FIRST_POINT.value:
            # Add first point to coordinate transformer
            self.add_calibration_point(
                self.initial_pixel_x, self.initial_pixel_y,
                self.point1_x_input.value(), self.point1_y_input.value(),
                "Point 1"
            )
        elif current_index == CalibrationStep.SECOND_POINT.value:
            # Add second point and calculate transformation
            if hasattr(self, 'pixel2_x') and hasattr(self, 'pixel2_y'):
                self.add_calibration_point(
                    self.pixel2_x, self.pixel2_y,
                    self.point2_x_input.value(), self.point2_y_input.value(),
                    "Point 2"
                )
                self.update_quality_display()
        
        # Move to next step
        if current_index < CalibrationStep.SAVE_TEMPLATE.value:
            self.current_step = CalibrationStep(current_index + 1)
            self.update_ui_state()
    
    def go_back(self) -> None:
        """Go to previous step."""
        current_index = self.current_step.value
        if current_index > 0:
            self.current_step = CalibrationStep(current_index - 1)
            self.update_ui_state()
    
    def add_calibration_point(self, pixel_x: int, pixel_y: int, 
                            stage_x: float, stage_y: float, label: str) -> None:
        """Add calibration point to transformer."""
        success = self.coordinate_transformer.add_calibration_point(
            pixel_x, pixel_y, stage_x, stage_y, label
        )
        
        if success:
            self.point_added.emit(pixel_x, pixel_y, stage_x, stage_y, label)
            self.log_info(f"Added calibration point: {label} at pixel({pixel_x}, {pixel_y}) -> stage({stage_x}, {stage_y})")
        else:
            self.log_error(f"Failed to add calibration point: {label}")
    
    def update_quality_display(self) -> None:
        """Update quality assessment display."""
        if not self.coordinate_transformer.is_calibrated:
            return
        
        quality = self.coordinate_transformer.calibration_quality
        
        # Update quality metrics
        if quality:
            avg_error = quality.get('average_error_um', 0)
            max_error = quality.get('max_error_um', 0)
            confidence = quality.get('transformation_confidence', 0)
            meets_target = quality.get('meets_accuracy_target', False)
            
            self.avg_error_label.setText(f"Average Error: {avg_error:.3f} µm")
            self.max_error_label.setText(f"Maximum Error: {max_error:.3f} µm")
            self.confidence_label.setText(f"Confidence: {confidence:.1%}")
            
            if meets_target:
                self.accuracy_status_label.setText("✅ Accuracy: Meets target requirements")
                self.accuracy_status_label.setStyleSheet("QLabel { color: #155724; }")
            else:
                self.accuracy_status_label.setText("⚠️ Accuracy: Below target requirements")
                self.accuracy_status_label.setStyleSheet("QLabel { color: #856404; }")
            
            # Update progress bar
            quality_percentage = int(confidence * 100)
            self.quality_progress.setValue(quality_percentage)
            
            if quality_percentage >= 80:
                self.quality_progress.setStyleSheet("QProgressBar::chunk { background-color: #28a745; }")
            elif quality_percentage >= 60:
                self.quality_progress.setStyleSheet("QProgressBar::chunk { background-color: #ffc107; }")
            else:
                self.quality_progress.setStyleSheet("QProgressBar::chunk { background-color: #dc3545; }")
            
            # Update recommendations
            if meets_target:
                self.recommendations_label.setText("""
                ✅ <strong>Excellent calibration quality!</strong><br>
                The calibration meets accuracy requirements and is ready for use.
                """)
            else:
                self.recommendations_label.setText("""
                ⚠️ <strong>Consider improving calibration:</strong><br>
                • Try placing points farther apart<br>
                • Ensure accurate stage coordinate measurements<br>
                • Choose more distinct reference points
                """)
        
        # Update points summary
        points_text = ""
        for i, point in enumerate(self.coordinate_transformer.calibration_points):
            points_text += f"Point {i+1}: Pixel({point.pixel_x}, {point.pixel_y}) → Stage({point.stage_x:.3f}, {point.stage_y:.3f}) µm\n"
        
        self.points_summary.setPlainText(points_text)
    
    def test_calibration(self) -> None:
        """Test calibration with user-provided coordinates."""
        if not self.coordinate_transformer.is_calibrated:
            QMessageBox.warning(self, "No Calibration", "No calibration available to test.")
            return
        
        # Simple test with center of image
        test_x, test_y = 100, 100
        result = self.coordinate_transformer.pixel_to_stage(test_x, test_y)
        
        if result:
            QMessageBox.information(
                self, "Test Result",
                f"Pixel({test_x}, {test_y}) → Stage({result.stage_x:.3f}, {result.stage_y:.3f}) µm\n"
                f"Confidence: {result.confidence:.1%}\n"
                f"Error estimate: {result.error_estimate_um:.3f} µm"
            )
    
    def restart_calibration(self) -> None:
        """Restart calibration process."""
        reply = QMessageBox.question(
            self, "Restart Calibration",
            "This will clear the current calibration and start over. Continue?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.coordinate_transformer.clear_calibration()
            self.current_step = CalibrationStep.INTRODUCTION
            self.update_ui_state()
    
    def save_template(self) -> None:
        """Save current calibration as template."""
        template_name = self.template_name_input.text().strip()
        if not template_name:
            QMessageBox.warning(self, "Invalid Name", "Please enter a template name.")
            return
        
        # Save template to file
        template_data = {
            'name': template_name,
            'calibration_data': self.coordinate_transformer.export_calibration(),
            'created_date': datetime.now().isoformat(),
            'description': f"Calibration template: {template_name}"
        }
        
        templates_dir = Path(".taskmaster/templates/calibration")
        templates_dir.mkdir(parents=True, exist_ok=True)
        
        template_file = templates_dir / f"{template_name}.json"
        
        try:
            with open(template_file, 'w') as f:
                json.dump(template_data, f, indent=2)
            
            QMessageBox.information(self, "Template Saved", f"Template '{template_name}' saved successfully.")
            self.refresh_templates()
            self.log_info(f"Saved calibration template: {template_name}")
            
        except Exception as e:
            QMessageBox.critical(self, "Save Failed", f"Failed to save template: {e}")
    
    def load_template(self) -> None:
        """Load selected template."""
        template_name = self.template_combo.currentText()
        if not template_name or template_name == "No templates available":
            return
        
        templates_dir = Path(".taskmaster/templates/calibration")
        template_file = templates_dir / f"{template_name}.json"
        
        try:
            with open(template_file, 'r') as f:
                template_data = json.load(f)
            
            # Load calibration data
            calibration_data = template_data.get('calibration_data', {})
            success = self.coordinate_transformer.import_calibration(calibration_data)
            
            if success:
                QMessageBox.information(self, "Template Loaded", f"Template '{template_name}' loaded successfully.")
                self.current_step = CalibrationStep.QUALITY_CHECK
                self.update_quality_display()
                self.update_ui_state()
                self.log_info(f"Loaded calibration template: {template_name}")
            else:
                QMessageBox.warning(self, "Load Failed", "Failed to load template data.")
                
        except Exception as e:
            QMessageBox.critical(self, "Load Failed", f"Failed to load template: {e}")
    
    def delete_template(self) -> None:
        """Delete selected template."""
        template_name = self.template_combo.currentText()
        if not template_name or template_name == "No templates available":
            return
        
        reply = QMessageBox.question(
            self, "Delete Template",
            f"Delete template '{template_name}'? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            templates_dir = Path(".taskmaster/templates/calibration")
            template_file = templates_dir / f"{template_name}.json"
            
            try:
                template_file.unlink()
                QMessageBox.information(self, "Template Deleted", f"Template '{template_name}' deleted.")
                self.refresh_templates()
                self.log_info(f"Deleted calibration template: {template_name}")
                
            except Exception as e:
                QMessageBox.critical(self, "Delete Failed", f"Failed to delete template: {e}")
    
    def refresh_templates(self) -> None:
        """Refresh template list."""
        if not self.template_combo:
            return
        
        self.template_combo.clear()
        
        templates_dir = Path(".taskmaster/templates/calibration")
        if not templates_dir.exists():
            self.template_combo.addItem("No templates available")
            return
        
        template_files = list(templates_dir.glob("*.json"))
        if not template_files:
            self.template_combo.addItem("No templates available")
        else:
            for template_file in template_files:
                self.template_combo.addItem(template_file.stem)
    
    def finish_calibration(self) -> None:
        """Finish calibration process."""
        if self.apply_calibration_checkbox.isChecked():
            # Calibration is already applied to coordinate_transformer
            self.calibration_completed.emit(True)
        
        self.accept()
        self.log_info("Calibration wizard completed successfully")
    
    def set_second_point(self, pixel_x: int, pixel_y: int) -> None:
        """Set second calibration point coordinates (called from main window)."""
        self.pixel2_x = pixel_x
        self.pixel2_y = pixel_y
        
        if hasattr(self, 'pixel2_x_label'):
            self.pixel2_x_label.setText(str(pixel_x))
            self.pixel2_y_label.setText(str(pixel_y))
        
        self.validate_point2()
    
    def get_calibration_data(self) -> Dict[str, Any]:
        """Get current calibration data."""
        return self.coordinate_transformer.export_calibration()
    
    def on_calibration_updated(self, is_valid: bool) -> None:
        """Handle calibration update from coordinate transformer."""
        self.update_ui_state()
        
        if is_valid and self.current_step == CalibrationStep.SECOND_POINT:
            # Auto-advance to quality check if both points are set
            QTimer.singleShot(500, self.update_quality_display)


# Legacy compatibility wrapper
class CalibrationDialog(CalibrationWizardDialog):
    """Legacy wrapper for backward compatibility."""
    
    def __init__(self, pixel_x: int, pixel_y: int, point_label: str, parent=None, coordinate_transformer=None):
        # Use existing transformer if provided, otherwise create new one
        if coordinate_transformer is None:
            from models.coordinate_transformer import CoordinateTransformer
            transformer = CoordinateTransformer()
        else:
            transformer = coordinate_transformer
            
        super().__init__(transformer, pixel_x, pixel_y, point_label, parent)
        
        # For legacy compatibility, start at first point step
        self.current_step = CalibrationStep.FIRST_POINT
        self.update_ui_state()
    
    def get_stage_coordinates(self) -> Tuple[float, float]:
        """Legacy method for getting coordinates."""
        # Return actual user input values from the first point
        if hasattr(self, 'point1_x_input') and hasattr(self, 'point1_y_input'):
            return (self.point1_x_input.value(), self.point1_y_input.value())
        return (0.0, 0.0)
    
    def set_stage_coordinates(self, stage_x: float, stage_y: float) -> None:
        """Legacy method for setting coordinates."""
        # Set the stage coordinates in the first point input fields
        if hasattr(self, 'point1_x_input') and hasattr(self, 'point1_y_input'):
            self.point1_x_input.setValue(stage_x)
            self.point1_y_input.setValue(stage_y)
            # Trigger validation to update UI state
            self.validate_point1()
