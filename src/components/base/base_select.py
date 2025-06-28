"""
Base Select Component

Modern select dropdown component with validation states following the design system.
"""

from typing import Optional, Dict, List
from enum import Enum

from PySide6.QtWidgets import QComboBox, QWidget
from PySide6.QtCore import Qt, Signal, Property, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPainter, QPen, QColor

from utils.design_tokens import DesignTokens
from services.theme_manager import ThemeManager
from utils.style_converter import convert_css_to_qt
from utils.accessibility import setup_input_accessibility, set_error_state, update_loading_state, AccessibilityRole


class SelectState(Enum):
    """Select field states."""
    DEFAULT = "default"
    FOCUSED = "focused"
    ERROR = "error"
    DISABLED = "disabled"
    PENDING = "pending"


class BaseSelect(QComboBox):
    """
    Modern select dropdown with validation states.
    
    Implements the design system's select specifications with proper
    focus handling, error states, pending states, and accessibility features.
    """
    
    # Signals
    state_changed = Signal(str)
    error_changed = Signal(bool)
    pending_changed = Signal(bool)
    
    def __init__(
        self,
        placeholder: str = "Select an option",
        options: Optional[List[str]] = None,
        parent: Optional[QWidget] = None
    ):
        """
        Initialize the select field.
        
        Args:
            placeholder: Placeholder text
            options: List of options to populate
            parent: Parent widget
        """
        super().__init__(parent)
        
        self._state = SelectState.DEFAULT
        self._has_error = False
        self._is_pending = False
        self._placeholder = placeholder
        self._theme_manager: Optional[ThemeManager] = None
        
        # Loading animation properties
        self._loading_angle = 0.0
        self._loading_animation: Optional[QPropertyAnimation] = None
        
        self._setup_ui()
        
        if options:
            self.set_options(options)
        
        self._apply_style()
    
    def _setup_ui(self) -> None:
        """Set up the select UI properties."""
        tokens = DesignTokens()
        
        # Enable focus
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Set dimensions
        self.setMinimumHeight(tokens.DIMENSIONS['input_height'])
        
        # Enhanced accessibility using utility functions
        setup_input_accessibility(
            self,
            label=self._placeholder,
            placeholder=self._placeholder
        )
        
        # Set combobox role for accessibility
        self.setProperty("accessibilityRole", AccessibilityRole.COMBOBOX.value)
        
        # Add placeholder item
        self.addItem(self._placeholder)
        self.setCurrentIndex(0)
        
        # Make placeholder item disabled (not selectable in code)
        model = self.model()
        if model:
            item = model.item(0)
            if item:
                item.setEnabled(False)
    
    def set_options(self, options: List[str]) -> None:
        """
        Set the available options.
        
        Args:
            options: List of option strings
        """
        # Clear existing options but keep placeholder
        current_text = self.currentText()
        self.clear()
        
        # Re-add placeholder
        self.addItem(self._placeholder)
        model = self.model()
        if model:
            item = model.item(0)
            if item:
                item.setEnabled(False)
        
        # Add new options
        for option in options:
            self.addItem(option)
        
        # Restore selection if it exists in new options
        if current_text in options:
            self.setCurrentText(current_text)
    
    def _apply_style(self) -> None:
        """Apply the appropriate style based on state."""
        tokens = DesignTokens()
        
        # Get theme colors
        color_vars = self._get_theme_colors()
        
        # Base styles
        base_style = f"""
        QComboBox {{
            font-family: {tokens.get_font_string()};
            font-size: {tokens.TYPOGRAPHY['text_sm']}px;
            background-color: transparent;
            border: 1px solid var(--border);
            border-radius: {tokens.BORDER_RADIUS['radius_default']}px;
            padding: {tokens.SPACING['spacing_2']}px {tokens.SPACING['spacing_3']}px;
            min-height: {tokens.DIMENSIONS['input_height']}px;
        }}
        
        QComboBox:focus {{
            border-color: var(--ring);
            outline: {tokens.FOCUS_STYLES['ring_width']}px solid var(--ring);
            outline-offset: {tokens.FOCUS_STYLES['ring_offset']}px;
        }}
        
        QComboBox:disabled {{
            background-color: var(--muted);
            color: var(--muted-foreground);
            opacity: 0.5;
        }}
        
        QComboBox[hasError="true"] {{
            border-color: var(--destructive);
        }}
        
        QComboBox[hasError="true"]:focus {{
            border-color: var(--destructive);
            outline-color: var(--destructive);
        }}
        
        QComboBox[isPending="true"] {{
            border-color: var(--ring);
            opacity: 0.8;
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        
        QComboBox::down-arrow {{
            image: none;
            border: none;
            width: 0px;
            height: 0px;
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
            margin = 30  # More margin to avoid dropdown arrow
            
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
    
    # State management
    def set_error(self, has_error: bool, error_message: str = "") -> None:
        """
        Set error state for the select.
        
        Args:
            has_error: Whether the select has an error
            error_message: Optional error message for accessibility
        """
        if self._has_error != has_error:
            self._has_error = has_error
            self._state = SelectState.ERROR if has_error else SelectState.DEFAULT
            
            # Update accessibility using utility function
            set_error_state(self, has_error, error_message)
            
            self._apply_style()
            self.error_changed.emit(has_error)
            self.state_changed.emit(self._state.value)
    
    def set_pending(self, is_pending: bool, pending_message: str = "Loading options") -> None:
        """
        Set pending state for async option loading.
        
        Args:
            is_pending: Whether the select is in pending state
            pending_message: Message to announce for pending state
        """
        if self._is_pending == is_pending:
            return
            
        self._is_pending = is_pending
        
        if is_pending:
            # Start loading animation
            self._state = SelectState.PENDING
            self._setup_loading_animation()
            if self._loading_animation:
                self._loading_animation.start()
            
        else:
            # Stop loading animation
            if self._loading_animation:
                self._loading_animation.stop()
            
            # Reset state if no error
            if not self._has_error:
                self._state = SelectState.DEFAULT
        
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
            self._state = SelectState.FOCUSED
            self.state_changed.emit(self._state.value)
    
    def focusOutEvent(self, event) -> None:
        """Handle focus out event."""
        super().focusOutEvent(event)
        if not self._has_error and not self._is_pending and self.isEnabled():
            self._state = SelectState.DEFAULT
            self.state_changed.emit(self._state.value)
    
    def setEnabled(self, enabled: bool) -> None:
        """Override setEnabled to handle state changes."""
        super().setEnabled(enabled)
        if enabled:
            self._state = SelectState.DEFAULT if not self._has_error and not self._is_pending else (SelectState.ERROR if self._has_error else SelectState.PENDING)
        else:
            self._state = SelectState.DISABLED
        self.state_changed.emit(self._state.value)
    
    # Properties
    @property
    def state(self) -> SelectState:
        """Get the current select state."""
        return self._state
    
    @property
    def has_error(self) -> bool:
        """Get whether the select has an error."""
        return self._has_error
    
    @property
    def is_pending(self) -> bool:
        """Get whether the select is in pending state."""
        return self._is_pending
    
    def get_selected_value(self) -> Optional[str]:
        """
        Get the currently selected value.
        
        Returns:
            Selected value or None if placeholder is selected
        """
        current_text = self.currentText()
        return current_text if current_text != self._placeholder else None
    
    def set_selected_value(self, value: str) -> bool:
        """
        Set the selected value.
        
        Args:
            value: Value to select
            
        Returns:
            True if value was found and selected, False otherwise
        """
        index = self.findText(value)
        if index > 0:  # Don't allow selecting placeholder (index 0)
            self.setCurrentIndex(index)
            return True
        return False
    
    # Convenience factory methods
    @staticmethod
    def create_country_select(parent: Optional[QWidget] = None) -> 'BaseSelect':
        """Create a country selection dropdown."""
        countries = ["United States", "Canada", "United Kingdom", "Germany", "France", "Japan"]
        return BaseSelect("Select country", countries, parent)
    
    @staticmethod
    def create_status_select(parent: Optional[QWidget] = None) -> 'BaseSelect':
        """Create a status selection dropdown."""
        statuses = ["Active", "Inactive", "Pending", "Suspended"]
        return BaseSelect("Select status", statuses, parent)
    
    @staticmethod
    def create_priority_select(parent: Optional[QWidget] = None) -> 'BaseSelect':
        """Create a priority selection dropdown."""
        priorities = ["Low", "Medium", "High", "Critical"]
        return BaseSelect("Select priority", priorities, parent) 