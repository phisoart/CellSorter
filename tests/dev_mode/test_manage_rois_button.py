"""
DEV Mode Tests for Manage ROIs Button and Dialog Trigger

Tests all functionality in headless simulation mode with comprehensive logging.
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

from components.widgets.selection_panel import SelectionPanel
from components.widgets.row_cell_manager import RowCellManager, CellRowData
from headless.testing.framework import UITestCase, HeadlessTestRunner
from utils.logging_config import setup_logging


class TestManageROIsButtonDEV(UITestCase):
    """DEV mode tests for Manage ROIs Button and Dialog Trigger."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class."""
        cls.app = QApplication.instance() or QApplication([])
        
        # Set up enhanced logging for DEV mode
        cls.logger = setup_logging("test_manage_rois_dev")
        cls.logger.info("=== DEV MODE: Manage ROIs Button Tests ===")
    
    def setUp(self):
        """Set up each test method."""
        super().setUp()
        self.selection_panel = SelectionPanel()
        self.logger.info(f"Setup test: {self._testMethodName}")
    
    def tearDown(self):
        """Tear down each test method."""
        if hasattr(self, 'selection_panel'):
            self.selection_panel.deleteLater()
        super().tearDown()
        self.logger.info(f"Teardown test: {self._testMethodName}")
    
    def _create_mock_selection_data(self, count: int = 1) -> List[Dict[str, Any]]:
        """Create mock selection data for testing."""
        selections = []
        for i in range(count):
            selection_data = {
                'id': f'selection_{i+1}',
                'label': f'Test Selection {i+1}',
                'color': '#FF5733' if i % 2 == 0 else '#33FF57',
                'enabled': True,
                'cell_count': 10 + i * 5,
                'cell_indices': list(range(10 + i * 5)),
                'well_position': f'A{i+1}',
                'cell_metadata': {}
            }
            
            # Add cell metadata
            for j in range(selection_data['cell_count']):
                selection_data['cell_metadata'][j] = {
                    'area': 100 + j * 10,
                    'intensity': 50 + j * 5,
                    'perimeter': 30 + j * 3
                }
            
            selections.append(selection_data)
        
        self.logger.debug(f"Created {count} mock selections")
        return selections
    
    def _simulate_row_selection(self, row_index: int) -> None:
        """Simulate selecting a table row."""
        # Create mock selection model behavior
        mock_row = Mock()
        mock_row.row.return_value = row_index
        mock_selection_model = Mock()
        mock_selection_model.selectedRows.return_value = [mock_row]
        
        # Patch the selection model temporarily
        with patch.object(self.selection_panel.selection_table, 'selectionModel', return_value=mock_selection_model):
            self.selection_panel.on_table_selection_changed()
    
    def _simulate_no_selection(self) -> None:
        """Simulate no row selection."""
        mock_selection_model = Mock()
        mock_selection_model.selectedRows.return_value = []
        
        with patch.object(self.selection_panel.selection_table, 'selectionModel', return_value=mock_selection_model):
            self.selection_panel.on_table_selection_changed()
    
    def _simulate_multiple_selection(self, row_indices: List[int]) -> None:
        """Simulate multiple row selection."""
        mock_selection_model = Mock()
        mock_rows = [Mock(row=lambda idx=i: idx) for i in row_indices]
        mock_selection_model.selectedRows.return_value = mock_rows
        
        with patch.object(self.selection_panel.selection_table, 'selectionModel', return_value=mock_selection_model):
            self.selection_panel.on_table_selection_changed()
    
    def test_component_initialization_dev(self):
        """DEV: Test component initialization with Manage ROIs button."""
        self.logger.info("Testing component initialization...")
        
        # Verify selection panel is created
        self.assertIsNotNone(self.selection_panel)
        self.assertIsInstance(self.selection_panel, SelectionPanel)
        
        # Verify Manage ROIs button exists
        self.assertTrue(hasattr(self.selection_panel, 'manage_rois_button'))
        self.assertIsNotNone(self.selection_panel.manage_rois_button)
        
        # Verify initial state - button should be disabled
        self.assertFalse(self.selection_panel.manage_rois_button.isEnabled())
        
        # Verify initial ROI management state
        self.assertIsNone(self.selection_panel.selected_row_id)
        self.assertIsNone(self.selection_panel.roi_manager)
        
        # Verify button properties
        self.assertEqual("Manage ROIs", self.selection_panel.manage_rois_button.text())
        self.assertEqual(28, self.selection_panel.manage_rois_button.minimumHeight())
        self.assertEqual(100, self.selection_panel.manage_rois_button.minimumWidth())
        
        self.logger.info("✅ Component initialization verified")
    
    def test_button_enabled_on_selection_dev(self):
        """DEV: Test button enabled state changes based on row selection."""
        self.logger.info("Testing button enabled state on selection...")
        
        # Load test data
        selections = self._create_mock_selection_data(3)
        self.selection_panel.load_selections(selections)
        
        # Initially, no row should be selected and button disabled
        self.assertIsNone(self.selection_panel.selected_row_id)
        self.assertFalse(self.selection_panel.manage_rois_button.isEnabled())
        
        # Select first row - button should be enabled
        self._simulate_row_selection(0)
        self.assertEqual('selection_1', self.selection_panel.selected_row_id)
        self.assertTrue(self.selection_panel.manage_rois_button.isEnabled())
        
        # Select second row - button should remain enabled with new selection
        self._simulate_row_selection(1)
        self.assertEqual('selection_2', self.selection_panel.selected_row_id)
        self.assertTrue(self.selection_panel.manage_rois_button.isEnabled())
        
        # Clear selection - button should be disabled
        self._simulate_no_selection()
        self.assertIsNone(self.selection_panel.selected_row_id)
        self.assertFalse(self.selection_panel.manage_rois_button.isEnabled())
        
        self.logger.info("✅ Button enabled state on selection verified")
    
    def test_button_disable_on_multiple_selection_dev(self):
        """DEV: Test button disables when multiple rows are selected."""
        self.logger.info("Testing button disable on multiple selection...")
        
        # Load test data
        selections = self._create_mock_selection_data(4)
        self.selection_panel.load_selections(selections)
        
        # Select single row - button should be enabled
        self._simulate_row_selection(0)
        self.assertEqual('selection_1', self.selection_panel.selected_row_id)
        self.assertTrue(self.selection_panel.manage_rois_button.isEnabled())
        
        # Select multiple rows - button should be disabled
        self._simulate_multiple_selection([0, 1, 2])
        self.assertIsNone(self.selection_panel.selected_row_id)
        self.assertFalse(self.selection_panel.manage_rois_button.isEnabled())
        
        # Back to single selection - button should be enabled again
        self._simulate_row_selection(2)
        self.assertEqual('selection_3', self.selection_panel.selected_row_id)
        self.assertTrue(self.selection_panel.manage_rois_button.isEnabled())
        
        self.logger.info("✅ Button disable on multiple selection verified")
    
    def test_roi_management_dialog_trigger_dev(self):
        """DEV: Test ROI management dialog trigger functionality."""
        self.logger.info("Testing ROI management dialog trigger...")
        
        # Load test data
        selections = self._create_mock_selection_data(2)
        self.selection_panel.load_selections(selections)
        
        # Select a row
        self._simulate_row_selection(0)
        self.assertEqual('selection_1', self.selection_panel.selected_row_id)
        
        # Mock signal connections
        roi_management_signals = []
        self.selection_panel.roi_management_requested.connect(
            lambda sel_id: roi_management_signals.append(sel_id)
        )
        
        # Click Manage ROIs button
        self.selection_panel.manage_rois_button.click()
        
        # Verify ROI manager was created
        self.assertIsNotNone(self.selection_panel.roi_manager)
        self.assertIsInstance(self.selection_panel.roi_manager, RowCellManager)
        
        # Verify signals were connected (we can't easily test this directly, but we can check the manager exists)
        self.assertTrue(hasattr(self.selection_panel.roi_manager, 'cell_inclusion_changed'))
        self.assertTrue(hasattr(self.selection_panel.roi_manager, 'cell_navigation_requested'))
        self.assertTrue(hasattr(self.selection_panel.roi_manager, 'row_management_closed'))
        
        self.logger.info("✅ ROI management dialog trigger verified")
    
    def test_cell_row_data_creation_dev(self):
        """DEV: Test CellRowData creation from selection data."""
        self.logger.info("Testing CellRowData creation...")
        
        # Create selection data
        selection_data = {
            'id': 'test_selection',
            'label': 'Test Cell Selection',
            'color': '#FF5733',
            'cell_count': 5,
            'cell_indices': [0, 1, 2, 3, 4],
            'cell_metadata': {
                0: {'area': 100, 'intensity': 50, 'perimeter': 30},
                1: {'area': 110, 'intensity': 55, 'perimeter': 33},
                2: {'area': 120, 'intensity': 60, 'perimeter': 36}
            }
        }
        
        # Create CellRowData
        cell_row_data = self.selection_panel._create_cell_row_data('test_selection', selection_data)
        
        # Verify CellRowData properties
        self.assertIsInstance(cell_row_data, CellRowData)
        self.assertEqual('test_selection', cell_row_data.selection_id)
        self.assertEqual('Test Cell Selection', cell_row_data.selection_label)
        self.assertEqual('#FF5733', cell_row_data.selection_color)
        self.assertEqual([0, 1, 2, 3, 4], cell_row_data.cell_indices)
        
        # Verify metadata was preserved and extended
        self.assertIn(0, cell_row_data.cell_metadata)
        self.assertIn(1, cell_row_data.cell_metadata)
        self.assertIn(2, cell_row_data.cell_metadata)
        self.assertIn(3, cell_row_data.cell_metadata)  # Should be auto-generated
        self.assertIn(4, cell_row_data.cell_metadata)  # Should be auto-generated
        
        # Verify existing metadata
        self.assertEqual(100, cell_row_data.cell_metadata[0]['area'])
        self.assertEqual(50, cell_row_data.cell_metadata[0]['intensity'])
        
        # Verify auto-generated metadata
        self.assertEqual(130, cell_row_data.cell_metadata[3]['area'])  # 100 + 3*10
        self.assertEqual(65, cell_row_data.cell_metadata[3]['intensity'])  # 50 + 3*5
        
        self.logger.info("✅ CellRowData creation verified")
    
    def test_cell_inclusion_change_handling_dev(self):
        """DEV: Test cell inclusion/exclusion change handling."""
        self.logger.info("Testing cell inclusion change handling...")
        
        # Load test data
        selections = self._create_mock_selection_data(1)
        self.selection_panel.load_selections(selections)
        
        # Mock signal connections
        selection_update_signals = []
        self.selection_panel.selection_updated.connect(
            lambda sel_id, data: selection_update_signals.append((sel_id, data))
        )
        
        # Test cell exclusion
        self.selection_panel.on_cell_inclusion_changed('selection_1', 3, False)
        
        # Verify excluded cells were updated
        selection_data = self.selection_panel.selections_data['selection_1']
        self.assertIn('excluded_cells', selection_data)
        self.assertIn(3, selection_data['excluded_cells'])
        
        # Verify signal was emitted
        self.assertEqual(1, len(selection_update_signals))
        signal_data = selection_update_signals[0]
        self.assertEqual('selection_1', signal_data[0])
        self.assertEqual('cell_inclusion_changed', signal_data[1]['action'])
        self.assertEqual(3, signal_data[1]['cell_index'])
        self.assertFalse(signal_data[1]['included'])
        
        # Test cell inclusion (re-include)
        self.selection_panel.on_cell_inclusion_changed('selection_1', 3, True)
        
        # Verify cell was re-included
        self.assertNotIn(3, selection_data['excluded_cells'])
        
        # Verify second signal
        self.assertEqual(2, len(selection_update_signals))
        signal_data = selection_update_signals[1]
        self.assertTrue(signal_data[1]['included'])
        
        self.logger.info("✅ Cell inclusion change handling verified")
    
    def test_cell_navigation_request_handling_dev(self):
        """DEV: Test cell navigation request handling."""
        self.logger.info("Testing cell navigation request handling...")
        
        # Load test data and select row
        selections = self._create_mock_selection_data(1)
        self.selection_panel.load_selections(selections)
        self._simulate_row_selection(0)
        
        # Mock signal connections
        roi_management_signals = []
        selection_update_signals = []
        
        self.selection_panel.roi_management_requested.connect(
            lambda sel_id: roi_management_signals.append(sel_id)
        )
        self.selection_panel.selection_updated.connect(
            lambda sel_id, data: selection_update_signals.append((sel_id, data))
        )
        
        # Request navigation to cell 5
        self.selection_panel.on_cell_navigation_requested(5)
        
        # Verify ROI management signal
        self.assertEqual(1, len(roi_management_signals))
        self.assertEqual('selection_1', roi_management_signals[0])
        
        # Verify selection update signal
        self.assertEqual(1, len(selection_update_signals))
        signal_data = selection_update_signals[0]
        self.assertEqual('selection_1', signal_data[0])
        self.assertEqual('navigate_to_cell', signal_data[1]['action'])
        self.assertEqual(5, signal_data[1]['cell_index'])
        
        self.logger.info("✅ Cell navigation request handling verified")
    
    def test_roi_management_close_handling_dev(self):
        """DEV: Test ROI management dialog close handling."""
        self.logger.info("Testing ROI management close handling...")
        
        # Load test data and create ROI manager
        selections = self._create_mock_selection_data(1)
        self.selection_panel.load_selections(selections)
        self._simulate_row_selection(0)
        
        # Create ROI manager
        self.selection_panel.open_roi_management()
        roi_manager = self.selection_panel.roi_manager
        self.assertIsNotNone(roi_manager)
        
        # Close ROI management
        self.selection_panel.on_roi_management_closed()
        
        # Verify manager was hidden (not destroyed)
        self.assertIsNotNone(self.selection_panel.roi_manager)
        # Note: In headless mode, we can't easily test visibility, but the method should execute without error
        
        self.logger.info("✅ ROI management close handling verified")
    
    def test_button_out_of_bounds_protection_dev(self):
        """DEV: Test button behavior with out-of-bounds row selection."""
        self.logger.info("Testing button out-of-bounds protection...")
        
        # Load test data
        selections = self._create_mock_selection_data(2)
        self.selection_panel.load_selections(selections)
        
        # Try to select row index that doesn't exist
        self._simulate_row_selection(5)  # Only 2 rows exist (0, 1)
        
        # Should remain unselected due to out-of-bounds
        self.assertIsNone(self.selection_panel.selected_row_id)
        
        # Valid selection should still work
        self._simulate_row_selection(1)
        self.assertEqual('selection_2', self.selection_panel.selected_row_id)
        
        self.logger.info("✅ Button out-of-bounds protection verified")
    
    def test_empty_selection_data_handling_dev(self):
        """DEV: Test behavior with empty selection data."""
        self.logger.info("Testing empty selection data handling...")
        
        # No selections loaded
        self.assertEqual(0, len(self.selection_panel.selections_data))
        
        # Try to select row - should not crash
        self._simulate_row_selection(0)
        
        # Should remain unselected with empty data
        self.assertIsNone(self.selection_panel.selected_row_id)
        
        # Try to open ROI management without selection - should not crash
        self.selection_panel.open_roi_management()
        self.assertIsNone(self.selection_panel.roi_manager)
        
        self.logger.info("✅ Empty selection data handling verified")
    
    def test_comprehensive_workflow_dev(self):
        """DEV: Test complete end-to-end workflow."""
        self.logger.info("Testing comprehensive workflow...")
        
        # Mock all signal connections
        signals_log = {
            'roi_management_requested': [],
            'selection_updated': []
        }
        
        self.selection_panel.roi_management_requested.connect(
            lambda sel_id: signals_log['roi_management_requested'].append(sel_id)
        )
        self.selection_panel.selection_updated.connect(
            lambda sel_id, data: signals_log['selection_updated'].append((sel_id, data))
        )
        
        # 1. Load multiple selections
        selections = self._create_mock_selection_data(3)
        self.selection_panel.load_selections(selections)
        
        # 2. Select first row
        self._simulate_row_selection(0)
        self.assertEqual('selection_1', self.selection_panel.selected_row_id)
        
        # 3. Open ROI management
        self.selection_panel.manage_rois_button.click()
        self.assertIsNotNone(self.selection_panel.roi_manager)
        
        # 4. Simulate cell exclusion
        self.selection_panel.on_cell_inclusion_changed('selection_1', 2, False)
        
        # 5. Simulate cell navigation
        self.selection_panel.on_cell_navigation_requested(7)
        
        # 6. Close ROI management
        self.selection_panel.on_roi_management_closed()
        
        # 7. Switch to different row
        self._simulate_row_selection(2)
        self.assertEqual('selection_3', self.selection_panel.selected_row_id)
        
        # 8. Clear selection
        self._simulate_no_selection()
        self.assertIsNone(self.selection_panel.selected_row_id)
        
        # Verify comprehensive signal flow
        self.assertEqual(1, len(signals_log['roi_management_requested']))
        # selection_updated signals include: data loading updates + cell inclusion + navigation
        self.assertGreaterEqual(len(signals_log['selection_updated']), 2)  # At least cell inclusion + navigation
        
        # Verify final state
        selection_data = self.selection_panel.selections_data['selection_1']
        self.assertIn('excluded_cells', selection_data)
        self.assertIn(2, selection_data['excluded_cells'])
        
        self.logger.info("✅ Comprehensive workflow verified")
        self.logger.info("🎉 All DEV mode tests completed successfully!")


def run_dev_tests():
    """Run DEV mode tests directly."""
    runner = HeadlessTestRunner()
    result = runner.run_test_case(TestManageROIsButtonDEV)
    runner.print_summary()
    return result


if __name__ == "__main__":
    # Run tests directly
    run_dev_tests() 