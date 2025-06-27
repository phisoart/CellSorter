"""
Test MainWindow Action Execution in Headless Mode

Tests for all MainWindow actions working correctly without display.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
from src.headless.main_window_adapter import MainWindowAdapter
from src.headless.mode_manager import ModeManager


class TestMainWindowActionsHeadless:
    """Test MainWindow actions in headless mode."""
    
    def setup_method(self):
        """Setup for each test."""
        # Create adapter in headless mode
        self.mode_manager = Mock(spec=ModeManager)
        self.mode_manager.is_dev_mode.return_value = True
        self.adapter = MainWindowAdapter(self.mode_manager)
    
    def test_file_actions(self):
        """Test file-related actions."""
        # Test open image
        result = self.adapter.execute_action('open_image', file_path='/test/image.tif')
        assert result['success'] is True
        assert result['result']['file_path'] == '/test/image.tif'
        assert result['result']['loaded'] is True
        assert self.adapter.state.current_image_path == '/test/image.tif'
        assert 'image.tif' in self.adapter.state.window_title
        
        # Test open CSV
        result = self.adapter.execute_action('open_csv', file_path='/test/data.csv')
        assert result['success'] is True
        assert result['result']['file_path'] == '/test/data.csv'
        assert result['result']['loaded'] is True
        assert self.adapter.state.current_csv_path == '/test/data.csv'
        
        # Test save session
        result = self.adapter.execute_action('save_session', file_path='/test/session.json')
        assert result['success'] is True
        assert result['result']['file_path'] == '/test/session.json'
        assert result['result']['saved'] is True
        assert 'data' in result['result']
        
        # Test load session
        result = self.adapter.execute_action('load_session', file_path='/test/session.json')
        assert result['success'] is True
        assert result['result']['file_path'] == '/test/session.json'
        assert result['result']['loaded'] is True
        
        # Test file actions without file path
        result = self.adapter.execute_action('open_image')
        assert result['success'] is True
        assert result['result']['error'] == 'No file path provided'
    
    def test_edit_actions(self):
        """Test edit-related actions."""
        # Test undo
        result = self.adapter.execute_action('undo')
        assert result['success'] is True
        assert result['result']['undone'] is True
        
        # Test redo
        result = self.adapter.execute_action('redo')
        assert result['success'] is True
        assert result['result']['redone'] is True
        
        # Test zoom in
        initial_zoom = self.adapter.state.zoom_level
        result = self.adapter.execute_action('zoom_in')
        assert result['success'] is True
        assert self.adapter.state.zoom_level > initial_zoom
        assert result['result']['zoom_level'] == self.adapter.state.zoom_level
        
        # Test zoom out
        result = self.adapter.execute_action('zoom_out')
        assert result['success'] is True
        assert self.adapter.state.zoom_level < 1.2  # Should be less than after zoom in
        
        # Test zoom fit
        result = self.adapter.execute_action('zoom_fit')
        assert result['success'] is True
        assert self.adapter.state.zoom_level == 1.0
        assert result['result']['zoom_level'] == 1.0
        
        # Test multiple zoom operations
        for _ in range(5):
            self.adapter.execute_action('zoom_in')
        assert self.adapter.state.zoom_level <= 10.0  # Max zoom limit
        
        for _ in range(10):
            self.adapter.execute_action('zoom_out')
        assert self.adapter.state.zoom_level >= 0.1  # Min zoom limit
    
    def test_view_actions(self):
        """Test view-related actions."""
        # Test toggle overlays
        initial_state = self.adapter.state.overlays_visible
        result = self.adapter.execute_action('toggle_overlays')
        assert result['success'] is True
        assert self.adapter.state.overlays_visible != initial_state
        assert result['result']['overlays_visible'] == self.adapter.state.overlays_visible
        
        # Toggle back
        result = self.adapter.execute_action('toggle_overlays')
        assert result['success'] is True
        assert self.adapter.state.overlays_visible == initial_state
        
        # Test reset view
        self.adapter.state.zoom_level = 2.5
        result = self.adapter.execute_action('reset_view')
        assert result['success'] is True
        assert result['result']['view_reset'] is True
        assert self.adapter.state.zoom_level == 1.0
    
    def test_tool_actions(self):
        """Test tool-related actions."""
        # Test activate selection tool
        result = self.adapter.execute_action('activate_selection_tool')
        assert result['success'] is True
        assert result['result']['active_tool'] == 'selection'
        assert self.adapter.state.active_tool == 'selection'
        
        # Test activate calibration tool
        result = self.adapter.execute_action('activate_calibration_tool')
        assert result['success'] is True
        assert result['result']['active_tool'] == 'calibration'
        assert self.adapter.state.active_tool == 'calibration'
        
        # Test calibrate coordinates
        result = self.adapter.execute_action('calibrate_coordinates')
        assert result['success'] is True
        assert result['result']['calibration_started'] is True
    
    def test_unknown_action(self):
        """Test handling of unknown actions."""
        result = self.adapter.execute_action('unknown_action')
        assert result['success'] is False
        assert 'error' in result
        assert 'Unknown action' in result['error']
