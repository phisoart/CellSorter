"""
Theme Manager for CellSorter

Manages theme switching between custom shadcn/ui inspired themes and qt-material themes.
Based on the design system specification in docs/design/DESIGN_SYSTEM.md
"""

from typing import Dict, Optional, Any
from pathlib import Path
import json

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal, QSettings
from PySide6.QtGui import QPalette, QColor

from utils.logging_config import LoggerMixin
from utils.style_converter import generate_qt_palette_stylesheet


class ThemeManager(QObject, LoggerMixin):
    """
    Manages theme switching between custom and qt-material themes.
    
    Implements the theme system defined in the design specification,
    supporting both shadcn/ui inspired custom themes and qt-material themes.
    """
    
    # Signals
    theme_changed = Signal(str)  # Theme name
    
    # Theme constants
    THEME_LIGHT = "light"
    THEME_DARK = "dark"
    THEME_QT_MATERIAL_PREFIX = "qt_material_"
    
    # Qt-Material theme names
    QT_MATERIAL_THEMES = [
        'dark_amber.xml', 'dark_blue.xml', 'dark_cyan.xml',
        'dark_lightgreen.xml', 'dark_pink.xml', 'dark_purple.xml',
        'dark_red.xml', 'dark_teal.xml', 'dark_yellow.xml',
        'light_amber.xml', 'light_blue.xml', 'light_cyan.xml',
        'light_lightgreen.xml', 'light_pink.xml', 'light_purple.xml',
        'light_red.xml', 'light_teal.xml', 'light_yellow.xml'
    ]
    
    # Color definitions (shadcn/ui inspired)
    COLORS_LIGHT = {
        'background': 'hsl(0, 0%, 100%)',
        'foreground': 'hsl(222.2, 84%, 4.9%)',
        'card': 'hsl(0, 0%, 100%)',
        'card_foreground': 'hsl(222.2, 84%, 4.9%)',
        'popover': 'hsl(0, 0%, 100%)',
        'popover_foreground': 'hsl(222.2, 84%, 4.9%)',
        'primary': 'hsl(222.2, 47.4%, 11.2%)',
        'primary_foreground': 'hsl(210, 40%, 98%)',
        'secondary': 'hsl(210, 40%, 96%)',
        'secondary_foreground': 'hsl(222.2, 84%, 4.9%)',
        'muted': 'hsl(210, 40%, 96%)',
        'muted_foreground': 'hsl(215.4, 16.3%, 46.9%)',
        'accent': 'hsl(210, 40%, 96%)',
        'accent_foreground': 'hsl(222.2, 84%, 4.9%)',
        'destructive': 'hsl(0, 84.2%, 60.2%)',
        'destructive_foreground': 'hsl(210, 40%, 98%)',
        'border': 'hsl(214.3, 31.8%, 91.4%)',
        'input': 'hsl(214.3, 31.8%, 91.4%)',
        'ring': 'hsl(222.2, 84%, 4.9%)',
    }
    
    COLORS_DARK = {
        'background': 'hsl(222.2, 84%, 4.9%)',
        'foreground': 'hsl(210, 40%, 98%)',
        'card': 'hsl(222.2, 84%, 4.9%)',
        'card_foreground': 'hsl(210, 40%, 98%)',
        'popover': 'hsl(222.2, 84%, 4.9%)',
        'popover_foreground': 'hsl(210, 40%, 98%)',
        'primary': 'hsl(210, 40%, 98%)',
        'primary_foreground': 'hsl(222.2, 47.4%, 11.2%)',
        'secondary': 'hsl(217.2, 32.6%, 17.5%)',
        'secondary_foreground': 'hsl(210, 40%, 98%)',
        'muted': 'hsl(217.2, 32.6%, 17.5%)',
        'muted_foreground': 'hsl(215, 20.2%, 65.1%)',
        'accent': 'hsl(217.2, 32.6%, 17.5%)',
        'accent_foreground': 'hsl(210, 40%, 98%)',
        'destructive': 'hsl(0, 62.8%, 30.6%)',
        'destructive_foreground': 'hsl(210, 40%, 98%)',
        'border': 'hsl(217.2, 32.6%, 17.5%)',
        'input': 'hsl(217.2, 32.6%, 17.5%)',
        'ring': 'hsl(212.7, 26.8%, 83.9%)',
    }
    
    # Medical/Scientific colors
    MEDICAL_COLORS = {
        'cancer_primary': 'hsl(0, 84.2%, 60.2%)',      # Red
        'normal_tissue': 'hsl(142.1, 76.2%, 36.3%)',   # Green
        'stroma': 'hsl(221.2, 83.2%, 53.3%)',          # Blue
        'immune_cells': 'hsl(262.1, 83.3%, 57.8%)',    # Purple
        'blood_vessels': 'hsl(24.6, 95%, 53.1%)',      # Orange
        'necrosis': 'hsl(47.9, 95.8%, 53.1%)',         # Yellow
    }
    
    def __init__(self, app: QApplication, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.app = app
        self.settings = QSettings("CellSorter", "ThemeManager")
        self.current_theme = self.settings.value("theme", self.THEME_LIGHT)
        self._style_sheet_cache: Dict[str, str] = {}
        
        self.log_info(f"ThemeManager initialized with theme: {self.current_theme}")
    
    def apply_theme(self, theme_name: str) -> None:
        """
        Apply the specified theme to the application.
        
        Args:
            theme_name: Name of the theme to apply
        """
        if theme_name.startswith(self.THEME_QT_MATERIAL_PREFIX):
            # Apply qt-material theme
            material_theme = theme_name.replace(self.THEME_QT_MATERIAL_PREFIX, "")
            self.apply_qt_material_theme(material_theme)
        else:
            # Apply custom shadcn/ui inspired theme
            self.apply_custom_theme(theme_name)
        
        self.current_theme = theme_name
        self.settings.setValue("theme", theme_name)
        self.theme_changed.emit(theme_name)
        self.log_info(f"Theme changed to: {theme_name}")
    
    def apply_custom_theme(self, theme_name: str) -> None:
        """
        Apply custom shadcn/ui inspired theme.
        
        Args:
            theme_name: Either "light" or "dark"
        """
        colors = self.COLORS_LIGHT if theme_name == self.THEME_LIGHT else self.COLORS_DARK
        
        # Generate stylesheet
        stylesheet = self._generate_custom_stylesheet(colors)
        
        # Apply to application
        self.app.setStyleSheet(stylesheet)
        
        # Update application palette
        self._update_palette(colors)
    
    def apply_qt_material_theme(self, theme_name: str) -> None:
        """
        Apply qt-material theme.
        
        Args:
            theme_name: Name of the qt-material theme
        """
        try:
            from qt_material import apply_stylesheet
            apply_stylesheet(self.app, theme=theme_name)
            self.log_info(f"Applied qt-material theme: {theme_name}")
        except ImportError:
            self.log_error("qt-material package not installed")
            # Fallback to custom theme
            self.apply_custom_theme(self.THEME_LIGHT)
    
    def toggle_theme(self) -> None:
        """Toggle between light and dark themes."""
        if self.current_theme == self.THEME_LIGHT:
            self.apply_theme(self.THEME_DARK)
        elif self.current_theme == self.THEME_DARK:
            self.apply_theme(self.THEME_LIGHT)
        else:
            # If using qt-material theme, switch to custom light theme
            self.apply_theme(self.THEME_LIGHT)
    
    def get_current_theme(self) -> str:
        """Get the name of the current theme."""
        return self.current_theme
    
    def get_available_themes(self) -> list:
        """Get list of all available themes."""
        custom_themes = [self.THEME_LIGHT, self.THEME_DARK]
        qt_material_themes = [
            f"{self.THEME_QT_MATERIAL_PREFIX}{theme}" 
            for theme in self.QT_MATERIAL_THEMES
        ]
        return custom_themes + qt_material_themes
    
    def get_color(self, color_name: str) -> str:
        """
        Get a color value from the current theme.
        
        Args:
            color_name: Name of the color to retrieve
            
        Returns:
            Color value as string
        """
        if self.current_theme == self.THEME_LIGHT:
            colors = self.COLORS_LIGHT
        elif self.current_theme == self.THEME_DARK:
            colors = self.COLORS_DARK
        else:
            # For qt-material themes, return a default
            colors = self.COLORS_LIGHT
        
        # Check medical colors first
        if color_name in self.MEDICAL_COLORS:
            return self.MEDICAL_COLORS[color_name]
        
        return colors.get(color_name, "#000000")
    
    def _generate_custom_stylesheet(self, colors: Dict[str, str]) -> str:
        """
        Generate custom stylesheet based on color definitions.
        
        Args:
            colors: Dictionary of color definitions
            
        Returns:
            Generated stylesheet
        """
        # Use the style converter to generate Qt-compatible stylesheet
        return generate_qt_palette_stylesheet(colors)
    
    def _update_palette(self, colors: Dict[str, str]) -> None:
        """
        Update application palette based on colors.
        
        Args:
            colors: Dictionary of color definitions
        """
        palette = QPalette()
        
        # Helper to convert HSL to QColor
        def hsl_to_qcolor(hsl_str: str) -> QColor:
            """Convert HSL string to QColor."""
            # Parse HSL values
            if hsl_str.startswith('hsl('):
                values = hsl_str[4:-1].split(',')
                if len(values) == 3:
                    h = float(values[0].strip())
                    s = float(values[1].strip().rstrip('%'))
                    l = float(values[2].strip().rstrip('%'))
                    color = QColor()
                    color.setHslF(h / 360, s / 100, l / 100)
                    return color
            return QColor(hsl_str)
        
        # Set palette colors
        palette.setColor(QPalette.Window, hsl_to_qcolor(colors['background']))
        palette.setColor(QPalette.WindowText, hsl_to_qcolor(colors['foreground']))
        palette.setColor(QPalette.Base, hsl_to_qcolor(colors['card']))
        palette.setColor(QPalette.AlternateBase, hsl_to_qcolor(colors['muted']))
        palette.setColor(QPalette.Text, hsl_to_qcolor(colors['card_foreground']))
        palette.setColor(QPalette.Button, hsl_to_qcolor(colors['secondary']))
        palette.setColor(QPalette.ButtonText, hsl_to_qcolor(colors['secondary_foreground']))
        palette.setColor(QPalette.Highlight, hsl_to_qcolor(colors['primary']))
        palette.setColor(QPalette.HighlightedText, hsl_to_qcolor(colors['primary_foreground']))
        
        self.app.setPalette(palette) 