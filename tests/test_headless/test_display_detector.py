"""
Tests for display detection system.
"""

import pytest
import os
import platform
from unittest.mock import patch, MagicMock

import sys
from pathlib import Path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from headless.display_detector import DisplayDetector, has_display, get_display_info


class TestDisplayDetector:
    """Test display detection functionality."""
    
    def setup_method(self):
        """Setup for each test."""
        self.detector = DisplayDetector()
    
    def test_initialization(self):
        """Test detector initialization."""
        assert self.detector._cached_result is None
        assert self.detector._detection_info == {}
    
    def test_cache_behavior(self):
        """Test caching mechanism."""
        # First call should detect and cache
        with patch.object(self.detector, '_detect_linux_display', return_value=True):
            with patch('platform.system', return_value='Linux'):
                result1 = self.detector.has_display()
                result2 = self.detector.has_display()
                
                assert result1 == result2 == True
                assert self.detector._cached_result == True
    
    def test_force_check_bypasses_cache(self):
        """Test force check bypasses cache."""
        self.detector._cached_result = False
        
        with patch.object(self.detector, '_detect_linux_display', return_value=True):
            with patch('platform.system', return_value='Linux'):
                result = self.detector.has_display(force_check=True)
                assert result == True
                assert self.detector._cached_result == True
    
    def test_clear_cache(self):
        """Test cache clearing."""
        self.detector._cached_result = True
        self.detector._detection_info = {'test': 'data'}
        
        self.detector.clear_cache()
        
        assert self.detector._cached_result is None
        assert self.detector._detection_info == {}
    
    @pytest.mark.skipif(platform.system() != "Linux", reason="Linux-specific test")
    def test_linux_display_detection_x11(self):
        """Test Linux X11 display detection."""
        with patch.dict(os.environ, {'DISPLAY': ':0'}):
            result = self.detector._detect_linux_display()
            assert result == True
            assert 'x11_display' in self.detector._detection_info
    
    @pytest.mark.skipif(platform.system() != "Linux", reason="Linux-specific test")
    def test_linux_display_detection_wayland(self):
        """Test Linux Wayland display detection."""
        with patch.dict(os.environ, {'WAYLAND_DISPLAY': 'wayland-0'}, clear=True):
            result = self.detector._detect_linux_display()
            assert result == True
            assert 'wayland_display' in self.detector._detection_info
    
    def test_linux_no_display(self):
        """Test Linux with no display."""
        with patch.dict(os.environ, {}, clear=True):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value.returncode = 1  # Process not found
                result = self.detector._detect_linux_display()
                assert result == False
                assert self.detector._detection_info['linux_display'] == 'none_found'
    
    @pytest.mark.skipif(platform.system() != "Darwin", reason="macOS-specific test")
    def test_macos_ssh_session(self):
        """Test macOS SSH session detection."""
        with patch.dict(os.environ, {'SSH_CLIENT': '192.168.1.1'}):
            result = self.detector._detect_macos_display()
            assert result == False
            assert self.detector._detection_info['connection_type'] == 'ssh'
    
    def test_unknown_platform(self):
        """Test unknown platform handling."""
        with patch('platform.system', return_value='UnknownOS'):
            result = self.detector.has_display()
            assert result == False
    
    def test_get_detection_info(self):
        """Test getting detection information."""
        self.detector._cached_result = True
        self.detector._detection_info = {'test': 'data'}
        
        info = self.detector.get_detection_info()
        
        assert 'platform' in info
        assert info['has_display'] == True
        assert info['detection_details']['test'] == 'data'


class TestGlobalFunctions:
    """Test global functions."""
    
    def test_has_display_force_headless(self):
        """Test force headless environment variable."""
        with patch.dict(os.environ, {'CELLSORTER_FORCE_HEADLESS': 'true'}):
            result = has_display()
            assert result == False
    
    def test_has_display_force_headless_variants(self):
        """Test different force headless values."""
        variants = ['true', '1', 'yes', 'TRUE', 'Yes']
        
        for variant in variants:
            with patch.dict(os.environ, {'CELLSORTER_FORCE_HEADLESS': variant}):
                result = has_display()
                assert result == False, f"Failed for variant: {variant}"
    
    def test_get_display_info(self):
        """Test global display info function."""
        info = get_display_info()
        assert isinstance(info, dict)
        assert 'platform' in info
        assert 'has_display' in info
        assert 'detection_details' in info 