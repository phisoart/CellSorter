"""
Auto-Session Loading System for CellSorter

This module provides automatic session loading and recovery functionality,
enabling seamless workflow continuation and crash recovery.
"""

import json
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime, timedelta

from PySide6.QtCore import QObject, Signal, QTimer, QSettings
from utils.logging_config import LoggerMixin
from utils.exceptions import SessionError


class AutoSessionManager(QObject, LoggerMixin):
    """
    Manages automatic session loading and recovery.
    
    Features:
    - Automatic session detection on startup
    - Recent session list with quick access
    - Crash recovery and session restoration
    - Auto-save with configurable intervals
    - Session backup and versioning
    - User preference management
    """
    
    # Signals
    session_available = Signal(dict)  # Session info
    recovery_available = Signal(str)  # Recovery file path
    auto_save_completed = Signal(str)  # Auto-save path
    
    def __init__(self, session_manager, parent=None):
        super().__init__(parent)
        
        self.session_manager = session_manager
        self.settings = QSettings("CellSorter", "AutoSession")
        
        # Auto-save timer
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self._perform_auto_save)
        
        # Configuration
        self.auto_save_enabled = self.settings.value("auto_save_enabled", True, bool)
        self.auto_save_interval = self.settings.value("auto_save_interval", 300000, int)  # 5 minutes
        self.auto_load_enabled = self.settings.value("auto_load_enabled", True, bool)
        self.max_recent_sessions = self.settings.value("max_recent_sessions", 10, int)
        
        # State
        self.current_session_data: Optional[Dict[str, Any]] = None
        self.last_auto_save_path: Optional[str] = None
        self.recovery_session_path: Optional[str] = None
        
        self.log_info("Auto-session manager initialized")
    
    def initialize(self) -> None:
        """Initialize auto-session system on application startup."""
        # Check for crash recovery
        self._check_crash_recovery()
        
        # Start auto-save timer if enabled
        if self.auto_save_enabled:
            self.start_auto_save()
        
        # Check for recent sessions if auto-load is enabled
        if self.auto_load_enabled:
            self._check_recent_sessions()
    
    def start_auto_save(self) -> None:
        """Start auto-save timer."""
        if self.auto_save_enabled and self.auto_save_interval > 0:
            self.auto_save_timer.start(self.auto_save_interval)
            self.log_info(f"Auto-save started with interval: {self.auto_save_interval/1000}s")
    
    def stop_auto_save(self) -> None:
        """Stop auto-save timer."""
        self.auto_save_timer.stop()
        self.log_info("Auto-save stopped")
    
    def set_auto_save_interval(self, interval_ms: int) -> None:
        """
        Set auto-save interval.
        
        Args:
            interval_ms: Interval in milliseconds (0 to disable)
        """
        self.auto_save_interval = interval_ms
        self.settings.setValue("auto_save_interval", interval_ms)
        
        if self.auto_save_timer.isActive():
            self.auto_save_timer.stop()
            if interval_ms > 0:
                self.auto_save_timer.start(interval_ms)
    
    def set_auto_save_enabled(self, enabled: bool) -> None:
        """
        Enable or disable auto-save.
        
        Args:
            enabled: Whether to enable auto-save
        """
        self.auto_save_enabled = enabled
        self.settings.setValue("auto_save_enabled", enabled)
        
        if enabled:
            self.start_auto_save()
        else:
            self.stop_auto_save()
    
    def set_auto_load_enabled(self, enabled: bool) -> None:
        """
        Enable or disable auto-load on startup.
        
        Args:
            enabled: Whether to enable auto-load
        """
        self.auto_load_enabled = enabled
        self.settings.setValue("auto_load_enabled", enabled)
    
    def update_session_data(self, session_data: Dict[str, Any]) -> None:
        """
        Update current session data for auto-save.
        
        Args:
            session_data: Current session data
        """
        self.current_session_data = session_data
    
    def get_recent_sessions(self) -> List[Dict[str, Any]]:
        """
        Get list of recent sessions with metadata.
        
        Returns:
            List of recent session information
        """
        return self.session_manager.get_recent_sessions(self.max_recent_sessions)
    
    def load_most_recent_session(self) -> Optional[Dict[str, Any]]:
        """
        Load the most recent session.
        
        Returns:
            Session data if successful, None otherwise
        """
        recent_sessions = self.get_recent_sessions()
        
        if recent_sessions:
            most_recent = recent_sessions[0]
            session_path = most_recent['path']
            
            self.log_info(f"Loading most recent session: {session_path}")
            return self.session_manager.load_session(session_path)
        
        return None
    
    def create_session_backup(self, session_path: str) -> Optional[str]:
        """
        Create a backup of the current session.
        
        Args:
            session_path: Path to current session file
        
        Returns:
            Path to backup file if successful, None otherwise
        """
        try:
            session_file = Path(session_path)
            if not session_file.exists():
                return None
            
            # Create backup directory
            backup_dir = session_file.parent / 'backups'
            backup_dir.mkdir(exist_ok=True)
            
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{session_file.stem}_backup_{timestamp}{session_file.suffix}"
            backup_path = backup_dir / backup_name
            
            # Copy session file to backup
            import shutil
            shutil.copy2(session_file, backup_path)
            
            # Clean up old backups (keep last 10)
            self._cleanup_old_backups(backup_dir, session_file.stem, keep_count=10)
            
            self.log_info(f"Created session backup: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            self.log_error(f"Failed to create session backup: {e}")
            return None
    
    def validate_session_integrity(self, session_path: str) -> bool:
        """
        Validate session file integrity.
        
        Args:
            session_path: Path to session file
        
        Returns:
            True if valid, False otherwise
        """
        try:
            with open(session_path, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Basic validation
            if 'version' not in session_data or 'data' not in session_data:
                return False
            
            # Check for required data fields
            data = session_data.get('data', {})
            required_fields = ['selections', 'calibration', 'settings']
            
            for field in required_fields:
                if field not in data:
                    return False
            
            return True
            
        except Exception as e:
            self.log_error(f"Session validation failed: {e}")
            return False
    
    def _perform_auto_save(self) -> None:
        """Perform auto-save of current session."""
        if not self.current_session_data:
            return
        
        try:
            # Create auto-save directory
            auto_save_dir = Path.home() / '.cellsorter' / 'autosave'
            auto_save_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate auto-save filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            auto_save_path = auto_save_dir / f"autosave_{timestamp}.cellsession"
            
            # Save session
            if self.session_manager.save_session(str(auto_save_path), self.current_session_data):
                self.last_auto_save_path = str(auto_save_path)
                self.auto_save_completed.emit(str(auto_save_path))
                
                # Mark as non-crash session
                self._mark_clean_shutdown(str(auto_save_path))
                
                # Cleanup old auto-saves
                self._cleanup_old_auto_saves(auto_save_dir)
            
        except Exception as e:
            self.log_error(f"Auto-save failed: {e}")
    
    def _check_crash_recovery(self) -> None:
        """Check for crash recovery sessions."""
        try:
            auto_save_dir = Path.home() / '.cellsorter' / 'autosave'
            if not auto_save_dir.exists():
                return
            
            # Look for sessions without clean shutdown marker
            for session_file in auto_save_dir.glob("autosave_*.cellsession"):
                marker_file = session_file.with_suffix('.clean')
                
                if not marker_file.exists():
                    # This is a potential crash recovery session
                    # Check if it's recent (within last 24 hours)
                    stat = session_file.stat()
                    age = datetime.now() - datetime.fromtimestamp(stat.st_mtime)
                    
                    if age < timedelta(days=1):
                        self.recovery_session_path = str(session_file)
                        self.recovery_available.emit(str(session_file))
                        self.log_info(f"Crash recovery session found: {session_file}")
                        break
            
        except Exception as e:
            self.log_error(f"Failed to check crash recovery: {e}")
    
    def _check_recent_sessions(self) -> None:
        """Check for recent sessions to auto-load."""
        recent_sessions = self.get_recent_sessions()
        
        if recent_sessions:
            # Get the most recent session
            most_recent = recent_sessions[0]
            
            # Check if it's recent enough (within last 7 days)
            try:
                modified_time = datetime.fromisoformat(most_recent['modified'])
                age = datetime.now() - modified_time
                
                if age < timedelta(days=7):
                    self.session_available.emit(most_recent)
                    self.log_info(f"Recent session available: {most_recent['name']}")
            except:
                pass
    
    def _mark_clean_shutdown(self, session_path: str) -> None:
        """Mark session as cleanly shut down."""
        try:
            marker_file = Path(session_path).with_suffix('.clean')
            marker_file.touch()
        except Exception as e:
            self.log_warning(f"Failed to mark clean shutdown: {e}")
    
    def _cleanup_old_auto_saves(self, auto_save_dir: Path, keep_count: int = 5) -> None:
        """Clean up old auto-save files."""
        try:
            auto_save_files = list(auto_save_dir.glob("autosave_*.cellsession"))
            auto_save_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            
            # Remove old files and their markers
            for old_file in auto_save_files[keep_count:]:
                old_file.unlink()
                marker_file = old_file.with_suffix('.clean')
                if marker_file.exists():
                    marker_file.unlink()
                self.log_info(f"Removed old auto-save: {old_file}")
                
        except Exception as e:
            self.log_warning(f"Failed to cleanup auto-saves: {e}")
    
    def _cleanup_old_backups(self, backup_dir: Path, session_stem: str, keep_count: int) -> None:
        """Clean up old backup files."""
        try:
            backup_files = list(backup_dir.glob(f"{session_stem}_backup_*.cellsession"))
            backup_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            
            # Remove old backups
            for old_backup in backup_files[keep_count:]:
                old_backup.unlink()
                self.log_info(f"Removed old backup: {old_backup}")
                
        except Exception as e:
            self.log_warning(f"Failed to cleanup backups: {e}") 