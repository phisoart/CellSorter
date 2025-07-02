"""
Custom Color Palette Dialog for CellSorter

A dialog that displays a predefined grid of colors for selection,
instead of a free-form QColorDialog.
"""

from typing import Optional
from PySide6.QtWidgets import QDialog, QGridLayout, QPushButton, QDialogButtonBox, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtCore import Signal, QSize, Qt

from config.settings import SELECTION_COLORS


class CustomColorDialog(QDialog):
    """
    A custom dialog to select a color from a predefined palette.
    """
    colorSelected = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Select Color")
        self.setModal(True)
        self.selected_color: Optional[str] = None

        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI components of the dialog."""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)  # Good spacing between sections
        layout.setContentsMargins(24, 20, 24, 20)  # Generous margins for elegance

        # Title area
        title_label = QLabel("색상 선택")
        title_label.setStyleSheet("""
            font-size: 14px; 
            font-weight: 600; 
            color: #2c3e50;
            margin-bottom: 8px;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Add separator line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("color: #bdc3c7; margin: 4px 0;")
        layout.addWidget(line)
        
        layout.addSpacing(8)

        # Color grid container
        grid_container = QWidget()
        grid_layout = QGridLayout(grid_container)
        grid_layout.setSpacing(12)  # Nice spacing between items
        grid_layout.setContentsMargins(8, 8, 8, 8)

        colors = list(SELECTION_COLORS.items())
        
        # Arrange in 2 columns for better layout
        for i, (color_name, color_hex) in enumerate(colors):
            row = i // 2
            col = i % 2
            
            # Create color item widget
            color_item = QWidget()
            color_item.setFixedHeight(40)  # Consistent height
            color_item.setCursor(Qt.PointingHandCursor)
            
            item_layout = QHBoxLayout(color_item)
            item_layout.setContentsMargins(8, 4, 8, 4)
            item_layout.setSpacing(12)

            # Color swatch - much larger and more visible
            color_btn = QPushButton()
            color_btn.setFixedSize(32, 28)  # Larger, more visible
            color_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color_hex}; 
                    border: 2px solid #34495e; 
                    border-radius: 6px;
                }}
                QPushButton:hover {{
                    border: 3px solid #2980b9;
                    transform: scale(1.05);
                }}
            """)
            color_btn.clicked.connect(lambda checked=False, c=color_hex: self._on_color_clicked(c))

            # Color name label
            name_label = QLabel(color_name)
            name_label.setStyleSheet("""
                font-size: 11px; 
                font-weight: 500;
                color: #2c3e50;
                padding: 2px;
            """)
            name_label.setMinimumWidth(80)

            item_layout.addWidget(color_btn)
            item_layout.addWidget(name_label)
            item_layout.addStretch()

            # Add hover effect to the entire item
            color_item.setStyleSheet("""
                QWidget:hover {
                    background-color: #ecf0f1;
                    border-radius: 8px;
                }
            """)

            grid_layout.addWidget(color_item, row, col)

        layout.addWidget(grid_container)
        
        # Add some space before buttons
        layout.addSpacing(16)

        # Button area with better styling
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        button_layout.addStretch()
        
        # Styled cancel button
        cancel_button = QPushButton("취소")
        cancel_button.setFixedSize(100, 35)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
            QPushButton:pressed {
                background-color: #6c7b7d;
            }
        """)
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(cancel_button)
        layout.addWidget(button_container)

        # Set dialog properties
        self.setFixedSize(320, 600)  # Taller for better 2-column layout
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border-radius: 12px;
            }
        """)

    def _on_color_clicked(self, color_hex: str):
        """Handle a color button click."""
        self.selected_color = color_hex
        self.colorSelected.emit(color_hex)
        self.accept()

    def get_selected_color(self) -> Optional[str]:
        """Returns the selected color hex string."""
        return self.selected_color

    @staticmethod
    def get_color(parent: Optional[QWidget] = None) -> Optional[str]:
        """
        Static method to show the dialog and get the selected color.
        """
        dialog = CustomColorDialog(parent)
        if dialog.exec() == QDialog.Accepted:
            return dialog.get_selected_color()
        return None 