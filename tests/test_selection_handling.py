"""
Test Selection Handling Fix

Tests to verify that expression-based selections do not create duplicate entries
and that selection types are properly handled.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock

from src.pages.main_window import MainWindow
from src.services.theme_manager import ThemeManager
from src.models.selection_manager import SelectionManager


class TestSelectionHandling:
    """Test cases for selection handling bug fix."""
    
    @pytest.fixture
    def main_window(self):
        """Create main window instance for testing."""
        theme_manager = Mock(spec=ThemeManager)
        theme_manager.apply_theme = Mock()
        theme_manager.get_current_theme = Mock(return_value="light")
        
        # Mock QSettings to avoid file system operations
        with patch('src.pages.main_window.QSettings'):
            window = MainWindow(theme_manager)
            return window
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        return pd.DataFrame({
            'AreaShape_Area': [100, 200, 150, 300, 250],
            'Intensity_Mean': [50, 75, 60, 90, 80],
            'Location_Center_X': [10, 20, 15, 30, 25],
            'Location_Center_Y': [5, 10, 7, 15, 12]
        })
    
    def test_rectangle_selection_only_creates_single_entry(self, main_window, sample_data):
        """Test that rectangle selections create only one entry."""
        # Setup
        main_window.csv_parser.data = sample_data
        initial_count = len(main_window.selection_manager.selections)
        
        # Simulate rectangle selection
        selected_indices = [0, 1, 2]
        main_window._on_selection_made(selected_indices)
        
        # Verify single selection was created
        final_count = len(main_window.selection_manager.selections)
        assert final_count == initial_count + 1
        
        # Verify selection properties
        selections = main_window.selection_manager.get_all_selections()
        new_selection = selections[-1]
        assert new_selection.label.startswith("Rectangle_")
        assert new_selection.cell_indices == selected_indices
    
    def test_expression_filter_selection_creates_single_entry(self, main_window, sample_data):
        """Test that expression filter selections create only one entry."""
        # Setup
        main_window.csv_parser.data = sample_data
        initial_count = len(main_window.selection_manager.selections)
        
        # Mock expression filter widget
        expression_filter = Mock()
        expression_filter.get_current_expression = Mock(return_value="AreaShape_Area > 150")
        main_window.scatter_plot_widget.expression_filter_widget = expression_filter
        
        # Simulate expression filter selection
        selected_indices = [1, 3, 4]  # Cells with area > 150
        main_window._on_expression_filter_selection(selected_indices)
        
        # Verify single selection was created
        final_count = len(main_window.selection_manager.selections)
        assert final_count == initial_count + 1
        
        # Verify selection properties
        selections = main_window.selection_manager.get_all_selections()
        new_selection = selections[-1]
        assert new_selection.label.startswith("Expression_")
        assert new_selection.cell_indices == selected_indices
        assert new_selection.metadata.get('expression') == "AreaShape_Area > 150"
        assert new_selection.metadata.get('selection_method') == 'expression_filter'
    
    def test_no_duplicate_selections_for_same_action(self, main_window, sample_data):
        """Test that the same selection action doesn't create duplicates."""
        # Setup
        main_window.csv_parser.data = sample_data
        initial_count = len(main_window.selection_manager.selections)
        
        # Mock expression filter widget
        expression_filter = Mock()
        expression_filter.get_current_expression = Mock(return_value="AreaShape_Area > 200")
        main_window.scatter_plot_widget.expression_filter_widget = expression_filter
        
        # Simulate expression filter selection
        selected_indices = [1, 3]
        
        # Call expression filter handler
        main_window._on_expression_filter_selection(selected_indices)
        count_after_expression = len(main_window.selection_manager.selections)
        
        # Verify only one selection was created by expression filter
        assert count_after_expression == initial_count + 1
        
        # Verify that calling rectangle selection handler separately 
        # would create a different selection (not a duplicate)
        main_window._on_selection_made(selected_indices)
        final_count = len(main_window.selection_manager.selections)
        
        # Should now have 2 selections (expression + rectangle)
        assert final_count == initial_count + 2
        
        # Verify they have different labels and metadata
        selections = main_window.selection_manager.get_all_selections()
        expression_selection = None
        rectangle_selection = None
        
        for selection in selections[-2:]:
            if selection.label.startswith("Expression_"):
                expression_selection = selection
            elif selection.label.startswith("Rectangle_"):
                rectangle_selection = selection
        
        assert expression_selection is not None
        assert rectangle_selection is not None
        assert expression_selection.metadata.get('selection_method') == 'expression_filter'
        assert rectangle_selection.metadata.get('selection_method') != 'expression_filter'
    
    def test_expression_selection_without_expression_details(self, main_window, sample_data):
        """Test expression selection when expression details are not available."""
        # Setup
        main_window.csv_parser.data = sample_data
        initial_count = len(main_window.selection_manager.selections)
        
        # Don't mock expression filter widget (simulating unavailable)
        # main_window.scatter_plot_widget.expression_filter_widget = None
        
        # Simulate expression filter selection without expression details
        selected_indices = [0, 2]
        main_window._on_expression_filter_selection(selected_indices)
        
        # Verify selection was still created
        final_count = len(main_window.selection_manager.selections)
        assert final_count == initial_count + 1
        
        # Verify selection properties
        selections = main_window.selection_manager.get_all_selections()
        new_selection = selections[-1]
        assert new_selection.label.startswith("Expression_")
        assert new_selection.cell_indices == selected_indices
        # Expression metadata should not be set when not available
        assert 'expression' not in new_selection.metadata
    
    def test_empty_selection_handling(self, main_window):
        """Test handling of empty selections."""
        initial_count = len(main_window.selection_manager.selections)
        
        # Test empty rectangle selection
        main_window._on_selection_made([])
        assert len(main_window.selection_manager.selections) == initial_count
        
        # Test empty expression selection
        main_window._on_expression_filter_selection([])
        assert len(main_window.selection_manager.selections) == initial_count
    
    def test_selection_status_updates(self, main_window, sample_data):
        """Test that status messages are correctly updated for different selection types."""
        # Setup
        main_window.csv_parser.data = sample_data
        main_window.update_status = Mock()
        
        # Test rectangle selection status
        main_window._on_selection_made([0, 1, 2])
        main_window.update_status.assert_called_with("Selected 3 cells using rectangle selection")
        
        # Reset mock
        main_window.update_status.reset_mock()
        
        # Test expression selection status
        main_window._on_expression_filter_selection([1, 3, 4])
        main_window.update_status.assert_called_with("Expression filter selected 3 cells")
        
        # Reset mock
        main_window.update_status.reset_mock()
        
        # Test empty selection status
        main_window._on_selection_made([])
        main_window.update_status.assert_called_with("No cells selected")
        
        main_window.update_status.reset_mock()
        main_window._on_expression_filter_selection([])
        main_window.update_status.assert_called_with("No cells selected by expression filter")


if __name__ == "__main__":
    pytest.main([__file__]) 