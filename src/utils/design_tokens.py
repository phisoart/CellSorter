"""
Design Tokens for CellSorter

Central repository for design system tokens including colors, typography,
spacing, and animations based on docs/design/DESIGN_SYSTEM.md
"""

from typing import Dict, Tuple
from dataclasses import dataclass


@dataclass
class DesignTokens:
    """Container for all design system tokens."""
    
    # Typography
    TYPOGRAPHY = {
        'font_family_sans': ['Inter', 'system-ui', 'Segoe UI', 'sans-serif'],
        'font_family_mono': ['JetBrains Mono', 'Consolas', 'monospace'],
        
        # Font Sizes (rem to px)
        'text_xs': 12,    # 0.75rem
        'text_sm': 14,    # 0.875rem
        'text_base': 16,  # 1rem
        'text_lg': 18,    # 1.125rem
        'text_xl': 20,    # 1.25rem
        'text_2xl': 24,   # 1.5rem
        'text_3xl': 30,   # 1.875rem
        'text_4xl': 36,   # 2.25rem
        
        # Line Heights
        'leading_none': 1.0,
        'leading_tight': 1.25,
        'leading_normal': 1.5,
        'leading_relaxed': 1.625,
        
        # Font Weights
        'font_normal': 400,
        'font_medium': 500,
        'font_semibold': 600,
        'font_bold': 700,
    }
    
    # Spacing (in pixels)
    SPACING = {
        'spacing_0': 0,
        'spacing_1': 4,    # 0.25rem
        'spacing_2': 8,    # 0.5rem
        'spacing_3': 12,   # 0.75rem
        'spacing_4': 16,   # 1rem
        'spacing_5': 20,   # 1.25rem
        'spacing_6': 24,   # 1.5rem
        'spacing_8': 32,   # 2rem
        'spacing_10': 40,  # 2.5rem
        'spacing_12': 48,  # 3rem
        'spacing_16': 64,  # 4rem
        'spacing_20': 80,  # 5rem
        'spacing_24': 96,  # 6rem
    }
    
    # Border Radius (in pixels)
    BORDER_RADIUS = {
        'radius_none': 0,
        'radius_sm': 2,      # 0.125rem
        'radius_default': 4, # 0.25rem
        'radius_md': 6,      # 0.375rem
        'radius_lg': 8,      # 0.5rem
        'radius_xl': 12,     # 0.75rem
        'radius_2xl': 16,    # 1rem
        'radius_full': 9999,
    }
    
    # Button Sizes
    BUTTON_SIZES = {
        'sm': {'height': 36, 'padding_h': 12, 'font_size': 14},
        'default': {'height': 40, 'padding_h': 16, 'font_size': 14},
        'lg': {'height': 44, 'padding_h': 32, 'font_size': 16},
        'icon': {'height': 40, 'width': 40},
    }
    
    # Component Dimensions
    DIMENSIONS = {
        'input_height': 40,
        'toolbar_height': 48,
        'statusbar_height': 32,
        'well_size': 32,
        'well_spacing': 2,
        'sidebar_expanded': 280,
        'sidebar_collapsed': 80,
    }
    
    # Animation Durations (in milliseconds)
    ANIMATIONS = {
        'duration_fast': 100,
        'duration_normal': 150,
        'duration_slow': 300,
        'easing': 'cubic-bezier(0.4, 0, 0.2, 1)',
    }
    
    # Transitions
    TRANSITIONS = {
        'default': 'all 150ms ease-out',
        'fast': 'all 100ms ease-out',
        'slow': 'all 300ms ease-out',
        'colors': 'color 150ms ease-out, background-color 150ms ease-out, border-color 150ms ease-out',
    }
    
    # Box Shadows
    SHADOWS = {
        'shadow_sm': '0 1px 2px 0 rgb(0 0 0 / 0.05)',
        'shadow': '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
        'shadow_md': '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
        'shadow_lg': '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
    }
    
    # Breakpoints (in pixels)
    BREAKPOINTS = {
        'mobile': 768,
        'tablet': 1024,
        'desktop': 1280,
        'wide': 1920,
    }
    
    # Focus Styles
    FOCUS_STYLES = {
        'ring_width': 2,
        'ring_offset': 2,
        'high_contrast_width': 3,
        'high_contrast_offset': 3,
    }
    
    # 96-Well Plate Layout
    WELL_PLATE = {
        'rows': 8,  # A-H
        'columns': 12,  # 01-12
        'labels': {
            'rows': ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'],
            'columns': [str(i).zfill(2) for i in range(1, 13)]
        }
    }
    
    # Cell Selection Colors (16 predefined colors, HEX)
    SELECTION_COLORS = {
        'red':      {'primary': '#FF0000', 'label': 'Red'},
        'green':    {'primary': '#00FF00', 'label': 'Green'},
        'blue':     {'primary': '#0000FF', 'label': 'Blue'},
        'yellow':   {'primary': '#FFFF00', 'label': 'Yellow'},
        'magenta':  {'primary': '#FF00FF', 'label': 'Magenta'},
        'cyan':     {'primary': '#00FFFF', 'label': 'Cyan'},
        'orange':   {'primary': '#FF8000', 'label': 'Orange'},
        'purple':   {'primary': '#8000FF', 'label': 'Purple'},
        'pink':     {'primary': '#FF0080', 'label': 'Pink'},
        'lime':     {'primary': '#80FF00', 'label': 'Lime'},
        'sky':      {'primary': '#0080FF', 'label': 'Sky Blue'},
        'light_red':    {'primary': '#FF8080', 'label': 'Light Red'},
        'light_green':  {'primary': '#80FF80', 'label': 'Light Green'},
        'light_blue':   {'primary': '#8080FF', 'label': 'Light Blue'},
        'light_yellow': {'primary': '#FFFF80', 'label': 'Light Yellow'},
        'light_magenta':{'primary': '#FF80FF', 'label': 'Light Magenta'},
    }
    
    @staticmethod
    def get_font_string(font_family: str = 'sans') -> str:
        """
        Get font family string for Qt stylesheet.
        
        Args:
            font_family: Either 'sans' or 'mono'
            
        Returns:
            Font family string
        """
        fonts = DesignTokens.TYPOGRAPHY[f'font_family_{font_family}']
        return ', '.join(f'"{font}"' if ' ' in font else font for font in fonts)
    
    @staticmethod
    def get_breakpoint(width: int) -> str:
        """
        Get current breakpoint based on window width.
        
        Args:
            width: Window width in pixels
            
        Returns:
            Breakpoint name ('mobile', 'tablet', 'desktop', or 'wide')
        """
        if width < DesignTokens.BREAKPOINTS['mobile']:
            return 'mobile'
        elif width < DesignTokens.BREAKPOINTS['tablet']:
            return 'tablet'
        elif width < DesignTokens.BREAKPOINTS['desktop']:
            return 'desktop'
        else:
            return 'wide'
    
    @staticmethod
    def get_well_label(row: int, column: int) -> str:
        """
        Get well label for 96-well plate position.
        
        Args:
            row: Row index (0-7)
            column: Column index (0-11)
            
        Returns:
            Well label (e.g., 'A01', 'H12')
        """
        if 0 <= row < 8 and 0 <= column < 12:
            return f"{DesignTokens.WELL_PLATE['labels']['rows'][row]}{DesignTokens.WELL_PLATE['labels']['columns'][column]}"
        return ""
    
    @staticmethod
    def get_well_position(label: str) -> Tuple[int, int]:
        """
        Get row and column indices from well label.
        
        Args:
            label: Well label (e.g., 'A01', 'H12')
            
        Returns:
            Tuple of (row, column) indices, or (-1, -1) if invalid
        """
        if len(label) >= 3:
            row_char = label[0].upper()
            col_str = label[1:3]
            
            try:
                row = DesignTokens.WELL_PLATE['labels']['rows'].index(row_char)
                col = int(col_str) - 1
                
                if 0 <= row < 8 and 0 <= col < 12:
                    return (row, col)
            except (ValueError, IndexError):
                pass
        
        return (-1, -1) 