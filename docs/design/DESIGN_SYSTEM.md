# CellSorter Design System

## Table of Contents
1. [Design Tokens](#design-tokens)
2. [Component Library](#component-library)
3. [Text Handling Guidelines](#text-handling-guidelines)
4. [Component States](#component-states)
5. [Responsive Patterns](#responsive-patterns)
6. [Accessibility Standards](#accessibility-standards)
7. [3-Mode Compatibility](#3-mode-compatibility)
8. [Theme Integration](#theme-integration)
9. [Animation System](#animation-system)
10. [Migration Guide](#migration-guide)

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

### Base Components

#### BaseButton

```python
from src.components.base.base_button import BaseButton

# Usage Examples
button = BaseButton("Click Me")
button = BaseButton("Primary", variant="default")
button = BaseButton("Secondary", variant="secondary") 
button = BaseButton("Outline", variant="outline")
button = BaseButton("Ghost", variant="ghost")
button = BaseButton("Delete", variant="destructive")

# With Loading State
button = BaseButton("Loading...", loading=True)

# With Icon
button = BaseButton("Save", icon=some_icon)

# Size Variants
button = BaseButton("Small", size="sm")
button = BaseButton("Default", size="default")
button = BaseButton("Large", size="lg")
button = BaseButton("", size="icon")  # Icon only

# Factory Methods
save_btn = BaseButton.create_primary("Save")
cancel_btn = BaseButton.create_secondary("Cancel") 
delete_btn = BaseButton.create_destructive("Delete")
loading_btn = BaseButton.create_loading("Processing...")
```

**States Supported:**
- `default`: Standard button state
- `hover`: Interactive hover state
- `pressed`: Active/pressed state
- `disabled`: Non-interactive state
- `loading`: Processing state with spinner

**Accessibility Features:**
- Keyboard navigation (Enter/Space)
- Screen reader support with accessible names
- Focus ring indicators
- Loading state announcements

#### BaseCard

```python
from src.components.base.base_card import BaseCard

# Basic Card
card = BaseCard()
card.add_content(some_widget)

# Clickable Card with Callback
def on_card_click():
    print("Card clicked!")

card = BaseCard(clickable=True, click_callback=on_card_click)

# With Header and Footer
card = BaseCard()
card.set_header("Card Title")
card.add_content(content_widget)
card.set_footer(footer_widget)

# Styling Variants
card = BaseCard(style="elevated")  # With shadow
card = BaseCard(style="outlined")  # With border only
```

**States Supported:**
- `default`: Standard card appearance
- `hover`: Elevated appearance on hover (for clickable cards)
- `pressed`: Pressed state for clickable cards
- `focused`: Keyboard focus state

**Accessibility Features:**
- Keyboard navigation for clickable cards
- Role announcements for screen readers
- Focus management

#### BaseInput

```python
from src.components.base.base_input import BaseInput

# Basic Input
input_field = BaseInput("Enter text...")

# With State Management
input_field = BaseInput("Email", state="default")
input_field.set_state("error", "Invalid email format")
input_field.set_state("pending", "Validating...")
input_field.set_state("disabled")

# Factory Methods
email_input = BaseInput.create_email("Enter email")
password_input = BaseInput.create_password("Enter password")
search_input = BaseInput.create_search("Search...")
```

**States Supported:**
- `default`: Standard input state
- `focused`: Active input state with focus ring
- `error`: Error state with validation message
- `disabled`: Non-interactive state
- `pending`: Loading state with spinner

**Features:**
- Real-time validation support
- Loading spinner for async operations
- Error message display
- Placeholder text support

#### BaseSelect

```python
from src.components.base.base_select import BaseSelect

# Basic Select
select = BaseSelect("Choose option...")
select.add_option("Option 1", "value1")
select.add_option("Option 2", "value2")

# With State Management
select.set_state("error", "Please select an option")
select.set_state("pending", "Loading options...")

# Multiple Selection
multi_select = BaseSelect("Choose multiple...", multiple=True)

# Factory Methods
priority_select = BaseSelect.create_priority()
status_select = BaseSelect.create_status()
```

**States Supported:**
- `default`: Standard select state
- `focused`: Active select state
- `error`: Error state with validation
- `disabled`: Non-interactive state
- `pending`: Loading state for async options

#### BaseTextarea

```python
from src.components.base.base_textarea import BaseTextarea

# Basic Textarea
textarea = BaseTextarea("Enter description...")

# With Character Limit
textarea = BaseTextarea("Comment", max_length=500)

# With Word Wrapping Control
textarea = BaseTextarea("Notes", word_wrap=True)

# Resizable
textarea = BaseTextarea("Content", resizable=True)

# Factory Methods
comment_area = BaseTextarea.create_comment()
notes_area = BaseTextarea.create_notes()
description_area = BaseTextarea.create_description()
```

**States Supported:**
- `default`: Standard textarea state
- `focused`: Active textarea state
- `error`: Error state with validation
- `disabled`: Non-interactive state
- `pending`: Loading state

**Features:**
- Character/word counting
- Auto-resize functionality
- Word wrap control
- Scroll bar management

### Utility Components

#### SkeletonLoader

```python
from src.components.skeleton_loader import SkeletonLoader

# Basic Skeleton
skeleton = SkeletonLoader(width=200, height=20)

# Text Skeleton
text_skeleton = SkeletonLoader.create_text_line()
paragraph_skeleton = SkeletonLoader.create_paragraph(lines=3)

# Card Skeleton
card_skeleton = SkeletonLoader.create_card()

# Custom Animation
skeleton = SkeletonLoader(width=100, height=100, animation_duration=1500)
```

**Animation Types:**
- `shimmer`: Default shimmer effect
- `pulse`: Pulsing opacity animation
- `wave`: Wave-like motion effect

#### TooltipWrapper

```python
from src.components.tooltip_wrapper import TooltipWrapper

# Basic Tooltip
tooltip = TooltipWrapper(target_widget, "This is a tooltip")

# Positioned Tooltip
tooltip = TooltipWrapper(widget, "Tooltip text", position="bottom")

# Rich Content Tooltip
tooltip = TooltipWrapper(widget, tooltip_content_widget)

# Delayed Tooltip
tooltip = TooltipWrapper(widget, "Delayed tooltip", delay=1000)
```

**Position Options:**
- `top`, `bottom`, `left`, `right`
- `top-start`, `top-end`
- `bottom-start`, `bottom-end`

### Scientific Components

#### ScatterPlotWidget

```python
class ScatterPlotWidget(QWidget):
    """
    Interactive scatter plot for cell data visualization with 3-mode support
    """
    
    def __init__(self, parent=None, mode="gui"):
        super().__init__(parent)
        self.mode = mode  # "gui", "dev", "dual"
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
    Microscopy image viewer with overlay support and 3-mode compatibility
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
    96-well plate visualization and selection with responsive design
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

## Text Handling Guidelines

### Overflow Strategies

```python
# Truncation with Ellipsis
def apply_text_truncation(widget, max_width):
    """Apply text truncation with ellipsis for overflow"""
    metrics = widget.fontMetrics()
    text = widget.text()
    elided_text = metrics.elidedText(text, Qt.ElideRight, max_width)
    widget.setText(elided_text)

# Word Wrapping
def apply_word_wrap(widget, word_wrap=True):
    """Apply word wrapping for multi-line text"""
    if hasattr(widget, 'setWordWrap'):
        widget.setWordWrap(word_wrap)
    elif hasattr(widget, 'setWordWrapMode'):
        from PySide6.QtGui import QTextOption
        widget.setWordWrapMode(QTextOption.WordWrap if word_wrap else QTextOption.NoWrap)

# Smart Truncation
def smart_truncate(text, max_length, suffix="..."):
    """Intelligently truncate text at word boundaries"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)].rsplit(' ', 1)[0] + suffix
```

### When to Truncate

- **Labels**: Always truncate with ellipsis when container width is fixed
- **Buttons**: Truncate button text but ensure minimum readable width
- **Table Cells**: Use ellipsis with tooltips showing full content
- **Cards**: Truncate descriptions but show full text in hover/focus
- **Lists**: Truncate long items but provide expansion mechanisms

### Typography Hierarchy

```python
TEXT_HIERARCHY = {
    'display': {'size': 'text_4xl', 'weight': 'font_bold', 'line_height': 'leading_tight'},
    'h1': {'size': 'text_3xl', 'weight': 'font_bold', 'line_height': 'leading_tight'},
    'h2': {'size': 'text_2xl', 'weight': 'font_semibold', 'line_height': 'leading_tight'},
    'h3': {'size': 'text_xl', 'weight': 'font_semibold', 'line_height': 'leading_normal'},
    'h4': {'size': 'text_lg', 'weight': 'font_medium', 'line_height': 'leading_normal'},
    'body': {'size': 'text_base', 'weight': 'font_normal', 'line_height': 'leading_normal'},
    'small': {'size': 'text_sm', 'weight': 'font_normal', 'line_height': 'leading_normal'},
    'caption': {'size': 'text_xs', 'weight': 'font_normal', 'line_height': 'leading_normal'},
}
```

## Component States

### Loading Patterns

```python
# Button Loading State
button = BaseButton("Save", loading=True)
# Shows spinner + disabled state + "Processing..." text

# Input Loading State  
input_field = BaseInput("Search...")
input_field.set_state("pending", "Searching...")
# Shows spinner in right side of input

# Card Loading State
card = BaseCard()
skeleton = SkeletonLoader.create_card()
card.add_content(skeleton)
# Shows skeleton animation while content loads

# Select Loading State
select = BaseSelect("Loading options...")
select.set_state("pending", "Loading...")
# Shows spinner + disabled state
```

### Error Handling

```python
# Input Validation Errors
input_field = BaseInput("Email")
input_field.set_state("error", "Please enter a valid email address")
# Shows red border + error message below

# Form Validation
def validate_form(form_inputs):
    errors = {}
    for field_name, input_widget in form_inputs.items():
        if not input_widget.text().strip():
            input_widget.set_state("error", f"{field_name} is required")
            errors[field_name] = "Required field"
    return len(errors) == 0

# Global Error Handling
def handle_api_error(error, affected_components):
    for component in affected_components:
        component.set_state("error", f"Failed to load: {error}")
```

### State Transitions

```python
# Smooth state transitions with animations
def transition_state(widget, from_state, to_state, duration=150):
    """Animate state transitions between component states"""
    animation = QPropertyAnimation(widget, b"styleSheet")
    animation.setDuration(duration)
    animation.setStartValue(widget.get_state_style(from_state))
    animation.setEndValue(widget.get_state_style(to_state))
    animation.start()
```

## Responsive Patterns

### Breakpoints

```python
BREAKPOINTS = {
    'mobile': 768,
    'tablet': 1024,
    'desktop': 1280,
    'wide': 1920,
}

# Responsive Layout Manager
class ResponsiveManager:
    @staticmethod
    def get_current_breakpoint(width):
        if width < BREAKPOINTS['mobile']:
            return 'mobile'
        elif width < BREAKPOINTS['tablet']:
            return 'tablet'
        elif width < BREAKPOINTS['desktop']:
            return 'desktop'
        return 'wide'
    
    @staticmethod
    def adapt_layout(widget, breakpoint):
        if breakpoint == 'mobile':
            widget.apply_mobile_layout()
        elif breakpoint == 'tablet':
            widget.apply_tablet_layout()
        else:
            widget.apply_desktop_layout()
```

### Touch Targets

```python
TOUCH_TARGETS = {
    'minimum': 44,  # Minimum touch target size (44x44px)
    'comfortable': 48,  # Comfortable touch target
    'spacious': 56,  # Spacious touch target
}

# Apply touch-friendly sizing
def make_touch_friendly(widget, size='comfortable'):
    min_size = TOUCH_TARGETS[size]
    widget.setMinimumSize(min_size, min_size)
```

### Layout Adaptation

```python
# Three-panel layout with responsive behavior
class ResponsiveThreePanel(QWidget):
    def __init__(self):
        super().__init__()
        self.left_panel = QWidget()    # Image viewer
        self.center_panel = QWidget()  # Data table
        self.right_panel = QWidget()   # Logs & well plate
        
        # Set minimum sizes to prevent panels from disappearing
        self.left_panel.setMinimumWidth(200)
        self.center_panel.setMinimumWidth(300)
        self.right_panel.setMinimumWidth(250)
        
        self.setup_splitters()
    
    def setup_splitters(self):
        # Main horizontal splitter
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.addWidget(self.left_panel)
        self.main_splitter.addWidget(self.center_panel)
        self.main_splitter.addWidget(self.right_panel)
        
        # Set default proportions (2:3:2)
        self.main_splitter.setSizes([200, 400, 200])
        
        # Set minimum sizes to prevent collapse
        self.main_splitter.setChildrenCollapsible(False)
        
    def adapt_to_window_size(self, width):
        if width < BREAKPOINTS['tablet']:
            # Stack vertically on small screens
            self.convert_to_vertical_layout()
        else:
            # Horizontal layout for larger screens
            self.convert_to_horizontal_layout()
```

## Accessibility Standards

### ARIA Implementation

```python
from src.utils.accessibility import AccessibilityRole, AccessibilityState

# Button Accessibility
button = BaseButton("Save Document")
button.setAccessibleName("Save Document")
button.setAccessibleDescription("Save the current document to disk")
button.set_accessibility_role(AccessibilityRole.BUTTON)

# Input Accessibility
input_field = BaseInput("Email Address")
input_field.setAccessibleName("Email Address")
input_field.setAccessibleDescription("Enter your email address for account registration")
input_field.set_accessibility_role(AccessibilityRole.TEXT_INPUT)

# Card Accessibility (when clickable)
card = BaseCard(clickable=True)
card.setAccessibleName("User Profile Card")
card.setAccessibleDescription("Click to view detailed user profile information")
card.set_accessibility_role(AccessibilityRole.BUTTON)

# Loading State Announcements
widget.set_accessibility_state(AccessibilityState.BUSY, True)
widget.setAccessibleDescription("Loading content, please wait...")
```

### Focus Management

```python
# Focus Ring Styles
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

# Focus Navigation
class FocusManager:
    @staticmethod
    def create_focus_chain(widgets):
        """Create keyboard navigation chain between widgets"""
        for i in range(len(widgets)):
            current = widgets[i]
            next_widget = widgets[(i + 1) % len(widgets)]
            current.setTabOrder(current, next_widget)
    
    @staticmethod
    def set_focus_policy(widget, policy=Qt.TabFocus):
        """Set focus policy for keyboard navigation"""
        widget.setFocusPolicy(policy)
        
    @staticmethod
    def announce_state_change(widget, message):
        """Announce state changes to screen readers"""
        widget.setAccessibleDescription(message)
```

### Screen Reader Support

```python
# Complete accessibility setup for components
def setup_accessibility(widget, role, name, description=None):
    """Setup comprehensive accessibility for any widget"""
    from src.utils.accessibility import get_accessibility_summary
    
    widget.setAccessibleName(name)
    if description:
        widget.setAccessibleDescription(description)
    
    # Set appropriate focus policy
    if role in [AccessibilityRole.BUTTON, AccessibilityRole.TEXT_INPUT]:
        widget.setFocusPolicy(Qt.TabFocus)
    
    # Enable keyboard navigation
    widget.setAttribute(Qt.WA_AcceptTouchEvents, True)
    
    # Log accessibility summary for debugging
    summary = get_accessibility_summary(widget)
    print(f"Accessibility setup for {widget.__class__.__name__}: {summary}")
```

## 3-Mode Compatibility

### Mode Detection and Adaptation

```python
from src.headless.mode_manager import ModeManager

class ComponentFactory:
    @staticmethod
    def create_button(text, **kwargs):
        """Create button with appropriate mode handling"""
        mode = ModeManager.get_current_mode()
        
        if mode == "dev":
            # Headless simulation mode
            return create_headless_button(text, **kwargs)
        elif mode == "dual":
            # Dual mode with synchronization
            return create_dual_mode_button(text, **kwargs)
        else:
            # Standard GUI mode
            return BaseButton(text, **kwargs)
    
    @staticmethod
    def create_input(placeholder, **kwargs):
        """Create input with mode-specific behavior"""
        mode = ModeManager.get_current_mode()
        
        input_widget = BaseInput(placeholder, **kwargs)
        
        if mode in ["dev", "dual"]:
            # Add headless compatibility
            input_widget.enable_headless_mode()
            
        return input_widget
```

### Cross-Mode Testing

```python
# Component testing across all three modes
def test_component_three_modes(component_class, test_data):
    """Test component functionality across DEV/DUAL/GUI modes"""
    
    # DEV Mode Test
    ModeManager.set_mode("dev")
    dev_component = component_class(**test_data)
    dev_results = run_headless_tests(dev_component)
    
    # DUAL Mode Test
    ModeManager.set_mode("dual") 
    dual_component = component_class(**test_data)
    dual_results = run_synchronization_tests(dual_component)
    
    # GUI Mode Test
    ModeManager.set_mode("gui")
    gui_component = component_class(**test_data)
    gui_results = run_production_tests(gui_component)
    
    return {
        'dev': dev_results,
        'dual': dual_results, 
        'gui': gui_results
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
    def apply_custom_theme(app, theme_name="light"):
        """Apply custom shadcn/ui inspired theme"""
        colors = COLORS_LIGHT if theme_name == "light" else COLORS_DARK
        app.setStyleSheet(generate_theme_stylesheet(colors))
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
    'spin': 'spin 1s linear infinite',
    'shimmer': 'shimmer 2s ease-in-out infinite',
}
```

### Loading States

```python
# Enhanced SkeletonLoader with multiple animation types
class SkeletonLoader(QWidget):
    """Skeleton loading animation for content"""
    
    ANIMATION_TYPES = {
        'shimmer': 'shimmer 2s ease-in-out infinite',
        'pulse': 'pulse 1.5s ease-in-out infinite',
        'wave': 'wave 2s linear infinite',
    }
    
    @classmethod
    def create_text_line(cls, width=200, height=16):
        return cls(width, height, animation='shimmer')
    
    @classmethod 
    def create_paragraph(cls, lines=3, line_height=16, spacing=8):
        container = QWidget()
        layout = QVBoxLayout(container)
        
        for i in range(lines):
            line_width = 200 if i < lines-1 else 150  # Last line shorter
            skeleton_line = cls(line_width, line_height, animation='shimmer')
            layout.addWidget(skeleton_line)
            
        return container
    
    @classmethod
    def create_card(cls, width=300, height=200):
        return cls(width, height, animation='shimmer')
```

## Migration Guide

### From Old Components to New Base Components

#### Button Migration

```python
# OLD - Direct QPushButton usage
old_button = QPushButton("Click Me")
old_button.setStyleSheet("background: blue; color: white;")

# NEW - BaseButton with variant system
new_button = BaseButton("Click Me", variant="default")
# or
new_button = BaseButton.create_primary("Click Me")
```

#### Input Migration

```python
# OLD - Direct QLineEdit usage
old_input = QLineEdit()
old_input.setPlaceholderText("Enter text...")
old_input.setStyleSheet("border: 1px solid gray;")

# NEW - BaseInput with state management
new_input = BaseInput("Enter text...")
new_input.set_state("error", "Please enter valid text")
```

#### Card Migration

```python
# OLD - Manual QFrame styling
old_card = QFrame()
old_card.setFrameStyle(QFrame.Box)
old_card.setStyleSheet("border: 1px solid gray; border-radius: 8px;")

# NEW - BaseCard with built-in styling
new_card = BaseCard()
new_card.set_header("Card Title")
```

### Accessibility Migration

```python
# OLD - No accessibility support
widget = QPushButton("Button")

# NEW - Full accessibility support
widget = BaseButton("Button")
widget.setAccessibleName("Action Button")
widget.setAccessibleDescription("Perform the main action")
```

### State Management Migration

```python
# OLD - Manual state handling
def set_input_error(widget, message):
    widget.setStyleSheet("border: 2px solid red;")
    # Manually create error label
    
# NEW - Built-in state management
input_widget = BaseInput("Email")
input_widget.set_state("error", "Invalid email format")
```

## Code Examples

### Complete Form Example

```python
from src.components.base import BaseButton, BaseCard, BaseInput, BaseSelect, BaseTextarea

class UserProfileForm(BaseCard):
    def __init__(self):
        super().__init__()
        self.setup_form()
        
    def setup_form(self):
        layout = QVBoxLayout(self)
        
        # Header
        self.set_header("User Profile")
        
        # Form fields
        self.name_input = BaseInput("Full Name")
        self.email_input = BaseInput.create_email("Email Address")
        self.role_select = BaseSelect("Select Role")
        self.role_select.add_option("Admin", "admin")
        self.role_select.add_option("User", "user")
        self.bio_textarea = BaseTextarea.create_description()
        
        # Buttons
        button_layout = QHBoxLayout()
        self.save_button = BaseButton.create_primary("Save")
        self.cancel_button = BaseButton.create_secondary("Cancel")
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        # Add to form
        form_layout = QVBoxLayout()
        form_layout.addWidget(self.name_input)
        form_layout.addWidget(self.email_input)
        form_layout.addWidget(self.role_select)
        form_layout.addWidget(self.bio_textarea)
        form_layout.addLayout(button_layout)
        
        self.add_content_layout(form_layout)
        
        # Connect signals
        self.save_button.clicked.connect(self.save_form)
        self.cancel_button.clicked.connect(self.cancel_form)
    
    def save_form(self):
        # Validate form
        if not self.validate_form():
            return
            
        # Show loading state
        self.save_button.set_loading(True)
        
        # Simulate API call
        QTimer.singleShot(2000, self.save_complete)
    
    def validate_form(self):
        valid = True
        
        if not self.name_input.text().strip():
            self.name_input.set_state("error", "Name is required")
            valid = False
        
        if not self.email_input.text().strip():
            self.email_input.set_state("error", "Email is required")
            valid = False
            
        return valid
    
    def save_complete(self):
        self.save_button.set_loading(False)
        # Show success state or close form
```

### Responsive Dashboard Example

```python
class DashboardLayout(ResponsiveThreePanel):
    def __init__(self):
        super().__init__()
        self.setup_panels()
        
    def setup_panels(self):
        # Left panel - Image viewer
        self.image_viewer = ImageViewerWidget()
        self.left_panel.setLayout(QVBoxLayout())
        self.left_panel.layout().addWidget(self.image_viewer)
        
        # Center panel - Data table
        self.data_table = Table()
        self.center_panel.setLayout(QVBoxLayout())
        self.center_panel.layout().addWidget(self.data_table)
        
        # Right panel - Logs and well plate
        right_layout = QVBoxLayout(self.right_panel)
        self.well_plate = WellPlateWidget()
        self.log_display = QTextEdit()
        
        right_layout.addWidget(self.well_plate, 1)
        right_layout.addWidget(self.log_display, 1)
        
        # Set minimum sizes to prevent collapse
        self.left_panel.setMinimumWidth(200)
        self.center_panel.setMinimumWidth(300)
        self.right_panel.setMinimumWidth(250)
```

This comprehensive design system provides a solid foundation for building consistent, accessible, and modern user interfaces in CellSorter while maintaining compatibility across all three operational modes (DEV/DUAL/GUI). 