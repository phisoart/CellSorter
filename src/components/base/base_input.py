"""
Base Input Component

Modern input field component with validation states following the design system.
"""

from typing import Optional, Dict
from enum import Enum

from PySide6.QtWidgets import QLineEdit, QWidget
from PySide6.QtCore import Qt, Signal, Property
from PySide6.QtGui import QPalette

from utils.design_tokens import DesignTokens
from utils.theme_manager import ThemeManager
from utils.style_converter import convert_css_to_qt


class InputState(Enum):
    """Input field states."""
    DEFAULT = "default"
    FOCUSED = "focused"
    ERROR = "error"
    DISABLED = "disabled"


class BaseInput(QLineEdit):
    """
    Modern input field with validation states.
    
    Implements the design system's input specifications with proper
    focus handling, error states, and accessibility features.
    """
    
    # Signals
    state_changed = Signal(str)
    error_changed = Signal(bool)
    
    def __init__(
        self,
        placeholder: str = "",
        parent: Optional[QWidget] = None
    ):
        """
        Initialize the input field.
        
        Args:
            placeholder: Placeholder text
            parent: Parent widget
        """
        super().__init__(parent)
        
        self._state = InputState.DEFAULT
        self._has_error = False
        self._theme_manager: Optional[ThemeManager] = None
        
        if placeholder:
            self.setPlaceholderText(placeholder)
        
        self._setup_ui()
        self._apply_style()
    
    def _setup_ui(self) -> None:
        """Set up the input UI properties."""
        tokens = DesignTokens()
        
        # Enable focus
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Set dimensions
        self.setMinimumHeight(tokens.DIMENSIONS['input_height'])
        
        # Set accessible properties
        self.setAccessibleName(self.placeholderText() or "Input field")
        self.setAccessibleDescription("Text input field")
        
        # Clear button
        self.setClearButtonEnabled(True)
    
    def _apply_style(self) -> None:
        """Apply the appropriate style based on state."""
        tokens = DesignTokens()
        
        # Get theme colors
        color_vars = self._get_theme_colors()
        
        # Base styles
        base_style = f"""
        QLineEdit {{
            font-family: {tokens.get_font_string()};
            font-size: {tokens.TYPOGRAPHY['text_sm']}px;
            background-color: transparent;
            border: 1px solid var(--border);
            border-radius: {tokens.BORDER_RADIUS['radius_default']}px;
            padding: {tokens.SPACING['spacing_2']}px {tokens.SPACING['spacing_3']}px;
            min-height: {tokens.DIMENSIONS['input_height']}px;
        }}
        
        QLineEdit:focus {{
            border-color: var(--ring);
            outline: {tokens.FOCUS_STYLES['ring_width']}px solid var(--ring);
            outline-offset: {tokens.FOCUS_STYLES['ring_offset']}px;
        }}
        
        QLineEdit:disabled {{
            background-color: var(--muted);
            color: var(--muted-foreground);
            opacity: 0.5;
        }}
        
        QLineEdit[hasError="true"] {{
            border-color: var(--destructive);
        }}
        
        QLineEdit[hasError="true"]:focus {{
            border-color: var(--destructive);
            outline-color: var(--destructive);
        }}
        """
        
        # Convert CSS variables to Qt values
        qt_style = convert_css_to_qt(base_style, color_vars)
        self.setStyleSheet(qt_style)
        
        # Update dynamic properties
        self.setProperty("hasError", self._has_error)
        
        # Force style update
        self.style().unpolish(self)
        self.style().polish(self)
    
    def set_theme_manager(self, theme_manager: ThemeManager) -> None:
        """
        Set the theme manager for dynamic theme updates.
        
        Args:
            theme_manager: ThemeManager instance
        """
        self._theme_manager = theme_manager
        self._theme_manager.theme_changed.connect(self._on_theme_changed)
    
    def _on_theme_changed(self, theme_name: str) -> None:
        """Handle theme change."""
        self._apply_style()
    
    def _get_theme_colors(self) -> Dict[str, str]:
        """
        Get theme color variables for style conversion.
        
        Returns:
            Dictionary mapping color variable names to their values
        """
        if self._theme_manager:
            # Get colors from theme manager
            return {
                'border': self._theme_manager.get_color('border'),
                'ring': self._theme_manager.get_color('ring'),
                'muted': self._theme_manager.get_color('muted'),
                'muted_foreground': self._theme_manager.get_color('muted_foreground'),
                'destructive': self._theme_manager.get_color('destructive'),
            }
        else:
            # Default light theme colors as fallback
            return {
                'border': 'hsl(214.3, 31.8%, 91.4%)',
                'ring': 'hsl(222.2, 84%, 4.9%)',
                'muted': 'hsl(210, 40%, 96%)',
                'muted_foreground': 'hsl(215.4, 16.3%, 46.9%)',
                'destructive': 'hsl(0, 84.2%, 60.2%)',
            }
    
    # State management
    def set_error(self, has_error: bool, error_message: str = "") -> None:
        """
        Set error state for the input.
        
        Args:
            has_error: Whether the input has an error
            error_message: Optional error message for accessibility
        """
        if self._has_error != has_error:
            self._has_error = has_error
            self._state = InputState.ERROR if has_error else InputState.DEFAULT
            
            # Update accessibility
            if has_error and error_message:
                self.setAccessibleDescription(f"Error: {error_message}")
            else:
                self.setAccessibleDescription("Text input field")
            
            self._apply_style()
            self.error_changed.emit(has_error)
            self.state_changed.emit(self._state.value)
    
    def clear_error(self) -> None:
        """Clear any error state."""
        self.set_error(False)
    
    # Event handlers
    def focusInEvent(self, event) -> None:
        """Handle focus in event."""
        super().focusInEvent(event)
        if not self._has_error and self.isEnabled():
            self._state = InputState.FOCUSED
            self.state_changed.emit(self._state.value)
    
    def focusOutEvent(self, event) -> None:
        """Handle focus out event."""
        super().focusOutEvent(event)
        if not self._has_error and self.isEnabled():
            self._state = InputState.DEFAULT
            self.state_changed.emit(self._state.value)
    
    def setEnabled(self, enabled: bool) -> None:
        """Override to handle state changes."""
        super().setEnabled(enabled)
        self._state = InputState.DEFAULT if enabled else InputState.DISABLED
        self.state_changed.emit(self._state.value)
    
    # Properties
    @property
    def state(self) -> InputState:
        """Get the current input state."""
        return self._state
    
    @property
    def has_error(self) -> bool:
        """Check if input has error."""
        return self._has_error
    
    # Convenience factory methods
    @staticmethod
    def create_email(
        placeholder: str = "Email",
        parent: Optional[QWidget] = None
    ) -> 'BaseInput':
        """Create an email input field."""
        input_field = BaseInput(placeholder, parent)
        input_field.setInputMask("")  # Can add email validation
        return input_field
    
    @staticmethod
    def create_password(
        placeholder: str = "Password",
        parent: Optional[QWidget] = None
    ) -> 'BaseInput':
        """Create a password input field."""
        input_field = BaseInput(placeholder, parent)
        input_field.setEchoMode(QLineEdit.EchoMode.Password)
        return input_field
    
    @staticmethod
    def create_search(
        placeholder: str = "Search...",
        parent: Optional[QWidget] = None
    ) -> 'BaseInput':
        """Create a search input field."""
        input_field = BaseInput(placeholder, parent)
        # Could add search icon in the future
        return input_field 