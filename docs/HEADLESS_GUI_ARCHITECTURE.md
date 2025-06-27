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

### 2. Three Execution Modes

CellSorter supports three distinct execution modes to accommodate different development and usage scenarios:

#### GUI Mode (실제사용모드)
- **Purpose**: Production use by end users
- **Characteristics**:
  - Normal PySide6 QApplication instantiation
  - Full graphical interface
  - Interactive widgets and visual feedback
  - No headless components loaded
- **Command**: `python run.py --gui-mode`
- **Environment**: `export CELLSORTER_MODE=gui`

#### Dev Mode (디버깅모드 - Headless Only)
- **Purpose**: AI agents and headless development
- **Characteristics**:
  - No QApplication instantiation
  - UI definition as structured data (JSON/YAML)
  - Terminal-based interaction only
  - AI-friendly editing interface
- **Command**: `python run.py --dev-mode`
- **Environment**: `export CELLSORTER_MODE=dev`

#### Dual Mode (디버깅모드 - Both)
- **Purpose**: Real-time debugging and demonstration
- **Characteristics**:
  - Both QApplication and headless components active
  - Real-time synchronization between terminal and GUI
  - AI agent operations immediately visible in GUI
  - Perfect for watching AI work in real-time
- **Command**: `python run.py --dual-mode`
- **Environment**: `export CELLSORTER_MODE=dual`
- **특징**: 터미널에서 수행하는 모든 작업이 GUI에 실시간 반영

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
- In dual mode, handles bidirectional sync

#### Layer 3: Mode Manager
- Detects and manages execution mode
- Controls component initialization
- Manages synchronization in dual mode
- Provides mode-aware APIs

## Mode Detection and Initialization

```python
from headless.mode_manager import get_mode, AppMode, requires_gui, requires_headless

# Determine mode
mode = get_mode()

# Initialize appropriate components
if requires_gui():
    # Initialize GUI components
    app = QApplication(sys.argv)
    window = MainWindow()
    
if requires_headless():
    # Initialize headless components
    adapter = MainWindowAdapter()
    
if mode == AppMode.DUAL:
    # Connect for real-time sync
    adapter.connect_to_window(window)
```

## Dual Mode Architecture

### Real-Time Synchronization

In dual mode, a bidirectional bridge connects headless and GUI components:

```
┌─────────────────┐         ┌─────────────────┐
│ Headless Layer  │ <-----> │   GUI Layer     │
│                 │  Sync   │                 │
│ - UI Model      │         │ - QApplication  │
│ - Adapter       │         │ - MainWindow    │
│ - CLI Commands  │         │ - Widgets       │
└─────────────────┘         └─────────────────┘
```

### Event Flow in Dual Mode

1. **Headless → GUI**:
   ```python
   # AI agent executes command
   adapter.load_image("sample.tif")
   
   # Adapter updates internal state
   # Emits state change signal
   # GUI receives signal and updates display
   # Image appears in GUI immediately
   ```

2. **GUI → Headless**:
   ```python
   # User clicks button in GUI
   # GUI emits signal
   # Adapter receives signal
   # Updates internal state
   # Available for headless querying
   ```

### Synchronization Implementation

```python
class MainWindowAdapter:
    def connect_to_window(self, window):
        """Connect adapter to GUI window for dual mode."""
        self.window = window
        
        # Headless → GUI sync
        self.state.property_changed.connect(
            lambda prop, val: self._sync_to_gui(prop, val)
        )
        
        # GUI → Headless sync
        window.action_performed.connect(
            lambda action: self._sync_from_gui(action)
        )
```

## Implementation Examples

### Mode-Aware Widget Creation

```python
def create_button(name: str, text: str):
    if requires_gui():
        # Create actual QPushButton
        button = QPushButton(text)
        button.setObjectName(name)
        return button
        
    if requires_headless():
        # Create UI model representation
        return {
            "type": "QPushButton",
            "name": name,
            "properties": {"text": text}
        }
```

### Dual Mode Event Handling

```python
class DualModeHandler:
    def on_button_clicked(self):
        # Handle in headless
        if requires_headless():
            self.log_action("button_clicked")
            self.update_state()
        
        # Handle in GUI
        if requires_gui():
            self.show_dialog()
            self.update_display()
        
        # In dual mode, both paths execute
```

## Testing Strategy

### Mode-Specific Testing

1. **GUI Mode Tests**:
   ```bash
   CELLSORTER_MODE=gui pytest tests/gui/
   ```

2. **Dev Mode Tests**:
   ```bash
   CELLSORTER_MODE=dev pytest tests/headless/
   ```

3. **Dual Mode Tests**:
   ```bash
   CELLSORTER_MODE=dual pytest tests/integration/
   ```

### Dual Mode Integration Tests

```python
def test_dual_mode_sync():
    # Start in dual mode
    os.environ['CELLSORTER_MODE'] = 'dual'
    
    # Create components
    adapter = MainWindowAdapter()
    window = MainWindow()
    adapter.connect_to_window(window)
    
    # Test headless → GUI
    adapter.set_title("Test Title")
    assert window.windowTitle() == "Test Title"
    
    # Test GUI → headless
    window.load_image_signal.emit("test.tif")
    assert adapter.state.current_image == "test.tif"
```

## Best Practices

### 1. Always Check Mode

```python
# ✓ Good
if requires_gui():
    show_dialog()

# ✗ Bad
show_dialog()  # May fail in headless
```

### 2. Mode-Specific Imports

```python
# ✓ Good
if requires_gui():
    from PySide6.QtWidgets import QMessageBox
    
# ✗ Bad
from PySide6.QtWidgets import QMessageBox  # Fails in headless
```

### 3. Graceful Degradation

```python
def show_message(text: str):
    if requires_gui():
        QMessageBox.information(None, "Info", text)
    else:
        print(f"INFO: {text}")
```

## Configuration

### Environment Variables

```bash
# Set operation mode
export CELLSORTER_MODE=gui|dev|dual

# Legacy support
export CELLSORTER_DEV_MODE=true|false

# Force headless (overrides mode)
export CELLSORTER_FORCE_HEADLESS=true

# Debug synchronization
export CELLSORTER_SYNC_DEBUG=true
```

### Command Line Arguments

```bash
# Explicit mode selection
python run.py --gui-mode    # 실제사용모드
python run.py --dev-mode    # 디버깅모드 (headless)
python run.py --dual-mode   # 디버깅모드 (both)

# Mode with commands
python run.py --dual-mode dump-ui output.yaml
```

## Troubleshooting

### Common Issues

1. **"No display available" in GUI/Dual mode**:
   - Check DISPLAY environment variable
   - Verify X server is running
   - Use dev mode instead

2. **"QApplication instance already exists" in Dual mode**:
   - Ensure only one QApplication creation
   - Check for duplicate initialization

3. **"Synchronization lag" in Dual mode**:
   - Check event queue processing
   - Verify signal connections
   - Enable sync debugging

### Debug Commands

```bash
# Check current mode
python -c "from headless.mode_manager import get_mode_info; print(get_mode_info())"

# Test mode detection
python run.py --mode-info

# Enable sync debugging
export CELLSORTER_SYNC_DEBUG=true
python run.py --dual-mode
```

## Performance Considerations

### Dual Mode Overhead

- Synchronization adds ~5-10ms latency
- Memory usage increases by ~20%
- CPU usage minimal unless heavy UI updates

### Optimization Tips

1. Batch updates in dual mode
2. Use async operations for heavy tasks
3. Throttle rapid UI updates
4. Disable unused sync channels

## Future Enhancements

1. **Selective Synchronization**: Choose which components sync
2. **Recording/Playback**: Record headless sessions for GUI replay
3. **Remote Dual Mode**: Headless and GUI on different machines
4. **Performance Profiling**: Built-in sync performance metrics

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