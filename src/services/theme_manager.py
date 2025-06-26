"""
Theme Manager for CellSorter Application

Manages theme switching between custom shadcn/ui inspired themes and qt-material themes.
Based on the design system specifications in docs/design/.
"""

from typing import Optional, Dict, Any
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal, QSettings
from PySide6.QtGui import QPalette, QColor

from utils.logging_config import LoggerMixin


class ThemeManager(QObject, LoggerMixin):
    """
    Manages theme switching between custom and qt-material themes.
    
    Based on the design specifications in docs/design/DESIGN_SYSTEM.md
    """
    
    # Signals
    theme_changed = Signal(str)  # theme_name
    
    # Light Theme Colors (shadcn/ui inspired) - HSL values
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
    
    # Dark Theme Colors
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
    
    # Scientific/Medical Colors
    MEDICAL_COLORS = {
        'cancer_primary': 'hsl(0, 84.2%, 60.2%)',
        'normal_tissue': 'hsl(142.1, 76.2%, 36.3%)',
        'stroma': 'hsl(221.2, 83.2%, 53.3%)',
        'immune_cells': 'hsl(262.1, 83.3%, 57.8%)',
        'blood_vessels': 'hsl(24.6, 95%, 53.1%)',
        'necrosis': 'hsl(47.9, 95.8%, 53.1%)',
    }
    
    # Qt-Material theme list
    QT_MATERIAL_THEMES = [
        'dark_amber.xml', 'dark_blue.xml', 'dark_cyan.xml',
        'dark_lightgreen.xml', 'dark_pink.xml', 'dark_purple.xml',
        'dark_red.xml', 'dark_teal.xml', 'dark_yellow.xml',
        'light_amber.xml', 'light_blue.xml', 'light_cyan.xml',
        'light_lightgreen.xml', 'light_pink.xml', 'light_purple.xml',
        'light_red.xml', 'light_teal.xml', 'light_yellow.xml'
    ]
    
    def __init__(self, app: QApplication, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.app = app
        self.settings = QSettings("CellSorter", "Theme")
        self.current_theme = self.settings.value("theme", "light")
        
    def apply_theme(self, theme_name: str) -> None:
        """
        Apply a theme to the application.
        
        Args:
            theme_name: Name of the theme ("light", "dark", or qt-material theme name)
        """
        if theme_name in ["light", "dark"]:
            self.apply_custom_theme(theme_name)
        elif theme_name + ".xml" in self.QT_MATERIAL_THEMES:
            self.apply_qt_material_theme(theme_name)
        else:
            self.log_error(f"Unknown theme: {theme_name}")
            return
            
        self.current_theme = theme_name
        self.settings.setValue("theme", theme_name)
        self.theme_changed.emit(theme_name)
        self.log_info(f"Applied theme: {theme_name}")
    
    def apply_custom_theme(self, theme_name: str) -> None:
        """Apply custom shadcn/ui inspired theme."""
        colors = self.COLORS_LIGHT if theme_name == "light" else self.COLORS_DARK
        
        # Generate stylesheet
        stylesheet = self._generate_stylesheet(colors)
        self.app.setStyleSheet(stylesheet)
        
    def apply_qt_material_theme(self, theme_name: str) -> None:
        """Apply qt-material theme."""
        try:
            from qt_material import apply_stylesheet
            apply_stylesheet(self.app, theme=theme_name + ".xml")
            self.log_info(f"Applied qt-material theme: {theme_name}")
        except ImportError:
            self.log_error("qt-material package not installed")
            # Fall back to custom theme
            self.apply_custom_theme("light" if "light" in theme_name else "dark")
    
    def toggle_theme(self) -> None:
        """Toggle between light and dark themes."""
        if self.current_theme == "light":
            self.apply_theme("dark")
        else:
            self.apply_theme("light")
    
    def get_current_theme(self) -> str:
        """Get the current theme name."""
        return self.current_theme
    
    def _hsl_to_qcolor(self, hsl_string: str) -> QColor:
        """Convert HSL string to QColor."""
        # Parse HSL string: "hsl(222.2, 84%, 4.9%)"
        hsl_string = hsl_string.strip()
        if hsl_string.startswith('hsl(') and hsl_string.endswith(')'):
            values = hsl_string[4:-1].split(',')
            if len(values) == 3:
                h = float(values[0].strip())
                s = float(values[1].strip().rstrip('%')) / 100.0
                l = float(values[2].strip().rstrip('%')) / 100.0
                color = QColor()
                color.setHslF(h / 360.0, s, l)
                return color
        return QColor(0, 0, 0)
    
    def _generate_stylesheet(self, colors: Dict[str, str]) -> str:
        """Generate Qt stylesheet from color dictionary."""
        # Convert HSL colors to hex for Qt
        hex_colors = {}
        for key, hsl in colors.items():
            qcolor = self._hsl_to_qcolor(hsl)
            hex_colors[key] = qcolor.name()
        
        # Load the CSS template from design specs
        from pathlib import Path
        css_file = Path(__file__).parent.parent.parent / "docs" / "design" / "style.css"
        
        if css_file.exists():
            with open(css_file, 'r') as f:
                stylesheet = f.read()
            
            # Replace CSS variables with actual colors
            for key, hex_color in hex_colors.items():
                stylesheet = stylesheet.replace(f'var(--{key.replace("_", "-")})', hex_color)
            
            return stylesheet
        else:
            # Fallback minimal stylesheet
            return f"""
            QMainWindow {{
                background-color: {hex_colors['background']};
                color: {hex_colors['foreground']};
            }}
            
            QPushButton {{
                background-color: {hex_colors['primary']};
                color: {hex_colors['primary_foreground']};
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 500;
            }}
            
            QPushButton:hover {{
                background-color: {hex_colors['primary']};
                opacity: 0.9;
            }}
            
            QLineEdit, QTextEdit {{
                background-color: transparent;
                border: 1px solid {hex_colors['border']};
                border-radius: 4px;
                padding: 8px 12px;
            }}
            
            QLineEdit:focus, QTextEdit:focus {{
                border-color: {hex_colors['ring']};
            }}
            """
    
    def get_color(self, color_name: str) -> str:
        """
        Get a color value for the current theme.
        
        Args:
            color_name: Name of the color (e.g., 'primary', 'background')
            
        Returns:
            Color value as hex string
        """
        colors = self.COLORS_LIGHT if self.current_theme == "light" else self.COLORS_DARK
        
        if color_name in colors:
            return self._hsl_to_qcolor(colors[color_name]).name()
        elif color_name in self.MEDICAL_COLORS:
            return self._hsl_to_qcolor(self.MEDICAL_COLORS[color_name]).name()
        else:
            return "#000000"  # Default to black
    
    def get_medical_color(self, tissue_type: str) -> str:
        """Get color for specific tissue type."""
        color_map = {
            'cancer': 'cancer_primary',
            'normal': 'normal_tissue',
            'stroma': 'stroma',
            'immune': 'immune_cells',
            'vessels': 'blood_vessels',
            'necrosis': 'necrosis'
        }
        
        color_key = color_map.get(tissue_type.lower(), 'primary')
        return self.get_color(color_key)