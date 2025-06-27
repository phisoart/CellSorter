"""
Test Runner Components

Additional test runner components for organizing and running headless UI tests.
Provides test result classes and test suite organization.
"""

import logging
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TestStatusEnum(Enum):
    """Test execution status."""
    PENDING = "pending"
    RUNNING = "running" 
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class TestResultData:
    """Individual test result."""
    
    test_name: str
    test_class: str
    status: TestStatusEnum
    duration: float = 0.0
    error_message: Optional[str] = None
    failure_message: Optional[str] = None
    skip_reason: Optional[str] = None
    assertions_count: int = 0
    widgets_created: int = 0
    signals_emitted: int = 0
    
    @property
    def passed(self) -> bool:
        """Check if test passed."""
        return self.status == TestStatusEnum.PASSED
    
    @property
    def failed(self) -> bool:
        """Check if test failed."""
        return self.status in [TestStatusEnum.FAILED, TestStatusEnum.ERROR]
    
    @property
    def skipped(self) -> bool:
        """Check if test was skipped."""
        return self.status == TestStatusEnum.SKIPPED
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "test_name": self.test_name,
            "test_class": self.test_class,
            "status": self.status.value,
            "duration": self.duration,
            "error_message": self.error_message,
            "failure_message": self.failure_message,
            "skip_reason": self.skip_reason,
            "assertions_count": self.assertions_count,
            "widgets_created": self.widgets_created,
            "signals_emitted": self.signals_emitted,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped
        }


class TestSuite:
    """Collection of related tests."""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.tests: List[TestResultData] = []
        self.setup_functions: List[Callable] = []
        self.teardown_functions: List[Callable] = []
        self.before_each_functions: List[Callable] = []
        self.after_each_functions: List[Callable] = []
    
    def add_test(self, test_result: TestResultData) -> None:
        """Add test result to suite."""
        self.tests.append(test_result)
    
    def add_setup(self, func: Callable) -> None:
        """Add setup function."""
        self.setup_functions.append(func)
    
    def add_teardown(self, func: Callable) -> None:
        """Add teardown function."""
        self.teardown_functions.append(func)
    
    def add_before_each(self, func: Callable) -> None:
        """Add before each test function."""
        self.before_each_functions.append(func)
    
    def add_after_each(self, func: Callable) -> None:
        """Add after each test function."""
        self.after_each_functions.append(func)
    
    def run_setup(self) -> None:
        """Run all setup functions."""
        for func in self.setup_functions:
            try:
                func()
            except Exception as e:
                logger.error(f"Setup function failed: {e}")
                raise
    
    def run_teardown(self) -> None:
        """Run all teardown functions."""
        for func in self.teardown_functions:
            try:
                func()
            except Exception as e:
                logger.warning(f"Teardown function failed: {e}")
    
    def run_before_each(self) -> None:
        """Run before each test functions."""
        for func in self.before_each_functions:
            try:
                func()
            except Exception as e:
                logger.error(f"Before each function failed: {e}")
                raise
    
    def run_after_each(self) -> None:
        """Run after each test functions."""
        for func in self.after_each_functions:
            try:
                func()
            except Exception as e:
                logger.warning(f"After each function failed: {e}")
    
    @property
    def total_tests(self) -> int:
        """Get total number of tests."""
        return len(self.tests)
    
    @property
    def passed_tests(self) -> int:
        """Get number of passed tests."""
        return len([t for t in self.tests if t.passed])
    
    @property
    def failed_tests(self) -> int:
        """Get number of failed tests."""
        return len([t for t in self.tests if t.failed])
    
    @property
    def skipped_tests(self) -> int:
        """Get number of skipped tests."""
        return len([t for t in self.tests if t.skipped])
    
    @property
    def success_rate(self) -> float:
        """Get success rate percentage."""
        if self.total_tests == 0:
            return 0.0
        return (self.passed_tests / self.total_tests) * 100
    
    @property
    def total_duration(self) -> float:
        """Get total duration of all tests."""
        return sum(t.duration for t in self.tests)
    
    @property
    def average_duration(self) -> float:
        """Get average test duration."""
        if self.total_tests == 0:
            return 0.0
        return self.total_duration / self.total_tests
    
    def get_failed_tests(self) -> List[TestResultData]:
        """Get all failed tests."""
        return [t for t in self.tests if t.failed]
    
    def get_passed_tests(self) -> List[TestResultData]:
        """Get all passed tests."""
        return [t for t in self.tests if t.passed]
    
    def get_skipped_tests(self) -> List[TestResultData]:
        """Get all skipped tests."""
        return [t for t in self.tests if t.skipped]
    
    def get_tests_by_status(self, status: TestStatusEnum) -> List[TestResultData]:
        """Get tests by status."""
        return [t for t in self.tests if t.status == status]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "skipped_tests": self.skipped_tests,
            "success_rate": self.success_rate,
            "total_duration": self.total_duration,
            "average_duration": self.average_duration,
            "tests": [t.to_dict() for t in self.tests]
        }
    
    def print_summary(self) -> None:
        """Print suite summary."""
        print(f"\nTest Suite: {self.name}")
        if self.description:
            print(f"Description: {self.description}")
        print(f"Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.failed_tests}")
        print(f"Skipped: {self.skipped_tests}")
        print(f"Success Rate: {self.success_rate:.1f}%")
        print(f"Duration: {self.total_duration:.2f}s")
        
        if self.failed_tests > 0:
            print("\nFailed Tests:")
            for test in self.get_failed_tests():
                print(f"  - {test.test_name}: {test.failure_message or test.error_message}")


class TestSuiteBuilder:
    """Builder for creating test suites."""
    
    def __init__(self, name: str):
        self.suite = TestSuite(name)
    
    def description(self, desc: str) -> 'TestSuiteBuilder':
        """Set suite description."""
        self.suite.description = desc
        return self
    
    def setup(self, func: Callable) -> 'TestSuiteBuilder':
        """Add setup function."""
        self.suite.add_setup(func)
        return self
    
    def teardown(self, func: Callable) -> 'TestSuiteBuilder':
        """Add teardown function."""
        self.suite.add_teardown(func)
        return self
    
    def before_each(self, func: Callable) -> 'TestSuiteBuilder':
        """Add before each function."""
        self.suite.add_before_each(func)
        return self
    
    def after_each(self, func: Callable) -> 'TestSuiteBuilder':
        """Add after each function."""
        self.suite.add_after_each(func)
        return self
    
    def build(self) -> TestSuite:
        """Build the test suite."""
        return self.suite


def create_test_suite(name: str) -> TestSuiteBuilder:
    """Create a new test suite builder."""
    return TestSuiteBuilder(name) 