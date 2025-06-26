"""
Style Converter Utilities

Converts design system styles to Qt-compatible formats.
"""

import colorsys
import re
from typing import Dict, Tuple


def hsl_to_rgb(h: float, s: float, l: float) -> Tuple[int, int, int]:
    """
    Convert HSL color values to RGB.
    
    Args:
        h: Hue (0-360)
        s: Saturation (0-100)
        l: Lightness (0-100)
        
    Returns:
        Tuple of (r, g, b) values (0-255)
    """
    # Convert to 0-1 range
    h = h / 360
    s = s / 100
    l = l / 100
    
    # Convert to RGB
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    
    # Convert to 0-255 range
    return (int(r * 255), int(g * 255), int(b * 255))


def parse_hsl_string(hsl_string: str) -> Tuple[float, float, float]:
    """
    Parse HSL color string to values.
    
    Args:
        hsl_string: HSL string like "hsl(222.2, 84%, 4.9%)"
        
    Returns:
        Tuple of (h, s, l) values
    """
    # Extract values using regex
    match = re.match(r'hsl\(([\d.]+),?\s*([\d.]+)%,?\s*([\d.]+)%\)', hsl_string)
    if match:
        h = float(match.group(1))
        s = float(match.group(2))
        l = float(match.group(3))
        return (h, s, l)
    return (0, 0, 0)


def hsl_to_hex(hsl_string: str) -> str:
    """
    Convert HSL color string to hex color.
    
    Args:
        hsl_string: HSL string like "hsl(222.2, 84%, 4.9%)"
        
    Returns:
        Hex color string like "#0C0A09"
    """
    h, s, l = parse_hsl_string(hsl_string)
    r, g, b = hsl_to_rgb(h, s, l)
    return f"#{r:02x}{g:02x}{b:02x}"


def convert_css_to_qt(css_string: str, color_vars: Dict[str, str]) -> str:
    """
    Convert CSS with variables to Qt stylesheet with comprehensive compatibility.
    
    Args:
        css_string: CSS string with var() references
        color_vars: Dictionary mapping variable names to color values
        
    Returns:
        Qt-compatible stylesheet
    """
    # Replace CSS variables with actual values
    qt_style = css_string
    
    # First, replace var(--name) with actual color values
    for var_name, var_value in color_vars.items():
        css_var_name = var_name.replace('_', '-')
        
        # Convert HSL to hex if needed
        if var_value.startswith('hsl('):
            var_value = hsl_to_hex(var_value)
        
        # Replace var(--name) format
        qt_style = qt_style.replace(f'var(--{css_var_name})', var_value)
    
    # Also replace CSS custom properties declarations (--name: value;)
    for var_name, var_value in color_vars.items():
        css_var_name = var_name.replace('_', '-')
        if var_value.startswith('hsl('):
            var_value = hsl_to_hex(var_value)
        # Remove CSS variable declarations
        qt_style = re.sub(f'--{css_var_name}:[^;]+;', '', qt_style)
    
    # Remove CSS-specific syntax that Qt doesn't support
    qt_style = qt_style.replace(':root', '')
    qt_style = qt_style.replace('[data-theme="dark"]', '')
    qt_style = qt_style.replace('* {', 'QWidget {')
    qt_style = qt_style.replace('body {', 'QMainWindow {')
    
    # Remove @-rules that Qt doesn't support
    qt_style = re.sub(r'@keyframes[^{]*{[^{}]*(?:{[^{}]*}[^{}]*)*}', '', qt_style)
    qt_style = re.sub(r'@media[^{]*{[^{}]*(?:{[^{}]*}[^{}]*)*}', '', qt_style)
    qt_style = re.sub(r'@import[^;]*;', '', qt_style)
    
    # Remove unsupported properties
    qt_style = re.sub(r'transition:[^;]+;', '', qt_style)
    qt_style = re.sub(r'animation:[^;]+;', '', qt_style)
    qt_style = re.sub(r'transform:[^;]+;', '', qt_style)
    qt_style = re.sub(r'backdrop-filter:[^;]+;', '', qt_style)
    qt_style = re.sub(r'cursor:[^;]+;', '', qt_style)
    qt_style = re.sub(r'z-index:[^;]+;', '', qt_style)
    qt_style = re.sub(r'position:[^;]+;', '', qt_style)
    qt_style = re.sub(r'overflow:[^;]+;', '', qt_style)
    qt_style = re.sub(r'clip:[^;]+;', '', qt_style)
    qt_style = re.sub(r'white-space:[^;]+;', '', qt_style)
    qt_style = re.sub(r'-webkit-[^:]+:[^;]+;', '', qt_style)
    qt_style = re.sub(r'-moz-[^:]+:[^;]+;', '', qt_style)
    
    # Handle box-shadow (Qt has limited support)
    qt_style = re.sub(r'box-shadow:\s*0\s+[^;]+;', '', qt_style)
    
    # Remove calc() functions
    qt_style = re.sub(r'calc\([^)]+\)', '8px', qt_style)
    
    # Fix pseudo-selectors for Qt
    qt_style = qt_style.replace(':!disabled', ':enabled')
    qt_style = qt_style.replace(':focus-visible', ':focus')
    qt_style = re.sub(r':not\([^)]+\)', '', qt_style)
    
    # Convert opacity values in colors
    qt_style = re.sub(r'hsl\([^)]+\)\s*/\s*[\d.]+', lambda m: m.group(0).split('/')[0], qt_style)
    qt_style = re.sub(r'rgb\([^)]+\)\s*/\s*[\d.]+', lambda m: m.group(0).split('/')[0], qt_style)
    
    # Remove utility classes that Qt doesn't use
    qt_style = re.sub(r'\.sr-only\s*{[^}]*}', '', qt_style)
    qt_style = re.sub(r'\.text-[^{]*{[^}]*}', '', qt_style)
    qt_style = re.sub(r'\.font-[^{]*{[^}]*}', '', qt_style)
    qt_style = re.sub(r'\.p-[^{]*{[^}]*}', '', qt_style)
    qt_style = re.sub(r'\.m-[^{]*{[^}]*}', '', qt_style)
    qt_style = re.sub(r'\.rounded[^{]*{[^}]*}', '', qt_style)
    qt_style = re.sub(r'\.shadow[^{]*{[^}]*}', '', qt_style)
    
    # Clean up empty rules and extra whitespace
    qt_style = re.sub(r'{[\s]*}', '', qt_style)
    qt_style = re.sub(r'\n\s*\n+', '\n\n', qt_style)
    qt_style = re.sub(r'/\*.*?\*/', '', qt_style, flags=re.DOTALL)
    
    return qt_style


def generate_qt_palette_stylesheet(colors: Dict[str, str]) -> str:
    """
    Generate a basic Qt stylesheet from color palette.
    
    Args:
        colors: Dictionary of color definitions
        
    Returns:
        Qt stylesheet string
    """
    # Convert colors to hex
    hex_colors = {}
    for name, value in colors.items():
        if value.startswith('hsl('):
            hex_colors[name] = hsl_to_hex(value)
        else:
            hex_colors[name] = value
    
    # Generate stylesheet
    return f"""
    /* Generated Qt Stylesheet */
    QWidget {{
        background-color: {hex_colors.get('background', '#ffffff')};
        color: {hex_colors.get('foreground', '#000000')};
    }}
    
    QPushButton {{
        background-color: {hex_colors.get('primary', '#0000ff')};
        color: {hex_colors.get('primary_foreground', '#ffffff')};
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        font-weight: 500;
    }}
    
    QPushButton:hover {{
        background-color: {hex_colors.get('primary', '#0000ff')};
    }}
    
    QPushButton:pressed {{
        background-color: {hex_colors.get('primary', '#0000ff')};
    }}
    
    QPushButton:disabled {{
        background-color: {hex_colors.get('muted', '#cccccc')};
        color: {hex_colors.get('muted_foreground', '#666666')};
    }}
    
    QLineEdit {{
        background-color: transparent;
        border: 1px solid {hex_colors.get('border', '#cccccc')};
        border-radius: 4px;
        padding: 8px 12px;
    }}
    
    QLineEdit:focus {{
        border-color: {hex_colors.get('ring', '#0000ff')};
    }}
    
    QFrame {{
        background-color: {hex_colors.get('card', '#ffffff')};
        color: {hex_colors.get('card_foreground', '#000000')};
    }}
    
    QMenuBar {{
        background-color: {hex_colors.get('background', '#ffffff')};
        border-bottom: 1px solid {hex_colors.get('border', '#cccccc')};
    }}
    
    QMenuBar::item:selected {{
        background-color: {hex_colors.get('accent', '#f0f0f0')};
    }}
    
    QToolBar {{
        background-color: {hex_colors.get('background', '#ffffff')};
        border-bottom: 1px solid {hex_colors.get('border', '#cccccc')};
    }}
    
    QStatusBar {{
        background-color: {hex_colors.get('muted', '#f0f0f0')};
        border-top: 1px solid {hex_colors.get('border', '#cccccc')};
    }}
    
    QTableWidget {{
        background-color: {hex_colors.get('background', '#ffffff')};
        gridline-color: {hex_colors.get('border', '#cccccc')};
        selection-background-color: {hex_colors.get('accent', '#f0f0f0')};
        selection-color: {hex_colors.get('accent_foreground', '#000000')};
    }}
    
    QHeaderView::section {{
        background-color: {hex_colors.get('muted', '#f0f0f0')};
        color: {hex_colors.get('muted_foreground', '#666666')};
        border: none;
        border-bottom: 1px solid {hex_colors.get('border', '#cccccc')};
        padding: 8px;
    }}
    """ 