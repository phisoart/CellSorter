"""
YAML Serializer

YAML serialization for UI models with preservation of structure and comments.
Optimized for human readability and AI parsing.
"""

import yaml
import logging
from typing import Any, Dict, Optional
from datetime import datetime

from .base_serializer import BaseSerializer, SerializationError
from ..ui_model import UIModel

logger = logging.getLogger(__name__)


class YAMLSerializer(BaseSerializer):
    """YAML serializer for UI models."""
    
    def __init__(self):
        super().__init__()
        self._preserve_comments = True
        self._use_safe_loader = True
    
    @property
    def preserve_comments(self) -> bool:
        """Get whether to preserve comments."""
        return self._preserve_comments
    
    @preserve_comments.setter
    def preserve_comments(self, value: bool) -> None:
        """Set whether to preserve comments."""
        self._preserve_comments = value
    
    def serialize(self, ui_model: UIModel) -> str:
        """
        Serialize UI model to YAML string.
        
        Args:
            ui_model: UI model to serialize
            
        Returns:
            YAML string representation
            
        Raises:
            SerializationError: If serialization fails
        """
        try:
            data = self._prepare_for_serialization(ui_model)
            
            # Add YAML-specific metadata
            data['metadata']['serialization_timestamp'] = datetime.now().isoformat()
            data['metadata']['format'] = 'yaml'
            
            # Configure YAML output
            yaml_str = yaml.dump(
                data,
                default_flow_style=False,
                indent=self.indent_size,
                sort_keys=self.sort_keys,
                allow_unicode=True,
                encoding=None,  # Return string, not bytes
                width=120,  # Line width for better readability
            )
            
            # Add header comment
            header = self._generate_header_comment(ui_model)
            return header + yaml_str
            
        except Exception as e:
            raise SerializationError(f"YAML serialization failed: {e}") from e
    
    def deserialize(self, data: str) -> UIModel:
        """
        Deserialize YAML string to UI model.
        
        Args:
            data: YAML string data
            
        Returns:
            Deserialized UI model
            
        Raises:
            SerializationError: If deserialization fails
        """
        try:
            # Parse YAML safely
            if self._use_safe_loader:
                parsed_data = yaml.safe_load(data)
            else:
                parsed_data = yaml.load(data, Loader=yaml.FullLoader)
            
            if parsed_data is None:
                parsed_data = {}
            
            self._validate_before_deserialization(parsed_data)
            
            # Create UI model from parsed data
            ui_model = UIModel.from_dict(parsed_data)
            
            logger.info("Successfully deserialized YAML to UI model")
            return ui_model
            
        except yaml.YAMLError as e:
            raise SerializationError(f"YAML parsing failed: {e}") from e
        except Exception as e:
            raise SerializationError(f"YAML deserialization failed: {e}") from e
    
    def _generate_header_comment(self, ui_model: UIModel) -> str:
        """Generate header comment for YAML file."""
        header = "# CellSorter UI Definition (YAML)\n"
        header += f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        header += f"# Version: {ui_model.version}\n"
        
        if ui_model.metadata.get('description'):
            header += f"# Description: {ui_model.metadata['description']}\n"
        
        header += "#\n"
        header += "# This file defines the UI structure in a format that can be\n"
        header += "# edited by both humans and AI agents. Changes to this file\n"
        header += "# will be reflected in the application UI.\n"
        header += "#\n"
        header += "# Rules:\n"
        header += "# - All widget names must be unique\n"
        header += "# - Widget names must be valid Python identifiers\n"
        header += "# - Use camelCase for widget names\n"
        header += "# - Validate changes with: python run.py --validate-ui <file>\n"
        header += "#\n\n"
        
        return header
    
    def get_supported_extensions(self) -> list[str]:
        """Get list of supported file extensions."""
        return ['.yaml', '.yml']
    
    def format_for_ai_editing(self, ui_model: UIModel) -> str:
        """
        Format UI model specifically for AI editing.
        
        Includes extra comments and structure to guide AI modifications.
        
        Args:
            ui_model: UI model to format
            
        Returns:
            AI-friendly YAML string
        """
        try:
            data = self._prepare_for_serialization(ui_model)
            
            # Add AI-specific metadata
            data['metadata']['ai_editing'] = True
            data['metadata']['editing_instructions'] = {
                'widget_naming': 'Use camelCase (e.g., submitButton, userNameEdit)',
                'property_format': 'Follow Qt property names (e.g., text, enabled, visible)',
                'event_format': 'signal -> handler mapping (e.g., clicked -> on_button_clicked)',
                'validation': 'Validate with --validate-ui before applying changes'
            }
            
            # Use specific formatting for AI
            yaml_str = yaml.dump(
                data,
                default_flow_style=False,
                indent=2,  # Fixed indent for consistency
                sort_keys=True,  # Sorted for predictability
                allow_unicode=True,
                encoding=None,
                width=80,  # Narrower for AI parsing
            )
            
            # Add comprehensive header
            header = self._generate_ai_header_comment(ui_model)
            return header + yaml_str
            
        except Exception as e:
            raise SerializationError(f"AI formatting failed: {e}") from e
    
    def _generate_ai_header_comment(self, ui_model: UIModel) -> str:
        """Generate AI-friendly header comment."""
        header = "# CellSorter UI Definition - AI Editing Mode\n"
        header += f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        header += "#\n"
        header += "# AI MODIFICATION GUIDELINES:\n"
        header += "#\n"
        header += "# 1. Widget Naming:\n"
        header += "#    - Use camelCase: submitButton, userNameEdit, statusLabel\n"
        header += "#    - Include widget type suffix: Button, Edit, Label, etc.\n"
        header += "#    - Be descriptive: exportButton not btn1\n"
        header += "#\n"
        header += "# 2. Properties:\n"
        header += "#    - Common: text, enabled, visible, tooltip\n"
        header += "#    - Geometry: x, y, width, height\n"
        header += "#    - Style: stylesheet, font, color\n"
        header += "#\n"
        header += "# 3. Events:\n"
        header += "#    - Format: signal -> handler\n"
        header += "#    - Example: clicked -> on_submit_clicked\n"
        header += "#    - Handler naming: on_[widget]_[signal]\n"
        header += "#\n"
        header += "# 4. Layouts:\n"
        header += "#    - Types: QVBoxLayout, QHBoxLayout, QGridLayout\n"
        header += "#    - Properties: margin, spacing\n"
        header += "#    - Items: widget references with stretch/alignment\n"
        header += "#\n"
        header += "# 5. Validation:\n"
        header += "#    - Always validate: python run.py --validate-ui <file>\n"
        header += "#    - Check for duplicate names\n"
        header += "#    - Verify widget references in layouts\n"
        header += "#\n\n"
        
        return header 