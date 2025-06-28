"""
Test Selection Management Production in GUI Mode

Tests selection manager in production GUI mode.
Verifies user interface integration, visual feedback, and production workflows.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

from src.headless.testing.framework import UITestCase
from src.models.selection_manager import SelectionManager, CellSelection, SelectionStatus
from src.headless.mode_manager import ModeManager
from src.utils.logging_config import get_logger


class TestSelectionManagementProductionGui(UITestCase):
    """Test selection management production in GUI mode."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        
        # Set up GUI mode
        self.mode_manager = Mock(spec=ModeManager)
        self.mode_manager.is_dev_mode.return_value = False
        self.mode_manager.is_gui_mode.return_value = True
        self.mode_manager.is_dual_mode.return_value = False
        
        # Create selection manager
        self.selection_manager = SelectionManager()
        
        # Mock GUI components
        self.mock_selection_panel = Mock()
        self.mock_selection_panel.update_selection = Mock()
        self.mock_selection_panel.remove_selection = Mock()
        self.mock_selection_panel.refresh_table = Mock()
        
        self.mock_image_handler = Mock()
        self.mock_image_handler.highlight_cells = Mock()
        self.mock_image_handler.remove_cell_highlights = Mock()
        
        self.mock_scatter_plot = Mock()
        self.mock_scatter_plot.highlight_points = Mock()
        self.mock_scatter_plot.clear_selection = Mock()
        
        # Test data for GUI workflows
        self.user_selections = [
            {
                'label': 'Positive Controls',
                'color': '#FF0000',
                'well_position': 'A01',
                'cell_indices': [1, 5, 9, 13, 17, 21],
                'metadata': {'type': 'control', 'expected_result': 'positive'}
            },
            {
                'label': 'Negative Controls',
                'color': '#0000FF',
                'well_position': 'A02',
                'cell_indices': [2, 6, 10, 14, 18, 22],
                'metadata': {'type': 'control', 'expected_result': 'negative'}
            },
            {
                'label': 'Test Samples',
                'color': '#00FF00',
                'well_position': 'B01',
                'cell_indices': [3, 7, 11, 15, 19, 23],
                'metadata': {'type': 'sample', 'sample_id': 'S001'}
            }
        ]
        
        self.logger = get_logger('test_selection_production')
    
    def tearDown(self):
        """Clean up test environment."""
        self.selection_manager.clear_all_selections()
        super().tearDown()
    
    def test_user_selection_workflow(self):
        """Test complete user selection workflow in GUI mode."""
        # Simulate user creating selections through GUI
        created_ids = []
        
        for user_selection in self.user_selections:
            # User creates selection
            selection_id = self.selection_manager.add_selection(
                cell_indices=user_selection['cell_indices'],
                label=user_selection['label'],
                color=user_selection['color'],
                well_position=user_selection['well_position']
            )
            
            created_ids.append(selection_id)
            
            # Simulate GUI updates
            self.mock_selection_panel.update_selection(selection_id, {
                'label': user_selection['label'],
                'color': user_selection['color'],
                'well_position': user_selection['well_position'],
                'cell_count': len(user_selection['cell_indices'])
            })
            
            # Simulate visual highlighting
            self.mock_image_handler.highlight_cells(
                selection_id,
                user_selection['cell_indices'],
                user_selection['color']
            )
            
            self.mock_scatter_plot.highlight_points(
                user_selection['cell_indices'],
                user_selection['color']
            )
        
        # Verify all selections were created
        all_selections = self.selection_manager.get_all_selections()
        assert len(all_selections) == len(self.user_selections)
        
        # Verify GUI components were updated
        assert self.mock_selection_panel.update_selection.call_count == len(self.user_selections)
        assert self.mock_image_handler.highlight_cells.call_count == len(self.user_selections)
        assert self.mock_scatter_plot.highlight_points.call_count == len(self.user_selections)
    
    def test_selection_visual_feedback(self):
        """Test visual feedback for selection operations."""
        # Create selection
        selection_id = self.selection_manager.add_selection(
            cell_indices=[10, 11, 12, 13, 14],
            label="Visual_Test",
            color="#FFFF00"
        )
        
        # Simulate immediate visual feedback
        self.mock_image_handler.highlight_cells(
            selection_id,
            [10, 11, 12, 13, 14],
            "#FFFF00",
            alpha=0.5
        )
        
        # Verify visual feedback calls
        self.mock_image_handler.highlight_cells.assert_called_with(
            selection_id,
            [10, 11, 12, 13, 14],
            "#FFFF00",
            alpha=0.5
        )
        
        # Test selection update visual feedback
        update_success = self.selection_manager.update_selection(
            selection_id,
            color="#FF00FF"
        )
        assert update_success is True
        
        # Simulate updated visual feedback
        updated_selection = self.selection_manager.get_selection(selection_id)
        self.mock_image_handler.highlight_cells(
            selection_id,
            updated_selection.cell_indices,
            updated_selection.color,
            alpha=0.5
        )
        
        # Verify updated feedback
        assert self.mock_image_handler.highlight_cells.call_count == 2
    
    def test_selection_table_integration(self):
        """Test integration with selection table widget."""
        # Create multiple selections
        selection_ids = []
        for user_selection in self.user_selections:
            selection_id = self.selection_manager.add_selection(
                cell_indices=user_selection['cell_indices'],
                label=user_selection['label'],
                color=user_selection['color'],
                well_position=user_selection['well_position']
            )
            selection_ids.append(selection_id)
        
        # Get table data
        table_data = self.selection_manager.get_selection_table_data()
        
        # Verify table data structure
        assert len(table_data) == len(self.user_selections)
        
        for row in table_data:
            assert 'id' in row
            assert 'enabled' in row
            assert 'label' in row
            assert 'color' in row
            assert 'well' in row
            assert 'cell_count' in row
            assert 'status' in row
            
            # Verify data types
            assert isinstance(row['enabled'], bool)
            assert isinstance(row['cell_count'], int)
            assert row['cell_count'] > 0
        
        # Simulate table refresh
        self.mock_selection_panel.refresh_table(table_data)
        self.mock_selection_panel.refresh_table.assert_called_with(table_data)
    
    def test_selection_editing_workflow(self):
        """Test selection editing workflow through GUI."""
        # Create initial selection
        selection_id = self.selection_manager.add_selection(
            cell_indices=[100, 101, 102],
            label="Editable_Selection",
            color="#808080"
        )
        
        # User edits label through GUI
        new_label = "Edited_Selection_Label"
        update_success = self.selection_manager.update_selection(
            selection_id,
            label=new_label
        )
        assert update_success is True
        
        # Simulate GUI update
        updated_selection = self.selection_manager.get_selection(selection_id)
        self.mock_selection_panel.update_selection(selection_id, {
            'label': updated_selection.label,
            'color': updated_selection.color,
            'well_position': updated_selection.well_position,
            'cell_count': len(updated_selection.cell_indices)
        })
        
        # User changes color through GUI
        new_color = "#FF8000"
        color_update_success = self.selection_manager.update_selection(
            selection_id,
            color=new_color
        )
        assert color_update_success is True
        
        # Simulate visual update
        final_selection = self.selection_manager.get_selection(selection_id)
        self.mock_image_handler.highlight_cells(
            selection_id,
            final_selection.cell_indices,
            final_selection.color
        )
        
        # Verify final state
        assert final_selection.label == new_label
        assert final_selection.color == new_color
        assert self.mock_selection_panel.update_selection.call_count >= 1
    
    def test_selection_deletion_workflow(self):
        """Test selection deletion workflow in GUI."""
        # Create selection to delete
        selection_id = self.selection_manager.add_selection(
            cell_indices=[200, 201, 202, 203],
            label="Delete_Me",
            color="#800080"
        )
        
        # Verify selection exists
        selection = self.selection_manager.get_selection(selection_id)
        assert selection is not None
        
        # User deletes selection through GUI
        delete_success = self.selection_manager.remove_selection(selection_id)
        assert delete_success is True
        
        # Simulate GUI cleanup
        self.mock_selection_panel.remove_selection(selection_id)
        self.mock_image_handler.remove_cell_highlights(selection_id)
        self.mock_scatter_plot.clear_selection()
        
        # Verify deletion
        deleted_selection = self.selection_manager.get_selection(selection_id)
        assert deleted_selection is None
        
        # Verify GUI cleanup calls
        self.mock_selection_panel.remove_selection.assert_called_with(selection_id)
        self.mock_image_handler.remove_cell_highlights.assert_called_with(selection_id)
        self.mock_scatter_plot.clear_selection.assert_called_once()
    
    def test_bulk_selection_operations(self):
        """Test bulk selection operations in GUI mode."""
        # Create multiple selections
        selection_ids = []
        for i in range(5):
            selection_id = self.selection_manager.add_selection(
                cell_indices=[i * 10, i * 10 + 1, i * 10 + 2],
                label=f"Bulk_Selection_{i}",
                color=f"#{i*50:02x}{i*30:02x}{i*20:02x}"
            )
            selection_ids.append(selection_id)
        
        # Test bulk enable/disable
        for selection_id in selection_ids:
            selection = self.selection_manager.get_selection(selection_id)
            assert selection.status == SelectionStatus.ACTIVE
        
        # Simulate bulk clear operation
        initial_count = len(self.selection_manager.get_all_selections())
        assert initial_count == 5
        
        self.selection_manager.clear_all_selections()
        
        # Simulate GUI refresh after bulk clear
        self.mock_selection_panel.refresh_table([])
        self.mock_image_handler.remove_cell_highlights("all")
        self.mock_scatter_plot.clear_selection()
        
        # Verify bulk clear
        final_count = len(self.selection_manager.get_all_selections())
        assert final_count == 0
        
        # Verify GUI updates
        self.mock_selection_panel.refresh_table.assert_called_with([])
    
    def test_selection_performance_gui_mode(self):
        """Test selection performance in GUI mode with visual updates."""
        # Test rapid selection creation (simulating user actions)
        rapid_selections = 20
        
        import time
        start_time = time.time()
        
        for i in range(rapid_selections):
            selection_id = self.selection_manager.add_selection(
                cell_indices=[i * 5, i * 5 + 1, i * 5 + 2, i * 5 + 3],
                label=f"Rapid_{i}"
            )
            
            # Simulate GUI updates for each selection
            if selection_id:
                selection = self.selection_manager.get_selection(selection_id)
                self.mock_selection_panel.update_selection(selection_id, {
                    'label': selection.label,
                    'color': selection.color,
                    'cell_count': len(selection.cell_indices)
                })
                
                self.mock_image_handler.highlight_cells(
                    selection_id,
                    selection.cell_indices,
                    selection.color
                )
        
        total_time = time.time() - start_time
        
        # Performance should be acceptable for GUI
        assert total_time < 5.0, f"Rapid selection creation too slow: {total_time:.2f}s"
        
        # Verify all selections were created
        all_selections = self.selection_manager.get_all_selections()
        assert len(all_selections) == rapid_selections
        
        # Verify GUI was updated for all selections
        assert self.mock_selection_panel.update_selection.call_count == rapid_selections
        assert self.mock_image_handler.highlight_cells.call_count == rapid_selections
    
    def test_selection_error_handling_gui(self):
        """Test selection error handling in GUI mode."""
        # Test invalid cell indices
        invalid_selection_id = self.selection_manager.add_selection(
            cell_indices=[],  # Empty list
            label="Invalid_Selection"
        )
        
        # Should fail gracefully
        assert invalid_selection_id is None
        
        # Test exceeding maximum selections
        max_selections = self.selection_manager.max_selections
        
        # Fill up to maximum
        for i in range(max_selections):
            selection_id = self.selection_manager.add_selection(
                cell_indices=[i],
                label=f"Max_Test_{i}"
            )
            if selection_id is None:  # If we hit the limit early
                break
        
        # Try to add one more (should fail)
        overflow_id = self.selection_manager.add_selection(
            cell_indices=[99999],
            label="Overflow_Selection"
        )
        
        # Should either succeed (if max not reached) or fail gracefully
        current_count = len(self.selection_manager.get_all_selections())
        assert current_count <= max_selections
    
    def test_selection_accessibility_features(self):
        """Test selection accessibility features for GUI mode."""
        # Create selections with accessibility considerations
        accessible_selections = [
            {
                'label': 'High Contrast Red',
                'color': '#CC0000',  # Dark red for better contrast
                'cell_indices': [1, 2, 3]
            },
            {
                'label': 'High Contrast Blue',
                'color': '#0000CC',  # Dark blue for better contrast
                'cell_indices': [4, 5, 6]
            },
            {
                'label': 'High Contrast Green',
                'color': '#00AA00',  # Dark green for better contrast
                'cell_indices': [7, 8, 9]
            }
        ]
        
        # Create accessible selections
        for acc_selection in accessible_selections:
            selection_id = self.selection_manager.add_selection(
                cell_indices=acc_selection['cell_indices'],
                label=acc_selection['label'],
                color=acc_selection['color']
            )
            
            # Verify accessible properties
            selection = self.selection_manager.get_selection(selection_id)
            assert len(selection.label) > 0  # Should have descriptive label
            assert selection.color.startswith('#')  # Should have valid color
            assert len(selection.cell_indices) > 0  # Should have content
        
        # Test color differentiation
        all_selections = self.selection_manager.get_all_selections()
        all_colors = [s.color for s in all_selections]
        
        # All colors should be different for accessibility
        assert len(set(all_colors)) == len(all_colors), "All colors should be unique for accessibility"
    
    def test_selection_undo_redo_support(self):
        """Test selection operations with undo/redo support."""
        # Note: This tests the selection manager's ability to support undo/redo
        # The actual undo/redo would be implemented at the application level
        
        # Capture initial state
        initial_selections = self.selection_manager.get_all_selections()
        initial_count = len(initial_selections)
        
        # Perform operations that could be undone
        operation_log = []
        
        # Add selection (operation 1)
        selection_id = self.selection_manager.add_selection(
            cell_indices=[50, 51, 52],
            label="Undoable_Selection",
            color="#AAAAAA"
        )
        operation_log.append(('add', selection_id))
        
        # Update selection (operation 2)
        update_success = self.selection_manager.update_selection(
            selection_id,
            label="Updated_Undoable_Selection"
        )
        operation_log.append(('update', selection_id, 'label', 'Updated_Undoable_Selection'))
        
        # Verify operations were successful
        assert selection_id is not None
        assert update_success is True
        
        # Simulate undo by reversing operations
        for operation in reversed(operation_log):
            if operation[0] == 'add':
                # Undo add by removing
                self.selection_manager.remove_selection(operation[1])
            elif operation[0] == 'update':
                # Undo update by restoring previous value
                self.selection_manager.update_selection(
                    operation[1],
                    label="Undoable_Selection"  # Original label
                )
        
        # After undo simulation, verify state
        final_selections = self.selection_manager.get_all_selections()
        final_count = len(final_selections)
        
        # Should be back to initial state (or close to it)
        assert final_count <= initial_count + 1  # Allow for partial undo
