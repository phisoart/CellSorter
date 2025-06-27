"""
UI Assertions

Assertion helpers for testing UI state, properties, and behavior in headless mode.
Provides fluent API for comprehensive UI testing.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from .mock_widgets import MockWidget, MockWidgetState

logger = logging.getLogger(__name__)


class UIAssertionError(AssertionError):
    """Custom assertion error for UI tests."""
    pass


class UIAssertions:
    """Fluent assertion API for UI testing."""
    
    def __init__(self, widget: MockWidget):
        self.widget = widget
        self._description = f"Widget '{widget.name}'"
    
    def described_as(self, description: str) -> 'UIAssertions':
        """Add description for better error messages."""
        self._description = description
        return self
    
    def exists(self) -> 'UIAssertions':
        """Assert widget exists."""
        if self.widget is None:
            raise UIAssertionError(f"{self._description} should exist but was None")
        return self
    
    def has_name(self, expected_name: str) -> 'UIAssertions':
        """Assert widget has specific name."""
        if self.widget.name != expected_name:
            raise UIAssertionError(
                f"{self._description} should have name '{expected_name}' but was '{self.widget.name}'"
            )
        return self
    
    def has_type(self, expected_type) -> 'UIAssertions':
        """Assert widget has specific type."""
        from ..ui_model import WidgetType
        
        if isinstance(expected_type, str):
            # Try to find enum by value
            found_type = None
            for widget_type in WidgetType:
                if widget_type.value.lower() == expected_type.lower() or widget_type.name.lower() == expected_type.lower():
                    found_type = widget_type
                    break
            if found_type is None:
                raise UIAssertionError(f"Unknown widget type: '{expected_type}'")
            expected_type = found_type
        
        if self.widget.widget_type != expected_type:
            raise UIAssertionError(
                f"{self._description} should have type '{expected_type.value}' but was '{self.widget.widget_type.value}'"
            )
        return self
    
    def is_visible(self) -> 'UIAssertions':
        """Assert widget is visible."""
        if not self.widget.is_visible():
            raise UIAssertionError(f"{self._description} should be visible but was not")
        return self
    
    def is_hidden(self) -> 'UIAssertions':
        """Assert widget is hidden."""
        if self.widget.is_visible():
            raise UIAssertionError(f"{self._description} should be hidden but was visible")
        return self
    
    def is_enabled(self) -> 'UIAssertions':
        """Assert widget is enabled."""
        if not self.widget.is_enabled():
            raise UIAssertionError(f"{self._description} should be enabled but was not")
        return self
    
    def is_disabled(self) -> 'UIAssertions':
        """Assert widget is disabled."""
        if self.widget.is_enabled():
            raise UIAssertionError(f"{self._description} should be disabled but was enabled")
        return self
    
    def has_text(self, expected_text: str) -> 'UIAssertions':
        """Assert widget has specific text."""
        actual_text = self.widget.get_text()
        if actual_text != expected_text:
            raise UIAssertionError(
                f"{self._description} should have text '{expected_text}' but was '{actual_text}'"
            )
        return self
    
    def has_property(self, property_name: str, expected_value: Any = None) -> 'UIAssertions':
        """Assert widget has property with optional value check."""
        if property_name not in self.widget.properties:
            raise UIAssertionError(
                f"{self._description} should have property '{property_name}' but it was missing"
            )
        
        if expected_value is not None:
            actual_value = self.widget.properties[property_name]
            if actual_value != expected_value:
                raise UIAssertionError(
                    f"{self._description}.{property_name} should be '{expected_value}' but was '{actual_value}'"
                )
        return self
    
    def has_child_count(self, expected_count: int) -> 'UIAssertions':
        """Assert widget has specific number of children."""
        actual_count = len(self.widget.children)
        if actual_count != expected_count:
            raise UIAssertionError(
                f"{self._description} should have {expected_count} children but had {actual_count}"
            )
        return self
    
    def has_child(self, child_name: str) -> 'UIAssertions':
        """Assert widget has child with specific name."""
        child = self.widget.find_child(child_name, recursive=False)
        if not child:
            child_names = [c.name for c in self.widget.children]
            raise UIAssertionError(
                f"{self._description} should have child '{child_name}' but children were: {child_names}"
            )
        return self
    
    def has_parent(self, parent_name: Optional[str] = None) -> 'UIAssertions':
        """Assert widget has parent, optionally with specific name."""
        if self.widget.parent is None:
            raise UIAssertionError(f"{self._description} should have a parent but was orphaned")
        
        if parent_name is not None and self.widget.parent.name != parent_name:
            raise UIAssertionError(
                f"{self._description} should have parent '{parent_name}' but had '{self.widget.parent.name}'"
            )
        return self
    
    def is_root(self) -> 'UIAssertions':
        """Assert widget is root (has no parent)."""
        if self.widget.parent is not None:
            raise UIAssertionError(
                f"{self._description} should be root but had parent '{self.widget.parent.name}'"
            )
        return self
    
    def has_state(self, expected_state: MockWidgetState) -> 'UIAssertions':
        """Assert widget has specific state."""
        if self.widget.state != expected_state:
            raise UIAssertionError(
                f"{self._description} should have state '{expected_state.value}' but was '{self.widget.state.value}'"
            )
        return self
    
    def has_emitted_signal(self, signal_name: str, count: Optional[int] = None) -> 'UIAssertions':
        """Assert widget has emitted specific signal."""
        emission_count = self.widget.signals_emitted.count(signal_name)
        
        if emission_count == 0:
            raise UIAssertionError(
                f"{self._description} should have emitted signal '{signal_name}' but it was never emitted"
            )
        
        if count is not None and emission_count != count:
            raise UIAssertionError(
                f"{self._description} should have emitted signal '{signal_name}' {count} times but was {emission_count}"
            )
        return self
    
    def has_not_emitted_signal(self, signal_name: str) -> 'UIAssertions':
        """Assert widget has not emitted specific signal."""
        if signal_name in self.widget.signals_emitted:
            count = self.widget.signals_emitted.count(signal_name)
            raise UIAssertionError(
                f"{self._description} should not have emitted signal '{signal_name}' but it was emitted {count} times"
            )
        return self
    
    def has_event_count(self, event_type: str, expected_count: int) -> 'UIAssertions':
        """Assert widget has specific number of events of given type."""
        actual_count = self.widget.get_event_count(event_type)
        if actual_count != expected_count:
            raise UIAssertionError(
                f"{self._description} should have {expected_count} '{event_type}' events but had {actual_count}"
            )
        return self
    
    def was_clicked(self, times: int = 1) -> 'UIAssertions':
        """Assert widget was clicked specific number of times."""
        click_count = self.widget.get_event_count("clicked")
        if click_count != times:
            raise UIAssertionError(
                f"{self._description} should have been clicked {times} times but was clicked {click_count} times"
            )
        return self
    
    def was_shown(self) -> 'UIAssertions':
        """Assert widget was shown."""
        show_count = self.widget.get_event_count("shown")
        if show_count == 0:
            raise UIAssertionError(f"{self._description} should have been shown but show() was never called")
        return self
    
    def was_hidden(self) -> 'UIAssertions':
        """Assert widget was hidden."""
        hide_count = self.widget.get_event_count("hidden")
        if hide_count == 0:
            raise UIAssertionError(f"{self._description} should have been hidden but hide() was never called")
        return self
    
    def matches_properties(self, expected_properties: Dict[str, Any]) -> 'UIAssertions':
        """Assert widget properties match expected values."""
        for prop_name, expected_value in expected_properties.items():
            actual_value = self.widget.get_property(prop_name)
            if actual_value != expected_value:
                raise UIAssertionError(
                    f"{self._description}.{prop_name} should be '{expected_value}' but was '{actual_value}'"
                )
        return self


def assert_widget(widget: MockWidget) -> UIAssertions:
    """Create assertion object for widget."""
    return UIAssertions(widget)


def assert_widget_tree(root_widget: MockWidget) -> 'TreeAssertions':
    """Create assertion object for widget tree."""
    return TreeAssertions(root_widget)


class TreeAssertions:
    """Assertions for widget tree structure."""
    
    def __init__(self, root_widget: MockWidget):
        self.root = root_widget
    
    def has_total_widgets(self, expected_count: int) -> 'TreeAssertions':
        """Assert tree has specific total number of widgets."""
        actual_count = self._count_widgets(self.root)
        if actual_count != expected_count:
            raise UIAssertionError(
                f"Widget tree should have {expected_count} total widgets but had {actual_count}"
            )
        return self
    
    def has_depth(self, expected_depth: int) -> 'TreeAssertions':
        """Assert tree has specific maximum depth."""
        actual_depth = self._calculate_depth(self.root)
        if actual_depth != expected_depth:
            raise UIAssertionError(
                f"Widget tree should have depth {expected_depth} but had {actual_depth}"
            )
        return self
    
    def contains_widget(self, widget_name: str) -> 'TreeAssertions':
        """Assert tree contains widget with specific name."""
        widget = self.root.find_child(widget_name, recursive=True)
        if not widget:
            raise UIAssertionError(f"Widget tree should contain widget '{widget_name}' but it was not found")
        return self
    
    def has_widgets_of_type(self, widget_type, expected_count: int) -> 'TreeAssertions':
        """Assert tree has specific number of widgets of given type."""
        from ..ui_model import WidgetType
        
        if isinstance(widget_type, str):
            widget_type = WidgetType(widget_type)
        
        actual_count = self._count_widgets_of_type(self.root, widget_type)
        if actual_count != expected_count:
            raise UIAssertionError(
                f"Widget tree should have {expected_count} widgets of type '{widget_type.value}' but had {actual_count}"
            )
        return self
    
    def _count_widgets(self, widget: MockWidget) -> int:
        """Recursively count all widgets in tree."""
        count = 1  # Count this widget
        for child in widget.children:
            count += self._count_widgets(child)
        return count
    
    def _calculate_depth(self, widget: MockWidget, current_depth: int = 1) -> int:
        """Recursively calculate maximum depth."""
        if not widget.children:
            return current_depth
        
        max_child_depth = max(
            self._calculate_depth(child, current_depth + 1)
            for child in widget.children
        )
        return max_child_depth
    
    def _count_widgets_of_type(self, widget: MockWidget, widget_type) -> int:
        """Recursively count widgets of specific type."""
        count = 1 if widget.widget_type == widget_type else 0
        for child in widget.children:
            count += self._count_widgets_of_type(child, widget_type)
        return count 