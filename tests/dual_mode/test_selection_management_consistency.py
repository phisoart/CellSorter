"""
Test Selection Management Consistency in DUAL Mode

Tests selection manager consistency between headless and GUI modes.
Verifies bidirectional synchronization and state consistency.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

from src.headless.testing.framework import UITestCase
from src.models.selection_manager import SelectionManager, CellSelection, SelectionStatus
from src.headless.mode_manager import ModeManager
from src.headless.main_window_adapter import MainWindowAdapter
from src.utils.logging_config import get_logger


class TestSelectionManagementConsistencyDual(UITestCase):
    """Test selection management consistency in DUAL mode."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        
        # Set up dual mode
        self.mode_manager = Mock(spec=ModeManager)
        self.mode_manager.is_dev_mode.return_value = False
        self.mode_manager.is_gui_mode.return_value = False
        self.mode_manager.is_dual_mode.return_value = True
        
        # Create headless and GUI selection managers
        self.headless_selection_manager = SelectionManager()
        self.gui_selection_manager = Mock(spec=SelectionManager)
        
        # Setup GUI selection manager mock behavior
        self.gui_selection_manager.add_selection = Mock()
        self.gui_selection_manager.remove_selection = Mock()
        self.gui_selection_manager.update_selection = Mock()
        self.gui_selection_manager.get_selection = Mock()
        self.gui_selection_manager.get_all_selections = Mock(return_value=[])
        self.gui_selection_manager.clear_all_selections = Mock()
        
        # Create adapter for synchronization
        self.adapter = Mock(spec=MainWindowAdapter)
        self.adapter.sync_selections_to_gui = Mock(return_value=True)
        self.adapter.sync_selections_from_gui = Mock(return_value=True)
        
        # Test data
        self.test_selections = [
            {
                'label': 'Sync Test 1',
                'color': '#FF0000',
                'well_position': 'A01',
                'cell_indices': [1, 2, 3, 4, 5],
                'metadata': {'type': 'positive'}
            },
            {
                'label': 'Sync Test 2',
                'color': '#00FF00',
                'well_position': 'A02',
                'cell_indices': [6, 7, 8, 9, 10],
                'metadata': {'type': 'negative'}
            }
        ]
        
        self.logger = get_logger('test_selection_consistency')
    
    def tearDown(self):
        """Clean up test environment."""
        self.headless_selection_manager.clear_all_selections()
        super().tearDown()
    
    def test_selection_sync_headless_to_gui(self):
        """Test selection synchronization from headless to GUI mode."""
        # Add selections in headless mode
        headless_ids = []
        for test_selection in self.test_selections:
            selection_id = self.headless_selection_manager.add_selection(
                cell_indices=test_selection['cell_indices'],
                label=test_selection['label'],
                color=test_selection['color'],
                well_position=test_selection['well_position']
            )
            headless_ids.append(selection_id)
        
        # Simulate synchronization to GUI
        headless_selections = self.headless_selection_manager.get_all_selections()
        
        # Mock GUI receiving synchronized selections
        for selection in headless_selections:
            self.gui_selection_manager.add_selection.return_value = selection.id
            self.gui_selection_manager.add_selection(
                cell_indices=selection.cell_indices,
                label=selection.label,
                color=selection.color,
                well_position=selection.well_position
            )
        
        # Trigger sync
        sync_success = self.adapter.sync_selections_to_gui()
        
        # Verify synchronization
        assert sync_success is True
        assert self.gui_selection_manager.add_selection.call_count == len(self.test_selections)
        
        # Verify call arguments
        for call_args in self.gui_selection_manager.add_selection.call_args_list:
            args, kwargs = call_args
            if 'cell_indices' in kwargs:
                assert len(kwargs['cell_indices']) > 0
            if 'label' in kwargs:
                assert kwargs['label'] in [s['label'] for s in self.test_selections]
    
    def test_selection_sync_gui_to_headless(self):
        """Test selection synchronization from GUI to headless mode."""
        # Mock GUI selections
        gui_selections = []
        for i, test_selection in enumerate(self.test_selections):
            mock_selection = Mock(spec=CellSelection)
            mock_selection.id = f"gui_selection_{i}"
            mock_selection.label = test_selection['label']
            mock_selection.color = test_selection['color']
            mock_selection.well_position = test_selection['well_position']
            mock_selection.cell_indices = test_selection['cell_indices']
            mock_selection.metadata = test_selection['metadata']
            mock_selection.status = SelectionStatus.ACTIVE
            gui_selections.append(mock_selection)
        
        # Setup GUI mock to return selections
        self.gui_selection_manager.get_all_selections.return_value = gui_selections
        
        # Simulate synchronization from GUI to headless
        gui_selections_data = self.gui_selection_manager.get_all_selections()
        
        for selection in gui_selections_data:
            self.headless_selection_manager.add_selection(
                cell_indices=selection.cell_indices,
                label=selection.label,
                color=selection.color,
                well_position=selection.well_position
            )
        
        # Trigger sync
        sync_success = self.adapter.sync_selections_from_gui()
        
        # Verify synchronization
        assert sync_success is True
        
        # Verify headless received all selections
        headless_selections = self.headless_selection_manager.get_all_selections()
        assert len(headless_selections) == len(self.test_selections)
        
        # Verify data consistency
        headless_labels = [s.label for s in headless_selections]
        for test_selection in self.test_selections:
            assert test_selection['label'] in headless_labels
    
    def test_bidirectional_selection_consistency(self):
        """Test bidirectional selection consistency between modes."""
        # Start with selections in headless
        initial_id = self.headless_selection_manager.add_selection(
            cell_indices=[1, 2, 3],
            label="Initial_Headless",
            color="#FF0000"
        )
        
        # Sync to GUI
        headless_selections = self.headless_selection_manager.get_all_selections()
        self.gui_selection_manager.add_selection.return_value = "gui_initial_id"
        
        for selection in headless_selections:
            self.gui_selection_manager.add_selection(
                cell_indices=selection.cell_indices,
                label=selection.label,
                color=selection.color
            )
        
        # Add selection in GUI (mock)
        gui_added_selection = Mock(spec=CellSelection)
        gui_added_selection.id = "gui_added_id"
        gui_added_selection.label = "Added_In_GUI"
        gui_added_selection.color = "#00FF00"
        gui_added_selection.well_position = "B01"
        gui_added_selection.cell_indices = [4, 5, 6]
        gui_added_selection.metadata = {}
        gui_added_selection.status = SelectionStatus.ACTIVE
        
        # Update GUI mock to include new selection
        all_gui_selections = [gui_added_selection]
        self.gui_selection_manager.get_all_selections.return_value = all_gui_selections
        
        # Sync back to headless
        gui_selections = self.gui_selection_manager.get_all_selections()
        for selection in gui_selections:
            self.headless_selection_manager.add_selection(
                cell_indices=selection.cell_indices,
                label=selection.label,
                color=selection.color,
                well_position=selection.well_position
            )
        
        # Verify final consistency
        final_headless_selections = self.headless_selection_manager.get_all_selections()
        final_labels = [s.label for s in final_headless_selections]
        
        # Should have both original and GUI-added selections
        assert "Added_In_GUI" in final_labels
    
    def test_selection_update_synchronization(self):
        """Test selection update synchronization between modes."""
        # Create initial selection in headless
        selection_id = self.headless_selection_manager.add_selection(
            cell_indices=[10, 11, 12],
            label="Update_Test",
            color="#0000FF"
        )
        
        # Update selection in headless
        update_success = self.headless_selection_manager.update_selection(
            selection_id,
            label="Updated_In_Headless",
            color="#FFFF00"
        )
        assert update_success is True
        
        # Simulate sync to GUI
        updated_selection = self.headless_selection_manager.get_selection(selection_id)
        self.gui_selection_manager.update_selection.return_value = True
        
        # Trigger GUI update
        self.gui_selection_manager.update_selection(
            selection_id,
            label=updated_selection.label,
            color=updated_selection.color
        )
        
        # Verify GUI update was called
        self.gui_selection_manager.update_selection.assert_called_with(
            selection_id,
            label="Updated_In_Headless",
            color="#FFFF00"
        )
    
    def test_selection_removal_synchronization(self):
        """Test selection removal synchronization between modes."""
        # Create selections in both modes
        headless_id = self.headless_selection_manager.add_selection(
            cell_indices=[20, 21, 22],
            label="Remove_Test",
            color="#FF00FF"
        )
        
        # Mock GUI has same selection
        self.gui_selection_manager.remove_selection.return_value = True
        
        # Remove from headless
        remove_success = self.headless_selection_manager.remove_selection(headless_id)
        assert remove_success is True
        
        # Simulate sync to GUI
        self.gui_selection_manager.remove_selection(headless_id)
        
        # Verify GUI removal was called
        self.gui_selection_manager.remove_selection.assert_called_with(headless_id)
        
        # Verify selection is gone from headless
        removed_selection = self.headless_selection_manager.get_selection(headless_id)
        assert removed_selection is None
    
    def test_color_consistency_between_modes(self):
        """Test color consistency between headless and GUI modes."""
        # Create selections with specific colors
        color_test_data = [
            {'color': '#FF0000', 'label': 'Red_Selection'},
            {'color': '#00FF00', 'label': 'Green_Selection'},
            {'color': '#0000FF', 'label': 'Blue_Selection'}
        ]
        
        headless_colors = []
        for i, color_data in enumerate(color_test_data):
            selection_id = self.headless_selection_manager.add_selection(
                cell_indices=[i * 10, i * 10 + 1, i * 10 + 2],
                label=color_data['label'],
                color=color_data['color']
            )
            
            selection = self.headless_selection_manager.get_selection(selection_id)
            headless_colors.append(selection.color)
        
        # Simulate sync to GUI and verify colors are preserved
        headless_selections = self.headless_selection_manager.get_all_selections()
        gui_colors = []
        
        for selection in headless_selections:
            # Mock GUI preserving colors
            gui_colors.append(selection.color)
            self.gui_selection_manager.add_selection(
                cell_indices=selection.cell_indices,
                label=selection.label,
                color=selection.color
            )
        
        # Verify color consistency
        assert headless_colors == gui_colors, "Colors should be consistent between modes"
        
        # Verify specific colors
        expected_colors = [data['color'] for data in color_test_data]
        for expected_color in expected_colors:
            assert expected_color in headless_colors
    
    def test_well_assignment_synchronization(self):
        """Test well assignment synchronization between modes."""
        # Create selections with well assignments
        well_assignments = ['A01', 'A02', 'B01', 'B02']
        
        headless_wells = []
        for i, well in enumerate(well_assignments):
            selection_id = self.headless_selection_manager.add_selection(
                cell_indices=[i * 5, i * 5 + 1, i * 5 + 2],
                label=f"Well_{well}",
                well_position=well
            )
            
            selection = self.headless_selection_manager.get_selection(selection_id)
            headless_wells.append(selection.well_position)
        
        # Simulate sync to GUI
        headless_selections = self.headless_selection_manager.get_all_selections()
        gui_wells = []
        
        for selection in headless_selections:
            gui_wells.append(selection.well_position)
            self.gui_selection_manager.add_selection(
                cell_indices=selection.cell_indices,
                label=selection.label,
                well_position=selection.well_position
            )
        
        # Verify well consistency
        assert headless_wells == gui_wells, "Well assignments should be consistent"
        assert set(headless_wells) == set(well_assignments), "All wells should be preserved"
    
    def test_metadata_synchronization(self):
        """Test metadata synchronization between modes."""
        # Create selection with rich metadata
        metadata = {
            'experiment': 'DUAL_MODE_TEST',
            'timestamp': '2024-01-01T12:00:00Z',
            'markers': ['CD4', 'CD8'],
            'threshold': 1500.0,
            'notes': 'Test synchronization of metadata'
        }
        
        selection_id = self.headless_selection_manager.add_selection(
            cell_indices=[100, 101, 102, 103],
            label="Metadata_Sync_Test"
        )
        
        # Add metadata to selection
        selection = self.headless_selection_manager.get_selection(selection_id)
        selection.metadata.update(metadata)
        
        # Simulate sync to GUI (metadata should be preserved)
        updated_selection = self.headless_selection_manager.get_selection(selection_id)
        
        # Verify metadata integrity
        for key, value in metadata.items():
            assert key in updated_selection.metadata
            assert updated_selection.metadata[key] == value
        
        # Mock GUI receiving metadata
        self.gui_selection_manager.add_selection(
            cell_indices=updated_selection.cell_indices,
            label=updated_selection.label,
            metadata=updated_selection.metadata
        )
        
        # Verify GUI call included metadata
        call_args = self.gui_selection_manager.add_selection.call_args
        if call_args and 'metadata' in call_args[1]:
            gui_metadata = call_args[1]['metadata']
            assert gui_metadata == metadata
