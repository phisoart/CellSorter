"""
Headless Session Manager

Manages application sessions in headless mode, including UI state,
application settings, and user data persistence.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union, Callable
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict

from .main_window_adapter import MainWindowState
from .mode_manager import ModeManager
from .ui_model import UIModel, Widget

logger = logging.getLogger(__name__)


@dataclass
class SessionData:
    """Complete session data container."""
    
    # Session metadata
    session_id: str = ""
    created_at: str = ""
    last_modified: str = ""
    version: str = "1.0"
    
    # Application state
    main_window_state: Optional[Dict[str, Any]] = None
    ui_models: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # User data
    recent_files: List[str] = field(default_factory=list)
    recent_sessions: List[str] = field(default_factory=list)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    
    # Project data
    project_settings: Dict[str, Any] = field(default_factory=dict)
    analysis_results: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session data to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionData":
        """Create session data from dictionary."""
        return cls(**data)


class HeadlessSessionManager:
    """
    Manages headless UI development sessions.
    
    Features:
    - Session persistence and restoration
    - Command history tracking
    - State management
    - Multi-session support
    """
    
    def __init__(self, mode_manager: Optional[ModeManager] = None):
        """
        Initialize session manager.
        
        Args:
            mode_manager: Mode manager instance (creates new if None)
        """
        self.mode_manager = mode_manager or ModeManager()
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.active_session: Optional[str] = None
        self.command_history: List[Dict[str, Any]] = []
        self.session_dir = Path.home() / '.cellsorter' / 'sessions'
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Command callbacks
        self.command_callbacks: Dict[str, Callable] = {}
        
        # Load existing sessions
        self._load_sessions()
        
        self.current_session: Optional[SessionData] = None
        self.session_file_path: Optional[Path] = None
        self.auto_save_enabled: bool = True
        self.auto_save_interval: int = 300  # seconds
        
        logger.info("Session manager initialized")
    
    def create_new_session(self, session_id: Optional[str] = None) -> SessionData:
        """Create a new session."""
        if session_id is None:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        session = SessionData(
            session_id=session_id,
            created_at=datetime.now().isoformat(),
            last_modified=datetime.now().isoformat()
        )
        
        self.current_session = session
        logger.info(f"New session created: {session_id}")
        return session
    
    def save_session(self, file_path: Optional[Union[str, Path]] = None) -> bool:
        """Save current session to file."""
        if not self.current_session:
            logger.warning("No current session to save")
            return False
        
        if file_path is None:
            if self.session_file_path:
                file_path = self.session_file_path
            else:
                file_path = self.session_dir / f"{self.current_session.session_id}.json"
        
        file_path = Path(file_path)
        
        try:
            # Update last modified timestamp
            self.current_session.last_modified = datetime.now().isoformat()
            
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.current_session.to_dict(), f, indent=2, ensure_ascii=False)
            
            self.session_file_path = file_path
            logger.info(f"Session saved to: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
            return False
    
    def load_session(self, file_path: Union[str, Path]) -> bool:
        """Load session from file."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"Session file not found: {file_path}")
            return False
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            self.current_session = SessionData.from_dict(session_data)
            self.session_file_path = file_path
            
            logger.info(f"Session loaded from: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return False
    
    def save_main_window_state(self, state: MainWindowState) -> None:
        """Save main window state to current session."""
        if not self.current_session:
            self.create_new_session()
        
        if self.current_session:
            self.current_session.main_window_state = state.to_dict()
            logger.debug("Main window state saved to session")
            
            if self.auto_save_enabled:
                self.save_session()
    
    def load_main_window_state(self) -> Optional[MainWindowState]:
        """Load main window state from current session."""
        if not self.current_session or not self.current_session.main_window_state:
            return None
        
        try:
            return MainWindowState.from_dict(self.current_session.main_window_state)
        except Exception as e:
            logger.error(f"Failed to load main window state: {e}")
            return None
    
    def add_recent_file(self, file_path: str, max_recent: int = 10) -> None:
        """Add file to recent files list."""
        if not self.current_session:
            self.create_new_session()
        
        if self.current_session:
            # Remove if already exists
            if file_path in self.current_session.recent_files:
                self.current_session.recent_files.remove(file_path)
            
            # Add to beginning
            self.current_session.recent_files.insert(0, file_path)
            
            # Limit list size
            self.current_session.recent_files = self.current_session.recent_files[:max_recent]
            
            logger.debug(f"Added recent file: {file_path}")
            
            if self.auto_save_enabled:
                self.save_session()
    
    def get_recent_files(self) -> List[str]:
        """Get list of recent files."""
        if not self.current_session:
            return []
        
        # Filter out non-existent files
        existing_files = []
        for file_path in self.current_session.recent_files:
            if Path(file_path).exists():
                existing_files.append(file_path)
            else:
                logger.debug(f"Removing non-existent recent file: {file_path}")
        
        # Update list if changes were made
        if len(existing_files) != len(self.current_session.recent_files):
            self.current_session.recent_files = existing_files
            if self.auto_save_enabled:
                self.save_session()
        
        return existing_files
    
    def set_user_preference(self, key: str, value: Any) -> None:
        """Set user preference."""
        if not self.current_session:
            self.create_new_session()
        
        if self.current_session:
            self.current_session.user_preferences[key] = value
            logger.debug(f"Set user preference: {key} = {value}")
            
            if self.auto_save_enabled:
                self.save_session()
    
    def get_user_preference(self, key: str, default: Any = None) -> Any:
        """Get user preference."""
        if not self.current_session:
            return default
        
        return self.current_session.user_preferences.get(key, default)
    
    def get_session_info(self) -> Optional[Dict[str, Any]]:
        """Get information about current session."""
        if not self.current_session:
            return None
        
        return {
            "session_id": self.current_session.session_id,
            "created_at": self.current_session.created_at,
            "last_modified": self.current_session.last_modified,
            "version": self.current_session.version,
            "file_path": str(self.session_file_path) if self.session_file_path else None,
            "auto_save_enabled": self.auto_save_enabled,
            "has_main_window_state": self.current_session.main_window_state is not None,
            "ui_models_count": len(self.current_session.ui_models),
            "recent_files_count": len(self.current_session.recent_files),
            "preferences_count": len(self.current_session.user_preferences),
            "analysis_results_count": len(self.current_session.analysis_results)
        }
    
    def clear_current_session(self) -> None:
        """Clear current session from memory."""
        self.current_session = None
        self.session_file_path = None
        logger.info("Current session cleared")

    def _load_sessions(self):
        # Implementation of _load_sessions method
        pass
