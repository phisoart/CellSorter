"""
Base Serializer

Abstract base class for UI serializers providing common functionality.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TextIO, Union
import logging
from pathlib import Path

from ..ui_model import UIModel, Widget

logger = logging.getLogger(__name__)


class SerializationError(Exception):
    """Raised when serialization fails."""
    pass


class BaseSerializer(ABC):
    """Abstract base class for UI serializers."""
    
    def __init__(self):
        self._indent_size = 2
        self._sort_keys = True
        self._preserve_order = False
    
    @property
    def indent_size(self) -> int:
        """Get indentation size."""
        return self._indent_size
    
    @indent_size.setter 
    def indent_size(self, value: int) -> None:
        """Set indentation size."""
        if value < 0:
            raise ValueError("Indent size must be non-negative")
        self._indent_size = value
    
    @property
    def sort_keys(self) -> bool:
        """Get whether to sort keys."""
        return self._sort_keys
    
    @sort_keys.setter
    def sort_keys(self, value: bool) -> None:
        """Set whether to sort keys."""
        self._sort_keys = value
    
    @abstractmethod
    def serialize(self, ui_model: UIModel) -> str:
        """
        Serialize UI model to string.
        
        Args:
            ui_model: UI model to serialize
            
        Returns:
            Serialized string representation
            
        Raises:
            SerializationError: If serialization fails
        """
        pass
    
    @abstractmethod
    def deserialize(self, data: str) -> UIModel:
        """
        Deserialize string to UI model.
        
        Args:
            data: Serialized string data
            
        Returns:
            Deserialized UI model
            
        Raises:
            SerializationError: If deserialization fails
        """
        pass
    
    def save(self, ui_model: UIModel, file_path: Union[str, Path]) -> None:
        """
        Save UI model to file.
        
        Args:
            ui_model: UI model to save
            file_path: Path to save file
            
        Raises:
            SerializationError: If saving fails
        """
        try:
            data = self.serialize(ui_model)
            Path(file_path).write_text(data, encoding='utf-8')
            logger.info(f"Saved UI model to {file_path}")
        except Exception as e:
            raise SerializationError(f"Failed to save to {file_path}: {e}") from e
    
    def load(self, file_path: Union[str, Path]) -> UIModel:
        """
        Load UI model from file.
        
        Args:
            file_path: Path to load from
            
        Returns:
            Loaded UI model
            
        Raises:
            SerializationError: If loading fails
        """
        try:
            data = Path(file_path).read_text(encoding='utf-8')
            ui_model = self.deserialize(data)
            logger.info(f"Loaded UI model from {file_path}")
            return ui_model
        except Exception as e:
            raise SerializationError(f"Failed to load from {file_path}: {e}") from e
    
    def save_to_stream(self, ui_model: UIModel, stream: TextIO) -> None:
        """
        Save UI model to text stream.
        
        Args:
            ui_model: UI model to save
            stream: Text stream to write to
            
        Raises:
            SerializationError: If saving fails
        """
        try:
            data = self.serialize(ui_model)
            stream.write(data)
            logger.debug("Saved UI model to stream")
        except Exception as e:
            raise SerializationError(f"Failed to save to stream: {e}") from e
    
    def load_from_stream(self, stream: TextIO) -> UIModel:
        """
        Load UI model from text stream.
        
        Args:
            stream: Text stream to read from
            
        Returns:
            Loaded UI model
            
        Raises:
            SerializationError: If loading fails
        """
        try:
            data = stream.read()
            ui_model = self.deserialize(data)
            logger.debug("Loaded UI model from stream")
            return ui_model
        except Exception as e:
            raise SerializationError(f"Failed to load from stream: {e}") from e
    
    def _prepare_for_serialization(self, ui_model: UIModel) -> Dict[str, Any]:
        """
        Prepare UI model for serialization.
        
        Args:
            ui_model: UI model to prepare
            
        Returns:
            Dictionary ready for serialization
        """
        data = ui_model.to_dict()
        
        # Add serialization metadata
        if 'metadata' not in data:
            data['metadata'] = {}
        
        data['metadata']['serializer'] = self.__class__.__name__
        data['metadata']['serialization_version'] = '1.0'
        
        return data
    
    def _validate_before_deserialization(self, data: Dict[str, Any]) -> None:
        """
        Validate data before deserialization.
        
        Args:
            data: Data to validate
            
        Raises:
            SerializationError: If validation fails
        """
        if not isinstance(data, dict):
            raise SerializationError("Data must be a dictionary")
        
        if 'version' not in data:
            logger.warning("No version field found in data")
        
        # Check for required fields
        # Note: root_widget is optional for empty UIs
        
    def get_supported_extensions(self) -> list[str]:
        """Get list of supported file extensions."""
        return [] 