"""
Base Button Component

Modern button component with shadcn/ui styling following the design system.
"""

from typing import Optional, Dict, Any
from enum import Enum

from PySide6.QtWidgets import QPushButton, QWidget
from PySide6.QtCore import Qt, Signal, Property
from PySide6.QtGui import QIcon

from utils.design_tokens import DesignTokens
from utils.theme_manager import ThemeManager
from utils.style_converter import convert_css_to_qt


class ButtonVariant(Enum):
    """Button style variants."""
    DEFAULT = "default"
    SECONDARY = "secondary"
    OUTLINE = "outline"
    GHOST = "ghost"
    DESTRUCTIVE = "destructive"


class ButtonSize(Enum):
    """Button size options."""
    SM = "sm"
    DEFAULT = "default"
    LG = "lg"
    ICON = "icon"


class BaseButton(QPushButton):
    """
    Modern button component with shadcn/ui styling.
    
    Supports multiple variants and sizes as defined in the design system.
    Includes hover states, focus management, and accessibility features.
    """
    
    # Signals
    variant_changed = Signal(str)
    size_changed = Signal(str)
    
    def __init__(
        self, 
        text: str = "",
        variant: ButtonVariant = ButtonVariant.DEFAULT,
        size: ButtonSize = ButtonSize.DEFAULT,
        icon: Optional[QIcon] = None,
        parent: Optional[QWidget] = None
    ):
        """
        Initialize the button.
        
        Args:
            text: Button text
            variant: Button style variant
            size: Button size
            icon: Optional button icon
            parent: Parent widget
        """
        super().__init__(text, parent)
        
        self._variant = variant
        self._size = size
        self._theme_manager: Optional[ThemeManager] = None
        
        if icon:
            self.setIcon(icon)
        
        self._setup_ui()
        self._apply_style()
    
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
            
        # Set accessible properties
        self.setAccessibleName(self.text() or "Button")
        self.setAccessibleDescription(f"{self._variant.value} {self._size.value} button")
    
    def _apply_style(self) -> None:
        """Apply the appropriate style based on variant and size."""
        tokens = DesignTokens()
        
        # Get size configuration
        size_config = tokens.BUTTON_SIZES.get(self._size.value, tokens.BUTTON_SIZES['default'])
        
        # Get theme colors
        color_vars = self._get_theme_colors()
        
        # Base styles common to all variants
        base_style = f"""
        QPushButton {{
            font-family: {tokens.get_font_string()};
            font-size: {size_config['font_size']}px;
            font-weight: {tokens.TYPOGRAPHY['font_medium']};
            border-radius: {tokens.BORDER_RADIUS['radius_default']}px;
            min-height: {size_config['height']}px;
        }}
        
        QPushButton:focus {{
            outline: {tokens.FOCUS_STYLES['ring_width']}px solid var(--ring);
            outline-offset: {tokens.FOCUS_STYLES['ring_offset']}px;
        }}
        
        QPushButton:disabled {{
            opacity: 0.5;
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
        
        # Combine styles and convert CSS variables to Qt values
        raw_style = base_style + variant_styles.get(self._variant, variant_styles[ButtonVariant.DEFAULT])
        qt_style = convert_css_to_qt(raw_style, color_vars)
        self.setStyleSheet(qt_style)
    
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
    def create_icon(
        icon: QIcon,
        variant: ButtonVariant = ButtonVariant.GHOST,
        parent: Optional[QWidget] = None
    ) -> 'BaseButton':
        """Create an icon-only button."""
        return BaseButton("", variant, ButtonSize.ICON, icon, parent) 