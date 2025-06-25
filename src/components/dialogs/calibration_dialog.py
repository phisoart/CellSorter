"""
Calibration Dialog for CellSorter

This dialog allows users to enter real-world stage coordinates
for calibration points clicked on the image.
"""

from typing import Optional, Tuple
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QPushButton,
    QDoubleSpinBox, QDialogButtonBox, QGroupBox, QTextEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class CalibrationDialog(QDialog):
    """
    Dialog for entering stage coordinates for calibration points.
    
    Allows users to input real-world XY stage coordinates corresponding
    to pixel coordinates clicked on the microscopy image.
    """
    
    def __init__(self, pixel_x: int, pixel_y: int, point_label: str, parent=None):
        super().__init__(parent)
        
        self.pixel_x = pixel_x
        self.pixel_y = pixel_y
        self.point_label = point_label
        self.stage_x: Optional[float] = None
        self.stage_y: Optional[float] = None
        
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Set up the dialog UI."""
        self.setWindowTitle(f"Calibration Point: {self.point_label}")
        self.setModal(True)
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel(f"Enter Stage Coordinates for {self.point_label}")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Pixel coordinates display
        pixel_group = QGroupBox("Image Coordinates (Pixels)")
        pixel_layout = QFormLayout(pixel_group)
        
        pixel_x_label = QLabel(str(self.pixel_x))
        pixel_x_label.setStyleSheet("QLabel { font-family: monospace; font-weight: bold; }")
        pixel_y_label = QLabel(str(self.pixel_y))
        pixel_y_label.setStyleSheet("QLabel { font-family: monospace; font-weight: bold; }")
        
        pixel_layout.addRow("X (pixels):", pixel_x_label)
        pixel_layout.addRow("Y (pixels):", pixel_y_label)
        layout.addWidget(pixel_group)
        
        # Stage coordinates input
        stage_group = QGroupBox("Stage Coordinates (Real-World)")
        stage_layout = QFormLayout(stage_group)
        
        self.stage_x_input = QDoubleSpinBox()
        self.stage_x_input.setRange(-999999.999, 999999.999)
        self.stage_x_input.setDecimals(3)
        self.stage_x_input.setSuffix(" μm")
        self.stage_x_input.setMinimumWidth(120)
        
        self.stage_y_input = QDoubleSpinBox()
        self.stage_y_input.setRange(-999999.999, 999999.999)
        self.stage_y_input.setDecimals(3)
        self.stage_y_input.setSuffix(" μm")
        self.stage_y_input.setMinimumWidth(120)
        
        stage_layout.addRow("X (μm):", self.stage_x_input)
        stage_layout.addRow("Y (μm):", self.stage_y_input)
        layout.addWidget(stage_group)
        
        # Instructions
        instructions = QTextEdit()
        instructions.setMaximumHeight(80)
        instructions.setReadOnly(True)
        instructions.setHtml("""
        <p><b>Instructions:</b> Enter the corresponding real-world XY stage coordinates 
        for this calibration point. These coordinates should be obtained from your 
        microscope's stage position readout.</p>
        """)
        layout.addWidget(instructions)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Set focus to first input
        self.stage_x_input.setFocus()
    
    def accept(self) -> None:
        """Accept dialog and store entered coordinates."""
        self.stage_x = self.stage_x_input.value()
        self.stage_y = self.stage_y_input.value()
        super().accept()
    
    def get_stage_coordinates(self) -> Tuple[float, float]:
        """
        Get the entered stage coordinates.
        
        Returns:
            Tuple of (stage_x, stage_y) in micrometers
        """
        return (self.stage_x or 0.0, self.stage_y or 0.0)
    
    def set_stage_coordinates(self, stage_x: float, stage_y: float) -> None:
        """
        Set default stage coordinates.
        
        Args:
            stage_x: X stage coordinate in micrometers
            stage_y: Y stage coordinate in micrometers
        """
        self.stage_x_input.setValue(stage_x)
        self.stage_y_input.setValue(stage_y)