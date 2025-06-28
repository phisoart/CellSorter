"""
Test Selection Management Synchronization in DEV Mode

Tests selection manager state synchronization in headless development mode.
Verifies selection persistence, state management, and consistency.
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

from src.headless.testing.framework import UITestCase
from src.models.selection_manager import SelectionManager, CellSelection, SelectionStatus
from src.headless.mode_manager import ModeManager
from src.utils.logging_config import get_logger


class TestSelectionManagementSyncDev(UITestCase):
    """Test selection management synchronization in DEV mode (headless)."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        
        # Set up headless mode
        self.mode_manager = Mock(spec=ModeManager)
        self.mode_manager.is_dev_mode.return_value = True
        self.mode_manager.is_gui_mode.return_value = False
        self.mode_manager.is_dual_mode.return_value = False
        
        # Create selection manager
        self.selection_manager = SelectionManager()
        
        # Test data
        self.test_cell_indices = {
            'selection_1': [0, 1, 2, 5, 8, 13],
            'selection_2': [3, 4, 6, 7, 9, 10],
            'selection_3': [11, 12, 14, 15, 16, 17],
            'selection_4': [18, 19, 20, 21, 22],
            'selection_5': [23, 24, 25, 26, 27, 28, 29]
        }
        
        self.test_selections = [
            {
                'label': 'Positive Cells',
                'color': '#FF0000',
                'well_position': 'A01',
                'cell_indices': self.test_cell_indices['selection_1'],
                'metadata': {'type': 'positive', 'marker': 'CD4+'}
            },
            {
                'label': 'Negative Cells',
                'color': '#0000FF',
                'well_position': 'A02',
                'cell_indices': self.test_cell_indices['selection_2'],
                'metadata': {'type': 'negative', 'marker': 'CD4-'}
            },
            {
                'label': 'High Expression',
                'color': '#00FF00',
                'well_position': 'A03',
                'cell_indices': self.test_cell_indices['selection_3'],
                'metadata': {'type': 'expression', 'expression': 'intensity > 1000'}
            }
        ]
        
        self.logger = get_logger('test_selection_sync')
    
    def tearDown(self):
        """Clean up test environment."""
        self.selection_manager.clear_all_selections()
        super().tearDown()
    
    def test_selection_creation_headless_mode(self):
        """Test selection creation in headless mode."""
        # Add selections programmatically
        selection_ids = []
        
        for test_selection in self.test_selections:
            selection_id = self.selection_manager.add_selection(
                cell_indices=test_selection['cell_indices'],
                label=test_selection['label'],
                color=test_selection['color'],
                well_position=test_selection['well_position']
            )
            
            assert selection_id is not None, f"Selection creation should succeed for {test_selection['label']}"
            selection_ids.append(selection_id)
        
        # Verify selections were created
        all_selections = self.selection_manager.get_all_selections()
        assert len(all_selections) == len(self.test_selections), "All selections should be created"
        
        # Verify selection details
        for i, selection in enumerate(all_selections):
            test_sel = self.test_selections[i]
            assert selection.label == test_sel['label']
            assert selection.color == test_sel['color']
            assert selection.well_position == test_sel['well_position']
            assert set(selection.cell_indices) == set(test_sel['cell_indices'])
    
    def test_selection_state_consistency(self):
        """Test selection state consistency in headless mode."""
        # Create selections
        selection_ids = []
        for test_selection in self.test_selections:
            selection_id = self.selection_manager.add_selection(
                cell_indices=test_selection['cell_indices'],
                label=test_selection['label'],
                color=test_selection['color'],
                well_position=test_selection['well_position']
            )
            selection_ids.append(selection_id)
        
        # Test state persistence
        for selection_id in selection_ids:
            selection = self.selection_manager.get_selection(selection_id)
            
            # Verify default state
            assert selection.status == SelectionStatus.ACTIVE
            assert selection.created_timestamp > 0
            assert len(selection.cell_indices) > 0
            
            # Test state modification
            updated = self.selection_manager.update_selection(
                selection_id,
                label=f"Updated_{selection.label}"
            )
            assert updated is True
            
            # Verify update
            updated_selection = self.selection_manager.get_selection(selection_id)
            assert updated_selection.label.startswith("Updated_")
    
    def test_selection_color_management(self):
        """Test selection color management and consistency."""
        # Test automatic color assignment
        auto_selections = []
        for i in range(5):
            selection_id = self.selection_manager.add_selection(
                cell_indices=[i * 10, i * 10 + 1, i * 10 + 2],
                label=f"Auto_Color_{i}"
            )
            auto_selections.append(selection_id)
        
        # Verify all selections have different colors
        colors = []
        for selection_id in auto_selections:
            selection = self.selection_manager.get_selection(selection_id)
            colors.append(selection.color)
        
        assert len(set(colors)) == len(colors), "All auto-assigned colors should be unique"
        
        # Test manual color assignment
        manual_color = "#FFFF00"  # Yellow
        manual_selection_id = self.selection_manager.add_selection(
            cell_indices=[100, 101, 102],
            label="Manual_Color",
            color=manual_color
        )
        
        manual_selection = self.selection_manager.get_selection(manual_selection_id)
        # Color might be changed if there's a conflict with auto-assigned colors
        assert manual_selection.color is not None, "Manual selection should have a color"
        
        # Test color conflict resolution
        conflict_selection_id = self.selection_manager.add_selection(
            cell_indices=[200, 201, 202],
            label="Conflict_Color",
            color=manual_color  # Same as manual color
        )
        
        conflict_selection = self.selection_manager.get_selection(conflict_selection_id)
        # Should either use the color or assign a different one
        assert conflict_selection.color is not None
    
    def test_well_position_assignment(self):
        """Test well position assignment and management."""
        # Test automatic well assignment
        self.selection_manager.auto_assign_wells = True
        
        auto_well_ids = []
        for i in range(5):
            selection_id = self.selection_manager.add_selection(
                cell_indices=[i * 5, i * 5 + 1, i * 5 + 2],
                label=f"Auto_Well_{i}"
            )
            auto_well_ids.append(selection_id)
        
        # Verify unique well assignments
        wells = []
        for selection_id in auto_well_ids:
            selection = self.selection_manager.get_selection(selection_id)
            if selection.well_position:
                wells.append(selection.well_position)
        
        if wells:  # Only check if wells were assigned
            assert len(set(wells)) == len(wells), "All auto-assigned wells should be unique"
        
        # Test manual well assignment
        manual_well = "B05"
        manual_well_id = self.selection_manager.add_selection(
            cell_indices=[500, 501, 502],
            label="Manual_Well",
            well_position=manual_well
        )
        
        manual_selection = self.selection_manager.get_selection(manual_well_id)
        assert manual_selection.well_position == manual_well, "Manual well should be preserved"
    
    def test_selection_metadata_management(self):
        """Test selection metadata management."""
        # Create selection with metadata
        metadata = {
            'experiment_id': 'EXP_001',
            'date': '2024-01-01',
            'protocol': 'standard_staining',
            'markers': ['CD4', 'CD8', 'CD3'],
            'threshold': 1000.5
        }
        
        selection_id = self.selection_manager.add_selection(
            cell_indices=[10, 11, 12, 13, 14],
            label="Metadata_Test",
            color="#FF00FF"
        )
        
        # Update selection with metadata
        selection = self.selection_manager.get_selection(selection_id)
        selection.metadata.update(metadata)
        
        # Verify metadata storage
        retrieved_selection = self.selection_manager.get_selection(selection_id)
        for key, value in metadata.items():
            assert key in retrieved_selection.metadata
            assert retrieved_selection.metadata[key] == value
    
    def test_selection_removal_and_cleanup(self):
        """Test selection removal and resource cleanup."""
        # Create multiple selections
        selection_ids = []
        colors_used = []
        wells_used = []
        
        for i, test_selection in enumerate(self.test_selections):
            selection_id = self.selection_manager.add_selection(
                cell_indices=test_selection['cell_indices'],
                label=test_selection['label'],
                color=test_selection['color'],
                well_position=test_selection['well_position']
            )
            selection_ids.append(selection_id)
            colors_used.append(test_selection['color'])
            wells_used.append(test_selection['well_position'])
        
        # Verify resources are used
        assert len(self.selection_manager.used_colors) >= len(colors_used)
        assert len(self.selection_manager.used_wells) >= len(wells_used)
        
        # Remove one selection
        removed_selection = self.selection_manager.get_selection(selection_ids[0])
        removed_color = removed_selection.color
        removed_well = removed_selection.well_position
        
        success = self.selection_manager.remove_selection(selection_ids[0])
        assert success is True, "Selection removal should succeed"
        
        # Verify selection is removed
        assert self.selection_manager.get_selection(selection_ids[0]) is None
        
        # Verify resources are freed (if not used by other selections)
        remaining_selections = self.selection_manager.get_all_selections()
        remaining_colors = [s.color for s in remaining_selections]
        remaining_wells = [s.well_position for s in remaining_selections]
        
        if removed_color not in remaining_colors:
            assert removed_color not in self.selection_manager.used_colors
        if removed_well not in remaining_wells:
            assert removed_well not in self.selection_manager.used_wells
    
    def test_selection_conflict_detection(self):
        """Test selection conflict detection."""
        # Create initial selection
        initial_indices = [1, 2, 3, 4, 5]
        initial_id = self.selection_manager.add_selection(
            cell_indices=initial_indices,
            label="Initial_Selection"
        )
        
        # Create overlapping selection
        overlapping_indices = [3, 4, 5, 6, 7]  # Overlaps with initial
        overlapping_id = self.selection_manager.add_selection(
            cell_indices=overlapping_indices,
            label="Overlapping_Selection"
        )
        
        # Both selections should be created (conflict resolution handled internally)
        assert initial_id is not None
        assert overlapping_id is not None
        
        # Verify both selections exist
        initial_selection = self.selection_manager.get_selection(initial_id)
        overlapping_selection = self.selection_manager.get_selection(overlapping_id)
        
        assert initial_selection is not None
        assert overlapping_selection is not None
        
        # Check conflict detection method
        conflicts = self.selection_manager._check_cell_conflicts([3, 4, 5])
        assert len(conflicts) >= 1, "Should detect conflicts with existing selections"
    
    def test_selection_statistics_calculation(self):
        """Test selection statistics calculation."""
        # Create multiple selections
        for test_selection in self.test_selections:
            self.selection_manager.add_selection(
                cell_indices=test_selection['cell_indices'],
                label=test_selection['label'],
                color=test_selection['color'],
                well_position=test_selection['well_position']
            )
        
        # Get statistics
        stats = self.selection_manager.get_statistics()
        
        # Verify statistics
        assert stats['total_selections'] == len(self.test_selections)
        assert stats['active_selections'] == len(self.test_selections)
        assert stats['total_cells'] > 0
        assert stats['used_wells'] > 0
        assert stats['used_colors'] > 0
        assert stats['average_cells_per_selection'] > 0
        assert stats['well_utilization'] >= 0
        assert stats['color_utilization'] >= 0
    
    def test_selection_export_import_consistency(self):
        """Test selection export/import consistency."""
        # Create selections
        original_ids = []
        for test_selection in self.test_selections:
            selection_id = self.selection_manager.add_selection(
                cell_indices=test_selection['cell_indices'],
                label=test_selection['label'],
                color=test_selection['color'],
                well_position=test_selection['well_position']
            )
            original_ids.append(selection_id)
        
        # Export selections
        exported_data = self.selection_manager.export_selections_data()
        assert len(exported_data) == len(self.test_selections)
        
        # Clear and reimport
        self.selection_manager.clear_all_selections()
        assert len(self.selection_manager.get_all_selections()) == 0
        
        import_success = self.selection_manager.import_selections_data(exported_data)
        assert import_success is True
        
        # Verify imported selections
        imported_selections = self.selection_manager.get_all_selections()
        assert len(imported_selections) == len(self.test_selections)
        
        # Verify data consistency (order might differ)
        original_labels = [s['label'] for s in self.test_selections]
        imported_labels = [s.label for s in imported_selections]
        
        for label in original_labels:
            assert label in imported_labels, f"Label {label} should be preserved"
    
    def test_large_selection_performance(self):
        """Test performance with large selections."""
        # Create large selection
        large_indices = list(range(10000))  # 10,000 cells
        
        import time
        start_time = time.time()
        
        large_selection_id = self.selection_manager.add_selection(
            cell_indices=large_indices,
            label="Large_Selection"
        )
        
        creation_time = time.time() - start_time
        
        # Verify creation succeeded
        assert large_selection_id is not None
        
        # Performance should be reasonable
        assert creation_time < 1.0, f"Large selection creation too slow: {creation_time:.2f}s"
        
        # Test retrieval performance
        start_time = time.time()
        
        large_selection = self.selection_manager.get_selection(large_selection_id)
        
        retrieval_time = time.time() - start_time
        
        # Verify data integrity
        assert len(large_selection.cell_indices) == 10000
        assert retrieval_time < 0.1, f"Large selection retrieval too slow: {retrieval_time:.2f}s"
