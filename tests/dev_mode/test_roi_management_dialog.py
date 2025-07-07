"""
DEV Mode Tests for ROI Management Dialog

Tests the modal dialog functionality in headless simulation mode with comprehensive logging.
Validates RowCellManager integration, signal handling, and dialog lifecycle.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any
import logging

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt, QTimer

from components.dialogs.roi_management_dialog import ROIManagementDialog, show_roi_management_dialog
from components.widgets.row_cell_manager import CellRowData
from headless.testing.framework import UITestCase, HeadlessTestRunner
from utils.logging_config import setup_logging


class TestROIManagementDialogDEV(UITestCase):
    """DEV mode tests for ROI Management Dialog."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class."""
        cls.app = QApplication.instance() or QApplication([])
        
        # Set up enhanced logging for DEV mode
        cls.logger = setup_logging("test_roi_dialog_dev")
        cls.logger.info("=== DEV MODE: ROI Management Dialog Tests ===")
    
    def setUp(self):
        """Set up each test method."""
        super().setUp()
        self.logger.info(f"Setup test: {self._testMethodName}")
    
    def tearDown(self):
        """Tear down each test method."""
        super().tearDown()
        self.logger.info(f"Teardown test: {self._testMethodName}")
    
    def _create_mock_cell_row_data(self, cell_count: int = 10) -> CellRowData:
        """Create mock cell row data for testing."""
        cell_indices = list(range(cell_count))
        cell_metadata = {}
        
        for i in range(cell_count):
            cell_metadata[i] = {
                'area': 100 + i * 10,
                'intensity': 50 + i * 5,
                'perimeter': 30 + i * 3,
                'x': i * 20,
                'y': i * 15
            }
        
        row_data = CellRowData(
            selection_id="test_selection_1",
            selection_label="Test Selection Row",
            selection_color="#FF5733",
            cell_indices=cell_indices,
            cell_metadata=cell_metadata
        )
        
        self.logger.debug(f"Created mock cell row data with {cell_count} cells")
        return row_data
    
    def test_dialog_initialization_dev(self):
        """DEV: Test dialog initialization and setup."""
        self.logger.info("Testing dialog initialization...")
        
        # Test initialization without data
        dialog = ROIManagementDialog()
        
        # Verify basic properties
        self.assertIsNotNone(dialog)
        self.assertTrue(dialog.isModal())
        self.assertEqual("Manage ROIs", dialog.windowTitle())
        
        # Verify components exist
        self.assertTrue(hasattr(dialog, 'cell_manager'))
        self.assertTrue(hasattr(dialog, 'cancel_button'))
        self.assertTrue(hasattr(dialog, 'confirm_button'))
        self.assertTrue(hasattr(dialog, 'title_label'))
        self.assertTrue(hasattr(dialog, 'subtitle_label'))
        
        # Verify initial state
        self.assertIsNone(dialog.row_data)
        self.assertFalse(dialog.changes_made)
        self.assertEqual({}, dialog.initial_states)
        
        # Verify button properties
        self.assertEqual("Cancel", dialog.cancel_button.text())
        self.assertEqual("Confirm", dialog.confirm_button.text())
        self.assertTrue(dialog.confirm_button.isDefault())
        
        dialog.deleteLater()
        self.logger.info("✅ Dialog initialization verified")
    
    def test_dialog_with_row_data_dev(self):
        """DEV: Test dialog initialization with row data."""
        self.logger.info("Testing dialog with row data...")
        
        # Create test data
        row_data = self._create_mock_cell_row_data(15)
        
        # Initialize dialog with data
        dialog = ROIManagementDialog(row_data=row_data)
        
        # Verify data loading
        self.assertEqual(row_data, dialog.row_data)
        self.assertEqual(15, len(dialog.initial_states))
        
        # Verify all cells initially included
        for cell_index in row_data.cell_indices:
            self.assertTrue(dialog.initial_states[cell_index])
        
        # Verify subtitle update
        subtitle_text = dialog.subtitle_label.text()
        self.assertIn("Test Selection Row", subtitle_text)
        self.assertIn("15 cells", subtitle_text)
        self.assertIn("#FF5733", subtitle_text)
        
        dialog.deleteLater()
        self.logger.info("✅ Dialog with row data verified")
    
    def test_cell_manager_integration_dev(self):
        """DEV: Test RowCellManager integration."""
        self.logger.info("Testing cell manager integration...")
        
        row_data = self._create_mock_cell_row_data(8)
        dialog = ROIManagementDialog(row_data=row_data)
        
        # Verify cell manager exists and is properly configured
        cell_manager = dialog.cell_manager
        self.assertIsNotNone(cell_manager)
        
        # Verify cell manager has data
        self.assertEqual(row_data, cell_manager.row_data)
        
        # Test cell manager methods
        included_cells = cell_manager.get_included_cells()
        excluded_cells = cell_manager.get_excluded_cells()
        
        # Initially all cells should be included
        self.assertEqual(8, len(included_cells))
        self.assertEqual(0, len(excluded_cells))
        self.assertEqual(set(range(8)), set(included_cells))
        
        dialog.deleteLater()
        self.logger.info("✅ Cell manager integration verified")
    
    def test_signal_connections_dev(self):
        """DEV: Test signal connections between dialog and cell manager."""
        self.logger.info("Testing signal connections...")
        
        row_data = self._create_mock_cell_row_data(5)
        dialog = ROIManagementDialog(row_data=row_data)
        
        # Mock signal receivers
        inclusion_signals = []
        navigation_signals = []
        
        dialog.cell_inclusion_changed.connect(
            lambda sel_id, cell_idx, included: inclusion_signals.append((sel_id, cell_idx, included))
        )
        dialog.cell_navigation_requested.connect(
            lambda cell_idx: navigation_signals.append(cell_idx)
        )
        
        # Simulate cell inclusion change
        dialog.on_cell_inclusion_changed("test_selection_1", 2, False)
        
        # Verify signal emission
        self.assertEqual(1, len(inclusion_signals))
        signal_data = inclusion_signals[0]
        self.assertEqual("test_selection_1", signal_data[0])
        self.assertEqual(2, signal_data[1])
        self.assertFalse(signal_data[2])
        
        # Verify changes tracking
        self.assertTrue(dialog.changes_made)
        
        # Simulate navigation request
        dialog.on_cell_navigation_requested(3)
        
        # Verify navigation signal
        self.assertEqual(1, len(navigation_signals))
        self.assertEqual(3, navigation_signals[0])
        
        dialog.deleteLater()
        self.logger.info("✅ Signal connections verified")
    
    def test_dialog_buttons_functionality_dev(self):
        """DEV: Test dialog button functionality."""
        self.logger.info("Testing dialog button functionality...")
        
        row_data = self._create_mock_cell_row_data(3)
        dialog = ROIManagementDialog(row_data=row_data)
        
        # Test cancel functionality
        cancel_result = []
        dialog.rejected.connect(lambda: cancel_result.append("cancelled"))
        
        # Simulate cancel button click
        dialog.on_cancel_clicked()
        
        # In headless mode, we check the result indirectly
        self.assertTrue(len(cancel_result) == 1 or dialog.result() == ROIManagementDialog.Rejected)
        
        # Create new dialog for confirm test
        dialog2 = ROIManagementDialog(row_data=row_data)
        
        # Test confirm functionality
        confirm_result = []
        changes_signals = []
        
        dialog2.accepted.connect(lambda: confirm_result.append("confirmed"))
        dialog2.changes_confirmed.connect(
            lambda sel_id, changes: changes_signals.append((sel_id, changes))
        )
        
        # Make some changes
        dialog2.on_cell_inclusion_changed("test_selection_1", 1, False)
        
        # Simulate confirm button click
        dialog2.on_confirm_clicked()
        
        # Verify confirm signal and changes
        self.assertTrue(len(confirm_result) == 1 or dialog2.result() == ROIManagementDialog.Accepted)
        self.assertEqual(1, len(changes_signals))
        
        changes_data = changes_signals[0][1]
        self.assertIn('included_cells', changes_data)
        self.assertIn('excluded_cells', changes_data)
        self.assertTrue(changes_data['changes_made'])
        
        dialog.deleteLater()
        dialog2.deleteLater()
        self.logger.info("✅ Dialog button functionality verified")
    
    def test_keyboard_navigation_dev(self):
        """DEV: Test keyboard navigation and shortcuts."""
        self.logger.info("Testing keyboard navigation...")
        
        row_data = self._create_mock_cell_row_data(4)
        dialog = ROIManagementDialog(row_data=row_data)
        
        # Mock key events
        escape_handled = False
        enter_handled = False
        
        # Test Escape key handling
        from PySide6.QtGui import QKeyEvent
        escape_event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_Escape, Qt.NoModifier)
        
        # Simulate escape key
        original_on_cancel = dialog.on_cancel_clicked
        def mock_cancel():
            nonlocal escape_handled
            escape_handled = True
            original_on_cancel()
        
        dialog.on_cancel_clicked = mock_cancel
        dialog.keyPressEvent(escape_event)
        
        # Verify escape handling
        self.assertTrue(escape_handled)
        
        # Create new dialog for Enter test
        dialog2 = ROIManagementDialog(row_data=row_data)
        
        # Test Enter key handling
        enter_event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_Return, Qt.NoModifier)
        
        original_on_confirm = dialog2.on_confirm_clicked
        def mock_confirm():
            nonlocal enter_handled
            enter_handled = True
            original_on_confirm()
        
        dialog2.on_confirm_clicked = mock_confirm
        dialog2.keyPressEvent(enter_event)
        
        # Verify enter handling
        self.assertTrue(enter_handled)
        
        dialog.deleteLater()
        dialog2.deleteLater()
        self.logger.info("✅ Keyboard navigation verified")
    
    def test_change_tracking_logic_dev(self):
        """DEV: Test change tracking and state management."""
        self.logger.info("Testing change tracking logic...")
        
        row_data = self._create_mock_cell_row_data(6)
        dialog = ROIManagementDialog(row_data=row_data)
        
        # Initially no changes
        self.assertFalse(dialog.changes_made)
        self.assertFalse(dialog._has_changes_from_initial())
        
        # Make a change
        dialog.on_cell_inclusion_changed("test_selection_1", 2, False)
        self.assertTrue(dialog.changes_made)
        
        # Revert the change
        dialog.on_cell_inclusion_changed("test_selection_1", 2, True)
        # Note: In real implementation, this might not automatically reset changes_made
        # as it tracks that ANY change was made, not current state vs initial
        
        # Make multiple changes
        dialog.on_cell_inclusion_changed("test_selection_1", 0, False)
        dialog.on_cell_inclusion_changed("test_selection_1", 1, False)
        dialog.on_cell_inclusion_changed("test_selection_1", 3, False)
        
        self.assertTrue(dialog.changes_made)
        
        dialog.deleteLater()
        self.logger.info("✅ Change tracking logic verified")
    
    def test_get_cell_states_dev(self):
        """DEV: Test cell states retrieval."""
        self.logger.info("Testing cell states retrieval...")
        
        row_data = self._create_mock_cell_row_data(5)
        dialog = ROIManagementDialog(row_data=row_data)
        
        # Get initial states
        initial_states = dialog.get_cell_states()
        
        self.assertEqual("test_selection_1", initial_states['selection_id'])
        self.assertEqual(5, len(initial_states['included_cells']))
        self.assertEqual(0, len(initial_states['excluded_cells']))
        self.assertFalse(initial_states['changes_made'])
        
        # Make changes
        dialog.on_cell_inclusion_changed("test_selection_1", 1, False)
        dialog.on_cell_inclusion_changed("test_selection_1", 3, False)
        
        # Get updated states
        updated_states = dialog.get_cell_states()
        
        self.assertEqual(3, len(updated_states['included_cells']))  # 0, 2, 4
        self.assertEqual(2, len(updated_states['excluded_cells']))  # 1, 3
        self.assertTrue(updated_states['changes_made'])
        
        # Verify specific excluded cells
        excluded_cells = updated_states['excluded_cells']
        self.assertIn(1, excluded_cells)
        self.assertIn(3, excluded_cells)
        
        dialog.deleteLater()
        self.logger.info("✅ Cell states retrieval verified")
    
    def test_convenience_function_dev(self):
        """DEV: Test convenience function for dialog usage."""
        self.logger.info("Testing convenience function...")
        
        row_data = self._create_mock_cell_row_data(3)
        
        # Mock dialog execution
        with patch.object(ROIManagementDialog, 'exec') as mock_exec:
            mock_exec.return_value = ROIManagementDialog.Accepted
            
            # Mock get_cell_states
            mock_states = {
                'selection_id': 'test_selection_1',
                'included_cells': [0, 2],
                'excluded_cells': [1],
                'changes_made': True
            }
            
            with patch.object(ROIManagementDialog, 'get_cell_states', return_value=mock_states):
                result = show_roi_management_dialog(row_data=row_data)
            
            # Verify result
            self.assertIsNotNone(result)
            self.assertEqual(mock_states, result)
        
        # Test cancelled dialog
        with patch.object(ROIManagementDialog, 'exec') as mock_exec:
            mock_exec.return_value = ROIManagementDialog.Rejected
            
            result = show_roi_management_dialog(row_data=row_data)
            
            # Should return None for cancelled dialog
            self.assertIsNone(result)
        
        self.logger.info("✅ Convenience function verified")
    
    def test_comprehensive_workflow_dev(self):
        """DEV: Test complete end-to-end dialog workflow."""
        self.logger.info("Testing comprehensive workflow...")
        
        # Create test data
        row_data = self._create_mock_cell_row_data(10)
        
        # Track all signals
        signals_log = {
            'cell_inclusion_changed': [],
            'cell_navigation_requested': [],
            'changes_confirmed': []
        }
        
        dialog = ROIManagementDialog(row_data=row_data)
        
        # Connect all signals
        dialog.cell_inclusion_changed.connect(
            lambda sel_id, cell_idx, included: signals_log['cell_inclusion_changed'].append((sel_id, cell_idx, included))
        )
        dialog.cell_navigation_requested.connect(
            lambda cell_idx: signals_log['cell_navigation_requested'].append(cell_idx)
        )
        dialog.changes_confirmed.connect(
            lambda sel_id, changes: signals_log['changes_confirmed'].append((sel_id, changes))
        )
        
        # 1. Verify initial state
        self.assertEqual(10, len(dialog.initial_states))
        self.assertFalse(dialog.changes_made)
        
        # 2. Exclude some cells
        dialog.on_cell_inclusion_changed("test_selection_1", 2, False)
        dialog.on_cell_inclusion_changed("test_selection_1", 5, False)
        dialog.on_cell_inclusion_changed("test_selection_1", 8, False)
        
        # 3. Navigate to a cell
        dialog.on_cell_navigation_requested(7)
        
        # 4. Include one cell back
        dialog.on_cell_inclusion_changed("test_selection_1", 5, True)
        
        # 5. Confirm changes
        dialog.on_confirm_clicked()
        
        # Verify signal history
        self.assertEqual(4, len(signals_log['cell_inclusion_changed']))  # 3 excludes + 1 include
        self.assertEqual(1, len(signals_log['cell_navigation_requested']))
        self.assertEqual(1, len(signals_log['changes_confirmed']))
        
        # Verify final state
        final_changes = signals_log['changes_confirmed'][0][1]
        self.assertTrue(final_changes['changes_made'])
        self.assertEqual(8, len(final_changes['included_cells']))  # 10 - 2 excluded
        self.assertEqual(2, len(final_changes['excluded_cells']))   # 2, 8 (5 was re-included)
        
        excluded_cells = final_changes['excluded_cells']
        self.assertIn(2, excluded_cells)
        self.assertIn(8, excluded_cells)
        self.assertNotIn(5, excluded_cells)  # Was re-included
        
        dialog.deleteLater()
        self.logger.info("✅ Comprehensive workflow verified")
        self.logger.info("🎉 All ROI Management Dialog DEV mode tests completed successfully!")


def run_dev_tests():
    """Run DEV mode tests directly."""
    runner = HeadlessTestRunner()
    result = runner.run_test_case(TestROIManagementDialogDEV)
    runner.print_summary()
    return result


if __name__ == "__main__":
    # Run tests directly
    run_dev_tests() 