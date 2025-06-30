"""
DEPRECATED: Headless Session Manager for CellSorter

This module has been deprecated and removed from the CellSorter application.
Session management functionality has been removed as per design specification changes.

DO NOT USE THIS MODULE IN NEW DEVELOPMENT.

The CellSorter application now uses a simplified direct file workflow:
Start → Open Image → Open CSV → Work → Export Protocol → Exit

No session persistence is maintained between application runs.
"""

# This entire module is deprecated and should not be used
# Session management functionality has been removed from CellSorter
# as specified in docs/design/DESIGN_SPEC.md

from typing import Optional, Dict, Any, Union
from pathlib import Path
from datetime import datetime
import json
import uuid
from dataclasses import dataclass, field

from utils.logging_config import LoggerMixin


@dataclass
class SessionData:
    """DEPRECATED: Session data structure - no longer used."""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_modified: str = field(default_factory=lambda: datetime.now().isoformat())
    version: str = "1.0"
    
    # DEPRECATED fields - maintained for compatibility only
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    project_settings: Dict[str, Any] = field(default_factory=dict)
    main_window_state: Optional[Dict[str, Any]] = None
    ui_models: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    recent_files: list = field(default_factory=list)
    analysis_results: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary - deprecated functionality."""
        return {
            'session_id': self.session_id,
            'created_at': self.created_at,
            'last_modified': self.last_modified,
            'version': self.version,
            'user_preferences': self.user_preferences,
            'project_settings': self.project_settings,
            'main_window_state': self.main_window_state,
            'ui_models': self.ui_models,
            'recent_files': self.recent_files,
            'analysis_results': self.analysis_results
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionData':
        """Create from dictionary - deprecated functionality."""
        return cls(
            session_id=data.get('session_id', str(uuid.uuid4())),
            created_at=data.get('created_at', datetime.now().isoformat()),
            last_modified=data.get('last_modified', datetime.now().isoformat()),
            version=data.get('version', '1.0'),
            user_preferences=data.get('user_preferences', {}),
            project_settings=data.get('project_settings', {}),
            main_window_state=data.get('main_window_state'),
            ui_models=data.get('ui_models', {}),
            recent_files=data.get('recent_files', []),
            analysis_results=data.get('analysis_results', {})
        )


class HeadlessSessionManager(LoggerMixin):
    """
    DEPRECATED: Headless Session Manager
    
    This class is no longer used in CellSorter as session management
    has been completely removed from the application.
    
    All methods are now no-ops or return default values.
    """
    
    def __init__(self, mode_manager=None):
        super().__init__()
        self.log_warning("HeadlessSessionManager is deprecated and non-functional")
        self.current_session: Optional[SessionData] = None
        self.session_file_path: Optional[Path] = None
        self.session_dir = Path.home() / '.cellsorter' / 'sessions'
        self.auto_save_enabled = False  # Always disabled
        
    def create_new_session(self, session_id: str = None) -> Optional[SessionData]:
        """DEPRECATED: Returns None - sessions are no longer created."""
        self.log_warning("Session creation is deprecated - no session will be created")
        return None
        
    def save_session(self, file_path: Optional[Union[str, Path]] = None) -> bool:
        """DEPRECATED: Returns False - sessions are no longer saved."""
        self.log_warning("Session saving is deprecated - no session will be saved")
        return False
    
    def load_session(self, file_path: Union[str, Path]) -> bool:
        """DEPRECATED: Returns False - sessions are no longer loaded."""
        self.log_warning("Session loading is deprecated - no session will be loaded")
        return False
    
    def save_main_window_state(self, state) -> None:
        """DEPRECATED: No-op - window state is no longer saved."""
        self.log_warning("Window state saving is deprecated - state will not be saved")
        
    def load_main_window_state(self):
        """DEPRECATED: Returns None - window state is no longer loaded."""
        self.log_warning("Window state loading is deprecated - no state will be loaded")
        return None
    
    def set_user_preference(self, key: str, value: Any) -> None:
        """DEPRECATED: No-op - preferences are no longer saved."""
        self.log_warning("User preference saving is deprecated - preference will not be saved")
        
    def get_user_preference(self, key: str, default: Any = None) -> Any:
        """DEPRECATED: Always returns default value."""
        self.log_warning("User preference loading is deprecated - returning default value")
        return default
    
    def clear_current_session(self) -> None:
        """DEPRECATED: No-op - no session to clear."""
        pass
    
    def get_session_info(self) -> Optional[Dict[str, Any]]:
        """DEPRECATED: Returns None - no session info available."""
        return None
