"""
Tests for MainWindow Headless Adapter

Tests the adapter that makes the existing MainWindow work in headless mode.
Covers UI definitions, state management, action handlers, and mode-aware operation.
"""

import unittest
from unittest.mock import Mock, patch
from pathlib import Path

from src.headless.main_window_adapter import MainWindowAdapter, MainWindowState
from src.headless.mode_manager import ModeManager
from src.headless.ui_model import WidgetType, Geometry


class TestMainWindowState(unittest.TestCase):
    """Test MainWindowState data class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.state = MainWindowState()
    
    def test_default_state(self):
        """Test default state values."""
        self.assertEqual(self.state.window_title, "CellSorter")
        self.assertIsNone(self.state.current_image_path)
        self.assertIsNone(self.state.current_csv_path)
        self.assertFalse(self.state.is_maximized)
        self.assertFalse(self.state.is_modified)
        self.assertEqual(self.state.status_message, "Ready")
        self.assertEqual(self.state.cell_count, 0)
        self.assertEqual(self.state.zoom_level, 1.0)
        self.assertEqual(self.state.mouse_coordinates, (0.0, 0.0))
        self.assertTrue(self.state.image_panel_visible)
        self.assertTrue(self.state.plot_panel_visible)
        self.assertTrue(self.state.selection_panel_visible)
        self.assertEqual(self.state.active_tool, "selection")
        self.assertTrue(self.state.overlays_visible)
        self.assertEqual(self.state.current_theme, "light")
        self.assertIsNone(self.state.last_session_path)
    
    def test_state_serialization(self):
        """Test state to/from dictionary conversion."""
        # Set up state with custom values
        self.state.current_image_path = "/path/to/image.png"
        self.state.current_csv_path = "/path/to/data.csv"
        self.state.window_title = "Custom Title"
        self.state.window_geometry = Geometry(x=100, y=200, width=800, height=600)
        self.state.is_maximized = True
        self.state.is_modified = True
        self.state.status_message = "Processing..."
        self.state.cell_count = 42
        self.state.zoom_level = 2.5
        self.state.mouse_coordinates = (150.0, 250.0)
        self.state.image_panel_visible = False
        self.state.plot_panel_visible = True
        self.state.selection_panel_visible = False
        self.state.active_tool = "calibration"
        self.state.overlays_visible = False
        self.state.current_theme = "dark"
        self.state.last_session_path = "/path/to/session.json"
        
        # Convert to dictionary
        state_dict = self.state.to_dict()
        
        # Verify dictionary contents
        self.assertEqual(state_dict["current_image_path"], "/path/to/image.png")
        self.assertEqual(state_dict["current_csv_path"], "/path/to/data.csv")
        self.assertEqual(state_dict["window_title"], "Custom Title")
        self.assertIsNotNone(state_dict["window_geometry"])
        self.assertTrue(state_dict["is_maximized"])
        self.assertTrue(state_dict["is_modified"])
        self.assertEqual(state_dict["status_message"], "Processing...")
        self.assertEqual(state_dict["cell_count"], 42)
        self.assertEqual(state_dict["zoom_level"], 2.5)
        self.assertEqual(state_dict["mouse_coordinates"], (150.0, 250.0))
        self.assertFalse(state_dict["image_panel_visible"])
        self.assertTrue(state_dict["plot_panel_visible"])
        self.assertFalse(state_dict["selection_panel_visible"])
        self.assertEqual(state_dict["active_tool"], "calibration")
        self.assertFalse(state_dict["overlays_visible"])
        self.assertEqual(state_dict["current_theme"], "dark")
        self.assertEqual(state_dict["last_session_path"], "/path/to/session.json")
        
        # Convert back from dictionary
        restored_state = MainWindowState.from_dict(state_dict)
        
        # Verify restored state
        self.assertEqual(restored_state.current_image_path, "/path/to/image.png")
        self.assertEqual(restored_state.current_csv_path, "/path/to/data.csv")
        self.assertEqual(restored_state.window_title, "Custom Title")
        self.assertIsNotNone(restored_state.window_geometry)
        self.assertTrue(restored_state.is_maximized)
        self.assertTrue(restored_state.is_modified)
        self.assertEqual(restored_state.status_message, "Processing...")
        self.assertEqual(restored_state.cell_count, 42)
        self.assertEqual(restored_state.zoom_level, 2.5)
        self.assertEqual(restored_state.mouse_coordinates, (150.0, 250.0))
        self.assertFalse(restored_state.image_panel_visible)
        self.assertTrue(restored_state.plot_panel_visible)
        self.assertFalse(restored_state.selection_panel_visible)
        self.assertEqual(restored_state.active_tool, "calibration")
        self.assertFalse(restored_state.overlays_visible)
        self.assertEqual(restored_state.current_theme, "dark")
        self.assertEqual(restored_state.last_session_path, "/path/to/session.json")


class TestMainWindowAdapter(unittest.TestCase):
    """Test MainWindowAdapter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mode_manager = Mock(spec=ModeManager)
        self.mode_manager.is_dev_mode.return_value = True
        self.adapter = MainWindowAdapter(self.mode_manager)
    
    def test_adapter_initialization(self):
        """Test adapter initialization."""
        self.assertIsNotNone(self.adapter.state)
        self.assertIsInstance(self.adapter.state, MainWindowState)
        self.assertEqual(len(self.adapter.action_handlers), 23)
        self.assertIn("open_image", self.adapter.action_handlers)
        self.assertIn("open_csv", self.adapter.action_handlers)
        self.assertIn("save_session", self.adapter.action_handlers)
        self.assertIn("zoom_in", self.adapter.action_handlers)
        self.assertIn("toggle_panel", self.adapter.action_handlers)
    
    def test_ui_definition_generation(self):
        """Test UI definition generation."""
        ui_def = self.adapter.get_ui_definition()
        
        # Check metadata
        self.assertIn("metadata", ui_def.to_dict())
        metadata = ui_def.metadata
        self.assertEqual(metadata["version"], "1.0")
        self.assertEqual(metadata["description"], "CellSorter Main Window")
        self.assertEqual(metadata["mode"], "headless")
        
        # Check widgets
        self.assertGreater(len(ui_def.widgets), 0)
        widget_names = [w.name for w in ui_def.widgets]
        self.assertIn("main_window", widget_names)
        self.assertIn("menu_bar", widget_names)
        self.assertIn("main_toolbar", widget_names)
        self.assertIn("central_widget", widget_names)
        self.assertIn("main_splitter", widget_names)
        self.assertIn("status_bar", widget_names)
        
        # Check main window widget
        main_window = next(w for w in ui_def.widgets if w.name == "main_window")
        self.assertEqual(main_window.type, WidgetType.MAIN_WINDOW)
        self.assertEqual(main_window.properties["title"], "CellSorter")
        self.assertEqual(main_window.properties["width"], 1200)
        self.assertEqual(main_window.properties["height"], 800)
        
        # Check panels are included when visible
        if self.adapter.state.image_panel_visible:
            self.assertIn("image_panel", widget_names)
        if self.adapter.state.plot_panel_visible:
            self.assertIn("plot_panel", widget_names)
        if self.adapter.state.selection_panel_visible:
            self.assertIn("selection_panel", widget_names)
    
    def test_ui_definition_with_hidden_panels(self):
        """Test UI definition when panels are hidden."""
        # Hide all panels
        self.adapter.state.image_panel_visible = False
        self.adapter.state.plot_panel_visible = False
        self.adapter.state.selection_panel_visible = False
        
        ui_def = self.adapter.get_ui_definition()
        widget_names = [w.name for w in ui_def.widgets]
        
        # Panels should not be included
        self.assertNotIn("image_panel", widget_names)
        self.assertNotIn("plot_panel", widget_names)
        self.assertNotIn("selection_panel", widget_names)
        
        # Other widgets should still be present
        self.assertIn("main_window", widget_names)
        self.assertIn("menu_bar", widget_names)
        self.assertIn("main_toolbar", widget_names)
        self.assertIn("status_bar", widget_names)
    
    def test_action_execution(self):
        """Test action execution framework."""
        # Test valid action
        result = self.adapter.execute_action("zoom_in")
        self.assertTrue(result["success"])
        self.assertIn("result", result)
        
        # Test invalid action
        result = self.adapter.execute_action("invalid_action")
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertIn("Unknown action", result["error"])
    
    def test_file_operations(self):
        """Test file operation actions."""
        # Test open image
        result = self.adapter.open_image_file("/path/to/image.png")
        self.assertEqual(result["file_path"], "/path/to/image.png")
        self.assertTrue(result["loaded"])
        self.assertEqual(self.adapter.state.current_image_path, "/path/to/image.png")
        self.assertIn("image.png", self.adapter.state.window_title)
        
        # Test open CSV
        result = self.adapter.open_csv_file("/path/to/data.csv")
        self.assertEqual(result["file_path"], "/path/to/data.csv")
        self.assertTrue(result["loaded"])
        self.assertEqual(self.adapter.state.current_csv_path, "/path/to/data.csv")
        
        # Test save session
        result = self.adapter.save_session("/path/to/session.json")
        self.assertEqual(result["file_path"], "/path/to/session.json")
        self.assertTrue(result["saved"])
        self.assertIn("data", result)
        self.assertEqual(self.adapter.state.last_session_path, "/path/to/session.json")
        
        # Test load session
        result = self.adapter.load_session("/path/to/session.json")
        self.assertEqual(result["file_path"], "/path/to/session.json")
        self.assertTrue(result["loaded"])
    
    def test_zoom_operations(self):
        """Test zoom operations."""
        initial_zoom = self.adapter.state.zoom_level
        
        # Test zoom in
        result = self.adapter.zoom_in()
        self.assertGreater(self.adapter.state.zoom_level, initial_zoom)
        self.assertEqual(result["zoom_level"], self.adapter.state.zoom_level)
        
        # Test zoom out
        zoom_before_out = self.adapter.state.zoom_level
        result = self.adapter.zoom_out()
        self.assertLess(self.adapter.state.zoom_level, zoom_before_out)
        self.assertEqual(result["zoom_level"], self.adapter.state.zoom_level)
        
        # Test zoom fit
        result = self.adapter.zoom_fit()
        self.assertEqual(self.adapter.state.zoom_level, 1.0)
        self.assertEqual(result["zoom_level"], 1.0)
        
        # Test zoom limits
        self.adapter.state.zoom_level = 0.05
        self.adapter.zoom_out()
        self.assertGreaterEqual(self.adapter.state.zoom_level, 0.1)
        
        self.adapter.state.zoom_level = 9.0
        self.adapter.zoom_in()
        self.assertLessEqual(self.adapter.state.zoom_level, 10.0)
    
    def test_panel_operations(self):
        """Test panel visibility operations."""
        # Test image panel toggle
        initial_visible = self.adapter.state.image_panel_visible
        result = self.adapter.toggle_panel("image")
        self.assertEqual(self.adapter.state.image_panel_visible, not initial_visible)
        self.assertEqual(result["panel"], "image")
        self.assertEqual(result["visible"], not initial_visible)
        
        # Test plot panel toggle
        initial_visible = self.adapter.state.plot_panel_visible
        result = self.adapter.toggle_panel("plot")
        self.assertEqual(self.adapter.state.plot_panel_visible, not initial_visible)
        self.assertEqual(result["panel"], "plot")
        self.assertEqual(result["visible"], not initial_visible)
        
        # Test selection panel toggle
        initial_visible = self.adapter.state.selection_panel_visible
        result = self.adapter.toggle_panel("selection")
        self.assertEqual(self.adapter.state.selection_panel_visible, not initial_visible)
        self.assertEqual(result["panel"], "selection")
        self.assertEqual(result["visible"], not initial_visible)
    
    def test_tool_operations(self):
        """Test tool activation operations."""
        # Test selection tool activation
        result = self.adapter.activate_selection_tool()
        self.assertEqual(self.adapter.state.active_tool, "selection")
        self.assertEqual(result["active_tool"], "selection")
        
        # Test calibration tool activation
        result = self.adapter.activate_calibration_tool()
        self.assertEqual(self.adapter.state.active_tool, "calibration")
        self.assertEqual(result["active_tool"], "calibration")
    
    def test_overlay_operations(self):
        """Test overlay operations."""
        initial_visible = self.adapter.state.overlays_visible
        result = self.adapter.toggle_overlays()
        self.assertEqual(self.adapter.state.overlays_visible, not initial_visible)
        self.assertEqual(result["overlays_visible"], not initial_visible)
    
    def test_theme_operations(self):
        """Test theme operations."""
        # Start with light theme
        self.adapter.state.current_theme = "light"
        result = self.adapter.toggle_theme()
        self.assertEqual(self.adapter.state.current_theme, "dark")
        self.assertEqual(result["theme"], "dark")
        
        # Toggle back to light theme
        result = self.adapter.toggle_theme()
        self.assertEqual(self.adapter.state.current_theme, "light")
        self.assertEqual(result["theme"], "light")
    
    def test_state_management(self):
        """Test state get/set operations."""
        # Create custom state
        custom_state = MainWindowState()
        custom_state.window_title = "Custom Window"
        custom_state.zoom_level = 2.0
        custom_state.current_theme = "dark"
        
        # Set state
        self.adapter.set_state(custom_state)
        
        # Verify state was set
        current_state = self.adapter.get_state()
        self.assertEqual(current_state.window_title, "Custom Window")
        self.assertEqual(current_state.zoom_level, 2.0)
        self.assertEqual(current_state.current_theme, "dark")
    
    def test_status_updates(self):
        """Test status update methods."""
        # Test status message update
        self.adapter.update_status("Processing image...")
        self.assertEqual(self.adapter.state.status_message, "Processing image...")
        
        # Test cell count update
        self.adapter.update_cell_count(123)
        self.assertEqual(self.adapter.state.cell_count, 123)
        
        # Test zoom level update
        self.adapter.update_zoom_level(3.5)
        self.assertEqual(self.adapter.state.zoom_level, 3.5)
        
        # Test coordinates update
        self.adapter.update_coordinates(100.5, 200.7)
        self.assertEqual(self.adapter.state.mouse_coordinates, (100.5, 200.7))
    
    def test_mode_aware_ui_generation(self):
        """Test that UI generation is mode-aware."""
        # Test headless mode
        self.mode_manager.is_dev_mode.return_value = True
        ui_def = self.adapter.get_ui_definition()
        self.assertEqual(ui_def.metadata["mode"], "headless")
        
        # Test GUI mode
        self.mode_manager.is_dev_mode.return_value = False
        ui_def = self.adapter.get_ui_definition()
        self.assertEqual(ui_def.metadata["mode"], "gui")
    
    def test_error_handling_in_actions(self):
        """Test error handling in action execution."""
        # Mock an action that raises an exception
        def failing_action():
            raise RuntimeError("Test error")
        
        self.adapter.action_handlers["test_failing"] = failing_action
        
        result = self.adapter.execute_action("test_failing")
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertIn("Test error", result["error"])


if __name__ == "__main__":
    unittest.main() 