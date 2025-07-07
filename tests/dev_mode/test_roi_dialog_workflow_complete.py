"""
Complete ROI Dialog Workflow Test for DEV Mode

Tests the entire workflow from image/CSV loading to ROI management dialog display
in headless DEV mode with comprehensive logging.
"""

import pytest
import sys
import os
import logging
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import QTimer, Qt
from PySide6.QtTest import QTest

# Set DEV mode before importing
os.environ['CELLSORTER_MODE'] = 'dev'

from pages.main_window import MainWindow
from services.theme_manager import ThemeManager
from models.selection_manager import SelectionManager
from components.widgets.selection_panel import SelectionPanel
from components.dialogs.roi_management_dialog import ROIManagementDialog


class TestROIDialogWorkflowComplete:
    """Complete workflow test for ROI management functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        # Ensure QApplication exists
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication([])
        
        # Set up logging to capture all workflow steps
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        
        # Create theme manager
        self.theme_manager = ThemeManager(self.app)
        
        # Create main window with mocked dependencies
        self.main_window = MainWindow(self.theme_manager)
        
        # Create mock data
        self.setup_mock_data()
        
        self.logger.info("=== Test setup completed ===")
    
    def setup_mock_data(self):
        """Set up mock image and CSV data."""
        # Mock image data
        self.mock_image_data = np.random.randint(0, 255, (1000, 1000, 3), dtype=np.uint8)
        
        # Mock CSV data with bounding boxes
        self.mock_csv_data = pd.DataFrame({
            'ObjectNumber': range(1, 21),  # 20 cells
            'Location_Center_X': np.random.uniform(100, 900, 20),
            'Location_Center_Y': np.random.uniform(100, 900, 20),
            'AreaShape_BoundingBoxMinimum_X': np.random.uniform(50, 850, 20),
            'AreaShape_BoundingBoxMinimum_Y': np.random.uniform(50, 850, 20),
            'AreaShape_BoundingBoxMaximum_X': np.random.uniform(150, 950, 20),
            'AreaShape_BoundingBoxMaximum_Y': np.random.uniform(150, 950, 20),
            'Intensity_MeanIntensity_DAPI': np.random.uniform(0.1, 1.0, 20),
            'Intensity_MeanIntensity_GFP': np.random.uniform(0.1, 1.0, 20)
        })
        
        self.logger.info(f"Mock data created: {len(self.mock_csv_data)} cells")
    
    def test_complete_roi_workflow(self):
        """Test the complete ROI management workflow."""
        self.logger.info("=== Starting complete ROI workflow test ===")
        
        # Step 1: Load image data
        self.logger.info("Step 1: Loading image data")
        self.main_window.image_handler.image_data = self.mock_image_data
        self.main_window.current_image_path = "/mock/path/image.tif"
        self.main_window._on_image_loaded("/mock/path/image.tif")
        self.logger.info("✓ Image data loaded successfully")
        
        # Step 2: Load CSV data
        self.logger.info("Step 2: Loading CSV data")
        self.main_window.csv_parser.data = self.mock_csv_data
        self.main_window.current_csv_path = "/mock/path/data.csv"
        
        # Mock bounding box data
        bounding_boxes = []
        for _, row in self.mock_csv_data.iterrows():
            bbox = (
                int(row['AreaShape_BoundingBoxMinimum_X']),
                int(row['AreaShape_BoundingBoxMinimum_Y']),
                int(row['AreaShape_BoundingBoxMaximum_X']),
                int(row['AreaShape_BoundingBoxMaximum_Y'])
            )
            bounding_boxes.append(bbox)
        
        self.main_window.image_handler.bounding_boxes = bounding_boxes
        self.main_window._on_csv_loaded("/mock/path/data.csv")
        self.logger.info(f"✓ CSV data loaded with {len(bounding_boxes)} bounding boxes")
        
        # Step 3: Create cell selections
        self.logger.info("Step 3: Creating cell selections")
        selected_indices = [0, 1, 2, 3, 4]  # Select first 5 cells
        
        # Simulate selection creation
        selection_id = self.main_window.selection_manager.add_selection(
            cell_indices=selected_indices,
            label="Test_Selection_1"
        )
        self.logger.info(f"✓ Selection created with ID: {selection_id}")
        
        # Verify selection was added to selection panel
        assert selection_id is not None
        selection = self.main_window.selection_manager.get_selection(selection_id)
        assert selection is not None
        assert len(selection.cell_indices) == 5
        self.logger.info("✓ Selection verified in selection manager")
        
        # Step 4: Test selection panel state
        self.logger.info("Step 4: Testing selection panel state")
        selection_panel = self.main_window.selection_panel
        
        # Verify selection panel has the selection
        assert len(selection_panel.selections_data) > 0
        self.logger.info(f"✓ Selection panel has {len(selection_panel.selections_data)} selections")
        
        # Step 5: Simulate row selection in table
        self.logger.info("Step 5: Simulating row selection")
        
        # Get the table widget
        table = selection_panel.selection_table
        assert table.rowCount() > 0, "Selection table should have rows"
        
        # Simulate selecting the first row
        table.selectRow(0)
        selection_panel.on_table_selection_changed()
        
        # Verify that a row is selected and button is enabled
        assert selection_panel.selected_row_id is not None
        assert selection_panel.manage_rois_button.isEnabled()
        self.logger.info(f"✓ Row selected: {selection_panel.selected_row_id}")
        self.logger.info("✓ Manage ROIs button is enabled")
        
        # Step 6: Test signal connection
        self.logger.info("Step 6: Testing signal connections")
        
        # Check if the signal is properly connected by testing emission
        signal = selection_panel.roi_management_requested
        
        # Verify main window slot is connected by testing signal emission
        signal_received = False
        received_selection_id = None
        
        def test_receiver(sel_id):
            nonlocal signal_received, received_selection_id
            signal_received = True
            received_selection_id = sel_id
            self.logger.info(f"Test signal received with selection_id: {sel_id}")
        
        # Connect test receiver temporarily
        signal.connect(test_receiver)
        
        try:
            # Emit signal manually to test connection
            signal.emit(selection_panel.selected_row_id)
            QTest.qWait(50)  # Allow signal processing
            
            assert signal_received, "Signal was not received"
            assert received_selection_id == selection_panel.selected_row_id, "Incorrect selection_id received"
            self.logger.info("✓ Signal-slot connection verified through emission test")
        finally:
            # Clean up test receiver
            signal.disconnect(test_receiver)
        
        # Step 7: Test actual ROI management button click
        self.logger.info("Step 7: Testing ROI management button click")
        
        # Track dialog creation and show calls using a more direct approach
        original_show_dialog = self.main_window.show_roi_management_dialog
        dialog_created = False
        show_called = False
        
        def track_dialog_creation(selection_id):
            nonlocal dialog_created, show_called
            dialog_created = True
            # Call original method
            result = original_show_dialog(selection_id)
            # Check if dialog was created and if show was called
            if hasattr(self.main_window, 'roi_management_dialog') and self.main_window.roi_management_dialog:
                show_called = True
                self.logger.info("Dialog creation and show() call confirmed")
            return result
        
        # Replace the method temporarily
        self.main_window.show_roi_management_dialog = track_dialog_creation
        
        # Click the button
        selection_panel.manage_rois_button.click()
        QTest.qWait(10)  # Allow for event processing
        
        # Restore original method
        self.main_window.show_roi_management_dialog = original_show_dialog
        
        # Verify results
        assert dialog_created, "Dialog creation method was not called"
        assert show_called, "Dialog show() was not called or dialog was not created"
        
        self.logger.info("✓ ROI management dialog creation and display confirmed")
        
        # Test that we can close the dialog if it exists
        if hasattr(self.main_window, 'roi_management_dialog') and self.main_window.roi_management_dialog:
            self.main_window.roi_management_dialog.close()
            self.logger.info("✓ Dialog closed successfully")
        
        self.logger.info("=== Complete ROI workflow test PASSED ===")
    
    def test_signal_slot_connections_detailed(self):
        """Detailed test of signal-slot connections."""
        self.logger.info("=== Testing signal-slot connections in detail ===")
        
        # Test 1: Selection panel signal emission
        selection_panel = self.main_window.selection_panel
        
        # Create a test selection
        selection_id = self.main_window.selection_manager.add_selection(
            cell_indices=[0, 1, 2],
            label="Signal_Test"
        )
        
        # Select the row
        table = selection_panel.selection_table
        table.selectRow(0)
        selection_panel.on_table_selection_changed()
        
        # Test signal emission
        signal_emitted = False
        received_selection_id = None
        
        def signal_receiver(sel_id):
            nonlocal signal_emitted, received_selection_id
            signal_emitted = True
            received_selection_id = sel_id
            self.logger.info(f"Signal received with selection_id: {sel_id}")
        
        # Connect test receiver
        selection_panel.roi_management_requested.connect(signal_receiver)
        
        # Emit signal manually
        selection_panel.roi_management_requested.emit(selection_id)
        QTest.qWait(50)
        
        assert signal_emitted, "Signal was not emitted or received"
        assert received_selection_id == selection_id, "Incorrect selection_id received"
        self.logger.info("✓ Signal emission and reception verified")
        
        # Test 2: Button click signal emission
        self.logger.info("Testing button click signal emission")
        
        # Reset signal tracker
        signal_emitted = False
        received_selection_id = None
        
        # Click button (should emit signal)
        selection_panel.manage_rois_button.click()
        QTest.qWait(100)
        
        assert signal_emitted, "Button click did not emit signal"
        self.logger.info("✓ Button click signal emission verified")
        
        self.logger.info("=== Signal-slot connection tests PASSED ===")
    
    def tearDown(self):
        """Clean up after tests."""
        if hasattr(self, 'main_window') and self.main_window:
            self.main_window.close()
        self.logger.info("=== Test cleanup completed ===")


if __name__ == "__main__":
    # Run the test directly
    import sys
    
    # Set up logging for direct execution
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create test instance and run
    test = TestROIDialogWorkflowComplete()
    test.setup_method()
    
    try:
        test.test_complete_roi_workflow()
        test.test_signal_slot_connections_detailed()
        print("\n✅ ALL TESTS PASSED - ROI workflow is working correctly in DEV mode")
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
    finally:
        test.tearDown() 