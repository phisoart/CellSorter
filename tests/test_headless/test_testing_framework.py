"""
Tests for Headless Testing Framework

Tests the mock widgets, assertions, and framework components.
"""

import unittest
import tempfile
import os
from pathlib import Path

from src.headless.testing import (
    UITestCase, HeadlessTestRunner, MockWidgetFactory, MockWidget, 
    MockWidgetState, UIAssertions, UIAssertionError, assert_widget,
    TestResult, TestStatus, create_test_suite
)
from src.headless.ui_model import WidgetType


class TestMockWidgets(unittest.TestCase):
    """Test mock widget functionality."""
    
    def setUp(self):
        self.factory = MockWidgetFactory()
    
    def tearDown(self):
        self.factory.clear_all()
    
    def test_widget_creation(self):
        """Test creating mock widgets."""
        widget = self.factory.create_widget("test_widget", WidgetType.LABEL)
        
        self.assertEqual(widget.name, "test_widget")
        self.assertEqual(widget.widget_type, WidgetType.LABEL)
        self.assertEqual(widget.state, MockWidgetState.CREATED)
        self.assertIsNone(widget.parent)
        self.assertEqual(len(widget.children), 0)
    
    def test_widget_hierarchy(self):
        """Test widget parent-child relationships."""
        parent = self.factory.create_widget("parent", WidgetType.MAIN_WINDOW)
        child1 = self.factory.create_widget("child1", WidgetType.LABEL, parent)
        child2 = self.factory.create_widget("child2", WidgetType.PUSH_BUTTON, parent)
        
        self.assertEqual(child1.parent, parent)
        self.assertEqual(child2.parent, parent)
        self.assertIn(child1, parent.children)
        self.assertIn(child2, parent.children)
        self.assertEqual(len(parent.children), 2)
    
    def test_widget_properties(self):
        """Test widget property management."""
        widget = self.factory.create_widget("test", WidgetType.LABEL)
        
        # Test default properties
        self.assertEqual(widget.get_property("text"), "")
        self.assertEqual(widget.get_property("alignment"), "Left")
        
        # Test setting properties
        widget.set_property("text", "Hello World")
        self.assertEqual(widget.get_property("text"), "Hello World")
        
        # Test property change history
        events = [e for e in widget.event_history if e["type"] == "property_changed"]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["property"], "text")
        self.assertEqual(events[0]["new_value"], "Hello World")
    
    def test_widget_signals(self):
        """Test widget signal emission and connection."""
        widget = self.factory.create_widget("button", WidgetType.PUSH_BUTTON)
        
        # Connect signal
        widget.connect_signal("clicked", "on_button_clicked")
        
        # Emit signal
        widget.emit_signal("clicked")
        
        self.assertIn("clicked", widget.signals_emitted)
        self.assertIn("clicked", widget.connected_signals)
        self.assertIn("on_button_clicked", widget.connected_signals["clicked"])
    
    def test_widget_visibility(self):
        """Test widget visibility states."""
        widget = self.factory.create_widget("test", WidgetType.LABEL)
        
        # Initially created, not visible
        self.assertFalse(widget.is_visible())
        
        # Show widget
        widget.show()
        self.assertTrue(widget.is_visible())
        self.assertEqual(widget.state, MockWidgetState.SHOWN)
        
        # Hide widget
        widget.hide()
        self.assertFalse(widget.is_visible())
        self.assertEqual(widget.state, MockWidgetState.HIDDEN)
    
    def test_widget_click_simulation(self):
        """Test simulating clicks on widgets."""
        button = self.factory.create_widget("button", WidgetType.PUSH_BUTTON)
        
        # Click should work for buttons
        button.click()
        self.assertIn("clicked", button.signals_emitted)
        self.assertEqual(button.get_event_count("clicked"), 1)
        
        # Multiple clicks
        button.click()
        button.click()
        self.assertEqual(button.get_event_count("clicked"), 3)
        
        # Click on label should log warning but not crash
        label = self.factory.create_widget("label", WidgetType.LABEL)
        label.click()  # Should not emit clicked signal
        self.assertNotIn("clicked", label.signals_emitted)
    
    def test_factory_management(self):
        """Test factory widget management."""
        self.assertEqual(self.factory.get_widget_count(), 0)
        
        # Create widgets
        widget1 = self.factory.create_widget("w1", WidgetType.LABEL)
        widget2 = self.factory.create_widget("w2", WidgetType.PUSH_BUTTON)
        
        self.assertEqual(self.factory.get_widget_count(), 2)
        self.assertIn("w1", self.factory.get_widget_names())
        self.assertIn("w2", self.factory.get_widget_names())
        
        # Get widgets
        self.assertEqual(self.factory.get_widget("w1"), widget1)
        self.assertEqual(self.factory.get_widget("w2"), widget2)
        self.assertIsNone(self.factory.get_widget("nonexistent"))
        
        # Find by type
        labels = self.factory.find_widgets_by_type(WidgetType.LABEL)
        buttons = self.factory.find_widgets_by_type(WidgetType.PUSH_BUTTON)
        
        self.assertEqual(len(labels), 1)
        self.assertEqual(len(buttons), 1)
        self.assertEqual(labels[0], widget1)
        self.assertEqual(buttons[0], widget2)


class TestUIAssertions(unittest.TestCase):
    """Test UI assertion helpers."""
    
    def setUp(self):
        self.factory = MockWidgetFactory()
    
    def tearDown(self):
        self.factory.clear_all()
    
    def test_basic_assertions(self):
        """Test basic widget assertions."""
        widget = self.factory.create_widget("test", WidgetType.LABEL)
        
        # Test successful assertions
        assert_widget(widget).exists()
        assert_widget(widget).has_name("test")
        assert_widget(widget).has_type(WidgetType.LABEL)
        assert_widget(widget).has_type("LABEL")  # String type using enum name
        assert_widget(widget).is_root()
        
        # Test property assertions
        widget.set_property("text", "Hello")
        assert_widget(widget).has_property("text", "Hello")
        assert_widget(widget).has_text("Hello")
    
    def test_assertion_failures(self):
        """Test assertion failures."""
        widget = self.factory.create_widget("test", WidgetType.LABEL)
        
        # Test failing assertions
        with self.assertRaises(UIAssertionError):
            assert_widget(widget).has_name("wrong_name")
        
        with self.assertRaises(UIAssertionError):
            assert_widget(widget).has_type(WidgetType.PUSH_BUTTON)
        
        with self.assertRaises(UIAssertionError):
            assert_widget(widget).has_text("wrong_text")
        
        with self.assertRaises(UIAssertionError):
            assert_widget(widget).is_visible()
    
    def test_hierarchy_assertions(self):
        """Test widget hierarchy assertions."""
        parent = self.factory.create_widget("parent", WidgetType.MAIN_WINDOW)
        child1 = self.factory.create_widget("child1", WidgetType.LABEL, parent)
        child2 = self.factory.create_widget("child2", WidgetType.PUSH_BUTTON, parent)
        
        # Parent assertions
        assert_widget(parent).has_child_count(2)
        assert_widget(parent).has_child("child1")
        assert_widget(parent).has_child("child2")
        assert_widget(parent).is_root()
        
        # Child assertions
        assert_widget(child1).has_parent("parent")
        assert_widget(child2).has_parent("parent")
        
        # Failing hierarchy assertions
        with self.assertRaises(UIAssertionError):
            assert_widget(parent).has_child_count(3)
        
        with self.assertRaises(UIAssertionError):
            assert_widget(parent).has_child("nonexistent")
        
        with self.assertRaises(UIAssertionError):
            assert_widget(child1).is_root()
    
    def test_state_assertions(self):
        """Test widget state assertions."""
        widget = self.factory.create_widget("test", WidgetType.PUSH_BUTTON)
        
        # Initial state
        assert_widget(widget).has_state(MockWidgetState.CREATED)
        
        # Show widget
        widget.show()
        assert_widget(widget).has_state(MockWidgetState.SHOWN)
        assert_widget(widget).is_visible()
        assert_widget(widget).was_shown()
        
        # Hide widget
        widget.hide()
        assert_widget(widget).has_state(MockWidgetState.HIDDEN)
        assert_widget(widget).is_hidden()
        assert_widget(widget).was_hidden()
    
    def test_signal_assertions(self):
        """Test signal emission assertions."""
        button = self.factory.create_widget("button", WidgetType.PUSH_BUTTON)
        
        # Initially no signals
        assert_widget(button).has_not_emitted_signal("clicked")
        
        # Click button
        button.click()
        assert_widget(button).has_emitted_signal("clicked")
        assert_widget(button).has_emitted_signal("clicked", count=1)
        assert_widget(button).was_clicked()
        
        # Click again
        button.click()
        assert_widget(button).has_emitted_signal("clicked", count=2)
        assert_widget(button).was_clicked(times=2)
        
        # Test failure
        with self.assertRaises(UIAssertionError):
            assert_widget(button).has_not_emitted_signal("clicked")


class TestUITestCase(UITestCase):
    """Test the UITestCase base class."""
    
    def test_widget_creation_helpers(self):
        """Test helper methods for widget creation."""
        # Create window
        window = self.create_window("main_window")
        self.assert_widget(window).has_name("main_window")
        self.assert_widget(window).has_type(WidgetType.MAIN_WINDOW)
        
        # Create dialog
        dialog = self.create_dialog("test_dialog")
        self.assert_widget(dialog).has_name("test_dialog")
        self.assert_widget(dialog).has_type(WidgetType.DIALOG)
        
        # Create controls
        button = self.create_button("btn", window, "Click Me")
        label = self.create_label("lbl", window, "Hello")
        edit = self.create_line_edit("edit", window, "Initial text")
        
        self.assert_widget(button).has_text("Click Me")
        self.assert_widget(label).has_text("Hello")
        self.assert_widget(edit).has_text("Initial text")
        
        # Test hierarchy
        self.assert_widget(window).has_child_count(3)
        self.assert_widget(button).has_parent("main_window")
    
    def test_simulation_methods(self):
        """Test event simulation methods."""
        window1 = self.create_window("sim_window1")
        button = self.create_button("btn", window1, "Test")
        
        # Simulate click
        self.simulate_click(button)
        self.assert_widget(button).was_clicked()
        
        # Simulate text input - create separate window to avoid conflicts
        window2 = self.create_window("sim_window2")
        edit = self.create_line_edit("edit", window2)
        self.simulate_text_input(edit, "New text")
        self.assert_widget(edit).has_text("New text")
        self.assert_widget(edit).has_emitted_signal("textChanged")
        
        # Simulate show/hide
        window3 = self.create_window("sim_window3")
        widget = self.create_label("label", window3)
        self.simulate_show(widget)
        self.assert_widget(widget).is_visible()
        
        self.simulate_hide(widget)
        self.assert_widget(widget).is_hidden()
    
    def test_widget_lookup(self):
        """Test widget lookup methods."""
        window = self.create_window("lookup_main")
        button = self.create_button("lookup_btn", window)
        label = self.create_label("lookup_lbl", window)
        
        # Test lookup
        found_button = self.get_widget_by_name("lookup_btn")
        self.assertEqual(found_button, button)
        
        # Test count - should include all widgets created in this test case
        self.assertGreaterEqual(self.get_widget_count(), 3)  # At least window + button + label
        
        # Test all widgets
        all_widgets = self.get_all_widgets()
        self.assertGreaterEqual(len(all_widgets), 3)
        self.assertIn(window, all_widgets)
        self.assertIn(button, all_widgets)
        self.assertIn(label, all_widgets)


class TestFrameworkIntegration(unittest.TestCase):
    """Test framework integration components."""
    
    def test_test_runner(self):
        """Test the HeadlessTestRunner."""
        runner = HeadlessTestRunner()
        
        # Run a simple test case - create a suite instead to avoid type issues
        import unittest
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestMockWidgets)
        result = runner.run_test_suite(suite, "TestMockWidgets")
        
        self.assertIn("suite_name", result)
        self.assertIn("tests_run", result)
        self.assertIn("success", result)
        self.assertIn("duration", result)
        self.assertTrue(result["success"])
        self.assertGreater(result["tests_run"], 0)
    
    def test_test_suite_creation(self):
        """Test test suite creation and management."""
        suite = create_test_suite("Test Suite").description("Test description").build()
        
        self.assertEqual(suite.name, "Test Suite")
        self.assertEqual(suite.description, "Test description")
        self.assertEqual(suite.total_tests, 0)
        
        # Add test results
        result1 = TestResult("test1", "TestClass", TestStatus.PASSED, 0.1)
        result2 = TestResult("test2", "TestClass", TestStatus.FAILED, 0.2, failure_message="Failed")
        
        suite.add_test(result1)
        suite.add_test(result2)
        
        self.assertEqual(suite.total_tests, 2)
        self.assertEqual(suite.passed_tests, 1)
        self.assertEqual(suite.failed_tests, 1)
        self.assertEqual(suite.success_rate, 50.0)


if __name__ == "__main__":
    # Create temporary test file for UI loading tests
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
metadata:
  version: "1.0"
  created: "2024-01-01T00:00:00Z"
  
widgets:
  - name: "main_window"
    type: "main_window" 
    properties:
      title: "Test Window"
      width: 800
      height: 600
    visible: true
    enabled: true
    
  - name: "label1"
    type: "label"
    parent: "main_window"
    properties:
      text: "Hello World"
    visible: true
    enabled: true
""")
        temp_file = f.name
    
    try:
        unittest.main()
    finally:
        # Clean up temp file
        if os.path.exists(temp_file):
            os.unlink(temp_file) 