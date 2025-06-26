"""
CellSorter Main Application Window

This module implements the main application window with menu bar, toolbar,
status bar, and dockable panels for the CellSorter application.
"""

from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QMenuBar, QToolBar, QStatusBar, QDockWidget, QLabel, QPushButton,
    QFileDialog, QMessageBox, QApplication, QFrame, QSizePolicy, QDialog
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
from services.theme_manager import ThemeManager
from models.image_handler import ImageHandler
from models.csv_parser import CSVParser
from models.coordinate_transformer import CoordinateTransformer
from models.selection_manager import SelectionManager
from models.extractor import Extractor
from models.session_manager import SessionManager
from components.widgets.scatter_plot import ScatterPlotWidget
from components.widgets.selection_panel import SelectionPanel
from components.dialogs.calibration_dialog import CalibrationDialog
from components.dialogs.export_dialog import ExportDialog
from components.dialogs.batch_process_dialog import BatchProcessDialog


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
    
    def __init__(self, theme_manager: ThemeManager, update_checker=None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # Initialize error handler
        self.error_handler = ErrorHandler(self)
        
        # Initialize theme manager
        self.theme_manager = theme_manager
        self.settings = QSettings(APP_NAME, APP_VERSION)
        self.theme_manager.apply_theme(self.settings.value("theme", "light"))
        
        # Initialize update checker
        self.update_checker = update_checker
        if self.update_checker:
            self.update_checker.update_available.connect(self._on_update_available)
        
        # State tracking
        self.current_image_path: Optional[str] = None
        self.current_csv_path: Optional[str] = None
        self.is_modified: bool = False
        
        # Initialize core components
        self.image_handler = ImageHandler(self)
        self.csv_parser = CSVParser(self)
        self.coordinate_transformer = CoordinateTransformer(self)
        self.selection_manager = SelectionManager(self)
        self.extractor = Extractor(self)
        self.session_manager = SessionManager(self)
        self.scatter_plot_widget = ScatterPlotWidget(self)
        self.selection_panel = SelectionPanel(self)
        
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
        
        # Add real components to splitter
        self.main_splitter.addWidget(self.image_handler)
        self.main_splitter.addWidget(self.scatter_plot_widget)
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
        
        # Analysis actions
        self.action_batch_process = QAction("&Batch Process...", self)
        self.action_batch_process.setShortcut(QKeySequence("Ctrl+B"))
        self.action_batch_process.setStatusTip("Process multiple image/CSV file pairs")
        
        # Help actions
        self.action_about = QAction("&About CellSorter", self)
        self.action_about.setStatusTip("About this application")
        
        self.action_check_updates = QAction("Check for &Updates...", self)
        self.action_check_updates.setStatusTip("Check for new versions of CellSorter")
        
        self.action_update_preferences = QAction("Update &Preferences...", self)
        self.action_update_preferences.setStatusTip("Configure automatic update checking")
    
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
        
        # Analysis menu
        analysis_menu = menubar.addMenu("&Analysis")
        analysis_menu.addAction("Generate Statistics...")
        analysis_menu.addAction(self.action_batch_process)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        help_menu.addAction("User &Guide")
        help_menu.addAction("&Tutorial")
        help_menu.addSeparator()
        help_menu.addAction(self.action_check_updates)
        help_menu.addAction(self.action_update_preferences)
        help_menu.addSeparator()
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
        
        # Analysis actions
        self.action_batch_process.triggered.connect(self.batch_process)
        
        # Help actions
        self.action_about.triggered.connect(self.show_about)
        self.action_check_updates.triggered.connect(self.check_for_updates)
        self.action_update_preferences.triggered.connect(self.show_update_preferences)
        
        # Theme button
        self.theme_button.clicked.connect(self.toggle_theme)
        
        # Component connections
        self.csv_parser.csv_loaded.connect(self._on_csv_loaded)
        self.csv_parser.csv_load_failed.connect(self._on_csv_load_failed)
        self.image_handler.image_loaded.connect(self._on_image_loaded)
        self.image_handler.image_load_failed.connect(self._on_image_load_failed)
        self.scatter_plot_widget.selection_made.connect(self._on_selection_made)
        
        # Connect expression filter specific signals if available
        if hasattr(self.scatter_plot_widget, 'expression_selection_made'):
            self.scatter_plot_widget.expression_selection_made.connect(self._on_expression_selection_made)
        
        self.coordinate_transformer.calibration_updated.connect(self._on_calibration_updated)
        self.selection_manager.selection_added.connect(self._on_selection_added)
        self.selection_manager.selection_updated.connect(self._on_selection_updated)
        self.selection_manager.selection_removed.connect(self._on_selection_removed)
        self.selection_panel.selection_deleted.connect(self._on_panel_selection_deleted)
        self.selection_panel.export_requested.connect(self.export_protocol)
        
        # Image handler connections
        self.image_handler.coordinates_changed.connect(self.update_coordinates)
        self.image_handler.calibration_point_clicked.connect(self._on_calibration_point_clicked)
    
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
            self.image_handler.load_image(file_path)  # Use actual image handler
            self.update_status(f"Loading image: {Path(file_path).name}")
            self.update_window_title()
            self.log_info(f"Loading image: {file_path}")
    
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
            self.csv_parser.load_csv(file_path)  # Use actual CSV parser
            self.update_status(f"Loading CSV: {Path(file_path).name}")
            self.update_window_title()
            self.log_info(f"Loading CSV: {file_path}")
    
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
            # Collect current session data
            session_data = self._collect_session_data()
            
            # Save using session manager
            if self.session_manager.save_session(file_path, session_data):
                self.session_saved.emit(file_path)
                self.update_status(f"Session saved: {Path(file_path).name}")
                self.is_modified = False
                self.log_info(f"Session saved: {file_path}")
            else:
                QMessageBox.warning(self, "Save Failed", "Failed to save session file.")
                self.log_error(f"Failed to save session: {file_path}")
    
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
            # Load using session manager
            session_data = self.session_manager.load_session(file_path)
            
            if session_data:
                # Restore session data
                self._restore_session_data(session_data)
                self.session_loaded.emit(file_path)
                self.update_status(f"Session loaded: {Path(file_path).name}")
                self.update_window_title()
                self.log_info(f"Session loaded: {file_path}")
            else:
                QMessageBox.warning(self, "Load Failed", "Failed to load session file.")
                self.log_error(f"Failed to load session: {file_path}")
    
    @error_handler("Exporting analysis results")
    def export_protocol(self) -> None:
        """Export analysis results with comprehensive options."""
        if not self.current_csv_path and not self.current_image_path:
            QMessageBox.warning(self, "No Data", "Please load data before exporting.")
            return
        
        # Show export dialog
        export_dialog = ExportDialog(self)
        if export_dialog.exec() == QDialog.Accepted:
            self.export_requested.emit()
            self.update_status("Export completed successfully")
            self.log_info("Analysis results exported")
    
    @error_handler("Starting batch processing")
    def batch_process(self) -> None:
        """Open batch processing dialog for multiple file pairs."""
        # Show batch processing dialog
        batch_dialog = BatchProcessDialog(self)
        if batch_dialog.exec() == QDialog.Accepted:
            self.update_status("Batch processing completed")
            self.log_info("Batch processing completed")
    
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
        if not self.current_image_path:
            QMessageBox.warning(self, "No Image", "Please load an image first.")
            return
        
        # Toggle calibration mode
        current_mode = getattr(self.image_handler, 'calibration_mode', False)
        new_mode = not current_mode
        
        self.image_handler.set_calibration_mode(new_mode)
        
        if new_mode:
            self.update_status("Calibration mode: Click on reference points on the image")
            self.action_calibrate.setText("Exit &Calibration")
        else:
            self.update_status("Calibration mode disabled")
            self.action_calibrate.setText("&Calibrate Coordinates")
    
    def clear_selections(self) -> None:
        """Clear all cell selections."""
        self.update_status("All selections cleared")
    
    def toggle_theme(self) -> None:
        """Toggle between light and dark themes."""
        self.theme_manager.toggle_theme()
        current_theme = self.theme_manager.get_current_theme()
        self.theme_button.setText("☀️" if current_theme == "dark" else "🌙")
        self.update_status(f"Theme switched to: {current_theme}")
    
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
    
    # Component callback methods
    def _on_image_loaded(self, file_path: str) -> None:
        """Handle successful image loading."""
        self.image_loaded.emit(file_path)
        self.update_status(f"Image loaded: {Path(file_path).name}")
        self.enable_image_actions()
        self.log_info(f"Image successfully loaded: {file_path}")
    
    def _on_image_load_failed(self, error_message: str) -> None:
        """Handle failed image loading."""
        self.update_status(f"Image loading failed: {error_message}")
        self.log_error(f"Image loading failed: {error_message}")
    
    def _on_csv_loaded(self, file_path: str) -> None:
        """Handle successful CSV loading."""
        # Load data into scatter plot widget
        if self.csv_parser.data is not None:
            self.scatter_plot_widget.load_data(self.csv_parser.data)
            
            # Extract bounding boxes for cell highlighting
            bounding_box_data = self.csv_parser.get_bounding_box_data()
            if bounding_box_data is not None:
                bounding_boxes = []
                for _, row in bounding_box_data.iterrows():
                    bbox = (
                        int(row['AreaShape_BoundingBoxMinimum_X']),
                        int(row['AreaShape_BoundingBoxMinimum_Y']),
                        int(row['AreaShape_BoundingBoxMaximum_X']),
                        int(row['AreaShape_BoundingBoxMaximum_Y'])
                    )
                    bounding_boxes.append(bbox)
                
                self.image_handler.set_bounding_boxes(bounding_boxes)
                self.log_info(f"Set {len(bounding_boxes)} bounding boxes for cell highlighting")
        
        self.csv_loaded.emit(file_path)
        self.update_status(f"CSV loaded: {Path(file_path).name}")
        self.enable_analysis_actions()
        self.log_info(f"CSV successfully loaded: {file_path}")
    
    def _on_csv_load_failed(self, error_message: str) -> None:
        """Handle failed CSV loading."""
        self.update_status(f"CSV loading failed: {error_message}")
        self.log_error(f"CSV loading failed: {error_message}")
    
    def _on_selection_made(self, indices: list) -> None:
        """Handle cell selection from scatter plot (rectangle or expression)."""
        if indices:
            # Determine selection type based on current mode
            selection_type = getattr(self.scatter_plot_widget, 'current_selection_type', 'rectangle')
            
            # Add selection to selection manager
            label_prefix = "Expression" if selection_type == "expression" else "Rectangle"
            selection_id = self.selection_manager.add_selection(
                cell_indices=indices,
                label=f"{label_prefix}_{len(self.selection_manager.selections) + 1}"
            )
            
            if selection_id:
                selection_method = "expression filter" if selection_type == "expression" else "rectangle selection"
                self.update_status(f"Selected {len(indices)} cells using {selection_method}")
                self.is_modified = True
                self.update_window_title()
                
                # Log expression details if available
                if selection_type == "expression" and hasattr(self.scatter_plot_widget, 'get_current_expression'):
                    expression = self.scatter_plot_widget.get_current_expression()
                    if expression:
                        self.log_info(f"Expression selection: {expression} -> {len(indices)} cells")
        else:
            self.update_status("No cells selected")
    
    def _on_expression_selection_made(self, indices: list) -> None:
        """Handle cell selection specifically from expression filter."""
        if indices:
            # Add selection to selection manager with expression prefix
            selection_id = self.selection_manager.add_selection(
                cell_indices=indices,
                label=f"Expression_{len(self.selection_manager.selections) + 1}"
            )
            
            if selection_id:
                # Get expression details if available
                expression = ""
                if hasattr(self.scatter_plot_widget, 'get_current_expression'):
                    expression = self.scatter_plot_widget.get_current_expression()
                
                self.update_status(f"Expression filter selected {len(indices)} cells")
                self.is_modified = True
                self.update_window_title()
                
                # Store expression in selection metadata
                selection = self.selection_manager.get_selection(selection_id)
                if selection and expression:
                    selection.metadata['expression'] = expression
                    selection.metadata['selection_method'] = 'expression_filter'
                    self.log_info(f"Expression selection: {expression} -> {len(indices)} cells")
        else:
            self.update_status("No cells selected by expression filter")
    
    def _on_calibration_updated(self, is_valid: bool) -> None:
        """Handle calibration update."""
        if is_valid:
            self.update_status("Coordinate calibration updated")
        else:
            self.update_status("Calibration cleared")
        
        self.is_modified = True
        self.update_window_title()
    
    def _on_selection_added(self, selection_id: str) -> None:
        """Handle new selection added."""
        selection = self.selection_manager.get_selection(selection_id)
        if selection:
            # Highlight cells on image
            self.image_handler.highlight_cells(
                selection_id, 
                selection.cell_indices, 
                selection.color,
                alpha=0.4
            )
            
            # Update selection panel display
            selection_data = {
                'id': selection.id,
                'label': selection.label,
                'color': selection.color,
                'well_position': selection.well_position,
                'cell_indices': selection.cell_indices,
                'enabled': selection.status.value == 'active'
            }
            self.selection_panel.add_selection(selection_data)
            
            self.update_status(f"Added selection: {selection.label}")
            self.is_modified = True
            self.update_window_title()
    
    def _on_selection_updated(self, selection_id: str) -> None:
        """Handle selection update."""
        selection = self.selection_manager.get_selection(selection_id)
        if selection:
            # Update selection panel
            selection_data = {
                'id': selection.id,
                'label': selection.label,
                'color': selection.color,
                'well_position': selection.well_position,
                'cell_indices': selection.cell_indices,
                'enabled': selection.status.value == 'active'
            }
            self.selection_panel.update_selection(selection_id, selection_data)
            
            # Update image highlights
            self.image_handler.highlight_cells(
                selection_id, 
                selection.cell_indices, 
                selection.color,
                alpha=0.4
            )
            
            self.is_modified = True
            self.update_window_title()
    
    def _on_selection_removed(self, selection_id: str) -> None:
        """Handle selection removal."""
        # Remove image highlights
        self.image_handler.remove_cell_highlights(selection_id)
        
        self.is_modified = True
        self.update_window_title()
    
    def _on_panel_selection_deleted(self, selection_id: str) -> None:
        """Handle selection deletion from panel."""
        # Remove from selection manager
        self.selection_manager.remove_selection(selection_id)
        
        # Remove image highlights
        self.image_handler.remove_cell_highlights(selection_id)
    
    def _collect_session_data(self) -> Dict[str, Any]:
        """
        Collect current session data for saving.
        
        Returns:
            Session data dictionary
        """
        # Get current selections
        selections_data = []
        for selection in self.selection_manager.get_all_selections():
            selection_data = {
                'id': selection.id,
                'label': selection.label,
                'color': selection.color,
                'cell_indices': selection.cell_indices,
                'well_position': selection.well_position,
                'status': selection.status.value,
                'created_at': datetime.fromtimestamp(selection.created_timestamp).isoformat(),
                'metadata': selection.metadata
            }
            selections_data.append(selection_data)
        
        # Get calibration data
        calibration_data = {
            'points': [],
            'transformation_matrix': None,
            'is_calibrated': self.coordinate_transformer.is_calibrated()
        }
        
        for point in self.coordinate_transformer.calibration_points:
            point_data = {
                'pixel_x': point.pixel_x,
                'pixel_y': point.pixel_y,
                'stage_x': point.stage_x,
                'stage_y': point.stage_y,
                'label': point.label
            }
            calibration_data['points'].append(point_data)
        
        if self.coordinate_transformer.transform_matrix is not None:
            calibration_data['transformation_matrix'] = self.coordinate_transformer.transform_matrix.tolist()
        
        # Get well assignments
        well_assignments = {}
        for selection in self.selection_manager.get_all_selections():
            if selection.well_position:
                well_assignments[selection.well_position] = {
                    'selection_id': selection.id,
                    'label': selection.label,
                    'color': selection.color
                }
        
        # Create session data
        session_data = self.session_manager.create_new_session()
        session_data['data'].update({
            'image_file': self.current_image_path,
            'csv_file': self.current_csv_path,
            'calibration': calibration_data,
            'selections': selections_data,
            'well_assignments': well_assignments,
            'settings': {
                'zoom_level': getattr(self.image_handler, 'zoom_level', 1.0),
                'show_overlays': getattr(self.image_handler, 'show_overlays', True),
                'overlay_alpha': 0.5
            }
        })
        
        return session_data
    
    def _restore_session_data(self, session_data: Dict[str, Any]) -> None:
        """
        Restore session data after loading.
        
        Args:
            session_data: Session data to restore
        """
        data = session_data.get('data', {})
        
        # Clear current state
        self.selection_manager.clear_all_selections()
        self.coordinate_transformer.clear_calibration()
        self.image_handler.clear_all_cell_highlights()
        
        # Restore files
        image_file = data.get('image_file')
        csv_file = data.get('csv_file')
        
        if image_file and Path(image_file).exists():
            self.current_image_path = image_file
            self.image_handler.load_image(image_file)
        
        if csv_file and Path(csv_file).exists():
            self.current_csv_path = csv_file
            self.csv_parser.load_csv(csv_file)
        
        # Restore calibration
        calibration_data = data.get('calibration', {})
        for point_data in calibration_data.get('points', []):
            self.coordinate_transformer.add_calibration_point(
                point_data['pixel_x'],
                point_data['pixel_y'],
                point_data['stage_x'],
                point_data['stage_y'],
                point_data['label']
            )
        
        # Restore selections
        for selection_data in data.get('selections', []):
            selection_id = self.selection_manager.add_selection(
                cell_indices=selection_data['cell_indices'],
                color=selection_data.get('color'),
                label=selection_data['label']
            )
            
            # Restore well assignment
            well_position = selection_data.get('well_position')
            if well_position and selection_id:
                selection = self.selection_manager.get_selection(selection_id)
                if selection:
                    selection.well_position = well_position
        
        # Restore settings
        settings = data.get('settings', {})
        if hasattr(self.image_handler, 'zoom_level'):
            self.image_handler.zoom_level = settings.get('zoom_level', 1.0)
        if hasattr(self.image_handler, 'show_overlays'):
            self.image_handler.show_overlays = settings.get('show_overlays', True)
        
        self.is_modified = False
        self.log_info("Session data restored successfully")
    
    def _on_calibration_point_clicked(self, image_x: int, image_y: int, point_label: str) -> None:
        """Handle calibration point clicked on image."""
        # Show dialog to enter stage coordinates
        dialog = CalibrationDialog(image_x, image_y, point_label, self)
        
        if dialog.exec() == QDialog.Accepted:
            stage_x, stage_y = dialog.get_stage_coordinates()
            
            # Add calibration point to coordinate transformer
            success = self.coordinate_transformer.add_calibration_point(
                image_x, image_y, stage_x, stage_y, point_label
            )
            
            if success:
                self.update_status(f"Added calibration point: {point_label} "
                                 f"({image_x}, {image_y}) → ({stage_x:.3f}, {stage_y:.3f})")
                
                # Check if we have enough points for calibration
                if len(self.coordinate_transformer.calibration_points) >= 2:
                    if self.coordinate_transformer.is_calibrated():
                        self.update_status("Coordinate calibration completed successfully!")
                        # Exit calibration mode
                        self.image_handler.set_calibration_mode(False)
                        self.action_calibrate.setText("&Calibrate Coordinates")
                    else:
                        self.update_status("Calibration points too close. Please select points further apart.")
            else:
                self.update_status("Failed to add calibration point")
        else:
            # Remove the point from image handler if dialog was cancelled
            if hasattr(self.image_handler, 'calibration_points'):
                if self.image_handler.calibration_points:
                    self.image_handler.calibration_points.pop()
                    self.image_handler._update_display()
    
    def check_for_updates(self) -> None:
        """Manually check for application updates."""
        if self.update_checker:
            self.update_checker.check_for_updates(force=True)
            self.update_status("Checking for updates...")
        else:
            QMessageBox.information(self, "Update Check", 
                                  "Update checking is not available in this version.")
    
    def show_update_preferences(self) -> None:
        """Show update preferences dialog."""
        if not self.update_checker:
            return
            
        dialog = QDialog(self)
        dialog.setWindowTitle("Update Preferences")
        dialog.setFixedSize(400, 200)
        
        layout = QVBoxLayout(dialog)
        
        # Auto-check checkbox
        from PySide6.QtWidgets import QCheckBox, QDialogButtonBox
        auto_check = QCheckBox("Automatically check for updates")
        auto_check.setChecked(self.update_checker.auto_check_enabled)
        layout.addWidget(auto_check)
        
        # Info label
        info_label = QLabel("CellSorter will check for updates once a week when this option is enabled.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; margin: 10px 0;")
        layout.addWidget(info_label)
        
        # Current version info
        version_label = QLabel(f"Current version: {APP_VERSION}")
        layout.addWidget(version_label)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.Accepted:
            self.update_checker.auto_check_enabled = auto_check.isChecked()
            self.log_info(f"Update auto-check set to: {auto_check.isChecked()}")
    
    def _on_update_available(self, current_version: str, latest_version: str, download_url: str) -> None:
        """Handle update available notification."""
        if self.update_checker:
            self.update_checker.show_update_dialog(self, current_version, latest_version, download_url)