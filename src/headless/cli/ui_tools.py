"""
UI Tools

Core tools for headless UI manipulation via CLI.
"""

import logging
from typing import Optional, List
from pathlib import Path

from ..ui_compatibility import UI, Widget
from ..ui_model import WidgetType, UIModel
from ..serializers import YAMLSerializer, JSONSerializer
from ..validators import UIValidator, ValidationResult

logger = logging.getLogger(__name__)


class UIToolsError(Exception):
    """Raised when UI tools operation fails."""
    pass


class UITools:
    """Tools for headless UI operations."""
    
    def __init__(self):
        self.yaml_serializer = YAMLSerializer()
        self.json_serializer = JSONSerializer()
        self.validator = UIValidator()
    
    def dump_ui(self, ui_def: UI, output_path: str, format: str = "yaml") -> None:
        """Dump UI definition to file."""
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert to UIModel for serializer
            ui_model = self._ui_to_model(ui_def)
            
            if format.lower() == "yaml":
                self.yaml_serializer.save(ui_model, str(output_file))
            elif format.lower() == "json":
                self.json_serializer.save(ui_model, str(output_file))
            else:
                raise UIToolsError(f"Unsupported format: {format}")
            
            logger.info(f"UI dumped to {output_path}")
            
        except Exception as e:
            raise UIToolsError(f"Failed to dump UI: {e}") from e
    
    def load_ui(self, input_path: str) -> UI:
        """Load UI definition from file."""
        try:
            input_file = Path(input_path)
            if not input_file.exists():
                raise UIToolsError(f"File not found: {input_path}")
            
            if input_file.suffix.lower() in ['.yaml', '.yml']:
                ui_model = self.yaml_serializer.load(str(input_file))
            elif input_file.suffix.lower() == '.json':
                ui_model = self.json_serializer.load(str(input_file))
            else:
                raise UIToolsError(f"Unsupported file format: {input_file.suffix}")
            
            # Convert to UI compatibility format
            ui_def = self._model_to_ui(ui_model)
            
            logger.info(f"UI loaded from {input_path}")
            return ui_def
            
        except Exception as e:
            raise UIToolsError(f"Failed to load UI: {e}") from e
    
    def validate_ui(self, ui_def: UI, strict: bool = False) -> List[ValidationResult]:
        """Validate UI definition."""
        try:
            # Convert to UIModel for validator
            ui_model = self._ui_to_model(ui_def)
            return self.validator.validate(ui_model)
        except Exception as e:
            raise UIToolsError(f"Failed to validate UI: {e}") from e
    
    def validate_ui_file(self, input_path: str, strict: bool = False) -> List[ValidationResult]:
        """Validate UI definition from file."""
        ui_def = self.load_ui(input_path)
        return self.validate_ui(ui_def, strict=strict)
    
    def _ui_to_model(self, ui_def: UI) -> UIModel:
        """Convert UI compatibility format to UIModel."""
        # For now, create a simple UIModel
        model = UIModel(
            version='1.0',
            metadata=ui_def.metadata.copy()
        )
        
        # If we have widgets, convert the first one to root
        if ui_def.widgets:
            # Find root widget (no parent)
            root_widget = None
            for widget in ui_def.widgets:
                if not widget.parent:
                    root_widget = widget.to_base_widget()
                    break
            
            if root_widget:
                model.set_root(root_widget)
        
        return model
    
    def _model_to_ui(self, ui_model: UIModel) -> UI:
        """Convert UIModel to UI compatibility format."""
        widgets = []
        
        if ui_model.root_widget:
            widgets = self._flatten_widget_tree(ui_model.root_widget)
        
        return UI(
            widgets=widgets,
            layouts=[],
            events=[],
            metadata=ui_model.metadata.copy()
        )
    
    def _flatten_widget_tree(self, widget, parent_name=None) -> List[Widget]:
        """Flatten widget tree to list."""
        from ..ui_compatibility import Widget as CompatWidget
        
        result = []
        
        # Convert widget
        compat_widget = CompatWidget.from_base_widget(widget)
        if parent_name:
            compat_widget.parent = parent_name
        
        result.append(compat_widget)
        
        # Add children
        for child in widget.children:
            result.extend(self._flatten_widget_tree(child, widget.name))
        
        return result
