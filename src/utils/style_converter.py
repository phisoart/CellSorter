"""
Style Converter Utility

Converts CSS with custom properties to Qt stylesheet format.
Handles shadcn/ui CSS variables and HSL color conversion.
"""

import re
from typing import Dict, Any, Optional, Tuple
from pathlib import Path


def hsl_to_rgb(h: float, s: float, l: float) -> Tuple[int, int, int]:
    """
    Convert HSL to RGB values.
    
    Args:
        h: Hue (0-360)
        s: Saturation (0-1)
        l: Lightness (0-1)
        
    Returns:
        RGB tuple (0-255 each)
    """
    h = h / 360.0
    
    if s == 0:
        r = g = b = l
    else:
        def hue_to_rgb(p, q, t):
            if t < 0: t += 1
            if t > 1: t -= 1
            if t < 1/6: return p + (q - p) * 6 * t
            if t < 1/2: return q
            if t < 2/3: return p + (q - p) * (2/3 - t) * 6
            return p
        
        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        
        r = hue_to_rgb(p, q, h + 1/3)
        g = hue_to_rgb(p, q, h)
        b = hue_to_rgb(p, q, h - 1/3)
    
    return int(r * 255), int(g * 255), int(b * 255)


def hsl_string_to_rgb(hsl_string: str) -> str:
    """
    Convert HSL string to RGB hex color.
    
    Args:
        hsl_string: HSL values like "222.2 84% 4.9%" or "hsl(222.2, 84%, 4.9%)"
        
    Returns:
        Hex color string like "#1a1a1a"
    """
    # Remove hsl() wrapper if present
    hsl_string = hsl_string.strip()
    if hsl_string.startswith('hsl(') and hsl_string.endswith(')'):
        hsl_string = hsl_string[4:-1]
    
    # Parse values - handle both comma and space separated
    if ',' in hsl_string:
        parts = [p.strip() for p in hsl_string.split(',')]
    else:
        parts = hsl_string.split()
    
    if len(parts) != 3:
        return "#000000"  # Fallback
    
    try:
        h = float(parts[0])
        s = float(parts[1].rstrip('%')) / 100.0
        l = float(parts[2].rstrip('%')) / 100.0
        
        r, g, b = hsl_to_rgb(h, s, l)
        return f"#{r:02x}{g:02x}{b:02x}"
    except (ValueError, IndexError):
        return "#000000"  # Fallback


def get_shadcn_color_variables() -> Dict[str, str]:
    """
    Get shadcn/ui color variables in HSL format.
    
    Returns:
        Dictionary mapping CSS variable names to HSL values
    """
    # Light theme colors (default)
    return {
        'background': '0 0% 100%',
        'foreground': '222.2 84% 4.9%',
        'card': '0 0% 100%',
        'card-foreground': '222.2 84% 4.9%',
        'popover': '0 0% 100%',
        'popover-foreground': '222.2 84% 4.9%',
        'primary': '222.2 47.4% 11.2%',
        'primary-foreground': '210 40% 98%',
        'secondary': '210 40% 96%',
        'secondary-foreground': '222.2 84% 4.9%',
        'muted': '210 40% 96%',
        'muted-foreground': '215.4 16.3% 46.9%',
        'accent': '210 40% 96%',
        'accent-foreground': '222.2 84% 4.9%',
        'destructive': '0 84.2% 60.2%',
        'destructive-foreground': '210 40% 98%',
        'success': '142.1 76.2% 36.3%',
        'success-foreground': '355.7 100% 97.3%',
        'warning': '32.5 94.6% 43.7%',
        'warning-foreground': '220.9 39.3% 11%',
        'info': '221.2 83.2% 53.3%',
        'info-foreground': '210 40% 98%',
        'border': '214.3 31.8% 91.4%',
        'input': '214.3 31.8% 91.4%',
        'ring': '222.2 84% 4.9%',
        'chart-1': '12 76% 61%',
        'chart-2': '173 58% 39%',
        'chart-3': '197 37% 24%',
        'chart-4': '43 74% 66%',
        'chart-5': '27 87% 67%',
        'cancer-primary': '0 84.2% 60.2%',
        'normal-tissue': '142.1 76.2% 36.3%',
        'stroma': '221.2 83.2% 53.3%',
        'immune-cells': '262.1 83.3% 57.8%',
        'blood-vessels': '24.6 95% 53.1%',
        'necrosis': '47.9 95.8% 53.1%',
    }


def get_shadcn_dark_color_variables() -> Dict[str, str]:
    """
    Get shadcn/ui dark theme color variables in HSL format.
    
    Returns:
        Dictionary mapping CSS variable names to HSL values
    """
    return {
        'background': '222.2 84% 4.9%',
        'foreground': '210 40% 98%',
        'card': '222.2 84% 4.9%',
        'card-foreground': '210 40% 98%',
        'popover': '222.2 84% 4.9%',
        'popover-foreground': '210 40% 98%',
        'primary': '210 40% 98%',
        'primary-foreground': '222.2 47.4% 11.2%',
        'secondary': '217.2 32.6% 17.5%',
        'secondary-foreground': '210 40% 98%',
        'muted': '217.2 32.6% 17.5%',
        'muted-foreground': '215 20.2% 65.1%',
        'accent': '217.2 32.6% 17.5%',
        'accent-foreground': '210 40% 98%',
        'destructive': '0 62.8% 30.6%',
        'destructive-foreground': '210 40% 98%',
        'success': '142.1 70.6% 45.3%',
        'success-foreground': '144.9 80.4% 10%',
        'warning': '35.5 91.7% 32.9%',
        'warning-foreground': '48 100% 96.1%',
        'info': '213.3 93.9% 67.8%',
        'info-foreground': '215.4 16.3% 46.9%',
        'border': '217.2 32.6% 17.5%',
        'input': '217.2 32.6% 17.5%',
        'ring': '212.7 26.8% 83.9%',
        'chart-1': '220 70% 50%',
        'chart-2': '160 60% 45%',
        'chart-3': '30 80% 55%',
        'chart-4': '280 65% 60%',
        'chart-5': '340 75% 55%',
        'cancer-primary': '0 84.2% 60.2%',
        'normal-tissue': '142.1 76.2% 36.3%',
        'stroma': '221.2 83.2% 53.3%',
        'immune-cells': '262.1 83.3% 57.8%',
        'blood-vessels': '24.6 95% 53.1%',
        'necrosis': '47.9 95.8% 53.1%',
    }


def convert_css_to_qt(css_string: str, color_vars: Optional[Dict[str, str]] = None, is_dark_theme: bool = False) -> str:
    """
    Convert CSS with variables to Qt stylesheet with comprehensive compatibility.
    
    Args:
        css_string: CSS string with var() references
        color_vars: Dictionary mapping variable names to color values (optional)
        is_dark_theme: Whether to use dark theme colors
        
    Returns:
        Qt-compatible stylesheet
    """
    # Use default shadcn/ui colors if not provided
    if color_vars is None:
        color_vars = get_shadcn_dark_color_variables() if is_dark_theme else get_shadcn_color_variables()
    
    # Convert HSL color variables to hex
    hex_color_vars = {}
    for var_name, hsl_value in color_vars.items():
        if isinstance(hsl_value, str) and (
            hsl_value.startswith('hsl(') or 
            re.match(r'^\d+\.?\d*\s+\d+\.?\d*%\s+\d+\.?\d*%$', hsl_value.strip())
        ):
            hex_color_vars[var_name] = hsl_string_to_rgb(hsl_value)
        else:
            # Already hex or other format
            hex_color_vars[var_name] = hsl_value
    
    # Replace CSS variables with actual values
    qt_style = css_string
    
    # Handle var() references with fallbacks
    var_pattern = r'var\((--[\w-]+)(?:,\s*([^)]+))?\)'
    
    def replace_var(match):
        var_name = match.group(1)[2:]  # Remove --
        fallback = match.group(2) if match.group(2) else None
        
        # Look for the variable in our color map
        if var_name in hex_color_vars:
            return hex_color_vars[var_name]
        elif var_name.replace('-', '_') in hex_color_vars:
            return hex_color_vars[var_name.replace('-', '_')]
        elif fallback:
            return fallback.strip()
        else:
            # Try common fallbacks
            fallback_colors = {
                'background': '#ffffff' if not is_dark_theme else '#0f172a',
                'foreground': '#0f172a' if not is_dark_theme else '#f8fafc',
                'primary': '#0f172a' if not is_dark_theme else '#f8fafc',
                'secondary': '#f1f5f9' if not is_dark_theme else '#1e293b',
                'muted': '#f1f5f9' if not is_dark_theme else '#1e293b',
                'border': '#e2e8f0' if not is_dark_theme else '#1e293b',
            }
            return fallback_colors.get(var_name, '#000000')
    
    qt_style = re.sub(var_pattern, replace_var, qt_style)
    
    # Convert modern CSS properties to Qt equivalents
    property_conversions = {
        'backdrop-filter': '',  # Remove - not supported
        'mask': '',  # Remove - not supported
        'clip-path': '',  # Remove - not supported
        'filter': '',  # Remove - limited support
        'transform': '',  # Remove - limited support
        'transition': '',  # Remove - use QPropertyAnimation instead
        'animation': '',  # Remove - use QPropertyAnimation instead
        'box-shadow': '',  # Convert to Qt shadow (limited)
        'text-shadow': '',  # Remove - not supported
        'opacity': 'background-color',  # Qt handles opacity differently
        'z-index': '',  # Remove - use widget stacking
    }
    
    for css_prop, qt_replacement in property_conversions.items():
        if qt_replacement == '':
            # Remove the property entirely
            pattern = rf'{css_prop}\s*:[^;]*;?'
            qt_style = re.sub(pattern, '', qt_style, flags=re.IGNORECASE)
        else:
            # Replace with Qt equivalent
            pattern = rf'{css_prop}(\s*:\s*[^;]*;?)'
            qt_style = re.sub(pattern, rf'{qt_replacement}\1', qt_style, flags=re.IGNORECASE)
    
    # Handle text overflow properties specifically for Qt
    text_overflow_conversions = {
        'text-overflow: ellipsis': '/* text-overflow: ellipsis handled by Qt widget */',
        'white-space: nowrap': '/* white-space: nowrap handled by Qt widget */',
        'overflow: hidden': '/* overflow: hidden handled by Qt widget */',
        'word-wrap: break-word': '/* word-wrap handled by Qt widget */',
        'word-break: break-all': '/* word-break handled by Qt widget */',
        'line-clamp': '/* line-clamp handled by Qt widget */',
        '-webkit-line-clamp': '/* webkit-line-clamp handled by Qt widget */',
        '-webkit-box-orient': '/* webkit-box-orient handled by Qt widget */',
        'display: -webkit-box': '/* display: -webkit-box handled by Qt widget */',
    }
    
    for css_rule, qt_comment in text_overflow_conversions.items():
        qt_style = qt_style.replace(css_rule, qt_comment)
    
    # Clean up multiple whitespace and empty rules
    qt_style = re.sub(r'\s+', ' ', qt_style)
    qt_style = re.sub(r'{\s*}', '', qt_style)  # Remove empty rules
    qt_style = re.sub(r';\s*;', ';', qt_style)  # Remove duplicate semicolons
    
    return qt_style.strip()


def apply_text_truncation_to_qt_widget(widget, max_width: Optional[int] = None, enable_ellipsis: bool = True):
    """
    Apply text truncation settings to a Qt widget.
    
    Args:
        widget: Qt widget (QLabel, QPushButton, etc.)
        max_width: Maximum width for the widget
        enable_ellipsis: Whether to enable ellipsis truncation
    """
    if max_width:
        widget.setMaximumWidth(max_width)
    
    if enable_ellipsis and hasattr(widget, 'setWordWrap'):
        widget.setWordWrap(False)
    
    # For QLabel widgets, set elide mode
    if hasattr(widget, 'setTextElideMode'):
        try:
            from PySide6.QtCore import Qt
            widget.setTextElideMode(Qt.TextElideMode.ElideRight if enable_ellipsis else Qt.TextElideMode.ElideNone)
        except ImportError:
            pass  # Fallback for development


def get_text_overflow_properties(css_classes: str) -> Dict[str, Any]:
    """
    Extract text overflow properties from CSS class names.
    
    Args:
        css_classes: Space-separated CSS class names
        
    Returns:
        Dictionary with overflow properties
    """
    classes = css_classes.split()
    properties = {
        'truncate': False,
        'line_clamp': None,
        'break_words': False,
        'whitespace_nowrap': False,
        'max_lines': None,
    }
    
    for cls in classes:
        if cls == 'truncate':
            properties['truncate'] = True
            properties['whitespace_nowrap'] = True
        elif cls.startswith('line-clamp-'):
            try:
                lines = int(cls.split('-')[-1])
                properties['line_clamp'] = lines
                properties['max_lines'] = lines
            except ValueError:
                pass
        elif cls == 'break-words':
            properties['break_words'] = True
        elif cls == 'whitespace-nowrap':
            properties['whitespace_nowrap'] = True
    
    return properties
