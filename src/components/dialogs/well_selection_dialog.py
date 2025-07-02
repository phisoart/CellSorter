from typing import Optional

from PySide6.QtWidgets import QDialog, QVBoxLayout, QDialogButtonBox
from PySide6.QtCore import Signal

from components.widgets.well_plate import WellPlateWidget

class WellSelectionDialog(QDialog):
    """Dialog providing a 96-well plate for well selection."""

    wellSelected = Signal(str)  # Emits selected well string

    def __init__(self, current_well: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Well")
        self.setModal(True)
        self._selected_well: Optional[str] = current_well
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self.well_plate = WellPlateWidget()
        if self._selected_well:
            self.well_plate.highlight_well(self._selected_well)
        self.well_plate.well_clicked.connect(self._on_well_clicked)
        layout.addWidget(self.well_plate)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _on_well_clicked(self, well: str):
        self._selected_well = well
        self.wellSelected.emit(well)

    def selected_well(self) -> Optional[str]:
        return self._selected_well

    @staticmethod
    def get_well(current_well: str = "", parent=None) -> Optional[str]:
        dialog = WellSelectionDialog(current_well, parent)
        if dialog.exec() == QDialog.Accepted:
            return dialog.selected_well()
        return None 