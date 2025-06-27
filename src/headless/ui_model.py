"""
UI Data Model

Platform-agnostic representation of UI components and layouts.
Provides the core data structures for headless UI development.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


@dataclass
class Size:
    """Size definition."""
    width: int = 100
    height: int = 30
    
    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary."""
        return {
            'width': self.width,
            'height': self.height
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> 'Size':
        """Create from dictionary."""
        return cls(
            width=data.get('width', 100),
            height=data.get('height', 30)
        )


class WidgetType(Enum):
    """Supported widget types."""
    # Basic widgets
    WIDGET = "QWidget"
    LABEL = "QLabel"
    PUSH_BUTTON = "QPushButton"
    LINE_EDIT = "QLineEdit"
    TEXT_EDIT = "QTextEdit"
    COMBO_BOX = "QComboBox"
    CHECK_BOX = "QCheckBox"
    RADIO_BUTTON = "QRadioButton"
    SPIN_BOX = "QSpinBox"
    DOUBLE_SPIN_BOX = "QDoubleSpinBox"
    SLIDER = "QSlider"
    PROGRESS_BAR = "QProgressBar"
    
    # Container widgets
    GROUP_BOX = "QGroupBox"
    FRAME = "QFrame"
    SCROLL_AREA = "QScrollArea"
    TAB_WIDGET = "QTabWidget"
    STACKED_WIDGET = "QStackedWidget"
    
    # Layout widgets
    SPLITTER = "QSplitter"
    
    # Top-level widgets
    MAIN_WINDOW = "QMainWindow"
    DIALOG = "QDialog"
    
    # Menu and toolbar widgets
    MENU_BAR = "QMenuBar"
    MENU = "QMenu"
    TOOL_BAR = "QToolBar"
    STATUS_BAR = "QStatusBar"
    ACTION = "QAction"
    
    # Advanced widgets
    TABLE_WIDGET = "QTableWidget"
    TREE_WIDGET = "QTreeWidget"
    LIST_WIDGET = "QListWidget"
    
    # Custom widgets (CellSorter specific)
    SCATTER_PLOT = "ScatterPlot"
    WELL_PLATE = "WellPlate"
    SELECTION_PANEL = "SelectionPanel"
    EXPRESSION_FILTER = "ExpressionFilter"


class LayoutType(Enum):
    """Supported layout types."""
    VBOX = "QVBoxLayout"
    HBOX = "QHBoxLayout"
    GRID = "QGridLayout"
    FORM = "QFormLayout"
    STACKED = "QStackedLayout"


@dataclass
class Geometry:
    """Widget geometry (position and size)."""
    x: int = 0
    y: int = 0
    width: int = 100
    height: int = 30
    
    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary."""
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> 'Geometry':
        """Create from dictionary."""
        return cls(
            x=data.get('x', 0),
            y=data.get('y', 0),
            width=data.get('width', 100),
            height=data.get('height', 30)
        )


@dataclass
class SizePolicy:
    """Widget size policy."""
    horizontal: str = "Preferred"
    vertical: str = "Preferred"
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return {
            'horizontal': self.horizontal,
            'vertical': self.vertical
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'SizePolicy':
        """Create from dictionary."""
        return cls(
            horizontal=data.get('horizontal', 'Preferred'),
            vertical=data.get('vertical', 'Preferred')
        )


@dataclass
class EventBinding:
    """Signal-slot event binding."""
    signal: str
    handler: str
    connection_type: str = "Qt::AutoConnection"
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return {
            'signal': self.signal,
            'handler': self.handler,
            'connection_type': self.connection_type
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'EventBinding':
        """Create from dictionary."""
        return cls(
            signal=data['signal'],
            handler=data['handler'],
            connection_type=data.get('connection_type', 'Qt::AutoConnection')
        )


@dataclass
class LayoutItem:
    """Item in a layout."""
    widget_name: str
    stretch: int = 0
    alignment: str = ""
    # Grid layout specific
    row: Optional[int] = None
    column: Optional[int] = None
    row_span: int = 1
    column_span: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = {
            'widget': self.widget_name,
            'stretch': self.stretch,
        }
        if self.alignment:
            data['alignment'] = self.alignment
        if self.row is not None:
            data['row'] = self.row
        if self.column is not None:
            data['column'] = self.column
        if self.row_span != 1:
            data['row_span'] = self.row_span
        if self.column_span != 1:
            data['column_span'] = self.column_span
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LayoutItem':
        """Create from dictionary."""
        return cls(
            widget_name=data['widget'],
            stretch=data.get('stretch', 0),
            alignment=data.get('alignment', ''),
            row=data.get('row'),
            column=data.get('column'),
            row_span=data.get('row_span', 1),
            column_span=data.get('column_span', 1)
        )


@dataclass
class Layout:
    """Layout definition."""
    type: LayoutType
    properties: Dict[str, Any] = field(default_factory=dict)
    items: List[LayoutItem] = field(default_factory=list)
    
    def add_item(self, widget_name: str, **kwargs) -> None:
        """Add item to layout."""
        item = LayoutItem(widget_name=widget_name, **kwargs)
        self.items.append(item)
    
    def remove_item(self, widget_name: str) -> bool:
        """Remove item from layout."""
        for i, item in enumerate(self.items):
            if item.widget_name == widget_name:
                del self.items[i]
                return True
        return False
    
    def find_item(self, widget_name: str) -> Optional[LayoutItem]:
        """Find layout item by widget name."""
        for item in self.items:
            if item.widget_name == widget_name:
                return item
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'type': self.type.value,
            'properties': self.properties.copy(),
            'items': [item.to_dict() for item in self.items]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Layout':
        """Create from dictionary."""
        layout_type = LayoutType(data['type'])
        items = [LayoutItem.from_dict(item_data) for item_data in data.get('items', [])]
        return cls(
            type=layout_type,
            properties=data.get('properties', {}),
            items=items
        )


@dataclass
class Widget:
    """Widget definition."""
    name: str
    type: WidgetType
    properties: Dict[str, Any] = field(default_factory=dict)
    geometry: Optional[Geometry] = None
    size_policy: Optional[SizePolicy] = None
    events: List[EventBinding] = field(default_factory=list)
    layout: Optional[Layout] = None
    children: List['Widget'] = field(default_factory=list)
    parent_name: Optional[str] = None
    visible: bool = True
    enabled: bool = True
    tooltip: str = ""
    style_sheet: str = ""
    minimum_size: Optional[Size] = None
    maximum_size: Optional[Size] = None
    
    def add_child(self, child: 'Widget') -> None:
        """Add child widget."""
        child.parent_name = self.name
        self.children.append(child)
    
    def remove_child(self, child_name: str) -> bool:
        """Remove child widget by name."""
        for i, child in enumerate(self.children):
            if child.name == child_name:
                child.parent_name = None
                del self.children[i]
                return True
        return False
    
    def find_child(self, name: str, recursive: bool = True) -> Optional['Widget']:
        """Find child widget by name."""
        for child in self.children:
            if child.name == name:
                return child
            if recursive:
                result = child.find_child(name, recursive)
                if result:
                    return result
        return None
    
    def add_event(self, signal: str, handler: str, connection_type: str = "Qt::AutoConnection") -> None:
        """Add event binding."""
        event = EventBinding(signal=signal, handler=handler, connection_type=connection_type)
        self.events.append(event)
    
    def remove_event(self, signal: str, handler: str) -> bool:
        """Remove event binding."""
        for i, event in enumerate(self.events):
            if event.signal == signal and event.handler == handler:
                del self.events[i]
                return True
        return False
    
    def set_layout(self, layout_type: LayoutType, **properties) -> Layout:
        """Set layout for this widget."""
        self.layout = Layout(type=layout_type, properties=properties)
        return self.layout
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = {
            'name': self.name,
            'type': self.type.value,
            'properties': self.properties.copy(),
            'visible': self.visible,
            'enabled': self.enabled,
            'tooltip': self.tooltip,
            'style_sheet': self.style_sheet
        }
        
        if self.geometry:
            data['geometry'] = self.geometry.to_dict()
        
        if self.size_policy:
            data['size_policy'] = self.size_policy.to_dict()
        
        if self.events:
            data['events'] = [event.to_dict() for event in self.events]
        
        if self.layout:
            data['layout'] = self.layout.to_dict()
        
        if self.children:
            data['children'] = [child.to_dict() for child in self.children]
        
        if self.parent_name:
            data['parent'] = self.parent_name
        
        if self.minimum_size:
            data['minimum_size'] = self.minimum_size.to_dict()
        
        if self.maximum_size:
            data['maximum_size'] = self.maximum_size.to_dict()
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Widget':
        """Create from dictionary."""
        widget_type = WidgetType(data['type'])
        
        # Create widget
        widget = cls(
            name=data['name'],
            type=widget_type,
            properties=data.get('properties', {}),
            parent_name=data.get('parent'),
            visible=data.get('visible', True),
            enabled=data.get('enabled', True),
            tooltip=data.get('tooltip', ''),
            style_sheet=data.get('style_sheet', ''),
            minimum_size=Size.from_dict(data.get('minimum_size', {})) if 'minimum_size' in data else None,
            maximum_size=Size.from_dict(data.get('maximum_size', {})) if 'maximum_size' in data else None
        )
        
        # Set geometry
        if 'geometry' in data:
            widget.geometry = Geometry.from_dict(data['geometry'])
        
        # Set size policy
        if 'size_policy' in data:
            widget.size_policy = SizePolicy.from_dict(data['size_policy'])
        
        # Set events
        if 'events' in data:
            widget.events = [EventBinding.from_dict(event_data) for event_data in data['events']]
        
        # Set layout
        if 'layout' in data:
            widget.layout = Layout.from_dict(data['layout'])
        
        # Set children
        if 'children' in data:
            widget.children = [cls.from_dict(child_data) for child_data in data['children']]
            for child in widget.children:
                child.parent_name = widget.name
        
        return widget


@dataclass
class UIModel:
    """Complete UI model."""
    version: str = "1.0"
    metadata: Dict[str, Any] = field(default_factory=dict)
    root_widget: Optional[Widget] = None
    resources: Dict[str, Any] = field(default_factory=dict)
    
    def set_root(self, widget: Widget) -> None:
        """Set root widget."""
        self.root_widget = widget
    
    def find_widget(self, name: str) -> Optional[Widget]:
        """Find widget by name in the entire tree."""
        if not self.root_widget:
            return None
        
        if self.root_widget.name == name:
            return self.root_widget
        
        return self.root_widget.find_child(name, recursive=True)
    
    def validate(self) -> List[str]:
        """Validate UI model and return list of errors."""
        errors = []
        
        if not self.root_widget:
            errors.append("No root widget defined")
            return errors
        
        # Check for duplicate names
        names = set()
        self._collect_names(self.root_widget, names, errors)
        
        # Validate widget references in layouts
        self._validate_layout_references(self.root_widget, errors)
        
        return errors
    
    def _collect_names(self, widget: Widget, names: set, errors: List[str]) -> None:
        """Collect all widget names and check for duplicates."""
        if widget.name in names:
            errors.append(f"Duplicate widget name: {widget.name}")
        else:
            names.add(widget.name)
        
        for child in widget.children:
            self._collect_names(child, names, errors)
    
    def _validate_layout_references(self, widget: Widget, errors: List[str]) -> None:
        """Validate that layout references point to existing widgets."""
        if widget.layout:
            for item in widget.layout.items:
                if not self.find_widget(item.widget_name):
                    errors.append(f"Layout item references non-existent widget: {item.widget_name}")
        
        for child in widget.children:
            self._validate_layout_references(child, errors)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = {
            'version': self.version,
            'metadata': self.metadata.copy()
        }
        
        if self.root_widget:
            data['root_widget'] = self.root_widget.to_dict()
        
        if self.resources:
            data['resources'] = self.resources.copy()
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UIModel':
        """Create from dictionary."""
        model = cls(
            version=data.get('version', '1.0'),
            metadata=data.get('metadata', {}),
            resources=data.get('resources', {})
        )
        
        if 'root_widget' in data:
            model.root_widget = Widget.from_dict(data['root_widget'])
        
        return model


# Additional UI classes for renderer compatibility


@dataclass 
class UI:
    """Simple UI definition for renderer compatibility."""
    widgets: List[Widget] = field(default_factory=list)
    layouts: List['LayoutItem'] = field(default_factory=list)
    events: List[EventBinding] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'widgets': [w.to_dict() for w in self.widgets],
            'layouts': [l.to_dict() for l in self.layouts],
            'events': [e.to_dict() for e in self.events],
            'metadata': self.metadata.copy()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UI':
        """Create from dictionary."""
        return cls(
            widgets=[Widget.from_dict(w) for w in data.get('widgets', [])],
            layouts=[LayoutItem.from_dict(l) for l in data.get('layouts', [])],
            events=[EventBinding.from_dict(e) for e in data.get('events', [])],
            metadata=data.get('metadata', {})
        ) 