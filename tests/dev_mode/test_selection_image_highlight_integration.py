"""
Test for selection panel checkbox and image highlight integration in DEV mode
"""

import pytest
import sys
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication

# Add src to path for imports
sys.path.insert(0, 'src')

from pages.main_window import MainWindow
from components.widgets.selection_panel import SelectionPanel
from models.image_handler import ImageHandler
from models.selection_manager import SelectionManager
from services.theme_manager import ThemeManager


class TestSelectionImageHighlightIntegration:
    """Test integration between selection panel checkbox and image highlights."""
    
    @pytest.fixture
    def app(self):
        """Create QApplication instance for testing."""
        if not QApplication.instance():
            app = QApplication([])
        else:
            app = QApplication.instance()
        yield app

    @pytest.fixture
    def mock_theme_manager(self):
        """Create mock ThemeManager."""
        theme_manager = Mock(spec=ThemeManager)
        theme_manager.get_current_theme.return_value = "dark"
        return theme_manager

    @pytest.fixture
    def main_window(self, app, mock_theme_manager):
        """Create MainWindow instance for testing."""
        window = MainWindow(mock_theme_manager)
        
        # Mock the image handler methods we care about
        window.image_handler.highlight_cells = Mock()
        window.image_handler.remove_cell_highlights = Mock()
        
        yield window
        window.close()

    def test_selection_toggle_updates_image_highlights_disabled(self, main_window):
        """Test that disabling selection removes image highlights."""
        # Create a mock selection in the selection manager
        selection_data = {
            'id': 'test_selection_highlight',
            'label': 'Highlight Test',
            'color': '#FF0000',
            'well_position': 'A1',
            'cell_indices': [1, 2, 3, 4, 5],
            'enabled': True
        }
        
        # Add selection to the selection manager first
        selection_id = main_window.selection_manager.add_selection(
            cell_indices=[1, 2, 3, 4, 5],
            label='Highlight Test',
            color='#FF0000'
        )
        
        # Clear previous mock calls
        main_window.image_handler.highlight_cells.reset_mock()
        main_window.image_handler.remove_cell_highlights.reset_mock()
        
        # Test toggling selection to disabled through the panel
        main_window._on_panel_selection_toggled(selection_id, False)
        
        # Verify that remove_cell_highlights was called
        main_window.image_handler.remove_cell_highlights.assert_called_once_with(selection_id)
        
        # Verify that highlight_cells was NOT called (since we're disabling)
        main_window.image_handler.highlight_cells.assert_not_called()

    def test_selection_toggle_updates_image_highlights_enabled(self, main_window):
        """Test that enabling selection adds image highlights."""
        # Create a mock selection in the selection manager
        selection_id = main_window.selection_manager.add_selection(
            cell_indices=[6, 7, 8, 9, 10],
            label='Enable Test',
            color='#00FF00'
        )
        
        # Clear previous mock calls
        main_window.image_handler.highlight_cells.reset_mock()
        main_window.image_handler.remove_cell_highlights.reset_mock()
        
        # Test toggling selection to enabled through the panel
        main_window._on_panel_selection_toggled(selection_id, True)
        
        # Get the selection to verify the correct parameters
        selection = main_window.selection_manager.get_selection(selection_id)
        
        # Verify that highlight_cells was called with correct parameters
        main_window.image_handler.highlight_cells.assert_called_once_with(
            selection_id,
            selection.cell_indices,
            selection.color,
            alpha=0.4
        )
        
        # Verify that remove_cell_highlights was NOT called (since we're enabling)
        main_window.image_handler.remove_cell_highlights.assert_not_called()

    def test_selection_panel_signal_connection(self, main_window):
        """Test that selection panel signals are properly connected to main window."""
        # Verify that the selection panel's signals are connected
        assert main_window.selection_panel.selection_toggled.receivers() > 0
        assert main_window.selection_panel.selection_updated.receivers() > 0
        assert main_window.selection_panel.selection_deleted.receivers() > 0

    def test_multiple_selections_toggle(self, main_window):
        """Test toggling multiple selections and verify independent highlight management."""
        # Create two selections
        selection_id_1 = main_window.selection_manager.add_selection(
            cell_indices=[1, 2, 3],
            label='Selection 1',
            color='#FF0000'
        )
        
        selection_id_2 = main_window.selection_manager.add_selection(
            cell_indices=[4, 5, 6],
            label='Selection 2', 
            color='#00FF00'
        )
        
        # Clear previous mock calls
        main_window.image_handler.highlight_cells.reset_mock()
        main_window.image_handler.remove_cell_highlights.reset_mock()
        
        # Disable first selection
        main_window._on_panel_selection_toggled(selection_id_1, False)
        
        # Verify only first selection's highlights were removed
        main_window.image_handler.remove_cell_highlights.assert_called_once_with(selection_id_1)
        
        # Reset mocks
        main_window.image_handler.highlight_cells.reset_mock()
        main_window.image_handler.remove_cell_highlights.reset_mock()
        
        # Enable first selection again
        main_window._on_panel_selection_toggled(selection_id_1, True)
        
        # Get selection for verification
        selection_1 = main_window.selection_manager.get_selection(selection_id_1)
        
        # Verify first selection's highlights were added back
        main_window.image_handler.highlight_cells.assert_called_once_with(
            selection_id_1,
            selection_1.cell_indices,
            selection_1.color,
            alpha=0.4
        )

    def test_logging_during_image_highlight_integration(self, main_window, caplog):
        """Test that appropriate logging occurs during highlight integration."""
        # Create a selection
        selection_id = main_window.selection_manager.add_selection(
            cell_indices=[11, 12, 13],
            label='Logging Test',
            color='#0000FF'
        )
        
        # Clear any existing log records
        caplog.clear()
        
        # Toggle selection to disabled
        main_window._on_panel_selection_toggled(selection_id, False)
        
        # Check that appropriate log messages were recorded
        log_messages = [record.message for record in caplog.records]
        
        # Should have log messages about the toggle operation with image highlights
        assert any('toggled to disabled - image highlights updated' in msg for msg in log_messages)

    def test_scatter_plot_update_on_toggle(self, main_window):
        """Test that scatter plot is also updated when selection is toggled."""
        # Create a selection
        selection_id = main_window.selection_manager.add_selection(
            cell_indices=[14, 15, 16],
            label='Scatter Plot Test',
            color='#FFFF00'
        )
        
        # Mock the scatter plot update method
        with patch.object(main_window, '_update_scatter_plot_highlights') as mock_scatter_update:
            # Toggle selection
            main_window._on_panel_selection_toggled(selection_id, False)
            
            # Verify scatter plot was updated
            mock_scatter_update.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 