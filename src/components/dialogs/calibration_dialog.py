"""
Simplified Calibration Dialog for CellSorter - 2 Steps Only
"""

from typing import Optional, Tuple, Dict, Any
from enum import Enum
from pathlib import Path
from datetime import datetime
import json

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QPushButton,
    QDoubleSpinBox, QDialogButtonBox, QGroupBox, QTextEdit, 
    QStackedWidget, QWidget, QFrame, QGridLayout, QSpacerItem, QSizePolicy,
    QCheckBox, QComboBox, QLineEdit, QMessageBox, QFileDialog, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor, QPen, QIcon

from models.coordinate_transformer import CoordinateTransformer, CalibrationPoint
from utils.logging_config import LoggerMixin


class CalibrationStep(Enum):
    """Simplified calibration wizard steps."""
    FIRST_POINT = 0
    SECOND_POINT = 1


class CalibrationWizardDialog(QDialog, LoggerMixin):
    """Simplified calibration dialog with 2-step wizard interface."""
    
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
        self.current_step = CalibrationStep.FIRST_POINT
        
        # UI components
        self.stacked_widget: Optional[QStackedWidget] = None
        self.next_button: Optional[QPushButton] = None
        self.back_button: Optional[QPushButton] = None
        self.finish_button: Optional[QPushButton] = None
        self.status_label: Optional[QLabel] = None
        
        # Point tracking for second point selection
        self.pixel2_x: Optional[int] = None
        self.pixel2_y: Optional[int] = None
        
        self.setup_ui()
        self.update_ui_state()
        
        self.log_info("Simplified calibration wizard dialog initialized")
        
    def setup_ui(self) -> None:
        """Set up the simplified wizard UI."""
        self.setWindowTitle("Calibration Wizard - CellSorter")
        
        # Make dialog non-modal to allow image interaction
        self.setModal(False)
        
        # Set appropriate size
        self.setMinimumSize(500, 600)
        self.resize(550, 650)
        
        # Enable window resizing
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Header
        header_frame = self.create_header()
        main_layout.addWidget(header_frame)
        
        # Stacked widget for steps
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)
        
        # Create step widgets
        self.create_steps()
        
        # Footer with navigation buttons
        footer_frame = self.create_footer()
        main_layout.addWidget(footer_frame)
        
        # Status area
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
        """Create simplified header."""
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
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("Coordinate Calibration")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(16)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("QLabel { color: #2c3e50; }")
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Map pixel coordinates to stage coordinates")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("QLabel { color: #6c757d; font-size: 12px; }")
        layout.addWidget(subtitle)
        
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
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(10)
        
        # Back button
        self.back_button = QPushButton("← Back")
        self.back_button.clicked.connect(self.go_back)
        self.back_button.setEnabled(False)
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: 500;
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
        
        layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        # Next button
        self.next_button = QPushButton("Next →")
        self.next_button.clicked.connect(self.go_next)
        self.next_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
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
        layout.addWidget(self.next_button)
        
        # Finish button
        self.finish_button = QPushButton("Finish")
        self.finish_button.clicked.connect(self.finish_calibration)
        self.finish_button.setVisible(False)
        self.finish_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #1e7e34;
            }
        """)
        layout.addWidget(self.finish_button)
        
        return footer
    
    def create_steps(self) -> None:
        """Create the 2 step widgets."""
        self.create_first_point_step()
        self.create_second_point_step()
    
    def create_first_point_step(self) -> None:
        """Create first point calibration step."""
        point1_widget = QWidget()
        layout = QVBoxLayout(point1_widget)
        
        # Step title
        title = QLabel("Step 1: First Calibration Point")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Instructions
        instructions = QLabel(
            "Enter the stage coordinates for the clicked point in your image."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("QLabel { color: #495057; margin: 10px 0; }")
        layout.addWidget(instructions)
        
        # Pixel coordinates (display only)
        pixel_group = QGroupBox("Image Coordinates")
        pixel_layout = QFormLayout(pixel_group)
        
        self.pixel1_x_label = QLabel(str(self.initial_pixel_x))
        self.pixel1_y_label = QLabel(str(self.initial_pixel_y))
        
        for label in [self.pixel1_x_label, self.pixel1_y_label]:
            label.setStyleSheet("QLabel { font-family: monospace; font-weight: bold; background: #f8f9fa; padding: 5px; border: 1px solid #dee2e6; }")
        
        pixel_layout.addRow("X (pixels):", self.pixel1_x_label)
        pixel_layout.addRow("Y (pixels):", self.pixel1_y_label)
        layout.addWidget(pixel_group)
        
        # Stage coordinates input
        stage_group = QGroupBox("Stage Coordinates")
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
        
        self.stacked_widget.addWidget(point1_widget)
    
    def create_second_point_step(self) -> None:
        """Create second point calibration step."""
        point2_widget = QWidget()
        layout = QVBoxLayout(point2_widget)
        
        # Step title
        title = QLabel("Step 2: Second Calibration Point")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Instructions
        instructions = QLabel(
            "Click on a second reference point in your image, then enter the corresponding stage coordinates."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("QLabel { color: #495057; margin: 10px 0; }")
        layout.addWidget(instructions)
        
        # Pixel coordinates for second point
        pixel_group = QGroupBox("Second Point - Image Coordinates")
        pixel_layout = QFormLayout(pixel_group)
        
        self.pixel2_x_label = QLabel("(Click on image)")
        self.pixel2_y_label = QLabel("(Click on image)")
        
        for label in [self.pixel2_x_label, self.pixel2_y_label]:
            label.setStyleSheet("QLabel { font-family: monospace; font-weight: bold; background: #f8f9fa; padding: 5px; border: 1px solid #dee2e6; }")
        
        pixel_layout.addRow("X (pixels):", self.pixel2_x_label)
        pixel_layout.addRow("Y (pixels):", self.pixel2_y_label)
        layout.addWidget(pixel_group)
        
        # Stage coordinates input for second point
        stage_group = QGroupBox("Stage Coordinates")
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
        
        # Distance info
        self.distance_label = QLabel("")
        self.distance_label.setStyleSheet("QLabel { color: #6c757d; font-style: italic; margin: 5px 0; }")
        layout.addWidget(self.distance_label)
        
        self.stacked_widget.addWidget(point2_widget)
    
    def update_ui_state(self) -> None:
        """Update UI state based on current step."""
        step_index = self.current_step.value
        self.stacked_widget.setCurrentIndex(step_index)
        
        # Update navigation buttons
        self.back_button.setEnabled(step_index > 0)
        
        if step_index == CalibrationStep.SECOND_POINT.value:
            self.next_button.setVisible(False)
            self.finish_button.setVisible(True)
        else:
            self.next_button.setVisible(True)
            self.finish_button.setVisible(False)
        
        # Update next button text and state
        if step_index == CalibrationStep.FIRST_POINT.value:
            self.next_button.setText("Next Point →")
            self.next_button.setEnabled(self.is_point1_valid())
        
        self.update_status_message()
    
    def update_status_message(self) -> None:
        """Update status message based on current state."""
        step = self.current_step
        
        if step == CalibrationStep.FIRST_POINT:
            if self.is_point1_valid():
                self.status_label.setText("✅ First point configured correctly")
            else:
                self.status_label.setText("⚠️ Please enter valid stage coordinates for first point")
        elif step == CalibrationStep.SECOND_POINT:
            if self.is_point2_valid():
                self.status_label.setText("✅ Both points configured - Ready to finish")
            else:
                self.status_label.setText("⚠️ Please click second point and enter stage coordinates")
    
    def is_point1_valid(self) -> bool:
        """Check if first point is valid."""
        if not hasattr(self, 'point1_x_input') or not hasattr(self, 'point1_y_input'):
            return False
        return True  # Any coordinate values are valid
    
    def is_point2_valid(self) -> bool:
        """Check if second point is valid."""
        if not hasattr(self, 'pixel2_x') or not hasattr(self, 'pixel2_y'):
            return False
        if self.pixel2_x is None or self.pixel2_y is None:
            return False
        if not hasattr(self, 'point2_x_input') or not hasattr(self, 'point2_y_input'):
            return False
        
        # Check minimum distance between points
        pixel_distance = ((self.pixel2_x - self.initial_pixel_x) ** 2 + 
                         (self.pixel2_y - self.initial_pixel_y) ** 2) ** 0.5
        
        return pixel_distance >= 50  # Minimum 50 pixels apart
    
    def validate_point1(self) -> None:
        """Validate first point input."""
        if self.is_point1_valid():
            self.point1_status.setText("✅ First point coordinates entered")
            self.point1_status.setStyleSheet("QLabel { color: #155724; background: #d4edda; padding: 8px; border: 1px solid #c3e6cb; border-radius: 4px; }")
        else:
            self.point1_status.setText("⚠️ Please enter stage coordinates")
            self.point1_status.setStyleSheet("QLabel { color: #856404; background: #fff3cd; padding: 8px; border: 1px solid #ffeaa7; border-radius: 4px; }")
        
        self.update_ui_state()
    
    def validate_point2(self) -> None:
        """Validate second point input."""
        if not hasattr(self, 'pixel2_x') or not hasattr(self, 'pixel2_y'):
            self.point2_status.setText("⚠️ Please click second point on image first")
            self.point2_status.setStyleSheet("QLabel { color: #856404; background: #fff3cd; padding: 8px; border: 1px solid #ffeaa7; border-radius: 4px; }")
            self.update_ui_state()
            return
        
        # Check minimum distance
        pixel_distance = ((self.pixel2_x - self.initial_pixel_x) ** 2 + 
                         (self.pixel2_y - self.initial_pixel_y) ** 2) ** 0.5
        
        if pixel_distance < 50:
            self.point2_status.setText(f"⚠️ Points too close ({pixel_distance:.1f} pixels). Minimum: 50 pixels")
            self.point2_status.setStyleSheet("QLabel { color: #856404; background: #fff3cd; padding: 8px; border: 1px solid #ffeaa7; border-radius: 4px; }")
            self.update_ui_state()
            return
        
        # All validations passed
        self.point2_status.setText(f"✅ Second point valid (distance: {pixel_distance:.1f} pixels)")
        self.point2_status.setStyleSheet("QLabel { color: #155724; background: #d4edda; padding: 8px; border: 1px solid #c3e6cb; border-radius: 4px; }")
        
        # Update distance display
        self.update_distance_display()
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
            # Move to second point step
            self.current_step = CalibrationStep.SECOND_POINT
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
    
    def finish_calibration(self) -> None:
        """Finish calibration and close dialog."""
        if self.current_step == CalibrationStep.SECOND_POINT and self.is_point2_valid():
            # Add second point
            self.add_calibration_point(
                self.pixel2_x, self.pixel2_y,
                self.point2_x_input.value(), self.point2_y_input.value(),
                "Point 2"
            )
            
            # Apply calibration and close
            self.calibration_completed.emit(True)
            self.accept()
        else:
            QMessageBox.warning(self, "Incomplete", "Please complete both calibration points.")
    
    def set_second_point(self, pixel_x: int, pixel_y: int) -> None:
        """Set the second calibration point from image click."""
        self.pixel2_x = pixel_x
        self.pixel2_y = pixel_y
        
        # Update UI labels
        self.pixel2_x_label.setText(str(pixel_x))
        self.pixel2_y_label.setText(str(pixel_y))
        
        # Update status and validation
        self.validate_point2()
        self.log_info(f"Second point set to: ({pixel_x}, {pixel_y})")
    
    def update_distance_display(self) -> None:
        """Update distance information display."""
        if hasattr(self, 'pixel2_x') and hasattr(self, 'pixel2_y'):
            # Calculate pixel distance
            pixel_distance = ((self.pixel2_x - self.initial_pixel_x) ** 2 + 
                             (self.pixel2_y - self.initial_pixel_y) ** 2) ** 0.5
            
            # Calculate stage distance if both coordinates are entered
            if hasattr(self, 'point1_x_input') and hasattr(self, 'point2_x_input'):
                stage_dx = self.point2_x_input.value() - self.point1_x_input.value()
                stage_dy = self.point2_y_input.value() - self.point1_y_input.value()
                stage_distance = (stage_dx ** 2 + stage_dy ** 2) ** 0.5
                
                # Calculate scale
                if pixel_distance > 0:
                    scale = stage_distance / pixel_distance
                    self.distance_label.setText(
                        f"Distance: {pixel_distance:.1f} pixels = {stage_distance:.3f} µm "
                        f"(Scale: {scale:.6f} µm/pixel)"
                    )
                else:
                    self.distance_label.setText(f"Distance: {pixel_distance:.1f} pixels")
            else:
                self.distance_label.setText(f"Pixel distance: {pixel_distance:.1f} pixels")
    
    def get_calibration_data(self) -> Dict[str, Any]:
        """Get current calibration data."""
        return self.coordinate_transformer.export_calibration()
    
    def on_calibration_updated(self, is_valid: bool) -> None:
        """Handle calibration updates."""
        self.log_info(f"Calibration updated. Valid: {is_valid}")


class CalibrationDialog(CalibrationWizardDialog):
    """Backward compatibility wrapper."""
    
    def __init__(self, pixel_x: int, pixel_y: int, point_label: str, parent=None, coordinate_transformer=None):
        # Use existing transformer if provided, otherwise create new one
        if coordinate_transformer is None:
            from models.coordinate_transformer import CoordinateTransformer
            coordinate_transformer = CoordinateTransformer()
        
        super().__init__(
            coordinate_transformer=coordinate_transformer,
            initial_pixel_x=pixel_x,
            initial_pixel_y=pixel_y,
            initial_label=point_label,
            parent=parent
        )
    
    def get_stage_coordinates(self) -> Tuple[float, float]:
        """Get stage coordinates from first point input."""
        if hasattr(self, 'point1_x_input') and hasattr(self, 'point1_y_input'):
            return self.point1_x_input.value(), self.point1_y_input.value()
        return 0.0, 0.0
    
    def set_stage_coordinates(self, stage_x: float, stage_y: float) -> None:
        """Set stage coordinates for first point."""
        if hasattr(self, 'point1_x_input') and hasattr(self, 'point1_y_input'):
            self.point1_x_input.setValue(stage_x)
            self.point1_y_input.setValue(stage_y)
