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
- 본 프로젝트는 별도의 CONTRIBUTING.md, RELEASE_PLAN.md 파일을 생성하지 않으며, 관련 규칙은 README.md 및 기타 문서에 통합되어 관리됩니다.

This comprehensive testing strategy ensures robust, reliable software that meets the demanding requirements of pathology research applications.