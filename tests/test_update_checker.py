"""
Tests for Update Checker module

This module tests the automatic update checking functionality.
"""

import json
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QWidget

from src.utils.update_checker import UpdateChecker


class TestUpdateChecker(unittest.TestCase):
    """Test cases for UpdateChecker class."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        if not QApplication.instance():
            cls.app = QApplication([])
    
    def setUp(self):
        """Set up each test."""
        self.current_version = "2.0.0"
        self.update_checker = UpdateChecker(self.current_version)
        
    def tearDown(self):
        """Clean up after each test."""
        # Clear settings
        self.update_checker.settings.clear()
        
    def test_initialization(self):
        """Test UpdateChecker initialization."""
        assert self.update_checker.current_version == "2.0.0"
        assert isinstance(self.update_checker.settings, QSettings)
        assert self.update_checker.auto_check_enabled == True  # Default
        
    def test_settings_persistence(self):
        """Test that settings are persisted correctly."""
        # Change settings
        self.update_checker.auto_check_enabled = False
        self.update_checker.last_check_date = datetime.now()
        self.update_checker.skip_version = "2.1.0"
        
        # Create new instance to test persistence
        new_checker = UpdateChecker(self.current_version)
        assert new_checker.auto_check_enabled == False
        assert new_checker.skip_version == "2.1.0"
        assert new_checker.last_check_date is not None
        
    def test_should_check_now(self):
        """Test the logic for determining if an update check is needed."""
        # No last check date - should check
        assert self.update_checker._should_check_now() == True
        
        # Recent check - should not check
        self.update_checker.last_check_date = datetime.now()
        assert self.update_checker._should_check_now() == False
        
        # Old check - should check
        old_date = datetime.now() - timedelta(days=8)
        self.update_checker.last_check_date = old_date
        assert self.update_checker._should_check_now() == True
        
    def test_version_comparison(self):
        """Test version comparison logic."""
        # Newer version
        assert self.update_checker._is_newer_version("2.1.0") == True
        assert self.update_checker._is_newer_version("3.0.0") == True
        
        # Same or older version
        assert self.update_checker._is_newer_version("2.0.0") == False
        assert self.update_checker._is_newer_version("1.9.0") == False
        
        # Invalid version
        assert self.update_checker._is_newer_version("invalid") == False
        
    @patch('urllib.request.urlopen')
    def test_perform_update_check_success(self, mock_urlopen):
        """Test successful update check."""
        # Mock response data
        mock_response = Mock()
        mock_response.read.return_value = json.dumps({
            'tag_name': 'v2.1.0',
            'html_url': 'https://github.com/phisoart/CellSorter/releases/tag/v2.1.0'
        }).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        # Connect signal spy
        update_available_spy = Mock()
        check_completed_spy = Mock()
        self.update_checker.update_available.connect(update_available_spy)
        self.update_checker.update_check_completed.connect(check_completed_spy)
        
        # Perform check
        self.update_checker._perform_update_check()
        
        # Verify signals
        update_available_spy.assert_called_once_with("2.0.0", "2.1.0", 
                                                    "https://github.com/phisoart/CellSorter/releases/tag/v2.1.0")
        check_completed_spy.assert_called_once_with(True)
        
        # Verify last check date was updated
        assert self.update_checker.last_check_date is not None
        
    @patch('urllib.request.urlopen')
    def test_perform_update_check_no_update(self, mock_urlopen):
        """Test update check when no update is available."""
        # Mock response data
        mock_response = Mock()
        mock_response.read.return_value = json.dumps({
            'tag_name': 'v1.9.0',
            'html_url': 'https://github.com/phisoart/CellSorter/releases/tag/v1.9.0'
        }).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        # Connect signal spy
        update_available_spy = Mock()
        check_completed_spy = Mock()
        self.update_checker.update_available.connect(update_available_spy)
        self.update_checker.update_check_completed.connect(check_completed_spy)
        
        # Perform check
        self.update_checker._perform_update_check()
        
        # Verify signals
        update_available_spy.assert_not_called()
        check_completed_spy.assert_called_once_with(True)
        
    @patch('urllib.request.urlopen')
    def test_perform_update_check_skip_version(self, mock_urlopen):
        """Test update check when version should be skipped."""
        # Set skip version
        self.update_checker.skip_version = "2.1.0"
        
        # Mock response data
        mock_response = Mock()
        mock_response.read.return_value = json.dumps({
            'tag_name': 'v2.1.0',
            'html_url': 'https://github.com/phisoart/CellSorter/releases/tag/v2.1.0'
        }).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        # Connect signal spy
        update_available_spy = Mock()
        self.update_checker.update_available.connect(update_available_spy)
        
        # Perform check
        self.update_checker._perform_update_check()
        
        # Verify update signal not emitted for skipped version
        update_available_spy.assert_not_called()
        
    @patch('urllib.request.urlopen')
    def test_perform_update_check_network_error(self, mock_urlopen):
        """Test update check with network error."""
        # Mock network error
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("Network error")
        
        # Connect signal spy
        check_completed_spy = Mock()
        self.update_checker.update_check_completed.connect(check_completed_spy)
        
        # Perform check
        self.update_checker._perform_update_check()
        
        # Verify failure signal
        check_completed_spy.assert_called_once_with(False)
        
    def test_get_update_status(self):
        """Test getting update checker status."""
        # Set some values
        self.update_checker.auto_check_enabled = False
        self.update_checker.skip_version = "2.1.0"
        check_date = datetime.now()
        self.update_checker.last_check_date = check_date
        
        # Get status
        status = self.update_checker.get_update_status()
        
        # Verify status
        assert status['auto_check_enabled'] == False
        assert status['skip_version'] == "2.1.0"
        assert status['current_version'] == "2.0.0"
        assert status['check_interval_days'] == 7
        assert status['last_check_date'] == check_date.isoformat()
        
    @patch('threading.Thread')
    def test_check_for_updates_threading(self, mock_thread):
        """Test that update check runs in background thread."""
        # Enable auto-check
        self.update_checker.auto_check_enabled = True
        
        # Call check_for_updates
        self.update_checker.check_for_updates()
        
        # Verify thread was created and started
        mock_thread.assert_called_once()
        mock_thread.return_value.start.assert_called_once()
        
    def test_check_for_updates_disabled(self):
        """Test that update check respects disabled setting."""
        # Disable auto-check
        self.update_checker.auto_check_enabled = False
        
        with patch.object(self.update_checker, '_perform_update_check') as mock_check:
            self.update_checker.check_for_updates(force=False)
            # Should not perform check when disabled and not forced
            mock_check.assert_not_called()
            
    def test_check_for_updates_forced(self):
        """Test that forced update check works even when disabled."""
        # Disable auto-check
        self.update_checker.auto_check_enabled = False
        
        with patch('threading.Thread') as mock_thread:
            self.update_checker.check_for_updates(force=True)
            # Should perform check when forced
            mock_thread.assert_called_once()
            
    @patch('webbrowser.open')
    def test_show_update_dialog_download(self, mock_browser):
        """Test update dialog when user chooses to download."""
        parent = QWidget()
        
        with patch('PySide6.QtWidgets.QMessageBox.exec') as mock_exec:
            with patch('PySide6.QtWidgets.QMessageBox.clickedButton') as mock_button:
                # Mock user clicking Download button
                mock_exec.return_value = None
                download_btn = Mock()
                mock_button.return_value = download_btn
                
                # Patch addButton to return our mock button
                with patch('PySide6.QtWidgets.QMessageBox.addButton', return_value=download_btn):
                    self.update_checker.show_update_dialog(
                        parent, "2.0.0", "2.1.0", 
                        "https://github.com/phisoart/CellSorter/releases"
                    )
                
                # Verify browser opened
                mock_browser.assert_called_once_with(
                    "https://github.com/phisoart/CellSorter/releases"
                )
                
                
if __name__ == '__main__':
    unittest.main() 