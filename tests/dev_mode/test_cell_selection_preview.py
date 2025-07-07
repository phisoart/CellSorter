"""
DEV Mode Tests for Cell Selection Preview Component

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

from components.widgets.cell_selection_preview import (
    CellSelectionPreview, 
    CellThumbnailWidget, 
    CellThumbnailData
)
from headless.testing.framework import UITestCase, HeadlessTestRunner
from utils.logging_config import setup_logging


class TestCellSelectionPreviewDEV(UITestCase):
    """DEV mode tests for Cell Selection Preview Component."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class."""
        cls.app = QApplication.instance() or QApplication([])
        
        # Set up enhanced logging for DEV mode
        cls.logger = setup_logging("test_cell_preview_dev")
        cls.logger.info("=== DEV MODE: Cell Selection Preview Tests ===")
    
    def setUp(self):
        """Set up each test method."""
        super().setUp()
        self.preview = CellSelectionPreview()
        self.logger.info(f"Setup test: {self._testMethodName}")
    
    def tearDown(self):
        """Tear down each test method."""
        if hasattr(self, 'preview'):
            self.preview.deleteLater()
        super().tearDown()
        self.logger.info(f"Teardown test: {self._testMethodName}")
    
    def _create_mock_cell_data(self, count: int = 5) -> List[CellThumbnailData]:
        """Create mock cell data for testing."""
        cell_data = []
        for i in range(count):
            # Create mock pixmap
            pixmap = QPixmap(100, 100)
            pixmap.fill(Qt.GlobalColor.blue)
            
            data = CellThumbnailData(
                cell_index=i,
                thumbnail_pixmap=pixmap,
                bounding_box=(i*10, i*10, i*10+50, i*10+50),
                is_included=True,
                metadata={'area': 100 + i*10, 'intensity': 50 + i*5}
            )
            cell_data.append(data)
        
        self.logger.debug(f"Created {count} mock cell data entries")
        return cell_data
    
    def _simulate_click(self, widget) -> None:
        """Simulate click on widget by calling click handler directly."""
        if hasattr(widget, 'cell_data'):
            # For thumbnail widgets, emit the clicked signal directly
            widget.clicked.emit(widget.cell_data.cell_index)
    
    def _simulate_double_click(self, widget) -> None:
        """Simulate double-click on widget by toggling inclusion directly."""
        if hasattr(widget, 'cell_data'):
            # Toggle inclusion state and emit signal
            widget.cell_data.is_included = not widget.cell_data.is_included
            widget.inclusion_changed.emit(widget.cell_data.cell_index, widget.cell_data.is_included)
            widget.update_appearance()
    
    def test_component_initialization_dev(self):
        """DEV: Test component initialization and UI setup."""
        self.logger.info("Testing component initialization...")
        
        # Verify component is created
        self.assertIsNotNone(self.preview)
        self.assertIsInstance(self.preview, CellSelectionPreview)
        
        # Verify initial state
        self.assertEqual(len(self.preview.cell_thumbnails), 0)
        self.assertEqual(len(self.preview.thumbnail_widgets), 0)
        self.assertIsNone(self.preview.selected_cell_index)
        
        # Verify UI elements exist
        self.assertTrue(hasattr(self.preview, 'title_label'))
        self.assertTrue(hasattr(self.preview, 'subtitle_label'))
        self.assertTrue(hasattr(self.preview, 'grid_container'))
        self.assertTrue(hasattr(self.preview, 'confirm_button'))
        self.assertTrue(hasattr(self.preview, 'cancel_button'))
        
        # Verify initial button states (confirm should be disabled when no cells)
        # Note: Update statistics to ensure button state is correct
        self.preview.update_statistics()
        self.assertFalse(self.preview.confirm_button.isEnabled())
        
        self.logger.info("✅ Component initialization verified")
    
    def test_cell_loading_dev(self):
        """DEV: Test loading cells into preview."""
        self.logger.info("Testing cell loading...")
        
        # Create test data
        cell_data = self._create_mock_cell_data(10)
        
        # Simulate loading cells
        self.preview.load_cells(cell_data)
        
        # Verify cells loaded
        self.assertEqual(len(self.preview.cell_thumbnails), 10)
        self.assertEqual(len(self.preview.thumbnail_widgets), 10)
        
        # Verify thumbnail widgets created
        for i, widget in enumerate(self.preview.thumbnail_widgets):
            self.assertIsInstance(widget, CellThumbnailWidget)
            self.assertEqual(widget.cell_data.cell_index, i)
            self.assertTrue(widget.cell_data.is_included)
        
        # Verify grid layout
        self.assertEqual(self.preview.grid_layout.count(), 10)
        
        # Verify statistics updated
        stats_text = self.preview.total_cells_label.text()
        self.assertIn("10", stats_text)
        
        self.logger.info("✅ Cell loading verified")
    
    def test_thumbnail_interaction_simulation_dev(self):
        """DEV: Test thumbnail click simulation."""
        self.logger.info("Testing thumbnail interaction simulation...")
        
        # Load test data
        cell_data = self._create_mock_cell_data(5)
        self.preview.load_cells(cell_data)
        
        # Mock signal connections
        cell_clicked_signals = []
        self.preview.cell_clicked.connect(lambda idx: cell_clicked_signals.append(idx))
        
        # Simulate clicking first thumbnail
        first_widget = self.preview.thumbnail_widgets[0]
        
        # Simulate click
        self._simulate_click(first_widget)
        
        # Verify click was handled
        self.assertEqual(len(cell_clicked_signals), 1)
        self.assertEqual(cell_clicked_signals[0], 0)
        self.assertEqual(self.preview.selected_cell_index, 0)
        
        # Verify visual state update
        self.assertTrue(first_widget._is_selected)
        
        self.logger.info("✅ Thumbnail interaction simulation verified")
    
    def test_inclusion_toggle_simulation_dev(self):
        """DEV: Test cell inclusion/exclusion simulation."""
        self.logger.info("Testing inclusion toggle simulation...")
        
        # Load test data
        cell_data = self._create_mock_cell_data(3)
        self.preview.load_cells(cell_data)
        
        # Get first thumbnail widget
        first_widget = self.preview.thumbnail_widgets[0]
        initial_inclusion = first_widget.cell_data.is_included
        
        # Simulate double-click to toggle inclusion
        self._simulate_double_click(first_widget)
        
        # Verify inclusion toggled
        self.assertNotEqual(first_widget.cell_data.is_included, initial_inclusion)
        
        # Verify statistics updated
        included_count = sum(1 for cell in self.preview.cell_thumbnails if cell.is_included)
        included_text = self.preview.included_cells_label.text()
        self.assertIn(str(included_count), included_text)
        
        self.logger.info("✅ Inclusion toggle simulation verified")
    
    def test_statistics_calculation_dev(self):
        """DEV: Test statistics calculation and display."""
        self.logger.info("Testing statistics calculation...")
        
        # Load test data with mixed inclusion states
        cell_data = self._create_mock_cell_data(8)
        # Set some cells as excluded
        cell_data[2].is_included = False
        cell_data[5].is_included = False
        cell_data[7].is_included = False
        
        self.preview.load_cells(cell_data)
        
        # Verify statistics
        total_count = len(self.preview.cell_thumbnails)
        included_count = sum(1 for cell in self.preview.cell_thumbnails if cell.is_included)
        excluded_count = total_count - included_count
        
        self.assertEqual(total_count, 8)
        self.assertEqual(included_count, 5)
        self.assertEqual(excluded_count, 3)
        
        # Verify UI displays correct statistics
        self.assertEqual(f"Total: {total_count}", self.preview.total_cells_label.text())
        self.assertEqual(f"Included: {included_count}", self.preview.included_cells_label.text())
        self.assertEqual(f"Excluded: {excluded_count}", self.preview.excluded_cells_label.text())
        
        # Verify confirm button state
        self.assertEqual(self.preview.confirm_button.isEnabled(), included_count > 0)
        
        self.logger.info("✅ Statistics calculation verified")
    
    def test_confirmation_workflow_dev(self):
        """DEV: Test confirmation workflow simulation."""
        self.logger.info("Testing confirmation workflow...")
        
        # Load test data
        cell_data = self._create_mock_cell_data(4)
        cell_data[1].is_included = False  # Exclude one cell
        self.preview.load_cells(cell_data)
        
        # Mock signal connections
        confirmed_signals = []
        cancelled_signals = []
        closed_signals = []
        
        self.preview.selection_confirmed.connect(lambda indices: confirmed_signals.append(indices))
        self.preview.selection_cancelled.connect(lambda: cancelled_signals.append(True))
        self.preview.preview_closed.connect(lambda: closed_signals.append(True))
        
        # Test confirmation
        self.preview.confirm_button.click()
        
        # Verify confirmation signal
        self.assertEqual(len(confirmed_signals), 1)
        self.assertEqual(len(confirmed_signals[0]), 3)  # Only included cells
        self.assertNotIn(1, confirmed_signals[0])  # Excluded cell not included
        self.assertEqual(len(closed_signals), 1)
        
        self.logger.info("✅ Confirmation workflow verified")
    
    def test_cancellation_workflow_dev(self):
        """DEV: Test cancellation workflow simulation."""
        self.logger.info("Testing cancellation workflow...")
        
        # Load test data
        cell_data = self._create_mock_cell_data(3)
        self.preview.load_cells(cell_data)
        
        # Mock signal connections
        cancelled_signals = []
        closed_signals = []
        
        self.preview.selection_cancelled.connect(lambda: cancelled_signals.append(True))
        self.preview.preview_closed.connect(lambda: closed_signals.append(True))
        
        # Test cancellation
        self.preview.cancel_button.click()
        
        # Verify cancellation signals
        self.assertEqual(len(cancelled_signals), 1)
        self.assertEqual(len(closed_signals), 1)
        
        self.logger.info("✅ Cancellation workflow verified")
    
    def test_large_dataset_performance_dev(self):
        """DEV: Test performance with large dataset."""
        self.logger.info("Testing large dataset performance...")
        
        # Test with maximum allowed thumbnails
        large_cell_data = self._create_mock_cell_data(50)  # Max limit
        
        import time
        start_time = time.time()
        self.preview.load_cells(large_cell_data)
        load_time = time.time() - start_time
        
        # Verify all cells loaded
        self.assertEqual(len(self.preview.cell_thumbnails), 50)
        self.assertEqual(len(self.preview.thumbnail_widgets), 50)
        
        # Performance should be reasonable (under 5 seconds for component creation)
        self.assertLess(load_time, 5.0, f"Loading took too long: {load_time:.2f}s")
        
        self.logger.info(f"✅ Large dataset performance verified (load time: {load_time:.3f}s)")
    
    def test_exceeded_limit_handling_dev(self):
        """DEV: Test handling of datasets exceeding limits."""
        self.logger.info("Testing exceeded limit handling...")
        
        # Test with more than maximum allowed thumbnails
        oversized_data = self._create_mock_cell_data(75)  # Over 50 limit
        
        with patch.object(self.preview, 'log_warning') as mock_warning:
            self.preview.load_cells(oversized_data)
            
            # Verify warning was logged
            mock_warning.assert_called_once()
            self.assertIn("Too many cells", str(mock_warning.call_args))
        
        # Verify only max allowed cells were loaded
        self.assertEqual(len(self.preview.cell_thumbnails), self.preview.max_thumbnails)
        self.assertEqual(len(self.preview.thumbnail_widgets), self.preview.max_thumbnails)
        
        self.logger.info("✅ Exceeded limit handling verified")
    
    def test_empty_dataset_handling_dev(self):
        """DEV: Test handling of empty datasets."""
        self.logger.info("Testing empty dataset handling...")
        
        # Load empty dataset
        self.preview.load_cells([])
        
        # Verify empty state
        self.assertEqual(len(self.preview.cell_thumbnails), 0)
        self.assertEqual(len(self.preview.thumbnail_widgets), 0)
        self.assertEqual(self.preview.grid_layout.count(), 0)
        
        # Verify statistics
        self.assertEqual("Total: 0", self.preview.total_cells_label.text())
        self.assertEqual("Included: 0", self.preview.included_cells_label.text())
        self.assertEqual("Excluded: 0", self.preview.excluded_cells_label.text())
        
        # Verify confirm button disabled
        self.assertFalse(self.preview.confirm_button.isEnabled())
        
        self.logger.info("✅ Empty dataset handling verified")
    
    def test_memory_management_dev(self):
        """DEV: Test memory management with widget cleanup."""
        self.logger.info("Testing memory management...")
        
        # Load data multiple times to test cleanup
        for iteration in range(3):
            cell_data = self._create_mock_cell_data(10)
            self.preview.load_cells(cell_data)
            
            # Verify current state
            self.assertEqual(len(self.preview.cell_thumbnails), 10)
            self.assertEqual(len(self.preview.thumbnail_widgets), 10)
            
            # Clear and verify cleanup
            self.preview.clear_thumbnails()
            self.assertEqual(len(self.preview.cell_thumbnails), 0)
            self.assertEqual(len(self.preview.thumbnail_widgets), 0)
            self.assertEqual(self.preview.grid_layout.count(), 0)
        
        self.logger.info("✅ Memory management verified")
    
    def test_comprehensive_workflow_dev(self):
        """DEV: Test complete end-to-end workflow."""
        self.logger.info("Testing comprehensive workflow...")
        
        # Mock all signal connections
        signals_log = {
            'cell_clicked': [],
            'selection_confirmed': [],
            'selection_cancelled': [],
            'preview_closed': []
        }
        
        self.preview.cell_clicked.connect(lambda idx: signals_log['cell_clicked'].append(idx))
        self.preview.selection_confirmed.connect(lambda indices: signals_log['selection_confirmed'].append(indices))
        self.preview.selection_cancelled.connect(lambda: signals_log['selection_cancelled'].append(True))
        self.preview.preview_closed.connect(lambda: signals_log['preview_closed'].append(True))
        
        # 1. Load cells
        cell_data = self._create_mock_cell_data(6)
        self.preview.load_cells(cell_data)
        
        # 2. Interact with thumbnails
        self._simulate_click(self.preview.thumbnail_widgets[0])
        self._simulate_click(self.preview.thumbnail_widgets[2])
        
        # 3. Toggle some inclusions
        self._simulate_double_click(self.preview.thumbnail_widgets[1])
        self._simulate_double_click(self.preview.thumbnail_widgets[4])
        
        # 4. Confirm selection
        self.preview.confirm_button.click()
        
        # Verify complete workflow
        self.assertEqual(len(signals_log['cell_clicked']), 2)  # Two clicks
        self.assertEqual(len(signals_log['selection_confirmed']), 1)
        self.assertEqual(len(signals_log['preview_closed']), 1)
        
        # Verify only included cells in confirmation
        confirmed_indices = signals_log['selection_confirmed'][0]
        self.assertEqual(len(confirmed_indices), 4)  # 6 total - 2 excluded
        self.assertNotIn(1, confirmed_indices)  # Excluded
        self.assertNotIn(4, confirmed_indices)  # Excluded
        
        self.logger.info("✅ Comprehensive workflow verified")
        self.logger.info("🎉 All DEV mode tests completed successfully!")


def run_dev_tests():
    """Run DEV mode tests directly."""
    runner = HeadlessTestRunner()
    result = runner.run_test_case(TestCellSelectionPreviewDEV)
    runner.print_summary()
    return result


if __name__ == "__main__":
    # Run tests directly
    run_dev_tests() 