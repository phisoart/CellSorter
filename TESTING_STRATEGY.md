# Testing Strategy

## 1. Test Philosophy
We follow a **Test-Driven Development (TDD)** approach.
- Every feature starts with a failing test.
- Tests drive design and modularity.
- All production code is written to make a test pass.

## 2. Test Types

### 2.1 Unit Tests
- Target: Business logic, utility functions, non-GUI modules
- Framework: `pytest`
- Location: `tests/unit/`

### 2.2 GUI Component Tests
- Target: Individual PySide6 widgets and dialogs
- Tool: `pytest-qt`, `pytest`
- Strategy: Use `QTest` or `qtbot` for interaction simulation
- Location: `tests/gui/`

### 2.3 Integration Tests
- Target: End-to-end workflows involving multiple components
- Tool: `pytest`, with optional custom headless setup
- Strategy: Mimic user behavior (e.g. open image → process → export)
- Location: `tests/integration/`

### 2.4 Regression Tests
- Every resolved bug must have a test that reproduces the issue and verifies the fix.
- Marked with `@pytest.mark.regression`

## 3. Test Naming and Structure
- All test files: `test_*.py`
- Test methods: `test_[functionality]_[expected_behavior]`
- Example: `test_image_loader_handles_jpeg.py`

## 4. Coverage
- Minimum: 85% line coverage, with focus on core logic
- Tool: `coverage.py`, integrated with `pytest-cov`

## 5. Continuous Testing
- Tool: GitHub Actions
- On push/PR: Run all unit + GUI tests on both macOS and Windows