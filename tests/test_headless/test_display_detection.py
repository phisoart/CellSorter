"""
Test Display Detection System

Tests for display detection on Windows, Linux, and macOS platforms.
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch
from src.headless.display_detector import DisplayDetector


class TestDisplayDetection:
    """Test display detection functionality across platforms."""
    
    def test_windows_display_detection(self):
        """Test display detection on Windows."""
        if sys.platform != 'win32':
            pytest.skip("Windows-specific test")
        
        detector = DisplayDetector()
        
        # On Windows desktop, display should be available
        has_display = detector.has_display()
        assert isinstance(has_display, bool)
        
        # In most Windows environments, display is available
        # But in CI/CD it might not be
        if os.environ.get('CI'):
            print(f"CI environment detected, display status: {has_display}")
        else:
            # On developer's Windows machine, display should be available
            assert has_display is True
    
    def test_linux_display_detection(self):
        """Test display detection on Linux."""
        detector = DisplayDetector()
        
        # Test Linux detection logic directly
        with patch.dict(os.environ, {'DISPLAY': ':0'}):
            assert detector._detect_linux_display() is True
        
        # Test without DISPLAY
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop('DISPLAY', None)
            os.environ.pop('WAYLAND_DISPLAY', None)
            assert detector._detect_linux_display() is False
    
    def test_macos_display_detection(self):
        """Test display detection on macOS."""
        detector = DisplayDetector()
        
        # Test macOS detection logic directly
        # Test SSH session (no display)
        with patch.dict(os.environ, {'SSH_CLIENT': '192.168.1.1 22 22'}):
            assert detector._detect_macos_display() is False
        
        # Test normal macOS environment (display available)
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop('SSH_CLIENT', None)
            os.environ.pop('SSH_TTY', None)
            # Mock subprocess for WindowServer check
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(returncode=0)
                assert detector._detect_macos_display() is True
    
    def test_force_mode_environment_variable(self):
        """Test CELLSORTER_DISPLAY_MODE environment variable."""
        detector = DisplayDetector()
        
        # Test force headless mode
        with patch.dict(os.environ, {'CELLSORTER_DISPLAY_MODE': 'headless'}):
            assert detector.has_display() is False
            assert detector.get_display_mode() == 'headless'
        
        # Test force gui mode
        with patch.dict(os.environ, {'CELLSORTER_DISPLAY_MODE': 'gui'}):
            assert detector.has_display() is True
            assert detector.get_display_mode() == 'gui'
        
        # Test invalid mode falls back to auto-detection
        with patch.dict(os.environ, {'CELLSORTER_DISPLAY_MODE': 'invalid'}):
            mode = detector.get_display_mode()
            assert mode in ['gui', 'headless']
    
    def test_virtual_display_detection(self):
        """Test detection of virtual display environments."""
        detector = DisplayDetector()
        
        # Test Xvfb detection
        with patch.dict(os.environ, {'DISPLAY': ':99'}):
            is_virtual = detector.is_virtual_display()
            # High display numbers often indicate virtual displays
            assert isinstance(is_virtual, bool)
        
        # Test VNC detection
        with patch.dict(os.environ, {'DISPLAY': ':1', 'VNC_CONNECTION': '1'}):
            assert detector.is_virtual_display() is True
    
    def test_ssh_session_detection(self):
        """Test detection of SSH sessions."""
        detector = DisplayDetector()
        
        # Test SSH detection
        with patch.dict(os.environ, {'SSH_CLIENT': '192.168.1.1 22 22'}):
            assert detector.is_ssh_session() is True
        
        with patch.dict(os.environ, {'SSH_TTY': '/dev/pts/0'}):
            assert detector.is_ssh_session() is True
        
        # Test non-SSH environment
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop('SSH_CLIENT', None)
            os.environ.pop('SSH_TTY', None)
            assert detector.is_ssh_session() is False
    
    def test_display_info_collection(self):
        """Test collection of display information."""
        detector = DisplayDetector()
        
        info = detector.get_display_info()
        
        # Check required fields
        assert 'platform' in info
        assert 'has_display' in info
        assert 'display_mode' in info
        assert 'is_virtual' in info
        assert 'is_ssh' in info
        
        # Verify platform
        assert info['platform'] in ['win32', 'linux', 'darwin']
    
    def test_headless_fallback_logic(self):
        """Test fallback logic for headless environments."""
        detector = DisplayDetector()
        
        # Test various headless indicators
        headless_indicators = [
            {'CI': 'true'},
            {'GITHUB_ACTIONS': 'true'},
            {'JENKINS_HOME': '/var/jenkins'},
            {'GITLAB_CI': 'true'},
            {'DOCKER_CONTAINER': 'true'}
        ]
        
        for env_vars in headless_indicators:
            with patch.dict(os.environ, env_vars):
                mode = detector.get_display_mode()
                # In CI/CD environments, should default to headless
                assert mode == 'headless'


class TestDisplayDetectorIntegration:
    """Integration tests for display detection with other components."""
    
    def test_mode_manager_integration(self):
        """Test integration with ModeManager."""
        from src.headless.mode_manager import ModeManager
        
        # Create mode manager with display detector
        mode_manager = ModeManager()
        
        # Mode manager should use display detector
        current_mode = mode_manager.get_current_mode()
        assert current_mode in ['dev-mode', 'gui-mode']
        
        # If no display, should be dev-mode
        with patch.dict(os.environ, {'CELLSORTER_DISPLAY_MODE': 'headless'}):
            mode_manager = ModeManager()
            assert mode_manager.is_dev_mode() is True
            assert mode_manager.is_gui_mode() is False
    
    def test_error_handling(self):
        """Test error handling in display detection."""
        detector = DisplayDetector()
        
        # Test with mocked exceptions
        with patch('subprocess.run', side_effect=Exception("Test error")):
            # Should handle errors gracefully
            has_display = detector.has_display()
            assert isinstance(has_display, bool)
            
            info = detector.get_display_info()
            assert 'error' not in info  # Should not expose internal errors 