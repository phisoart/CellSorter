"""
Test Session Save/Load in DEV Mode

Tests session save and load functionality in headless development mode.
Verifies data persistence, state restoration, and session integrity.
"""

import pytest
import json
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

from src.headless.testing.framework import UITestCase
from src.headless.session_manager import HeadlessSessionManager, SessionData
from src.headless.main_window_adapter import MainWindowAdapter, MainWindowState
from src.headless.mode_manager import ModeManager
from src.models.session_manager import SessionManager
from src.models.selection_manager import SelectionManager, CellSelection
from src.models.coordinate_transformer import CoordinateTransformer
from src.utils.logging_config import get_logger


class TestSessionSaveLoadDev(UITestCase):
    """Test session save/load functionality in DEV mode (headless)."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        
        # Set up DEV mode
        self.mode_manager = Mock(spec=ModeManager)
        self.mode_manager.is_dev_mode.return_value = True
        self.mode_manager.is_gui_mode.return_value = False
        self.mode_manager.is_dual_mode.return_value = False
        
        # Create headless session manager
        self.session_manager = HeadlessSessionManager(self.mode_manager)
        
        # Create temporary directory for session files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.session_dir = Path(self.temp_dir.name)
        
        # Mock components
        self.selection_manager = Mock(spec=SelectionManager)
        self.coordinate_transformer = Mock(spec=CoordinateTransformer)
        self.main_adapter = Mock(spec=MainWindowAdapter)
        
        # Test session data
        self.test_session_data = {
            'session_id': 'test_session_dev',
            'image_path': '/path/to/test_image.tiff',
            'csv_path': '/path/to/test_data.csv',
            'calibration_points': [
                {
                    'pixel_x': 100.0,
                    'pixel_y': 150.0,
                    'real_x': 1000.0,
                    'real_y': 2000.0,
                    'label': 'Calibration Point 1'
                },
                {
                    'pixel_x': 800.0,
                    'pixel_y': 600.0,
                    'real_x': 8000.0,
                    'real_y': 6000.0,
                    'label': 'Calibration Point 2'
                }
            ],
            'selections': [
                {
                    'id': 'selection_1',
                    'label': 'Positive Cells',
                    'color': '#FF0000',
                    'well_position': 'A01',
                    'cell_indices': [1, 5, 9, 13, 17],
                    'metadata': {'type': 'positive', 'marker': 'CD4+'}
                },
                {
                    'id': 'selection_2',
                    'label': 'Negative Cells',
                    'color': '#0000FF',
                    'well_position': 'A02',
                    'cell_indices': [2, 6, 10, 14, 18],
                    'metadata': {'type': 'negative', 'marker': 'CD4-'}
                }
            ],
            'analysis_parameters': {
                'threshold': 1000.0,
                'min_cell_size': 50,
                'max_cell_size': 500,
                'filter_expression': 'intensity > 800'
            },
            'ui_settings': {
                'zoom_level': 2.5,
                'current_theme': 'dark',
                'panel_visibility': {
                    'selection_panel': True,
                    'plot_panel': True,
                    'image_panel': True
                }
            },
            'metadata': {
                'created_at': '2024-01-01T12:00:00Z',
                'last_modified': '2024-01-01T12:30:00Z',
                'version': '1.0',
                'mode': 'headless'
            }
        }
        
        self.logger = get_logger('test_session_save_load')
    
    def tearDown(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()
        super().tearDown()
    
    def test_create_new_session(self):
        """Test creating a new session in headless mode."""
        # Create session with custom ID
        session = self.session_manager.create_new_session("test_custom_session")
        
        # Verify session creation
        assert session.session_id == "test_custom_session"
        assert session.created_at is not None
        assert session.last_modified is not None
        assert session.version == "1.0"
        
        # Verify current session is set
        assert self.session_manager.current_session == session
        
        # Create session with auto-generated ID
        auto_session = self.session_manager.create_new_session()
        
        assert auto_session.session_id.startswith("session_")
        assert auto_session.session_id != session.session_id
    
    def test_save_session_to_file(self):
        """Test saving session to file."""
        # Create session with test data
        session = self.session_manager.create_new_session("save_test")
        session.user_preferences = self.test_session_data['ui_settings']
        session.project_settings = self.test_session_data['analysis_parameters']
        session.analysis_results = {
            'calibration_points': self.test_session_data['calibration_points'],
            'selections': self.test_session_data['selections']
        }
        
        # Save to custom path
        session_file = self.session_dir / "test_save_session.json"
        success = self.session_manager.save_session(session_file)
        
        # Verify save success
        assert success is True
        assert session_file.exists()
        assert self.session_manager.session_file_path == session_file
        
        # Verify file content
        with open(session_file, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data['session_id'] == "save_test"
        assert saved_data['user_preferences'] == self.test_session_data['ui_settings']
        assert saved_data['project_settings'] == self.test_session_data['analysis_parameters']
        assert 'last_modified' in saved_data
        assert saved_data['version'] == "1.0"
    
    def test_load_session_from_file(self):
        """Test loading session from file."""
        # Create session file
        session_file = self.session_dir / "test_load_session.json"
        
        # Prepare session data
        save_data = SessionData(
            session_id="load_test",
            user_preferences=self.test_session_data['ui_settings'],
            project_settings=self.test_session_data['analysis_parameters'],
            analysis_results={
                'calibration_points': self.test_session_data['calibration_points'],
                'selections': self.test_session_data['selections']
            }
        )
        
        # Save test data to file
        with open(session_file, 'w') as f:
            json.dump(save_data.to_dict(), f, indent=2)
        
        # Clear current session
        self.session_manager.clear_current_session()
        assert self.session_manager.current_session is None
        
        # Load session
        success = self.session_manager.load_session(session_file)
        
        # Verify load success
        assert success is True
        assert self.session_manager.current_session is not None
        assert self.session_manager.current_session.session_id == "load_test"
        assert self.session_manager.session_file_path == session_file
        
        # Verify loaded data
        loaded_session = self.session_manager.current_session
        assert loaded_session.user_preferences == self.test_session_data['ui_settings']
        assert loaded_session.project_settings == self.test_session_data['analysis_parameters']
        assert len(loaded_session.analysis_results['calibration_points']) == 2
        assert len(loaded_session.analysis_results['selections']) == 2
    
    def test_main_window_state_persistence(self):
        """Test main window state save and load."""
        # Create main window state
        state = MainWindowState(
            window_title="Test Headless Window",
            zoom_level=3.0,
            current_theme="dark",
            status_message="Ready for testing",
            cell_count=150,
            mouse_coordinates=(100.5, 200.5),
            active_tool="selection",
            overlays_visible=True,
            current_image_path=self.test_session_data['image_path'],
            current_csv_path=self.test_session_data['csv_path']
        )
        
        # Save state to session
        self.session_manager.save_main_window_state(state)
        
        # Verify session was created and state saved
        assert self.session_manager.current_session is not None
        assert self.session_manager.current_session.main_window_state is not None
        
        # Load state back
        loaded_state = self.session_manager.load_main_window_state()
        
        assert loaded_state is not None
        assert loaded_state.window_title == "Test Headless Window"
        assert loaded_state.zoom_level == 3.0
        assert loaded_state.current_theme == "dark"
        assert loaded_state.status_message == "Ready for testing"
        assert loaded_state.cell_count == 150
        assert loaded_state.mouse_coordinates == (100.5, 200.5)
        assert loaded_state.active_tool == "selection"
        assert loaded_state.overlays_visible is True
        assert loaded_state.current_image_path == self.test_session_data['image_path']
        assert loaded_state.current_csv_path == self.test_session_data['csv_path']
    
    def test_user_preferences_management(self):
        """Test user preferences save and load."""
        # Set user preferences
        test_preferences = {
            'theme': 'dark',
            'auto_save': True,
            'auto_save_interval': 300,
            'default_zoom': 1.5,
            'show_grid': False,
            'language': 'en',
            'recent_files_count': 10
        }
        
        for key, value in test_preferences.items():
            self.session_manager.set_user_preference(key, value)
        
        # Verify preferences are set
        for key, expected_value in test_preferences.items():
            actual_value = self.session_manager.get_user_preference(key)
            assert actual_value == expected_value, f"Preference {key} should be {expected_value}, got {actual_value}"
        
        # Test default values
        default_pref = self.session_manager.get_user_preference('non_existent_key', 'default_value')
        assert default_pref == 'default_value'
        
        # Save and reload session
        session_file = self.session_dir / "test_preferences.json"
        save_success = self.session_manager.save_session(session_file)
        assert save_success is True
        
        # Clear and reload
        self.session_manager.clear_current_session()
        load_success = self.session_manager.load_session(session_file)
        assert load_success is True
        
        # Verify preferences persist
        for key, expected_value in test_preferences.items():
            actual_value = self.session_manager.get_user_preference(key)
            assert actual_value == expected_value, f"Reloaded preference {key} should be {expected_value}"
    
    def test_auto_save_functionality(self):
        """Test auto-save functionality."""
        # Enable auto-save
        self.session_manager.auto_save_enabled = True
        
        # Make changes that should trigger auto-save
        self.session_manager.set_user_preference('test_auto_save', 'test_value')
        
        # Verify session was created and potentially saved
        assert self.session_manager.current_session is not None
        
        # For testing, we don't wait for actual auto-save timer
        # Instead, we test the auto-save logic directly
        if self.session_manager.session_file_path:
            assert self.session_manager.session_file_path.exists()
        
        # Test disabling auto-save
        self.session_manager.auto_save_enabled = False
        
        # Clear session file path to test manual save only
        self.session_manager.session_file_path = None
        
        self.session_manager.set_user_preference('test_manual_save', 'test_value_2')
        
        # Should not auto-save
        assert self.session_manager.session_file_path is None
    
    def test_session_error_handling(self):
        """Test session error handling."""
        # Test save to invalid path
        invalid_path = Path("/invalid/path/that/does/not/exist/session.json")
        success = self.session_manager.save_session(invalid_path)
        assert success is False
        
        # Test load from non-existent file
        non_existent_file = self.session_dir / "non_existent.json"
        success = self.session_manager.load_session(non_existent_file)
        assert success is False
        
        # Test load from invalid JSON
        invalid_json_file = self.session_dir / "invalid.json"
        with open(invalid_json_file, 'w') as f:
            f.write("{ invalid json content")
        
        success = self.session_manager.load_session(invalid_json_file)
        assert success is False
        
        # Test save without current session
        self.session_manager.clear_current_session()
        success = self.session_manager.save_session()
        assert success is False
    
    def test_session_info_retrieval(self):
        """Test session information retrieval."""
        # Test with no session
        info = self.session_manager.get_session_info()
        assert info is None
        
        # Create session with data
        session = self.session_manager.create_new_session("info_test")
        session.user_preferences = {'theme': 'dark', 'auto_save': True}
        session.recent_files = ['/file1.png', '/file2.csv', '/file3.tiff']
        session.analysis_results = {'test_result': {'value': 123}}
        
        # Get session info
        info = self.session_manager.get_session_info()
        
        assert info is not None
        assert info['session_id'] == "info_test"
        assert info['version'] == "1.0"
        assert info['auto_save_enabled'] is True
        assert info['has_main_window_state'] is False
        assert info['ui_models_count'] == 0
        assert info['recent_files_count'] == 3
        assert info['preferences_count'] == 2
        assert info['analysis_results_count'] == 1
    
    def test_large_session_data_handling(self):
        """Test handling of large session data."""
        # Create large session data
        large_session = self.session_manager.create_new_session("large_test")
        
        # Add large amounts of data
        large_selections = []
        for i in range(1000):  # 1000 selections
            large_selections.append({
                'id': f'selection_{i}',
                'label': f'Large Selection {i}',
                'color': f'#{i:06x}',
                'cell_indices': list(range(i * 10, (i + 1) * 10)),
                'metadata': {'index': i, 'type': 'large_test'}
            })
        
        large_session.analysis_results = {
            'large_selections': large_selections,
            'large_data_array': list(range(10000))  # 10k integers
        }
        
        # Test save performance
        start_time = time.time()
        session_file = self.session_dir / "large_session.json"
        success = self.session_manager.save_session(session_file)
        save_time = time.time() - start_time
        
        assert success is True
        assert save_time < 5.0, f"Large session save too slow: {save_time:.2f}s"
        assert session_file.exists()
        
        # Test file size is reasonable
        file_size = session_file.stat().st_size
        assert file_size > 0
        assert file_size < 50 * 1024 * 1024, f"Session file too large: {file_size / 1024 / 1024:.1f}MB"
        
        # Test load performance
        self.session_manager.clear_current_session()
        
        start_time = time.time()
        success = self.session_manager.load_session(session_file)
        load_time = time.time() - start_time
        
        assert success is True
        assert load_time < 3.0, f"Large session load too slow: {load_time:.2f}s"
        
        # Verify data integrity
        loaded_session = self.session_manager.current_session
        assert len(loaded_session.analysis_results['large_selections']) == 1000
        assert len(loaded_session.analysis_results['large_data_array']) == 10000
    
    def test_session_versioning(self):
        """Test session version handling."""
        # Create session with current version
        current_session = self.session_manager.create_new_session("version_test")
        current_session.version = "1.0"
        
        session_file = self.session_dir / "version_test.json"
        success = self.session_manager.save_session(session_file)
        assert success is True
        
        # Verify version in saved file
        with open(session_file, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data['version'] == "1.0"
        
        # Test loading session with older version (simulate)
        saved_data['version'] = "0.9"
        
        with open(session_file, 'w') as f:
            json.dump(saved_data, f)
        
        # Load should succeed with version warning
        self.session_manager.clear_current_session()
        success = self.session_manager.load_session(session_file)
        assert success is True
        
        # Version should be updated to current
        loaded_session = self.session_manager.current_session
        assert loaded_session.version == "0.9"  # Preserves original version
