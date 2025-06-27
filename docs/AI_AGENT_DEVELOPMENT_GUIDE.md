# AI Agent Development Guide for CellSorter

This guide provides comprehensive instructions for AI agents to develop and modify the CellSorter GUI using the headless architecture system.

## Overview

CellSorter now supports a complete headless development environment that allows AI agents to:
- Develop GUI interfaces entirely through code and YAML definitions
- Work in terminal-only environments without display servers
- Make real-time UI modifications with instant preview
- Use natural language commands for UI operations
- Validate and test UI changes without GUI instantiation

## Architecture Components

### 1. Mode Management
- **Automatic detection**: System detects display availability
- **Dev mode**: `CELLSORTER_DEV_MODE=true` for headless development
- **GUI mode**: Traditional Qt interface when display is available
- **Force headless**: `CELLSORTER_FORCE_HEADLESS=true` for testing

### 2. UI Definition System
- **YAML format**: Human and AI-friendly UI definitions
- **JSON support**: Alternative structured format
- **Round-trip editing**: Modify YAML, see changes in GUI
- **Version control friendly**: Text-based definitions

### 3. Component Library
- **Base components**: Buttons, labels, inputs with CellSorter styling
- **Scientific widgets**: Specialized components for microscopy
- **Composition patterns**: Reusable component combinations
- **Theme variants**: Light/dark themes, compact modes

### 4. AI Integration Tools
- **Natural language parsing**: "Create a button named save"
- **Command suggestions**: AI-friendly error messages
- **Batch operations**: Modify multiple widgets at once
- **Change validation**: Prevent breaking changes

## Getting Started

### 1. Environment Setup
```bash
# Enable dev mode
export CELLSORTER_DEV_MODE=true

# Start in headless mode
python run.py --headless

# Or use CLI directly
python -m src.headless.cli.cli_commands
```

### 2. Basic UI Operations

#### Export Current UI
```bash
python -m src.headless.cli.cli_commands model export ui_current.yaml
```

#### Import UI Definition
```bash
python -m src.headless.cli.cli_commands model import ui_definitions/main_window.yaml
```

#### Validate UI
```bash
python -m src.headless.cli.cli_commands model validate ui_definitions/main_window.yaml --strict
```

### 3. Natural Language Commands

The AI command parser supports intuitive commands:

```python
from src.headless.ai_tools import AICommandParser

parser = AICommandParser()

# Widget search
commands = parser.parse("find widget named scatter_plot")

# Property modification  
commands = parser.parse("set title of main_window to 'CellSorter v2.1'")

# Widget creation
commands = parser.parse("create button widget named export_btn")

# Batch operations
commands = parser.parse("batch hide all buttons in toolbar")
```

## UI Definition Structure

### Main Window Definition
```yaml
# ui_definitions/main_window.yaml
name: "MainWindow"
type: "QMainWindow"
title: "CellSorter - 2.0.0"

properties:
  windowTitle: "CellSorter - 2.0.0"
  centralWidget:
    type: "QWidget"
    layout:
      type: "QHBoxLayout"
      children:
        - type: "ImageHandler"
          name: "image_handler"
        - type: "ScatterPlotWidget"  
          name: "scatter_plot_widget"
        - type: "SelectionPanel"
          name: "selection_panel"

menuBar:
  type: "QMenuBar"
  menus:
    - name: "File"
      text: "&File"
      actions:
        - name: "action_open_image"
          text: "Open &Image..."
          shortcut: "Ctrl+O"
```

### Component Usage
```yaml
# Use predefined components
button_save:
  extends: "primary_button"
  properties:
    text: "Save Session"
    objectName: "btn_save"

# Custom styling
custom_label:
  type: "QLabel"
  properties:
    text: "Cell Count: 0"
    styleSheet: |
      QLabel {
        color: #0066cc;
        font-weight: bold;
      }
```

## Development Workflows

### 1. Interactive Development
```bash
# Start file watcher for live reload
python -c "
from src.headless.sync.watcher import create_ui_watcher
from pathlib import Path

watcher = create_ui_watcher(Path('.'))
watcher.add_callback('modified', lambda e: print(f'UI changed: {e.file_path}'))
watcher.start()
"
```

### 2. AI-Driven Modifications
```python
from src.headless.ai_tools import AIUIAssistant

assistant = AIUIAssistant()

# Natural language UI modification
result = assistant.process_command(
    "Add a progress bar to the bottom of the main window"
)

# Validate changes
validation = assistant.validate_current_ui()
if validation.is_valid:
    assistant.apply_changes()
```

### 3. Testing Without Display
```python
from src.headless.testing import HeadlessTestFramework

# Test UI structure
framework = HeadlessTestFramework()
framework.load_ui_definition("ui_definitions/main_window.yaml")

# Validate widget hierarchy
assert framework.find_widget("scatter_plot_widget") is not None
assert framework.get_property("main_window", "windowTitle") == "CellSorter - 2.0.0"

# Test events and signals
framework.trigger_action("action_open_image")
assert framework.last_signal == "open_image_requested"
```

## Command Reference

### CLI Commands
```bash
# Session management
cellsorter session create my_session
cellsorter session load session.json
cellsorter session save output.json

# UI model operations
cellsorter model export ui.yaml --format yaml
cellsorter model import ui.yaml
cellsorter model validate ui.yaml --strict

# Real-time development
cellsorter watch start --auto-reload
cellsorter mode-info
```

### Python API
```python
from src.headless import (
    HeadlessSessionManager,
    UIFileWatcher,
    AICommandParser,
    MainWindowAdapter
)

# Initialize headless session
session_manager = HeadlessSessionManager()
session = session_manager.create_new_session("dev_session")

# Load UI from definition
adapter = MainWindowAdapter()
ui_model = adapter.load_from_yaml("ui_definitions/main_window.yaml")

# Apply changes
ui_model.set_property("main_window", "windowTitle", "Modified Title")
adapter.save_to_yaml(ui_model, "modified_ui.yaml")
```

## Best Practices

### 1. Structure Organization
```
ui_definitions/
├── main_window.yaml          # Main application window
├── components/
│   ├── base_components.yaml  # Reusable components
│   └── dialogs/
│       ├── calibration.yaml  # Specific dialogs
│       └── export.yaml
└── themes/
    ├── light.yaml            # Theme definitions
    └── dark.yaml
```

### 2. Component Reuse
```yaml
# Define once, use everywhere
standard_button:
  type: "QPushButton"
  properties:
    minimumHeight: 32
    styleSheet: "/* CellSorter standard button style */"

# Reference in definitions
my_button:
  extends: "standard_button"
  properties:
    text: "My Action"
```

### 3. Change Validation
Always validate changes before applying:
```python
# Check if change is safe
validator = ChangeValidator()
is_safe = validator.validate_property_change(
    widget="main_window", 
    property="windowTitle", 
    new_value="New Title"
)

if is_safe:
    apply_change()
else:
    print("Change would break UI compatibility")
```

### 4. Error Handling
```python
try:
    result = parser.parse("invalid command syntax")
    if result[0].command_type == CommandType.VALIDATION:
        suggestions = result[0].parameters["suggestions"]
        print("Suggestions:", suggestions)
except Exception as e:
    logger.error(f"Command parsing failed: {e}")
```

## Advanced Features

### 1. Real-time Synchronization
```python
# Bidirectional sync between code and UI
from src.headless.sync import create_ui_watcher

watcher = create_ui_watcher(project_root)
watcher.add_callback('modified', reload_ui_definition)
watcher.start()

# Changes to YAML files automatically update GUI
```

### 2. Batch Operations
```python
from src.headless.ai_tools import BatchOperations

batch = BatchOperations()
batch.add_operation("hide", ["button1", "button2", "button3"])
batch.add_operation("set_property", {
    "target": "all_labels",
    "property": "styleSheet", 
    "value": "color: blue;"
})
batch.execute()
```

### 3. Template System
```yaml
# templates/dialog_template.yaml
template:
  type: "QDialog"
  properties:
    modal: true
    minimumSize: [400, 300]
  layout:
    type: "QVBoxLayout"
    children:
      - type: "dialog_content"  # Placeholder
      - type: "dialog_buttons"
        
# Use template
my_dialog:
  extends: "dialog_template"
  dialog_content:
    type: "QLabel"
    text: "Custom dialog content"
```

## Troubleshooting

### Common Issues

1. **Display Detection Problems**
   ```bash
   # Force headless mode
   export CELLSORTER_FORCE_HEADLESS=true
   
   # Check detection status
   python -c "from src.headless.display_detector import get_display_info; print(get_display_info())"
   ```

2. **YAML Syntax Errors**
   ```bash
   # Validate YAML syntax
   python -c "import yaml; yaml.safe_load(open('ui_definitions/main_window.yaml'))"
   ```

3. **Import/Export Issues**
   ```bash
   # Test serialization round-trip
   cellsorter model export test.yaml
   cellsorter model validate test.yaml --strict
   cellsorter model import test.yaml
   ```

### Debug Mode
```bash
# Enable verbose logging
export CELLSORTER_LOG_LEVEL=DEBUG
python run.py --headless
```

## Integration Examples

### Example 1: Add New Menu Item
```yaml
# In main_window.yaml, add to menuBar.menus[0].actions:
- name: "action_new_feature"
  text: "New &Feature..."
  shortcut: "Ctrl+N"
  statusTip: "Access new feature"
  enabled: true
```

### Example 2: Create Custom Dialog
```yaml
# ui_definitions/dialogs/custom_dialog.yaml
name: "CustomDialog"
type: "QDialog"
properties:
  windowTitle: "Custom Dialog"
  modal: true
  geometry: [100, 100, 400, 300]

layout:
  type: "QVBoxLayout"
  children:
    - extends: "title_label"
      properties:
        text: "Dialog Title"
    
    - extends: "text_input"
      properties:
        objectName: "input_value"
        placeholderText: "Enter value..."
    
    - extends: "dialog_buttons"
```

### Example 3: Modify Existing Component
```python
# AI agent command
command = "set background color of scatter_plot_widget to light gray"
result = parser.parse(command)

# Translates to:
ui_model.set_property(
    "scatter_plot_widget", 
    "styleSheet", 
    "background-color: #f8f9fa;"
)
```

This headless architecture enables AI agents to develop sophisticated GUIs entirely through code, making CellSorter development more accessible and efficient for automated development workflows.