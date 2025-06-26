"""
Session Manager for CellSorter

This module provides functionality for saving and loading analysis sessions,
allowing users to preserve their work and restore it later.
"""

import json
import time
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

from PySide6.QtCore import QObject, Signal
from utils.logging_config import LoggerMixin
from utils.exceptions import SessionError


class SessionManager(QObject, LoggerMixin):
    """
    Manages saving and loading of CellSorter analysis sessions.
    
    Sessions include:
    - Loaded image and CSV file paths
    - Coordinate calibration data
    - Cell selections and their properties
    - 96-well plate assignments
    - Analysis parameters and settings
    """
    
    # Signals
    session_saved = Signal(str)  # file_path
    session_loaded = Signal(str)  # file_path
    session_error = Signal(str)  # error_message
    
    SESSION_VERSION = "1.0"
    SESSION_EXTENSION = ".cellsession"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.current_session_path: Optional[str] = None
        self.session_data: Dict[str, Any] = {}
        self.is_modified: bool = False
        
    def create_new_session(self) -> Dict[str, Any]:
        """
        Create a new empty session.
        
        Returns:
            Empty session dictionary
        """
        session = {
            'version': self.SESSION_VERSION,
            'created_at': datetime.now().isoformat(),
            'last_modified': datetime.now().isoformat(),
            'application': 'CellSorter',
            'data': {
                'image_file': None,
                'csv_file': None,
                'calibration': {
                    'points': [],
                    'transformation_matrix': None,
                    'is_calibrated': False
                },
                'selections': [],
                'well_assignments': {},
                'settings': {
                    'zoom_level': 1.0,
                    'show_overlays': True,
                    'overlay_alpha': 0.5
                },
                'metadata': {
                    'analysis_notes': '',
                    'user': '',
                    'project': ''
                }
            }
        }
        
        self.session_data = session
        self.current_session_path = None
        self.is_modified = False
        
        self.log_info("Created new session")
        return session
    
    def save_session(self, file_path: str, session_data: Dict[str, Any]) -> bool:
        """
        Save session to file.
        
        Args:
            file_path: Path to save session file
            session_data: Session data to save
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure proper extension
            file_path = Path(file_path)
            if file_path.suffix != self.SESSION_EXTENSION:
                file_path = file_path.with_suffix(self.SESSION_EXTENSION)
            
            # Update session metadata
            session_data['last_modified'] = datetime.now().isoformat()
            session_data['version'] = self.SESSION_VERSION
            
            # Create backup if file exists
            if file_path.exists():
                backup_path = file_path.with_suffix(f'{self.SESSION_EXTENSION}.backup')
                file_path.rename(backup_path)
                self.log_info(f"Created backup: {backup_path}")
            
            # Save session
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            
            self.current_session_path = str(file_path)
            self.session_data = session_data
            self.is_modified = False
            
            self.session_saved.emit(str(file_path))
            self.log_info(f"Session saved: {file_path}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to save session: {e}"
            self.log_error(error_msg)
            self.session_error.emit(error_msg)
            return False
    
    def load_session(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Load session from file.
        
        Args:
            file_path: Path to session file
        
        Returns:
            Session data if successful, None otherwise
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                raise SessionError(f"Session file not found: {file_path}")
            
            if file_path.suffix != self.SESSION_EXTENSION:
                raise SessionError(f"Invalid session file format: {file_path.suffix}")
            
            # Load and validate session
            with open(file_path, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Validate session format
            if not self._validate_session(session_data):
                raise SessionError("Invalid session file format")
            
            # Check version compatibility
            session_version = session_data.get('version', '0.0')
            if not self._is_version_compatible(session_version):
                self.log_warning(f"Session version {session_version} may be incompatible")
            
            self.current_session_path = str(file_path)
            self.session_data = session_data
            self.is_modified = False
            
            self.session_loaded.emit(str(file_path))
            self.log_info(f"Session loaded: {file_path}")
            return session_data
            
        except Exception as e:
            error_msg = f"Failed to load session: {e}"
            self.log_error(error_msg)
            self.session_error.emit(error_msg)
            return None
    
    def auto_save_session(self, session_data: Dict[str, Any]) -> bool:
        """
        Automatically save session to temporary location.
        
        Args:
            session_data: Session data to save
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create auto-save directory
            auto_save_dir = Path.home() / '.cellsorter' / 'autosave'
            auto_save_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate auto-save filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            auto_save_path = auto_save_dir / f"autosave_{timestamp}{self.SESSION_EXTENSION}"
            
            # Keep only latest 5 auto-save files
            self._cleanup_auto_saves(auto_save_dir, keep_count=5)
            
            return self.save_session(str(auto_save_path), session_data)
            
        except Exception as e:
            self.log_error(f"Auto-save failed: {e}")
            return False
    
    def export_session_summary(self, file_path: str, session_data: Dict[str, Any]) -> bool:
        """
        Export session summary as human-readable text.
        
        Args:
            file_path: Path to export summary
            session_data: Session data to summarize
        
        Returns:
            True if successful, False otherwise
        """
        try:
            summary = self._generate_session_summary(session_data)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(summary)
            
            self.log_info(f"Session summary exported: {file_path}")
            return True
            
        except Exception as e:
            self.log_error(f"Failed to export session summary: {e}")
            return False
    
    def get_recent_sessions(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Get list of recent session files.
        
        Args:
            count: Maximum number of recent sessions to return
        
        Returns:
            List of session file information
        """
        recent_sessions = []
        
        try:
            # Search common session locations
            search_paths = [
                Path.home() / 'Documents' / 'CellSorter',
                Path.home() / '.cellsorter' / 'autosave',
                Path.cwd()
            ]
            
            session_files = []
            for search_path in search_paths:
                if search_path.exists():
                    session_files.extend(search_path.glob(f'*{self.SESSION_EXTENSION}'))
            
            # Sort by modification time (newest first)
            session_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            
            # Get file information
            for session_file in session_files[:count]:
                try:
                    stat = session_file.stat()
                    file_info = {
                        'path': str(session_file),
                        'name': session_file.stem,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'size': stat.st_size
                    }
                    
                    # Try to get session metadata
                    try:
                        with open(session_file, 'r', encoding='utf-8') as f:
                            session_data = json.load(f)
                        
                        file_info.update({
                            'version': session_data.get('version', 'Unknown'),
                            'created': session_data.get('created_at', 'Unknown'),
                            'has_image': bool(session_data.get('data', {}).get('image_file')),
                            'has_csv': bool(session_data.get('data', {}).get('csv_file')),
                            'selection_count': len(session_data.get('data', {}).get('selections', []))
                        })
                    except:
                        # If we can't read the session, just use file info
                        pass
                    
                    recent_sessions.append(file_info)
                    
                except Exception as e:
                    self.log_warning(f"Could not read session file {session_file}: {e}")
                    continue
            
        except Exception as e:
            self.log_error(f"Failed to get recent sessions: {e}")
        
        return recent_sessions
    
    def _validate_session(self, session_data: Dict[str, Any]) -> bool:
        """
        Validate session data format.
        
        Args:
            session_data: Session data to validate
        
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['version', 'data']
        
        for field in required_fields:
            if field not in session_data:
                return False
        
        # Validate data section
        data = session_data.get('data', {})
        required_data_fields = ['selections', 'calibration', 'settings']
        
        for field in required_data_fields:
            if field not in data:
                return False
        
        return True
    
    def _is_version_compatible(self, version: str) -> bool:
        """
        Check if session version is compatible.
        
        Args:
            version: Session version string
        
        Returns:
            True if compatible, False otherwise
        """
        try:
            major, minor = map(int, version.split('.'))
            current_major, current_minor = map(int, self.SESSION_VERSION.split('.'))
            
            # Compatible if same major version
            return major == current_major
            
        except:
            return False
    
    def _cleanup_auto_saves(self, auto_save_dir: Path, keep_count: int) -> None:
        """
        Clean up old auto-save files.
        
        Args:
            auto_save_dir: Auto-save directory
            keep_count: Number of files to keep
        """
        try:
            auto_save_files = list(auto_save_dir.glob(f'autosave_*{self.SESSION_EXTENSION}'))
            auto_save_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            
            # Remove old files
            for old_file in auto_save_files[keep_count:]:
                old_file.unlink()
                self.log_info(f"Removed old auto-save: {old_file}")
                
        except Exception as e:
            self.log_warning(f"Failed to cleanup auto-saves: {e}")
    
    def _generate_session_summary(self, session_data: Dict[str, Any]) -> str:
        """
        Generate human-readable session summary.
        
        Args:
            session_data: Session data to summarize
        
        Returns:
            Formatted summary string
        """
        data = session_data.get('data', {})
        
        summary = f"""CellSorter Analysis Session Summary
========================================

Session Information:
- Version: {session_data.get('version', 'Unknown')}
- Created: {session_data.get('created_at', 'Unknown')}
- Last Modified: {session_data.get('last_modified', 'Unknown')}

Files:
- Image: {data.get('image_file', 'None')}
- CSV Data: {data.get('csv_file', 'None')}

Analysis Results:
- Selections: {len(data.get('selections', []))}
- Calibration: {'Yes' if data.get('calibration', {}).get('is_calibrated', False) else 'No'}
- Well Assignments: {len(data.get('well_assignments', {}))}

Settings:
- Zoom Level: {data.get('settings', {}).get('zoom_level', 1.0)}
- Show Overlays: {'Yes' if data.get('settings', {}).get('show_overlays', True) else 'No'}

Metadata:
- Notes: {data.get('metadata', {}).get('analysis_notes', 'None')}
- User: {data.get('metadata', {}).get('user', 'Not specified')}
- Project: {data.get('metadata', {}).get('project', 'Not specified')}
"""
        
        return summary