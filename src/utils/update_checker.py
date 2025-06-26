"""
Update Checker for CellSorter

This module handles automatic update checking and notification.
"""

import json
import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from packaging import version
import urllib.request
import urllib.error
import threading

from PySide6.QtCore import QObject, Signal, QSettings, QTimer
from PySide6.QtWidgets import QMessageBox, QCheckBox, QWidget

from src.utils.error_handler import handle_errors

logger = logging.getLogger(__name__)


class UpdateChecker(QObject):
    """Handles automatic update checking for CellSorter."""
    
    # Signals
    update_available = Signal(str, str, str)  # current_version, latest_version, download_url
    update_check_completed = Signal(bool)  # success
    
    # Configuration
    UPDATE_CHECK_URL = "https://api.github.com/repos/phisoart/CellSorter/releases/latest"
    CHECK_INTERVAL_DAYS = 7  # Check once a week
    
    def __init__(self, current_version: str):
        super().__init__()
        self.current_version = current_version
        self.settings = QSettings("CellSorter", "UpdateChecker")
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_for_updates)
        
        # Initialize settings
        self._init_settings()
        
    def _init_settings(self):
        """Initialize default settings."""
        if not self.settings.contains("auto_check_enabled"):
            self.settings.setValue("auto_check_enabled", True)
        if not self.settings.contains("last_check_date"):
            self.settings.setValue("last_check_date", "")
        if not self.settings.contains("skip_version"):
            self.settings.setValue("skip_version", "")
            
    @property
    def auto_check_enabled(self) -> bool:
        """Check if automatic update checking is enabled."""
        return self.settings.value("auto_check_enabled", True, type=bool)
    
    @auto_check_enabled.setter
    def auto_check_enabled(self, value: bool):
        """Set automatic update checking preference."""
        self.settings.setValue("auto_check_enabled", value)
        if value:
            self.start_periodic_check()
        else:
            self.stop_periodic_check()
            
    @property
    def last_check_date(self) -> Optional[datetime]:
        """Get the last check date."""
        date_str = self.settings.value("last_check_date", "")
        if date_str:
            try:
                return datetime.fromisoformat(date_str)
            except ValueError:
                return None
        return None
    
    @last_check_date.setter
    def last_check_date(self, value: datetime):
        """Set the last check date."""
        self.settings.setValue("last_check_date", value.isoformat())
        
    @property
    def skip_version(self) -> str:
        """Get the version to skip."""
        return self.settings.value("skip_version", "")
    
    @skip_version.setter
    def skip_version(self, value: str):
        """Set the version to skip."""
        self.settings.setValue("skip_version", value)
        
    def start_periodic_check(self):
        """Start periodic update checking."""
        if not self.auto_check_enabled:
            return
            
        # Check on startup if needed
        if self._should_check_now():
            self.check_for_updates()
            
        # Set up periodic checking (24 hours)
        self.timer.start(24 * 60 * 60 * 1000)  # milliseconds
        
    def stop_periodic_check(self):
        """Stop periodic update checking."""
        self.timer.stop()
        
    def _should_check_now(self) -> bool:
        """Determine if an update check should be performed now."""
        if not self.last_check_date:
            return True
            
        days_since_last_check = (datetime.now() - self.last_check_date).days
        return days_since_last_check >= self.CHECK_INTERVAL_DAYS
        
    @handle_errors
    def check_for_updates(self, force: bool = False):
        """Check for updates in a background thread."""
        if not force and not self.auto_check_enabled:
            return
            
        logger.info("Checking for updates...")
        
        # Perform check in background thread
        thread = threading.Thread(target=self._perform_update_check)
        thread.daemon = True
        thread.start()
        
    def _perform_update_check(self):
        """Perform the actual update check (runs in background thread)."""
        try:
            # Fetch latest release info from GitHub
            req = urllib.request.Request(
                self.UPDATE_CHECK_URL,
                headers={'User-Agent': 'CellSorter-UpdateChecker'}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                
            # Extract version info
            latest_version = data.get('tag_name', '').lstrip('v')
            download_url = data.get('html_url', '')
            
            if not latest_version:
                logger.warning("No version information found in release data")
                self.update_check_completed.emit(False)
                return
                
            # Update last check date
            self.last_check_date = datetime.now()
            
            # Compare versions
            if self._is_newer_version(latest_version):
                # Skip if user chose to skip this version
                if latest_version == self.skip_version:
                    logger.info(f"Skipping version {latest_version} as requested")
                    self.update_check_completed.emit(True)
                    return
                    
                logger.info(f"Update available: {latest_version}")
                self.update_available.emit(self.current_version, latest_version, download_url)
            else:
                logger.info("No updates available")
                
            self.update_check_completed.emit(True)
            
        except urllib.error.URLError as e:
            logger.error(f"Network error checking for updates: {e}")
            self.update_check_completed.emit(False)
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            self.update_check_completed.emit(False)
            
    def _is_newer_version(self, latest_version: str) -> bool:
        """Compare version strings."""
        try:
            return version.parse(latest_version) > version.parse(self.current_version)
        except Exception as e:
            logger.error(f"Error comparing versions: {e}")
            return False
            
    def show_update_dialog(self, parent: QWidget, current_version: str, 
                          latest_version: str, download_url: str):
        """Show update available dialog."""
        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle("Update Available")
        msg_box.setText(f"A new version of CellSorter is available!")
        msg_box.setInformativeText(
            f"Current version: {current_version}\n"
            f"Latest version: {latest_version}\n\n"
            f"Would you like to download the update?"
        )
        
        # Add buttons
        download_btn = msg_box.addButton("Download", QMessageBox.AcceptRole)
        skip_btn = msg_box.addButton("Skip This Version", QMessageBox.RejectRole)
        later_btn = msg_box.addButton("Remind Me Later", QMessageBox.RejectRole)
        msg_box.setDefaultButton(download_btn)
        
        # Add checkbox for auto-check preference
        check_box = QCheckBox("Automatically check for updates")
        check_box.setChecked(self.auto_check_enabled)
        msg_box.setCheckBox(check_box)
        
        # Execute dialog
        msg_box.exec()
        
        # Update auto-check preference
        self.auto_check_enabled = check_box.isChecked()
        
        # Handle response
        clicked_button = msg_box.clickedButton()
        if clicked_button == download_btn:
            # Open download URL in browser
            import webbrowser
            webbrowser.open(download_url)
        elif clicked_button == skip_btn:
            # Remember to skip this version
            self.skip_version = latest_version
            logger.info(f"User chose to skip version {latest_version}")
            
    def get_update_status(self) -> Dict[str, Any]:
        """Get current update checker status."""
        return {
            "auto_check_enabled": self.auto_check_enabled,
            "last_check_date": self.last_check_date.isoformat() if self.last_check_date else None,
            "skip_version": self.skip_version,
            "current_version": self.current_version,
            "check_interval_days": self.CHECK_INTERVAL_DAYS
        } 