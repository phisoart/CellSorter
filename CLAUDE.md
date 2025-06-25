# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development Setup
```bash
# Activate the cellsorter conda environment (ALWAYS do this first)
conda activate cellsorter

# Install dependencies
pip install -r requirements.txt

# Run the application
python src/main.py
```

### Testing
```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit
pytest -m gui
pytest -m integration

# Run with coverage
pytest --cov=src --cov-report=html

# Run performance tests
pytest -m performance --benchmark-only

# Run tests matching pattern
pytest -k "test_image_loader"
```

### Code Quality
```bash
# Format code with Black
black src/ tests/

# Check formatting without changes
black --check src/ tests/

# Run linting
flake8 src/ tests/

# Type checking
mypy src/

# Generate documentation
sphinx-build -b html docs/ docs/_build/
```

## Architecture Overview

CellSorter is a PySide6-based GUI application for advanced cell sorting and tissue extraction, designed to work with CosmoSort hardware. The application processes microscopy images and CellProfiler CSV data to enable precise cell selection and coordinate transformation.

### Core Components

1. **GUI Controller** (`src/pages/main_window.py`): Main application window, menu system, component orchestration
2. **Image Handler** (`src/models/image_handler.py`): Multi-format image loading (TIFF/JPG/JPEG/PNG), overlay management, coordinate tracking
3. **CSV Parser** (`src/models/csv_parser.py`): CellProfiler CSV validation, feature extraction, bounding box extraction
4. **Scatter Plot View** (`src/components/widgets/scatter_plot.py`): Interactive matplotlib plots, rectangle selection tool
5. **Selection Manager** (`src/models/selection_manager.py`): Cell selection state, color assignment, 96-well plate mapping
6. **Coordinate Transformer** (`src/models/coordinate_transformer.py`): Two-point calibration, affine transformation, pixel-to-stage conversion
7. **Extractor** (`src/models/extractor.py`): Square crop calculation, .cxprotocol file generation

### Data Flow
```
[Microscopy Image] ──┐
                     ├──► [CellSorter GUI] ──► [.cxprotocol] ──► [CosmoSort Hardware]
[CellProfiler CSV] ──┘
```

### Key Design Principles
- **Cross-platform compatibility**: Works on Windows and macOS
- **Test-Driven Development (TDD)**: All features start with tests
- **Real-time feedback**: Progressive loading, responsive UI
- **Modular architecture**: Clear separation between GUI, data processing, and export logic

## Development Guidelines

### Environment Management
- **ALWAYS activate the cellsorter conda environment before any work**:
  ```bash
  conda activate cellsorter
  ```
- Verify environment is active before running commands
- Update requirements.txt when packages change:
  ```bash
  pip freeze > requirements.txt
  ```

### Code Style
- Follow PEP 8 standards
- Use Black formatter (88 character line length)
- Type hints for all public functions
- Google-style docstrings
- Naming conventions:
  - `PascalCase` for classes
  - `snake_case` for functions and variables
  - `UPPER_SNAKE_CASE` for constants
  - Prefix private members with underscore `_`

### Testing Requirements
- Write tests FIRST (TDD approach)
- Minimum 85% code coverage
- Test categories:
  - Unit tests: Business logic, utilities
  - GUI tests: PySide6 widgets using pytest-qt
  - Integration tests: End-to-end workflows
  - Performance tests: Large dataset handling
- All tests must pass before merging code

### Project Structure
```
src/
├── components/     # Reusable UI components
├── pages/         # Main application screens
├── models/        # Data models and business logic
├── utils/         # Utility functions
├── config/        # Configuration files
├── assets/        # Icons, images, static files
└── main.py        # Application entry point
```

### File Format Support
- **Images**: TIFF, JPG, JPEG, PNG
- **Data**: CellProfiler CSV format with required bounding box columns
- **Export**: .cxprotocol INI-style format for CosmoSort

### Coordinate System
- Two-point calibration for pixel-to-stage transformation
- Affine transformation matrix calculation
- Real-time validation and error checking

## Important Notes

1. **Cross-platform**: Use `pathlib` for file operations, handle platform-specific behavior explicitly
2. **Memory management**: Efficient handling of large images and datasets
3. **Error handling**: Graceful degradation with informative user messages
4. **No network operations**: All processing is local for data security
5. **Session management**: Support for saving/restoring analysis sessions
6. **Batch processing**: Handle multiple samples with consistent criteria

## Development Workflow

1. Activate cellsorter environment
2. Write failing test for new feature
3. Implement feature to pass test
4. Run full test suite
5. Format code with Black
6. Run linting and type checking
7. Update documentation if needed
8. Commit with conventional commit message format