"""
Template Management System for CellSorter (TASK-021)

Comprehensive template system for storing and managing analysis workflows,
selection criteria, calibration settings, and well plate configurations.
Enables consistent, repeatable analysis protocols for research teams.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import uuid

from PySide6.QtCore import QObject, Signal
from utils.logging_config import LoggerMixin
from utils.error_handler import error_handler


class TemplateType(Enum):
    """Types of templates supported by the system."""
    SELECTION = "selection"
    CALIBRATION = "calibration"
    WELL_PLATE = "well_plate"
    WORKFLOW = "workflow"
    EXPRESSION = "expression"


class TemplateStatus(Enum):
    """Template status indicators."""
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    DRAFT = "draft"
    ARCHIVED = "archived"


@dataclass
class TemplateMetadata:
    """Metadata for all template types."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    author: str = ""
    created_date: str = field(default_factory=lambda: datetime.now().isoformat())
    modified_date: str = field(default_factory=lambda: datetime.now().isoformat())
    version: str = "1.0.0"
    tags: List[str] = field(default_factory=list)
    status: TemplateStatus = TemplateStatus.ACTIVE
    usage_count: int = 0
    last_used: Optional[str] = None


@dataclass
class SelectionTemplate:
    """Template for cell selection criteria and methods."""
    metadata: TemplateMetadata = field(default_factory=TemplateMetadata)
    
    # Selection method configuration
    selection_method: str = "rectangle"  # "rectangle", "expression", "manual"
    
    # Scatter plot configuration
    x_column: str = ""
    y_column: str = ""
    
    # Rectangle election parameters
    rectangle_bounds: Optional[Dict[str, float]] = None
    
    # Expression filtering parameters
    expression: str = ""
    expression_parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Selection labeling
    label_template: str = "Selection_{index}"
    color_scheme: str = "default"
    custom_colors: List[str] = field(default_factory=list)
    
    # Quality criteria
    min_cell_count: int = 1
    max_cell_count: int = 100000
    
    # Auto-apply settings
    auto_apply: bool = False
    apply_on_load: bool = False


@dataclass
class CalibrationTemplate:
    """Template for coordinate calibration settings."""
    metadata: TemplateMetadata = field(default_factory=TemplateMetadata)
    
    # Calibration method
    calibration_method: str = "two_point"
    
    # Reference points
    reference_points: List[Dict[str, float]] = field(default_factory=list)
    
    # Transformation matrix
    transformation_matrix: Optional[List[List[float]]] = None
    
    # Validation settings
    validation_enabled: bool = True
    min_distance_pixels: int = 50
    max_error_threshold: float = 1.0
    
    # Auto-apply settings
    auto_apply: bool = False
    apply_on_load: bool = False


@dataclass 
class WellPlateTemplate:
    """Template for 96-well plate assignments."""
    metadata: TemplateMetadata = field(default_factory=TemplateMetadata)
    
    # Plate configuration
    plate_type: str = "96_well"
    plate_dimensions: Dict[str, int] = field(default_factory=lambda: {"rows": 8, "columns": 12})
    
    # Assignment rules
    assignment_strategy: str = "sequential"
    well_assignments: Dict[str, List[str]] = field(default_factory=dict)
    cell_type_rules: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    well_metadata: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Organization settings
    skip_empty_wells: bool = True
    fill_order: str = "row_wise"
    max_cells_per_well: int = 1000
    min_cells_per_well: int = 10


@dataclass
class WorkflowTemplate:
    """Template for complete analysis workflows."""
    metadata: TemplateMetadata = field(default_factory=TemplateMetadata)
    
    # File handling
    image_path_template: str = ""
    csv_path_template: str = ""
    output_path_template: str = ""
    
    # Workflow steps
    steps: List[Dict[str, Any]] = field(default_factory=list)
    
    # Sub-templates
    selection_template_id: Optional[str] = None
    calibration_template_id: Optional[str] = None
    well_plate_template_id: Optional[str] = None
    
    # Execution settings
    auto_execute: bool = False
    validate_steps: bool = True
    save_intermediate: bool = True
    
    # Batch processing
    batch_enabled: bool = False
    batch_settings: Dict[str, Any] = field(default_factory=dict)


class TemplateManager(QObject, LoggerMixin):
    """
    Central manager for all template operations.
    
    Features:
    - Template storage and retrieval
    - Template validation and versioning
    - Template sharing and import/export
    - Usage tracking and analytics
    """
    
    # Signals
    template_created = Signal(str, str)      # template_type, template_id
    template_updated = Signal(str, str)      # template_type, template_id
    template_deleted = Signal(str, str)      # template_type, template_id
    template_applied = Signal(str, str)      # template_type, template_id
    templates_loaded = Signal()
    
    def __init__(self, templates_directory: str = ".taskmaster/templates", parent: Optional[QObject] = None):
        super().__init__(parent)
        
        # Configuration
        self.templates_directory = Path(templates_directory)
        self.ensure_directory_structure()
        
        # Template storage
        self.templates: Dict[TemplateType, Dict[str, Any]] = {
            TemplateType.SELECTION: {},
            TemplateType.CALIBRATION: {},
            TemplateType.WELL_PLATE: {},
            TemplateType.WORKFLOW: {},
            TemplateType.EXPRESSION: {}
        }
        
        # Template class mappings
        self.template_classes = {
            TemplateType.SELECTION: SelectionTemplate,
            TemplateType.CALIBRATION: CalibrationTemplate,
            TemplateType.WELL_PLATE: WellPlateTemplate,
            TemplateType.WORKFLOW: WorkflowTemplate,
        }
        
        # Load existing templates
        self.load_all_templates()
        
        self.log_info("Template manager initialized")
    
    def ensure_directory_structure(self) -> None:
        """Ensure template directory structure exists."""
        self.templates_directory.mkdir(parents=True, exist_ok=True)
        
        for template_type in TemplateType:
            if template_type != TemplateType.EXPRESSION:  # Skip expression for now
                type_dir = self.templates_directory / template_type.value
                type_dir.mkdir(exist_ok=True)
    
    @error_handler("Loading templates")
    def load_all_templates(self) -> None:
        """Load all templates from storage."""
        for template_type in TemplateType:
            if template_type in self.template_classes:
                self.load_templates_by_type(template_type)
        
        total_count = sum(len(templates) for templates in self.templates.values())
        self.log_info(f"Loaded {total_count} templates")
        self.templates_loaded.emit()
    
    def load_templates_by_type(self, template_type: TemplateType) -> None:
        """Load templates of a specific type."""
        type_dir = self.templates_directory / template_type.value
        if not type_dir.exists():
            return
            
        template_class = self.template_classes[template_type]
        
        for template_file in type_dir.glob("*.json"):
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Convert to template object
                template = self._dict_to_template(data, template_class)
                self.templates[template_type][template.metadata.id] = template
                
            except Exception as e:
                self.log_error(f"Failed to load template {template_file}: {e}")
    
    def _dict_to_template(self, data: Dict[str, Any], template_class) -> Any:
        """Convert dictionary to template object."""
        # Handle metadata conversion
        if 'metadata' in data:
            metadata_data = data['metadata']
            if isinstance(metadata_data.get('status'), str):
                metadata_data['status'] = TemplateStatus(metadata_data['status'])
            data['metadata'] = TemplateMetadata(**metadata_data)
        
        return template_class(**data)
    
    def _template_to_dict(self, template: Any) -> Dict[str, Any]:
        """Convert template object to dictionary."""
        data = asdict(template)
        
        # Handle enum serialization
        if 'metadata' in data and 'status' in data['metadata']:
            status = data['metadata']['status']
            if hasattr(status, 'value'):
                data['metadata']['status'] = status.value
        
        return data
    
    @error_handler("Creating template")
    def create_template(self, template_type: TemplateType, template_data: Dict[str, Any], 
                       template_name: str = "", auto_save: bool = True) -> str:
        """Create a new template."""
        template_class = self.template_classes.get(template_type)
        if not template_class:
            raise ValueError(f"Unsupported template type: {template_type}")
        
        # Create metadata if not provided
        if 'metadata' not in template_data:
            template_data['metadata'] = {}
        
        metadata = template_data['metadata']
        if not metadata.get('name'):
            metadata['name'] = template_name or f"New {template_type.value.title()} Template"
        
        # Create template object
        template = template_class(**template_data)
        
        # Store template
        template_id = template.metadata.id
        self.templates[template_type][template_id] = template
        
        # Save to file if requested
        if auto_save:
            self.save_template(template_type, template_id)
        
        self.template_created.emit(template_type.value, template_id)
        self.log_info(f"Created template: {template.metadata.name} ({template_id})")
        
        return template_id
    
    @error_handler("Saving template")
    def save_template(self, template_type: TemplateType, template_id: str) -> bool:
        """Save template to file."""
        if template_id not in self.templates[template_type]:
            return False
        
        template = self.templates[template_type][template_id]
        
        # Create file path
        filename = f"{template_id}.json"
        file_path = self.templates_directory / template_type.value / filename
        
        # Convert to dictionary and save
        try:
            data = self._template_to_dict(template)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.log_info(f"Saved template: {template.metadata.name}")
            return True
            
        except Exception as e:
            self.log_error(f"Failed to save template {template_id}: {e}")
            return False
    
    def get_template(self, template_type: TemplateType, template_id: str) -> Optional[Any]:
        """Get a template by ID."""
        return self.templates[template_type].get(template_id)
    
    def get_templates_by_type(self, template_type: TemplateType, 
                             status_filter: Optional[TemplateStatus] = None) -> List[Any]:
        """Get all templates of a specific type."""
        templates = list(self.templates[template_type].values())
        
        if status_filter:
            templates = [t for t in templates if t.metadata.status == status_filter]
        
        # Sort by name
        return sorted(templates, key=lambda t: t.metadata.name.lower())
    
    def apply_template(self, template_type: TemplateType, template_id: str) -> Dict[str, Any]:
        """Apply a template and return configuration."""
        template = self.get_template(template_type, template_id)
        if not template:
            return {}
        
        # Update usage statistics
        template.metadata.usage_count += 1
        template.metadata.last_used = datetime.now().isoformat()
        
        # Save updated statistics
        self.save_template(template_type, template_id)
        
        # Emit signal
        self.template_applied.emit(template_type.value, template_id)
        
        # Return template configuration
        config = self._template_to_dict(template)
        
        self.log_info(f"Applied template: {template.metadata.name}")
        
        return config
    
    def delete_template(self, template_type: TemplateType, template_id: str) -> bool:
        """Delete a template."""
        if template_id not in self.templates[template_type]:
            return False
        
        template = self.templates[template_type][template_id]
        template_name = template.metadata.name
        
        # Remove from memory
        del self.templates[template_type][template_id]
        
        # Delete file
        filename = f"{template_id}.json"
        file_path = self.templates_directory / template_type.value / filename
        
        try:
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            self.log_error(f"Failed to delete template file {file_path}: {e}")
        
        self.template_deleted.emit(template_type.value, template_id)
        self.log_info(f"Deleted template: {template_name}")
        
        return True
