"""
DEV Mode Test for Main Image Navigation from ROI Dialog
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject

from pages.main_window import MainWindow
from services.theme_manager import ThemeManager
from utils.logging_config import setup_logging

# Ensure QApplication instance exists
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

class TestMainImageNavigationDEV(unittest.TestCase):
    """Test suite for main image navigation functionality in DEV mode."""

    @classmethod
    def setUpClass(cls):
        """Set up logging for the test class."""
        setup_logging()

    def setUp(self):
        """Set up the test environment."""
        self.theme_manager = MagicMock(spec=ThemeManager)
        self.main_window = MainWindow(theme_manager=self.theme_manager)
        
        # Mock dependencies to isolate navigation logic
        self.main_window.csv_parser = MagicMock()
        self.main_window.image_handler = MagicMock()
        self.main_window.coordinate_transformer = MagicMock()
        self.main_window.selection_manager = MagicMock()

    def tearDown(self):
        """Clean up after each test."""
        if self.main_window.roi_management_dialog:
            self.main_window.roi_management_dialog.close()
        self.main_window.close()

    def test_navigate_to_cell_dev(self):
        """DEV: Test navigation to a cell centers the image view."""
        # 1. Setup Mocks
        # Mock CSV data
        self.main_window.csv_parser.get_data.return_value.any.return_value.any.return_value = True
        self.main_window.csv_parser.get_xy_columns.return_value = ('x', 'y')
        self.main_window.csv_parser.get_data_by_index.return_value = {'x': 100, 'y': 200}
        
        # Mock coordinate transformation
        self.main_window.coordinate_transformer.transform.return_value = (150.5, 250.5)

        # 2. Call the navigation method directly
        self.main_window.navigate_to_cell(cell_index=42)

        # 3. Assertions
        # Verify that the CSV parser was called correctly
        self.main_window.csv_parser.get_data_by_index.assert_called_once_with(42)
        
        # Verify that the coordinate transformer was called with the correct data
        self.main_window.coordinate_transformer.transform.assert_called_once_with(100, 200)

        # Verify that the image handler's center_on method was called with the transformed coordinates
        self.main_window.image_handler.center_on.assert_called_once_with(150.5, 250.5)

    @patch('pages.main_window.ROIManagementDialog')
    def test_roi_dialog_navigation_signal_dev(self, MockROIManagementDialog):
        """DEV: Test that the dialog's navigation signal triggers main window's navigation."""
        # 1. Setup Mocks
        # Mock selection and CSV data
        self.main_window.selection_manager.get_selection.return_value = {'indices': [1, 2, 3], 'label': 'Test', 'color': '#ff0000'}
        self.main_window.csv_parser.get_data.return_value.any.return_value.any.return_value = True
        
        # Mock the dialog instance and its signal
        mock_dialog_instance = MockROIManagementDialog.return_value
        # Create a mock signal
        mock_dialog_instance.cell_navigation_requested = MagicMock(spec=QObject)
        mock_dialog_instance.cell_navigation_requested.connect = MagicMock()
        
        # Mock the data creation helper to avoid dependency on real CSV data
        with patch.object(self.main_window, '_create_cell_row_data', return_value=MagicMock()):
            # 2. Trigger the dialog creation
            self.main_window.show_roi_management_dialog('sel_1')

        # 3. Assert that the signal was connected
        mock_dialog_instance.cell_navigation_requested.connect.assert_called_with(self.main_window.navigate_to_cell)

        # 4. Simulate the signal emission
        # To do this "properly" we'd need a real signal, but we can call the slot directly
        # as we've already tested the connection. Here we'll just re-test navigate_to_cell
        # to ensure the E2E flow is implicitly sound.
        
        self.main_window.csv_parser.get_xy_columns.return_value = ('x', 'y')
        self.main_window.csv_parser.get_data_by_index.return_value = {'x': 50, 'y': 75}
        self.main_window.coordinate_transformer.transform.return_value = (60.0, 90.0)

        self.main_window.navigate_to_cell(cell_index=2)

        self.main_window.image_handler.center_on.assert_called_once_with(60.0, 90.0)

if __name__ == '__main__':
    unittest.main() 