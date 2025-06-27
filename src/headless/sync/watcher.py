"""
Real-time File Watcher

Monitors UI definition files for changes and triggers automatic reloading
for live development experience in headless mode.
"""

import os
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Callable, Set
from threading import Thread, Event
from dataclasses import dataclass

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    # Fallback to polling-based monitoring

logger = logging.getLogger(__name__)


@dataclass
class FileChangeEvent:
    """Represents a file change event."""
    file_path: Path
    event_type: str  # 'modified', 'created', 'deleted'
    timestamp: float
    checksum: Optional[str] = None


class UIFileWatcher:
    """
    Watches UI definition files for changes and triggers reload callbacks.
    
    Supports both watchdog-based monitoring (preferred) and polling fallback.
    Includes debouncing to prevent excessive reloads during rapid changes.
    """
    
    def __init__(self, 
                 watch_directories: List[Path],
                 file_patterns: List[str] = None,
                 debounce_delay: float = 0.5):
        """
        Initialize the file watcher.
        
        Args:
            watch_directories: Directories to monitor
            file_patterns: File patterns to watch (e.g., ['*.yaml', '*.json'])
            debounce_delay: Delay in seconds before triggering callback
        """
        self.watch_directories = [Path(d) for d in watch_directories]
        self.file_patterns = file_patterns or ['*.yaml', '*.yml', '*.json']
        self.debounce_delay = debounce_delay
        
        self._callbacks: Dict[str, List[Callable]] = {}
        self._observer: Optional[Observer] = None
        self._polling_thread: Optional[Thread] = None
        self._stop_event = Event()
        self._file_checksums: Dict[Path, str] = {}
        self._pending_events: Dict[Path, FileChangeEvent] = {}
        self._debounce_timer: Optional[Thread] = None
        
        self._running = False
        
    def add_callback(self, event_type: str, callback: Callable[[FileChangeEvent], None]):
        """
        Add a callback for specific event types.
        
        Args:
            event_type: 'modified', 'created', 'deleted', or 'any'
            callback: Function to call when event occurs
        """
        if event_type not in self._callbacks:
            self._callbacks[event_type] = []
        self._callbacks[event_type].append(callback)
        logger.debug(f"Added callback for {event_type} events")
    
    def start(self) -> bool:
        """
        Start monitoring files.
        
        Returns:
            True if started successfully
        """
        if self._running:
            logger.warning("File watcher is already running")
            return True
        
        # Initialize file checksums
        self._scan_initial_files()
        
        if WATCHDOG_AVAILABLE:
            return self._start_watchdog()
        else:
            logger.warning("Watchdog not available, falling back to polling")
            return self._start_polling()
    
    def stop(self):
        """Stop monitoring files."""
        if not self._running:
            return
        
        logger.info("Stopping file watcher")
        self._stop_event.set()
        self._running = False
        
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
        
        if self._polling_thread:
            self._polling_thread.join()
            self._polling_thread = None
        
        if self._debounce_timer and self._debounce_timer.is_alive():
            self._debounce_timer.join()
    
    def _start_watchdog(self) -> bool:
        """Start watchdog-based monitoring."""
        try:
            self._observer = Observer()
            handler = UIFileHandler(self)
            
            for directory in self.watch_directories:
                if directory.exists():
                    self._observer.schedule(handler, str(directory), recursive=True)
                    logger.info(f"Watching directory: {directory}")
                else:
                    logger.warning(f"Watch directory does not exist: {directory}")
            
            self._observer.start()
            self._running = True
            logger.info("File watcher started using watchdog")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start watchdog: {e}")
            return False
    
    def _start_polling(self) -> bool:
        """Start polling-based monitoring."""
        try:
            self._polling_thread = Thread(target=self._polling_loop, daemon=True)
            self._polling_thread.start()
            self._running = True
            logger.info("File watcher started using polling")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start polling: {e}")
            return False
    
    def _polling_loop(self):
        """Polling loop for file change detection."""
        while not self._stop_event.is_set():
            try:
                self._check_file_changes()
                time.sleep(1.0)  # Poll every second
            except Exception as e:
                logger.error(f"Error in polling loop: {e}")
                time.sleep(5.0)  # Wait longer on error
    
    def _scan_initial_files(self):
        """Scan initial files and store checksums."""
        for directory in self.watch_directories:
            if not directory.exists():
                continue
                
            for pattern in self.file_patterns:
                for file_path in directory.rglob(pattern):
                    if file_path.is_file():
                        checksum = self._calculate_checksum(file_path)
                        self._file_checksums[file_path] = checksum
        
        logger.debug(f"Initial scan found {len(self._file_checksums)} files")
    
    def _check_file_changes(self):
        """Check for file changes using checksums."""
        current_files = set()
        
        # Check existing and new files
        for directory in self.watch_directories:
            if not directory.exists():
                continue
                
            for pattern in self.file_patterns:
                for file_path in directory.rglob(pattern):
                    if file_path.is_file():
                        current_files.add(file_path)
                        
                        current_checksum = self._calculate_checksum(file_path)
                        previous_checksum = self._file_checksums.get(file_path)
                        
                        if previous_checksum is None:
                            # New file
                            self._file_checksums[file_path] = current_checksum
                            self._handle_file_event(file_path, 'created', current_checksum)
                        elif current_checksum != previous_checksum:
                            # Modified file
                            self._file_checksums[file_path] = current_checksum
                            self._handle_file_event(file_path, 'modified', current_checksum)
        
        # Check for deleted files
        deleted_files = set(self._file_checksums.keys()) - current_files
        for file_path in deleted_files:
            del self._file_checksums[file_path]
            self._handle_file_event(file_path, 'deleted')
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate file checksum for change detection."""
        try:
            import hashlib
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            logger.warning(f"Failed to calculate checksum for {file_path}: {e}")
            # Fallback to modification time
            return str(file_path.stat().st_mtime)
    
    def _handle_file_event(self, file_path: Path, event_type: str, checksum: str = None):
        """Handle a file system event with debouncing."""
        event = FileChangeEvent(
            file_path=file_path,
            event_type=event_type,
            timestamp=time.time(),
            checksum=checksum
        )
        
        # Add to pending events (overwrites previous event for same file)
        self._pending_events[file_path] = event
        
        # Start or restart debounce timer
        if self._debounce_timer and self._debounce_timer.is_alive():
            # Timer is already running, event will be processed when it fires
            return
        
        self._debounce_timer = Thread(target=self._debounce_callback, daemon=True)
        self._debounce_timer.start()
    
    def _debounce_callback(self):
        """Debounced callback that processes pending events."""
        time.sleep(self.debounce_delay)
        
        # Process all pending events
        events_to_process = list(self._pending_events.values())
        self._pending_events.clear()
        
        for event in events_to_process:
            self._trigger_callbacks(event)
    
    def _trigger_callbacks(self, event: FileChangeEvent):
        """Trigger registered callbacks for an event."""
        logger.info(f"File {event.event_type}: {event.file_path}")
        
        # Trigger specific event type callbacks
        for callback in self._callbacks.get(event.event_type, []):
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in callback for {event.event_type}: {e}")
        
        # Trigger 'any' event callbacks
        for callback in self._callbacks.get('any', []):
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in 'any' callback: {e}")
    
    def is_running(self) -> bool:
        """Check if the watcher is currently running."""
        return self._running
    
    def get_watched_files(self) -> List[Path]:
        """Get list of currently watched files."""
        return list(self._file_checksums.keys())


class UIFileHandler(FileSystemEventHandler):
    """Watchdog event handler for UI files."""
    
    def __init__(self, watcher: UIFileWatcher):
        self.watcher = watcher
    
    def on_modified(self, event):
        if not event.is_directory and self._should_handle_file(event.src_path):
            file_path = Path(event.src_path)
            checksum = self.watcher._calculate_checksum(file_path)
            self.watcher._handle_file_event(file_path, 'modified', checksum)
    
    def on_created(self, event):
        if not event.is_directory and self._should_handle_file(event.src_path):
            file_path = Path(event.src_path)
            checksum = self.watcher._calculate_checksum(file_path)
            self.watcher._handle_file_event(file_path, 'created', checksum)
    
    def on_deleted(self, event):
        if not event.is_directory and self._should_handle_file(event.src_path):
            file_path = Path(event.src_path)
            self.watcher._handle_file_event(file_path, 'deleted')
    
    def _should_handle_file(self, file_path: str) -> bool:
        """Check if file should be handled based on patterns."""
        path = Path(file_path)
        return any(path.match(pattern) for pattern in self.watcher.file_patterns)


# Convenience function for creating a standard UI watcher
def create_ui_watcher(project_root: Path, 
                     debounce_delay: float = 0.5) -> UIFileWatcher:
    """
    Create a standard UI file watcher for a CellSorter project.
    
    Args:
        project_root: Root directory of the project
        debounce_delay: Debounce delay in seconds
        
    Returns:
        Configured UIFileWatcher instance
    """
    watch_dirs = [
        project_root / "ui_definitions",
        project_root / "src" / "headless",
        project_root / "src" / "components",
    ]
    
    # Only watch directories that exist
    existing_dirs = [d for d in watch_dirs if d.exists()]
    
    return UIFileWatcher(
        watch_directories=existing_dirs,
        file_patterns=['*.yaml', '*.yml', '*.json', '*.py'],
        debounce_delay=debounce_delay
    ) 