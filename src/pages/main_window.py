"""
CellSorter Main Application Window

This module implements the main application window with menu bar, toolbar,
status bar, and dockable panels for the CellSorter application.
"""

from typing import Optional, Dict, Any
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QMenuBar, QToolBar, QStatusBar, QDockWidget, QLabel, QPushButton,
    QFileDialog, QMessageBox, QApplication, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer, QSettings
from PySide6.QtGui import QAction, QKeySequence, QIcon

from config.settings import (
    APP_NAME, APP_VERSION, DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT, IMAGE_PANEL_WIDTH, PLOT_PANEL_WIDTH,
    SELECTION_PANEL_WIDTH, SUPPORTED_IMAGE_FORMATS, SUPPORTED_CSV_FORMATS
)
from utils.error_handler import ErrorHandler, error_handler
from utils.logging_config import LoggerMixin


class MainWindow(QMainWindow, LoggerMixin):
    """
    Main application window for CellSorter.
    
    Provides the primary interface with menu bar, toolbar, status bar,
    and dockable panels for image viewing, data visualization, and selection management.
    """
    
    # Signals
    image_loaded = Signal(str)  # File path
    csv_loaded = Signal(str)    # File path
    session_saved = Signal(str) # File path
    session_loaded = Signal(str) # File path
    export_requested = Signal() # Export protocol request
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # Initialize error handler
        self.error_handler = ErrorHandler(self)
        
        # Initialize settings
        self.settings = QSettings(APP_NAME, APP_VERSION)
        
        # State tracking
        self.current_image_path: Optional[str] = None
        self.current_csv_path: Optional[str] = None
        self.is_modified: bool = False
        
        # UI setup
        self.setup_ui()
        self.setup_actions()
        self.setup_menu_bar()
        self.setup_toolbar()
        self.setup_status_bar()
        self.setup_dock_widgets()
        self.setup_connections()
        
        # Restore window state
        self.restore_settings()
        
        self.log_info("CellSorter main window initialized")
    
    def setup_ui(self) -> None:
        """Initialize the main window UI."""
        self.setWindowTitle(f"{APP_NAME} - {APP_VERSION}")
        self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        
        # Central widget with splitter layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(4, 4, 4, 4)
        
        # Create main splitter
        self.main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.main_splitter)
        
        # Create placeholder panels
        self.image_panel = self.create_placeholder_panel("Image Panel", "📷")
        self.plot_panel = self.create_placeholder_panel("Scatter Plot Panel", "📊") 
        self.selection_panel = self.create_placeholder_panel("Selection Panel", "📋")
        
        # Add panels to splitter
        self.main_splitter.addWidget(self.image_panel)
        self.main_splitter.addWidget(self.plot_panel)
        self.main_splitter.addWidget(self.selection_panel)
        
        # Set initial panel sizes
        total_width = DEFAULT_WINDOW_WIDTH - 50  # Account for margins
        sizes = [
            int(total_width * IMAGE_PANEL_WIDTH / 100),
            int(total_width * PLOT_PANEL_WIDTH / 100),
            int(total_width * SELECTION_PANEL_WIDTH / 100)
        ]
        self.main_splitter.setSizes(sizes)
    
    def create_placeholder_panel(self, title: str, icon: str) -> QFrame:
        """
        Create a placeholder panel with title and icon.
        
        Args:
            title: Panel title
            icon: Panel icon (emoji)
        
        Returns:
            Placeholder panel widget
        """
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        panel.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setAlignment(Qt.AlignCenter)
        
        # Icon label
        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 48px; color: #6c757d; margin: 20px;")
        
        # Title label
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #495057; margin: 10px;")
        
        # Description label
        desc_label = QLabel("Panel will be implemented\nin upcoming phases")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("font-size: 12px; color: #6c757d; margin: 10px;")
        
        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        
        return panel
    
    def setup_actions(self) -> None:
        """Create and configure UI actions."""
        # File actions
        self.action_open_image = QAction("Open &Image...", self)
        self.action_open_image.setShortcut(QKeySequence.Open)
        self.action_open_image.setStatusTip("Open microscopy image file")
        
        self.action_open_csv = QAction("Open &CSV...", self)
        self.action_open_csv.setShortcut(QKeySequence("Ctrl+Shift+O"))
        self.action_open_csv.setStatusTip("Open CellProfiler CSV data file")
        
        self.action_save_session = QAction("&Save Session", self)
        self.action_save_session.setShortcut(QKeySequence.Save)
        self.action_save_session.setStatusTip("Save current analysis session")
        self.action_save_session.setEnabled(False)
        
        self.action_load_session = QAction("&Load Session...", self)
        self.action_load_session.setShortcut(QKeySequence("Ctrl+L"))
        self.action_load_session.setStatusTip("Load previous analysis session")
        
        self.action_export_protocol = QAction("&Export Protocol...", self)
        self.action_export_protocol.setShortcut(QKeySequence("Ctrl+E"))
        self.action_export_protocol.setStatusTip("Export .cxprotocol file for CosmoSort")
        self.action_export_protocol.setEnabled(False)
        
        self.action_exit = QAction("E&xit", self)
        self.action_exit.setShortcut(QKeySequence.Quit)
        self.action_exit.setStatusTip("Exit CellSorter")
        
        # Edit actions
        self.action_undo = QAction("&Undo", self)
        self.action_undo.setShortcut(QKeySequence.Undo)
        self.action_undo.setEnabled(False)
        
        self.action_redo = QAction("&Redo", self)
        self.action_redo.setShortcut(QKeySequence.Redo)
        self.action_redo.setEnabled(False)
        
        # View actions
        self.action_zoom_in = QAction("Zoom &In", self)
        self.action_zoom_in.setShortcut(QKeySequence.ZoomIn)
        self.action_zoom_in.setEnabled(False)
        
        self.action_zoom_out = QAction("Zoom &Out", self)
        self.action_zoom_out.setShortcut(QKeySequence.ZoomOut)
        self.action_zoom_out.setEnabled(False)
        
        self.action_zoom_fit = QAction("&Fit to Window", self)
        self.action_zoom_fit.setShortcut(QKeySequence("Ctrl+0"))
        self.action_zoom_fit.setEnabled(False)
        
        self.action_toggle_overlays = QAction("Toggle &Overlays", self)
        self.action_toggle_overlays.setShortcut(QKeySequence("Ctrl+Shift+O"))
        self.action_toggle_overlays.setCheckable(True)
        self.action_toggle_overlays.setChecked(True)
        self.action_toggle_overlays.setEnabled(False)
        
        # Tools actions
        self.action_calibrate = QAction("&Calibrate Coordinates", self)
        self.action_calibrate.setShortcut(QKeySequence("Ctrl+K"))
        self.action_calibrate.setStatusTip("Set coordinate calibration points")
        self.action_calibrate.setEnabled(False)
        
        self.action_clear_selections = QAction("&Clear All Selections", self)
        self.action_clear_selections.setShortcut(QKeySequence("Ctrl+Shift+C"))
        self.action_clear_selections.setEnabled(False)
        
        # Help actions
        self.action_about = QAction("&About CellSorter", self)
        self.action_about.setStatusTip("About this application")
    
    def setup_menu_bar(self) -> None:
        """Create and configure the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        file_menu.addAction(self.action_open_image)
        file_menu.addAction(self.action_open_csv)
        file_menu.addSeparator()
        file_menu.addAction(self.action_save_session)
        file_menu.addAction(self.action_load_session)
        file_menu.addSeparator()
        file_menu.addAction(self.action_export_protocol)
        file_menu.addSeparator()
        file_menu.addAction(self.action_exit)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        edit_menu.addAction(self.action_undo)
        edit_menu.addAction(self.action_redo)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        view_menu.addAction(self.action_zoom_in)
        view_menu.addAction(self.action_zoom_out)
        view_menu.addAction(self.action_zoom_fit)
        view_menu.addSeparator()
        view_menu.addAction(self.action_toggle_overlays)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        tools_menu.addAction(self.action_calibrate)
        tools_menu.addAction(self.action_clear_selections)
        
        # Analysis menu (placeholder)
        analysis_menu = menubar.addMenu("&Analysis")
        analysis_menu.addAction("Generate Statistics...")
        analysis_menu.addAction("Batch Process...")
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        help_menu.addAction(self.action_about)
    
    def setup_toolbar(self) -> None:
        """Create and configure the toolbar."""
        toolbar = self.addToolBar("Main Toolbar")
        toolbar.setMovable(False)
        
        # File operations
        toolbar.addAction(self.action_open_image)
        toolbar.addAction(self.action_open_csv)
        toolbar.addSeparator()
        
        # Session operations
        toolbar.addAction(self.action_save_session)
        toolbar.addAction(self.action_export_protocol)
        toolbar.addSeparator()
        
        # View operations
        toolbar.addAction(self.action_zoom_in)
        toolbar.addAction(self.action_zoom_out)
        toolbar.addAction(self.action_zoom_fit)
        toolbar.addSeparator()
        
        # Tools
        toolbar.addAction(self.action_calibrate)
        
        # Add spacer to push theme toggle to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)
        
        # Theme toggle (placeholder)
        self.theme_button = QPushButton("🌙")
        self.theme_button.setFixedSize(32, 32)
        self.theme_button.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 16px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
        """)
        self.theme_button.setToolTip("Toggle theme (Light/Dark)")
        toolbar.addWidget(self.theme_button)
    
    def setup_status_bar(self) -> None:
        """Create and configure the status bar."""
        self.status_bar = self.statusBar()
        
        # Ready message
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)
        
        # Cell count indicator
        self.cell_count_label = QLabel("")
        self.status_bar.addPermanentWidget(self.cell_count_label)
        
        # Zoom indicator
        self.zoom_label = QLabel("")
        self.status_bar.addPermanentWidget(self.zoom_label)
        
        # Coordinate indicator
        self.coord_label = QLabel("")
        self.status_bar.addPermanentWidget(self.coord_label)
    
    def setup_dock_widgets(self) -> None:
        """Create dockable widgets (for future expansion)."""
        # This method is prepared for future dockable panels
        # Currently, panels are embedded in the main splitter
        pass
    
    def setup_connections(self) -> None:
        """Connect signals and slots."""
        # File actions
        self.action_open_image.triggered.connect(self.open_image_file)
        self.action_open_csv.triggered.connect(self.open_csv_file)
        self.action_save_session.triggered.connect(self.save_session)
        self.action_load_session.triggered.connect(self.load_session)
        self.action_export_protocol.triggered.connect(self.export_protocol)
        self.action_exit.triggered.connect(self.close)
        
        # Edit actions
        self.action_undo.triggered.connect(self.undo)
        self.action_redo.triggered.connect(self.redo)
        
        # View actions
        self.action_zoom_in.triggered.connect(self.zoom_in)
        self.action_zoom_out.triggered.connect(self.zoom_out)
        self.action_zoom_fit.triggered.connect(self.zoom_fit)
        self.action_toggle_overlays.triggered.connect(self.toggle_overlays)
        
        # Tools actions
        self.action_calibrate.triggered.connect(self.calibrate_coordinates)
        self.action_clear_selections.triggered.connect(self.clear_selections)
        
        # Help actions
        self.action_about.triggered.connect(self.show_about)
        
        # Theme button
        self.theme_button.clicked.connect(self.toggle_theme)
    
    @error_handler("Opening image file")
    def open_image_file(self) -> None:
        """Open an image file dialog and load selected image."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Image File",
            "",
            f"Image Files ({' '.join(f'*{ext}' for ext in SUPPORTED_IMAGE_FORMATS)})"
        )
        
        if file_path:
            self.current_image_path = file_path
            self.image_loaded.emit(file_path)
            self.update_status(f"Loaded image: {Path(file_path).name}")
            self.update_window_title()
            self.enable_image_actions()
            self.log_info(f"Image loaded: {file_path}")
    
    @error_handler("Opening CSV file")
    def open_csv_file(self) -> None:
        """Open a CSV file dialog and load selected data."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open CSV File",
            "",
            f"CSV Files ({' '.join(f'*{ext}' for ext in SUPPORTED_CSV_FORMATS)})"
        )
        
        if file_path:
            self.current_csv_path = file_path
            self.csv_loaded.emit(file_path)
            self.update_status(f"Loaded CSV: {Path(file_path).name}")
            self.update_window_title()
            self.enable_analysis_actions()
            self.log_info(f"CSV loaded: {file_path}")
    
    @error_handler("Saving session")
    def save_session(self) -> None:
        """Save current analysis session."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Session",
            "",
            "Session Files (*.cellsession)"
        )
        
        if file_path:
            self.session_saved.emit(file_path)
            self.update_status(f"Session saved: {Path(file_path).name}")
            self.is_modified = False
            self.log_info(f"Session saved: {file_path}")
    
    @error_handler("Loading session")
    def load_session(self) -> None:
        """Load a previous analysis session."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Session",
            "",
            "Session Files (*.cellsession)"
        )
        
        if file_path:
            self.session_loaded.emit(file_path)
            self.update_status(f"Session loaded: {Path(file_path).name}")
            self.update_window_title()
            self.log_info(f"Session loaded: {file_path}")
    
    @error_handler("Exporting protocol")
    def export_protocol(self) -> None:
        """Export .cxprotocol file for CosmoSort."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Protocol",
            "",
            "CosmoSort Protocol (*.cxprotocol)"
        )
        
        if file_path:
            self.export_requested.emit()
            self.update_status(f"Protocol exported: {Path(file_path).name}")
            self.log_info(f"Protocol exported: {file_path}")
    
    def undo(self) -> None:
        """Undo last action."""
        self.update_status("Undo performed")
    
    def redo(self) -> None:
        """Redo last undone action."""
        self.update_status("Redo performed")
    
    def zoom_in(self) -> None:
        """Zoom in on image."""
        self.update_status("Zoomed in")
    
    def zoom_out(self) -> None:
        """Zoom out on image."""
        self.update_status("Zoomed out")
    
    def zoom_fit(self) -> None:
        """Fit image to window."""
        self.update_status("Fit to window")
    
    def toggle_overlays(self) -> None:
        """Toggle cell overlay visibility."""
        enabled = self.action_toggle_overlays.isChecked()
        self.update_status(f"Overlays {'enabled' if enabled else 'disabled'}")
    
    def calibrate_coordinates(self) -> None:
        """Start coordinate calibration process."""
        self.update_status("Coordinate calibration mode activated")
    
    def clear_selections(self) -> None:
        """Clear all cell selections."""
        self.update_status("All selections cleared")
    
    def toggle_theme(self) -> None:
        """Toggle between light and dark themes."""
        # TODO: Implement theme switching
        current_text = self.theme_button.text()
        new_text = "☀️" if current_text == "🌙" else "🌙"
        self.theme_button.setText(new_text)
        self.update_status("Theme toggled")
    
    def show_about(self) -> None:
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About CellSorter",
            f"""
            <h3>{APP_NAME} {APP_VERSION}</h3>
            <p>Advanced Cell Sorting and Tissue Extraction Software</p>
            <p>Designed for precision cell sorting workflows in pathology research.</p>
            <p><b>Features:</b></p>
            <ul>
            <li>Multi-format image support (TIFF, JPG, PNG)</li>
            <li>CellProfiler integration</li>
            <li>Interactive data visualization</li>
            <li>Coordinate calibration system</li>
            <li>CosmoSort hardware integration</li>
            </ul>
            <p><small>Built with PySide6 and scientific Python libraries.</small></p>
            """
        )
    
    def update_status(self, message: str) -> None:
        """Update status bar message."""
        self.status_label.setText(message)
        
        # Auto-clear status after 5 seconds
        QTimer.singleShot(5000, lambda: self.status_label.setText("Ready"))
    
    def update_cell_count(self, count: int) -> None:
        """Update cell count indicator."""
        self.cell_count_label.setText(f"{count:,} cells" if count > 0 else "")
    
    def update_zoom_level(self, zoom: float) -> None:
        """Update zoom level indicator."""
        self.zoom_label.setText(f"Zoom: {zoom:.0%}" if zoom != 1.0 else "")
    
    def update_coordinates(self, x: float, y: float) -> None:
        """Update coordinate indicator."""
        self.coord_label.setText(f"({x:.1f}, {y:.1f})")
    
    def update_window_title(self) -> None:
        """Update window title with current file information."""
        title = f"{APP_NAME} - {APP_VERSION}"
        
        if self.current_image_path or self.current_csv_path:
            files = []
            if self.current_image_path:
                files.append(Path(self.current_image_path).name)
            if self.current_csv_path:
                files.append(Path(self.current_csv_path).name)
            title += f" - {', '.join(files)}"
        
        if self.is_modified:
            title += " *"
        
        self.setWindowTitle(title)
    
    def enable_image_actions(self) -> None:
        """Enable actions that require an image to be loaded."""
        self.action_zoom_in.setEnabled(True)
        self.action_zoom_out.setEnabled(True)
        self.action_zoom_fit.setEnabled(True)
        self.action_toggle_overlays.setEnabled(True)
        self.action_calibrate.setEnabled(True)
    
    def enable_analysis_actions(self) -> None:
        """Enable actions that require data to be loaded."""
        self.action_save_session.setEnabled(True)
        
        # Enable export if both image and CSV are loaded
        if self.current_image_path and self.current_csv_path:
            self.action_export_protocol.setEnabled(True)
            self.action_clear_selections.setEnabled(True)
    
    def restore_settings(self) -> None:
        """Restore window settings from previous session."""
        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
            
            state = self.settings.value("windowState")
            if state:
                self.restoreState(state)
            
            splitter_state = self.settings.value("splitterState")
            if splitter_state:
                self.main_splitter.restoreState(splitter_state)
        except Exception as e:
            self.log_warning(f"Failed to restore settings: {e}")
    
    def save_settings(self) -> None:
        """Save window settings for next session."""
        try:
            self.settings.setValue("geometry", self.saveGeometry())
            self.settings.setValue("windowState", self.saveState())
            self.settings.setValue("splitterState", self.main_splitter.saveState())
        except Exception as e:
            self.log_warning(f"Failed to save settings: {e}")
    
    def closeEvent(self, event) -> None:
        """Handle application close event."""
        if self.is_modified:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before closing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Save:
                self.save_session()
                if self.is_modified:  # Save was cancelled
                    event.ignore()
                    return
            elif reply == QMessageBox.Cancel:
                event.ignore()
                return
        
        # Save settings
        self.save_settings()
        
        # Accept close event
        self.log_info("CellSorter application closing")
        event.accept()