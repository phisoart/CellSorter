"""
DEV Mode Tests for Row Cell Manager

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
from PySide6.QtGui import QPixmap

from components.widgets.row_cell_manager import (
    RowCellManager, 
    CellRowItem, 
    CellRowData
)
from headless.testing.framework import UITestCase, HeadlessTestRunner
from utils.logging_config import setup_logging


class TestRowCellManagerDEV(UITestCase):
    """DEV mode tests for Row Cell Manager."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class."""
        cls.app = QApplication.instance() or QApplication([])
        
        # Set up enhanced logging for DEV mode
        cls.logger = setup_logging("test_row_cell_manager_dev")
        cls.logger.info("=== DEV MODE: Row Cell Manager Tests ===")
    
    def setUp(self):
        """Set up each test method."""
        super().setUp()
        self.manager = RowCellManager()
        self.logger.info(f"Setup test: {self._testMethodName}")
    
    def tearDown(self):
        """Tear down each test method."""
        if hasattr(self, 'manager'):
            self.manager.deleteLater()
        super().tearDown()
        self.logger.info(f"Teardown test: {self._testMethodName}")
    
    def _create_mock_row_data(self, cell_count: int = 5) -> CellRowData:
        """Create mock row data for testing."""
        cell_indices = list(range(cell_count))
        cell_metadata = {}
        
        for i in cell_indices:
            cell_metadata[i] = {
                'area': 100 + i*20,
                'intensity': 50 + i*10,
                'perimeter': 30 + i*5
            }
        
        row_data = CellRowData(
            selection_id="test_selection_1",
            selection_label="Test Selection",
            selection_color="#FF5733",
            cell_indices=cell_indices,
            cell_metadata=cell_metadata
        )
        
        self.logger.debug(f"Created mock row data with {cell_count} cells")
        return row_data
    
    def _simulate_cell_click(self, cell_index: int) -> None:
        """Simulate clicking on a cell item."""
        for item in self.manager.cell_items:
            if item.cell_index == cell_index:
                item.cell_selected.emit(cell_index)
                break
    
    def _simulate_inclusion_toggle(self, cell_index: int) -> None:
        """Simulate toggling cell inclusion."""
        for item in self.manager.cell_items:
            if item.cell_index == cell_index:
                current_state = item.is_included
                new_state = not current_state
                item.inclusion_checkbox.setChecked(new_state)
                break
    
    def test_component_initialization_dev(self):
        """DEV: Test component initialization."""
        self.logger.info("Testing component initialization...")
        
        # Verify component is created
        self.assertIsNotNone(self.manager)
        self.assertIsInstance(self.manager, RowCellManager)
        
        # Verify initial state
        self.assertIsNone(self.manager.current_row_data)
        self.assertEqual(len(self.manager.cell_items), 0)
        self.assertIsNone(self.manager.selected_cell_index)
        
        # Verify UI elements exist
        self.assertTrue(hasattr(self.manager, 'title_label'))
        self.assertTrue(hasattr(self.manager, 'selection_info_label'))
        self.assertTrue(hasattr(self.manager, 'cell_list_widget'))
        self.assertTrue(hasattr(self.manager, 'navigate_button'))
        self.assertTrue(hasattr(self.manager, 'close_button'))
        
        # Verify initial button states
        self.assertFalse(self.manager.navigate_button.isEnabled())
        
        # Verify statistics labels
        self.assertEqual("Total: 0", self.manager.total_cells_label.text())
        self.assertEqual("Included: 0", self.manager.included_cells_label.text())
        self.assertEqual("Excluded: 0", self.manager.excluded_cells_label.text())
        
        self.logger.info("✅ Component initialization verified")
    
    def test_row_data_loading_dev(self):
        """DEV: Test loading row data."""
        self.logger.info("Testing row data loading...")
        
        # Create test data
        row_data = self._create_mock_row_data(8)
        
        # Load row data
        self.manager.load_row_data(row_data)
        
        # Verify data loaded
        self.assertEqual(self.manager.current_row_data, row_data)
        self.assertEqual(len(self.manager.cell_items), 8)
        
        # Verify UI updated
        expected_info = "Selection: Test Selection (8 cells)"
        self.assertEqual(expected_info, self.manager.selection_info_label.text())
        
        # Verify cell items created correctly
        for i, item in enumerate(self.manager.cell_items):
            self.assertIsInstance(item, CellRowItem)
            self.assertEqual(item.cell_index, i)
            self.assertTrue(item.is_included)  # Default state
        
        # Verify statistics updated
        self.assertEqual("Total: 8", self.manager.total_cells_label.text())
        self.assertEqual("Included: 8", self.manager.included_cells_label.text())
        self.assertEqual("Excluded: 0", self.manager.excluded_cells_label.text())
        
        self.logger.info("✅ Row data loading verified")
    
    def test_cell_selection_simulation_dev(self):
        """DEV: Test cell selection simulation."""
        self.logger.info("Testing cell selection simulation...")
        
        # Load test data
        row_data = self._create_mock_row_data(5)
        self.manager.load_row_data(row_data)
        
        # Mock signal connections
        selection_signals = []
        self.manager.cell_navigation_requested.connect(
            lambda idx: selection_signals.append(idx)
        )
        
        # Simulate selecting cell 2
        self._simulate_cell_click(2)
        
        # Verify selection state
        self.assertEqual(self.manager.selected_cell_index, 2)
        
        # Verify visual state
        for item in self.manager.cell_items:
            if item.cell_index == 2:
                self.assertTrue(item._is_selected)
            else:
                self.assertFalse(item._is_selected)
        
        # Verify details panel updated
        self.assertEqual("Cell 2", self.manager.selected_cell_label.text())
        self.assertTrue(self.manager.navigate_button.isEnabled())
        
        # Verify cell properties displayed
        properties_text = self.manager.cell_properties.toPlainText()
        self.assertIn("Cell Index: 2", properties_text)
        self.assertIn("Area: 140", properties_text)  # Integer format from metadata
        self.assertIn("Intensity: 70", properties_text)
        
        self.logger.info("✅ Cell selection simulation verified")
    
    def test_inclusion_toggle_simulation_dev(self):
        """DEV: Test cell inclusion/exclusion simulation."""
        self.logger.info("Testing inclusion toggle simulation...")
        
        # Load test data
        row_data = self._create_mock_row_data(4)
        self.manager.load_row_data(row_data)
        
        # Mock signal connections
        inclusion_signals = []
        self.manager.cell_inclusion_changed.connect(
            lambda sel_id, cell_idx, included: inclusion_signals.append((sel_id, cell_idx, included))
        )
        
        # Initially all cells should be included
        included_count = sum(1 for item in self.manager.cell_items if item.is_included)
        self.assertEqual(included_count, 4)
        
        # Simulate excluding cells 1 and 3
        self._simulate_inclusion_toggle(1)
        self._simulate_inclusion_toggle(3)
        
        # Verify inclusion states changed
        self.assertFalse(self.manager.cell_items[1].is_included)
        self.assertFalse(self.manager.cell_items[3].is_included)
        self.assertTrue(self.manager.cell_items[0].is_included)
        self.assertTrue(self.manager.cell_items[2].is_included)
        
        # Verify signals emitted
        self.assertEqual(len(inclusion_signals), 2)
        self.assertEqual(inclusion_signals[0], ("test_selection_1", 1, False))
        self.assertEqual(inclusion_signals[1], ("test_selection_1", 3, False))
        
        # Verify statistics updated
        self.assertEqual("Total: 4", self.manager.total_cells_label.text())
        self.assertEqual("Included: 2", self.manager.included_cells_label.text())
        self.assertEqual("Excluded: 2", self.manager.excluded_cells_label.text())
        
        self.logger.info("✅ Inclusion toggle simulation verified")
    
    def test_navigation_request_dev(self):
        """DEV: Test navigation request functionality."""
        self.logger.info("Testing navigation request...")
        
        # Load test data
        row_data = self._create_mock_row_data(3)
        self.manager.load_row_data(row_data)
        
        # Mock signal connections
        navigation_signals = []
        self.manager.cell_navigation_requested.connect(
            lambda idx: navigation_signals.append(idx)
        )
        
        # Select a cell
        self._simulate_cell_click(1)
        
        # Click navigate button
        self.manager.navigate_button.click()
        
        # Verify navigation signal
        self.assertEqual(len(navigation_signals), 1)
        self.assertEqual(navigation_signals[0], 1)
        
        self.logger.info("✅ Navigation request verified")
    
    def test_bulk_operations_dev(self):
        """DEV: Test bulk include/exclude operations."""
        self.logger.info("Testing bulk operations...")
        
        # Load test data
        row_data = self._create_mock_row_data(6)
        self.manager.load_row_data(row_data)
        
        # Exclude some cells first
        self._simulate_inclusion_toggle(1)
        self._simulate_inclusion_toggle(3)
        self._simulate_inclusion_toggle(5)
        
        # Verify mixed state
        included_count = sum(1 for item in self.manager.cell_items if item.is_included)
        self.assertEqual(included_count, 3)
        
        # Test "Include All"
        self.manager.select_all_button.click()
        
        # Verify all cells included
        for item in self.manager.cell_items:
            self.assertTrue(item.is_included)
        
        # Verify statistics
        self.assertEqual("Included: 6", self.manager.included_cells_label.text())
        self.assertEqual("Excluded: 0", self.manager.excluded_cells_label.text())
        
        # Test "Exclude All"
        self.manager.exclude_all_button.click()
        
        # Verify all cells excluded
        for item in self.manager.cell_items:
            self.assertFalse(item.is_included)
        
        # Verify statistics
        self.assertEqual("Included: 0", self.manager.included_cells_label.text())
        self.assertEqual("Excluded: 6", self.manager.excluded_cells_label.text())
        
        self.logger.info("✅ Bulk operations verified")
    
    def test_close_functionality_dev(self):
        """DEV: Test close functionality."""
        self.logger.info("Testing close functionality...")
        
        # Load test data
        row_data = self._create_mock_row_data(3)
        self.manager.load_row_data(row_data)
        
        # Mock signal connections
        close_signals = []
        self.manager.row_management_closed.connect(lambda: close_signals.append(True))
        
        # Click close button
        self.manager.close_button.click()
        
        # Verify close signal
        self.assertEqual(len(close_signals), 1)
        
        self.logger.info("✅ Close functionality verified")
    
    def test_cell_item_initialization_dev(self):
        """DEV: Test individual cell item initialization."""
        self.logger.info("Testing cell item initialization...")
        
        # Create test metadata
        metadata = {
            'area': 150.5,
            'intensity': 75.2,
            'perimeter': 45.8
        }
        
        # Create cell item
        cell_item = CellRowItem(cell_index=10, cell_metadata=metadata, is_included=True)
        
        # Verify initialization
        self.assertEqual(cell_item.cell_index, 10)
        self.assertEqual(cell_item.cell_metadata, metadata)
        self.assertTrue(cell_item.is_included)
        self.assertFalse(cell_item._is_selected)
        
        # Verify UI elements
        self.assertTrue(hasattr(cell_item, 'inclusion_checkbox'))
        self.assertTrue(hasattr(cell_item, 'index_label'))
        self.assertTrue(hasattr(cell_item, 'metadata_label'))
        self.assertTrue(hasattr(cell_item, 'thumbnail_label'))
        
        # Verify content
        self.assertEqual("Cell 10", cell_item.index_label.text())
        self.assertIn("Area: 150.5", cell_item.metadata_label.text())
        self.assertIn("Intensity: 75.2", cell_item.metadata_label.text())
        self.assertIn("Perimeter: 45.8", cell_item.metadata_label.text())
        
        # Clean up
        cell_item.deleteLater()
        
        self.logger.info("✅ Cell item initialization verified")
    
    def test_cell_item_thumbnail_dev(self):
        """DEV: Test cell item thumbnail functionality."""
        self.logger.info("Testing cell item thumbnail...")
        
        # Create cell item
        cell_item = CellRowItem(cell_index=5, cell_metadata={}, is_included=True)
        
        # Create test pixmap
        pixmap = QPixmap(100, 100)
        pixmap.fill(Qt.GlobalColor.red)
        
        # Set thumbnail
        cell_item.set_thumbnail(pixmap)
        
        # Verify thumbnail was set (pixmap should be scaled to 60x60)
        thumbnail_pixmap = cell_item.thumbnail_label.pixmap()
        self.assertIsNotNone(thumbnail_pixmap)
        
        # Clean up
        cell_item.deleteLater()
        
        self.logger.info("✅ Cell item thumbnail verified")
    
    def test_empty_row_data_handling_dev(self):
        """DEV: Test handling of empty row data."""
        self.logger.info("Testing empty row data handling...")
        
        # Create empty row data
        empty_row_data = CellRowData(
            selection_id="empty_selection",
            selection_label="Empty Selection",
            selection_color="#000000",
            cell_indices=[],
            cell_metadata={}
        )
        
        # Load empty data
        self.manager.load_row_data(empty_row_data)
        
        # Verify empty state
        self.assertEqual(len(self.manager.cell_items), 0)
        self.assertIsNone(self.manager.selected_cell_index)
        
        # Verify UI reflects empty state
        expected_info = "Selection: Empty Selection (0 cells)"
        self.assertEqual(expected_info, self.manager.selection_info_label.text())
        
        # Verify statistics
        self.assertEqual("Total: 0", self.manager.total_cells_label.text())
        self.assertEqual("Included: 0", self.manager.included_cells_label.text())
        self.assertEqual("Excluded: 0", self.manager.excluded_cells_label.text())
        
        self.logger.info("✅ Empty row data handling verified")
    
    def test_large_dataset_performance_dev(self):
        """DEV: Test performance with large dataset."""
        self.logger.info("Testing large dataset performance...")
        
        # Create large dataset (simulate many cells)
        large_row_data = self._create_mock_row_data(100)
        
        import time
        start_time = time.time()
        self.manager.load_row_data(large_row_data)
        load_time = time.time() - start_time
        
        # Verify all cells loaded
        self.assertEqual(len(self.manager.cell_items), 100)
        
        # Performance should be reasonable (under 5 seconds)
        self.assertLess(load_time, 5.0, f"Loading took too long: {load_time:.2f}s")
        
        # Test bulk operations performance
        start_time = time.time()
        self.manager.exclude_all_button.click()
        bulk_time = time.time() - start_time
        
        # Bulk operations should be fast (under 2 seconds)
        self.assertLess(bulk_time, 2.0, f"Bulk operation took too long: {bulk_time:.2f}s")
        
        # Verify all excluded
        excluded_count = sum(1 for item in self.manager.cell_items if not item.is_included)
        self.assertEqual(excluded_count, 100)
        
        self.logger.info(f"✅ Large dataset performance verified (load: {load_time:.3f}s, bulk: {bulk_time:.3f}s)")
    
    def test_memory_management_dev(self):
        """DEV: Test memory management with widget cleanup."""
        self.logger.info("Testing memory management...")
        
        # Load data multiple times to test cleanup
        for iteration in range(3):
            row_data = self._create_mock_row_data(10)
            self.manager.load_row_data(row_data)
            
            # Verify current state
            self.assertEqual(len(self.manager.cell_items), 10)
            
            # Clear and verify cleanup
            self.manager.clear_cell_items()
            self.assertEqual(len(self.manager.cell_items), 0)
            self.assertIsNone(self.manager.selected_cell_index)
        
        self.logger.info("✅ Memory management verified")
    
    def test_comprehensive_workflow_dev(self):
        """DEV: Test complete end-to-end workflow."""
        self.logger.info("Testing comprehensive workflow...")
        
        # Mock all signal connections
        signals_log = {
            'cell_inclusion_changed': [],
            'cell_navigation_requested': [],
            'row_management_closed': []
        }
        
        self.manager.cell_inclusion_changed.connect(
            lambda sel_id, cell_idx, included: signals_log['cell_inclusion_changed'].append((sel_id, cell_idx, included))
        )
        self.manager.cell_navigation_requested.connect(
            lambda idx: signals_log['cell_navigation_requested'].append(idx)
        )
        self.manager.row_management_closed.connect(
            lambda: signals_log['row_management_closed'].append(True)
        )
        
        # 1. Load row data
        row_data = self._create_mock_row_data(6)
        self.manager.load_row_data(row_data)
        
        # 2. Select some cells
        self._simulate_cell_click(2)
        self._simulate_cell_click(4)
        
        # 3. Toggle inclusion for some cells
        self._simulate_inclusion_toggle(1)
        self._simulate_inclusion_toggle(3)
        
        # 4. Navigate to selected cell
        self.manager.navigate_button.click()
        
        # 5. Use bulk operations
        self.manager.select_all_button.click()
        
        # 6. Close manager
        self.manager.close_button.click()
        
        # Verify complete workflow
        self.assertEqual(len(signals_log['cell_inclusion_changed']), 2 + 2)  # 2 toggles + 2 from select all
        self.assertEqual(len(signals_log['cell_navigation_requested']), 1)
        self.assertEqual(len(signals_log['row_management_closed']), 1)
        
        # Verify final state - all cells should be included after select all
        included_count = sum(1 for item in self.manager.cell_items if item.is_included)
        self.assertEqual(included_count, 6)
        
        self.logger.info("✅ Comprehensive workflow verified")
        self.logger.info("🎉 All DEV mode tests completed successfully!")


def run_dev_tests():
    """Run DEV mode tests directly."""
    runner = HeadlessTestRunner()
    result = runner.run_test_case(TestRowCellManagerDEV)
    runner.print_summary()
    return result


if __name__ == "__main__":
    # Run tests directly
    run_dev_tests() 