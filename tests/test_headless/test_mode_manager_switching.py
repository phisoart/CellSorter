"""
Test Mode Manager Switching

Tests for switching between dev-mode and gui-mode.
"""

import pytest
import os
from unittest.mock import Mock, patch
from src.headless.mode_manager import ModeManager, AppMode, get_mode, set_mode, is_dev_mode, is_gui_mode


class TestModeManagerSwitching:
    """Test mode switching functionality."""
    
    def setup_method(self):
        """Reset mode manager state before each test."""
        # Clear any cached mode
        manager = ModeManager()
        manager._current_mode = None
        manager._mode_locked = False
    
    def test_initial_mode_detection(self):
        """Test initial mode is determined correctly."""
        manager = ModeManager()
        
        # On Windows with display, should default to GUI mode
        mode = manager.get_mode()
        assert mode in [AppMode.GUI, AppMode.DEV, AppMode.DUAL]
        
        # Verify mode string
        mode_str = manager.get_current_mode()
        assert mode_str in ['dev-mode', 'gui-mode']
    
    def test_mode_switching(self):
        """Test switching between modes."""
        manager = ModeManager()
        
        # Switch to DEV mode
        success = manager.set_mode(AppMode.DEV)
        assert success is True
        assert manager.get_mode() == AppMode.DEV
        assert manager.is_dev_mode() is True
        assert manager.is_gui_mode() is False
        assert manager.get_current_mode() == 'dev-mode'
        
        # Switch to GUI mode
        success = manager.set_mode(AppMode.GUI)
        assert success is True
        assert manager.get_mode() == AppMode.GUI
        assert manager.is_dev_mode() is False
        assert manager.is_gui_mode() is True
        assert manager.get_current_mode() == 'gui-mode'
        
        # Switch to DUAL mode
        success = manager.set_mode(AppMode.DUAL)
        assert success is True
        assert manager.get_mode() == AppMode.DUAL
        assert manager.is_dual_mode() is True
    
    def test_mode_locking(self):
        """Test mode locking prevents changes."""
        manager = ModeManager()
        
        # Set initial mode
        manager.set_mode(AppMode.GUI)
        assert manager.get_mode() == AppMode.GUI
        
        # Lock the mode
        manager.lock_mode()
        assert manager.is_locked() is True
        
        # Try to change mode - should fail
        success = manager.set_mode(AppMode.DEV)
        assert success is False
        assert manager.get_mode() == AppMode.GUI  # Mode unchanged
        
        # Force change should work even when locked
        success = manager.set_mode(AppMode.DEV, force=True)
        assert success is True
        assert manager.get_mode() == AppMode.DEV
        
        # Unlock and change normally
        manager.unlock_mode()
        assert manager.is_locked() is False
        success = manager.set_mode(AppMode.GUI)
        assert success is True
    
    def test_environment_variable_mode_selection(self):
        """Test mode selection via environment variables."""
        manager = ModeManager()
        
        # Test CELLSORTER_MODE
        test_cases = [
            ('gui', AppMode.GUI),
            ('production', AppMode.GUI),
            ('dev', AppMode.DEV),
            ('headless', AppMode.DEV),
            ('dual', AppMode.DUAL),
            ('both', AppMode.DUAL),
            ('debug', AppMode.DUAL)
        ]
        
        for env_value, expected_mode in test_cases:
            with patch.dict(os.environ, {'CELLSORTER_MODE': env_value}):
                manager._current_mode = None  # Reset cache
                mode = manager.get_mode()
                assert mode == expected_mode, f"Expected {expected_mode} for CELLSORTER_MODE={env_value}"
    
    def test_legacy_environment_variable(self):
        """Test legacy CELLSORTER_DEV_MODE variable."""
        manager = ModeManager()
        
        # Test dev mode values
        for value in ['true', '1', 'yes', 'on']:
            with patch.dict(os.environ, {'CELLSORTER_DEV_MODE': value}, clear=True):
                manager._current_mode = None
                assert manager.get_mode() == AppMode.DEV
        
        # Test gui mode values
        for value in ['false', '0', 'no', 'off']:
            with patch.dict(os.environ, {'CELLSORTER_DEV_MODE': value}, clear=True):
                manager._current_mode = None
                assert manager.get_mode() == AppMode.GUI
    
    def test_ci_environment_detection(self):
        """Test CI/CD environment detection."""
        manager = ModeManager()
        
        ci_vars = ['CI', 'GITHUB_ACTIONS', 'GITLAB_CI', 'JENKINS_URL']
        
        for var in ci_vars:
            with patch.dict(os.environ, {var: 'true'}, clear=True):
                manager._current_mode = None
                mode = manager.get_mode()
                assert mode == AppMode.DEV, f"{var} should trigger DEV mode"
    
    def test_display_based_mode_selection(self):
        """Test mode selection based on display availability."""
        manager = ModeManager()
        
        # Mock has_display to return False
        with patch('src.headless.mode_manager.has_display', return_value=False):
            with patch.dict(os.environ, {}, clear=True):  # Clear env vars
                manager._current_mode = None
                mode = manager.get_mode()
                assert mode == AppMode.DEV
        
        # Mock has_display to return True
        with patch('src.headless.mode_manager.has_display', return_value=True):
            with patch.dict(os.environ, {}, clear=True):
                manager._current_mode = None
                mode = manager.get_mode()
                assert mode == AppMode.GUI
    
    def test_mode_requirements(self):
        """Test mode requirement checks."""
        manager = ModeManager()
        
        # GUI mode
        manager.set_mode(AppMode.GUI)
        assert manager.requires_gui() is True
        assert manager.requires_headless() is False
        
        # DEV mode
        manager.set_mode(AppMode.DEV)
        assert manager.requires_gui() is False
        assert manager.requires_headless() is True
        
        # DUAL mode
        manager.set_mode(AppMode.DUAL)
        assert manager.requires_gui() is True
        assert manager.requires_headless() is True
    
    def test_mode_info(self):
        """Test comprehensive mode information."""
        manager = ModeManager()
        manager.set_mode(AppMode.DEV)
        
        info = manager.get_mode_info()
        
        # Check required fields
        assert 'mode' in info
        assert 'mode_description' in info
        assert 'dev_mode' in info
        assert 'gui_mode' in info
        assert 'dual_mode' in info
        assert 'requires_gui' in info
        assert 'requires_headless' in info
        assert 'display_available' in info
        assert 'environment' in info
        assert 'locked' in info
        
        # Verify values
        assert info['mode'] == 'dev'
        assert info['dev_mode'] is True
        assert info['gui_mode'] is False
        assert info['requires_headless'] is True
    
    def test_runtime_mode_switching(self):
        """Test mode switching during runtime."""
        manager = ModeManager()
        
        # Start in GUI mode
        manager.set_mode(AppMode.GUI)
        
        # Simulate runtime switch to dev mode
        manager.set_mode(AppMode.DEV)
        
        # Verify immediate effect
        assert manager.is_dev_mode() is True
        assert manager.requires_gui() is False
        
        # Switch back
        manager.set_mode(AppMode.GUI)
        assert manager.is_gui_mode() is True
        assert manager.requires_gui() is True
    
    def test_qapplication_requirement(self):
        """Test QApplication creation based on mode."""
        manager = ModeManager()
        
        # In DEV mode, should not require QApplication
        manager.set_mode(AppMode.DEV)
        assert manager.requires_gui() is False
        
        # In GUI mode, should require QApplication
        manager.set_mode(AppMode.GUI)
        assert manager.requires_gui() is True
        
        # In DUAL mode, should require QApplication
        manager.set_mode(AppMode.DUAL)
        assert manager.requires_gui() is True


class TestModeManagerGlobalFunctions:
    """Test global function interface."""
    
    def test_global_mode_functions(self):
        """Test global convenience functions."""
        # Set mode using global function
        success = set_mode(AppMode.DEV)
        assert success is True
        
        # Check mode using global functions
        assert is_dev_mode() is True
        assert is_gui_mode() is False
        
        # Get mode
        mode = get_mode()
        assert mode == AppMode.DEV 