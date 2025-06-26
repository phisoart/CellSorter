"""
Design Tokens Configuration

Central configuration for all design tokens based on docs/design/DESIGN_SYSTEM.md
Ensures consistency across the application.
"""

from typing import Dict, Tuple


class Colors:
    """Color design tokens in HSL format."""
    
    # Light Theme Colors
    LIGHT = {
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
    DARK = {
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
    
    # Medical/Scientific Colors
    MEDICAL = {
        'cancer_primary': 'hsl(0, 84.2%, 60.2%)',
        'normal_tissue': 'hsl(142.1, 76.2%, 36.3%)',
        'stroma': 'hsl(221.2, 83.2%, 53.3%)',
        'immune_cells': 'hsl(262.1, 83.3%, 57.8%)',
        'blood_vessels': 'hsl(24.6, 95%, 53.1%)',
        'necrosis': 'hsl(47.9, 95.8%, 53.1%)',
    }


class Typography:
    """Typography design tokens."""
    
    # Font Families
    FONT_FAMILY_SANS = ['Inter', 'system-ui', 'Segoe UI', 'sans-serif']
    FONT_FAMILY_MONO = ['JetBrains Mono', 'Consolas', 'monospace']
    
    # Font Sizes (rem and px)
    FONT_SIZES = {
        'xs': {'rem': '0.75rem', 'px': 12},
        'sm': {'rem': '0.875rem', 'px': 14},
        'base': {'rem': '1rem', 'px': 16},
        'lg': {'rem': '1.125rem', 'px': 18},
        'xl': {'rem': '1.25rem', 'px': 20},
        '2xl': {'rem': '1.5rem', 'px': 24},
        '3xl': {'rem': '1.875rem', 'px': 30},
        '4xl': {'rem': '2.25rem', 'px': 36},
    }
    
    # Line Heights
    LINE_HEIGHTS = {
        'none': 1.0,
        'tight': 1.25,
        'normal': 1.5,
        'relaxed': 1.625,
    }
    
    # Font Weights
    FONT_WEIGHTS = {
        'normal': 400,
        'medium': 500,
        'semibold': 600,
        'bold': 700,
    }


class Spacing:
    """Spacing design tokens."""
    
    # Spacing values (rem and px)
    VALUES = {
        '0': {'rem': '0', 'px': 0},
        '1': {'rem': '0.25rem', 'px': 4},
        '2': {'rem': '0.5rem', 'px': 8},
        '3': {'rem': '0.75rem', 'px': 12},
        '4': {'rem': '1rem', 'px': 16},
        '5': {'rem': '1.25rem', 'px': 20},
        '6': {'rem': '1.5rem', 'px': 24},
        '8': {'rem': '2rem', 'px': 32},
        '10': {'rem': '2.5rem', 'px': 40},
        '12': {'rem': '3rem', 'px': 48},
        '16': {'rem': '4rem', 'px': 64},
        '20': {'rem': '5rem', 'px': 80},
        '24': {'rem': '6rem', 'px': 96},
    }


class BorderRadius:
    """Border radius design tokens."""
    
    # Radius values (rem and px)
    VALUES = {
        'none': {'rem': '0', 'px': 0},
        'sm': {'rem': '0.125rem', 'px': 2},
        'default': {'rem': '0.25rem', 'px': 4},
        'md': {'rem': '0.375rem', 'px': 6},
        'lg': {'rem': '0.5rem', 'px': 8},
        'xl': {'rem': '0.75rem', 'px': 12},
        '2xl': {'rem': '1rem', 'px': 16},
        'full': {'rem': '9999px', 'px': 9999},
    }


class Shadows:
    """Box shadow design tokens."""
    
    VALUES = {
        'sm': '0 1px 2px 0 rgb(0 0 0 / 0.05)',
        'default': '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
        'md': '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
        'lg': '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
        'xl': '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
        '2xl': '0 25px 50px -12px rgb(0 0 0 / 0.25)',
        'inner': 'inset 0 2px 4px 0 rgb(0 0 0 / 0.05)',
        'none': 'none',
    }


class Transitions:
    """Transition and animation design tokens."""
    
    # Durations (ms)
    DURATIONS = {
        'fast': 100,
        'default': 150,
        'slow': 300,
    }
    
    # Easings
    EASINGS = {
        'default': 'ease-out',
        'in': 'ease-in',
        'out': 'ease-out',
        'in-out': 'ease-in-out',
    }
    
    # Common transitions
    TRANSITIONS = {
        'all': 'all 150ms ease-out',
        'colors': 'color 150ms ease-out, background-color 150ms ease-out, border-color 150ms ease-out',
        'transform': 'transform 150ms ease-out',
        'opacity': 'opacity 150ms ease-out',
    }


class ComponentSizes:
    """Standard component size design tokens."""
    
    # Button sizes
    BUTTON_SIZES = {
        'sm': {'height': 36, 'padding_x': 12, 'padding_y': 4},
        'default': {'height': 40, 'padding_x': 16, 'padding_y': 8},
        'lg': {'height': 44, 'padding_x': 32, 'padding_y': 12},
        'icon': {'height': 40, 'width': 40},
    }
    
    # Input sizes
    INPUT_SIZES = {
        'default': {'height': 40, 'padding_x': 12, 'padding_y': 8},
    }
    
    # Panel sizes (percentages)
    PANEL_SIZES = {
        'image': 40,
        'plot': 35,
        'selection': 25,
    }


class Breakpoints:
    """Responsive breakpoint design tokens."""
    
    VALUES = {
        'mobile': 768,
        'tablet': 1024,
        'desktop': 1280,
        'wide': 1920,
    }