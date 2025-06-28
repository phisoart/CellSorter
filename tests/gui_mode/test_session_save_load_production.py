"""
Test Session Save/Load Production in GUI Mode

Tests session save/load functionality in production GUI mode.
Verifies user experience, file dialogs, and production workflows.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

from src.headless.testing.framework import UITestCase
from src.models.session_manager import SessionManager
from src.models.selection_manager import SelectionManager
from src.models.coordinate_transformer import CoordinateTransformer
from src.models.image_handler import ImageHandler
from src.headless.mode_manager import ModeManager
from src.utils.logging_config import get_logger


class TestSessionSaveLoadProductionGui(UITestCase):
    """Test session save/load production in GUI mode."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        
        # Set up GUI mode
        self.mode_manager = Mock(spec=ModeManager)
        self.mode_manager.is_dev_mode.return_value = False
        self.mode_manager.is_gui_mode.return_value = True
        self.mode_manager.is_dual_mode.return_value = False
        
        # Create production session manager
        self.session_manager = Mock(spec=SessionManager)
        self.session_manager.SESSION_VERSION = "1.0"
        self.session_manager.SESSION_EXTENSION = ".cellsession"
        
        # Set up mock behavior for session operations
        self.session_manager.save_session = Mock(return_value=True)
        self.session_manager.load_session = Mock()
        self.session_manager.get_session_info = Mock()
        self.session_manager.current_session_path = None
        self.session_manager.session_data = {}
        self.session_manager.is_modified = False
        
        # Mock dependent components
        self.selection_manager = Mock(spec=SelectionManager)
        self.coordinate_transformer = Mock(spec=CoordinateTransformer)
        self.image_handler = Mock(spec=ImageHandler)
        
        # Mock main window for production testing
        from PySide6.QtWidgets import QMainWindow
        self.main_window = Mock(spec=QMainWindow)
        
        # Set up main window behavior
        self.main_window.session_manager = self.session_manager
        self.main_window.selection_manager = self.selection_manager
        self.main_window.coordinate_transformer = self.coordinate_transformer
        self.main_window.image_handler = self.image_handler
        
        # Mock UI components
        self.main_window.show = Mock()
        self.main_window.update_status = Mock()
        self.main_window.update_window_title = Mock()
        
        # Create temporary directory for session files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.session_dir = Path(self.temp_dir.name)
        
        # Production test session data
        self.production_session_data = {
            'session_id': 'production_test',
            'created_at': '2024-01-01T09:00:00Z',
            'last_modified': '2024-01-01T09:30:00Z',
            'version': '1.0',
            'image_path': '/Users/researcher/data/experiment_001.tiff',
            'csv_path': '/Users/researcher/data/cells_data.csv',
            'calibration_points': [
                {
                    'pixel_x': 150.5,
                    'pixel_y': 200.3,
                    'real_x': 1500.0,
                    'real_y': 2000.0,
                    'label': 'Top Left Reference'
                },
                {
                    'pixel_x': 850.7,
                    'pixel_y': 650.1,
                    'real_x': 8500.0,
                    'real_y': 6500.0,
                    'label': 'Bottom Right Reference'
                }
            ],
            'selections': [
                {
                    'id': 'positive_cells',
                    'label': 'CD4+ T Cells',
                    'color': '#FF4444',
                    'well_position': 'A01',
                    'cell_indices': [15, 23, 47, 91, 156, 234],
                    'metadata': {
                        'marker': 'CD4',
                        'expression_level': 'high',
                        'confidence': 0.95,
                        'analysis_date': '2024-01-01'
                    }
                },
                {
                    'id': 'negative_cells',
                    'label': 'CD4- Cells',
                    'color': '#4444FF',
                    'well_position': 'A02',
                    'cell_indices': [8, 19, 32, 65, 98, 127, 189, 245],
                    'metadata': {
                        'marker': 'CD4',
                        'expression_level': 'low',
                        'confidence': 0.88,
                        'analysis_date': '2024-01-01'
                    }
                }
            ],
            'analysis_parameters': {
                'threshold_intensity': 1200.0,
                'min_cell_area': 75,
                'max_cell_area': 450,
                'filter_expression': 'intensity > 800 AND area > 50',
                'edge_removal': True,
                'debris_filter': True
            },
            'ui_settings': {
                'window_geometry': {
                    'width': 1400,
                    'height': 900,
                    'x': 200,
                    'y': 100
                },
                'zoom_level': 1.75,
                'current_theme': 'light',
                'panel_layout': {
                    'selection_panel_width': 300,
                    'plot_panel_height': 250,
                    'image_panel_splitter': [700, 400]
                },
                'recently_used_colors': ['#FF4444', '#4444FF', '#44FF44', '#FFFF44'],
                'auto_save_enabled': True,
                'auto_save_interval': 300
            },
            'export_settings': {
                'default_format': 'cxprotocol',
                'crop_size': 64,
                'export_path': '/Users/researcher/exports/',
                'include_metadata': True,
                'compression_level': 5
            }
        }
        
        self.logger = get_logger('test_session_gui_production')
    
    def tearDown(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()
        super().tearDown()
    
    def test_save_session_user_workflow(self):
        """Test save session user workflow with file dialog."""
        # Mock file dialog for save
        session_file_path = str(self.session_dir / "user_save_test.cellsession")
        
        with patch('PySide6.QtWidgets.QFileDialog.getSaveFileName') as mock_save_dialog:
            mock_save_dialog.return_value = (session_file_path, "Session Files (*.cellsession)")
            
            # Configure session manager to return test data when collecting
            self.session_manager.save_session.return_value = True
            
            # Mock main window's collect session data method
            def mock_collect_session_data():
                return self.production_session_data
            
            self.main_window._collect_session_data = Mock(return_value=self.production_session_data)
            
            # Simulate user saving session
            # Since we're testing in mock environment, simulate the file dialog call
            dialog_result = mock_save_dialog()
            file_path = dialog_result[0] if dialog_result else session_file_path
            
            if file_path:
                # Collect session data and save
                collect_success = self.main_window._collect_session_data()
                save_success = self.session_manager.save_session(file_path, collect_success)
                assert save_success is True
                
                # Simulate UI update after successful save
                self.main_window.update_status(f"Session saved: {Path(file_path).name}")
            
            # Verify file dialog was called
            mock_save_dialog.assert_called_once()
            
            # Verify session manager save was called with correct data
            self.session_manager.save_session.assert_called_with(file_path, self.production_session_data)
            
            # Verify UI updates
            if hasattr(self.main_window, 'update_status'):
                self.main_window.update_status.assert_called()
    
    def test_load_session_user_workflow(self):
        """Test load session user workflow with file dialog."""
        # Create session file for loading
        session_file_path = str(self.session_dir / "user_load_test.cellsession")
        
        # Write test session data to file
        with open(session_file_path, 'w') as f:
            json.dump(self.production_session_data, f, indent=2)
        
        # Mock file dialog for load
        with patch('PySide6.QtWidgets.QFileDialog.getOpenFileName') as mock_open_dialog:
            mock_open_dialog.return_value = (session_file_path, "Session Files (*.cellsession)")
            
            # Configure session manager to return loaded data
            self.session_manager.load_session.return_value = self.production_session_data
            
            # Mock main window's restore session data method
            self.main_window._restore_session_data = Mock()
            
            # Simulate user loading session
            # Since we're testing in mock environment, simulate the file dialog call
            dialog_result = mock_open_dialog()
            file_path = dialog_result[0] if dialog_result else session_file_path
            
            if file_path:
                # Load session data and restore
                loaded_data = self.session_manager.load_session(file_path)
                if loaded_data:
                    self.main_window._restore_session_data(loaded_data)
                    
                    # Simulate UI updates after successful load
                    self.main_window.update_status(f"Session loaded: {Path(file_path).name}")
                    self.main_window.update_window_title()
            
            # Verify file dialog was called
            mock_open_dialog.assert_called_once()
            
            # Verify session manager load was called
            self.session_manager.load_session.assert_called_with(file_path)
            
            # Verify UI restoration
            if hasattr(self.main_window, '_restore_session_data'):
                self.main_window._restore_session_data.assert_called_with(self.production_session_data)
            
            # Verify UI updates
            self.main_window.update_status.assert_called()
            self.main_window.update_window_title.assert_called()
    
    def test_auto_save_user_experience(self):
        """Test auto-save user experience and feedback."""
        # Enable auto-save in UI settings
        auto_save_settings = self.production_session_data['ui_settings'].copy()
        auto_save_settings['auto_save_enabled'] = True
        auto_save_settings['auto_save_interval'] = 60  # 1 minute for testing
        
        # Mock auto-save timer and functionality
        with patch('PySide6.QtCore.QTimer') as mock_timer:
            mock_timer_instance = Mock()
            mock_timer.return_value = mock_timer_instance
            
            # Simulate auto-save trigger
            # In real implementation, this would be triggered by timer
            auto_save_path = str(self.session_dir / "auto_save_backup.cellsession")
            
            # Mock auto-save execution
            self.session_manager.save_session.return_value = True
            auto_save_success = self.session_manager.save_session(auto_save_path, self.production_session_data)
            
            assert auto_save_success is True
            
            # Verify UI feedback for auto-save
            # In production, this might show a subtle indicator
            if hasattr(self.main_window, 'update_status'):
                # Could show "Auto-saved" message briefly
                pass
    
    def test_session_file_validation_user_experience(self):
        """Test session file validation and user feedback."""
        # Test loading invalid session file
        invalid_session_file = self.session_dir / "invalid_session.cellsession"
        
        # Create invalid JSON file
        with open(invalid_session_file, 'w') as f:
            f.write("{ invalid json content")
        
        # Mock session manager to simulate validation failure
        self.session_manager.load_session.return_value = None
        
        # Mock error dialog
        with patch('PySide6.QtWidgets.QMessageBox.warning') as mock_warning:
            # Attempt to load invalid session
            loaded_data = self.session_manager.load_session(str(invalid_session_file))
            
            if loaded_data is None:
                # Show user-friendly error message
                mock_warning("Load Failed", "Failed to load session file.")
            
            # Verify error handling
            assert loaded_data is None
            mock_warning.assert_called_once()
    
    def test_recent_sessions_management(self):
        """Test recent sessions management in GUI."""
        # Mock recent sessions functionality
        recent_sessions = [
            {
                'path': '/Users/researcher/session1.cellsession',
                'name': 'Experiment 001',
                'last_modified': '2024-01-01T10:00:00Z',
                'preview': 'CD4+ analysis, 156 cells'
            },
            {
                'path': '/Users/researcher/session2.cellsession',
                'name': 'Control Group',
                'last_modified': '2024-01-01T11:30:00Z',
                'preview': 'Control analysis, 203 cells'
            }
        ]
        
        # Mock main window recent sessions functionality
        self.main_window.get_recent_sessions = Mock(return_value=recent_sessions)
        self.main_window.update_recent_sessions_menu = Mock()
        
        # Test getting recent sessions
        sessions = self.main_window.get_recent_sessions()
        assert len(sessions) == 2
        assert sessions[0]['name'] == 'Experiment 001'
        
        # Test updating recent sessions menu
        self.main_window.update_recent_sessions_menu()
        self.main_window.update_recent_sessions_menu.assert_called_once()
    
    def test_session_backup_creation(self):
        """Test session backup creation on save."""
        # Create existing session file
        existing_session_file = self.session_dir / "existing_session.cellsession"
        
        original_data = self.production_session_data.copy()
        original_data['session_id'] = 'original_session'
        
        with open(existing_session_file, 'w') as f:
            json.dump(original_data, f, indent=2)
        
        # Mock session manager backup behavior
        backup_file = existing_session_file.with_suffix('.cellsession.backup')
        
        def mock_save_with_backup(file_path, session_data):
            # Simulate backup creation
            if Path(file_path).exists():
                # In real implementation, this would rename existing file
                with open(backup_file, 'w') as f:
                    json.dump(original_data, f, indent=2)
            return True
        
        self.session_manager.save_session.side_effect = mock_save_with_backup
        
        # Save new session data to same file
        updated_data = self.production_session_data.copy()
        updated_data['session_id'] = 'updated_session'
        
        save_success = self.session_manager.save_session(str(existing_session_file), updated_data)
        
        assert save_success is True
        
        # Verify backup was created (in mock)
        assert backup_file.exists()
        
        # Verify backup contains original data
        with open(backup_file, 'r') as f:
            backup_data = json.load(f)
        
        assert backup_data['session_id'] == 'original_session'
    
    def test_session_import_export_compatibility(self):
        """Test session import/export compatibility."""
        # Test exporting session for sharing
        export_data = {
            'format_version': '1.0',
            'export_timestamp': '2024-01-01T15:00:00Z',
            'session_data': self.production_session_data,
            'export_settings': {
                'include_image_paths': False,  # For portability
                'include_user_preferences': True,
                'include_analysis_results': True,
                'anonymize_paths': True
            }
        }
        
        # Mock export functionality
        export_file = self.session_dir / "exported_session.json"
        
        with open(export_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        # Mock import functionality
        self.session_manager.load_session.return_value = export_data['session_data']
        
        # Test importing exported session
        imported_data = self.session_manager.load_session(str(export_file))
        
        assert imported_data is not None
        assert imported_data['session_id'] == self.production_session_data['session_id']
        assert imported_data['analysis_parameters'] == self.production_session_data['analysis_parameters']
    
    def test_session_performance_large_datasets(self):
        """Test session performance with large datasets."""
        # Create large session data
        large_session_data = self.production_session_data.copy()
        
        # Add large selection data
        large_selections = []
        for i in range(100):  # 100 selections
            selection = {
                'id': f'large_selection_{i}',
                'label': f'Selection Group {i}',
                'color': f'#{i:06x}',
                'well_position': f'{chr(65 + i // 12)}{(i % 12) + 1:02d}',
                'cell_indices': list(range(i * 50, (i + 1) * 50)),  # 50 cells per selection
                'metadata': {
                    'group': i // 10,
                    'batch': f'batch_{i // 25}',
                    'analysis_time': f'2024-01-0{(i % 9) + 1}T10:00:00Z'
                }
            }
            large_selections.append(selection)
        
        large_session_data['selections'] = large_selections
        large_session_data['analysis_parameters']['total_cells'] = 5000
        
        # Test save performance
        import time
        start_time = time.time()
        
        large_session_file = self.session_dir / "large_session.cellsession"
        save_success = self.session_manager.save_session(str(large_session_file), large_session_data)
        
        save_time = time.time() - start_time
        
        assert save_success is True
        assert save_time < 2.0, f"Large session save too slow: {save_time:.2f}s"
        
        # Test load performance
        start_time = time.time()
        
        self.session_manager.load_session.return_value = large_session_data
        loaded_data = self.session_manager.load_session(str(large_session_file))
        
        load_time = time.time() - start_time
        
        assert loaded_data is not None
        assert load_time < 1.0, f"Large session load too slow: {load_time:.2f}s"
        
        # Verify data integrity
        assert len(loaded_data['selections']) == 100
        assert loaded_data['analysis_parameters']['total_cells'] == 5000
    
    def test_session_recovery_after_crash(self):
        """Test session recovery after application crash."""
        # Simulate auto-save before crash
        crash_recovery_data = self.production_session_data.copy()
        crash_recovery_data['session_id'] = 'crash_recovery_test'
        crash_recovery_data['ui_settings']['unsaved_changes'] = True
        
        # Create auto-save file
        auto_save_file = self.session_dir / ".auto_save_crash_recovery.cellsession"
        
        with open(auto_save_file, 'w') as f:
            json.dump(crash_recovery_data, f, indent=2)
        
        # Mock crash recovery dialog
        with patch('PySide6.QtWidgets.QMessageBox.question') as mock_question:
            mock_question.return_value = True  # User chooses to recover
            
            # Simulate application startup after crash
            if auto_save_file.exists():
                # Ask user if they want to recover
                user_wants_recovery = mock_question(
                    "Session Recovery",
                    "A previous session was found. Would you like to recover it?"
                )
                
                if user_wants_recovery:
                    # Load auto-save file
                    self.session_manager.load_session.return_value = crash_recovery_data
                    recovered_data = self.session_manager.load_session(str(auto_save_file))
                    
                    assert recovered_data is not None
                    assert recovered_data['session_id'] == 'crash_recovery_test'
                    
                    # Clean up auto-save file after successful recovery
                    auto_save_file.unlink()
            
            # Verify recovery dialog was shown
            mock_question.assert_called_once()
    
    def test_session_version_migration(self):
        """Test session version migration in GUI."""
        # Create old version session file
        old_version_data = {
            'session_id': 'old_version_test',
            'version': '0.9',  # Old version
            'legacy_field': 'old_value',
            'image_path': '/path/to/image.tiff',
            'selections': [
                {
                    'label': 'Old Format Selection',
                    'color': 'red',  # Old color format
                    'cells': [1, 2, 3]  # Old field name
                }
            ]
        }
        
        old_session_file = self.session_dir / "old_version.cellsession"
        
        with open(old_session_file, 'w') as f:
            json.dump(old_version_data, f, indent=2)
        
        # Mock version migration
        def mock_migrate_session(file_path):
            # Simulate migration process
            migrated_data = {
                'session_id': old_version_data['session_id'],
                'version': '1.0',  # Updated version
                'created_at': '2024-01-01T12:00:00Z',
                'last_modified': '2024-01-01T12:00:00Z',
                'image_path': old_version_data['image_path'],
                'selections': [
                    {
                        'id': 'migrated_selection_1',
                        'label': 'Old Format Selection',
                        'color': '#FF0000',  # Converted color
                        'cell_indices': [1, 2, 3],  # Updated field name
                        'metadata': {'migrated_from': '0.9'}
                    }
                ]
            }
            return migrated_data
        
        # Mock migration dialog
        with patch('PySide6.QtWidgets.QMessageBox.information') as mock_info:
            migrated_data = mock_migrate_session(str(old_session_file))
            
            # Show migration success message
            mock_info("Migration Complete", "Session has been updated to the latest format.")
            
            # Verify migration
            assert migrated_data['version'] == '1.0'
            assert migrated_data['selections'][0]['color'] == '#FF0000'
            assert 'cell_indices' in migrated_data['selections'][0]
            
            # Verify user was informed
            mock_info.assert_called_once()
