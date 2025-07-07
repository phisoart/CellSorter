"""
DUAL Mode Test for Main Image Navigation Sync
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from PySide6.QtCore import QObject, Signal

from headless.ui_model import UIModel
from headless.main_window_adapter import MainWindowAdapter
from headless.mode_manager import ModeManager
from pages.main_window import MainWindow
from services.theme_manager import ThemeManager

# Ensure QApplication instance exists
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

class TestNavigationSyncDUAL(unittest.TestCase):
    """
    Test suite for ensuring navigation requests from the ROI dialog
    are correctly handled by the GUI in DUAL mode.
    """

    def setUp(self):
        """Set up the DUAL mode test environment."""
        self.theme_manager = MagicMock(spec=ThemeManager)
        
        self.main_window = MainWindow(theme_manager=self.theme_manager)

        # The adapter now only takes the mode_manager, and we connect the window later
        self.mode_manager = MagicMock(spec=ModeManager)
        self.adapter = MainWindowAdapter(self.mode_manager)
        self.adapter.connect_to_window(self.main_window)

        # Mock dependencies to isolate navigation logic
        self.main_window.csv_parser = MagicMock()
        self.main_window.selection_manager = MagicMock()
        # Crucially, we mock the ImageHandler to check if its methods are called
        self.main_window.image_handler = MagicMock()
        self.main_window.coordinate_transformer = MagicMock()
        
        self.main_window.show()

    def tearDown(self):
        """Clean up after each test."""
        self.main_window.close()

    @patch('pages.main_window.ROIManagementDialog')
    def test_navigation_request_sync_dual(self, MockROIManagementDialog):
        """DUAL: Test that a navigation request from the dialog calls the image_handler."""
        # 1. Setup Mocks
        mock_dialog_instance = self._setup_dialog_mocks(MockROIManagementDialog)
        
        # Configure mocks for the navigation path
        self.main_window.csv_parser.get_data.return_value.any.return_value.any.return_value = True
        self.main_window.csv_parser.get_xy_columns.return_value = ('x', 'y')
        self.main_window.csv_parser.get_data_by_index.return_value = {'x': 123, 'y': 456}
        self.main_window.coordinate_transformer.transform.return_value = (150, 480)

        # 2. Open the dialog
        self.main_window.show_roi_management_dialog('sel_1')
        QTest.qWait(50)

        # 3. Simulate the navigation signal from the mocked dialog
        self.main_window.roi_management_dialog.cell_navigation_requested.emit(42)
        QTest.qWait(50)

        # 4. Assertions
        # Verify that the image handler's centering method was called with the correct, transformed coordinates
        self.main_window.image_handler.center_on.assert_called_once_with(150, 480)

        # Also check that the UIModel was updated (a key part of DUAL mode)
        # This assumes the adapter has a method to sync the view's center
        # For now, we focus on the direct GUI reaction, which is a prerequisite.
        # A more advanced test would be:
        # self.adapter.sync_viewport_to_model()
        # self.assertEqual(self.ui_model.get_property('image_view.center'), (150, 480))
        self.assertTrue(self.main_window.image_handler.center_on.called)
        
    def _setup_dialog_mocks(self, MockROIManagementDialog):
        """Helper to set up common mocks for the ROI dialog."""
        self.main_window.selection_manager.get_selection.return_value = {'indices': [10, 20, 42], 'label': 'Test', 'color': '#00ff00'}
        self.main_window.csv_parser.get_data.return_value.any.return_value.any.return_value = True

        mock_dialog_instance = MockROIManagementDialog.return_value
        
        class SignalEmitter(QObject):
            cell_navigation_requested = Signal(int)
            changes_confirmed = Signal(str, dict)

        self.emitter = SignalEmitter()
        mock_dialog_instance.cell_navigation_requested = self.emitter.cell_navigation_requested
        mock_dialog_instance.changes_confirmed = self.emitter.changes_confirmed
        
        mock_dialog_instance.show = MagicMock()
        mock_dialog_instance.isVisible.return_value = True
        
        with patch.object(self.main_window, '_create_cell_row_data', return_value=MagicMock()):
            pass

        return mock_dialog_instance

if __name__ == '__main__':
    unittest.main() 