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
    """Enhanced calibration dialog with step-by-step wizard interface."""
    
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
        
        # Point tracking for second point selection
        self.pixel2_x: Optional[int] = None
        self.pixel2_y: Optional[int] = None
        
        self.setup_ui()
        self.update_ui_state()
        
        self.log_info("Enhanced calibration wizard dialog initialized")
        
    def setup_ui(self) -> None:
        """Set up the enhanced wizard UI with improved layout."""
        self.setWindowTitle("Calibration Wizard - CellSorter")
        
        # CRITICAL FIX: Make dialog non-modal to allow image interaction
        self.setModal(False)
        
        # ENLARGED SIZING: Use bigger minimum size to prevent overlap
        self.setMinimumSize(600, 800)
        self.resize(650, 850)  # ENLARGED: Initial size, but user can resize
        
        # Enable window resizing and keep on top for visibility
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
        
        # ENLARGED LAYOUT: Better margins and spacing to prevent overlap
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)  # ENLARGED: Even more generous margins
        main_layout.setSpacing(20)  # ENLARGED: More spacing to prevent overlap
        
        # Header with progress
        header_frame = self.create_header()
        main_layout.addWidget(header_frame)
        
        # Stacked widget for different steps - ENLARGED margins
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setContentsMargins(15, 15, 15, 15)  # ENLARGED: More content margins
        main_layout.addWidget(self.stacked_widget)
        
        # Create step widgets
        self.create_basic_steps()
        
        # Footer with navigation buttons
        footer_frame = self.create_footer()
        main_layout.addWidget(footer_frame)
        
        # Status area with better styling
        self.status_label = QLabel("Ready to start calibration")
        self.status_label.setStyleSheet("""
            QLabel { 
                color: #666; 
                font-style: italic; 
                padding: 8px;
                background-color: #f8f9fa;
                border-radius: 4px;
                border: 1px solid #e9ecef;
            }
        """)
        self.status_label.setWordWrap(True)
        main_layout.addWidget(self.status_label)
    
    def create_header(self) -> QFrame:
        """Create header with title and progress bar."""
        header = QFrame()
        header.setFrameStyle(QFrame.StyledPanel)
        header.setStyleSheet("""
            QFrame { 
                background-color: #f8f9fa; 
                border: 1px solid #dee2e6; 
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout(header)
        layout.setContentsMargins(20, 20, 20, 20)  # ENLARGED: More header margins
        layout.setSpacing(15)  # ENLARGED: More header spacing
        
        # Title with improved typography
        title = QLabel("Coordinate Calibration Wizard")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(16)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("QLabel { color: #2c3e50; margin-bottom: 5px; }")
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Map pixel coordinates to stage coordinates")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("QLabel { color: #6c757d; font-size: 12px; }")
        layout.addWidget(subtitle)
        
        # Progress bar with better styling
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Step %v%")
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #e9ecef;
                border-radius: 8px;
                text-align: center;
                background-color: #ffffff;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #007bff;
                border-radius: 6px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        return header
    
    def create_footer(self) -> QFrame:
        """Create footer with navigation buttons."""
        footer = QFrame()
        footer.setStyleSheet("""
            QFrame {
                border-top: 1px solid #dee2e6;
                padding-top: 10px;
                margin-top: 10px;
            }
        """)
        
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(0, 15, 0, 0)  # ENLARGED: More footer margins
        layout.setSpacing(15)  # ENLARGED: More button spacing
        
        # Back button with styling - ENLARGED
        self.back_button = QPushButton("← Back")
        self.back_button.clicked.connect(self.go_back)
        self.back_button.setEnabled(False)
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 10px 20px;  /* ENLARGED: Bigger button padding */
                border-radius: 4px;
                font-weight: bold;
                min-width: 100px;  /* ENLARGED: Minimum button width */
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:disabled {
                background-color: #e9ecef;
                color: #6c757d;
            }
        """)
        layout.addWidget(self.back_button)
        
        # Spacer
        layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        # Next button with styling - ENLARGED
        self.next_button = QPushButton("Next →")
        self.next_button.clicked.connect(self.go_next)
        self.next_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 10px 20px;  /* ENLARGED: Bigger button padding */
                border-radius: 4px;
                font-weight: bold;
                min-width: 100px;  /* ENLARGED: Bigger minimum width */
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:disabled {
                background-color: #e9ecef;
                color: #6c757d;
            }
        """)
        layout.addWidget(self.next_button)
        
        # Finish button with styling - ENLARGED
        self.finish_button = QPushButton("Finish")
        self.finish_button.clicked.connect(self.finish_calibration)
        self.finish_button.setVisible(False)
        self.finish_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 10px 20px;  /* ENLARGED: Bigger button padding */
                border-radius: 4px;
                font-weight: bold;
                min-width: 100px;  /* ENLARGED: Bigger minimum width */
            }
            QPushButton:hover {
                background-color: #1e7e34;
            }
        """)
        layout.addWidget(self.finish_button)
        
        # Cancel button with styling - ENLARGED
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 10px 20px;  /* ENLARGED: Bigger button padding */
                border-radius: 4px;
                font-weight: bold;
                min-width: 100px;  /* ENLARGED: Minimum button width */
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
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
        """Create second point calibration step with non-modal support."""
        point2_widget = QWidget()
        layout = QVBoxLayout(point2_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Step title
        title = QLabel("Step 2: Second Calibration Point")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(11)
        title.setFont(title_font)
        title.setStyleSheet("QLabel { color: #2c3e50; margin-bottom: 10px; }")
        layout.addWidget(title)
        
        # CRITICAL: Instructions for non-modal interaction
        instructions = QLabel(
            "🖱️ <strong>Click on a second reference point in your image</strong> (this dialog won't block image interaction), "
            "then enter the corresponding stage coordinates below. "
            "Choose a point at least 50 pixels away from the first point for optimal accuracy."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("""
            QLabel { 
                color: #495057; 
                background: #e8f4fd; 
                padding: 12px; 
                border-left: 4px solid #007bff; 
                border-radius: 4px; 
                margin: 10px 0; 
            }
        """)
        layout.addWidget(instructions)
        
        # Current first point reference
        first_point_ref = QLabel(f"First point: ({self.initial_pixel_x}, {self.initial_pixel_y}) pixels")
        first_point_ref.setStyleSheet("QLabel { color: #6c757d; font-style: italic; margin: 5px 0; }")
        layout.addWidget(first_point_ref)
        
        # Pixel coordinates for second point (initially empty, filled when clicked)
        pixel_group = QGroupBox("Second Point - Image Coordinates")
        pixel_layout = QFormLayout(pixel_group)
        pixel_layout.setSpacing(8)
        
        self.pixel2_x_label = QLabel("(Click on image)")
        self.pixel2_y_label = QLabel("(Click on image)")
        
        for label in [self.pixel2_x_label, self.pixel2_y_label]:
            label.setStyleSheet("""
                QLabel { 
                    font-family: monospace; 
                    font-weight: bold; 
                    background: #f8f9fa; 
                    padding: 8px; 
                    border: 1px solid #dee2e6; 
                    border-radius: 4px;
                    min-width: 120px;
                }
            """)
        
        pixel_layout.addRow("X (pixels):", self.pixel2_x_label)
        pixel_layout.addRow("Y (pixels):", self.pixel2_y_label)
        layout.addWidget(pixel_group)
        
        # Stage coordinates input
        stage_group = QGroupBox("Second Point - Stage Coordinates")
        stage_layout = QFormLayout(stage_group)
        stage_layout.setSpacing(8)
        
        self.point2_x_input = QDoubleSpinBox()
        self.point2_x_input.setRange(-999999.999, 999999.999)
        self.point2_x_input.setDecimals(3)
        self.point2_x_input.setSuffix(" µm")
        self.point2_x_input.setMinimumWidth(150)
        self.point2_x_input.valueChanged.connect(self.validate_point2)
        self.point2_x_input.setStyleSheet("""
            QDoubleSpinBox {
                padding: 6px;
                border: 2px solid #e9ecef;
                border-radius: 4px;
            }
            QDoubleSpinBox:focus {
                border-color: #007bff;
            }
        """)
        
        self.point2_y_input = QDoubleSpinBox()
        self.point2_y_input.setRange(-999999.999, 999999.999)
        self.point2_y_input.setDecimals(3)
        self.point2_y_input.setSuffix(" µm")
        self.point2_y_input.setMinimumWidth(150)
        self.point2_y_input.valueChanged.connect(self.validate_point2)
        self.point2_y_input.setStyleSheet("""
            QDoubleSpinBox {
                padding: 6px;
                border: 2px solid #e9ecef;
                border-radius: 4px;
            }
            QDoubleSpinBox:focus {
                border-color: #007bff;
            }
        """)
        
        stage_layout.addRow("X (µm):", self.point2_x_input)
        stage_layout.addRow("Y (µm):", self.point2_y_input)
        layout.addWidget(stage_group)
        
        # Distance display
        distance_group = QGroupBox("Point Distance Analysis")
        distance_layout = QVBoxLayout(distance_group)
        
        self.distance_label = QLabel("Select second point to see distance analysis")
        self.distance_label.setStyleSheet("""
            QLabel { 
                font-family: monospace; 
                background: #f8f9fa; 
                padding: 10px; 
                border: 1px solid #dee2e6; 
                border-radius: 4px; 
            }
        """)
        distance_layout.addWidget(self.distance_label)
        layout.addWidget(distance_group)
        
        # Validation status
        self.point2_status = QLabel("⚠️ Click on the image to select second point")
        self.point2_status.setStyleSheet("""
            QLabel { 
                color: #856404; 
                background: #fff3cd; 
                padding: 10px; 
                border: 1px solid #ffeaa7; 
                border-radius: 4px; 
                margin: 5px 0;
            }
        """)
        layout.addWidget(self.point2_status)
        
        # Tips for non-modal interaction
        tips = QLabel("""
        💡 <strong>Non-Modal Dialog Tips:</strong><br>
        • This dialog stays open while you click on the image<br>
        • You can move or resize this dialog as needed<br>
        • Choose points that are far apart (>50 pixels) for better calibration<br>
        • Use distinctive features like cell corners or fiducial markers
        """)
        tips.setWordWrap(True)
        tips.setStyleSheet("""
            QLabel { 
                background: #d4edda; 
                color: #155724;
                padding: 12px; 
                border-left: 4px solid #28a745; 
                border-radius: 4px;
                margin: 10px 0; 
            }
        """)
        layout.addWidget(tips)
        
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
        """Check if second point is valid - ENHANCED."""
        # Must have pixel coordinates set (from image click)
        if self.pixel2_x is None or self.pixel2_y is None:
            return False
            
        # Must have stage coordinate inputs
        if not (hasattr(self, 'point2_x_input') and hasattr(self, 'point2_y_input')):
            return False
            
        # Stage coordinates must not be zero
        stage_x = self.point2_x_input.value()
        stage_y = self.point2_y_input.value()
        if stage_x == 0.0 and stage_y == 0.0:
            return False
            
        # Check minimum distance from first point (at least 50 pixels)
        pixel_distance = ((self.pixel2_x - self.initial_pixel_x) ** 2 + 
                         (self.pixel2_y - self.initial_pixel_y) ** 2) ** 0.5
        if pixel_distance < 50:
            return False
            
        return True
    
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
        """Validate second point and update UI - ENHANCED."""
        if not hasattr(self, 'point2_status'):
            return
            
        if self.pixel2_x is None or self.pixel2_y is None:
            self.point2_status.setText("⚠️ Click on the image to select second point")
            self.point2_status.setStyleSheet("""
                QLabel { 
                    color: #856404; 
                    background: #fff3cd; 
                    padding: 10px; 
                    border: 1px solid #ffeaa7; 
                    border-radius: 4px; 
                }
            """)
            return
            
        # Check distance
        pixel_distance = ((self.pixel2_x - self.initial_pixel_x) ** 2 + 
                         (self.pixel2_y - self.initial_pixel_y) ** 2) ** 0.5
        
        if pixel_distance < 50:
            self.point2_status.setText(f"❌ Points too close ({pixel_distance:.1f} pixels). Select a point at least 50 pixels away.")
            self.point2_status.setStyleSheet("""
                QLabel { 
                    color: #721c24; 
                    background: #f8d7da; 
                    padding: 10px; 
                    border: 1px solid #f5c6cb; 
                    border-radius: 4px; 
                }
            """)
            return
            
        # Check stage coordinates
        if hasattr(self, 'point2_x_input') and hasattr(self, 'point2_y_input'):
            stage_x = self.point2_x_input.value()
            stage_y = self.point2_y_input.value()
            
            if stage_x == 0.0 and stage_y == 0.0:
                self.point2_status.setText("⚠️ Please enter stage coordinates")
                self.point2_status.setStyleSheet("""
                    QLabel { 
                        color: #856404; 
                        background: #fff3cd; 
                        padding: 10px; 
                        border: 1px solid #ffeaa7; 
                        border-radius: 4px; 
                    }
                """)
                return
        
        # All validations passed
        self.point2_status.setText(f"✅ Second point valid (distance: {pixel_distance:.1f} pixels)")
        self.point2_status.setStyleSheet("""
            QLabel { 
                color: #155724; 
                background: #d4edda; 
                padding: 10px; 
                border: 1px solid #c3e6cb; 
                border-radius: 4px; 
            }
        """)
        
        # Update distance display
        self.update_distance_display()
        
        # Update overall UI state
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
        """Set the second calibration point from image click - ENHANCED for non-modal."""
        self.log_info(f"Setting second calibration point at pixel ({pixel_x}, {pixel_y})")
        
        # Store pixel coordinates
        self.pixel2_x = pixel_x
        self.pixel2_y = pixel_y
        
        # Update UI labels immediately
        if hasattr(self, 'pixel2_x_label') and hasattr(self, 'pixel2_y_label'):
            self.pixel2_x_label.setText(str(pixel_x))
            self.pixel2_y_label.setText(str(pixel_y))
            
            # Update styling to show coordinates are set
            coordinate_style = """
                QLabel { 
                    font-family: monospace; 
                    font-weight: bold; 
                    background: #d4edda; 
                    color: #155724;
                    padding: 8px; 
                    border: 2px solid #28a745; 
                    border-radius: 4px;
                    min-width: 120px;
                }
            """
            self.pixel2_x_label.setStyleSheet(coordinate_style)
            self.pixel2_y_label.setStyleSheet(coordinate_style)
        
        # Calculate and display distance immediately
        self.update_distance_display()
        
        # Validate the point
        self.validate_point2()
        
        # If we're on the second point step, update UI state
        if self.current_step == CalibrationStep.SECOND_POINT:
            self.update_ui_state()
        
        self.log_info("Second point set successfully with non-modal interaction")

    def update_distance_display(self) -> None:
        """Update distance display between calibration points."""
        if not hasattr(self, 'distance_label'):
            return
            
        # Check if we have both points
        if self.pixel2_x is None or self.pixel2_y is None:
            self.distance_label.setText("Select second point to see distance analysis")
            return
            
        # Calculate pixel distance
        pixel_distance = ((self.pixel2_x - self.initial_pixel_x) ** 2 + 
                         (self.pixel2_y - self.initial_pixel_y) ** 2) ** 0.5
        
        # Check if stage coordinates are available for both points
        if (hasattr(self, 'point1_x_input') and hasattr(self, 'point1_y_input') and
            hasattr(self, 'point2_x_input') and hasattr(self, 'point2_y_input')):
            
            stage1_x = self.point1_x_input.value()
            stage1_y = self.point1_y_input.value()
            stage2_x = self.point2_x_input.value()
            stage2_y = self.point2_y_input.value()
            
            # Only calculate stage distance if coordinates are not zero
            if not (stage1_x == 0 and stage1_y == 0 and stage2_x == 0 and stage2_y == 0):
                stage_distance = ((stage2_x - stage1_x) ** 2 + (stage2_y - stage1_y) ** 2) ** 0.5
                scale_factor = stage_distance / pixel_distance if pixel_distance > 0 else 0
                
                distance_info = f"""
                📏 Distance Analysis:
                • Pixel distance: {pixel_distance:.1f} pixels
                • Stage distance: {stage_distance:.1f} µm  
                • Scale factor: {scale_factor:.3f} µm/pixel
                """
                
                # Color code based on distance quality
                if pixel_distance >= 100:
                    color_style = "background: #d4edda; color: #155724; border-color: #28a745;"
                elif pixel_distance >= 50:
                    color_style = "background: #fff3cd; color: #856404; border-color: #ffc107;"
                else:
                    color_style = "background: #f8d7da; color: #721c24; border-color: #dc3545;"
                    
            else:
                distance_info = f"📏 Pixel distance: {pixel_distance:.1f} pixels\n(Enter stage coordinates to see full analysis)"
                color_style = "background: #e2e3e5; color: #6c757d; border-color: #6c757d;"
        else:
            distance_info = f"📏 Pixel distance: {pixel_distance:.1f} pixels"
            color_style = "background: #f8f9fa; color: #6c757d; border-color: #dee2e6;"
        
        self.distance_label.setText(distance_info)
        self.distance_label.setStyleSheet(f"""
            QLabel {{ 
                font-family: monospace; 
                padding: 10px; 
                border: 2px solid; 
                border-radius: 4px;
                {color_style}
            }}
        """)

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
