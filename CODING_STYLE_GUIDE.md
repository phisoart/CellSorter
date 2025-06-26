# Coding Style Guide

This document outlines the coding standards and conventions for the CellSorter PySide6 application.

## Table of Contents

1. [General Python Style](#general-python-style)
2. [PySide6/Qt Specific Guidelines](#pyside6qt-specific-guidelines)
3. [Project Structure](#project-structure)
4. [Naming Conventions](#naming-conventions)
5. [File Organization](#file-organization)
6. [Documentation](#documentation)
7. [Error Handling](#error-handling)
8. [Testing](#testing)
9. [Import Organization](#import-organization)
10. [Code Formatting](#code-formatting)

## General Python Style

### Base Standards
- Follow [PEP 8](https://pep8.org/) for general Python coding style
- Use 4 spaces for indentation (no tabs)
- Line length: 88 characters (Black formatter standard)
- Use double quotes for strings by default
- Use trailing commas in multi-line structures

### Type Hints
- Use type hints for all public functions and methods
- Import types from `typing` module when needed
- Use `Optional[T]` for nullable types

```python
from typing import Optional, List, Dict, Any
from PySide6.QtWidgets import QWidget

def process_cells(data: List[Dict[str, Any]], 
                 threshold: Optional[float] = None) -> bool:
    """Process cell data with optional threshold."""
    pass
```

## PySide6/Qt Specific Guidelines

### Widget Classes
- Inherit from appropriate Qt base classes
- Use descriptive class names ending with the widget type
- Initialize UI in `__init__` or separate `setup_ui()` method

```python
class CellSorterMainWindow(QMainWindow):
    """Main application window for cell sorting."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self) -> None:
        """Initialize the user interface."""
        pass
    
    def connect_signals(self) -> None:
        """Connect signals to their respective slots."""
        pass
```

### Signal and Slot Naming
- Use descriptive names for custom signals
- Prefix slot methods with `on_` or `handle_`
- Use snake_case for signal and slot names

```python
from PySide6.QtCore import Signal

class CellProcessor(QObject):
    # Signals
    processing_started = Signal()
    processing_finished = Signal(bool)  # success status
    progress_updated = Signal(int)      # percentage
    
    def on_start_button_clicked(self) -> None:
        """Handle start button click."""
        pass
    
    def handle_processing_error(self, error: str) -> None:
        """Handle processing errors."""
        pass
```

### UI File Integration
- When using `.ui` files, load them in a consistent manner
- Keep UI logic separate from business logic

```python
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile

class FormWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.load_ui()
    
    def load_ui(self) -> None:
        """Load UI from .ui file."""
        ui_file = QFile("forms/cell_form.ui")
        ui_file.open(QFile.ReadOnly)
        
        loader = QUiLoader()
        self.ui = loader.load(ui_file, self)
        ui_file.close()
```

## Project Structure

### Directory Organization
```
src/
├── components/          # Reusable UI components
│   ├── __init__.py
│   ├── base/           # Base component classes
│   ├── dialogs/        # Custom dialogs
│   └── widgets/        # Custom widgets
├── pages/              # Main application pages/windows
├── models/             # Data models and business logic
├── utils/              # Utility functions and helpers
├── resources/          # Qt resource files (.qrc)
├── assets/             # Static assets (icons, images)
└── config/             # Configuration files
```

### File Naming
- Use snake_case for Python files
- Use PascalCase for class names
- Use descriptive names that indicate purpose

```
# Good
cell_sorter_widget.py
image_processor.py
main_window.py

# Bad
widget1.py
processor.py
window.py
```

## Naming Conventions

### Classes
```python
# Widget classes
class CellSorterWidget(QWidget): pass
class ImageViewerDialog(QDialog): pass
class ProcessingProgressBar(QProgressBar): pass

# Model classes
class CellDataModel(QAbstractTableModel): pass
class ImageModel: pass

# Utility classes
class ImageProcessor: pass
class DataExporter: pass
```

### Variables and Functions
```python
# Variables
cell_count = 0
selected_cells = []
processing_status = False

# Functions
def load_image_data() -> None: pass
def process_cell_selection() -> bool: pass
def export_results_to_csv() -> None: pass

# Private methods (prefix with underscore)
def _validate_input_data(self) -> bool: pass
def _setup_internal_connections(self) -> None: pass
```

### Constants
```python
# Use UPPER_CASE for constants
DEFAULT_CELL_SIZE = 50
MAX_PROCESSING_THREADS = 4
SUPPORTED_IMAGE_FORMATS = ['.png', '.jpg', '.tiff']

# Group related constants in classes
class Colors:
    PRIMARY = "#2196F3"
    SECONDARY = "#FFC107"
    SUCCESS = "#4CAF50"
    ERROR = "#F44336"
```

## File Organization

### Import Order
1. Standard library imports
2. Third-party imports
3. PySide6/Qt imports
4. Local application imports

```python
# Standard library
import os
import sys
from pathlib import Path
from typing import Optional, List

# Third-party
import numpy as np
import cv2

# PySide6/Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QPixmap, QIcon

# Local imports
from .models.cell_model import CellModel
from .utils.image_processor import ImageProcessor
from .components.dialogs.settings_dialog import SettingsDialog
```

### Class Structure Order
```python
class ExampleWidget(QWidget):
    # 1. Class-level constants
    DEFAULT_SIZE = (800, 600)
    
    # 2. Signals
    data_changed = Signal(dict)
    
    def __init__(self, parent=None):
        # 3. Constructor
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()
    
    # 4. Properties
    @property
    def current_data(self) -> dict:
        return self._data
    
    # 5. Public methods
    def load_data(self, file_path: str) -> bool:
        pass
    
    def save_data(self, file_path: str) -> bool:
        pass
    
    # 6. Slots (event handlers)
    @Slot()
    def on_button_clicked(self) -> None:
        pass
    
    # 7. Private methods
    def _setup_ui(self) -> None:
        pass
    
    def _connect_signals(self) -> None:
        pass
```

## Documentation

### Docstrings
Use Google-style docstrings for all public methods and classes:

```python
class CellAnalyzer:
    """Analyzes cell data and provides sorting functionality.
    
    This class handles the core cell analysis logic including
    detection, classification, and sorting operations.
    
    Attributes:
        cell_data: List of cell objects to analyze
        threshold: Detection threshold value
    """
    
    def analyze_cells(self, image_data: np.ndarray, 
                     parameters: dict) -> List[dict]:
        """Analyze cells in the provided image data.
        
        Args:
            image_data: Input image as numpy array
            parameters: Analysis parameters including threshold,
                       minimum size, etc.
        
        Returns:
            List of dictionaries containing cell information
            including position, size, and classification.
        
        Raises:
            ValueError: If image_data is empty or invalid
            ProcessingError: If analysis fails
        """
        pass
```

### Comments
- Use inline comments sparingly, prefer self-documenting code
- Add comments for complex algorithms or non-obvious logic

```python
def process_image(self, image: np.ndarray) -> dict:
    # Apply Gaussian blur to reduce noise before detection
    blurred = cv2.GaussianBlur(image, (5, 5), 0)
    
    # Complex morphological operations for cell detection
    # Based on research paper: "Advanced Cell Detection Methods"
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    processed = cv2.morphologyEx(blurred, cv2.MORPH_OPEN, kernel)
    
    return self._extract_cell_features(processed)
```

## Error Handling

### Exception Handling
```python
from PySide6.QtWidgets import QMessageBox
import logging

logger = logging.getLogger(__name__)

class CellProcessor:
    def process_data(self, file_path: str) -> bool:
        """Process cell data from file."""
        try:
            data = self._load_data(file_path)
            result = self._analyze_data(data)
            return True
            
        except FileNotFoundError:
            error_msg = f"File not found: {file_path}"
            logger.error(error_msg)
            self._show_error_dialog("File Error", error_msg)
            return False
            
        except ValueError as e:
            error_msg = f"Invalid data format: {str(e)}"
            logger.error(error_msg)
            self._show_error_dialog("Data Error", error_msg)
            return False
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.exception("Unexpected error during processing")
            self._show_error_dialog("Processing Error", error_msg)
            return False
    
    def _show_error_dialog(self, title: str, message: str) -> None:
        """Show error dialog to user."""
        msg_box = QMessageBox(QMessageBox.Critical, title, message)
        msg_box.exec()
```

## Testing

### Test File Naming
- Test files should mirror the source structure
- Prefix test files with `test_`
- Use descriptive test method names

```python
# tests/test_cell_processor.py
import pytest
from unittest.mock import Mock, patch
from src.models.cell_processor import CellProcessor

class TestCellProcessor:
    """Test cases for CellProcessor class."""
    
    def test_process_valid_data_returns_true(self):
        """Test that processing valid data returns True."""
        processor = CellProcessor()
        result = processor.process_data("valid_data.csv")
        assert result is True
    
    def test_process_nonexistent_file_returns_false(self):
        """Test that processing non-existent file returns False."""
        processor = CellProcessor()
        result = processor.process_data("nonexistent.csv")
        assert result is False
    
    @patch('src.models.cell_processor.cv2')
    def test_image_processing_with_mock(self, mock_cv2):
        """Test image processing with mocked OpenCV."""
        mock_cv2.imread.return_value = Mock()
        processor = CellProcessor()
        result = processor.process_image("test.jpg")
        assert result is not None
```

## Code Formatting

### Automated Formatting
Use Black for code formatting:

```bash
# Format all Python files
black src/ tests/

# Check formatting without changes
black --check src/ tests/
```

### Line Breaking
```python
# Good: Break long function calls
result = self.image_processor.analyze_cells(
    image_data=loaded_image,
    threshold=self.detection_threshold,
    min_size=self.min_cell_size,
    max_size=self.max_cell_size
)

# Good: Break long conditional statements
if (self.processing_enabled and 
    self.has_valid_data() and 
    not self.is_processing_running()):
    self.start_processing()

# Good: Multi-line list/dict definitions
supported_formats = [
    '.png', '.jpg', '.jpeg',
    '.tiff', '.tif', '.bmp'
]

config = {
    'threshold': 0.5,
    'min_size': 10,
    'max_size': 1000,
    'enable_filtering': True
}
```

### String Formatting
Prefer f-strings for string formatting:

```python
# Good
filename = f"processed_cells_{timestamp}.csv"
error_msg = f"Failed to process {file_count} files"

# Acceptable for logging with lazy evaluation
logger.info("Processing file %s with threshold %f", filename, threshold)

# Avoid
error_msg = "Failed to process {} files".format(file_count)
error_msg = "Failed to process " + str(file_count) + " files"
```

---

## Tools and Enforcement

### Recommended Tools
- **Black**: Code formatting (requirements-dev.txt)
- **flake8**: Linting and style checking (requirements-dev.txt)
- **mypy**: Type checking (requirements-dev.txt)
- **pytest**: Testing framework (requirements-dev.txt)
- **pytest-qt**: Qt testing utilities (requirements-dev.txt)
- **pyinstaller**: Build/deployment (requirements-build.txt)

### Pre-commit Hooks
- 개발/테스트/코드 품질 도구는 requirements-dev.txt에, 빌드/배포 도구는 requirements-build.txt에 분리 관리합니다.

## Collaboration Notes
- 본 프로젝트는 별도의 CONTRIBUTING.md, RELEASE_PLAN.md 파일을 생성하지 않으며, 관련 규칙은 README.md 및 기타 문서에 통합되어 관리됩니다.

Following these guidelines will ensure consistent, maintainable, and readable code across the CellSorter project. 