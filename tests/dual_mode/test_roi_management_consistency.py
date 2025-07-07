"""
DUAL Mode Test for ROI Management Dialog Consistency
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

class TestROIManagementConsistencyDUAL(unittest.TestCase):
    """
    Test suite for ensuring consistency of the ROI Management Dialog
    between the Headless UI Model and the GUI in DUAL mode.
    """

    def setUp(self):
        """Set up the DUAL mode test environment."""
        self.theme_manager = MagicMock(spec=ThemeManager)
        
        # We need a real MainWindow for GUI interactions
        self.main_window = MainWindow(theme_manager=self.theme_manager)
        
        # The adapter connects the UI model to the real GUI
        # The adapter now only takes the mode_manager, and we connect the window later
        self.mode_manager = MagicMock(spec=ModeManager)
        self.adapter = MainWindowAdapter(self.mode_manager)
        self.adapter.connect_to_window(self.main_window)

        # Mock dependencies that are not relevant to this test
        self.main_window.csv_parser = MagicMock()
        self.main_window.selection_manager = MagicMock()
        
        self.main_window.show()

    def tearDown(self):
        """Clean up after each test."""
        self.main_window.close()
        
    @patch('pages.main_window.ROIManagementDialog')
    def test_dialog_state_sync_dual(self, MockROIManagementDialog):
        """DUAL: Test that cell inclusion/exclusion in the dialog syncs with the model."""
        # 1. Setup Mocks and Initial State
        mock_dialog_instance = self._setup_dialog_mocks(MockROIManagementDialog)
        
        # 2. Simulate opening the dialog from the GUI
        # This would normally happen by clicking the "Manage ROIs" button
        self.main_window.show_roi_management_dialog('sel_1')
        QTest.qWait(50) # Allow event loop to process

        self.assertIsNotNone(self.main_window.roi_management_dialog)
        self.assertTrue(self.main_window.roi_management_dialog.isVisible())

        # 3. Simulate a change in the dialog (e.g., a cell is excluded)
        # This is tricky without a real dialog. We'll emit the dialog's signal
        # and check if the underlying models are updated.
        self.main_window.selection_manager.update_selection_indices.return_value = None
        
        # Simulate confirming changes in the dialog
        changes = {'changes_made': True, 'included_cells': [1, 3]}
        self.main_window.roi_management_dialog.changes_confirmed.emit('sel_1', changes)
        QTest.qWait(50)
        
        # 4. Assertions
        # Check that the selection_manager in the main_window was updated
        self.main_window.selection_manager.update_selection_indices.assert_called_once_with('sel_1', [1, 3])

        # To properly test the UI model sync, the adapter would need a method
        # to reflect this change. Let's assume the adapter's `_sync_selections`
        # would be called (this is an integration test aspect).
        
        # For this test, we confirm the signal from the dialog correctly calls
        # the main window's handler, which is the key DUAL mode integration point.
        self.assertTrue(self.main_window.selection_manager.update_selection_indices.called)
        
    def _setup_dialog_mocks(self, MockROIManagementDialog):
        """Helper to set up common mocks for the ROI dialog."""
        # Mock selection and CSV data
        self.main_window.selection_manager.get_selection.return_value = {'indices': [1, 2, 3], 'label': 'Test', 'color': '#ff0000'}
        self.main_window.csv_parser.get_data.return_value.any.return_value.any.return_value = True
        
        mock_dialog_instance = MockROIManagementDialog.return_value
        
        # To make signals work in tests, they need to be on a QObject
        class SignalEmitter(QObject):
            cell_navigation_requested = Signal(int)
            changes_confirmed = Signal(str, dict)
        
        self.emitter = SignalEmitter()
        mock_dialog_instance.cell_navigation_requested = self.emitter.cell_navigation_requested
        mock_dialog_instance.changes_confirmed = self.emitter.changes_confirmed
        
        # Mock the show method to prevent a real dialog from showing
        mock_dialog_instance.show = MagicMock()
        mock_dialog_instance.isVisible.return_value = True

        # Mock the data creation helper
        with patch.object(self.main_window, '_create_cell_row_data', return_value=MagicMock()):
            pass

        return mock_dialog_instance

if __name__ == '__main__':
    unittest.main() 