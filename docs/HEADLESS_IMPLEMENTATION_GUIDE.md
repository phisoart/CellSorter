# Headless GUI Implementation Guide

## Phase 1: Core Infrastructure (Foundation)

### 1.1 Display Detection Module

Create `src/headless/display_detector.py`:

```python
"""Display detection for headless mode support."""

import os
import sys
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class DisplayDetector:
    """Detects display availability across platforms."""
    
    @staticmethod
    def has_display() -> bool:
        """Check if a display server is available."""
        # Check forced headless mode
        if os.environ.get('CELLSORTER_FORCE_HEADLESS', '').lower() == 'true':
            logger.info("Forced headless mode via environment variable")
            return False
            
        # Platform-specific detection
        if sys.platform == 'linux':
            has_x11 = bool(os.environ.get('DISPLAY'))
            has_wayland = bool(os.environ.get('WAYLAND_DISPLAY'))
            result = has_x11 or has_wayland
            logger.info(f"Linux display detection: X11={has_x11}, Wayland={has_wayland}")
            return result
            
        elif sys.platform == 'darwin':
            # macOS typically always has display
            # Could check for SSH session if needed
            return True
            
        elif sys.platform == 'win32':
            # Windows display detection
            try:
                import win32api
                return win32api.GetSystemMetrics(0) > 0
            except ImportError:
                # Assume display available if can't check
                return True
                
        # Default to assuming display available
        return True
        
    @staticmethod
    def is_dev_mode() -> bool:
        """Check if running in development mode."""
        return os.environ.get('CELLSORTER_DEV_MODE', '').lower() == 'true'
```

### 1.2 UI Data Model

Create `src/headless/ui_model.py`:

```python
"""UI data model for headless representation."""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import uuid


@dataclass
class WidgetDefinition:
    """Represents a widget in the UI hierarchy."""
    type: str
    name: str
    properties: Dict[str, Any] = field(default_factory=dict)
    layout: Optional[Dict[str, Any]] = None
    children: List['WidgetDefinition'] = field(default_factory=list)
    events: List[Dict[str, str]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        # Ensure unique name
        if not self.name:
            self.name = f"{self.type.lower()}_{uuid.uuid4().hex[:8]}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            'type': self.type,
            'name': self.name,
            'properties': self.properties
        }
        
        if self.layout:
            result['layout'] = self.layout
        if self.children:
            result['children'] = [child.to_dict() for child in self.children]
        if self.events:
            result['events'] = self.events
        if self.metadata:
            result['metadata'] = self.metadata
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WidgetDefinition':
        """Create from dictionary representation."""
        children = [cls.from_dict(child) for child in data.get('children', [])]
        return cls(
            type=data['type'],
            name=data['name'],
            properties=data.get('properties', {}),
            layout=data.get('layout'),
            children=children,
            events=data.get('events', []),
            metadata=data.get('metadata', {})
        )


@dataclass
class UIDefinition:
    """Complete UI definition."""
    version: str = "1.0"
    metadata: Dict[str, Any] = field(default_factory=dict)
    widgets: WidgetDefinition = None
    components: Dict[str, WidgetDefinition] = field(default_factory=dict)
    resources: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'version': self.version,
            'metadata': self.metadata,
            'widgets': self.widgets.to_dict() if self.widgets else None,
            'components': {k: v.to_dict() for k, v in self.components.items()},
            'resources': self.resources
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UIDefinition':
        """Create from dictionary representation."""
        return cls(
            version=data.get('version', '1.0'),
            metadata=data.get('metadata', {}),
            widgets=WidgetDefinition.from_dict(data['widgets']) if data.get('widgets') else None,
            components={k: WidgetDefinition.from_dict(v) for k, v in data.get('components', {}).items()},
            resources=data.get('resources', {})
        )
```

### 1.3 Mode Manager

Create `src/headless/mode_manager.py`:

```python
"""Manages execution modes for the application."""

import sys
import logging
from typing import Optional

from .display_detector import DisplayDetector
from .ui_model import UIDefinition

logger = logging.getLogger(__name__)


class ModeManager:
    """Manages GUI vs headless execution modes."""
    
    def __init__(self):
        self.has_display = DisplayDetector.has_display()
        self.is_dev_mode = DisplayDetector.is_dev_mode()
        self.ui_definition: Optional[UIDefinition] = None
        
    def should_create_gui(self) -> bool:
        """Determine if GUI should be created."""
        if self.is_dev_mode:
            logger.info("Development mode active - GUI creation disabled")
            return False
            
        if not self.has_display:
            logger.warning("No display detected - GUI creation disabled")
            return False
            
        return True
    
    def initialize_app(self, argv: list) -> Optional['QApplication']:
        """Initialize application in appropriate mode."""
        if self.should_create_gui():
            from PySide6.QtWidgets import QApplication
            logger.info("Creating QApplication for GUI mode")
            return QApplication(argv)
        else:
            logger.info("Running in headless mode - no QApplication created")
            return None
    
    def get_mode_info(self) -> dict:
        """Get current mode information."""
        return {
            'has_display': self.has_display,
            'is_dev_mode': self.is_dev_mode,
            'gui_enabled': self.should_create_gui(),
            'mode': 'gui' if self.should_create_gui() else 'headless'
        }
```

## Phase 2: Serialization System

### 2.1 YAML Serializer

Create `src/headless/serializers/yaml_serializer.py`:

```python
"""YAML serialization for UI definitions."""

import yaml
from typing import Union
from pathlib import Path

from ..ui_model import UIDefinition, WidgetDefinition


class YAMLSerializer:
    """Handles YAML serialization/deserialization of UI definitions."""
    
    @staticmethod
    def save(ui_def: UIDefinition, file_path: Union[str, Path]) -> None:
        """Save UI definition to YAML file."""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(
                ui_def.to_dict(),
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True
            )
    
    @staticmethod
    def load(file_path: Union[str, Path]) -> UIDefinition:
        """Load UI definition from YAML file."""
        file_path = Path(file_path)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            
        return UIDefinition.from_dict(data)
    
    @staticmethod
    def dumps(ui_def: UIDefinition) -> str:
        """Serialize UI definition to YAML string."""
        return yaml.dump(
            ui_def.to_dict(),
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True
        )
    
    @staticmethod
    def loads(yaml_str: str) -> UIDefinition:
        """Deserialize UI definition from YAML string."""
        data = yaml.safe_load(yaml_str)
        return UIDefinition.from_dict(data)
```

### 2.2 JSON Serializer

Create `src/headless/serializers/json_serializer.py`:

```python
"""JSON serialization for UI definitions."""

import json
from typing import Union
from pathlib import Path

from ..ui_model import UIDefinition


class JSONSerializer:
    """Handles JSON serialization/deserialization of UI definitions."""
    
    @staticmethod
    def save(ui_def: UIDefinition, file_path: Union[str, Path]) -> None:
        """Save UI definition to JSON file."""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(ui_def.to_dict(), f, indent=2)
    
    @staticmethod
    def load(file_path: Union[str, Path]) -> UIDefinition:
        """Load UI definition from JSON file."""
        file_path = Path(file_path)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        return UIDefinition.from_dict(data)
    
    @staticmethod
    def dumps(ui_def: UIDefinition) -> str:
        """Serialize UI definition to JSON string."""
        return json.dumps(ui_def.to_dict(), indent=2)
    
    @staticmethod
    def loads(json_str: str) -> UIDefinition:
        """Deserialize UI definition from JSON string."""
        data = json.loads(json_str)
        return UIDefinition.from_dict(data)
```

### 2.3 Schema Validator

Create `src/headless/validators/schema_validator.py`:

```python
"""Schema validation for UI definitions."""

from typing import Dict, List, Any, Optional
import re

from ..ui_model import WidgetDefinition, UIDefinition


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


class SchemaValidator:
    """Validates UI definitions against schema rules."""
    
    # Valid widget types
    VALID_WIDGETS = {
        'QMainWindow', 'QWidget', 'QDialog',
        'QPushButton', 'QLabel', 'QLineEdit', 'QTextEdit',
        'QComboBox', 'QSpinBox', 'QCheckBox', 'QRadioButton',
        'QTableWidget', 'QTreeWidget', 'QListWidget',
        'QGroupBox', 'QTabWidget', 'QSplitter',
        'QToolBar', 'QMenuBar', 'QStatusBar'
    }
    
    # Valid layout types
    VALID_LAYOUTS = {
        'QVBoxLayout', 'QHBoxLayout', 'QGridLayout', 
        'QFormLayout', 'QStackedLayout'
    }
    
    # Valid property types
    PROPERTY_TYPES = {
        'text': str,
        'enabled': bool,
        'visible': bool,
        'tooltip': str,
        'geometry': list,
        'size': list,
        'minimum_size': list,
        'maximum_size': list,
        'font': dict,
        'color': str,
        'stylesheet': str
    }
    
    @classmethod
    def validate_ui_definition(cls, ui_def: UIDefinition) -> List[str]:
        """Validate complete UI definition."""
        errors = []
        
        # Validate version
        if not ui_def.version:
            errors.append("Missing version field")
            
        # Validate root widget
        if ui_def.widgets:
            errors.extend(cls.validate_widget(ui_def.widgets))
            
        # Validate components
        for name, widget in ui_def.components.items():
            errors.extend(cls.validate_widget(widget, f"component:{name}"))
            
        return errors
    
    @classmethod
    def validate_widget(cls, widget: WidgetDefinition, path: str = "") -> List[str]:
        """Validate a widget definition."""
        errors = []
        widget_path = f"{path}/{widget.name}" if path else widget.name
        
        # Validate widget type
        if widget.type not in cls.VALID_WIDGETS:
            errors.append(f"{widget_path}: Invalid widget type '{widget.type}'")
            
        # Validate name
        if not cls._is_valid_identifier(widget.name):
            errors.append(f"{widget_path}: Invalid widget name '{widget.name}'")
            
        # Validate properties
        errors.extend(cls._validate_properties(widget.properties, widget_path))
        
        # Validate layout
        if widget.layout:
            errors.extend(cls._validate_layout(widget.layout, widget_path))
            
        # Validate events
        errors.extend(cls._validate_events(widget.events, widget_path))
        
        # Validate children
        for child in widget.children:
            errors.extend(cls.validate_widget(child, widget_path))
            
        return errors
    
    @classmethod
    def _is_valid_identifier(cls, name: str) -> bool:
        """Check if name is a valid Python identifier."""
        return bool(re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', name))
    
    @classmethod
    def _validate_properties(cls, properties: Dict[str, Any], path: str) -> List[str]:
        """Validate widget properties."""
        errors = []
        
        for prop, value in properties.items():
            if prop in cls.PROPERTY_TYPES:
                expected_type = cls.PROPERTY_TYPES[prop]
                if not isinstance(value, expected_type):
                    errors.append(
                        f"{path}: Property '{prop}' should be {expected_type.__name__}, "
                        f"got {type(value).__name__}"
                    )
                    
        return errors
    
    @classmethod
    def _validate_layout(cls, layout: Dict[str, Any], path: str) -> List[str]:
        """Validate layout definition."""
        errors = []
        
        layout_type = layout.get('type')
        if not layout_type:
            errors.append(f"{path}: Layout missing 'type' field")
        elif layout_type not in cls.VALID_LAYOUTS:
            errors.append(f"{path}: Invalid layout type '{layout_type}'")
            
        return errors
    
    @classmethod
    def _validate_events(cls, events: List[Dict[str, str]], path: str) -> List[str]:
        """Validate event bindings."""
        errors = []
        
        for i, event in enumerate(events):
            if 'signal' not in event:
                errors.append(f"{path}: Event {i} missing 'signal' field")
            if 'handler' not in event:
                errors.append(f"{path}: Event {i} missing 'handler' field")
                
        return errors
```

## Phase 3: Rendering Engine

### 3.1 Widget Factory

Create `src/headless/rendering/widget_factory.py`:

```python
"""Factory for creating PySide6 widgets from definitions."""

import logging
from typing import Dict, Any, Optional

from PySide6.QtWidgets import (
    QWidget, QMainWindow, QPushButton, QLabel, QLineEdit,
    QComboBox, QCheckBox, QRadioButton, QGroupBox,
    QTableWidget, QTreeWidget, QListWidget, QTabWidget,
    QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout
)
from PySide6.QtCore import Qt

from ..ui_model import WidgetDefinition

logger = logging.getLogger(__name__)


class WidgetFactory:
    """Creates PySide6 widgets from widget definitions."""
    
    # Widget class mapping
    WIDGET_CLASSES = {
        'QMainWindow': QMainWindow,
        'QWidget': QWidget,
        'QPushButton': QPushButton,
        'QLabel': QLabel,
        'QLineEdit': QLineEdit,
        'QComboBox': QComboBox,
        'QCheckBox': QCheckBox,
        'QRadioButton': QRadioButton,
        'QGroupBox': QGroupBox,
        'QTableWidget': QTableWidget,
        'QTreeWidget': QTreeWidget,
        'QListWidget': QListWidget,
        'QTabWidget': QTabWidget,
    }
    
    # Layout class mapping
    LAYOUT_CLASSES = {
        'QVBoxLayout': QVBoxLayout,
        'QHBoxLayout': QHBoxLayout,
        'QGridLayout': QGridLayout,
        'QFormLayout': QFormLayout,
    }
    
    @classmethod
    def create_widget(cls, definition: WidgetDefinition, parent: Optional[QWidget] = None) -> QWidget:
        """Create a widget from definition."""
        # Get widget class
        widget_class = cls.WIDGET_CLASSES.get(definition.type)
        if not widget_class:
            raise ValueError(f"Unknown widget type: {definition.type}")
            
        # Create widget instance
        if definition.type == 'QMainWindow':
            widget = widget_class()
        else:
            widget = widget_class(parent)
            
        # Set object name
        widget.setObjectName(definition.name)
        
        # Apply properties
        cls._apply_properties(widget, definition.properties)
        
        # Create layout if specified
        if definition.layout:
            layout = cls._create_layout(definition.layout)
            if definition.type == 'QMainWindow':
                central_widget = QWidget()
                central_widget.setLayout(layout)
                widget.setCentralWidget(central_widget)
            else:
                widget.setLayout(layout)
        
        # Create children
        for child_def in definition.children:
            child_widget = cls.create_widget(child_def, widget)
            if definition.layout and definition.type != 'QMainWindow':
                widget.layout().addWidget(child_widget)
                
        return widget
    
    @classmethod
    def _apply_properties(cls, widget: QWidget, properties: Dict[str, Any]) -> None:
        """Apply properties to widget."""
        for prop, value in properties.items():
            try:
                if prop == 'text':
                    widget.setText(str(value))
                elif prop == 'enabled':
                    widget.setEnabled(bool(value))
                elif prop == 'visible':
                    widget.setVisible(bool(value))
                elif prop == 'tooltip':
                    widget.setToolTip(str(value))
                elif prop == 'geometry' and isinstance(value, list) and len(value) == 4:
                    widget.setGeometry(*value)
                elif prop == 'minimum_size' and isinstance(value, list) and len(value) == 2:
                    widget.setMinimumSize(*value)
                elif prop == 'maximum_size' and isinstance(value, list) and len(value) == 2:
                    widget.setMaximumSize(*value)
                elif prop == 'stylesheet':
                    widget.setStyleSheet(str(value))
            except Exception as e:
                logger.warning(f"Failed to apply property {prop}={value}: {e}")
    
    @classmethod
    def _create_layout(cls, layout_def: Dict[str, Any]) -> QWidget:
        """Create layout from definition."""
        layout_type = layout_def.get('type')
        layout_class = cls.LAYOUT_CLASSES.get(layout_type)
        
        if not layout_class:
            raise ValueError(f"Unknown layout type: {layout_type}")
            
        layout = layout_class()
        
        # Apply layout properties
        props = layout_def.get('properties', {})
        if 'margin' in props:
            layout.setContentsMargins(props['margin'], props['margin'], 
                                    props['margin'], props['margin'])
        if 'spacing' in props:
            layout.setSpacing(props['spacing'])
            
        return layout
```

### 3.2 Event Connector

Create `src/headless/rendering/event_connector.py`:

```python
"""Connects signals and slots based on event definitions."""

import logging
from typing import Dict, List, Any, Callable

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QWidget

logger = logging.getLogger(__name__)


class EventConnector:
    """Manages signal-slot connections for widgets."""
    
    def __init__(self, handler_object: QObject):
        """Initialize with object containing handler methods."""
        self.handler_object = handler_object
        self._connections = []
    
    def connect_events(self, widget: QWidget, events: List[Dict[str, str]]) -> None:
        """Connect events for a widget."""
        for event in events:
            signal_name = event.get('signal')
            handler_name = event.get('handler')
            
            if not signal_name or not handler_name:
                logger.warning(f"Invalid event definition: {event}")
                continue
                
            try:
                # Get signal from widget
                signal = getattr(widget, signal_name, None)
                if not signal:
                    logger.warning(f"Widget {widget.objectName()} has no signal '{signal_name}'")
                    continue
                
                # Get handler from handler object
                handler = getattr(self.handler_object, handler_name, None)
                if not handler:
                    logger.warning(f"Handler object has no method '{handler_name}'")
                    continue
                
                # Connect signal to handler
                signal.connect(handler)
                self._connections.append((widget, signal_name, handler_name))
                logger.debug(f"Connected {widget.objectName()}.{signal_name} to {handler_name}")
                
            except Exception as e:
                logger.error(f"Failed to connect event: {e}")
    
    def disconnect_all(self) -> None:
        """Disconnect all connections."""
        for widget, signal_name, handler_name in self._connections:
            try:
                signal = getattr(widget, signal_name)
                handler = getattr(self.handler_object, handler_name)
                signal.disconnect(handler)
            except Exception as e:
                logger.warning(f"Failed to disconnect: {e}")
                
        self._connections.clear()
```

### 3.3 UI Renderer

Create `src/headless/rendering/ui_renderer.py`:

```python
"""Main UI renderer that orchestrates widget creation."""

import logging
from typing import Optional, Dict, Any

from PySide6.QtWidgets import QWidget

from ..ui_model import UIDefinition
from .widget_factory import WidgetFactory
from .event_connector import EventConnector

logger = logging.getLogger(__name__)


class UIRenderer:
    """Renders UI definitions into PySide6 widgets."""
    
    def __init__(self, handler_object: Optional[Any] = None):
        """Initialize renderer with optional event handler object."""
        self.handler_object = handler_object
        self.event_connector = EventConnector(handler_object) if handler_object else None
        self._widget_registry: Dict[str, QWidget] = {}
    
    def render(self, ui_definition: UIDefinition) -> Optional[QWidget]:
        """Render UI definition into widgets."""
        if not ui_definition.widgets:
            logger.warning("No root widget in UI definition")
            return None
            
        try:
            # Create root widget
            root_widget = self._render_widget(ui_definition.widgets)
            
            logger.info(f"Successfully rendered UI with root widget: {root_widget.objectName()}")
            return root_widget
            
        except Exception as e:
            logger.error(f"Failed to render UI: {e}")
            raise
    
    def _render_widget(self, definition) -> QWidget:
        """Recursively render a widget and its children."""
        # Create widget
        widget = WidgetFactory.create_widget(definition)
        
        # Register widget
        self._widget_registry[definition.name] = widget
        
        # Connect events if handler available
        if self.event_connector and definition.events:
            self.event_connector.connect_events(widget, definition.events)
            
        return widget
    
    def get_widget(self, name: str) -> Optional[QWidget]:
        """Get widget by name."""
        return self._widget_registry.get(name)
    
    def get_all_widgets(self) -> Dict[str, QWidget]:
        """Get all registered widgets."""
        return self._widget_registry.copy()
```

## Phase 4: CLI Tools

### 4.1 Main CLI Interface

Create `src/headless/cli/main_cli.py`:

```python
"""Main CLI interface for headless UI development."""

import argparse
import sys
import logging
from pathlib import Path

from ..mode_manager import ModeManager
from ..serializers.yaml_serializer import YAMLSerializer
from ..serializers.json_serializer import JSONSerializer
from ..validators.schema_validator import SchemaValidator
from .commands import dump_ui, load_ui, validate_ui, ui_editor

logger = logging.getLogger(__name__)


class HeadlessCLI:
    """Command-line interface for headless UI operations."""
    
    def __init__(self):
        self.mode_manager = ModeManager()
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser."""
        parser = argparse.ArgumentParser(
            prog='cellsorter',
            description='CellSorter - Headless UI Development'
        )
        
        # Global options
        parser.add_argument('--dev-mode', action='store_true',
                          help='Run in development mode (headless)')
        parser.add_argument('--verbose', '-v', action='store_true',
                          help='Enable verbose output')
        
        # Subcommands
        subparsers = parser.add_subparsers(dest='command', help='Commands')
        
        # dump-ui command
        dump_parser = subparsers.add_parser('dump-ui', help='Dump UI to file')
        dump_parser.add_argument('--output', '-o', help='Output file path')
        dump_parser.add_argument('--format', choices=['yaml', 'json'], 
                               default='yaml', help='Output format')
        
        # load-ui command
        load_parser = subparsers.add_parser('load-ui', help='Load UI from file')
        load_parser.add_argument('input', help='Input file path')
        
        # validate-ui command
        validate_parser = subparsers.add_parser('validate-ui', help='Validate UI definition')
        validate_parser.add_argument('input', help='Input file path')
        
        # ui-editor command
        editor_parser = subparsers.add_parser('ui-editor', help='Interactive UI editor')
        
        return parser
    
    def run(self, argv: list = None) -> int:
        """Run CLI with given arguments."""
        args = self.parser.parse_args(argv)
        
        # Set up logging
        if args.verbose:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)
            
        # Handle dev mode
        if args.dev_mode:
            import os
            os.environ['CELLSORTER_DEV_MODE'] = 'true'
            
        # Execute command
        if args.command == 'dump-ui':
            return dump_ui(args)
        elif args.command == 'load-ui':
            return load_ui(args)
        elif args.command == 'validate-ui':
            return validate_ui(args)
        elif args.command == 'ui-editor':
            return ui_editor(args)
        else:
            # Run main application
            from ...main import main
            return main()
```

### 4.2 Example Main Window Definition

Create `ui_definitions/main_window.yaml`:

```yaml
version: "1.0"
metadata:
  created_by: "CellSorter Team"
  description: "Main application window"
  
widgets:
  type: QMainWindow
  name: mainWindow
  properties:
    windowTitle: "CellSorter - Cell Analysis Platform"
    geometry: [100, 100, 1200, 800]
    
  layout:
    type: QVBoxLayout
    
  children:
    - type: QWidget
      name: centralWidget
      layout:
        type: QHBoxLayout
        properties:
          margin: 0
          spacing: 0
          
      children:
        # Image Panel
        - type: QWidget
          name: imagePanel
          properties:
            minimumWidth: 400
          layout:
            type: QVBoxLayout
            
        # Scatter Plot Panel  
        - type: QWidget
          name: plotPanel
          properties:
            minimumWidth: 350
          layout:
            type: QVBoxLayout
            
        # Selection Panel
        - type: QWidget
          name: selectionPanel
          properties:
            minimumWidth: 300
          layout:
            type: QVBoxLayout
            
  # Menu Bar
  menubar:
    - title: "&File"
      actions:
        - text: "&Open Image..."
          name: actionOpenImage
          shortcut: "Ctrl+O"
          events:
            - signal: triggered
              handler: on_open_image
              
    - title: "&Help"
      actions:
        - text: "&About"
          name: actionAbout
          events:
            - signal: triggered
              handler: on_about
```

## Integration with Existing Code

### Modified main.py

```python
"""Enhanced main entry point with headless support."""

import sys
import logging

from src.headless.mode_manager import ModeManager
from src.headless.cli.main_cli import HeadlessCLI

logger = logging.getLogger(__name__)


def main():
    """Main application entry point."""
    # Check if running as CLI
    if len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
        cli = HeadlessCLI()
        return cli.run(sys.argv[1:])
    
    # Initialize mode manager
    mode_manager = ModeManager()
    
    # Log mode information
    mode_info = mode_manager.get_mode_info()
    logger.info(f"Starting CellSorter in {mode_info['mode']} mode")
    
    # Initialize application
    app = mode_manager.initialize_app(sys.argv)
    
    if app:
        # GUI mode - create and show main window
        from src.pages.main_window import MainWindow
        window = MainWindow()
        window.show()
        return app.exec()
    else:
        # Headless mode - run CLI
        cli = HeadlessCLI()
        return cli.run()


if __name__ == "__main__":
    sys.exit(main())
```

## Testing Strategy

### Headless UI Tests

Create `tests/headless/test_ui_structure.py`:

```python
"""Tests for headless UI structure."""

import pytest
from pathlib import Path

from src.headless.serializers.yaml_serializer import YAMLSerializer
from src.headless.validators.schema_validator import SchemaValidator


def test_main_window_structure():
    """Test main window UI structure."""
    # Load UI definition
    ui_def = YAMLSerializer.load('ui_definitions/main_window.yaml')
    
    # Validate structure
    errors = SchemaValidator.validate_ui_definition(ui_def)
    assert len(errors) == 0, f"Validation errors: {errors}"
    
    # Check root widget
    assert ui_def.widgets.type == 'QMainWindow'
    assert ui_def.widgets.name == 'mainWindow'
    
    # Check panels exist
    panels = {child.name for child in ui_def.widgets.children[0].children}
    assert 'imagePanel' in panels
    assert 'plotPanel' in panels
    assert 'selectionPanel' in panels
```

## Benefits

1. **Complete Headless Development**: Full UI development without display
2. **AI-Friendly**: Structured format perfect for AI manipulation
3. **Version Control**: Text-based UI definitions work with git
4. **Testing**: UI structure testable without Qt
5. **Cross-Platform**: Same UI definition works everywhere
6. **Round-Trip Editing**: Seamless code ↔ UI synchronization 