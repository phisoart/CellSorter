"""
Tests for CLI tools
"""

import pytest
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from headless.cli.ui_tools import UITools, UIToolsError
from headless.cli.cli_commands import HeadlessCLI
from headless.ui_compatibility import UI, Widget
from headless.ui_model import WidgetType


class TestUITools:
    """Test UI tools functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.ui_tools = UITools()
        self.test_ui = self._create_test_ui()
    
    def _create_test_ui(self) -> UI:
        """Create test UI definition."""
        widgets = [
            Widget(
                name="test_window",
                type=WidgetType.MAIN_WINDOW,
                parent=None,
                properties={"title": "Test Window"}
            ),
            Widget(
                name="test_label",
                type=WidgetType.LABEL,
                parent="test_window",
                properties={"text": "Test Label"}
            )
        ]
        
        return UI(
            widgets=widgets,
            metadata={"name": "Test UI", "version": "1.0"}
        )
    
    def test_dump_ui_yaml(self, tmp_path):
        """Test dumping UI to YAML format."""
        output_file = tmp_path / "test.yaml"
        
        self.ui_tools.dump_ui(self.test_ui, str(output_file), "yaml")
        
        assert output_file.exists()
        content = output_file.read_text()
        assert "test_window" in content
        assert "QMainWindow" in content
    
    def test_dump_ui_json(self, tmp_path):
        """Test dumping UI to JSON format."""
        output_file = tmp_path / "test.json"
        
        self.ui_tools.dump_ui(self.test_ui, str(output_file), "json")
        
        assert output_file.exists()
        content = output_file.read_text()
        assert "test_window" in content
    
    def test_dump_ui_unsupported_format(self, tmp_path):
        """Test dumping UI with unsupported format."""
        output_file = tmp_path / "test.xml"
        
        with pytest.raises(UIToolsError, match="Unsupported format"):
            self.ui_tools.dump_ui(self.test_ui, str(output_file), "xml")
    
    def test_load_ui(self, tmp_path):
        """Test loading UI from file."""
        # First create a UI file
        output_file = tmp_path / "test.yaml"
        self.ui_tools.dump_ui(self.test_ui, str(output_file), "yaml")
        
        # Load it back
        loaded_ui = self.ui_tools.load_ui(str(output_file))
        
        assert loaded_ui.metadata["name"] == "Test UI"
        assert len(loaded_ui.widgets) == 1  # Only root widget due to conversion
    
    def test_load_ui_file_not_found(self):
        """Test loading UI from non-existent file."""
        with pytest.raises(UIToolsError, match="File not found"):
            self.ui_tools.load_ui("non_existent.yaml")
    
    def test_load_ui_unsupported_format(self, tmp_path):
        """Test loading UI from unsupported format."""
        test_file = tmp_path / "test.xml"
        test_file.write_text("<xml></xml>")
        
        with pytest.raises(UIToolsError, match="Unsupported file format"):
            self.ui_tools.load_ui(str(test_file))
    
    def test_validate_ui(self):
        """Test UI validation."""
        results = self.ui_tools.validate_ui(self.test_ui)
        
        # Should have no errors for simple valid UI
        errors = [r for r in results if r.level.value == 'error']
        assert len(errors) == 0
    
    def test_validate_ui_file(self, tmp_path):
        """Test UI validation from file."""
        # First create a UI file
        output_file = tmp_path / "test.yaml"
        self.ui_tools.dump_ui(self.test_ui, str(output_file), "yaml")
        
        # Validate it
        results = self.ui_tools.validate_ui_file(str(output_file))
        
        # Should have no errors
        errors = [r for r in results if r.level.value == 'error']
        assert len(errors) == 0


class TestHeadlessCLI:
    """Test CLI command implementations."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.cli = HeadlessCLI()
    
    def test_mode_info_command(self):
        """Test mode info command."""
        result = self.cli.run(['mode-info'])
        assert result == 0  # Success
    
    def test_session_create_command(self):
        """Test session create command."""
        result = self.cli.run(['session', 'create', 'test_session'])
        assert result == 0  # Success
    
    def test_model_export_command(self, tmp_path):
        """Test model export command."""
        output_file = tmp_path / "test_export.yaml"
        result = self.cli.run(['model', 'export', str(output_file)])
        assert result == 0  # Success
        assert output_file.exists()


def test_cli_integration():
    """Test CLI integration through main function."""
    from headless.cli.cli_commands import main
    
    # Test mode-info command
    result = main(['mode-info'])
    assert result == 0 