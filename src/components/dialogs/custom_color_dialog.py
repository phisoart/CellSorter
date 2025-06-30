"""
Custom Color Palette Dialog for CellSorter

A dialog that displays a predefined grid of colors for selection,
instead of a free-form QColorDialog.
"""

from typing import Optional
from PySide6.QtWidgets import QDialog, QGridLayout, QPushButton, QDialogButtonBox, QWidget
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtCore import Signal, QSize

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
        layout = QGridLayout(self)
        layout.setSpacing(10)

        # Create color swatches
        row, col = 0, 0
        for color_name, color_hex in SELECTION_COLORS.items():
            btn = QPushButton()
            btn.setFixedSize(40, 40)
            btn.setStyleSheet(f"background-color: {color_hex}; border: 1px solid #333; border-radius: 4px;")
            btn.setToolTip(color_name)
            btn.clicked.connect(lambda chk=None, c=color_hex: self._on_color_clicked(c))
            layout.addWidget(btn, row, col)
            
            col += 1
            if col > 3:
                col = 0
                row += 1

        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Cancel)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box, row + 1, 0, 1, 4)

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