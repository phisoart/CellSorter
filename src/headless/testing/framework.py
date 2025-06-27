"""
UI Testing Framework

Main framework classes for headless UI testing.
Provides test case base class and test runner for comprehensive UI testing.
"""

import logging
import unittest
import time
from typing import Any, Dict, List, Optional, Type
from pathlib import Path

from .mock_widgets import MockWidgetFactory, MockWidget
from .assertions import assert_widget, assert_widget_tree, UIAssertionError
from ..ui_compatibility import UI, Widget
from ..ui_model import WidgetType, UIModel
from ..cli.ui_tools import UITools

logger = logging.getLogger(__name__)


class UITestCase(unittest.TestCase):
    """Base class for UI test cases."""
    
    def setUp(self) -> None:
        """Set up test case."""
        super().setUp()
        self.factory = MockWidgetFactory()
        self.ui_tools = UITools()
        self.created_widgets = []
        logger.debug(f"Set up test case: {self.__class__.__name__}")
    
    def tearDown(self) -> None:
        """Clean up after test case."""
        super().tearDown()
        self.factory.clear_all()
        self.created_widgets.clear()
        logger.debug(f"Cleaned up test case: {self.__class__.__name__}")
    
    def create_widget(self, name: str, widget_type: WidgetType, parent: Optional[MockWidget] = None) -> MockWidget:
        """Create mock widget for testing."""
        widget = self.factory.create_widget(name, widget_type, parent)
        self.created_widgets.append(widget)
        return widget
    
    def create_window(self, name: str = "test_window") -> MockWidget:
        """Create main window for testing."""
        # Ensure unique names by checking if it exists
        counter = 1
        original_name = name
        while self.factory.get_widget(name) is not None:
            name = f"{original_name}_{counter}"
            counter += 1
        return self.create_widget(name, WidgetType.MAIN_WINDOW)
    
    def create_dialog(self, name: str = "test_dialog") -> MockWidget:
        """Create dialog for testing."""
        return self.create_widget(name, WidgetType.DIALOG)
    
    def create_button(self, name: str, parent: MockWidget, text: str = "Button") -> MockWidget:
        """Create button for testing."""
        button = self.create_widget(name, WidgetType.PUSH_BUTTON, parent)
        button.set_property("text", text)
        return button
    
    def create_label(self, name: str, parent: MockWidget, text: str = "") -> MockWidget:
        """Create label for testing."""
        label = self.create_widget(name, WidgetType.LABEL, parent)
        label.set_property("text", text)
        return label
    
    def create_line_edit(self, name: str, parent: MockWidget, text: str = "") -> MockWidget:
        """Create line edit for testing."""
        edit = self.create_widget(name, WidgetType.LINE_EDIT, parent)
        edit.set_property("text", text)
        return edit
    
    def load_ui_from_file(self, file_path: str) -> UI:
        """Load UI definition from file for testing."""
        return self.ui_tools.load_ui(file_path)
    
    def create_ui_from_definition(self, ui_def: UI) -> MockWidget:
        """Create mock widget tree from UI definition."""
        if not ui_def.widgets:
            raise ValueError("UI definition has no widgets")
        
        # Find root widget (no parent)
        root_widgets = [w for w in ui_def.widgets if w.parent is None]
        if not root_widgets:
            raise ValueError("No root widget found in UI definition")
        if len(root_widgets) > 1:
            raise ValueError("Multiple root widgets found in UI definition")
        
        root_def = root_widgets[0]
        
        # Create widget tree
        return self._create_widget_tree(root_def, ui_def.widgets)
    
    def _create_widget_tree(self, widget_def: Widget, all_widgets: List[Widget], parent: Optional[MockWidget] = None) -> MockWidget:
        """Recursively create widget tree."""
        widget = self.create_widget(widget_def.name, widget_def.type, parent)
        
        # Set properties
        for prop_name, prop_value in widget_def.properties.items():
            widget.set_property(prop_name, prop_value)
        
        # Set additional attributes
        if widget_def.visible is not None:
            widget.properties["visible"] = widget_def.visible
        if widget_def.enabled is not None:
            widget.properties["enabled"] = widget_def.enabled
        if widget_def.tooltip:
            widget.properties["tooltip"] = widget_def.tooltip
        
        # Create children
        children = [w for w in all_widgets if w.parent == widget_def.name]
        for child_def in children:
            self._create_widget_tree(child_def, all_widgets, widget)
        
        return widget
    
    def assert_widget(self, widget: MockWidget):
        """Create assertion helper for widget."""
        return assert_widget(widget)
    
    def assert_widget_tree(self, root_widget: MockWidget):
        """Create assertion helper for widget tree."""
        return assert_widget_tree(root_widget)
    
    def simulate_click(self, widget: MockWidget) -> None:
        """Simulate click on widget."""
        widget.click()
    
    def simulate_text_input(self, widget: MockWidget, text: str) -> None:
        """Simulate text input on widget."""
        widget.set_text(text)
        widget.emit_signal("textChanged", text)
    
    def simulate_show(self, widget: MockWidget) -> None:
        """Simulate showing widget."""
        widget.show()
    
    def simulate_hide(self, widget: MockWidget) -> None:
        """Simulate hiding widget."""
        widget.hide()
    
    def wait_for_signal(self, widget: MockWidget, signal_name: str, timeout_ms: int = 1000) -> bool:
        """Wait for signal to be emitted (mock implementation)."""
        # In real implementation, this would wait for actual signals
        # For mock widgets, we just check if signal was already emitted
        return signal_name in widget.signals_emitted
    
    def get_widget_by_name(self, name: str) -> Optional[MockWidget]:
        """Get widget by name."""
        return self.factory.get_widget(name)
    
    def get_all_widgets(self) -> List[MockWidget]:
        """Get all created widgets."""
        return self.created_widgets.copy()
    
    def get_widget_count(self) -> int:
        """Get total widget count."""
        return self.factory.get_widget_count()


class HeadlessTestRunner:
    """Test runner for headless UI tests."""
    
    def __init__(self):
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.start_time = None
        self.end_time = None
    
    def run_test_case(self, test_case_class: Type[UITestCase]) -> Dict[str, Any]:
        """Run single test case class."""
        suite = unittest.TestLoader().loadTestsFromTestCase(test_case_class)
        return self.run_test_suite(suite, test_case_class.__name__)
    
    def run_test_suite(self, suite: unittest.TestSuite, suite_name: str = "TestSuite") -> Dict[str, Any]:
        """Run test suite."""
        self.start_time = time.time()
        
        # Custom test result class to capture UI-specific information
        result = HeadlessTestResult()
        
        logger.info(f"Running test suite: {suite_name}")
        suite.run(result)
        
        self.end_time = time.time()
        
        # Compile results
        suite_result = {
            "suite_name": suite_name,
            "tests_run": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "skipped": len(result.skipped),
            "success": result.wasSuccessful(),
            "duration": self.end_time - self.start_time,
            "failure_details": result.failures,
            "error_details": result.errors,
            "skipped_details": result.skipped
        }
        
        self.test_results.append(suite_result)
        
        # Update totals
        self.total_tests += result.testsRun
        if result.wasSuccessful():
            self.passed_tests += result.testsRun
        else:
            self.failed_tests += len(result.failures) + len(result.errors)
        
        logger.info(f"Test suite '{suite_name}' completed: {result.testsRun} tests, "
                   f"{len(result.failures)} failures, {len(result.errors)} errors")
        
        return suite_result
    
    def run_test_directory(self, test_dir: str, pattern: str = "test_*.py") -> Dict[str, Any]:
        """Run all tests in directory."""
        test_path = Path(test_dir)
        if not test_path.exists():
            raise FileNotFoundError(f"Test directory not found: {test_dir}")
        
        # Discover tests
        loader = unittest.TestLoader()
        suite = loader.discover(str(test_path), pattern=pattern)
        
        return self.run_test_suite(suite, f"Directory: {test_dir}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get test run summary."""
        return {
            "total_suites": len(self.test_results),
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "success_rate": (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0,
            "total_duration": sum(r.get("duration", 0) for r in self.test_results),
            "suite_results": self.test_results
        }
    
    def print_summary(self) -> None:
        """Print test run summary."""
        summary = self.get_summary()
        
        print("\n" + "="*60)
        print("HEADLESS UI TEST SUMMARY")
        print("="*60)
        print(f"Test Suites: {summary['total_suites']}")
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']}")
        print(f"Failed: {summary['failed_tests']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Total Duration: {summary['total_duration']:.2f}s")
        print("="*60)
        
        # Print suite details
        for result in self.test_results:
            status = "PASS" if result["success"] else "FAIL"
            print(f"{status}: {result['suite_name']} "
                  f"({result['tests_run']} tests, {result['duration']:.2f}s)")
            
            if not result["success"]:
                for failure in result["failure_details"]:
                    print(f"  FAIL: {failure[0]} - {failure[1].split(chr(10))[0]}")
                for error in result["error_details"]:
                    print(f"  ERROR: {error[0]} - {error[1].split(chr(10))[0]}")


class HeadlessTestResult(unittest.TestResult):
    """Custom test result class for headless UI tests."""
    
    def __init__(self):
        super().__init__()
        self.test_start_times = {}
        self.test_durations = {}
    
    def startTest(self, test) -> None:
        """Called when test starts."""
        super().startTest(test)
        self.test_start_times[test] = time.time()
        logger.debug(f"Starting test: {test}")
    
    def stopTest(self, test) -> None:
        """Called when test stops."""
        super().stopTest(test)
        if test in self.test_start_times:
            duration = time.time() - self.test_start_times[test]
            self.test_durations[test] = duration
            logger.debug(f"Finished test: {test} ({duration:.3f}s)")
    
    def addSuccess(self, test) -> None:
        """Called when test succeeds."""
        super().addSuccess(test)
        logger.debug(f"Test passed: {test}")
    
    def addError(self, test, err) -> None:
        """Called when test has error."""
        super().addError(test, err)
        logger.error(f"Test error: {test} - {err[1]}")
    
    def addFailure(self, test, err) -> None:
        """Called when test fails."""
        super().addFailure(test, err)
        logger.warning(f"Test failed: {test} - {err[1]}")
    
    def addSkip(self, test, reason) -> None:
        """Called when test is skipped."""
        super().addSkip(test, reason)
        logger.info(f"Test skipped: {test} - {reason}")


def run_headless_tests(test_path: Optional[str] = None, pattern: str = "test_*.py") -> Dict[str, Any]:
    """Convenience function to run headless tests."""
    runner = HeadlessTestRunner()
    
    if test_path:
        result = runner.run_test_directory(test_path, pattern)
    else:
        # Run current test directory
        current_dir = Path(__file__).parent.parent.parent.parent / "tests" / "test_headless"
        result = runner.run_test_directory(str(current_dir), pattern)
    
    runner.print_summary()
    return runner.get_summary() 