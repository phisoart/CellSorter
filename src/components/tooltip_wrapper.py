"""
Tooltip Wrapper Component

Automatically shows tooltips for truncated text in Qt widgets.
Follows shadcn/ui patterns for tooltip behavior and styling.
"""

from typing import Optional, Union, Any
from enum import Enum

from PySide6.QtWidgets import (
    QLabel, QWidget, QHBoxLayout, QVBoxLayout, 
    QSizePolicy, QApplication
)
from PySide6.QtCore import (
    Qt, Signal, QTimer, QRect, QPoint, 
    QEvent, QSize
)
from PySide6.QtGui import QFontMetrics, QPainter, QResizeEvent

from utils.design_tokens import DesignTokens
from services.theme_manager import ThemeManager
from utils.style_converter import convert_css_to_qt


class TooltipPosition(Enum):
    """Tooltip position options."""
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"
    AUTO = "auto"


class TruncatedTextLabel(QLabel):
    """
    Enhanced QLabel that automatically shows tooltips when text is truncated.
    
    Features:
    - Automatic truncation detection
    - Dynamic tooltip management
    - Responsive behavior on resize
    - Accessibility support
    """
    
    # Signals
    truncation_changed = Signal(bool)  # Emitted when truncation state changes
    
    def __init__(
        self,
        text: str = "",
        max_width: Optional[int] = None,
        max_lines: int = 1,
        tooltip_position: TooltipPosition = TooltipPosition.AUTO,
        tooltip_delay: int = 500,
        parent: Optional[QWidget] = None
    ):
        """
        Initialize the truncated text label.
        
        Args:
            text: The text to display
            max_width: Maximum width in pixels (None for no limit)
            max_lines: Maximum number of lines (1 for single line)
            tooltip_position: Preferred tooltip position
            tooltip_delay: Delay before showing tooltip in milliseconds
            parent: Parent widget
        """
        super().__init__(text, parent)
        
        self._original_text = text
        self._max_width = max_width
        self._max_lines = max_lines
        self._tooltip_position = tooltip_position
        self._tooltip_delay = tooltip_delay
        self._is_truncated = False
        self._theme_manager: Optional[ThemeManager] = None
        
        # Timer for tooltip delay
        self._tooltip_timer = QTimer()
        self._tooltip_timer.setSingleShot(True)
        self._tooltip_timer.timeout.connect(self._show_tooltip)
        
        self._setup_ui()
        self._apply_style()
        self._update_truncation()
    
    def _setup_ui(self) -> None:
        """Set up the label UI properties."""
        # Set text elide mode for single line
        if self._max_lines == 1:
            self.setTextFormat(Qt.TextFormat.PlainText)
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        else:
            self.setWordWrap(True)
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Set maximum width if specified
        if self._max_width:
            self.setMaximumWidth(self._max_width)
        
        # Enable mouse tracking for hover events
        self.setMouseTracking(True)
        
        # Set accessible properties
        self.setAccessibleName(self._original_text or "Text")
        self.setAccessibleDescription("Text label with automatic tooltip")
    
    def _apply_style(self) -> None:
        """Apply styling based on design system."""
        tokens = DesignTokens()
        
        # Get theme colors
        color_vars = self._get_theme_colors()
        
        # Base styles
        base_style = f"""
        QLabel {{
            font-family: {tokens.get_font_string()};
            font-size: {tokens.TYPOGRAPHY['font_size_base']}px;
            color: var(--foreground);
            background-color: transparent;
            padding: {tokens.SPACING['spacing_1']}px;
        }}
        """
        
        # Convert to Qt-compatible stylesheet
        qt_style = convert_css_to_qt(base_style, color_vars)
        self.setStyleSheet(qt_style)
    
    def _get_theme_colors(self) -> dict:
        """Get current theme colors."""
        if self._theme_manager:
            return self._theme_manager.get_current_colors()
        
        # Fallback colors
        return {
            'foreground': '#000000',
            'background': '#ffffff',
            'muted_foreground': '#6b7280',
        }
    
    def _update_truncation(self) -> None:
        """Update truncation state and text display."""
        if not self._original_text:
            self._is_truncated = False
            self.setToolTip("")
            return
        
        font_metrics = QFontMetrics(self.font())
        available_width = self.width() - (self.margin() * 2)
        
        if self._max_lines == 1:
            # Single line truncation
            text_width = font_metrics.horizontalAdvance(self._original_text)
            
            if available_width > 0 and text_width > available_width:
                # Text is truncated
                self._is_truncated = True
                truncated_text = font_metrics.elidedText(
                    self._original_text,
                    Qt.TextElideMode.ElideRight,
                    available_width
                )
                super().setText(truncated_text)
                self.setToolTip(self._original_text)
            else:
                # Text fits
                self._is_truncated = False
                super().setText(self._original_text)
                self.setToolTip("")
        else:
            # Multi-line truncation (simplified approach)
            line_height = font_metrics.height()
            available_height = self.height() - (self.margin() * 2)
            max_visible_lines = max(1, available_height // line_height)
            
            if max_visible_lines < self._max_lines:
                # Might be truncated - show tooltip
                self._is_truncated = True
                self.setToolTip(self._original_text)
            else:
                # Check if text actually fits
                text_rect = font_metrics.boundingRect(
                    QRect(0, 0, available_width, available_height),
                    Qt.TextFlag.TextWordWrap,
                    self._original_text
                )
                
                if text_rect.height() > available_height:
                    self._is_truncated = True
                    self.setToolTip(self._original_text)
                else:
                    self._is_truncated = False
                    self.setToolTip("")
            
            super().setText(self._original_text)
        
        # Emit signal if truncation state changed
        self.truncation_changed.emit(self._is_truncated)
    
    def setText(self, text: str) -> None:
        """
        Set the text content.
        
        Args:
            text: The text to display
        """
        self._original_text = text
        self.setAccessibleName(text or "Text")
        self._update_truncation()
    
    def text(self) -> str:
        """Get the original (non-truncated) text."""
        return self._original_text
    
    def displayed_text(self) -> str:
        """Get the currently displayed (possibly truncated) text."""
        return super().text()
    
    def is_truncated(self) -> bool:
        """Check if the text is currently truncated."""
        return self._is_truncated
    
    def set_max_width(self, width: Optional[int]) -> None:
        """
        Set maximum width.
        
        Args:
            width: Maximum width in pixels (None for no limit)
        """
        self._max_width = width
        if width:
            self.setMaximumWidth(width)
        else:
            self.setMaximumWidth(16777215)  # Qt's maximum width
        self._update_truncation()
    
    def set_max_lines(self, lines: int) -> None:
        """
        Set maximum number of lines.
        
        Args:
            lines: Maximum number of lines
        """
        self._max_lines = max(1, lines)
        
        if self._max_lines == 1:
            self.setWordWrap(False)
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        else:
            self.setWordWrap(True)
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        self._update_truncation()
    
    def set_theme_manager(self, theme_manager: ThemeManager) -> None:
        """Set the theme manager for dynamic theming."""
        self._theme_manager = theme_manager
        if theme_manager:
            theme_manager.theme_changed.connect(self._on_theme_changed)
        self._apply_style()
    
    def _on_theme_changed(self, theme_name: str) -> None:
        """Handle theme changes."""
        self._apply_style()
    
    def resizeEvent(self, event: QResizeEvent) -> None:
        """Handle resize events to update truncation."""
        super().resizeEvent(event)
        # Use timer to avoid excessive updates during resize
        QTimer.singleShot(50, self._update_truncation)
    
    def enterEvent(self, event: QEvent) -> None:
        """Handle mouse enter events for tooltip delay."""
        super().enterEvent(event)
        if self._is_truncated and self._tooltip_delay > 0:
            self._tooltip_timer.start(self._tooltip_delay)
    
    def leaveEvent(self, event: QEvent) -> None:
        """Handle mouse leave events to cancel tooltip."""
        super().leaveEvent(event)
        self._tooltip_timer.stop()
    
    def _show_tooltip(self) -> None:
        """Show the tooltip at the appropriate position."""
        if not self._is_truncated:
            return
        
        # Get cursor position relative to widget
        cursor_pos = self.mapFromGlobal(QApplication.instance().cursor().pos())
        
        # Show tooltip at cursor position
        global_pos = self.mapToGlobal(cursor_pos)
        self.setToolTip(self._original_text)
        
        # Force tooltip to show
        QApplication.instance().processEvents()


class TooltipWrapper(QWidget):
    """
    Wrapper widget that can contain any child widget and provides tooltip functionality.
    
    Useful for wrapping existing widgets that don't have built-in truncation support.
    """
    
    def __init__(
        self,
        child_widget: Optional[QWidget] = None,
        tooltip_text: str = "",
        auto_tooltip: bool = True,
        parent: Optional[QWidget] = None
    ):
        """
        Initialize the tooltip wrapper.
        
        Args:
            child_widget: The widget to wrap
            tooltip_text: Static tooltip text (overrides auto tooltip)
            auto_tooltip: Whether to automatically generate tooltips
            parent: Parent widget
        """
        super().__init__(parent)
        
        self._child_widget = child_widget
        self._tooltip_text = tooltip_text
        self._auto_tooltip = auto_tooltip
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the wrapper UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        if self._child_widget:
            layout.addWidget(self._child_widget)
            
            # Set tooltip
            if self._tooltip_text:
                self._child_widget.setToolTip(self._tooltip_text)
            elif self._auto_tooltip and hasattr(self._child_widget, 'text'):
                self._child_widget.setToolTip(self._child_widget.text())
    
    def set_child_widget(self, widget: QWidget) -> None:
        """
        Set or replace the child widget.
        
        Args:
            widget: The widget to wrap
        """
        if self._child_widget:
            self.layout().removeWidget(self._child_widget)
            self._child_widget.setParent(None)
        
        self._child_widget = widget
        if widget:
            self.layout().addWidget(widget)
            
            # Update tooltip
            if self._tooltip_text:
                widget.setToolTip(self._tooltip_text)
            elif self._auto_tooltip and hasattr(widget, 'text'):
                widget.setToolTip(widget.text())
    
    def set_tooltip_text(self, text: str) -> None:
        """
        Set static tooltip text.
        
        Args:
            text: The tooltip text
        """
        self._tooltip_text = text
        if self._child_widget:
            self._child_widget.setToolTip(text)
    
    def child_widget(self) -> Optional[QWidget]:
        """Get the wrapped child widget."""
        return self._child_widget


# Convenience factory functions
def create_truncated_label(
    text: str,
    max_width: Optional[int] = None,
    max_lines: int = 1,
    parent: Optional[QWidget] = None
) -> TruncatedTextLabel:
    """
    Create a truncated text label with automatic tooltip.
    
    Args:
        text: The text to display
        max_width: Maximum width in pixels
        max_lines: Maximum number of lines
        parent: Parent widget
        
    Returns:
        Configured TruncatedTextLabel instance
    """
    return TruncatedTextLabel(
        text=text,
        max_width=max_width,
        max_lines=max_lines,
        parent=parent
    )


def wrap_with_tooltip(
    widget: QWidget,
    tooltip_text: str = "",
    auto_tooltip: bool = True
) -> TooltipWrapper:
    """
    Wrap an existing widget with tooltip functionality.
    
    Args:
        widget: The widget to wrap
        tooltip_text: Static tooltip text
        auto_tooltip: Whether to automatically generate tooltips
        
    Returns:
        TooltipWrapper instance containing the widget
    """
    wrapper = TooltipWrapper(
        child_widget=widget,
        tooltip_text=tooltip_text,
        auto_tooltip=auto_tooltip
    )
    return wrapper 