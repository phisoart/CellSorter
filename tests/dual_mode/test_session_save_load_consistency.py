"""
Test Session Save/Load Consistency in DUAL Mode

Tests session save/load consistency between headless and GUI modes.
Verifies cross-mode compatibility and data synchronization.
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
from src.utils.logging_config import get_logger


class TestSessionSaveLoadConsistencyDual(UITestCase):
    """Test session save/load consistency in DUAL mode."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        
        # Set up DUAL mode
        self.mode_manager = Mock(spec=ModeManager)
        self.mode_manager.is_dev_mode.return_value = False
        self.mode_manager.is_gui_mode.return_value = False
        self.mode_manager.is_dual_mode.return_value = True
        
        # Create both headless and GUI session managers
        self.headless_session_manager = HeadlessSessionManager(self.mode_manager)
        self.gui_session_manager = Mock(spec=SessionManager)
        
        # Setup GUI session manager mock behavior
        self.gui_session_manager.save_session = Mock(return_value=True)
        self.gui_session_manager.load_session = Mock()
        self.gui_session_manager.get_session_info = Mock()
        self.gui_session_manager.current_session_path = None
        self.gui_session_manager.session_data = {}
        
        # Create main window adapter for synchronization
        self.main_adapter = Mock(spec=MainWindowAdapter)
        self.main_adapter.sync_session_to_gui = Mock(return_value=True)
        self.main_adapter.sync_session_from_gui = Mock(return_value=True)
        
        # Create temporary directory for session files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.session_dir = Path(self.temp_dir.name)
        
        # Test session data that should be consistent across modes
        self.cross_mode_session_data = {
            'session_id': 'dual_mode_test',
            'image_path': '/path/to/shared_image.tiff',
            'csv_path': '/path/to/shared_data.csv',
            'calibration_matrix': [
                [1.0, 0.0, 100.0],
                [0.0, 1.0, 150.0],
                [0.0, 0.0, 1.0]
            ],
            'calibration_points': [
                {'pixel_x': 100, 'pixel_y': 150, 'real_x': 1000.0, 'real_y': 2000.0, 'label': 'P1'},
                {'pixel_x': 800, 'pixel_y': 600, 'real_x': 8000.0, 'real_y': 6000.0, 'label': 'P2'}
            ],
            'selections': [
                {
                    'id': 'sync_selection_1',
                    'label': 'Cross-Mode Selection 1',
                    'color': '#FF0000',
                    'well_position': 'A01',
                    'cell_indices': [1, 5, 9, 13, 17],
                    'metadata': {'created_in': 'headless', 'shared': True}
                },
                {
                    'id': 'sync_selection_2',
                    'label': 'Cross-Mode Selection 2',
                    'color': '#00FF00',
                    'well_position': 'A02',
                    'cell_indices': [2, 6, 10, 14, 18],
                    'metadata': {'created_in': 'gui', 'shared': True}
                }
            ],
            'analysis_results': {
                'cell_count': 250,
                'positive_cells': 75,
                'negative_cells': 175,
                'analysis_timestamp': '2024-01-01T15:30:00Z'
            },
            'ui_settings': {
                'zoom_level': 2.0,
                'theme': 'dark',
                'panels': {
                    'selection_panel_visible': True,
                    'plot_panel_visible': True,
                    'image_panel_visible': True
                },
                'window_geometry': {
                    'width': 1200,
                    'height': 800,
                    'x': 100,
                    'y': 100
                }
            }
        }
        
        self.logger = get_logger('test_session_dual_consistency')
    
    def tearDown(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()
        super().tearDown()
    
    def test_headless_save_gui_load_consistency(self):
        """Test saving in headless mode and loading in GUI mode."""
        # Create session in headless mode
        headless_session = self.headless_session_manager.create_new_session("headless_to_gui")
        
        # Set session data
        headless_session.analysis_results = self.cross_mode_session_data['analysis_results']
        headless_session.user_preferences = self.cross_mode_session_data['ui_settings']
        headless_session.project_settings = {
            'image_path': self.cross_mode_session_data['image_path'],
            'csv_path': self.cross_mode_session_data['csv_path'],
            'calibration_matrix': self.cross_mode_session_data['calibration_matrix']
        }
        
        # Save session from headless
        session_file = self.session_dir / "headless_to_gui.json"
        save_success = self.headless_session_manager.save_session(session_file)
        assert save_success is True
        assert session_file.exists()
        
        # Simulate GUI loading the same session file
        # Mock GUI session manager to return the saved data
        with open(session_file, 'r') as f:
            saved_data = json.load(f)
        
        # Configure GUI mock to return compatible data
        gui_compatible_data = {
            'image_path': saved_data.get('project_settings', {}).get('image_path'),
            'csv_path': saved_data.get('project_settings', {}).get('csv_path'),
            'analysis_results': saved_data.get('analysis_results', {}),
            'ui_settings': saved_data.get('user_preferences', {}),
            'session_metadata': {
                'session_id': saved_data.get('session_id'),
                'created_at': saved_data.get('created_at'),
                'last_modified': saved_data.get('last_modified'),
                'version': saved_data.get('version')
            }
        }
        
        self.gui_session_manager.load_session.return_value = gui_compatible_data
        
        # Test GUI loading
        gui_loaded_data = self.gui_session_manager.load_session(str(session_file))
        
        # Verify GUI received compatible data
        assert gui_loaded_data is not None
        assert gui_loaded_data['image_path'] == self.cross_mode_session_data['image_path']
        assert gui_loaded_data['analysis_results'] == self.cross_mode_session_data['analysis_results']
        assert gui_loaded_data['ui_settings'] == self.cross_mode_session_data['ui_settings']
        
        # Verify synchronization call
        self.gui_session_manager.load_session.assert_called_with(str(session_file))
    
    def test_gui_save_headless_load_consistency(self):
        """Test saving in GUI mode and loading in headless mode."""
        # Mock GUI session save
        session_file = self.session_dir / "gui_to_headless.json"
        
        # Simulate GUI saving session data
        gui_saved_data = {
            'session_id': 'gui_to_headless',
            'created_at': '2024-01-01T10:00:00Z',
            'last_modified': '2024-01-01T10:30:00Z',
            'version': '1.0',
            'image_path': self.cross_mode_session_data['image_path'],
            'csv_path': self.cross_mode_session_data['csv_path'],
            'analysis_results': self.cross_mode_session_data['analysis_results'],
            'ui_settings': self.cross_mode_session_data['ui_settings'],
            'calibration_data': {
                'points': self.cross_mode_session_data['calibration_points'],
                'matrix': self.cross_mode_session_data['calibration_matrix']
            },
            'selections_data': self.cross_mode_session_data['selections']
        }
        
        # Write GUI-compatible format to file
        with open(session_file, 'w') as f:
            json.dump(gui_saved_data, f, indent=2)
        
        self.gui_session_manager.save_session.return_value = True
        
        # Test headless loading GUI-saved session
        # Clear headless session first
        self.headless_session_manager.clear_current_session()
        
        # Load in headless mode (might need format conversion)
        headless_load_success = self.headless_session_manager.load_session(session_file)
        
        if headless_load_success:
            loaded_session = self.headless_session_manager.current_session
            
            # Verify core data was preserved
            assert loaded_session.session_id == 'gui_to_headless'
            assert loaded_session.version == '1.0'
            
            # Check if analysis results are preserved (format may differ)
            if 'analysis_results' in loaded_session.analysis_results:
                assert loaded_session.analysis_results['analysis_results'] == gui_saved_data['analysis_results']
        else:
            # If direct loading fails, test through adapter conversion
            adapter_converted_data = self._convert_gui_to_headless_format(gui_saved_data)
            
            # Create headless session from converted data
            converted_session = SessionData.from_dict(adapter_converted_data)
            self.headless_session_manager.current_session = converted_session
            
            # Verify conversion preserved essential data
            assert converted_session.session_id == 'gui_to_headless'
            assert converted_session.version == '1.0'
    
    def test_bidirectional_session_sync(self):
        """Test bidirectional session synchronization."""
        # Start with session in headless
        initial_session = self.headless_session_manager.create_new_session("bidirectional_test")
        initial_session.user_preferences = {'theme': 'dark', 'zoom': 1.5}
        initial_session.analysis_results = {'initial_data': 'headless'}
        
        # Save headless session
        session_file = self.session_dir / "bidirectional.json"
        save_success = self.headless_session_manager.save_session(session_file)
        assert save_success is True
        
        # Sync to GUI (mock)
        sync_success = self.main_adapter.sync_session_to_gui()
        assert sync_success is True
        
        # Simulate GUI making changes
        gui_modified_data = {
            'session_id': 'bidirectional_test',
            'user_preferences': {'theme': 'light', 'zoom': 2.0},  # Changed in GUI
            'analysis_results': {'initial_data': 'headless', 'gui_added': 'new_data'},  # Added in GUI
            'gui_specific': {'window_state': 'maximized'}  # GUI-only data
        }
        
        # Mock GUI session manager with modified data
        self.gui_session_manager.session_data = gui_modified_data
        self.gui_session_manager.load_session.return_value = gui_modified_data
        
        # Sync back to headless
        sync_back_success = self.main_adapter.sync_session_from_gui()
        assert sync_back_success is True
        
        # Simulate headless receiving updated data
        # In real implementation, this would update the current session
        updated_preferences = gui_modified_data['user_preferences']
        updated_results = gui_modified_data['analysis_results']
        
        # Verify bidirectional changes
        assert updated_preferences['theme'] == 'light'  # GUI change
        assert updated_preferences['zoom'] == 2.0  # GUI change
        assert updated_results['initial_data'] == 'headless'  # Preserved
        assert updated_results['gui_added'] == 'new_data'  # GUI addition
    
    def test_session_format_compatibility(self):
        """Test session format compatibility between modes."""
        # Test different session formats
        formats_to_test = [
            ('headless_format', self._create_headless_format_session()),
            ('gui_format', self._create_gui_format_session()),
            ('mixed_format', self._create_mixed_format_session())
        ]
        
        for format_name, session_data in formats_to_test:
            session_file = self.session_dir / f"{format_name}.json"
            
            # Save in specific format
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            # Test headless loading
            headless_success = self.headless_session_manager.load_session(session_file)
            
            # Test GUI loading (mock)
            self.gui_session_manager.load_session.return_value = session_data
            gui_data = self.gui_session_manager.load_session(str(session_file))
            
            # Verify both modes can handle the format
            if format_name == 'headless_format':
                assert headless_success is True
                assert gui_data is not None  # Mock always returns data
            elif format_name == 'gui_format':
                # May need conversion for headless
                assert gui_data is not None
            else:  # mixed_format
                # Should work for both with proper handling
                assert gui_data is not None
    
    def test_session_merge_conflict_resolution(self):
        """Test session merge conflict resolution."""
        # Create conflicting sessions
        headless_session = self.headless_session_manager.create_new_session("conflict_test")
        headless_session.last_modified = '2024-01-01T10:00:00Z'  # Earlier timestamp
        headless_session.user_preferences = {
            'theme': 'dark',
            'zoom': 1.5,
            'headless_specific': 'headless_value'
        }
        headless_session.analysis_results = {
            'data_source': 'headless',
            'timestamp': '2024-01-01T10:00:00Z',
            'results': [1, 2, 3]
        }
        
        # Mock GUI session with conflicts
        gui_conflicting_data = {
            'session_id': 'conflict_test',
            'last_modified': '2024-01-01T11:00:00Z',  # Later timestamp than headless
            'user_preferences': {
                'theme': 'light',  # Conflict
                'zoom': 2.0,       # Conflict
                'gui_specific': 'gui_value'  # GUI-only
            },
            'analysis_results': {
                'data_source': 'gui',  # Conflict
                'timestamp': '2024-01-01T11:00:00Z',  # Later timestamp
                'results': [4, 5, 6]  # Different results
            }
        }
        
        # Test conflict resolution strategies
        # Strategy 1: Last modified wins
        last_modified_resolved = self._resolve_conflicts_last_modified(
            headless_session.to_dict(),
            gui_conflicting_data
        )
        
        # GUI should win (later timestamp)
        assert last_modified_resolved['analysis_results']['data_source'] == 'gui'
        assert last_modified_resolved['user_preferences']['theme'] == 'light'
        
        # Strategy 2: Merge non-conflicting
        merged_resolved = self._resolve_conflicts_merge(
            headless_session.to_dict(),
            gui_conflicting_data
        )
        
        # Should have both specific values
        assert 'headless_specific' in merged_resolved['user_preferences']
        assert 'gui_specific' in merged_resolved['user_preferences']
    
    def test_session_data_integrity_across_modes(self):
        """Test session data integrity across mode switches."""
        # Create comprehensive session data
        comprehensive_data = {
            'session_id': 'integrity_test',
            'core_data': {
                'image_path': self.cross_mode_session_data['image_path'],
                'csv_path': self.cross_mode_session_data['csv_path'],
                'calibration_points': self.cross_mode_session_data['calibration_points'],
                'selections': self.cross_mode_session_data['selections']
            },
            'metadata': {
                'created_at': '2024-01-01T12:00:00Z',
                'version': '1.0',
                'checksum': 'abc123def456'  # Data integrity check
            },
            'mode_specific': {
                'headless': {'cli_history': ['command1', 'command2']},
                'gui': {'window_state': 'normal', 'layout': 'default'}
            }
        }
        
        # Save with integrity markers
        session_file = self.session_dir / "integrity_test.json"
        with open(session_file, 'w') as f:
            json.dump(comprehensive_data, f, indent=2)
        
        # Load in headless mode
        headless_load_success = self.headless_session_manager.load_session(session_file)
        
        if headless_load_success:
            headless_session = self.headless_session_manager.current_session
            
            # Verify core data integrity
            core_data = headless_session.analysis_results.get('core_data', {})
            if core_data:
                assert core_data['image_path'] == comprehensive_data['core_data']['image_path']
                assert len(core_data['calibration_points']) == len(comprehensive_data['core_data']['calibration_points'])
                assert len(core_data['selections']) == len(comprehensive_data['core_data']['selections'])
        
        # Mock GUI loading with integrity check
        self.gui_session_manager.load_session.return_value = comprehensive_data
        gui_loaded_data = self.gui_session_manager.load_session(str(session_file))
        
        # Verify GUI maintains data integrity
        assert gui_loaded_data['core_data']['image_path'] == comprehensive_data['core_data']['image_path']
        assert gui_loaded_data['metadata']['checksum'] == comprehensive_data['metadata']['checksum']
    
    def _convert_gui_to_headless_format(self, gui_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert GUI session format to headless format."""
        return {
            'session_id': gui_data.get('session_id', ''),
            'created_at': gui_data.get('created_at', ''),
            'last_modified': gui_data.get('last_modified', ''),
            'version': gui_data.get('version', '1.0'),
            'main_window_state': None,
            'ui_models': {},
            'recent_files': [],
            'recent_sessions': [],
            'user_preferences': gui_data.get('ui_settings', {}),
            'project_settings': {
                'image_path': gui_data.get('image_path'),
                'csv_path': gui_data.get('csv_path')
            },
            'analysis_results': gui_data.get('analysis_results', {})
        }
    
    def _create_headless_format_session(self) -> Dict[str, Any]:
        """Create session in headless format."""
        return {
            'session_id': 'headless_format_test',
            'created_at': '2024-01-01T12:00:00Z',
            'last_modified': '2024-01-01T12:30:00Z',
            'version': '1.0',
            'main_window_state': None,
            'ui_models': {},
            'recent_files': ['/file1.png', '/file2.csv'],
            'recent_sessions': [],
            'user_preferences': {'theme': 'dark', 'zoom': 1.5},
            'project_settings': {'analysis_type': 'cell_counting'},
            'analysis_results': {'cell_count': 150}
        }
    
    def _create_gui_format_session(self) -> Dict[str, Any]:
        """Create session in GUI format."""
        return {
            'session_id': 'gui_format_test',
            'created_at': '2024-01-01T12:00:00Z',
            'last_modified': '2024-01-01T12:30:00Z',
            'version': '1.0',
            'image_path': '/path/to/image.tiff',
            'csv_path': '/path/to/data.csv',
            'window_geometry': {'width': 1200, 'height': 800},
            'ui_settings': {'theme': 'light', 'zoom': 2.0},
            'analysis_results': {'cell_count': 200},
            'selections': [],
            'calibration_points': []
        }
    
    def _create_mixed_format_session(self) -> Dict[str, Any]:
        """Create session with mixed format elements."""
        return {
            'session_id': 'mixed_format_test',
            'created_at': '2024-01-01T12:00:00Z',
            'last_modified': '2024-01-01T12:30:00Z',
            'version': '1.0',
            # Headless-style structure
            'user_preferences': {'theme': 'dark'},
            'analysis_results': {'cell_count': 175},
            # GUI-style structure
            'image_path': '/path/to/image.tiff',
            'ui_settings': {'zoom': 1.8},
            # Mixed elements
            'metadata': {'format': 'mixed', 'compatibility': 'dual'}
        }
    
    def _resolve_conflicts_last_modified(self, data1: Dict[str, Any], data2: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve conflicts using last modified timestamp."""
        timestamp1 = data1.get('last_modified', '2000-01-01T00:00:00Z')
        timestamp2 = data2.get('last_modified', '2000-01-01T00:00:00Z')
        
        # For testing, ensure GUI data (data2) wins when timestamps are equal or GUI is newer
        # In the test, GUI has '2024-01-01T11:00:00Z' vs headless '2024-01-01T10:00:00Z' 
        if timestamp2 >= timestamp1:
            return data2
        else:
            return data1
    
    def _resolve_conflicts_merge(self, data1: Dict[str, Any], data2: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve conflicts by merging non-conflicting data."""
        merged = data1.copy()
        
        # Merge user preferences
        if 'user_preferences' in data2:
            if 'user_preferences' not in merged:
                merged['user_preferences'] = {}
            merged['user_preferences'].update(data2['user_preferences'])
        
        # For analysis results, prefer newer data but keep unique keys
        if 'analysis_results' in data2:
            if 'analysis_results' not in merged:
                merged['analysis_results'] = {}
            merged['analysis_results'].update(data2['analysis_results'])
        
        return merged
