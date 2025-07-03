import pytest
from types import SimpleNamespace

from PySide6.QtWidgets import QApplication

from src.components.dialogs.image_export_dialog import ImageExportDialog
from src.components.dialogs.protocol_export_dialog import ProtocolExportDialog


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def _get_app():
    """Return existing QApplication or create a headless one."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class _DummyTransformer:
    """Minimal coordinate transformer stub for dialog construction."""

    def is_calibrated(self) -> bool:
        return True

    def pixel_to_stage(self, x: int, y: int):
        return SimpleNamespace(stage_x=x, stage_y=y)


# Sample test data shared by both dialogs
_SAMPLE_SELECTIONS = {
    "sel1": {
        "label": "Selection 1",
        "color": "#FF0000",
        "cell_indices": list(range(10)),
        "well_position": "A01",
    },
    "sel2": {
        "label": "Selection 2",
        "color": "#00FF00",
        "cell_indices": list(range(5)),
        "well_position": "B01",
    },
}

_DUMMY_BOUNDING_BOXES = [(0, 0, 1, 1)] * 20  # Minimal placeholder boxes
_DUMMY_IMAGE_INFO = {"filename": "img", "width": 1, "height": 1, "format": "TIFF"}


@pytest.mark.parametrize("dialog_cls", [ImageExportDialog, ProtocolExportDialog])
def test_table_button_size_compact(dialog_cls):
    """Ensure Extract/Export buttons inside QTableWidget fit within row height."""
    app = _get_app()

    # Prepare dialog instance based on required arguments
    if dialog_cls is ImageExportDialog:
        dlg = dialog_cls(_SAMPLE_SELECTIONS, image_data=[], bounding_boxes=_DUMMY_BOUNDING_BOXES)
    else:  # ProtocolExportDialog
        dlg = dialog_cls(
            _SAMPLE_SELECTIONS,
            image_data=[],
            bounding_boxes=_DUMMY_BOUNDING_BOXES,
            coordinate_transformer=_DummyTransformer(),
            image_info=_DUMMY_IMAGE_INFO,
        )

    dlg.show()
    app.processEvents()

    # Check first row/button size as representative
    row_height = dlg.table.rowHeight(0)
    btn = dlg.table.cellWidget(0, 5)
    assert btn is not None, "Button widget not found in table cell"

    # `sizeHint` gives preferred size, actual size should be <= row height
    button_height = btn.sizeHint().height()

    # Log values for debug output
    print(f"Row height: {row_height}px, Button height: {button_height}px")

    # Assertion: button should not exceed row height and preferably be equal or smaller
    assert button_height <= row_height, (
        f"Button height {button_height}px exceeds row height {row_height}px"
    )

    dlg.close() 