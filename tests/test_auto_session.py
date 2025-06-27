"""
Tests for Auto-Session Loading System
"""

import pytest
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from PySide6.QtCore import QSettings

from src.models.auto_session import AutoSessionManager
from src.models.session_manager import SessionManager


@pytest.fixture
def mock_session_manager():
    """Create a mock session manager."""
    mock = Mock(spec=SessionManager)
    mock.save_session = Mock(return_value=True)
    mock.load_session = Mock(return_value={'data': {}})
    mock.get_recent_sessions = Mock(return_value=[])
    return mock


@pytest.fixture
def auto_session_manager(mock_session_manager, qtbot):
    """Create an auto-session manager for testing."""
    manager = AutoSessionManager(mock_session_manager)
    qtbot.addWidget(manager)
    return manager


@pytest.fixture
def temp_session_dir(tmp_path):
    """Create temporary session directory."""
    session_dir = tmp_path / '.cellsorter' / 'autosave'
    session_dir.mkdir(parents=True)
    return session_dir


class TestAutoSessionManager:
    """Test suite for AutoSessionManager."""
    
    def test_initialization(self, auto_session_manager):
        """Test manager initialization."""
        assert auto_session_manager.session_manager is not None
        assert auto_session_manager.auto_save_timer is not None
        assert auto_session_manager.current_session_data is None
        assert auto_session_manager.last_auto_save_path is None
    
    def test_auto_save_timer_start(self, auto_session_manager):
        """Test auto-save timer starts when enabled."""
        auto_session_manager.auto_save_enabled = True
        auto_session_manager.auto_save_interval = 1000  # 1 second
        
        auto_session_manager.start_auto_save()
        assert auto_session_manager.auto_save_timer.isActive()
        
        auto_session_manager.stop_auto_save()
        assert not auto_session_manager.auto_save_timer.isActive()
    
    def test_set_auto_save_interval(self, auto_session_manager):
        """Test setting auto-save interval."""
        auto_session_manager.set_auto_save_interval(5000)
        assert auto_session_manager.auto_save_interval == 5000
        
        # Test disabling with 0 interval
        auto_session_manager.set_auto_save_interval(0)
        assert not auto_session_manager.auto_save_timer.isActive()
    
    def test_update_session_data(self, auto_session_manager):
        """Test updating session data."""
        test_data = {'test': 'data'}
        auto_session_manager.update_session_data(test_data)
        assert auto_session_manager.current_session_data == test_data
    
    def test_get_recent_sessions(self, auto_session_manager, mock_session_manager):
        """Test getting recent sessions."""
        mock_sessions = [
            {'path': '/path/to/session1.cellsession', 'name': 'Session 1'},
            {'path': '/path/to/session2.cellsession', 'name': 'Session 2'}
        ]
        mock_session_manager.get_recent_sessions.return_value = mock_sessions
        
        sessions = auto_session_manager.get_recent_sessions()
        assert len(sessions) == 2
        assert sessions[0]['name'] == 'Session 1'
    
    def test_load_most_recent_session(self, auto_session_manager, mock_session_manager):
        """Test loading most recent session."""
        mock_sessions = [
            {'path': '/path/to/recent.cellsession', 'name': 'Recent Session'}
        ]
        mock_session_manager.get_recent_sessions.return_value = mock_sessions
        mock_session_manager.load_session.return_value = {'data': 'test'}
        
        result = auto_session_manager.load_most_recent_session()
        assert result is not None
        mock_session_manager.load_session.assert_called_once_with('/path/to/recent.cellsession')
    
    @patch('src.models.auto_session.Path')
    def test_create_session_backup(self, mock_path_class, auto_session_manager, tmp_path):
        """Test creating session backup."""
        # Create a test session file
        session_file = tmp_path / 'test.cellsession'
        session_file.write_text('test session data')
        
        # Mock Path behavior
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.parent = tmp_path
        mock_path.stem = 'test'
        mock_path.suffix = '.cellsession'
        mock_path_class.return_value = mock_path
        
        # Test backup creation
        with patch('shutil.copy2') as mock_copy:
            backup_path = auto_session_manager.create_session_backup(str(session_file))
            mock_copy.assert_called_once()
    
    def test_validate_session_integrity_valid(self, auto_session_manager, tmp_path):
        """Test validating a valid session file."""
        # Create valid session file
        session_data = {
            'version': '1.0',
            'data': {
                'selections': [],
                'calibration': {},
                'settings': {}
            }
        }
        session_file = tmp_path / 'valid.cellsession'
        session_file.write_text(json.dumps(session_data))
        
        assert auto_session_manager.validate_session_integrity(str(session_file)) is True
    
    def test_validate_session_integrity_invalid(self, auto_session_manager, tmp_path):
        """Test validating an invalid session file."""
        # Create invalid session file (missing required fields)
        session_data = {'version': '1.0'}
        session_file = tmp_path / 'invalid.cellsession'
        session_file.write_text(json.dumps(session_data))
        
        assert auto_session_manager.validate_session_integrity(str(session_file)) is False
    
    @patch('src.models.auto_session.Path.home')
    def test_perform_auto_save(self, mock_home, auto_session_manager, mock_session_manager, tmp_path):
        """Test performing auto-save."""
        mock_home.return_value = tmp_path
        
        # Set current session data
        test_data = {'test': 'auto-save data'}
        auto_session_manager.current_session_data = test_data
        
        # Perform auto-save
        auto_session_manager._perform_auto_save()
        
        # Check save was called
        assert mock_session_manager.save_session.called
        save_path = mock_session_manager.save_session.call_args[0][0]
        assert 'autosave_' in save_path
        assert save_path.endswith('.cellsession')
    
    @patch('src.models.auto_session.Path.home')
    def test_check_crash_recovery(self, mock_home, auto_session_manager, tmp_path, qtbot):
        """Test crash recovery detection."""
        mock_home.return_value = tmp_path
        auto_save_dir = tmp_path / '.cellsorter' / 'autosave'
        auto_save_dir.mkdir(parents=True)
        
        # Create a session file without clean marker (simulating crash)
        crash_session = auto_save_dir / 'autosave_20240101_120000.cellsession'
        crash_session.write_text('{}')
        
        # Set modification time to recent
        import os
        import time
        recent_time = time.time() - 3600  # 1 hour ago
        os.utime(crash_session, (recent_time, recent_time))
        
        # Check for crash recovery
        with qtbot.waitSignal(auto_session_manager.recovery_available, timeout=1000) as blocker:
            auto_session_manager._check_crash_recovery()
        
        assert len(blocker.args) == 1
        assert str(crash_session) in blocker.args[0]
    
    def test_session_available_signal(self, auto_session_manager, qtbot):
        """Test session available signal emission."""
        test_session = {
            'path': '/test/session.cellsession',
            'name': 'Test Session',
            'modified': datetime.now().isoformat()
        }
        
        with qtbot.waitSignal(auto_session_manager.session_available) as blocker:
            auto_session_manager.session_available.emit(test_session)
        
        assert blocker.args[0] == test_session
    
    def test_preferences_persistence(self, auto_session_manager):
        """Test that preferences are saved and loaded correctly."""
        # Set preferences
        auto_session_manager.set_auto_save_enabled(False)
        auto_session_manager.set_auto_save_interval(10000)
        auto_session_manager.set_auto_load_enabled(False)
        
        # Create new instance to test persistence
        new_manager = AutoSessionManager(auto_session_manager.session_manager)
        
        # Check preferences were loaded
        assert new_manager.auto_save_enabled == False
        assert new_manager.auto_save_interval == 10000
        assert new_manager.auto_load_enabled == False 