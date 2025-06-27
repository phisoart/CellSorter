# Headless GUI Architecture for CellSorter

## Overview

This document describes the architecture for developing and maintaining PySide6-based GUI applications in headless environments, enabling AI agents and developers to work with the UI purely through code.

## Core Concepts

### 1. Display Detection System

The application detects at runtime whether a graphical display is available:

```python
def has_display():
    """Check if a display server is available."""
    if sys.platform == 'linux':
        return bool(os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY'))
    elif sys.platform == 'darwin':
        # macOS always has display
        return True
    elif sys.platform == 'win32':
        # Windows display detection
        return True  # Can be refined
    return False
```

### 2. Execution Modes

#### GUI Mode (dev-mode=false)
- Normal PySide6 QApplication instantiation
- Full graphical interface for end users
- Interactive widgets and visual feedback

#### Code Editing Mode (dev-mode=true)
- No QApplication instantiation
- UI definition as structured data (JSON/YAML)
- Terminal-based interaction
- AI-friendly editing interface

### 3. Three-Layer Architecture

#### Layer 1: UI Data Model
- Platform-agnostic UI representation
- Hierarchical widget definitions
- Properties, layouts, and event bindings
- No PySide6 dependencies

```python
ui_definition = {
    "type": "QMainWindow",
    "name": "mainWindow",
    "properties": {
        "windowTitle": "CellSorter",
        "geometry": [0, 0, 1200, 800]
    },
    "children": [
        {
            "type": "QWidget",
            "name": "centralWidget",
            "layout": {
                "type": "QVBoxLayout",
                "children": [...]
            }
        }
    ]
}
```

#### Layer 2: Rendering Engine
- Converts data model to PySide6 widgets
- Property application
- Signal/slot connections
- Layout management

#### Layer 3: Serialization System
- JSON/YAML export/import
- Round-trip editing support
- Version control friendly
- AI-parseable format

## UI Definition Schema

### Widget Definition
```yaml
type: string          # Widget class name (e.g., "QPushButton")
name: string          # Unique identifier (objectName)
properties:           # Widget-specific properties
  text: string
  enabled: boolean
  visible: boolean
  geometry: [x, y, width, height]
  styleSheet: string
  font:
    family: string
    size: integer
    bold: boolean
  color:
    foreground: string
    background: string
layout:               # Layout definition
  type: string
  properties:
    margin: integer
    spacing: integer
children: []          # Child widgets
events:               # Signal/slot connections
  - signal: string
    handler: string
```

### Layout Definition
```yaml
type: string          # Layout type (QVBoxLayout, QHBoxLayout, etc.)
properties:
  margin: integer
  spacing: integer
  alignment: string
children: []          # Widgets in layout
```

## Development Workflow

### 1. Headless Development
```bash
# Start in code editing mode
python run.py --dev-mode

# Output current UI definition
python run.py --dump-ui > ui_definition.yaml

# Load modified UI definition
python run.py --load-ui ui_definition.yaml

# Validate UI definition
python run.py --validate-ui ui_definition.yaml
```

### 2. AI-Assisted Editing
```bash
# AI can modify ui_definition.yaml
# Properties are clearly labeled
# Hierarchy is preserved
# Changes are trackable in git
```

### 3. GUI Preview
```bash
# Run with display to see changes
python run.py --dev-mode=false
```

## Implementation Strategy

### Phase 1: Core Infrastructure
1. Display detection system
2. Mode switching mechanism
3. Basic UI data model

### Phase 2: Serialization
1. JSON/YAML export
2. Import and validation
3. Schema definition

### Phase 3: Rendering Engine
1. Widget factory
2. Property application
3. Layout reconstruction
4. Event binding

### Phase 4: Developer Tools
1. CLI interface
2. Validation tools
3. Diff visualization
4. Migration utilities

## Benefits

### For AI Development
- Complete UI visibility in code
- Predictable modification patterns
- Version control integration
- Automated testing capability

### For Human Developers
- Work without display server
- Clear UI structure
- Easy collaboration
- Simplified debugging

### For CI/CD
- Headless testing
- Automated UI validation
- Performance benchmarking
- Regression detection

## Example Use Cases

### 1. AI Adding a Button
```yaml
# AI modifies ui_definition.yaml
- type: QPushButton
  name: newFeatureButton
  properties:
    text: "New Feature"
    enabled: true
  events:
    - signal: clicked
      handler: on_new_feature_clicked
```

### 2. Batch UI Updates
```python
# Script to update all button colors
ui_def = load_ui_definition('ui_definition.yaml')
for widget in find_widgets_by_type(ui_def, 'QPushButton'):
    widget['properties']['styleSheet'] = 'background-color: #3498db;'
save_ui_definition('ui_definition.yaml', ui_def)
```

### 3. UI Testing
```python
# Test UI structure without display
ui_def = load_ui_definition('ui_definition.yaml')
assert find_widget_by_name(ui_def, 'mainWindow') is not None
assert count_widgets_by_type(ui_def, 'QPushButton') == 5
```

## Migration Path

### From Current Architecture
1. Extract UI definitions from existing code
2. Create data model representations
3. Implement serialization layer
4. Add rendering engine
5. Enable mode switching

### Backwards Compatibility
- Existing PySide6 code remains functional
- Gradual migration of components
- Optional headless mode
- Preserves current functionality 