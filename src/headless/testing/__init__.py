"""
Headless Testing Framework

Framework for testing UI definitions and logic without requiring a display server.
Provides mock widgets, assertions, and test runners for comprehensive UI testing.
"""

from .framework import UITestCase, HeadlessTestRunner, run_headless_tests
from .mock_widgets import MockWidgetFactory, MockWidget, MockWidgetState
from .assertions import UIAssertions, UIAssertionError, assert_widget, assert_widget_tree
from .test_runner import TestResultData, TestSuite, TestStatusEnum, create_test_suite

# Aliases for compatibility
TestResult = TestResultData
TestStatus = TestStatusEnum

__all__ = [
    'UITestCase',
    'HeadlessTestRunner',
    'run_headless_tests',
    'MockWidgetFactory',
    'MockWidget',
    'MockWidgetState',
    'UIAssertions',
    'UIAssertionError',
    'assert_widget',
    'assert_widget_tree',
    'TestResult',
    'TestSuite',
    'TestStatus',
    'create_test_suite',
] 