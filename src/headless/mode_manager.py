"""
Mode Manager

Manages switching between development mode (headless) and GUI mode.
Provides centralized control over application operation mode.
"""

import os
import logging
from typing import Optional, Dict, Any
from enum import Enum

from .display_detector import has_display

logger = logging.getLogger(__name__)


class AppMode(Enum):
    """Application operation modes."""
    GUI = "gui"
    DEV = "dev"
    AUTO = "auto"


class ModeManager:
    """Manages application operation mode."""
    
    def __init__(self):
        self._current_mode: Optional[AppMode] = None
        self._mode_locked: bool = False
    
    def get_mode(self) -> AppMode:
        """
        Get current application mode.
        
        Returns:
            Current application mode
        """
        if self._current_mode is not None:
            return self._current_mode
        
        # Auto-detect mode based on environment
        return self._detect_mode()
    
    def set_mode(self, mode: AppMode, force: bool = False) -> bool:
        """
        Set application mode.
        
        Args:
            mode: Target mode to set
            force: Force mode change even if locked
            
        Returns:
            True if mode was set successfully
        """
        if self._mode_locked and not force:
            logger.warning(f"Mode is locked, cannot change to {mode}")
            return False
        
        old_mode = self._current_mode
        self._current_mode = mode
        
        logger.info(f"Mode changed from {old_mode} to {mode}")
        return True
    
    def lock_mode(self) -> None:
        """Lock the current mode to prevent changes."""
        self._mode_locked = True
        logger.debug("Mode locked")
    
    def unlock_mode(self) -> None:
        """Unlock mode to allow changes."""
        self._mode_locked = False
        logger.debug("Mode unlocked")
    
    def is_locked(self) -> bool:
        """Check if mode is locked."""
        return self._mode_locked
    
    def is_dev_mode(self) -> bool:
        """Check if currently in development mode."""
        return self.get_mode() == AppMode.DEV
    
    def is_gui_mode(self) -> bool:
        """Check if currently in GUI mode."""
        return self.get_mode() == AppMode.GUI
    
    def _detect_mode(self) -> AppMode:
        """Auto-detect appropriate mode based on environment."""
        # Check explicit environment variable
        env_mode = os.environ.get('CELLSORTER_DEV_MODE', '').lower()
        if env_mode in ('true', '1', 'yes', 'on'):
            logger.info("Dev mode set by CELLSORTER_DEV_MODE environment variable")
            return AppMode.DEV
        elif env_mode in ('false', '0', 'no', 'off'):
            logger.info("GUI mode set by CELLSORTER_DEV_MODE environment variable")
            return AppMode.GUI
        
        # Check for dev mode indicators
        if os.environ.get('CELLSORTER_FORCE_HEADLESS'):
            logger.info("Dev mode forced by CELLSORTER_FORCE_HEADLESS")
            return AppMode.DEV
        
        # Check CI/CD environments
        ci_vars = [
            'CI', 'CONTINUOUS_INTEGRATION', 'GITHUB_ACTIONS',
            'GITLAB_CI', 'JENKINS_URL', 'TRAVIS', 'CIRCLECI'
        ]
        if any(os.environ.get(var) for var in ci_vars):
            logger.info("Dev mode detected for CI/CD environment")
            return AppMode.DEV
        
        # Check for display availability
        if not has_display():
            logger.info("Dev mode selected due to no display available")
            return AppMode.DEV
        
        # Default to GUI mode when display is available
        logger.info("GUI mode selected (display available)")
        return AppMode.GUI
    
    def get_mode_info(self) -> Dict[str, Any]:
        """
        Get comprehensive mode information.
        
        Returns:
            Dictionary containing mode information
        """
        current_mode = self._current_mode if self._current_mode else self._detect_mode()
        
        return {
            'mode': current_mode.value if current_mode else 'unknown',
            'dev_mode': self.is_dev_mode(),
            'display_available': has_display(),
            'environment': {
                'CELLSORTER_DEV_MODE': os.environ.get('CELLSORTER_DEV_MODE', 'not set'),
                'CELLSORTER_FORCE_HEADLESS': os.environ.get('CELLSORTER_FORCE_HEADLESS', 'not set'),
                'CI': os.environ.get('CI', 'not set'),
                'DISPLAY': os.environ.get('DISPLAY', 'not set'),
                'WAYLAND_DISPLAY': os.environ.get('WAYLAND_DISPLAY', 'not set'),
            },
            'locked': self._mode_locked
        }


# Global instance
_mode_manager = ModeManager()


def get_mode() -> AppMode:
    """Get current application mode."""
    return _mode_manager.get_mode()


def set_mode(mode: AppMode, force: bool = False) -> bool:
    """Set application mode."""
    return _mode_manager.set_mode(mode, force)


def is_dev_mode() -> bool:
    """Check if currently in development mode."""
    return _mode_manager.is_dev_mode()


def is_gui_mode() -> bool:
    """Check if currently in GUI mode."""
    return _mode_manager.is_gui_mode()


def set_dev_mode(enabled: bool = True) -> bool:
    """
    Enable or disable development mode.
    
    Args:
        enabled: True to enable dev mode, False for GUI mode
        
    Returns:
        True if mode was set successfully
    """
    target_mode = AppMode.DEV if enabled else AppMode.GUI
    return _mode_manager.set_mode(target_mode)


def lock_mode() -> None:
    """Lock the current mode to prevent changes."""
    _mode_manager.lock_mode()


def unlock_mode() -> None:
    """Unlock mode to allow changes."""
    _mode_manager.unlock_mode()


def get_mode_info() -> Dict[str, Any]:
    """
    Get comprehensive mode information.
    
    Returns:
        Dictionary containing mode information
    """
    return _mode_manager.get_mode_info() 