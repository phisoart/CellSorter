"""
JSON Serializer

JSON serialization for UI models with compact format and schema validation.
Suitable for API communication and automated processing.
"""

import json
import logging
from typing import Any, Dict, Optional
from datetime import datetime

from .base_serializer import BaseSerializer, SerializationError
from ..ui_model import UIModel

logger = logging.getLogger(__name__)


class JSONSerializer(BaseSerializer):
    """JSON serializer for UI models."""
    
    def __init__(self):
        super().__init__()
        self._compact_output = False
        self._ensure_ascii = False
    
    @property
    def compact_output(self) -> bool:
        """Get whether to use compact output."""
        return self._compact_output
    
    @compact_output.setter
    def compact_output(self, value: bool) -> None:
        """Set whether to use compact output."""
        self._compact_output = value
    
    @property
    def ensure_ascii(self) -> bool:
        """Get whether to ensure ASCII output."""
        return self._ensure_ascii
    
    @ensure_ascii.setter
    def ensure_ascii(self, value: bool) -> None:
        """Set whether to ensure ASCII output."""
        self._ensure_ascii = value
    
    def serialize(self, ui_model: UIModel) -> str:
        """
        Serialize UI model to JSON string.
        
        Args:
            ui_model: UI model to serialize
            
        Returns:
            JSON string representation
            
        Raises:
            SerializationError: If serialization fails
        """
        try:
            data = self._prepare_for_serialization(ui_model)
            
            # Add JSON-specific metadata
            data['metadata']['serialization_timestamp'] = datetime.now().isoformat()
            data['metadata']['format'] = 'json'
            
            # Configure JSON output
            if self._compact_output:
                json_str = json.dumps(
                    data,
                    ensure_ascii=self._ensure_ascii,
                    sort_keys=self.sort_keys,
                    separators=(',', ':')  # Compact separators
                )
            else:
                json_str = json.dumps(
                    data,
                    ensure_ascii=self._ensure_ascii,
                    sort_keys=self.sort_keys,
                    indent=self.indent_size
                )
            
            return json_str
            
        except Exception as e:
            raise SerializationError(f"JSON serialization failed: {e}") from e
    
    def deserialize(self, data: str) -> UIModel:
        """
        Deserialize JSON string to UI model.
        
        Args:
            data: JSON string data
            
        Returns:
            Deserialized UI model
            
        Raises:
            SerializationError: If deserialization fails
        """
        try:
            # Parse JSON
            parsed_data = json.loads(data)
            
            if parsed_data is None:
                parsed_data = {}
            
            self._validate_before_deserialization(parsed_data)
            
            # Create UI model from parsed data
            ui_model = UIModel.from_dict(parsed_data)
            
            logger.info("Successfully deserialized JSON to UI model")
            return ui_model
            
        except json.JSONDecodeError as e:
            raise SerializationError(f"JSON parsing failed: {e}") from e
        except Exception as e:
            raise SerializationError(f"JSON deserialization failed: {e}") from e
    
    def get_supported_extensions(self) -> list[str]:
        """Get list of supported file extensions."""
        return ['.json']
    
    def serialize_compact(self, ui_model: UIModel) -> str:
        """
        Serialize UI model to compact JSON string.
        
        Args:
            ui_model: UI model to serialize
            
        Returns:
            Compact JSON string
        """
        old_compact = self._compact_output
        try:
            self._compact_output = True
            return self.serialize(ui_model)
        finally:
            self._compact_output = old_compact
    
    def serialize_pretty(self, ui_model: UIModel) -> str:
        """
        Serialize UI model to pretty-printed JSON string.
        
        Args:
            ui_model: UI model to serialize
            
        Returns:
            Pretty-printed JSON string
        """
        old_compact = self._compact_output
        try:
            self._compact_output = False
            return self.serialize(ui_model)
        finally:
            self._compact_output = old_compact
    
    def to_schema_dict(self, ui_model: UIModel) -> Dict[str, Any]:
        """
        Convert UI model to schema-compatible dictionary.
        
        Used for API communication and validation.
        
        Args:
            ui_model: UI model to convert
            
        Returns:
            Schema-compatible dictionary
        """
        data = self._prepare_for_serialization(ui_model)
        
        # Add schema information
        data['$schema'] = "https://cellsorter.org/schemas/ui-definition/v1.0.json"
        data['metadata']['schema_version'] = "1.0"
        
        return data
    
    def from_schema_dict(self, data: Dict[str, Any]) -> UIModel:
        """
        Create UI model from schema dictionary.
        
        Args:
            data: Schema dictionary
            
        Returns:
            UI model
        """
        # Validate schema if present
        if '$schema' in data:
            logger.debug(f"Using schema: {data['$schema']}")
        
        self._validate_before_deserialization(data)
        return UIModel.from_dict(data) 