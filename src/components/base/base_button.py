"""
Base Button Component

Modern button component with shadcn/ui styling following the design system.
Includes loading states, icon support, text overflow handling, and full accessibility.
"""

from typing import Optional, Dict, Any
from enum import Enum

from PySide6.QtWidgets import QPushButton, QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal, Property, QTimer, QPoint, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QIcon, QFontMetrics, QMovie, QPainter, QPen

from utils.design_tokens import DesignTokens
from services.theme_manager import ThemeManager
from utils.style_converter import convert_css_to_qt


class ButtonVariant(Enum):
    """Button style variants."""
    DEFAULT = "default"
    SECONDARY = "secondary"
    OUTLINE = "outline"
    GHOST = "ghost"
    DESTRUCTIVE = "destructive"
    LINK = "link"


class ButtonSize(Enum):
    """Button size options."""
    SM = "sm"
    DEFAULT = "default"
    LG = "lg"
    ICON = "icon"


class IconPosition(Enum):
    """Icon position options."""
    LEFT = "left"
    RIGHT = "right"
    ONLY = "only"


class BaseButton(QPushButton):
    """
    Modern button component with shadcn/ui styling.
    
    Features:
    - Multiple variants (default, secondary, outline, ghost, destructive, link)
    - Multiple sizes (sm, default, lg, icon)
    - Icon support with positioning
    - Loading state with spinner
    - Text overflow handling with ellipsis and tooltips
    - Accessibility features
    - Theme integration
    """
    
    # Signals
    variant_changed = Signal(str)
    size_changed = Signal(str)
    loading_changed = Signal(bool)
    
    def __init__(
        self, 
        text: str = "",
        variant: ButtonVariant = ButtonVariant.DEFAULT,
        size: ButtonSize = ButtonSize.DEFAULT,
        icon: Optional[QIcon] = None,
        icon_position: IconPosition = IconPosition.LEFT,
        loading: bool = False,
        max_width: Optional[int] = None,
        enable_ellipsis: bool = True,
        parent: Optional[QWidget] = None
    ):
        """
        Initialize the button.
        
        Args:
            text: Button text
            variant: Button style variant
            size: Button size
            icon: Optional button icon
            icon_position: Icon position (left, right, only)
            loading: Initial loading state
            max_width: Maximum button width in pixels (None for auto)
            enable_ellipsis: Whether to show ellipsis for long text
            parent: Parent widget
        """
        super().__init__(text, parent)
        
        self._variant = variant
        self._size = size
        self._icon_position = icon_position
        self._loading = loading
        self._max_width = max_width
        self._enable_ellipsis = enable_ellipsis
        self._original_text = text
        self._original_icon = icon
        self._theme_manager: Optional[ThemeManager] = None
        
        # Loading animation
        self._loading_angle = 0.0
        self._loading_timer: Optional[QTimer] = None
        self._loading_animation: Optional[QPropertyAnimation] = None
        
        if icon and not loading:
            self.setIcon(icon)
        
        self._setup_ui()
        self._apply_style()
        self._setup_text_overflow()
        
        if loading:
            self.set_loading(True)
    
    def _setup_ui(self) -> None:
        """Set up the button UI properties."""
        # Enable focus and keyboard navigation
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Set cursor
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Size configuration
        size_config = DesignTokens.BUTTON_SIZES.get(self._size.value, {})
        
        if self._size == ButtonSize.ICON:
            # Icon-only button
            self.setFixedSize(size_config.get('width', 40), size_config.get('height', 40))
        else:
            # Text button
            self.setMinimumHeight(size_config.get('height', 40))
            if self._max_width:
                self.setMaximumWidth(self._max_width)
        
        # Enhanced accessible properties
        self._update_accessibility_properties()
    
    def _update_accessibility_properties(self) -> None:
        """Update accessibility properties based on current state."""
        # Set accessible name
        if self._size == ButtonSize.ICON or self._icon_position == IconPosition.ONLY:
            # Icon-only button needs descriptive name
            base_name = self._original_text or "Action button"
            accessible_name = f"{base_name} ({self._variant.value})"
        else:
            accessible_name = self._original_text or "Button"
        
        self.setAccessibleName(accessible_name)
        
        # Set accessible description with state information
        description_parts = [f"{self._variant.value} {self._size.value} button"]
        
        if self._loading:
            description_parts.append("Loading")
        
        if not self.isEnabled():
            description_parts.append("Disabled")
            
        self.setAccessibleDescription(", ".join(description_parts))
        
        # Set role for better screen reader support
        # QPushButton already has button role, but we can enhance it
        self.setProperty("accessibilityRole", "button")
        
        # Set busy state for loading (equivalent to aria-busy)
        self.setProperty("accessibilityBusy", self._loading)
    
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
        """Custom paint event to draw loading spinner."""
        super().paintEvent(event)
        
        if self._loading:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Calculate spinner position and size
            rect = self.rect()
            center = rect.center()
            
            # Spinner size based on button size
            if self._size == ButtonSize.SM:
                radius = 8
                pen_width = 2
            elif self._size == ButtonSize.LG:
                radius = 12
                pen_width = 3
            else:
                radius = 10
                pen_width = 2
            
            # Adjust position if there's text
            if self._original_text and self._icon_position != IconPosition.ONLY:
                if self._icon_position == IconPosition.LEFT:
                    center.setX(center.x() - 40)
                elif self._icon_position == IconPosition.RIGHT:
                    center.setX(center.x() + 40)
            
            # Set up pen
            pen = QPen()
            pen.setWidth(pen_width)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            
            # Draw spinner background (muted)
            pen.setColor(self.palette().color(self.palette().ColorRole.Mid))
            painter.setPen(pen)
            painter.drawEllipse(center, radius, radius)
            
            # Draw spinner arc (accent color)
            pen.setColor(self.palette().color(self.palette().ColorRole.Highlight))
            painter.setPen(pen)
            
            # Calculate arc parameters
            start_angle = int(self._loading_angle * 16)  # Qt uses 1/16th degree units
            span_angle = 90 * 16  # 90 degree arc
            
            painter.drawArc(
                center.x() - radius, center.y() - radius,
                radius * 2, radius * 2,
                start_angle, span_angle
            )
            
            painter.end()
    
    def set_loading(self, loading: bool) -> None:
        """
        Set the loading state.
        
        Args:
            loading: Whether button should show loading state
        """
        if self._loading == loading:
            return
            
        self._loading = loading
        
        if loading:
            # Start loading animation
            self.setEnabled(False)
            self._setup_loading_animation()
            if self._loading_animation:
                self._loading_animation.start()
            
            # Hide icon during loading (will show spinner instead)
            if self._original_icon and not self._original_icon.isNull():
                self.setIcon(QIcon())
                
        else:
            # Stop loading animation
            if self._loading_animation:
                self._loading_animation.stop()
                
            self.setEnabled(True)
            
            # Restore original icon
            if self._original_icon and not self._original_icon.isNull():
                self.setIcon(self._original_icon)
        
        # Update accessibility properties to reflect new state
        self._update_accessibility_properties()
        
        self.loading_changed.emit(loading)
        self.update()  # Trigger repaint
    
    @property
    def loading(self) -> bool:
        """Get current loading state."""
        return self._loading
    
    def _setup_text_overflow(self) -> None:
        """Set up text overflow handling and tooltips."""
        if not self._enable_ellipsis or self._size == ButtonSize.ICON:
            return
            
        # Enable tooltips
        self.setToolTip(self._original_text)
        
        # Set up text truncation if max_width is specified
        if self._max_width:
            self._truncate_text()
    
    def _truncate_text(self) -> None:
        """Truncate text if it exceeds max width."""
        if not self._max_width or not self._original_text:
            return
            
        # Get font metrics
        font_metrics = QFontMetrics(self.font())
        
        # Calculate available width (accounting for padding and icon)
        size_config = DesignTokens.BUTTON_SIZES.get(self._size.value, {})
        padding = size_config.get('padding_h', 16) * 2
        
        # Account for icon space
        icon_width = 0
        if (self._original_icon and not self._original_icon.isNull()) or self._loading:
            if self._icon_position == IconPosition.ONLY:
                icon_width = 0  # No text space needed
            else:
                icon_width = 24  # Icon + spacing
        
        available_width = self._max_width - padding - icon_width
        
        # Check if text needs truncation
        if self._icon_position == IconPosition.ONLY:
            # Icon-only button, no text truncation needed
            return
            
        text_width = font_metrics.horizontalAdvance(self._original_text)
        
        if text_width > available_width:
            # Truncate text with ellipsis
            truncated_text = font_metrics.elidedText(
                self._original_text, 
                Qt.TextElideMode.ElideRight, 
                available_width
            )
            super().setText(truncated_text)  # Use super to avoid recursion
            
            # Update tooltip to show full text
            self.setToolTip(self._original_text)
        else:
            # Text fits, no need for ellipsis
            super().setText(self._original_text)
            self.setToolTip("")  # Clear tooltip if not needed
    
    def _apply_style(self) -> None:
        """Apply the appropriate style based on variant and size."""
        tokens = DesignTokens()
        
        # Get size configuration
        size_config = tokens.BUTTON_SIZES.get(self._size.value, tokens.BUTTON_SIZES['default'])
        
        # Get theme colors
        color_vars = self._get_theme_colors()
        
        # Text overflow CSS class
        text_overflow_class = "truncate" if self._enable_ellipsis and self._max_width else ""
        
        # Base styles common to all variants
        base_style = f"""
        QPushButton {{
            font-family: {tokens.get_font_string()};
            font-size: {size_config['font_size']}px;
            font-weight: {tokens.TYPOGRAPHY['font_medium']};
            border-radius: {tokens.BORDER_RADIUS['radius_default']}px;
            min-height: {size_config['height']}px;
            text-align: left;
        }}
        
        QPushButton:focus {{
            outline: {tokens.FOCUS_STYLES['ring_width']}px solid var(--ring);
            outline-offset: {tokens.FOCUS_STYLES['ring_offset']}px;
        }}
        
        QPushButton:disabled {{
            opacity: 0.5;
        }}
        """
        
        # Add text overflow styles if enabled
        if self._enable_ellipsis and self._max_width:
            base_style += f"""
            QPushButton {{
                max-width: {self._max_width}px;
            }}
            """
        
        # Variant-specific styles
        variant_styles = {
            ButtonVariant.DEFAULT: f"""
            QPushButton {{
                background-color: var(--primary);
                color: var(--primary-foreground);
                border: none;
                padding: 0 {size_config['padding_h']}px;
            }}
            QPushButton:hover:!disabled {{
                background-color: var(--primary);
                opacity: 0.9;
            }}
            QPushButton:pressed {{
                background-color: var(--primary);
                opacity: 0.8;
            }}
            """,
            
            ButtonVariant.SECONDARY: f"""
            QPushButton {{
                background-color: var(--secondary);
                color: var(--secondary-foreground);
                border: none;
                padding: 0 {size_config['padding_h']}px;
            }}
            QPushButton:hover:!disabled {{
                background-color: var(--secondary);
                opacity: 0.8;
            }}
            """,
            
            ButtonVariant.OUTLINE: f"""
            QPushButton {{
                background-color: transparent;
                color: var(--foreground);
                border: 1px solid var(--border);
                padding: 0 {size_config['padding_h']}px;
            }}
            QPushButton:hover:!disabled {{
                background-color: var(--accent);
                color: var(--accent-foreground);
            }}
            """,
            
            ButtonVariant.GHOST: f"""
            QPushButton {{
                background-color: transparent;
                color: var(--foreground);
                border: none;
                padding: 0 {size_config['padding_h']}px;
            }}
            QPushButton:hover:!disabled {{
                background-color: var(--accent);
                color: var(--accent-foreground);
            }}
            """,
            
            ButtonVariant.DESTRUCTIVE: f"""
            QPushButton {{
                background-color: var(--destructive);
                color: var(--destructive-foreground);
                border: none;
                padding: 0 {size_config['padding_h']}px;
            }}
            QPushButton:hover:!disabled {{
                background-color: var(--destructive);
                opacity: 0.9;
            }}
            """,
        }
        
        # Combine styles
        full_style = base_style + variant_styles.get(self._variant, "")
        
        # Convert to Qt-compatible stylesheet
        qt_style = convert_css_to_qt(full_style, color_vars)
        self.setStyleSheet(qt_style)
    
    def setText(self, text: str) -> None:
        """
        Set the button text with automatic truncation handling.
        
        Args:
            text: The text to display
        """
        self._original_text = text
        super().setText(text)
        
        # Update accessibility properties when text changes
        self._update_accessibility_properties()
        
        # Handle text truncation
        if self._enable_ellipsis:
            self._setup_text_overflow()
    
    def resizeEvent(self, event) -> None:
        """Handle resize events to re-truncate text if needed."""
        super().resizeEvent(event)
        if self._enable_ellipsis and self._max_width:
            self._truncate_text()
    
    def set_max_width(self, width: Optional[int]) -> None:
        """
        Set maximum width and enable/disable text truncation.
        
        Args:
            width: Maximum width in pixels (None to disable)
        """
        self._max_width = width
        if width:
            self.setMaximumWidth(width)
            if self._enable_ellipsis:
                self._truncate_text()
        else:
            self.setMaximumWidth(16777215)  # Qt's maximum width
            self.setText(self._original_text)
            self.setToolTip("")
        
        self._apply_style()
    
    def set_ellipsis_enabled(self, enabled: bool) -> None:
        """
        Enable or disable text ellipsis.
        
        Args:
            enabled: Whether to enable ellipsis
        """
        self._enable_ellipsis = enabled
        if enabled and self._max_width:
            self._truncate_text()
        else:
            self.setText(self._original_text)
            self.setToolTip("")
        
        self._apply_style()
    
    @property
    def original_text(self) -> str:
        """Get the original, non-truncated text."""
        return self._original_text
    
    @property 
    def max_width(self) -> Optional[int]:
        """Get the maximum width setting."""
        return self._max_width
    
    @property
    def ellipsis_enabled(self) -> bool:
        """Get whether ellipsis is enabled."""
        return self._enable_ellipsis
    
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
                'primary': self._theme_manager.get_color('primary'),
                'primary_foreground': self._theme_manager.get_color('primary_foreground'),
                'secondary': self._theme_manager.get_color('secondary'),
                'secondary_foreground': self._theme_manager.get_color('secondary_foreground'),
                'foreground': self._theme_manager.get_color('foreground'),
                'accent': self._theme_manager.get_color('accent'),
                'accent_foreground': self._theme_manager.get_color('accent_foreground'),
                'destructive': self._theme_manager.get_color('destructive'),
                'destructive_foreground': self._theme_manager.get_color('destructive_foreground'),
                'border': self._theme_manager.get_color('border'),
                'ring': self._theme_manager.get_color('ring'),
            }
        else:
            # Default light theme colors as fallback
            return {
                'primary': 'hsl(222.2, 47.4%, 11.2%)',
                'primary_foreground': 'hsl(210, 40%, 98%)',
                'secondary': 'hsl(210, 40%, 96%)',
                'secondary_foreground': 'hsl(222.2, 84%, 4.9%)',
                'foreground': 'hsl(222.2, 84%, 4.9%)',
                'accent': 'hsl(210, 40%, 96%)',
                'accent_foreground': 'hsl(222.2, 84%, 4.9%)',
                'destructive': 'hsl(0, 84.2%, 60.2%)',
                'destructive_foreground': 'hsl(210, 40%, 98%)',
                'border': 'hsl(214.3, 31.8%, 91.4%)',
                'ring': 'hsl(222.2, 84%, 4.9%)',
            }
    
    # Properties
    @property
    def variant(self) -> ButtonVariant:
        """Get the current button variant."""
        return self._variant
    
    @variant.setter
    def variant(self, value: ButtonVariant) -> None:
        """Set the button variant."""
        if self._variant != value:
            self._variant = value
            self._update_accessibility_properties()
            self._apply_style()
            self.variant_changed.emit(value.value)
    
    @property
    def size(self) -> ButtonSize:
        """Get the current button size."""
        return self._size
    
    @size.setter
    def size(self, value: ButtonSize) -> None:
        """Set the button size."""
        if self._size != value:
            self._size = value
            self._setup_ui()
            self._apply_style()
            self.size_changed.emit(value.value)
    
    @property
    def icon_position(self) -> IconPosition:
        """Get the current icon position."""
        return self._icon_position
    
    @icon_position.setter
    def icon_position(self, value: IconPosition) -> None:
        """Set the icon position."""
        if self._icon_position != value:
            self._icon_position = value
            self._setup_ui()
            self._apply_style()
    
    # Convenience factory methods
    @staticmethod
    def create_primary(
        text: str,
        icon: Optional[QIcon] = None,
        parent: Optional[QWidget] = None
    ) -> 'BaseButton':
        """Create a primary button."""
        return BaseButton(text, ButtonVariant.DEFAULT, ButtonSize.DEFAULT, icon, parent)
    
    @staticmethod
    def create_secondary(
        text: str,
        icon: Optional[QIcon] = None,
        parent: Optional[QWidget] = None
    ) -> 'BaseButton':
        """Create a secondary button."""
        return BaseButton(text, ButtonVariant.SECONDARY, ButtonSize.DEFAULT, icon, parent)
    
    @staticmethod
    def create_outline(
        text: str,
        icon: Optional[QIcon] = None,
        parent: Optional[QWidget] = None
    ) -> 'BaseButton':
        """Create an outline button."""
        return BaseButton(text, ButtonVariant.OUTLINE, ButtonSize.DEFAULT, icon, parent)
    
    @staticmethod
    def create_ghost(
        text: str,
        icon: Optional[QIcon] = None,
        parent: Optional[QWidget] = None
    ) -> 'BaseButton':
        """Create a ghost button."""
        return BaseButton(text, ButtonVariant.GHOST, ButtonSize.DEFAULT, icon, parent)
    
    @staticmethod
    def create_destructive(
        text: str,
        icon: Optional[QIcon] = None,
        parent: Optional[QWidget] = None
    ) -> 'BaseButton':
        """Create a destructive button."""
        return BaseButton(text, ButtonVariant.DESTRUCTIVE, ButtonSize.DEFAULT, icon, parent)
    
    @staticmethod
    def create_link(
        text: str,
        icon: Optional[QIcon] = None,
        parent: Optional[QWidget] = None
    ) -> 'BaseButton':
        """Create a link button."""
        return BaseButton(text, ButtonVariant.LINK, ButtonSize.DEFAULT, icon, parent)
    
    @staticmethod
    def create_icon(
        icon: QIcon,
        variant: ButtonVariant = ButtonVariant.GHOST,
        parent: Optional[QWidget] = None
    ) -> 'BaseButton':
        """Create an icon-only button."""
        return BaseButton("", variant, ButtonSize.ICON, icon, parent) 