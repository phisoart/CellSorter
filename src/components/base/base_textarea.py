"""
Base Textarea Component

Modern multi-line text input component with validation states following the design system.
"""

from typing import Optional, Dict
from enum import Enum

from PySide6.QtWidgets import QTextEdit, QWidget
from PySide6.QtCore import Qt, Signal, Property, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPainter, QPen, QColor, QTextOption

from utils.design_tokens import DesignTokens
from services.theme_manager import ThemeManager
from utils.style_converter import convert_css_to_qt
from utils.accessibility import setup_input_accessibility, set_error_state, update_loading_state, AccessibilityRole


class TextareaState(Enum):
    """Textarea field states."""
    DEFAULT = "default"
    FOCUSED = "focused"
    ERROR = "error"
    DISABLED = "disabled"
    PENDING = "pending"


class BaseTextarea(QTextEdit):
    """
    Modern multi-line text input with validation states.
    
    Implements the design system's textarea specifications with proper
    focus handling, error states, pending states, and accessibility features.
    """
    
    # Signals
    state_changed = Signal(str)
    error_changed = Signal(bool)
    pending_changed = Signal(bool)
    text_changed = Signal(str)  # Custom text changed signal
    
    def __init__(
        self,
        placeholder: str = "",
        min_height: int = 100,
        max_height: Optional[int] = None,
        parent: Optional[QWidget] = None
    ):
        """
        Initialize the textarea field.
        
        Args:
            placeholder: Placeholder text
            min_height: Minimum height in pixels
            max_height: Maximum height in pixels (None for unlimited)
            parent: Parent widget
        """
        super().__init__(parent)
        
        self._state = TextareaState.DEFAULT
        self._has_error = False
        self._is_pending = False
        self._placeholder = placeholder
        self._min_height = min_height
        self._max_height = max_height
        self._theme_manager: Optional[ThemeManager] = None
        
        # Loading animation properties
        self._loading_angle = 0.0
        self._loading_animation: Optional[QPropertyAnimation] = None
        
        self._setup_ui()
        self._apply_style()
        
        # Connect text changed signal
        self.textChanged.connect(self._on_text_changed)
    
    def _setup_ui(self) -> None:
        """Set up the textarea UI properties."""
        tokens = DesignTokens()
        
        # Enable focus
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Set dimensions
        self.setMinimumHeight(self._min_height)
        if self._max_height:
            self.setMaximumHeight(self._max_height)
        
        # Set placeholder
        if self._placeholder:
            self.setPlaceholderText(self._placeholder)
        
        # Enhanced accessibility using utility functions
        setup_input_accessibility(
            self,
            label=self._placeholder or "Text area",
            placeholder=self._placeholder
        )
        
        # Set textarea role for accessibility
        self.setProperty("accessibilityRole", AccessibilityRole.TEXTBOX.value)
        
        # Enable word wrap
        self.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        
        # Disable horizontal scrollbar
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Set vertical scrollbar policy
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    
    def _on_text_changed(self) -> None:
        """Handle internal text changed signal."""
        self.text_changed.emit(self.toPlainText())
    
    def _apply_style(self) -> None:
        """Apply the appropriate style based on state."""
        tokens = DesignTokens()
        
        # Get theme colors
        color_vars = self._get_theme_colors()
        
        # Base styles
        base_style = f"""
        QTextEdit {{
            font-family: {tokens.get_font_string()};
            font-size: {tokens.TYPOGRAPHY['text_sm']}px;
            background-color: transparent;
            border: 1px solid var(--border);
            border-radius: {tokens.BORDER_RADIUS['radius_default']}px;
            padding: {tokens.SPACING['spacing_2']}px {tokens.SPACING['spacing_3']}px;
            min-height: {self._min_height}px;
        }}
        
        QTextEdit:focus {{
            border-color: var(--ring);
            outline: {tokens.FOCUS_STYLES['ring_width']}px solid var(--ring);
            outline-offset: {tokens.FOCUS_STYLES['ring_offset']}px;
        }}
        
        QTextEdit:disabled {{
            background-color: var(--muted);
            color: var(--muted-foreground);
            opacity: 0.5;
        }}
        
        QTextEdit[hasError="true"] {{
            border-color: var(--destructive);
        }}
        
        QTextEdit[hasError="true"]:focus {{
            border-color: var(--destructive);
            outline-color: var(--destructive);
        }}
        
        QTextEdit[isPending="true"] {{
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
            
            # Position spinner on the top-right corner
            center_x = rect.width() - margin - spinner_size // 2
            center_y = margin + spinner_size // 2
            
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
    
    # State management
    def set_error(self, has_error: bool, error_message: str = "") -> None:
        """
        Set error state for the textarea.
        
        Args:
            has_error: Whether the textarea has an error
            error_message: Optional error message for accessibility
        """
        if self._has_error != has_error:
            self._has_error = has_error
            self._state = TextareaState.ERROR if has_error else TextareaState.DEFAULT
            
            # Update accessibility using utility function
            set_error_state(self, has_error, error_message)
            
            self._apply_style()
            self.error_changed.emit(has_error)
            self.state_changed.emit(self._state.value)
    
    def set_pending(self, is_pending: bool, pending_message: str = "Processing text") -> None:
        """
        Set pending state for async processing.
        
        Args:
            is_pending: Whether the textarea is in pending state
            pending_message: Message to announce for pending state
        """
        if self._is_pending == is_pending:
            return
            
        self._is_pending = is_pending
        
        if is_pending:
            # Start loading animation
            self._state = TextareaState.PENDING
            self._setup_loading_animation()
            if self._loading_animation:
                self._loading_animation.start()
            
        else:
            # Stop loading animation
            if self._loading_animation:
                self._loading_animation.stop()
            
            # Reset state if no error
            if not self._has_error:
                self._state = TextareaState.DEFAULT
        
        # Update accessibility for pending state
        update_loading_state(self, is_pending, pending_message)
        
        self._apply_style()
        self.pending_changed.emit(is_pending)
        self.state_changed.emit(self._state.value)
        self.update()  # Trigger repaint
    
    def clear_error(self) -> None:
        """Clear any error state."""
        self.set_error(False)
    
    def clear_pending(self) -> None:
        """Clear pending state."""
        self.set_pending(False)
    
    # Event handlers
    def focusInEvent(self, event) -> None:
        """Handle focus in event."""
        super().focusInEvent(event)
        if not self._has_error and not self._is_pending and self.isEnabled():
            self._state = TextareaState.FOCUSED
            self.state_changed.emit(self._state.value)
    
    def focusOutEvent(self, event) -> None:
        """Handle focus out event."""
        super().focusOutEvent(event)
        if not self._has_error and not self._is_pending and self.isEnabled():
            self._state = TextareaState.DEFAULT
            self.state_changed.emit(self._state.value)
    
    def setEnabled(self, enabled: bool) -> None:
        """Override setEnabled to handle state changes."""
        super().setEnabled(enabled)
        if enabled:
            self._state = TextareaState.DEFAULT if not self._has_error and not self._is_pending else (TextareaState.ERROR if self._has_error else TextareaState.PENDING)
        else:
            self._state = TextareaState.DISABLED
        self.state_changed.emit(self._state.value)
    
    # Properties
    @property
    def state(self) -> TextareaState:
        """Get the current textarea state."""
        return self._state
    
    @property
    def has_error(self) -> bool:
        """Get whether the textarea has an error."""
        return self._has_error
    
    @property
    def is_pending(self) -> bool:
        """Get whether the textarea is in pending state."""
        return self._is_pending
    
    def get_text(self) -> str:
        """Get the current text content."""
        return self.toPlainText()
    
    def set_text(self, text: str) -> None:
        """Set the text content."""
        self.setPlainText(text)
    
    def get_word_count(self) -> int:
        """Get the current word count."""
        text = self.get_text().strip()
        return len(text.split()) if text else 0
    
    def get_character_count(self) -> int:
        """Get the current character count."""
        return len(self.get_text())
    
    # Convenience factory methods
    @staticmethod
    def create_comment_textarea(parent: Optional[QWidget] = None) -> 'BaseTextarea':
        """Create a comment input textarea."""
        return BaseTextarea("Enter your comment...", 100, 200, parent)
    
    @staticmethod
    def create_description_textarea(parent: Optional[QWidget] = None) -> 'BaseTextarea':
        """Create a description input textarea."""
        return BaseTextarea("Enter description...", 120, 300, parent)
    
    @staticmethod
    def create_message_textarea(parent: Optional[QWidget] = None) -> 'BaseTextarea':
        """Create a message input textarea."""
        return BaseTextarea("Type your message...", 80, 150, parent) 