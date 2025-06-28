"""
Accessibility Utility Module

Provides common accessibility helpers and patterns for Qt components.
Ensures consistent accessibility implementation across the application.
"""

from typing import Optional, Dict, Any, List
from enum import Enum
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt


class AccessibilityRole(Enum):
    """Standard accessibility roles for better screen reader support."""
    BUTTON = "button"
    LINK = "link"
    TEXTBOX = "textbox"
    COMBOBOX = "combobox"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    TAB = "tab"
    TABPANEL = "tabpanel"
    MENU = "menu"
    MENUITEM = "menuitem"
    LISTBOX = "listbox"
    OPTION = "option"
    GRID = "grid"
    GRIDCELL = "gridcell"
    DIALOG = "dialog"
    ALERTDIALOG = "alertdialog"
    ALERT = "alert"
    STATUS = "status"
    PROGRESSBAR = "progressbar"
    SLIDER = "slider"
    SPINBUTTON = "spinbutton"


class AccessibilityState(Enum):
    """Standard accessibility states."""
    BUSY = "busy"
    CHECKED = "checked"
    DISABLED = "disabled"
    EXPANDED = "expanded"
    HIDDEN = "hidden"
    INVALID = "invalid"
    PRESSED = "pressed"
    READONLY = "readonly"
    REQUIRED = "required"
    SELECTED = "selected"


def set_accessibility_properties(
    widget: QWidget,
    name: Optional[str] = None,
    description: Optional[str] = None,
    role: Optional[AccessibilityRole] = None,
    states: Optional[List[AccessibilityState]] = None,
    value: Optional[str] = None,
    help_text: Optional[str] = None
) -> None:
    """
    Set comprehensive accessibility properties on a widget.
    
    Args:
        widget: The Qt widget to enhance
        name: Accessible name (equivalent to aria-label)
        description: Accessible description (equivalent to aria-describedby)
        role: Widget role for screen readers
        states: List of current states (busy, disabled, etc.)
        value: Current value for input widgets
        help_text: Additional help text
    """
    if name:
        widget.setAccessibleName(name)
    
    if description:
        widget.setAccessibleDescription(description)
    
    if role:
        widget.setProperty("accessibilityRole", role.value)
    
    # Set state properties
    if states:
        for state in states:
            widget.setProperty(f"accessibility{state.value.capitalize()}", True)
    
    if value:
        widget.setProperty("accessibilityValue", value)
    
    if help_text:
        widget.setProperty("accessibilityHelp", help_text)


def update_loading_state(widget: QWidget, is_loading: bool, loading_text: str = "Loading") -> None:
    """
    Update accessibility properties for loading state.
    
    Args:
        widget: Widget to update
        is_loading: Whether widget is in loading state
        loading_text: Text to announce for loading state
    """
    widget.setProperty("accessibilityBusy", is_loading)
    
    if is_loading:
        # Add loading to description
        current_desc = widget.accessibleDescription()
        if current_desc and loading_text not in current_desc:
            widget.setAccessibleDescription(f"{current_desc}, {loading_text}")
        elif not current_desc:
            widget.setAccessibleDescription(loading_text)
    else:
        # Remove loading from description
        current_desc = widget.accessibleDescription()
        if current_desc:
            # Remove loading text variations
            loading_variations = [", Loading", "Loading", ", loading", "loading"]
            for variation in loading_variations:
                current_desc = current_desc.replace(variation, "")
            widget.setAccessibleDescription(current_desc.strip().rstrip(","))


def set_focus_properties(widget: QWidget, focusable: bool = True, tab_order: Optional[int] = None) -> None:
    """
    Configure focus and keyboard navigation properties.
    
    Args:
        widget: Widget to configure
        focusable: Whether widget should be focusable
        tab_order: Tab order position (None for default)
    """
    if focusable:
        widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    else:
        widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    
    if tab_order is not None:
        widget.setProperty("tabOrder", tab_order)


def set_error_state(widget: QWidget, has_error: bool, error_message: Optional[str] = None) -> None:
    """
    Set error state accessibility properties.
    
    Args:
        widget: Widget to update
        has_error: Whether widget has an error
        error_message: Error message to announce
    """
    widget.setProperty("accessibilityInvalid", has_error)
    
    if has_error and error_message:
        widget.setProperty("accessibilityErrorText", error_message)
        
        # Update description to include error
        current_desc = widget.accessibleDescription()
        if current_desc:
            widget.setAccessibleDescription(f"{current_desc}, Error: {error_message}")
        else:
            widget.setAccessibleDescription(f"Error: {error_message}")
    else:
        widget.setProperty("accessibilityErrorText", "")
        
        # Remove error from description
        current_desc = widget.accessibleDescription()
        if current_desc and "Error:" in current_desc:
            # Remove error text
            error_start = current_desc.find(", Error:")
            if error_start != -1:
                widget.setAccessibleDescription(current_desc[:error_start])


def announce_to_screen_reader(widget: QWidget, message: str) -> None:
    """
    Announce a message to screen readers (live region).
    
    Args:
        widget: Widget context for announcement
        message: Message to announce
    """
    # In Qt, we can use a temporary property change to trigger screen reader updates
    widget.setProperty("accessibilityLiveRegion", message)


def create_keyboard_shortcut_text(shortcut: str) -> str:
    """
    Create standardized keyboard shortcut text for accessibility.
    
    Args:
        shortcut: Keyboard shortcut (e.g., "Ctrl+S")
        
    Returns:
        Formatted shortcut text for screen readers
    """
    # Standardize shortcut format for screen readers
    shortcut = shortcut.replace("Ctrl", "Control")
    shortcut = shortcut.replace("Alt", "Alt")
    shortcut = shortcut.replace("Shift", "Shift")
    return f"Keyboard shortcut: {shortcut}"


def get_accessibility_summary(widget: QWidget) -> Dict[str, Any]:
    """
    Get a summary of current accessibility properties for debugging.
    
    Args:
        widget: Widget to inspect
        
    Returns:
        Dictionary of accessibility properties
    """
    return {
        "name": widget.accessibleName(),
        "description": widget.accessibleDescription(),
        "role": widget.property("accessibilityRole"),
        "busy": widget.property("accessibilityBusy"),
        "invalid": widget.property("accessibilityInvalid"),
        "value": widget.property("accessibilityValue"),
        "focus_policy": widget.focusPolicy(),
        "enabled": widget.isEnabled(),
        "visible": widget.isVisible(),
    }


def setup_button_accessibility(
    button: QWidget,
    text: str,
    variant: str = "default",
    is_loading: bool = False,
    is_icon_only: bool = False
) -> None:
    """
    Set up standard accessibility for button widgets.
    
    Args:
        button: Button widget
        text: Button text
        variant: Button variant (default, primary, etc.)
        is_loading: Whether button is loading
        is_icon_only: Whether button is icon-only
    """
    # Set basic properties
    name = text if text else "Action button"
    if is_icon_only:
        name = f"{name} ({variant} button)"
    
    description = f"{variant} button"
    if is_loading:
        description += ", Loading"
    
    set_accessibility_properties(
        button,
        name=name,
        description=description,
        role=AccessibilityRole.BUTTON,
        states=[AccessibilityState.BUSY] if is_loading else None
    )
    
    set_focus_properties(button, focusable=True)


def setup_input_accessibility(
    input_widget: QWidget,
    label: str,
    placeholder: Optional[str] = None,
    is_required: bool = False,
    has_error: bool = False,
    error_message: Optional[str] = None
) -> None:
    """
    Set up standard accessibility for input widgets.
    
    Args:
        input_widget: Input widget
        label: Input label
        placeholder: Placeholder text
        is_required: Whether input is required
        has_error: Whether input has validation error
        error_message: Error message if any
    """
    description_parts = []
    
    if placeholder:
        description_parts.append(f"Placeholder: {placeholder}")
    
    if is_required:
        description_parts.append("Required")
    
    states = []
    if is_required:
        states.append(AccessibilityState.REQUIRED)
    
    set_accessibility_properties(
        input_widget,
        name=label,
        description=", ".join(description_parts) if description_parts else None,
        role=AccessibilityRole.TEXTBOX,
        states=states
    )
    
    if has_error:
        set_error_state(input_widget, True, error_message)
    
    set_focus_properties(input_widget, focusable=True) 