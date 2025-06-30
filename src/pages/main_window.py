"""
CellSorter Main Application Window

This module implements the main application window with menu bar, toolbar,
status bar, and dockable panels for the CellSorter application.

Supports both traditional GUI mode and headless development mode.
"""

from typing import Optional, Dict, Any, Union
from pathlib import Path
from datetime import datetime
import platform

import numpy as np

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QMenuBar, QToolBar, QStatusBar, QDockWidget, QLabel, QPushButton,
    QFileDialog, QMessageBox, QApplication, QFrame, QSizePolicy, QDialog
)
from PySide6.QtCore import Qt, Signal, QTimer, QSettings, QRect, QSize
from PySide6.QtGui import QAction, QKeySequence, QIcon, QImage

# Headless mode imports
from headless.mode_manager import is_dev_mode, is_dual_mode, get_mode_info
from headless.main_window_adapter import MainWindowAdapter
from headless.ui_compatibility import UI

from config.settings import (
    APP_NAME, APP_VERSION, DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT, IMAGE_PANEL_WIDTH, PLOT_PANEL_WIDTH,
    SELECTION_PANEL_WIDTH, SUPPORTED_IMAGE_FORMATS, SUPPORTED_CSV_FORMATS,
    MIN_IMAGE_PANEL_WIDTH, MIN_PLOT_PANEL_WIDTH, MIN_SELECTION_PANEL_WIDTH,
    PANEL_MARGIN, COMPONENT_SPACING, BUTTON_SPACING, BUTTON_HEIGHT, BUTTON_MIN_WIDTH,
    BREAKPOINT_MOBILE, BREAKPOINT_TABLET, BREAKPOINT_DESKTOP
)
from utils.error_handler import ErrorHandler, error_handler
from utils.logging_config import LoggerMixin
from services.theme_manager import ThemeManager
from models.image_handler import ImageHandler
from models.csv_parser import CSVParser
from models.coordinate_transformer import CoordinateTransformer
from models.selection_manager import SelectionManager
from models.extractor import Extractor
from components.widgets.scatter_plot import ScatterPlotWidget
from components.widgets.selection_panel import SelectionPanel
from components.widgets.minimap import MinimapWidget
from components.dialogs.calibration_dialog import CalibrationDialog
from components.dialogs.export_dialog import ExportDialog


class MainWindow(QMainWindow, LoggerMixin):
    """
    Main application window for CellSorter.
    
    Provides the primary interface with menu bar, toolbar, status bar,
    and dockable panels for image viewing, data visualization, and selection management.
    
    Supports both traditional GUI mode and headless development mode through
    the MainWindowAdapter pattern.
    """
    
    # Signals
    image_loaded = Signal(str)  # File path
    csv_loaded = Signal(str)    # File path
    export_requested = Signal() # Export protocol request
    
    def __init__(self, theme_manager: ThemeManager, update_checker=None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # Initialize error handler
        self.error_handler = ErrorHandler(self)
        
        # Initialize theme manager (light theme only)
        self.theme_manager = theme_manager
        self.update_checker = update_checker
        
        # Component state tracking - removed session management
        self.current_image_path: Optional[str] = None
        self.current_csv_path: Optional[str] = None
        
        # QSettings for window state persistence only
        self.settings = QSettings("CellSorter", "MainWindow")
        
        # Initialize theme manager (light theme only)
        self.theme_manager.apply_theme("light")
        
        # Initialize update checker
        if self.update_checker:
            self.update_checker.update_available.connect(self._on_update_available)
        
        # Initialize core components
        self.image_handler = ImageHandler(self)
        self.csv_parser = CSVParser(self)
        self.coordinate_transformer = CoordinateTransformer(self)
        self.selection_manager = SelectionManager(self)
        self.extractor = Extractor(self)
        self.scatter_plot_widget = ScatterPlotWidget(self)
        self.selection_panel = SelectionPanel(self)
        
        # Initialize minimap widget
        self.minimap_widget = MinimapWidget(self)
        
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
        """Initialize the main window UI with responsive layout and minimum size constraints."""
        self.setWindowTitle(f"{APP_NAME} - {APP_VERSION}")
        self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        
        # Fix titlebar visibility on macOS
        if platform.system() == "Darwin":  # macOS
            # Ensure title bar is visible on macOS
            self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.WindowCloseButtonHint | 
                              Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)
            # Set unified title and toolbar look on macOS
            self.setUnifiedTitleAndToolBarOnMac(True)
        else:
            # Standard window flags for Windows/Linux
            self.setWindowFlags(Qt.Window)
        
        # Central widget with splitter layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout with proper margins
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(PANEL_MARGIN, PANEL_MARGIN, PANEL_MARGIN, PANEL_MARGIN)
        main_layout.setSpacing(COMPONENT_SPACING)
        
        # Create main splitter with minimum size constraints
        self.main_splitter = QSplitter(Qt.Horizontal)
        
        # Configure splitter to prevent panels from collapsing completely
        self.main_splitter.setChildrenCollapsible(False)
        self.main_splitter.setHandleWidth(6)  # Slightly wider handle for better usability
        
        # Set minimum sizes for each panel to prevent disappearing
        self.image_handler.setMinimumWidth(MIN_IMAGE_PANEL_WIDTH)
        self.scatter_plot_widget.setMinimumWidth(MIN_PLOT_PANEL_WIDTH)
        self.selection_panel.setMinimumWidth(MIN_SELECTION_PANEL_WIDTH)
        
        # Set size policies for better responsive behavior
        self.image_handler.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.scatter_plot_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.selection_panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        
        # Add real components to splitter
        self.main_splitter.addWidget(self.image_handler)
        self.main_splitter.addWidget(self.scatter_plot_widget)
        self.main_splitter.addWidget(self.selection_panel)
        
        main_layout.addWidget(self.main_splitter)
        
        # Create minimap overlay on image handler
        self.minimap_widget.setParent(self.image_handler)
        self.minimap_widget.move(10, 10)  # Position in top-left corner
        self.minimap_widget.raise_()  # Ensure it's on top
        
        # Set initial panel sizes with responsive calculation
        self.setup_responsive_layout()
        
        # Connect resize event for responsive behavior
        self.original_resize_event = super().resizeEvent
    
    def setup_responsive_layout(self) -> None:
        """Setup responsive layout based on current window size."""
        current_width = self.width()
        
        # Calculate available width (subtract margins and splitter handles)
        available_width = current_width - (PANEL_MARGIN * 2) - (self.main_splitter.handleWidth() * 2)
        
        # Determine layout mode based on window width
        if current_width < BREAKPOINT_TABLET:
            # Compact layout for smaller windows
            image_width = max(MIN_IMAGE_PANEL_WIDTH, int(available_width * 0.3))
            plot_width = max(MIN_PLOT_PANEL_WIDTH, int(available_width * 0.4))
            selection_width = max(MIN_SELECTION_PANEL_WIDTH, available_width - image_width - plot_width)
        else:
            # Standard layout for larger windows
            image_width = max(MIN_IMAGE_PANEL_WIDTH, int(available_width * IMAGE_PANEL_WIDTH / 100))
            plot_width = max(MIN_PLOT_PANEL_WIDTH, int(available_width * PLOT_PANEL_WIDTH / 100))
            selection_width = max(MIN_SELECTION_PANEL_WIDTH, int(available_width * SELECTION_PANEL_WIDTH / 100))
        
        # Apply calculated sizes
        self.main_splitter.setSizes([image_width, plot_width, selection_width])
    
    def resizeEvent(self, event) -> None:
        """Handle window resize events for responsive layout."""
        if hasattr(self, 'original_resize_event'):
            self.original_resize_event(event)
        
        # Update layout if splitter exists
        if hasattr(self, 'main_splitter'):
            QTimer.singleShot(10, self.setup_responsive_layout)  # Delay to ensure proper sizing
    
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
        
        self.action_export_protocol = QAction("&Export Protocol...", self)
        self.action_export_protocol.setShortcut(QKeySequence("Ctrl+E"))
        self.action_export_protocol.setStatusTip("Export .cxprotocol file for CosmoSort")
        self.action_export_protocol.setEnabled(False)
        
        self.action_exit = QAction("E&xit", self)
        self.action_exit.setShortcut(QKeySequence.Quit)
        self.action_exit.setStatusTip("Exit CellSorter")
        
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
        
        self.action_reset_view = QAction("&Reset View", self)
        self.action_reset_view.setShortcut(QKeySequence("R"))
        self.action_reset_view.setStatusTip("Reset view to default")
        self.action_reset_view.setEnabled(False)
        
        # Tools actions
        self.action_selection_tool = QAction("&Selection Tool", self)
        self.action_selection_tool.setShortcut(QKeySequence("S"))
        self.action_selection_tool.setStatusTip("Activate selection tool")
        self.action_selection_tool.setCheckable(True)
        self.action_selection_tool.setEnabled(False)
        
        self.action_calibration_tool = QAction("&Calibration Tool", self)
        self.action_calibration_tool.setShortcut(QKeySequence("C"))
        self.action_calibration_tool.setStatusTip("Activate calibration tool")
        self.action_calibration_tool.setCheckable(True)
        self.action_calibration_tool.setEnabled(False)
        
        self.action_calibrate = QAction("&Calibrate Coordinates", self)
        self.action_calibrate.setShortcut(QKeySequence("Ctrl+K"))
        self.action_calibrate.setStatusTip("Set coordinate calibration points")
        self.action_calibrate.setEnabled(False)
        
        self.action_clear_selections = QAction("&Clear All Selections", self)
        self.action_clear_selections.setShortcut(QKeySequence("Ctrl+Shift+C"))
        self.action_clear_selections.setEnabled(False)
        
        # Navigation shortcuts
        self.action_pan_left = QAction("Pan Left", self)
        self.action_pan_left.setShortcut(QKeySequence("Left"))
        self.action_pan_left.setEnabled(False)
        
        self.action_pan_right = QAction("Pan Right", self)
        self.action_pan_right.setShortcut(QKeySequence("Right"))
        self.action_pan_right.setEnabled(False)
        
        self.action_pan_up = QAction("Pan Up", self)
        self.action_pan_up.setShortcut(QKeySequence("Up"))
        self.action_pan_up.setEnabled(False)
        
        self.action_pan_down = QAction("Pan Down", self)
        self.action_pan_down.setShortcut(QKeySequence("Down"))
        self.action_pan_down.setEnabled(False)
    
    def setup_menu_bar(self) -> None:
        """Create and configure the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        file_menu.addAction(self.action_open_image)
        file_menu.addAction(self.action_open_csv)
        file_menu.addSeparator()
        file_menu.addAction(self.action_export_protocol)
        file_menu.addSeparator()
        file_menu.addAction(self.action_exit)
        
        # View menu (removed toggle actions)
        view_menu = menubar.addMenu("&View")
        view_menu.addAction(self.action_zoom_in)
        view_menu.addAction(self.action_zoom_out)
        view_menu.addAction(self.action_zoom_fit)
        view_menu.addAction(self.action_reset_view)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        tools_menu.addAction(self.action_selection_tool)
        tools_menu.addAction(self.action_calibration_tool)
        tools_menu.addSeparator()
        tools_menu.addAction(self.action_calibrate)
        tools_menu.addAction(self.action_clear_selections)
        
        # Analysis menu
        analysis_menu = menubar.addMenu("&Analysis")
        # Analysis menu actions will be added as needed
    
    def setup_toolbar(self) -> None:
        """Create and configure the toolbar."""
        toolbar = self.addToolBar("Main Toolbar")
        toolbar.setMovable(False)
        
        # File operations
        toolbar.addAction(self.action_open_image)
        toolbar.addAction(self.action_open_csv)
        toolbar.addSeparator()
        
        # Export operations
        toolbar.addAction(self.action_export_protocol)
        toolbar.addSeparator()
        
        # View operations
        toolbar.addAction(self.action_zoom_in)
        toolbar.addAction(self.action_zoom_out)
        toolbar.addAction(self.action_zoom_fit)
        toolbar.addSeparator()
        
                # Tools
        toolbar.addAction(self.action_calibrate)
    
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
        self.action_export_protocol.triggered.connect(self.export_protocol)
        self.action_exit.triggered.connect(self.close)
        
        # View actions
        self.action_zoom_in.triggered.connect(self.zoom_in)
        self.action_zoom_out.triggered.connect(self.zoom_out)
        self.action_zoom_fit.triggered.connect(self.zoom_fit)
        self.action_reset_view.triggered.connect(self.reset_view)

        
        # Navigation actions
        self.action_pan_left.triggered.connect(self.pan_left)
        self.action_pan_right.triggered.connect(self.pan_right)
        self.action_pan_up.triggered.connect(self.pan_up)
        self.action_pan_down.triggered.connect(self.pan_down)
        
        # Tools actions
        self.action_selection_tool.triggered.connect(self.activate_selection_tool)
        self.action_calibration_tool.triggered.connect(self.activate_calibration_tool)
        self.action_calibrate.triggered.connect(self.calibrate_coordinates)
        self.action_clear_selections.triggered.connect(self.clear_selections)
        

        
        # Component connections
        self.csv_parser.csv_loaded.connect(self._on_csv_loaded)
        self.csv_parser.csv_load_failed.connect(self._on_csv_load_failed)
        self.image_handler.image_loaded.connect(self._on_image_loaded)
        self.image_handler.image_load_failed.connect(self._on_image_load_failed)
        
        # Selection handling - connect to unified handler
        # Use the new signal with method information for enhanced functionality
        self.scatter_plot_widget.selection_made_with_method.connect(self._on_selection_made)
        

        
        self.coordinate_transformer.calibration_updated.connect(self._on_calibration_updated)
        self.selection_manager.selection_added.connect(self._on_selection_added)
        self.selection_manager.selection_updated.connect(self._on_selection_updated)
        self.selection_manager.selection_removed.connect(self._on_selection_removed)
        self.selection_panel.selection_deleted.connect(self._on_panel_selection_deleted)
        self.selection_panel.export_requested.connect(self.export_protocol)
        
        # Image handler connections
        self.image_handler.coordinates_changed.connect(self.update_coordinates)
        self.image_handler.calibration_point_clicked.connect(self._on_calibration_point_clicked)
        
        # Minimap connections
        self.minimap_widget.navigation_requested.connect(self.image_handler.navigate_to_position)
        self.image_handler.zoom_changed.connect(self._update_minimap_viewport)
    
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
    

    
    def zoom_in(self) -> None:
        """Zoom in on image."""
        if self.current_image_path:
            self.image_handler.zoom_in()
            zoom_level = getattr(self.image_handler, 'zoom_level', 1.0)
            self.update_zoom_level(zoom_level)
            self.update_status(f"Zoomed in to {zoom_level:.0%}")
    
    def zoom_out(self) -> None:
        """Zoom out on image."""
        if self.current_image_path:
            self.image_handler.zoom_out()
            zoom_level = getattr(self.image_handler, 'zoom_level', 1.0)
            self.update_zoom_level(zoom_level)
            self.update_status(f"Zoomed out to {zoom_level:.0%}")
    
    def zoom_fit(self) -> None:
        """Fit image to window."""
        if self.current_image_path:
            self.image_handler.fit_to_window()
            zoom_level = getattr(self.image_handler, 'zoom_level', 1.0)
            self.update_zoom_level(zoom_level)
            self.update_status("Fit to window")
    
    def toggle_overlays(self) -> None:
        """Toggle cell overlay visibility (deprecated - overlays are always enabled)."""
        self.update_status("Overlays are always enabled")
    
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
        self.selection_manager.clear_all_selections()
        self.image_handler.clear_all_cell_highlights()
        self.update_status("All selections cleared")
        self.update_window_title()
    

    
    def reset_view(self) -> None:
        """Reset view to default state."""
        if self.current_image_path:
            self.image_handler.reset_view()
            self.update_status("View reset to default")
    
    def pan_left(self) -> None:
        """Pan image view left."""
        if self.current_image_path:
            self.image_handler.pan(-50, 0)  # Pan left by 50 pixels
    
    def pan_right(self) -> None:
        """Pan image view right."""
        if self.current_image_path:
            self.image_handler.pan(50, 0)  # Pan right by 50 pixels
    
    def pan_up(self) -> None:
        """Pan image view up."""
        if self.current_image_path:
            self.image_handler.pan(0, -50)  # Pan up by 50 pixels
    
    def pan_down(self) -> None:
        """Pan image view down."""
        if self.current_image_path:
            self.image_handler.pan(0, 50)  # Pan down by 50 pixels
    
    def activate_selection_tool(self) -> None:
        """Activate selection tool mode."""
        if self.action_selection_tool.isChecked():
            # Deactivate other tools
            self.action_calibration_tool.setChecked(False)
            self.image_handler.set_selection_mode(True)
            self.update_status("Selection tool activated")
        else:
            self.image_handler.set_selection_mode(False)
            self.update_status("Selection tool deactivated")
    
    def activate_calibration_tool(self) -> None:
        """Activate calibration tool mode."""
        if self.action_calibration_tool.isChecked():
            # Deactivate other tools
            self.action_selection_tool.setChecked(False)
            self.calibrate_coordinates()
        else:
            self.image_handler.set_calibration_mode(False)
            self.update_status("Calibration tool deactivated")
    

    

    
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
        
        self.setWindowTitle(title)
    
    def enable_image_actions(self) -> None:
        """Enable actions that require an image to be loaded."""
        self.action_zoom_in.setEnabled(True)
        self.action_zoom_out.setEnabled(True)
        self.action_zoom_fit.setEnabled(True)
        self.action_reset_view.setEnabled(True)

        self.action_calibrate.setEnabled(True)
        self.action_selection_tool.setEnabled(True)
        self.action_calibration_tool.setEnabled(True)
        # Enable navigation shortcuts
        self.action_pan_left.setEnabled(True)
        self.action_pan_right.setEnabled(True)
        self.action_pan_up.setEnabled(True)
        self.action_pan_down.setEnabled(True)
    
    def enable_analysis_actions(self) -> None:
        """Enable actions that require data to be loaded."""
        # Analysis actions are automatically enabled when needed
        pass
        
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
        
        # Update minimap with loaded image
        if self.image_handler.image_data is not None:
            # Use the shared method from ImageHandler
            qimage = self.image_handler._numpy_to_qimage(self.image_handler.image_data)
            self.minimap_widget.set_image(qimage)
            self._update_minimap_viewport()
    
    def _on_image_load_failed(self, error_message: str) -> None:
        """Handle failed image loading."""
        self.update_status(f"Image loading failed: {error_message}")
        self.log_error(f"Image loading failed: {error_message}")
    
    def _on_csv_loaded(self, file_path: str) -> None:
        """Handle successful CSV loading."""
        # Load data into scatter plot widget (without expression filter)
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
    
    def _on_selection_made(self, indices: list, method: str = "rectangle_selection") -> None:
        """Handle cell selection from scatter plot."""
        if indices:
            # Create label based on selection method
            if method == "point_selection":
                label = f"Point_{len(self.selection_manager.selections) + 1}"
                status_message = f"Selected {len(indices)} cells using point selection"
            elif method == "rectangle_selection":
                label = f"Rectangle_{len(self.selection_manager.selections) + 1}"
                status_message = f"Selected {len(indices)} cells using rectangle selection"
            else:
                label = f"Selection_{len(self.selection_manager.selections) + 1}"
                status_message = f"Selected {len(indices)} cells"
            
            selection_id = self.selection_manager.add_selection(
                cell_indices=indices,
                label=label
            )
            
            if selection_id:
                self.update_status(status_message)
                self.update_window_title()
                
                # Store selection method in metadata
                selection = self.selection_manager.get_selection(selection_id)
                if selection:
                    selection.metadata['selection_method'] = method
                self.log_info(f"{method}: {len(indices)} cells")
        else:
            self.update_status("No cells selected")
    

    
    def _on_calibration_updated(self, is_valid: bool) -> None:
        """Handle calibration update."""
        if is_valid:
            self.update_status("Coordinate calibration updated")
        else:
            self.update_status("Calibration cleared")
        
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
            
            self.update_window_title()
    
    def _on_selection_removed(self, selection_id: str) -> None:
        """Handle selection removal."""
        # Remove image highlights
        self.image_handler.remove_cell_highlights(selection_id)
        
        self.update_window_title()
    
    def _on_panel_selection_deleted(self, selection_id: str) -> None:
        """Handle selection deletion from panel."""
        # Remove from selection manager
        self.selection_manager.remove_selection(selection_id)
        
        # Remove image highlights
        self.image_handler.remove_cell_highlights(selection_id)
    
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
                    if self.coordinate_transformer.is_calibrated:
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
        """Handle update availability notification."""
        reply = QMessageBox.information(
            self,
            "Update Available",
            f"A new version of CellSorter is available!\n\n"
            f"Current version: {current_version}\n"
            f"Latest version: {latest_version}\n\n"
            f"Would you like to download the update?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            import webbrowser
            webbrowser.open(download_url)
    
    def _update_minimap_viewport(self) -> None:
        """Update minimap viewport rectangle."""
        if self.image_handler.image_data is not None:
            visible_rect = self.image_handler.get_visible_rect()
            x, y, width, height = visible_rect
            viewport_rect = QRect(x, y, width, height)
            
            img_height, img_width = self.image_handler.image_data.shape[:2]
            image_size = QSize(img_width, img_height)
            
            self.minimap_widget.update_viewport(viewport_rect, image_size)
    

    
