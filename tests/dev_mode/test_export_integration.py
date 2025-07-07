"""
DEV Mode Integration Test for Protocol Export with ROI Management
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from PySide6.QtWidgets import QApplication

from pages.main_window import MainWindow
from services.theme_manager import ThemeManager

# Ensure QApplication instance exists
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

class TestExportIntegrationDEV(unittest.TestCase):
    """
    Tests that changes from ROI management are correctly reflected
    in the data passed to the protocol export dialog.
    """

    def setUp(self):
        """Set up the test environment."""
        self.theme_manager = MagicMock(spec=ThemeManager)
        self.main_window = MainWindow(theme_manager=self.theme_manager)
        
        # Mock dependencies
        self.main_window.image_handler = MagicMock()
        self.main_window.csv_parser = MagicMock()
        self.main_window.coordinate_transformer = MagicMock()
        self.main_window.selection_manager = MagicMock()

        # Configure mocks to meet preconditions for export
        self.main_window.image_handler.image_data = MagicMock()
        self.main_window.image_handler.image_data.shape = (800, 1000, 3) # (height, width, channels)
        self.main_window.csv_parser.data = MagicMock()
        self.main_window.csv_parser.data.empty = False
        self.main_window.coordinate_transformer.is_calibrated.return_value = True

    def tearDown(self):
        """Clean up after each test."""
        self.main_window.close()

    @patch('pages.main_window.ProtocolExportDialog')
    def test_export_reflects_roi_changes_dev(self, MockProtocolExportDialog):
        """
        DEV: Test that protocol export uses the latest cell indices
        after simulated ROI management.
        """
        # 1. Initial selection data
        initial_selection = {
            'id': 'sel1',
            'label': 'Group A',
            'color': '#ff0000',
            'well_position': 'A01',
            'indices': [10, 20, 30, 40, 50]
        }
        selections_data_stub = [{'id': 'sel1'}]

        # 2. Simulate ROI Management: user removes cells 20 and 40
        updated_indices = [10, 30, 50]
        updated_selection = initial_selection.copy()
        updated_selection['indices'] = updated_indices
        
        # Configure the selection_manager mock to return the *updated* data
        self.main_window.selection_manager.get_selection.return_value = updated_selection

        # 3. Trigger the export process
        self.main_window.export_protocol_with_data(selections_data_stub)

        # 4. Assertions
        # Check that ProtocolExportDialog was called
        MockProtocolExportDialog.assert_called_once()
        
        # Get the arguments passed to the dialog's constructor
        args, kwargs = MockProtocolExportDialog.call_args
        
        # The first argument should be the selections_dict
        passed_selections = args[0]
        
        # Verify the dialog received the *updated* selection data
        self.assertIn('sel1', passed_selections)
        self.assertEqual(len(passed_selections['sel1']['indices']), 3)
        self.assertEqual(passed_selections['sel1']['indices'], updated_indices)
        self.assertNotIn(20, passed_selections['sel1']['indices'])
        self.assertNotIn(40, passed_selections['sel1']['indices'])

if __name__ == '__main__':
    unittest.main() 