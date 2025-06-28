"""
Theme Manager for CellSorter Application

Manages theme switching between custom shadcn/ui inspired themes and qt-material themes.
Based on the design system specifications in docs/design/.
"""

import platform
from typing import Optional, Dict, Any
from pathlib import Path

try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QObject, Signal, QSettings
    from PySide6.QtGui import QPalette, QColor
except ImportError:
    # Fallback for development environment
    QApplication = object
    QObject = object
    Signal = lambda x: lambda: None
    QSettings = object
    QPalette = object
    QColor = object

from utils.logging_config import LoggerMixin
from utils.style_converter import convert_css_to_qt, get_shadcn_color_variables, get_shadcn_dark_color_variables, hsl_string_to_rgb


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
        # Force dark mode only
        self.current_theme = "dark"
        self.settings.setValue("theme", "dark")
        
        # Apply dark theme immediately
        self.apply_theme("dark")
        
    def apply_theme(self, theme_name: str) -> None:
        """
        Apply dark theme to the application (only dark mode supported).
        
        Args:
            theme_name: Theme name (forced to "dark")
        """
        # Force dark mode only
        theme_name = "dark"
        
        self.apply_custom_theme(theme_name)
            
        self.current_theme = theme_name
        self.settings.setValue("theme", theme_name)
        self.theme_changed.emit(theme_name)
        self.log_info(f"Applied dark theme (forced dark mode)")
    
    def apply_custom_theme(self, theme_name: str) -> None:
        """Apply custom shadcn/ui inspired theme."""
        try:
            colors = self.COLORS_LIGHT if theme_name == "light" else self.COLORS_DARK
            
            # Generate stylesheet
            stylesheet = self._generate_stylesheet(colors)
            
            # Log stylesheet length for debugging
            self.log_info(f"Generated stylesheet length: {len(stylesheet)} characters")
            
            # Apply to application
            self.app.setStyleSheet(stylesheet)
            
            self.log_info(f"Successfully applied custom theme: {theme_name}")
            
        except Exception as e:
            self.log_error(f"Failed to apply custom theme {theme_name}: {e}")
            # Try fallback
            try:
                colors = self.COLORS_LIGHT if theme_name == "light" else self.COLORS_DARK
                hex_colors = {}
                for key, hsl in colors.items():
                    qcolor = self._hsl_to_qcolor(hsl)
                    hex_colors[key] = qcolor.name()
                fallback_stylesheet = self._generate_fallback_stylesheet(hex_colors)
                self.app.setStyleSheet(fallback_stylesheet)
                self.log_info(f"Applied fallback stylesheet for theme: {theme_name}")
            except Exception as fallback_error:
                self.log_error(f"Even fallback failed: {fallback_error}")
                # Clear stylesheet to avoid parsing errors
                self.app.setStyleSheet("")
    
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
        """No-op: Only dark theme supported."""
        self.log_info("Theme toggle disabled - dark mode only")
        
    def get_current_theme(self) -> str:
        """Get the current theme name (always dark)."""
        return "dark"
    
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
        
        # For now, use the fallback stylesheet which is guaranteed to work
        # Later, we can implement a proper CSS parser when needed
        self.log_info("Using direct Qt stylesheet generation for compatibility")
        return self._generate_fallback_stylesheet(hex_colors)
    
    def _generate_fallback_stylesheet(self, hex_colors: Dict[str, str]) -> str:
        """Generate fallback stylesheet when CSS file is not available."""
        # Platform-specific font families
        if platform.system() == "Darwin":  # macOS
            font_family = '"SF Pro Text", "Helvetica Neue", system-ui, sans-serif'
        elif platform.system() == "Windows":
            font_family = '"Segoe UI", "Microsoft YaHei", system-ui, sans-serif'
        else:  # Linux and others
            font_family = '"Ubuntu", "Roboto", system-ui, sans-serif'
            
        return f"""
        /* CellSorter Fallback Stylesheet - Platform: {platform.system()} */
        QMainWindow {{
            background-color: {hex_colors.get('background', '#ffffff')};
            color: {hex_colors.get('foreground', '#000000')};
            font-family: {font_family};
        }}
        
        /* Menu Bar */
        QMenuBar {{
            background-color: {hex_colors.get('background', '#ffffff')};
            border-bottom: 1px solid {hex_colors.get('border', '#e5e5e5')};
            color: {hex_colors.get('foreground', '#000000')};
            font-weight: 500;
        }}
        
        QMenuBar::item {{
            background: transparent;
            padding: 8px 12px;
            border-radius: 4px;
        }}
        
        QMenuBar::item:selected {{
            background-color: {hex_colors.get('accent', '#f5f5f5')};
            color: {hex_colors.get('accent_foreground', '#000000')};
        }}
        
        /* Toolbar */
        QToolBar {{
            background-color: {hex_colors.get('background', '#ffffff')};
            border-bottom: 1px solid {hex_colors.get('border', '#e5e5e5')};
            spacing: 8px;
        }}
        
        QToolButton {{
            background-color: transparent;
            border: 1px solid transparent;
            border-radius: 4px;
            padding: 8px;
            min-width: 36px;
            min-height: 36px;
        }}
        
        QToolButton:hover {{
            background-color: {hex_colors.get('accent', '#f5f5f5')};
            border-color: {hex_colors.get('border', '#e5e5e5')};
        }}
        
        QToolButton:pressed {{
            background-color: {hex_colors.get('muted', '#f0f0f0')};
        }}
        
        /* Buttons */
        QPushButton {{
            background-color: {hex_colors.get('primary', '#1f2937')};
            color: {hex_colors.get('primary_foreground', '#ffffff')};
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            font-weight: 500;
            font-size: 14px;
            min-height: 40px;
        }}
        
        QPushButton:hover {{
            background-color: {hex_colors.get('primary', '#1f2937')};
            opacity: 0.9;
        }}
        
        QPushButton:pressed {{
            background-color: {hex_colors.get('primary', '#1f2937')};
            opacity: 0.8;
        }}
        
        QPushButton:disabled {{
            background-color: {hex_colors.get('muted', '#f0f0f0')};
            color: {hex_colors.get('muted_foreground', '#6b7280')};
        }}
        
        /* Input Fields */
        QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox {{
            background-color: transparent;
            border: 1px solid {hex_colors.get('border', '#e5e5e5')};
            border-radius: 4px;
            padding: 8px 12px;
            font-size: 14px;
            min-height: 40px;
        }}
        
        QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
            border-color: {hex_colors.get('ring', '#1f2937')};
            outline: 2px solid {hex_colors.get('ring', '#1f2937')};
            outline-offset: 2px;
        }}
        
        QLineEdit:disabled, QTextEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {{
            background-color: {hex_colors.get('muted', '#f0f0f0')};
            color: {hex_colors.get('muted_foreground', '#6b7280')};
            opacity: 0.5;
        }}
        
        /* Tables */
        QTableWidget {{
            background-color: {hex_colors.get('background', '#ffffff')};
            border: 1px solid {hex_colors.get('border', '#e5e5e5')};
            border-radius: 4px;
            gridline-color: {hex_colors.get('border', '#e5e5e5')};
            selection-background-color: {hex_colors.get('accent', '#f5f5f5')};
            selection-color: {hex_colors.get('accent_foreground', '#000000')};
        }}
        
        QHeaderView::section {{
            background-color: {hex_colors.get('muted', '#f0f0f0')};
            color: {hex_colors.get('muted_foreground', '#6b7280')};
            padding: 8px 12px;
            border: none;
            border-bottom: 1px solid {hex_colors.get('border', '#e5e5e5')};
            font-weight: 600;
        }}
        
        /* Status Bar */
        QStatusBar {{
            background-color: {hex_colors.get('muted', '#f0f0f0')};
            border-top: 1px solid {hex_colors.get('border', '#e5e5e5')};
            color: {hex_colors.get('muted_foreground', '#6b7280')};
            font-size: 12px;
        }}
        
        /* Cards and Frames */
        QFrame[role="card"] {{
            background-color: {hex_colors.get('card', '#ffffff')};
            color: {hex_colors.get('card_foreground', '#000000')};
            border: 1px solid {hex_colors.get('border', '#e5e5e5')};
            border-radius: 8px;
        }}
        
        /* Progress Bar */
        QProgressBar {{
            background-color: {hex_colors.get('secondary', '#f5f5f5')};
            border: none;
            border-radius: 4px;
            text-align: center;
            height: 8px;
        }}
        
        QProgressBar::chunk {{
            background-color: {hex_colors.get('primary', '#1f2937')};
            border-radius: 4px;
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
    
    def get_current_colors(self) -> Dict[str, str]:
        """
        Get current theme colors as hex values for Qt compatibility.
        
        Returns:
            Dictionary mapping variable names to hex color values
        """
        # Get HSL colors based on current theme
        if self.current_theme == "dark":
            hsl_colors = get_shadcn_dark_color_variables()
        else:
            hsl_colors = get_shadcn_color_variables()
        
        # Convert HSL to hex for Qt compatibility
        hex_colors = {}
        for var_name, hsl_value in hsl_colors.items():
            if isinstance(hsl_value, str):
                hex_colors[var_name] = hsl_string_to_rgb(hsl_value)
            else:
                hex_colors[var_name] = hsl_value
        
        return hex_colors