"""
Skeleton Loader Components

Loading placeholders with shimmer animations following shadcn/ui patterns.
Provides skeleton components for cards, lists, tables, and text elements.
"""

from typing import Optional, List, Tuple
from enum import Enum

from PySide6.QtWidgets import (
    QWidget, QLabel, QFrame, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QSizePolicy, QSpacerItem
)
from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    QParallelAnimationGroup, QSequentialAnimationGroup,
    Property, QRect, Signal
)
from PySide6.QtGui import (
    QPaintEvent, QPainter, QLinearGradient, QColor,
    QBrush, QPen
)

from utils.design_tokens import DesignTokens
from services.theme_manager import ThemeManager
from utils.style_converter import convert_css_to_qt


class SkeletonAnimation(Enum):
    """Skeleton animation types."""
    PULSE = "pulse"
    WAVE = "wave"
    SHIMMER = "shimmer"
    NONE = "none"


class SkeletonShape(Enum):
    """Skeleton shape types."""
    RECTANGLE = "rectangle"
    CIRCLE = "circle"
    ROUNDED = "rounded"


class BaseSkeleton(QFrame):
    """
    Base skeleton component with configurable animations and shapes.
    """
    
    def __init__(
        self,
        width: Optional[int] = None,
        height: Optional[int] = None,
        animation: SkeletonAnimation = SkeletonAnimation.SHIMMER,
        shape: SkeletonShape = SkeletonShape.ROUNDED,
        parent: Optional[QWidget] = None
    ):
        """
        Initialize the skeleton.
        
        Args:
            width: Fixed width in pixels (None for flexible)
            height: Fixed height in pixels (None for flexible)
            animation: Animation type
            shape: Shape type
            parent: Parent widget
        """
        super().__init__(parent)
        
        self._width = width
        self._height = height
        self._animation = animation
        self._shape = shape
        self._theme_manager: Optional[ThemeManager] = None
        
        # Animation properties
        self._animation_opacity = 0.3
        self._animation_position = 0.0
        self._animation_group: Optional[QParallelAnimationGroup] = None
        
        self._setup_ui()
        self._apply_style()
        self._setup_animation()
    
    def _setup_ui(self) -> None:
        """Set up the skeleton UI properties."""
        # Set size policy
        if self._width and self._height:
            self.setFixedSize(self._width, self._height)
        elif self._width:
            self.setFixedWidth(self._width)
            self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        elif self._height:
            self.setFixedHeight(self._height)
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        else:
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Set minimum size for visibility
        if not self._width:
            self.setMinimumWidth(20)
        if not self._height:
            self.setMinimumHeight(20)
        
        # Set accessible properties
        self.setAccessibleName("Loading placeholder")
        self.setAccessibleDescription("Content is loading")
    
    def _apply_style(self) -> None:
        """Apply styling based on design system and shape."""
        tokens = DesignTokens()
        color_vars = self._get_theme_colors()
        
        # Shape-specific border radius
        border_radius = {
            SkeletonShape.RECTANGLE: "0px",
            SkeletonShape.CIRCLE: "50%",
            SkeletonShape.ROUNDED: f"{tokens.BORDER_RADIUS['radius_default']}px"
        }
        
        base_style = f"""
        QFrame {{
            background-color: var(--muted);
            border: none;
            border-radius: {border_radius[self._shape]};
        }}
        """
        
        qt_style = convert_css_to_qt(base_style, color_vars)
        self.setStyleSheet(qt_style)
    
    def _get_theme_colors(self) -> dict:
        """Get current theme colors."""
        if self._theme_manager:
            return self._theme_manager.get_current_colors()
        
        # Fallback colors
        return {
            'muted': '#f1f5f9',
            'muted_foreground': '#64748b',
            'background': '#ffffff',
        }
    
    def _setup_animation(self) -> None:
        """Set up skeleton animation."""
        if self._animation == SkeletonAnimation.NONE:
            return
        
        self._animation_group = QParallelAnimationGroup()
        
        if self._animation == SkeletonAnimation.PULSE:
            self._setup_pulse_animation()
        elif self._animation == SkeletonAnimation.WAVE:
            self._setup_wave_animation()
        elif self._animation == SkeletonAnimation.SHIMMER:
            self._setup_shimmer_animation()
        
        if self._animation_group:
            self._animation_group.setLoopCount(-1)  # Infinite loop
            self._animation_group.start()
    
    def _setup_pulse_animation(self) -> None:
        """Set up pulse animation."""
        # Opacity animation
        opacity_animation = QPropertyAnimation(self, b"animation_opacity")
        opacity_animation.setDuration(2000)
        opacity_animation.setStartValue(0.3)
        opacity_animation.setKeyValueAt(0.5, 1.0)
        opacity_animation.setEndValue(0.3)
        opacity_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        self._animation_group.addAnimation(opacity_animation)
    
    def _setup_wave_animation(self) -> None:
        """Set up wave animation."""
        # Position animation for wave effect
        position_animation = QPropertyAnimation(self, b"animation_position")
        position_animation.setDuration(2000)
        position_animation.setStartValue(0.0)
        position_animation.setEndValue(1.0)
        position_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        self._animation_group.addAnimation(position_animation)
    
    def _setup_shimmer_animation(self) -> None:
        """Set up shimmer animation (combines pulse and wave)."""
        # Opacity animation
        opacity_animation = QPropertyAnimation(self, b"animation_opacity")
        opacity_animation.setDuration(1500)
        opacity_animation.setStartValue(0.3)
        opacity_animation.setKeyValueAt(0.5, 0.8)
        opacity_animation.setEndValue(0.3)
        opacity_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        # Position animation
        position_animation = QPropertyAnimation(self, b"animation_position")
        position_animation.setDuration(1500)
        position_animation.setStartValue(-0.2)
        position_animation.setEndValue(1.2)
        position_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        self._animation_group.addAnimation(opacity_animation)
        self._animation_group.addAnimation(position_animation)
    
    @Property(float)
    def animation_opacity(self) -> float:
        """Get animation opacity."""
        return self._animation_opacity
    
    @animation_opacity.setter
    def animation_opacity(self, value: float) -> None:
        """Set animation opacity."""
        self._animation_opacity = value
        self.update()
    
    @Property(float)
    def animation_position(self) -> float:
        """Get animation position."""
        return self._animation_position
    
    @animation_position.setter
    def animation_position(self, value: float) -> None:
        """Set animation position."""
        self._animation_position = value
        self.update()
    
    def paintEvent(self, event: QPaintEvent) -> None:
        """Custom paint for animation effects."""
        super().paintEvent(event)
        
        if self._animation == SkeletonAnimation.NONE:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        
        if self._animation == SkeletonAnimation.SHIMMER:
            # Draw shimmer gradient overlay
            gradient = QLinearGradient(rect.topLeft(), rect.topRight())
            
            # Base color
            base_color = QColor(255, 255, 255, int(self._animation_opacity * 100))
            
            # Create shimmer effect
            pos = self._animation_position
            gradient.setColorAt(max(0.0, pos - 0.2), QColor(255, 255, 255, 0))
            gradient.setColorAt(pos, base_color)
            gradient.setColorAt(min(1.0, pos + 0.2), QColor(255, 255, 255, 0))
            
            painter.fillRect(rect, QBrush(gradient))
        
        elif self._animation == SkeletonAnimation.WAVE:
            # Draw wave effect
            wave_color = QColor(255, 255, 255, int(self._animation_position * 100))
            painter.fillRect(rect, wave_color)
        
        painter.end()
    
    def set_theme_manager(self, theme_manager: ThemeManager) -> None:
        """Set the theme manager for dynamic theming."""
        self._theme_manager = theme_manager
        if theme_manager:
            theme_manager.theme_changed.connect(self._on_theme_changed)
        self._apply_style()
    
    def _on_theme_changed(self, theme_name: str) -> None:
        """Handle theme changes."""
        self._apply_style()
    
    def stop_animation(self) -> None:
        """Stop the skeleton animation."""
        if self._animation_group:
            self._animation_group.stop()
    
    def start_animation(self) -> None:
        """Start the skeleton animation."""
        if self._animation_group:
            self._animation_group.start()


# Convenience factory functions
def create_skeleton_text(
    lines: int = 1,
    line_height: int = 20,
    parent: Optional[QWidget] = None
):
    """Create a text skeleton."""
    from .skeleton_loader import BaseSkeleton
    return BaseSkeleton(height=line_height * lines, parent=parent)


def create_skeleton_card(
    show_avatar: bool = False,
    content_lines: int = 3,
    parent: Optional[QWidget] = None
):
    """Create a card skeleton."""
    return BaseSkeleton(height=120, parent=parent)


def create_skeleton_table(
    rows: int = 5,
    columns: int = 4,
    parent: Optional[QWidget] = None
):
    """Create a table skeleton."""
    return BaseSkeleton(height=rows * 40, parent=parent)


def create_skeleton_list(
    items: int = 5,
    show_avatar: bool = False,
    parent: Optional[QWidget] = None
):
    """Create a list skeleton."""
    return BaseSkeleton(height=items * 60, parent=parent)
