"""
Display Detection System

Cross-platform display server detection for Linux, Windows, and macOS.
Determines if GUI applications can be launched.
"""

import os
import platform
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class DisplayDetector:
    """Cross-platform display detection system."""
    
    def __init__(self):
        self._cached_result: Optional[bool] = None
        self._detection_info: Dict[str, Any] = {}
    
    def has_display(self, force_check: bool = False) -> bool:
        """
        Check if display server is available.
        
        Args:
            force_check: Force re-detection instead of using cache
            
        Returns:
            True if display is available, False otherwise
        """
        # Check for CELLSORTER_DISPLAY_MODE override first
        display_mode = os.environ.get('CELLSORTER_DISPLAY_MODE', '').lower()
        if display_mode == 'headless':
            return False
        elif display_mode == 'gui':
            return True
        
        if self._cached_result is not None and not force_check:
            return self._cached_result
        
        system = platform.system()
        
        if system == "Linux":
            result = self._detect_linux_display()
        elif system == "Darwin":  # macOS
            result = self._detect_macos_display()
        elif system == "Windows":
            result = self._detect_windows_display()
        else:
            logger.warning(f"Unknown platform: {system}, assuming no display")
            result = False
        
        self._cached_result = result
        logger.info(f"Display detection: {result} on {system}")
        logger.debug(f"Detection info: {self._detection_info}")
        
        return result
    
    def _detect_linux_display(self) -> bool:
        """Detect display on Linux systems."""
        # Check X11 display
        x11_display = os.environ.get('DISPLAY')
        if x11_display:
            self._detection_info['x11_display'] = x11_display
            logger.debug(f"Found X11 DISPLAY: {x11_display}")
            return True
        
        # Check Wayland display
        wayland_display = os.environ.get('WAYLAND_DISPLAY')
        if wayland_display:
            self._detection_info['wayland_display'] = wayland_display
            logger.debug(f"Found Wayland DISPLAY: {wayland_display}")
            return True
        
        # Check for running display manager
        try:
            import subprocess
            # Check for X server process
            result = subprocess.run(['pgrep', '-x', 'Xorg'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                self._detection_info['x_server'] = 'running'
                logger.debug("Found running X server")
                return True
            
            # Check for Wayland compositor
            wayland_result = subprocess.run(['pgrep', '-f', 'wayland'], 
                                          capture_output=True, text=True)
            if wayland_result.returncode == 0:
                self._detection_info['wayland_compositor'] = 'running'
                logger.debug("Found running Wayland compositor")
                return True
        except Exception as e:
            logger.debug(f"Process check failed: {e}")
        
        self._detection_info['linux_display'] = 'none_found'
        return False
    
    def _detect_macos_display(self) -> bool:
        """Detect display on macOS systems."""
        # On macOS, display is generally always available unless in SSH/headless mode
        # Check for SSH session
        if os.environ.get('SSH_CLIENT') or os.environ.get('SSH_TTY'):
            self._detection_info['connection_type'] = 'ssh'
            logger.debug("SSH session detected, assuming no display")
            return False
        
        # Check for display environment variables
        if os.environ.get('DISPLAY'):
            self._detection_info['display'] = os.environ.get('DISPLAY')
            return True
        
        # Try to access window server
        try:
            import subprocess
            result = subprocess.run(['launchctl', 'list', 'com.apple.WindowServer'],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                self._detection_info['window_server'] = 'running'
                logger.debug("WindowServer is running")
                return True
        except Exception as e:
            logger.debug(f"WindowServer check failed: {e}")
        
        # Fallback: assume display is available on macOS unless proven otherwise
        self._detection_info['macos_display'] = 'assumed_available'
        return True
    
    def _detect_windows_display(self) -> bool:
        """Detect display on Windows systems."""
        # Check for interactive session
        import subprocess
        try:
            # Check if we're in an interactive session
            result = subprocess.run(['query', 'session'], 
                                  capture_output=True, text=True)
            if result.returncode == 0 and 'Active' in result.stdout:
                self._detection_info['session_type'] = 'interactive'
                logger.debug("Interactive Windows session detected")
                return True
        except Exception as e:
            logger.debug(f"Session query failed: {e}")
        
        # Check for common headless indicators
        if os.environ.get('SSH_CLIENT') or os.environ.get('SSH_CONNECTION'):
            self._detection_info['connection_type'] = 'ssh'
            return False
        
        # On Windows, assume display is available unless in service/headless mode
        try:
            import win32gui
            if win32gui.GetDesktopWindow():
                self._detection_info['desktop_window'] = 'available'
                return True
        except ImportError:
            # win32gui not available, use fallback
            pass
        except Exception as e:
            logger.debug(f"Desktop window check failed: {e}")
        
        # Fallback: assume display is available on Windows
        self._detection_info['windows_display'] = 'assumed_available'
        return True
    
    def get_detection_info(self) -> Dict[str, Any]:
        """Get detailed information about display detection."""
        return {
            'platform': platform.system(),
            'has_display': self._cached_result,
            'detection_details': self._detection_info.copy()
        }
    
    def clear_cache(self) -> None:
        """Clear cached detection result."""
        self._cached_result = None
        self._detection_info.clear()
    
    def get_display_mode(self) -> str:
        """
        Get the current display mode.
        
        Returns:
            'gui' if display is available, 'headless' otherwise
        """
        # Check force mode environment variable
        force_mode = os.environ.get('CELLSORTER_DISPLAY_MODE', '').lower()
        if force_mode in ('gui', 'headless'):
            return force_mode
        
        # Check for CI/CD environments
        ci_indicators = ['CI', 'GITHUB_ACTIONS', 'JENKINS_HOME', 'GITLAB_CI', 'DOCKER_CONTAINER']
        for indicator in ci_indicators:
            if os.environ.get(indicator):
                return 'headless'
        
        # Auto-detect based on display availability
        return 'gui' if self.has_display() else 'headless'
    
    def is_virtual_display(self) -> bool:
        """
        Check if running on a virtual display (Xvfb, VNC, etc).
        
        Returns:
            True if virtual display detected, False otherwise
        """
        # Check for Xvfb (high display numbers)
        display = os.environ.get('DISPLAY', '')
        if display.startswith(':'):
            try:
                display_num = int(display[1:].split('.')[0])
                if display_num >= 99:  # Common Xvfb range
                    return True
            except ValueError:
                pass
        
        # Check for VNC
        if os.environ.get('VNC_CONNECTION'):
            return True
        
        # Check detection info
        if 'virtual' in str(self._detection_info).lower():
            return True
        
        return False
    
    def is_ssh_session(self) -> bool:
        """
        Check if running in an SSH session.
        
        Returns:
            True if SSH session detected, False otherwise
        """
        return bool(os.environ.get('SSH_CLIENT') or 
                   os.environ.get('SSH_TTY') or 
                   os.environ.get('SSH_CONNECTION'))
    
    def get_display_info(self) -> Dict[str, Any]:
        """
        Get comprehensive display information.
        
        Returns:
            Dictionary with display status and metadata
        """
        # Ensure detection has run
        if self._cached_result is None:
            self.has_display()
        
        # Get platform in consistent format
        system = platform.system()
        platform_map = {
            'Windows': 'win32',
            'Linux': 'linux',
            'Darwin': 'darwin'
        }
        
        return {
            'platform': platform_map.get(system, system.lower()),
            'has_display': self._cached_result or False,
            'display_mode': self.get_display_mode(),
            'is_virtual': self.is_virtual_display(),
            'is_ssh': self.is_ssh_session(),
            'detection_details': self._detection_info.copy()
        }


# Global instance
_detector = DisplayDetector()


def has_display(force_check: bool = False) -> bool:
    """
    Check if display server is available.
    
    Args:
        force_check: Force re-detection instead of using cache
        
    Returns:
        True if display is available, False otherwise
    """
    # Check for force headless environment variable
    if os.environ.get('CELLSORTER_FORCE_HEADLESS', '').lower() in ('true', '1', 'yes'):
        logger.info("CELLSORTER_FORCE_HEADLESS is set, returning False")
        return False
    
    return _detector.has_display(force_check)


def get_display_info() -> Dict[str, Any]:
    """Get detailed display detection information."""
    return _detector.get_detection_info()


def clear_display_cache() -> None:
    """Clear display detection cache."""
    _detector.clear_cache() 