# CellSorter Design System

## Design Tokens

### Color System

#### Base Colors (shadcn/ui inspired)

```python
# Light Theme
COLORS_LIGHT = {
    'background': 'hsl(0 0% 100%)',
    'foreground': 'hsl(222.2 84% 4.9%)',
    'card': 'hsl(0 0% 100%)',
    'card_foreground': 'hsl(222.2 84% 4.9%)',
    'popover': 'hsl(0 0% 100%)',
    'popover_foreground': 'hsl(222.2 84% 4.9%)',
    'primary': 'hsl(222.2 47.4% 11.2%)',
    'primary_foreground': 'hsl(210 40% 98%)',
    'secondary': 'hsl(210 40% 96%)',
    'secondary_foreground': 'hsl(222.2 84% 4.9%)',
    'muted': 'hsl(210 40% 96%)',
    'muted_foreground': 'hsl(215.4 16.3% 46.9%)',
    'accent': 'hsl(210 40% 96%)',
    'accent_foreground': 'hsl(222.2 84% 4.9%)',
    'destructive': 'hsl(0 84.2% 60.2%)',
    'destructive_foreground': 'hsl(210 40% 98%)',
    'border': 'hsl(214.3 31.8% 91.4%)',
    'input': 'hsl(214.3 31.8% 91.4%)',
    'ring': 'hsl(222.2 84% 4.9%)',
}

# Dark Theme
COLORS_DARK = {
    'background': 'hsl(222.2 84% 4.9%)',
    'foreground': 'hsl(210 40% 98%)',
    'card': 'hsl(222.2 84% 4.9%)',
    'card_foreground': 'hsl(210 40% 98%)',
    'popover': 'hsl(222.2 84% 4.9%)',
    'popover_foreground': 'hsl(210 40% 98%)',
    'primary': 'hsl(210 40% 98%)',
    'primary_foreground': 'hsl(222.2 47.4% 11.2%)',
    'secondary': 'hsl(217.2 32.6% 17.5%)',
    'secondary_foreground': 'hsl(210 40% 98%)',
    'muted': 'hsl(217.2 32.6% 17.5%)',
    'muted_foreground': 'hsl(215 20.2% 65.1%)',
    'accent': 'hsl(217.2 32.6% 17.5%)',
    'accent_foreground': 'hsl(210 40% 98%)',
    'destructive': 'hsl(0 62.8% 30.6%)',
    'destructive_foreground': 'hsl(210 40% 98%)',
    'border': 'hsl(217.2 32.6% 17.5%)',
    'input': 'hsl(217.2 32.6% 17.5%)',
    'ring': 'hsl(212.7 26.8% 83.9%)',
}

# Scientific/Medical Colors
MEDICAL_COLORS = {
    'cancer_primary': 'hsl(0 84.2% 60.2%)',      # Red
    'normal_tissue': 'hsl(142.1 76.2% 36.3%)',   # Green
    'stroma': 'hsl(221.2 83.2% 53.3%)',          # Blue
    'immune_cells': 'hsl(262.1 83.3% 57.8%)',    # Purple
    'blood_vessels': 'hsl(24.6 95% 53.1%)',      # Orange
    'necrosis': 'hsl(47.9 95.8% 53.1%)',         # Yellow
}
```

#### Typography

```python
TYPOGRAPHY = {
    'font_family_sans': ['Inter', 'system-ui', 'Segoe UI', 'sans-serif'],
    'font_family_mono': ['JetBrains Mono', 'Consolas', 'monospace'],
    
    # Font Sizes (rem)
    'text_xs': '0.75rem',    # 12px
    'text_sm': '0.875rem',   # 14px
    'text_base': '1rem',     # 16px
    'text_lg': '1.125rem',   # 18px
    'text_xl': '1.25rem',    # 20px
    'text_2xl': '1.5rem',    # 24px
    'text_3xl': '1.875rem',  # 30px
    'text_4xl': '2.25rem',   # 36px
    
    # Line Heights
    'leading_none': '1',
    'leading_tight': '1.25',
    'leading_normal': '1.5',
    'leading_relaxed': '1.625',
    
    # Font Weights
    'font_normal': '400',
    'font_medium': '500',
    'font_semibold': '600',
    'font_bold': '700',
}
```

#### Spacing

```python
SPACING = {
    'spacing_0': '0px',
    'spacing_1': '0.25rem',   # 4px
    'spacing_2': '0.5rem',    # 8px
    'spacing_3': '0.75rem',   # 12px
    'spacing_4': '1rem',      # 16px
    'spacing_5': '1.25rem',   # 20px
    'spacing_6': '1.5rem',    # 24px
    'spacing_8': '2rem',      # 32px
    'spacing_10': '2.5rem',   # 40px
    'spacing_12': '3rem',     # 48px
    'spacing_16': '4rem',     # 64px
    'spacing_20': '5rem',     # 80px
    'spacing_24': '6rem',     # 96px
}
```

#### Border Radius

```python
BORDER_RADIUS = {
    'radius_none': '0',
    'radius_sm': '0.125rem',   # 2px
    'radius_default': '0.25rem',  # 4px
    'radius_md': '0.375rem',   # 6px
    'radius_lg': '0.5rem',     # 8px
    'radius_xl': '0.75rem',    # 12px
    'radius_2xl': '1rem',      # 16px
    'radius_full': '9999px',
}
```

## Component Library

### Primary Components

#### Button

```python
class Button(QPushButton):
    """
    Modern button component with shadcn/ui styling
    
    Variants:
    - default: Primary button style
    - secondary: Secondary button style
    - outline: Outlined button style
    - ghost: Minimal button style
    - destructive: Destructive action style
    """
    
    VARIANTS = {
        'default': {
            'background': 'var(--primary)',
            'color': 'var(--primary-foreground)',
            'hover_background': 'var(--primary)/90',
        },
        'secondary': {
            'background': 'var(--secondary)',
            'color': 'var(--secondary-foreground)',
            'hover_background': 'var(--secondary)/80',
        },
        'outline': {
            'border': '1px solid var(--border)',
            'background': 'transparent',
            'hover_background': 'var(--accent)',
        },
        'ghost': {
            'background': 'transparent',
            'hover_background': 'var(--accent)',
        },
        'destructive': {
            'background': 'var(--destructive)',
            'color': 'var(--destructive-foreground)',
            'hover_background': 'var(--destructive)/90',
        }
    }
    
    SIZES = {
        'sm': {'height': '36px', 'padding': '0 12px', 'font_size': '14px'},
        'default': {'height': '40px', 'padding': '0 16px', 'font_size': '14px'},
        'lg': {'height': '44px', 'padding': '0 32px', 'font_size': '16px'},
        'icon': {'height': '40px', 'width': '40px'},
    }
```

#### Input

```python
class Input(QLineEdit):
    """
    Modern input field with validation states
    """
    
    STATES = {
        'default': {
            'border': '1px solid var(--border)',
            'background': 'transparent',
        },
        'focused': {
            'border': '1px solid var(--ring)',
            'outline': '2px solid var(--ring)',
            'outline_offset': '2px',
        },
        'error': {
            'border': '1px solid var(--destructive)',
        },
        'disabled': {
            'opacity': '0.5',
            'cursor': 'not-allowed',
        }
    }
```

#### Card

```python
class Card(QFrame):
    """
    Container component for grouped content
    """
    
    STYLES = {
        'background': 'var(--card)',
        'color': 'var(--card-foreground)',
        'border': '1px solid var(--border)',
        'border_radius': 'var(--radius-lg)',
        'box_shadow': '0 1px 3px 0 rgb(0 0 0 / 0.1)',
    }
    
    class Header(QLabel):
        """Card header component"""
        pass
        
    class Content(QWidget):
        """Card content area"""
        pass
        
    class Footer(QWidget):
        """Card footer area"""
        pass
```

#### Dialog

```python
class Dialog(QDialog):
    """
    Modal dialog component with overlay
    """
    
    STYLES = {
        'background': 'var(--background)',
        'border': '1px solid var(--border)',
        'border_radius': 'var(--radius-lg)',
        'box_shadow': '0 10px 15px -3px rgb(0 0 0 / 0.1)',
    }
    
    class Overlay(QWidget):
        """Semi-transparent background overlay"""
        STYLES = {
            'background': 'rgb(0 0 0 / 0.8)',
            'backdrop_filter': 'blur(4px)',
        }
```

### Scientific Components

#### ScatterPlotWidget

```python
class ScatterPlotWidget(QWidget):
    """
    Interactive scatter plot for cell data visualization
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_interactions()
    
    PLOT_STYLES = {
        'background': 'var(--card)',
        'grid_color': 'var(--border)',
        'axis_color': 'var(--muted-foreground)',
        'selection_color': 'var(--primary)',
        'selection_alpha': 0.3,
    }
    
    POINT_STYLES = {
        'default': {'size': 3, 'alpha': 0.7},
        'selected': {'size': 4, 'alpha': 1.0, 'outline': True},
        'highlighted': {'size': 5, 'alpha': 1.0},
    }
```

#### ImageViewerWidget

```python
class ImageViewerWidget(QLabel):
    """
    Microscopy image viewer with overlay support
    """
    
    OVERLAY_STYLES = {
        'cell_boundary': {
            'color': 'var(--primary)',
            'width': 1,
            'style': 'solid',
        },
        'selection_highlight': {
            'color': 'var(--accent)',
            'width': 2,
            'fill_alpha': 0.2,
        },
        'calibration_point': {
            'color': 'var(--destructive)',
            'size': 8,
            'shape': 'cross',
        }
    }
```

#### WellPlateWidget

```python
class WellPlateWidget(QGridLayout):
    """
    96-well plate visualization and selection
    """
    
    WELL_STYLES = {
        'empty': {
            'background': 'var(--muted)',
            'border': '1px solid var(--border)',
        },
        'assigned': {
            'background': 'var(--primary)',
            'color': 'var(--primary-foreground)',
        },
        'selected': {
            'border': '2px solid var(--ring)',
        }
    }
    
    LAYOUT = {
        'rows': 8,  # A-H
        'columns': 12,  # 01-12
        'well_size': 32,
        'spacing': 2,
    }
```

### Navigation Components

#### Sidebar

```python
class Sidebar(QFrame):
    """
    Collapsible sidebar navigation
    """
    
    STATES = {
        'expanded': {'width': 280},
        'collapsed': {'width': 80},
    }
    
    class NavigationItem(QPushButton):
        """Individual navigation item"""
        STYLES = {
            'default': {
                'background': 'transparent',
                'padding': '8px 12px',
                'text_align': 'left',
            },
            'active': {
                'background': 'var(--accent)',
                'color': 'var(--accent-foreground)',
            },
            'hover': {
                'background': 'var(--muted)',
            }
        }
```

#### Toolbar

```python
class Toolbar(QToolBar):
    """
    Main application toolbar
    """
    
    STYLES = {
        'background': 'var(--background)',
        'border_bottom': '1px solid var(--border)',
        'height': 48,
        'padding': '0 16px',
    }
    
    class ToolButton(QToolButton):
        """Toolbar button component"""
        pass
    
    class Separator(QFrame):
        """Toolbar separator"""
        pass
```

### Data Display Components

#### Table

```python
class Table(QTableWidget):
    """
    Data table with sorting and filtering
    """
    
    STYLES = {
        'header': {
            'background': 'var(--muted)',
            'font_weight': 'var(--font-medium)',
            'border_bottom': '1px solid var(--border)',
        },
        'row_even': {
            'background': 'var(--background)',
        },
        'row_odd': {
            'background': 'var(--muted)/50',
        },
        'row_selected': {
            'background': 'var(--accent)',
        }
    }
```

#### StatusBar

```python
class StatusBar(QStatusBar):
    """
    Application status bar with indicators
    """
    
    STYLES = {
        'background': 'var(--muted)',
        'border_top': '1px solid var(--border)',
        'height': 32,
        'padding': '0 16px',
    }
    
    class Indicator(QLabel):
        """Status indicator widget"""
        STATES = {
            'success': {'color': 'var(--success)'},
            'warning': {'color': 'var(--warning)'},
            'error': {'color': 'var(--destructive)'},
        }
```

## Theme Integration

### Qt-Material Integration

```python
class ThemeManager:
    """
    Manages theme switching between custom and qt-material themes
    """
    
    QT_MATERIAL_THEMES = [
        'dark_amber.xml', 'dark_blue.xml', 'dark_cyan.xml',
        'dark_lightgreen.xml', 'dark_pink.xml', 'dark_purple.xml',
        'dark_red.xml', 'dark_teal.xml', 'dark_yellow.xml',
        'light_amber.xml', 'light_blue.xml', 'light_cyan.xml',
        'light_lightgreen.xml', 'light_pink.xml', 'light_purple.xml',
        'light_red.xml', 'light_teal.xml', 'light_yellow.xml'
    ]
    
    @staticmethod
    def apply_qt_material_theme(app, theme_name):
        """Apply qt-material theme"""
        from qt_material import apply_stylesheet
        apply_stylesheet(app, theme=theme_name)
    
    @staticmethod
    def apply_custom_theme(app, theme_name):
        """Apply custom shadcn/ui inspired theme"""
        # Implementation for custom theme application
        pass
```

### CSS Variables

```css
:root {
    /* Light theme variables */
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 222.2 84% 4.9%;
    --primary: 222.2 47.4% 11.2%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96%;
    --secondary-foreground: 222.2 84% 4.9%;
    --muted: 210 40% 96%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96%;
    --accent-foreground: 222.2 84% 4.9%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 222.2 84% 4.9%;
    --radius: 0.5rem;
}

[data-theme="dark"] {
    /* Dark theme variables */
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    /* ... etc */
}
```

## Animation System

### Transitions

```python
TRANSITIONS = {
    'default': 'all 150ms ease-out',
    'fast': 'all 100ms ease-out',
    'slow': 'all 300ms ease-out',
    'colors': 'color 150ms ease-out, background-color 150ms ease-out, border-color 150ms ease-out',
}

ANIMATIONS = {
    'fade_in': 'fadeIn 200ms ease-out',
    'fade_out': 'fadeOut 200ms ease-out',
    'slide_up': 'slideUp 300ms ease-out',
    'slide_down': 'slideDown 300ms ease-out',
    'scale_up': 'scaleUp 200ms ease-out',
    'scale_down': 'scaleDown 200ms ease-out',
}
```

### Loading States

```python
class LoadingSpinner(QWidget):
    """Animated loading spinner"""
    
    STYLES = {
        'size': 24,
        'color': 'var(--primary)',
        'animation': 'spin 1s linear infinite',
    }

class SkeletonLoader(QWidget):
    """Skeleton loading animation for content"""
    
    STYLES = {
        'background': 'var(--muted)',
        'animation': 'shimmer 2s ease-in-out infinite',
    }
```

## Accessibility Features

### Focus Management

```python
FOCUS_STYLES = {
    'ring': {
        'outline': '2px solid var(--ring)',
        'outline_offset': '2px',
        'border_radius': 'var(--radius)',
    },
    'high_contrast': {
        'outline': '3px solid currentColor',
        'outline_offset': '3px',
    }
}
```

### Screen Reader Support

```python
class AccessibleWidget(QWidget):
    """Base widget with accessibility features"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAccessibleName("")
        self.setAccessibleDescription("")
        self.setFocusPolicy(Qt.TabFocus)
    
    def set_aria_label(self, label):
        """Set ARIA label for screen readers"""
        self.setAccessibleName(label)
    
    def set_aria_description(self, description):
        """Set ARIA description for screen readers"""
        self.setAccessibleDescription(description)
```

## Responsive Design

### Breakpoints

```python
BREAKPOINTS = {
    'mobile': 768,
    'tablet': 1024,
    'desktop': 1280,
    'wide': 1920,
}

class ResponsiveLayout(QWidget):
    """Layout that adapts to window size"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_breakpoint = 'desktop'
        self.layouts = {}
    
    def update_layout(self, width):
        """Update layout based on window width"""
        if width < BREAKPOINTS['mobile']:
            self.current_breakpoint = 'mobile'
        elif width < BREAKPOINTS['tablet']:
            self.current_breakpoint = 'tablet'
        elif width < BREAKPOINTS['desktop']:
            self.current_breakpoint = 'desktop'
        else:
            self.current_breakpoint = 'wide'
```

This design system provides a comprehensive foundation for building CellSorter's user interface with modern, accessible, and consistent components that seamlessly integrate both qt-material's robust theming capabilities and shadcn/ui's contemporary design principles. 