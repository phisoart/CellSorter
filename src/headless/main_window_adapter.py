"""
MainWindow Headless Adapter

Adapter to make the existing MainWindow work in headless mode.
Provides UI definitions and state management without Qt dependencies.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from dataclasses import dataclass, field

from .ui_model import WidgetType, Geometry, Size, SizePolicy
from .ui_compatibility import UI, Widget
from .mode_manager import ModeManager

logger = logging.getLogger(__name__)


@dataclass
class MainWindowState:
    """State container for MainWindow."""
    
    # File paths
    current_image_path: Optional[str] = None
    current_csv_path: Optional[str] = None
    
    # Window properties
    window_title: str = "CellSorter"
    window_geometry: Optional[Geometry] = None
    is_maximized: bool = False
    
    # UI state
    is_modified: bool = False
    status_message: str = "Ready"
    cell_count: int = 0
    zoom_level: float = 1.0
    mouse_coordinates: tuple = (0.0, 0.0)
    
    # Panel visibility
    image_panel_visible: bool = True
    plot_panel_visible: bool = True
    selection_panel_visible: bool = True
    
    # Tool states
    active_tool: str = "selection"
    overlays_visible: bool = True
    
    # Theme
    current_theme: str = "light"
    
    # Session data
    last_session_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary."""
        return {
            "current_image_path": self.current_image_path,
            "current_csv_path": self.current_csv_path,
            "window_title": self.window_title,
            "window_geometry": self.window_geometry.to_dict() if self.window_geometry else None,
            "is_maximized": self.is_maximized,
            "is_modified": self.is_modified,
            "status_message": self.status_message,
            "cell_count": self.cell_count,
            "zoom_level": self.zoom_level,
            "mouse_coordinates": self.mouse_coordinates,
            "image_panel_visible": self.image_panel_visible,
            "plot_panel_visible": self.plot_panel_visible,
            "selection_panel_visible": self.selection_panel_visible,
            "active_tool": self.active_tool,
            "overlays_visible": self.overlays_visible,
            "current_theme": self.current_theme,
            "last_session_path": self.last_session_path
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MainWindowState':
        """Create state from dictionary."""
        state = cls()
        state.current_image_path = data.get("current_image_path")
        state.current_csv_path = data.get("current_csv_path")
        state.window_title = data.get("window_title", "CellSorter")
        
        if data.get("window_geometry"):
            state.window_geometry = Geometry.from_dict(data["window_geometry"])
        
        state.is_maximized = data.get("is_maximized", False)
        state.is_modified = data.get("is_modified", False)
        state.status_message = data.get("status_message", "Ready")
        state.cell_count = data.get("cell_count", 0)
        state.zoom_level = data.get("zoom_level", 1.0)
        state.mouse_coordinates = data.get("mouse_coordinates", (0.0, 0.0))
        state.image_panel_visible = data.get("image_panel_visible", True)
        state.plot_panel_visible = data.get("plot_panel_visible", True)
        state.selection_panel_visible = data.get("selection_panel_visible", True)
        state.active_tool = data.get("active_tool", "selection")
        state.overlays_visible = data.get("overlays_visible", True)
        state.current_theme = data.get("current_theme", "light")
        state.last_session_path = data.get("last_session_path")
        
        return state


class MainWindowAdapter:
    """Adapter for MainWindow to work in headless mode."""
    
    def __init__(self, mode_manager: ModeManager):
        self.mode_manager = mode_manager
        self.state = MainWindowState()
        
        # Model placeholders (for headless mode)
        self.image_handler = None
        self.csv_parser = None
        self.coordinate_transformer = None
        self.selection_manager = None
        self.extractor = None
        self.session_manager = None
        self.template_manager = None
        
        # Action handlers
        self.action_handlers = {}
        self._setup_action_handlers()
        
        logger.info("MainWindow adapter initialized")
    
    def _setup_action_handlers(self) -> None:
        """Setup action handlers for headless mode."""
        self.action_handlers = {
            "open_image": self.open_image_file,
            "open_csv": self.open_csv_file,
            "save_session": self.save_session,
            "load_session": self.load_session,
            "export_protocol": self.export_protocol,
            "batch_process": self.batch_process,
            "undo": self.undo,
            "redo": self.redo,
            "zoom_in": self.zoom_in,
            "zoom_out": self.zoom_out,
            "zoom_fit": self.zoom_fit,
            "toggle_overlays": self.toggle_overlays,
            "calibrate_coordinates": self.calibrate_coordinates,
            "clear_selections": self.clear_selections,
            "select_all": self.select_all,
            "delete_selection": self.delete_selection,
            "reset_view": self.reset_view,
            "toggle_panel": self.toggle_panel,
            "activate_selection_tool": self.activate_selection_tool,
            "activate_calibration_tool": self.activate_calibration_tool,
            "manage_templates": self.manage_templates,
            "toggle_theme": self.toggle_theme,
            "show_about": self.show_about
        }
    
    def initialize_models(self) -> None:
        """Initialize data models."""
        # Only initialize in GUI mode or if explicitly requested
        if not self.mode_manager.is_dev_mode():
            try:
                # Dynamic imports to avoid circular dependencies
                from ..models.image_handler import ImageHandler
                from ..models.csv_parser import CSVParser
                from ..models.coordinate_transformer import CoordinateTransformer
                from ..models.selection_manager import SelectionManager
                from ..models.extractor import Extractor
                from ..models.session_manager import SessionManager
                from ..models.template_manager import TemplateManager
                
                self.image_handler = ImageHandler(None)
                self.csv_parser = CSVParser(None)
                self.coordinate_transformer = CoordinateTransformer(None)
                self.selection_manager = SelectionManager(None)
                self.extractor = Extractor(None)
                self.session_manager = SessionManager(None)
                self.template_manager = TemplateManager(parent=None)
                
                logger.info("Data models initialized")
            except ImportError as e:
                logger.warning(f"Could not import models: {e}")
                # This is expected in headless testing environment
    
    def get_ui_definition(self) -> UI:
        """Generate UI definition for the main window."""
        widgets = []
        
        # Main window
        main_window = Widget(
            name="main_window",
            type=WidgetType.MAIN_WINDOW,
            properties={
                "title": self.state.window_title,
                "width": 1200,
                "height": 800,
                "minimumWidth": 800,
                "minimumHeight": 600,
                "windowState": "maximized" if self.state.is_maximized else "normal"
            },
            visible=True,
            enabled=True
        )
        widgets.append(main_window)
        
        # Menu bar
        menu_bar = Widget(
            name="menu_bar",
            type=WidgetType.MENU_BAR,
            properties={},
            parent="main_window"
        )
        widgets.append(menu_bar)
        
        # File menu
        file_menu = Widget(
            name="file_menu", 
            type=WidgetType.MENU,
            properties={"title": "File"},
            parent="menu_bar"
        )
        widgets.append(file_menu)
        
        # Toolbar
        toolbar = Widget(
            name="main_toolbar",
            type=WidgetType.TOOL_BAR,
            properties={"title": "Main Toolbar"},
            parent="main_window"
        )
        widgets.append(toolbar)
        
        # Central widget
        central_widget = Widget(
            name="central_widget",
            type=WidgetType.WIDGET,
            properties={},
            parent="main_window"
        )
        widgets.append(central_widget)
        
        # Splitter
        splitter = Widget(
            name="main_splitter",
            type=WidgetType.SPLITTER,
            properties={"orientation": "horizontal"},
            parent="central_widget"
        )
        widgets.append(splitter)
        
        # Panels (only if visible)
        if self.state.image_panel_visible:
            image_panel = Widget(
                name="image_panel",
                type=WidgetType.WIDGET,
                properties={"title": "Image View", "minimumWidth": 300},
                parent="main_splitter"
            )
            widgets.append(image_panel)
        
        if self.state.plot_panel_visible:
            plot_panel = Widget(
                name="plot_panel",
                type=WidgetType.WIDGET,
                properties={"title": "Scatter Plot", "minimumWidth": 400},
                parent="main_splitter"
            )
            widgets.append(plot_panel)
        
        if self.state.selection_panel_visible:
            selection_panel = Widget(
                name="selection_panel",
                type=WidgetType.WIDGET,
                properties={"title": "Selection Manager", "minimumWidth": 250},
                parent="main_splitter"
            )
            widgets.append(selection_panel)
        
        # Status bar
        status_bar = Widget(
            name="status_bar",
            type=WidgetType.STATUS_BAR,
            properties={"message": self.state.status_message},
            parent="main_window"
        )
        widgets.append(status_bar)
        
        return UI(
            metadata={
                "version": "1.0",
                "created": "2024-01-01T00:00:00Z",
                "description": "CellSorter Main Window",
                "mode": "headless" if self.mode_manager.is_dev_mode() else "gui"
            },
            widgets=widgets
        )
    
    def _is_action_enabled(self, action_name: str) -> bool:
        """Check if action should be enabled based on current state."""
        # File operations requiring both image and CSV
        if action_name in ["save_session_action", "export_action"]:
            return (self.state.current_image_path is not None and 
                   self.state.current_csv_path is not None)
        
        # Always enabled actions
        if action_name in ["open_image_action", "open_csv_action", "load_session_action", "exit_action"]:
            return True
        
        return True
    
    def execute_action(self, action_name: str, **kwargs) -> Dict[str, Any]:
        """Execute action by name."""
        if action_name in self.action_handlers:
            try:
                result = self.action_handlers[action_name](**kwargs)
                return {"success": True, "result": result}
            except Exception as e:
                logger.error(f"Error executing action {action_name}: {e}")
                return {"success": False, "error": str(e)}
        else:
            return {"success": False, "error": f"Unknown action: {action_name}"}
    
    # Action implementations (headless versions)
    
    def open_image_file(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """Open image file in headless mode."""
        if file_path:
            self.state.current_image_path = file_path
            self.state.window_title = f"CellSorter - {Path(file_path).name}"
            self.state.is_modified = False
            logger.info(f"Image file path set: {file_path}")
            return {"file_path": file_path, "loaded": True}
        else:
            return {"error": "No file path provided"}
    
    def open_csv_file(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """Open CSV file in headless mode."""
        if file_path:
            self.state.current_csv_path = file_path
            self.state.is_modified = False
            logger.info(f"CSV file path set: {file_path}")
            return {"file_path": file_path, "loaded": True}
        else:
            return {"error": "No file path provided"}
    
    def save_session(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """Save session in headless mode."""
        if file_path:
            self.state.last_session_path = file_path
            session_data = self.state.to_dict()
            logger.info(f"Session would be saved to: {file_path}")
            return {"file_path": file_path, "saved": True, "data": session_data}
        else:
            return {"error": "No file path provided"}
    
    def load_session(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """Load session in headless mode."""
        if file_path:
            self.state.last_session_path = file_path
            logger.info(f"Session would be loaded from: {file_path}")
            return {"file_path": file_path, "loaded": True}
        else:
            return {"error": "No file path provided"}
    
    def export_protocol(self) -> Dict[str, Any]:
        """Export protocol in headless mode."""
        logger.info("Export protocol requested")
        return {"exported": True, "message": "Export would be performed"}
    
    def batch_process(self) -> Dict[str, Any]:
        """Start batch processing in headless mode."""
        logger.info("Batch processing requested")
        return {"started": True, "message": "Batch processing would start"}
    
    def undo(self) -> Dict[str, Any]:
        """Undo last action."""
        logger.info("Undo requested")
        return {"undone": True}
    
    def redo(self) -> Dict[str, Any]:
        """Redo last undone action."""
        logger.info("Redo requested")
        return {"redone": True}
    
    def zoom_in(self) -> Dict[str, Any]:
        """Zoom in."""
        self.state.zoom_level = min(self.state.zoom_level * 1.2, 10.0)
        logger.info(f"Zoom level: {self.state.zoom_level:.1f}x")
        return {"zoom_level": self.state.zoom_level}
    
    def zoom_out(self) -> Dict[str, Any]:
        """Zoom out."""
        self.state.zoom_level = max(self.state.zoom_level / 1.2, 0.1)
        logger.info(f"Zoom level: {self.state.zoom_level:.1f}x")
        return {"zoom_level": self.state.zoom_level}
    
    def zoom_fit(self) -> Dict[str, Any]:
        """Fit image to view."""
        self.state.zoom_level = 1.0
        logger.info("Zoom fit to window")
        return {"zoom_level": self.state.zoom_level}
    
    def toggle_overlays(self) -> Dict[str, Any]:
        """Toggle overlay visibility."""
        self.state.overlays_visible = not self.state.overlays_visible
        logger.info(f"Overlays visible: {self.state.overlays_visible}")
        return {"overlays_visible": self.state.overlays_visible}
    
    def calibrate_coordinates(self) -> Dict[str, Any]:
        """Start coordinate calibration."""
        logger.info("Coordinate calibration requested")
        return {"calibration_started": True}
    
    def clear_selections(self) -> Dict[str, Any]:
        """Clear all selections."""
        logger.info("Clear selections requested")
        return {"selections_cleared": True}
    
    def select_all(self) -> Dict[str, Any]:
        """Select all items."""
        logger.info("Select all requested")
        return {"all_selected": True}
    
    def delete_selection(self) -> Dict[str, Any]:
        """Delete current selection."""
        logger.info("Delete selection requested")
        return {"selection_deleted": True}
    
    def reset_view(self) -> Dict[str, Any]:
        """Reset view to default."""
        self.state.zoom_level = 1.0
        logger.info("View reset")
        return {"view_reset": True, "zoom_level": self.state.zoom_level}
    
    def toggle_panel(self, panel_name: str = "image") -> Dict[str, Any]:
        """Toggle panel visibility."""
        visible = False
        if panel_name == "image":
            self.state.image_panel_visible = not self.state.image_panel_visible
            visible = self.state.image_panel_visible
        elif panel_name == "plot":
            self.state.plot_panel_visible = not self.state.plot_panel_visible
            visible = self.state.plot_panel_visible
        elif panel_name == "selection":
            self.state.selection_panel_visible = not self.state.selection_panel_visible
            visible = self.state.selection_panel_visible
        
        logger.info(f"Panel visibility toggled: {panel_name}")
        return {
            "panel": panel_name,
            "visible": visible
        }
    
    def activate_selection_tool(self) -> Dict[str, Any]:
        """Activate selection tool."""
        self.state.active_tool = "selection"
        logger.info("Selection tool activated")
        return {"active_tool": self.state.active_tool}
    
    def activate_calibration_tool(self) -> Dict[str, Any]:
        """Activate calibration tool."""
        self.state.active_tool = "calibration"
        logger.info("Calibration tool activated")
        return {"active_tool": self.state.active_tool}
    
    def manage_templates(self) -> Dict[str, Any]:
        """Open template management."""
        logger.info("Template management requested")
        return {"template_management_opened": True}
    
    def toggle_theme(self) -> Dict[str, Any]:
        """Toggle application theme."""
        self.state.current_theme = "dark" if self.state.current_theme == "light" else "light"
        logger.info(f"Theme changed to: {self.state.current_theme}")
        return {"theme": self.state.current_theme}
    
    def show_about(self) -> Dict[str, Any]:
        """Show about dialog."""
        logger.info("About dialog requested")
        return {"about_shown": True}
    
    def update_status(self, message: str) -> None:
        """Update status message."""
        self.state.status_message = message
        logger.debug(f"Status updated: {message}")
    
    def update_cell_count(self, count: int) -> None:
        """Update cell count."""
        self.state.cell_count = count
        logger.debug(f"Cell count updated: {count}")
    
    def update_zoom_level(self, zoom: float) -> None:
        """Update zoom level."""
        self.state.zoom_level = zoom
        logger.debug(f"Zoom level updated: {zoom:.1f}x")
    
    def update_coordinates(self, x: float, y: float) -> None:
        """Update mouse coordinates."""
        self.state.mouse_coordinates = (x, y)
        logger.debug(f"Coordinates updated: ({x:.1f}, {y:.1f})")
    
    def get_state(self) -> MainWindowState:
        """Get current state."""
        return self.state
    
    def set_state(self, state: MainWindowState) -> None:
        """Set current state."""
        self.state = state
        logger.info("Main window state updated") 