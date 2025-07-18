"""
Base Input Component

Modern input field component with validation states following the design system.
"""

from typing import Optional, Dict
from enum import Enum

from PySide6.QtWidgets import QLineEdit, QWidget
from PySide6.QtCore import Qt, Signal, Property, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPalette, QPainter, QPen, QColor

from utils.design_tokens import DesignTokens
from services.theme_manager import ThemeManager
from utils.style_converter import convert_css_to_qt
from utils.accessibility import setup_input_accessibility, set_error_state, update_loading_state, AccessibilityState


class InputState(Enum):
    """Input field states."""
    DEFAULT = "default"
    FOCUSED = "focused"
    ERROR = "error"
    DISABLED = "disabled"
    PENDING = "pending"


class BaseInput(QLineEdit):
    """
    Modern input field with validation states.
    
    Implements the design system's input specifications with proper
    focus handling, error states, pending states, and accessibility features.
    """
    
    # Signals
    state_changed = Signal(str)
    error_changed = Signal(bool)
    pending_changed = Signal(bool)
    
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
        self._is_pending = False
        self._theme_manager: Optional[ThemeManager] = None
        
        # Loading animation properties
        self._loading_angle = 0.0
        self._loading_animation: Optional[QPropertyAnimation] = None
        
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
        
        # Enhanced accessibility using utility functions
        setup_input_accessibility(
            self,
            label=self.placeholderText() or "Input field",
            placeholder=self.placeholderText()
        )
        
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
        
        QLineEdit[isPending="true"] {{
            border-color: var(--ring);
            opacity: 0.8;
        }}
        """
        
        # Convert CSS variables to Qt values
        qt_style = convert_css_to_qt(base_style, color_vars)
        self.setStyleSheet(qt_style)
        
        # Update dynamic properties
        self.setProperty("hasError", self._has_error)
        self.setProperty("isPending", self._is_pending)
        
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
            
            # Update accessibility using utility function
            set_error_state(self, has_error, error_message)
            
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
        """Override setEnabled to handle state changes."""
        super().setEnabled(enabled)
        if enabled:
            self._state = InputState.DEFAULT if not self._has_error and not self._is_pending else (InputState.ERROR if self._has_error else InputState.PENDING)
        else:
            self._state = InputState.DISABLED
        self.state_changed.emit(self._state.value)
    
    # Properties
    @property
    def state(self) -> InputState:
        """Get the current input state."""
        return self._state
    
    @property
    def has_error(self) -> bool:
        """Get whether the input has an error."""
        return self._has_error
    
    @property
    def is_pending(self) -> bool:
        """Get whether the input is in pending state."""
        return self._is_pending
    
    def clear_pending(self) -> None:
        """Clear pending state."""
        self.set_pending(False)
    
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

    def _setup_loading_animation(self) -> None:
        """Set up the loading spinner animation."""
        if not self._loading_animation:
            self._loading_animation = QPropertyAnimation(self, b"loading_angle")
            self._loading_animation.setDuration(1000)
            self._loading_animation.setStartValue(0.0)
            self._loading_animation.setEndValue(360.0)
            self._loading_animation.setLoopCount(-1)  # Infinite loop
            self._loading_animation.setEasingCurve(QEasingCurve.Type.Linear)
    
    @Property(float)
    def loading_angle(self) -> float:
        """Get the current loading spinner angle."""
        return self._loading_angle
    
    @loading_angle.setter
    def loading_angle(self, angle: float) -> None:
        """Set the loading spinner angle."""
        self._loading_angle = angle % 360.0
        self.update()  # Trigger repaint
    
    def paintEvent(self, event) -> None:
        """Custom paint event to draw loading spinner when pending."""
        super().paintEvent(event)
        
        if self._is_pending:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Calculate spinner position and size
            rect = self.rect()
            spinner_size = 16
            margin = 8
            
            # Position spinner on the right side
            center_x = rect.width() - margin - spinner_size // 2
            center_y = rect.height() // 2
            
            # Set up pen
            pen = QPen()
            pen.setWidth(2)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            
            # Draw spinner background (muted)
            pen.setColor(QColor("#e5e7eb"))  # Light gray
            painter.setPen(pen)
            painter.drawEllipse(
                center_x - spinner_size // 2, 
                center_y - spinner_size // 2,
                spinner_size, 
                spinner_size
            )
            
            # Draw spinner arc (accent color)
            pen.setColor(QColor("#3b82f6"))  # Blue
            painter.setPen(pen)
            
            # Calculate arc parameters
            start_angle = int(self._loading_angle * 16)  # Qt uses 1/16th degree units
            span_angle = 90 * 16  # 90 degree arc
            
            painter.drawArc(
                center_x - spinner_size // 2, 
                center_y - spinner_size // 2,
                spinner_size, 
                spinner_size,
                start_angle, 
                span_angle
            )
            
            painter.end()
    
    def set_pending(self, is_pending: bool, pending_message: str = "Validating") -> None:
        """
        Set pending state for async validation.
        
        Args:
            is_pending: Whether the input is in pending state
            pending_message: Message to announce for pending state
        """
        if self._is_pending == is_pending:
            return
            
        self._is_pending = is_pending
        
        if is_pending:
            # Start loading animation
            self._state = InputState.PENDING
            self._setup_loading_animation()
            if self._loading_animation:
                self._loading_animation.start()
            
        else:
            # Stop loading animation
            if self._loading_animation:
                self._loading_animation.stop()
            
            # Reset state if no error
            if not self._has_error:
                self._state = InputState.DEFAULT
        
        # Update accessibility for pending state
        update_loading_state(self, is_pending, pending_message)
        
        self._apply_style()
        self.pending_changed.emit(is_pending)
        self.state_changed.emit(self._state.value)
        self.update()  # Trigger repaint 