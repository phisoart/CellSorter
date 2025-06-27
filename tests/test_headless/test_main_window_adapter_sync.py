"""
Test MainWindow Adapter State Synchronization

Tests for property_changed signal and set_property method in MainWindowState
"""

import pytest
from unittest.mock import Mock, MagicMock
from src.headless.main_window_adapter import MainWindowAdapter, MainWindowState
from src.headless.mode_manager import ModeManager


class TestMainWindowStateSync:
    """Test MainWindowState synchronization features."""
    
    def test_property_changed_signal_exists(self):
        """Test that MainWindowState has property_changed signal."""
        state = MainWindowState()
        assert hasattr(state, 'property_changed')
        assert hasattr(state.property_changed, 'connect')
        assert hasattr(state.property_changed, 'emit')
    
    def test_set_property_method_exists(self):
        """Test that MainWindowState has set_property method."""
        state = MainWindowState()
        assert hasattr(state, 'set_property')
        assert callable(state.set_property)
    
    def test_set_property_updates_value(self):
        """Test that set_property actually updates the property value."""
        state = MainWindowState()
        
        # Test various properties
        state.set_property('window_title', 'New Title')
        assert state.window_title == 'New Title'
        
        state.set_property('zoom_level', 2.5)
        assert state.zoom_level == 2.5
        
        state.set_property('is_modified', True)
        assert state.is_modified is True
    
    def test_set_property_emits_signal(self):
        """Test that set_property emits property_changed signal."""
        state = MainWindowState()
        
        # Create a mock callback
        callback = Mock()
        state.property_changed.connect(callback)
        
        # Set a property
        state.set_property('window_title', 'Test Title')
        
        # Verify callback was called with correct arguments
        callback.assert_called_once_with('window_title', 'Test Title')
    
    def test_set_property_unknown_property(self):
        """Test that set_property handles unknown properties gracefully."""
        state = MainWindowState()
        
        # Should not raise exception
        state.set_property('unknown_property', 'value')
        
        # Property should not be added
        assert not hasattr(state, 'unknown_property')
    
    def test_multiple_callbacks(self):
        """Test that multiple callbacks can be connected to property_changed."""
        state = MainWindowState()
        
        callback1 = Mock()
        callback2 = Mock()
        
        state.property_changed.connect(callback1)
        state.property_changed.connect(callback2)
        
        state.set_property('status_message', 'Testing')
        
        # Both callbacks should be called
        callback1.assert_called_once_with('status_message', 'Testing')
        callback2.assert_called_once_with('status_message', 'Testing')
    
    def test_adapter_sync_to_window(self):
        """Test MainWindowAdapter syncs state changes to actual window."""
        mode_manager = Mock(spec=ModeManager)
        adapter = MainWindowAdapter(mode_manager)
        
        # Create a mock window
        mock_window = Mock()
        mock_window.setWindowTitle = Mock()
        mock_window.update_status = Mock()
        
        # Connect adapter to window
        adapter.connect_to_window(mock_window)
        
        # Change state through set_property
        adapter.state.set_property('window_title', 'Synced Title')
        adapter.state.set_property('status_message', 'Synced Status')
        
        # Verify window methods were called
        mock_window.setWindowTitle.assert_called_with('Synced Title')
        mock_window.update_status.assert_called_with('Synced Status')
    
    def test_adapter_sync_from_window(self):
        """Test MainWindowAdapter syncs window events to state."""
        mode_manager = Mock(spec=ModeManager)
        adapter = MainWindowAdapter(mode_manager)
        
        # Create a mock window with signals
        mock_window = Mock()
        mock_window.image_loaded = Mock()
        mock_window.image_loaded.connect = Mock()
        mock_window.csv_loaded = Mock()
        mock_window.csv_loaded.connect = Mock()
        mock_window.selection_changed = Mock()
        mock_window.selection_changed.connect = Mock()
        
        # Connect adapter to window
        adapter.connect_to_window(mock_window)
        
        # Simulate window events
        adapter._sync_from_window('image_loaded', '/path/to/image.tif')
        adapter._sync_from_window('csv_loaded', '/path/to/data.csv')
        adapter._sync_from_window('selection_changed', {'id': 1, 'cells': [1, 2, 3]})
        
        # Verify state was updated
        assert adapter.state.current_image_path == '/path/to/image.tif'
        assert adapter.state.current_csv_path == '/path/to/data.csv'
        assert adapter.state.current_selection == {'id': 1, 'cells': [1, 2, 3]}
    
    def test_state_serialization_with_selection(self):
        """Test that state serialization includes current_selection."""
        state = MainWindowState()
        state.current_selection = {'id': 1, 'cells': [1, 2, 3]}
        
        # Convert to dict
        state_dict = state.to_dict()
        
        # Verify current_selection is included
        assert 'current_selection' in state_dict
        assert state_dict['current_selection'] == {'id': 1, 'cells': [1, 2, 3]}
        
        # Create new state from dict
        new_state = MainWindowState.from_dict(state_dict)
        assert new_state.current_selection == {'id': 1, 'cells': [1, 2, 3]}


class TestMainWindowAdapterHeadlessMode:
    """Test MainWindowAdapter functionality in headless mode."""
    
    def test_action_execution_without_display(self):
        """Test that actions can be executed without display."""
        mode_manager = Mock(spec=ModeManager)
        mode_manager.is_dev_mode.return_value = True
        adapter = MainWindowAdapter(mode_manager)
        
        # Test various actions
        result = adapter.execute_action('open_image', file_path='/test/image.tif')
        assert result['success'] is True
        assert adapter.state.current_image_path == '/test/image.tif'
        
        result = adapter.execute_action('zoom_in')
        assert result['success'] is True
        assert adapter.state.zoom_level > 1.0
        
        result = adapter.execute_action('toggle_overlays')
        assert result['success'] is True
        assert adapter.state.overlays_visible is False
    
    def test_ui_definition_generation(self):
        """Test UI definition generation in headless mode."""
        mode_manager = Mock(spec=ModeManager)
        mode_manager.is_dev_mode.return_value = True
        adapter = MainWindowAdapter(mode_manager)
        
        # Get UI definition
        ui_def = adapter.get_ui_definition()
        
        # Verify structure
        assert ui_def.metadata['mode'] == 'headless'
        assert len(ui_def.widgets) > 0
        
        # Find main window widget
        main_window = next(w for w in ui_def.widgets if w.name == 'main_window')
        assert main_window.properties['title'] == 'CellSorter'
        
        # Verify panel visibility affects UI definition
        adapter.state.image_panel_visible = False
        ui_def2 = adapter.get_ui_definition()
        
        # Image panel should not be in widgets
        image_panels = [w for w in ui_def2.widgets if w.name == 'image_panel']
        assert len(image_panels) == 0 