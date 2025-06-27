"""
Mock Widgets

Mock implementations of Qt widgets for headless testing.
Provides all necessary properties and methods without actual GUI rendering.
"""

import logging
from typing import Any, Dict, Optional, List, Set
from dataclasses import dataclass, field
from enum import Enum

from ..ui_model import WidgetType, Geometry, Size, SizePolicy

logger = logging.getLogger(__name__)


class MockWidgetState(Enum):
    """States a mock widget can be in."""
    CREATED = "created"
    SHOWN = "shown" 
    HIDDEN = "hidden"
    DESTROYED = "destroyed"


@dataclass
class MockWidget:
    """Mock widget implementation for testing."""
    
    name: str
    widget_type: WidgetType
    properties: Dict[str, Any] = field(default_factory=dict)
    geometry: Optional[Geometry] = None
    size_policy: Optional[SizePolicy] = None
    parent: Optional['MockWidget'] = None
    children: List['MockWidget'] = field(default_factory=list)
    state: MockWidgetState = MockWidgetState.CREATED
    signals_emitted: List[str] = field(default_factory=list)
    connected_signals: Dict[str, List[str]] = field(default_factory=dict)
    event_history: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize widget after creation."""
        # Set default properties based on widget type
        self._set_default_properties()
        
        # Log creation
        logger.debug(f"Created mock widget: {self.name} ({self.widget_type.value})")
    
    def _set_default_properties(self) -> None:
        """Set default properties based on widget type."""
        defaults = {
            WidgetType.LABEL: {"text": "", "alignment": "Left"},
            WidgetType.PUSH_BUTTON: {"text": "Button", "enabled": True},
            WidgetType.LINE_EDIT: {"text": "", "placeholder_text": ""},
            WidgetType.MAIN_WINDOW: {"title": "MainWindow", "width": 800, "height": 600},
            WidgetType.DIALOG: {"title": "Dialog", "modal": True},
        }
        
        if self.widget_type in defaults:
            for key, value in defaults[self.widget_type].items():
                if key not in self.properties:
                    self.properties[key] = value
    
    def set_property(self, name: str, value: Any) -> None:
        """Set widget property."""
        old_value = self.properties.get(name)
        self.properties[name] = value
        
        # Log property change
        self.event_history.append({
            "type": "property_changed",
            "property": name,
            "old_value": old_value,
            "new_value": value
        })
        
        logger.debug(f"{self.name}.{name} = {value}")
    
    def get_property(self, name: str, default: Any = None) -> Any:
        """Get widget property."""
        return self.properties.get(name, default)
    
    def add_child(self, child: 'MockWidget') -> None:
        """Add child widget."""
        if child.parent:
            child.parent.remove_child(child)
        
        child.parent = self
        self.children.append(child)
        
        self.event_history.append({
            "type": "child_added",
            "child": child.name
        })
        
        logger.debug(f"Added child {child.name} to {self.name}")
    
    def remove_child(self, child: 'MockWidget') -> bool:
        """Remove child widget."""
        if child in self.children:
            child.parent = None
            self.children.remove(child)
            
            self.event_history.append({
                "type": "child_removed", 
                "child": child.name
            })
            
            logger.debug(f"Removed child {child.name} from {self.name}")
            return True
        return False
    
    def find_child(self, name: str, recursive: bool = True) -> Optional['MockWidget']:
        """Find child widget by name."""
        for child in self.children:
            if child.name == name:
                return child
            if recursive:
                result = child.find_child(name, recursive)
                if result:
                    return result
        return None
    
    def emit_signal(self, signal_name: str, *args) -> None:
        """Emit signal (for testing)."""
        self.signals_emitted.append(signal_name)
        
        # Call connected handlers
        if signal_name in self.connected_signals:
            for handler in self.connected_signals[signal_name]:
                self.event_history.append({
                    "type": "signal_emitted",
                    "signal": signal_name,
                    "handler": handler,
                    "args": args
                })
        
        logger.debug(f"{self.name} emitted signal: {signal_name}")
    
    def connect_signal(self, signal_name: str, handler: str) -> None:
        """Connect signal to handler."""
        if signal_name not in self.connected_signals:
            self.connected_signals[signal_name] = []
        self.connected_signals[signal_name].append(handler)
        
        logger.debug(f"Connected {self.name}.{signal_name} -> {handler}")
    
    def show(self) -> None:
        """Show widget."""
        self.state = MockWidgetState.SHOWN
        self.event_history.append({"type": "shown"})
        logger.debug(f"Showed widget: {self.name}")
    
    def hide(self) -> None:
        """Hide widget."""
        self.state = MockWidgetState.HIDDEN  
        self.event_history.append({"type": "hidden"})
        logger.debug(f"Hid widget: {self.name}")
    
    def destroy(self) -> None:
        """Destroy widget."""
        # Remove from parent
        if self.parent:
            self.parent.remove_child(self)
        
        # Destroy children
        for child in self.children.copy():
            child.destroy()
        
        self.state = MockWidgetState.DESTROYED
        self.event_history.append({"type": "destroyed"})
        logger.debug(f"Destroyed widget: {self.name}")
    
    def is_visible(self) -> bool:
        """Check if widget is visible."""
        return self.state == MockWidgetState.SHOWN
    
    def is_enabled(self) -> bool:
        """Check if widget is enabled."""
        return self.get_property("enabled", True)
    
    def get_text(self) -> str:
        """Get widget text (for applicable widgets)."""
        return self.get_property("text", "")
    
    def set_text(self, text: str) -> None:
        """Set widget text (for applicable widgets)."""
        self.set_property("text", text)
    
    def click(self) -> None:
        """Simulate click event."""
        if self.widget_type in [WidgetType.PUSH_BUTTON, WidgetType.CHECK_BOX, WidgetType.RADIO_BUTTON]:
            self.emit_signal("clicked")
            self.event_history.append({"type": "clicked"})
        else:
            logger.warning(f"Click not supported for {self.widget_type}")
    
    def get_event_count(self, event_type: str) -> int:
        """Get count of specific event type."""
        return len([e for e in self.event_history if e.get("type") == event_type])
    
    def clear_event_history(self) -> None:
        """Clear event history."""
        self.event_history.clear()
        self.signals_emitted.clear()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for inspection."""
        return {
            "name": self.name,
            "type": self.widget_type.value,
            "properties": self.properties.copy(),
            "state": self.state.value,
            "children": [child.name for child in self.children],
            "signals_emitted": self.signals_emitted.copy(),
            "event_count": len(self.event_history)
        }


class MockWidgetFactory:
    """Factory for creating mock widgets."""
    
    def __init__(self):
        self.created_widgets: Dict[str, MockWidget] = {}
        self.widget_count = 0
    
    def create_widget(self, name: str, widget_type: WidgetType, parent: Optional[MockWidget] = None) -> MockWidget:
        """Create mock widget."""
        if name in self.created_widgets:
            raise ValueError(f"Widget with name '{name}' already exists")
        
        widget = MockWidget(
            name=name,
            widget_type=widget_type,
            parent=parent
        )
        
        if parent:
            parent.add_child(widget)
        
        self.created_widgets[name] = widget
        self.widget_count += 1
        
        logger.info(f"Created mock widget: {name} ({widget_type.value})")
        return widget
    
    def get_widget(self, name: str) -> Optional[MockWidget]:
        """Get widget by name."""
        return self.created_widgets.get(name)
    
    def destroy_widget(self, name: str) -> bool:
        """Destroy widget."""
        widget = self.created_widgets.get(name)
        if widget:
            widget.destroy()
            del self.created_widgets[name]
            logger.info(f"Destroyed mock widget: {name}")
            return True
        return False
    
    def clear_all(self) -> None:
        """Clear all widgets."""
        for widget in list(self.created_widgets.values()):
            widget.destroy()
        self.created_widgets.clear()
        self.widget_count = 0
        logger.info("Cleared all mock widgets")
    
    def get_widget_count(self) -> int:
        """Get total widget count."""
        return len(self.created_widgets)
    
    def get_widget_names(self) -> List[str]:
        """Get all widget names."""
        return list(self.created_widgets.keys())
    
    def find_widgets_by_type(self, widget_type: WidgetType) -> List[MockWidget]:
        """Find all widgets of specific type."""
        return [w for w in self.created_widgets.values() if w.widget_type == widget_type]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get factory statistics."""
        type_counts = {}
        for widget in self.created_widgets.values():
            type_name = widget.widget_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        return {
            "total_widgets": len(self.created_widgets),
            "widgets_created": self.widget_count,
            "type_distribution": type_counts,
            "widget_names": list(self.created_widgets.keys())
        } 