"""
Tests for Session Manager

Test session management functionality including save/load,
state management, and user preferences.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

import unittest
import tempfile
import json
from unittest.mock import Mock, patch
from pathlib import Path
from datetime import datetime

from src.headless.session_manager import HeadlessSessionManager, SessionData
from src.headless.main_window_adapter import MainWindowState
from src.headless.mode_manager import ModeManager
from src.headless.ui_model import UIModel, Widget, WidgetType


class TestSessionData(unittest.TestCase):
    """Test SessionData data class."""
    
    def test_default_session_data(self):
        """Test default session data values."""
        session = SessionData()
        
        self.assertEqual(session.session_id, "")
        self.assertEqual(session.created_at, "")
        self.assertEqual(session.last_modified, "")
        self.assertEqual(session.version, "1.0")
        self.assertIsNone(session.main_window_state)
        self.assertEqual(len(session.ui_models), 0)
        self.assertEqual(len(session.recent_files), 0)
        self.assertEqual(len(session.recent_sessions), 0)
        self.assertEqual(len(session.user_preferences), 0)
        self.assertEqual(len(session.project_settings), 0)
        self.assertEqual(len(session.analysis_results), 0)
    
    def test_session_data_serialization(self):
        """Test session data to/from dictionary conversion."""
        # Create session with data
        session = SessionData(
            session_id="test_session",
            created_at="2024-01-01T00:00:00",
            last_modified="2024-01-01T01:00:00",
            version="1.0"
        )
        
        # Add some data
        session.main_window_state = {"window_title": "Test Window"}
        session.ui_models = {"main": {"version": "1.0"}}
        session.recent_files = ["/path/to/file1.png", "/path/to/file2.csv"]
        session.user_preferences = {"theme": "dark", "auto_save": True}
        session.project_settings = {"image_format": "PNG"}
        session.analysis_results = {"analysis1": {"result": "success"}}
        
        # Convert to dictionary
        session_dict = session.to_dict()
        
        # Verify dictionary contents
        self.assertEqual(session_dict["session_id"], "test_session")
        self.assertEqual(session_dict["created_at"], "2024-01-01T00:00:00")
        self.assertEqual(session_dict["last_modified"], "2024-01-01T01:00:00")
        self.assertEqual(session_dict["version"], "1.0")
        self.assertEqual(session_dict["main_window_state"]["window_title"], "Test Window")
        self.assertEqual(len(session_dict["recent_files"]), 2)
        self.assertEqual(session_dict["user_preferences"]["theme"], "dark")
        
        # Convert back from dictionary
        restored_session = SessionData.from_dict(session_dict)
        
        # Verify restored session
        self.assertEqual(restored_session.session_id, "test_session")
        self.assertEqual(restored_session.created_at, "2024-01-01T00:00:00")
        self.assertEqual(restored_session.last_modified, "2024-01-01T01:00:00")
        self.assertEqual(restored_session.version, "1.0")
        if restored_session.main_window_state is not None:
            self.assertEqual(restored_session.main_window_state["window_title"], "Test Window")
        self.assertEqual(len(restored_session.recent_files), 2)
        self.assertEqual(restored_session.user_preferences["theme"], "dark")


class TestHeadlessSessionManager(unittest.TestCase):
    """Test HeadlessSessionManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mode_manager = Mock(spec=ModeManager)
        self.mode_manager.is_dev_mode.return_value = True
        
        # Use temporary directory for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        
        with patch('pathlib.Path.home') as mock_home:
            mock_home.return_value = Path(self.temp_dir.name)
            self.session_manager = HeadlessSessionManager(self.mode_manager)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def test_session_manager_initialization(self):
        """Test session manager initialization."""
        self.assertIsNotNone(self.session_manager.mode_manager)
        self.assertIsNone(self.session_manager.current_session)
        self.assertIsNone(self.session_manager.session_file_path)
        self.assertTrue(self.session_manager.auto_save_enabled)
        self.assertEqual(self.session_manager.auto_save_interval, 300)
        self.assertTrue(self.session_manager.sessions_dir.exists())
    
    def test_create_new_session(self):
        """Test new session creation."""
        # Create session with custom ID
        session = self.session_manager.create_new_session("custom_session")
        
        self.assertEqual(session.session_id, "custom_session")
        self.assertIsNotNone(session.created_at)
        self.assertIsNotNone(session.last_modified)
        self.assertEqual(session.version, "1.0")
        self.assertEqual(self.session_manager.current_session, session)
        
        # Create session with auto-generated ID
        session2 = self.session_manager.create_new_session()
        self.assertTrue(session2.session_id.startswith("session_"))
        self.assertNotEqual(session.session_id, session2.session_id)
    
    def test_save_and_load_session(self):
        """Test session save and load operations."""
        # Create and configure session
        session = self.session_manager.create_new_session("test_session")
        session.user_preferences = {"theme": "dark", "auto_save": True}
        session.recent_files = ["/path/to/file1.png", "/path/to/file2.csv"]
        
        # Save session
        success = self.session_manager.save_session()
        self.assertTrue(success)
        self.assertIsNotNone(self.session_manager.session_file_path)
        if self.session_manager.session_file_path is not None:
            self.assertTrue(self.session_manager.session_file_path.exists())
        
        # Clear current session
        saved_path = self.session_manager.session_file_path
        self.session_manager.clear_current_session()
        self.assertIsNone(self.session_manager.current_session)
        
        # Load session
        if saved_path is not None:
            success = self.session_manager.load_session(saved_path)
            self.assertTrue(success)
            self.assertIsNotNone(self.session_manager.current_session)
            if self.session_manager.current_session is not None:
                self.assertEqual(self.session_manager.current_session.session_id, "test_session")
                self.assertEqual(self.session_manager.current_session.user_preferences["theme"], "dark")
                self.assertEqual(len(self.session_manager.current_session.recent_files), 2)
    
    def test_save_session_with_custom_path(self):
        """Test saving session to custom path."""
        session = self.session_manager.create_new_session("custom_path_session")
        
        custom_path = Path(self.temp_dir.name) / "custom" / "session.json"
        success = self.session_manager.save_session(custom_path)
        
        self.assertTrue(success)
        self.assertTrue(custom_path.exists())
        self.assertEqual(self.session_manager.session_file_path, custom_path)
    
    def test_load_nonexistent_session(self):
        """Test loading non-existent session file."""
        nonexistent_path = Path(self.temp_dir.name) / "nonexistent.json"
        success = self.session_manager.load_session(nonexistent_path)
        
        self.assertFalse(success)
        self.assertIsNone(self.session_manager.current_session)
    
    def test_main_window_state_management(self):
        """Test main window state save and load."""
        # Create main window state
        state = MainWindowState()
        state.window_title = "Test Window"
        state.zoom_level = 2.5
        state.current_theme = "dark"
        
        # Save state (should create session automatically)
        self.session_manager.save_main_window_state(state)
        
        self.assertIsNotNone(self.session_manager.current_session)
        if self.session_manager.current_session is not None:
            self.assertIsNotNone(self.session_manager.current_session.main_window_state)
        
        # Load state
        loaded_state = self.session_manager.load_main_window_state()
        
        self.assertIsNotNone(loaded_state)
        if loaded_state is not None:
            self.assertEqual(loaded_state.window_title, "Test Window")
            self.assertEqual(loaded_state.zoom_level, 2.5)
            self.assertEqual(loaded_state.current_theme, "dark")
    
    def test_main_window_state_load_without_session(self):
        """Test loading main window state without session."""
        state = self.session_manager.load_main_window_state()
        self.assertIsNone(state)
    
    def test_recent_files_management(self):
        """Test recent files management."""
        # Add recent files
        self.session_manager.add_recent_file("/path/to/file1.png")
        self.session_manager.add_recent_file("/path/to/file2.csv")
        self.session_manager.add_recent_file("/path/to/file3.tiff")
        
        recent_files = self.session_manager.get_recent_files()
        
        # Should be in reverse order (most recent first)
        self.assertEqual(len(recent_files), 3)
        self.assertEqual(recent_files[0], "/path/to/file3.tiff")
        self.assertEqual(recent_files[1], "/path/to/file2.csv")
        self.assertEqual(recent_files[2], "/path/to/file1.png")
        
        # Add duplicate file - should move to front
        self.session_manager.add_recent_file("/path/to/file1.png")
        recent_files = self.session_manager.get_recent_files()
        
        self.assertEqual(len(recent_files), 3)  # Still 3 files
        self.assertEqual(recent_files[0], "/path/to/file1.png")  # Moved to front
        
        # Test max recent limit
        for i in range(15):
            self.session_manager.add_recent_file(f"/path/to/file{i}.ext")
        
        recent_files = self.session_manager.get_recent_files()
        self.assertEqual(len(recent_files), 10)  # Limited to 10
    
    def test_recent_files_without_session(self):
        """Test getting recent files without session."""
        recent_files = self.session_manager.get_recent_files()
        self.assertEqual(len(recent_files), 0)
    
    def test_user_preferences_management(self):
        """Test user preferences management."""
        # Set preferences
        self.session_manager.set_user_preference("theme", "dark")
        self.session_manager.set_user_preference("auto_save", True)
        self.session_manager.set_user_preference("zoom_level", 1.5)
        
        # Get preferences
        theme = self.session_manager.get_user_preference("theme")
        auto_save = self.session_manager.get_user_preference("auto_save")
        zoom = self.session_manager.get_user_preference("zoom_level")
        default_value = self.session_manager.get_user_preference("nonexistent", "default")
        
        self.assertEqual(theme, "dark")
        self.assertTrue(auto_save)
        self.assertEqual(zoom, 1.5)
        self.assertEqual(default_value, "default")
    
    def test_user_preferences_without_session(self):
        """Test user preferences without session."""
        # Should return default values
        value = self.session_manager.get_user_preference("nonexistent", "default")
        self.assertEqual(value, "default")
        
        value = self.session_manager.get_user_preference("nonexistent")
        self.assertIsNone(value)
    
    def test_session_info(self):
        """Test getting session information."""
        # No session initially
        info = self.session_manager.get_session_info()
        self.assertIsNone(info)
        
        # Create session with data
        session = self.session_manager.create_new_session("info_test")
        session.user_preferences = {"theme": "dark"}
        session.recent_files = ["/file1.png", "/file2.csv"]
        
        info = self.session_manager.get_session_info()
        
        self.assertIsNotNone(info)
        if info is not None:
            self.assertEqual(info["session_id"], "info_test")
            self.assertIsNotNone(info["created_at"])
            self.assertIsNotNone(info["last_modified"])
            self.assertEqual(info["version"], "1.0")
            self.assertIsNone(info["file_path"])
            self.assertTrue(info["auto_save_enabled"])
            self.assertFalse(info["has_main_window_state"])
            self.assertEqual(info["ui_models_count"], 0)
            self.assertEqual(info["recent_files_count"], 2)
            self.assertEqual(info["preferences_count"], 1)
            self.assertEqual(info["analysis_results_count"], 0)
    
    def test_auto_save_configuration(self):
        """Test auto-save configuration."""
        # Disable auto-save
        self.session_manager.auto_save_enabled = False
        self.session_manager.auto_save_interval = 600
        
        self.assertFalse(self.session_manager.auto_save_enabled)
        self.assertEqual(self.session_manager.auto_save_interval, 600)
        
        # Re-enable auto-save
        self.session_manager.auto_save_enabled = True
        self.session_manager.auto_save_interval = 120
        
        self.assertTrue(self.session_manager.auto_save_enabled)
        self.assertEqual(self.session_manager.auto_save_interval, 120)
    
    def test_auto_save_behavior(self):
        """Test auto-save behavior when making changes."""
        # Disable auto-save for this test
        self.session_manager.auto_save_enabled = False
        
        # Make changes
        self.session_manager.set_user_preference("test", "value")
        
        # Session should exist but not be saved to file
        self.assertIsNotNone(self.session_manager.current_session)
        self.assertIsNone(self.session_manager.session_file_path)
        
        # Enable auto-save and make another change
        self.session_manager.auto_save_enabled = True
        self.session_manager.set_user_preference("test2", "value2")
        
        self.assertIsNotNone(self.session_manager.session_file_path)
        if self.session_manager.session_file_path is not None:
            self.assertTrue(self.session_manager.session_file_path.exists())
    
    def test_save_session_without_current_session(self):
        """Test saving when no current session exists."""
        success = self.session_manager.save_session()
        self.assertFalse(success)
    
    def test_clear_current_session(self):
        """Test clearing current session."""
        # Create session
        self.session_manager.create_new_session("test_clear")
        self.assertIsNotNone(self.session_manager.current_session)
        
        # Clear session
        self.session_manager.clear_current_session()
        self.assertIsNone(self.session_manager.current_session)
        self.assertIsNone(self.session_manager.session_file_path)


if __name__ == "__main__":
    unittest.main() 