# Testing Strategy

## 1. Mandatory Headless Testing Philosophy

### CRITICAL: All tests MUST run in headless mode
- **NEVER show GUI during testing unless explicitly specified**
- **ALL UI tests MUST work without display server**
- **Use virtual display (Xvfb) or `--headless` flag for any GUI testing**
- **MUST test ALL user interactions (clicks, drags, keyboard) in terminal mode**

### Test-Driven Development (TDD) with Interactive Simulation
We follow a **Test-Driven Development (TDD)** approach enhanced with comprehensive UI interaction testing.
- Every feature starts with a failing test that includes UI interaction simulation.
- Tests drive design and modularity while ensuring headless compatibility.
- All production code is written to make a test pass in headless environment.
- **MANDATORY**: Every UI test must simulate real user interactions without display.

## 2. Test Types

### 2.1 Unit Tests
- Target: Business logic, utility functions, non-GUI modules
- Framework: `pytest`
- Location: `tests/unit/`

#### Key Unit Test Areas:
- **Image Processing**: Test image loading, validation, and format conversion
- **CSV Parsing**: Validate CellProfiler data parsing and column validation
- **Coordinate Transformation**: Test affine transformation calculations
- **Data Models**: Test cell selection, bounding box calculations
- **Export Logic**: Test .cxprotocol file generation and validation

### 2.2 Headless GUI Component Tests
- Target: Individual PySide6 widgets and dialogs **WITHOUT display**
- Tool: `pytest-qt`, `pytest` with `--headless` flag
- Strategy: Use `QTest` or `qtbot` for interaction simulation in virtual environment
- Location: `tests/gui/`
- **CRITICAL**: All GUI tests MUST run without showing actual windows

#### Mandatory Interactive Test Scenarios:
- **All Clicks**: Test every button, menu item, toolbar action
- **All Drags**: Test drag-and-drop, slider movement, splitter resizing
- **Keyboard Navigation**: Test Tab navigation, shortcuts, text input
- **Mouse Gestures**: Test double-click, right-click, hover effects
- **User Workflows**: Test complete interaction sequences headlessly

#### GUI Test Examples:
```python
def test_scatter_plot_all_interactions(qtbot):
    \"\"\"Test ALL scatter plot interactions in headless mode\"\"\"
    widget = ScatterPlotWidget()
    qtbot.addWidget(widget)  # No window shown
    
    # Test all clicks
    qtbot.mouseClick(widget.zoom_button, QtCore.Qt.LeftButton)
    qtbot.mouseClick(widget.reset_button, QtCore.Qt.LeftButton)
    
    # Test all drags
    qtbot.mouseDrag(widget.plot_area, QtCore.QPoint(10, 10), QtCore.QPoint(50, 50))
    
    # Test keyboard navigation
    qtbot.keyPress(widget, QtCore.Qt.Key_Tab)
    qtbot.keyPress(widget, QtCore.Qt.Key_Enter)
```

### 2.3 Integration Tests
- Target: End-to-end workflows involving multiple components
- Tool: `pytest`, with optional custom headless setup
- Strategy: Mimic user behavior (e.g. open image → process → export)
- Location: `tests/integration/`

#### Integration Test Workflows:
1. **Complete Analysis Workflow**:
   - Load microscopy image and CSV data
   - Generate scatter plot visualization
   - Perform cell selection via rectangle tool
   - Execute coordinate calibration
   - Export .cxprotocol file
   - Validate output integrity

2. **Batch Processing Workflow**:
   - Process multiple image/CSV pairs
   - Apply consistent selection criteria
   - Validate coordinate transformation accuracy
   - Test export file naming and organization

3. **Error Recovery Scenarios**:
   - Invalid file format handling
   - Corrupted CSV data processing
   - Failed calibration recovery
   - Memory management under large datasets

### 2.4 Performance Tests
- Target: Large dataset handling and memory management
- Tool: `pytest-benchmark`, custom memory profilers
- Focus Areas:
  - Image loading performance (>50MB TIFF files)
  - CSV processing speed (>10,000 cell records)
  - UI responsiveness during heavy operations
  - Memory usage optimization

### 2.5 Regression Tests
- Every resolved bug must have a test that reproduces the issue and verifies the fix.
- Marked with `@pytest.mark.regression`

## 3. Test Naming and Structure
- All test files: `test_*.py`
- Test methods: `test_[functionality]_[expected_behavior]`
- Example: `test_image_loader_handles_jpeg.py`

### Test File Organization:
```
tests/
├── unit/
│   ├── test_csv_parser.py
│   ├── test_coordinate_transformer.py
│   ├── test_image_handler.py
│   └── test_selection_manager.py
├── gui/
│   ├── test_scatter_plot_widget.py
│   ├── test_image_viewer_widget.py
│   ├── test_main_window.py
│   └── test_dialogs.py
├── integration/
│   ├── test_complete_workflow.py
│   ├── test_batch_processing.py
│   └── test_error_recovery.py
├── fixtures/
│   ├── sample_images/
│   ├── sample_csv_data/
│   └── expected_outputs/
└── conftest.py
```

## 4. Test Data Management

### 4.1 Test Fixtures
- **Sample Images**: TIFF, JPG, PNG files of varying sizes
- **CellProfiler CSV**: Valid and invalid data samples
- **Expected Outputs**: Reference .cxprotocol files
- **Mock Data**: Synthetic datasets for edge case testing

### 4.2 Data Generation
- Automated generation of test CSV data with known characteristics
- Programmatic creation of test images with controlled properties
- Mock CosmoSort hardware responses for integration testing

## 5. Test Execution Strategy

### 5.1 Test Categories
- **Smoke Tests**: Quick validation of core functionality
- **Critical Path Tests**: Essential user workflows
- **Edge Case Tests**: Boundary conditions and error scenarios
- **Performance Tests**: Speed and memory benchmarks

### 5.2 Test Markers
```python
@pytest.mark.unit          # Unit tests
@pytest.mark.gui           # GUI tests requiring Qt
@pytest.mark.integration   # Integration tests
@pytest.mark.performance   # Performance benchmarks
@pytest.mark.regression    # Regression tests
@pytest.mark.slow          # Long-running tests
```

## 6. Coverage Requirements
- **Minimum**: 85% line coverage, with focus on core logic
- **Target Areas**: 
  - Business logic: >90% coverage
  - GUI components: >80% coverage
  - Utility functions: >95% coverage
- **Tool**: `coverage.py`, integrated with `pytest-cov`

### Coverage Exclusions:
- GUI event loops and Qt-specific boilerplate
- Development/debugging utilities
- Platform-specific error handling

## 7. Mocking Strategy

### 7.1 External Dependencies
- **File System**: Mock file operations for consistent testing
- **CosmoSort Hardware**: Mock device communication
- **Heavy Computations**: Mock complex image processing operations

### 7.2 GUI Dependencies
- **Qt Widgets**: Use `qtbot` fixtures for widget testing
- **File Dialogs**: Mock file selection dialogs
- **System Dialogs**: Mock platform-specific dialogs

## 8. Continuous Testing

### 8.1 Automated Testing
- **Tool**: GitHub Actions
- **Triggers**: Push to main, pull requests, scheduled runs
- **Platforms**: Windows 10/11, macOS (latest 2 versions)
- **Python Versions**: 3.11, 3.12

### 8.2 Test Pipeline
```yaml
1. Code Quality Checks:
   - Black formatting
   - flake8 linting
   - mypy type checking

2. Unit Tests:
   - Run all unit tests
   - Generate coverage report

3. GUI Tests:
   - Run Qt-dependent tests
   - Test on virtual display (Linux/CI)

4. Integration Tests:
   - Execute complete workflows
   - Validate output files

5. Performance Tests:
   - Run benchmark suite
   - Compare against baselines
```

### 8.3 Test Reports
- Coverage reports uploaded to Codecov
- Performance benchmarks tracked over time
- Failed test notifications via GitHub Issues

## 9. Local Development Testing

### 9.1 Pre-commit Testing
- Run relevant test subset based on changed files
- Fast feedback loop for developers
- Integration with pre-commit hooks

### 9.2 Development Commands
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

## 10. Test Quality Assurance

### 10.1 Test Review Process
- All new tests require code review
- Test coverage must not decrease
- Performance tests must include baseline comparison

### 10.2 Test Maintenance
- Regular review of test suite performance
- Periodic cleanup of obsolete tests
- Update test data to reflect real-world usage

## Collaboration Notes
- This project does not create separate CONTRIBUTING.md or RELEASE_PLAN.md files; related rules are integrated and managed in README.md and other documents.

This comprehensive testing strategy ensures robust, reliable software that meets the demanding requirements of pathology research applications.

# CellSorter Testing Strategy

## Overview

This document outlines the comprehensive testing strategy for the CellSorter application, including unit tests, integration tests, and end-to-end tests across all three operation modes.

## Three Mode Testing Strategy

CellSorter supports three distinct operation modes, each requiring specific testing approaches:

### 1. GUI Mode Testing (Production Mode)
**Environment**: `CELLSORTER_MODE=gui`
```bash
# Run GUI mode tests
CELLSORTER_MODE=gui pytest tests/gui/
```

**Focus Areas**:
- Widget rendering and display
- User interaction responses
- Visual feedback correctness
- GUI-specific features

**Requirements**:
- Display server available
- PySide6 properly installed
- Visual regression tests

### 2. Dev Mode Testing (Debug Mode - Headless Only)
**Environment**: `CELLSORTER_MODE=dev`
```bash
# Run headless mode tests
CELLSORTER_MODE=dev pytest tests/headless/
```

**Focus Areas**:
- UI model manipulation
- Serialization/deserialization
- Command processing
- No display dependencies

**Requirements**:
- Works in CI/CD environments
- No GUI imports or operations
- Terminal-only validation

### 3. Dual Mode Testing (Debug Mode - Both)
**Environment**: `CELLSORTER_MODE=dual`
```bash
# Run dual mode integration tests
CELLSORTER_MODE=dual pytest tests/integration/
```

**Focus Areas**:
- Real-time synchronization
- Bidirectional event flow
- Consistency between modes
- Performance overhead

**Requirements**:
- Both headless and GUI components
- Synchronization verification
- Latency measurements

## Test Categories

### 1. Unit Tests

Unit tests focus on individual components in isolation.

#### Structure
```
tests/
├── test_models/           # Business logic tests
├── test_components/       # UI component tests
├── test_headless/        # Headless infrastructure tests
├── test_services/        # Service layer tests
└── test_utils/           # Utility function tests
```

#### Mode-Specific Unit Tests

**GUI Mode Unit Tests**:
```python
@pytest.mark.gui_mode
def test_button_click_gui():
    """Test button click in GUI mode only."""
    assert requires_gui()
    button = QPushButton("Test")
    # ... GUI-specific test
```

**Dev Mode Unit Tests**:
```python
@pytest.mark.dev_mode
def test_ui_serialization():
    """Test UI serialization in headless mode."""
    assert is_dev_mode()
    ui_model = UIModel()
    # ... Headless-specific test
```

**Dual Mode Unit Tests**:
```python
@pytest.mark.dual_mode
def test_sync_operation():
    """Test synchronization in dual mode."""
    assert is_dual_mode()
    # ... Test both components
```

### 2. Integration Tests

Integration tests verify interactions between components.

#### Key Integration Points

1. **Image Processing Pipeline**
   - Image loading → CSV parsing → Coordinate transformation
   - Test in all modes to ensure consistency

2. **Selection Management**
   - Scatter plot → Selection → Well plate updates
   - Verify synchronization in dual mode

3. **Template System**
   - Template creation → Saving → Loading → Application
   - Test persistence across modes

4. **Mode Switching**
   - Test transitions between modes
   - Verify state preservation
   - Check resource cleanup

### 3. End-to-End Tests

End-to-end tests simulate complete user workflows.

#### Mode-Specific Workflows

**GUI Mode E2E**:
```python
def test_complete_analysis_workflow_gui():
    """Test complete analysis in GUI mode."""
    # 1. Start application
    # 2. Load image via file dialog
    # 3. Load CSV data
    # 4. Apply filters
    # 5. Export results
```

**Dev Mode E2E**:
```python
def test_complete_analysis_workflow_headless():
    """Test complete analysis in headless mode."""
    # 1. Load UI definition
    # 2. Execute commands via CLI
    # 3. Verify state changes
    # 4. Export results
```

**Dual Mode E2E**:
```python
def test_ai_agent_workflow_dual():
    """Test AI agent operations with visual feedback."""
    # 1. Start in dual mode
    # 2. Execute headless commands
    # 3. Verify GUI updates
    # 4. Check synchronization
```

## Test Implementation Guidelines

### 1. Mode Detection

Always check and respect the current mode:

```python
from headless.mode_manager import get_mode, AppMode

@pytest.fixture
def mode_aware_setup():
    mode = get_mode()
    if mode == AppMode.GUI:
        # GUI-specific setup
        pass
    elif mode == AppMode.DEV:
        # Headless-specific setup
        pass
    elif mode == AppMode.DUAL:
        # Dual mode setup
        pass
```

### 2. Conditional Imports

Use conditional imports to avoid failures:

```python
def test_widget_creation():
    if requires_gui():
        from PySide6.QtWidgets import QPushButton
        button = QPushButton("Test")
        assert button.text() == "Test"
    else:
        # Test UI model instead
        button = {"type": "QPushButton", "text": "Test"}
        assert button["text"] == "Test"
```

### 3. Mock Strategies

Different mocking approaches per mode:

**GUI Mode**: Mock external services
```python
@patch('requests.get')
def test_with_mock(mock_get):
    # Test GUI with mocked network
```

**Dev Mode**: Mock GUI components
```python
@patch('PySide6.QtWidgets.QApplication')
def test_headless(mock_app):
    # Test without real GUI
```

**Dual Mode**: Minimal mocking
```python
# Test real synchronization
# Only mock external dependencies
```

## Performance Testing

### Mode-Specific Benchmarks

1. **GUI Mode Performance**
   - Widget rendering time
   - User interaction responsiveness
   - Memory usage with large datasets

2. **Dev Mode Performance**
   - Command processing speed
   - Serialization efficiency
   - Memory footprint

3. **Dual Mode Performance**
   - Synchronization latency
   - Event propagation time
   - Overhead comparison

### Performance Test Example

```python
@pytest.mark.benchmark
def test_image_loading_performance(benchmark):
    mode = get_mode()
    
    if mode == AppMode.GUI:
        result = benchmark(load_image_gui, "large_image.tif")
    elif mode == AppMode.DEV:
        result = benchmark(load_image_headless, "large_image.tif")
    elif mode == AppMode.DUAL:
        result = benchmark(load_image_dual, "large_image.tif")
    
    assert result.load_time < 5.0  # 5 seconds max
```

## Continuous Integration

### CI Configuration

```yaml
# .github/workflows/test.yml
name: Test All Modes

jobs:
  test-gui-mode:
    runs-on: ubuntu-latest
    env:
      CELLSORTER_MODE: gui
    steps:
      - uses: actions/checkout@v2
      - name: Setup display
        run: |
          export DISPLAY=:99
          Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &
      - name: Run GUI tests
        run: pytest tests/gui/

  test-dev-mode:
    runs-on: ubuntu-latest
    env:
      CELLSORTER_MODE: dev
    steps:
      - uses: actions/checkout@v2
      - name: Run headless tests
        run: pytest tests/headless/

  test-dual-mode:
    runs-on: ubuntu-latest
    env:
      CELLSORTER_MODE: dual
    steps:
      - uses: actions/checkout@v2
      - name: Setup display
        run: |
          export DISPLAY=:99
          Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &
      - name: Run integration tests
        run: pytest tests/integration/
```

## Test Coverage Requirements

### Minimum Coverage by Mode

1. **GUI Mode**: 80% coverage
   - Focus on user-facing features
   - Visual components
   - Event handlers

2. **Dev Mode**: 90% coverage
   - Core business logic
   - Data processing
   - Serialization

3. **Dual Mode**: 85% coverage
   - Synchronization logic
   - Event propagation
   - State consistency

### Coverage Report Generation

```bash
# Generate coverage for specific mode
CELLSORTER_MODE=dev pytest --cov=src --cov-report=html

# Combined coverage report
pytest --cov=src --cov-report=html --cov-report=term
```

## Test Data Management

### Mode-Specific Test Data

1. **GUI Mode**: Visual test data
   - Sample images
   - UI screenshots
   - Visual regression baselines

2. **Dev Mode**: Structured data
   - UI definition files
   - Command sequences
   - State snapshots

3. **Dual Mode**: Synchronization data
   - Event logs
   - State transitions
   - Timing information

## Debugging Failed Tests

### Mode-Specific Debugging

1. **GUI Mode Debugging**
   ```bash
   # Enable GUI debugging
   export QT_DEBUG_PLUGINS=1
   pytest -vv --pdb tests/gui/test_failing.py
   ```

2. **Dev Mode Debugging**
   ```bash
   # Enable headless debugging
   export CELLSORTER_DEBUG=true
   pytest -vv --pdb tests/headless/test_failing.py
   ```

3. **Dual Mode Debugging**
   ```bash
   # Enable sync debugging
   export CELLSORTER_SYNC_DEBUG=true
   pytest -vv --pdb tests/integration/test_failing.py
   ```

## Best Practices

1. **Always specify test mode**
   - Use pytest markers
   - Set environment variables
   - Document mode requirements

2. **Write mode-agnostic tests when possible**
   - Test business logic separately
   - Use abstraction layers
   - Minimize mode-specific code

3. **Maintain mode parity**
   - Features should work in all applicable modes
   - Test the same functionality across modes
   - Document mode-specific limitations

4. **Performance considerations**
   - Dual mode tests may be slower
   - Use appropriate timeouts
   - Consider parallel execution

## Test Maintenance

### Regular Tasks

1. **Weekly**: Run full test suite in all modes
2. **Daily**: Run mode-specific quick tests
3. **Per commit**: Run relevant mode tests
4. **Monthly**: Update visual regression baselines

### Test Review Checklist

- [ ] Tests run in appropriate mode(s)
- [ ] Mode detection is correct
- [ ] No hardcoded mode assumptions
- [ ] Synchronization tests for dual mode
- [ ] Performance benchmarks updated
- [ ] Documentation reflects mode support