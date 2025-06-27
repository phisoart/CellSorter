"""
UI Validator

Main validator that combines schema, semantic, and best practice validation.
Provides comprehensive validation for UI definitions.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from ..ui_model import UIModel
from .schema_validator import SchemaValidator
from .semantic_validator import SemanticValidator

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation severity levels."""
    ERROR = "error"
    WARNING = "warning"  
    INFO = "info"


@dataclass
class ValidationResult:
    """Result of validation check."""
    level: ValidationLevel
    message: str
    path: str = ""
    widget_name: str = ""
    code: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'level': self.level.value,
            'message': self.message,
            'path': self.path,
            'widget_name': self.widget_name,
            'code': self.code
        }


class UIValidator:
    """Main UI validator combining all validation types."""
    
    def __init__(self):
        self.schema_validator = SchemaValidator()
        self.semantic_validator = SemanticValidator()
        self._strict_mode = False
        self._validation_rules = {
            'widget_naming': True,
            'duplicate_names': True,
            'missing_references': True,
            'layout_consistency': True,
            'property_types': True,
            'event_handlers': True,
        }
    
    @property
    def strict_mode(self) -> bool:
        """Get strict mode setting."""
        return self._strict_mode
    
    @strict_mode.setter
    def strict_mode(self, value: bool) -> None:
        """Set strict mode (warnings become errors)."""
        self._strict_mode = value
    
    def enable_rule(self, rule_name: str) -> None:
        """Enable specific validation rule."""
        if rule_name in self._validation_rules:
            self._validation_rules[rule_name] = True
        else:
            logger.warning(f"Unknown validation rule: {rule_name}")
    
    def disable_rule(self, rule_name: str) -> None:
        """Disable specific validation rule."""
        if rule_name in self._validation_rules:
            self._validation_rules[rule_name] = False
        else:
            logger.warning(f"Unknown validation rule: {rule_name}")
    
    def validate(self, ui_model: UIModel) -> List[ValidationResult]:
        """
        Validate UI model comprehensively.
        
        Args:
            ui_model: UI model to validate
            
        Returns:
            List of validation results
        """
        results = []
        
        # Schema validation
        if self._validation_rules.get('property_types', True):
            schema_results = self.schema_validator.validate(ui_model)
            results.extend(schema_results)
        
        # Semantic validation
        if self._validation_rules.get('duplicate_names', True):
            results.extend(self._validate_unique_names(ui_model))
        
        if self._validation_rules.get('missing_references', True):
            results.extend(self._validate_widget_references(ui_model))
        
        if self._validation_rules.get('widget_naming', True):
            results.extend(self._validate_naming_conventions(ui_model))
        
        if self._validation_rules.get('layout_consistency', True):
            results.extend(self._validate_layout_consistency(ui_model))
        
        if self._validation_rules.get('event_handlers', True):
            results.extend(self._validate_event_handlers(ui_model))
        
        # Additional validations
        results.extend(self._validate_basic_structure(ui_model))
        
        # Apply strict mode
        if self._strict_mode:
            for result in results:
                if result.level == ValidationLevel.WARNING:
                    result.level = ValidationLevel.ERROR
        
        return results
    
    def validate_and_report(self, ui_model: UIModel) -> bool:
        """
        Validate and report results to logger.
        
        Args:
            ui_model: UI model to validate
            
        Returns:
            True if validation passed (no errors)
        """
        results = self.validate(ui_model)
        
        has_errors = False
        has_warnings = False
        
        for result in results:
            if result.level == ValidationLevel.ERROR:
                has_errors = True
                logger.error(f"[{result.code}] {result.message} (Path: {result.path})")
            elif result.level == ValidationLevel.WARNING:
                has_warnings = True
                logger.warning(f"[{result.code}] {result.message} (Path: {result.path})")
            else:
                logger.info(f"[{result.code}] {result.message} (Path: {result.path})")
        
        # Summary
        error_count = sum(1 for r in results if r.level == ValidationLevel.ERROR)
        warning_count = sum(1 for r in results if r.level == ValidationLevel.WARNING)
        
        if error_count == 0 and warning_count == 0:
            logger.info("Validation passed - no issues found")
        else:
            logger.info(f"Validation completed: {error_count} errors, {warning_count} warnings")
        
        return not has_errors
    
    def _validate_unique_names(self, ui_model: UIModel) -> List[ValidationResult]:
        """Validate that all widget names are unique."""
        results = []
        
        if not ui_model.root_widget:
            return results
        
        names = set()
        self._collect_widget_names(ui_model.root_widget, names, results, "")
        
        return results
    
    def _collect_widget_names(self, widget, names: set, results: List[ValidationResult], path: str):
        """Recursively collect widget names and check for duplicates."""
        current_path = f"{path}.{widget.name}" if path else widget.name
        
        if widget.name in names:
            results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                message=f"Duplicate widget name: {widget.name}",
                path=current_path,
                widget_name=widget.name,
                code="DUPLICATE_NAME"
            ))
        else:
            names.add(widget.name)
        
        for child in widget.children:
            self._collect_widget_names(child, names, results, current_path)
    
    def _validate_widget_references(self, ui_model: UIModel) -> List[ValidationResult]:
        """Validate that all widget references in layouts exist."""
        results = []
        
        if not ui_model.root_widget:
            return results
        
        all_names = set()
        self._collect_all_names(ui_model.root_widget, all_names)
        
        self._check_layout_references(ui_model.root_widget, all_names, results, "")
        
        return results
    
    def _collect_all_names(self, widget, names: set):
        """Collect all widget names in the tree."""
        names.add(widget.name)
        for child in widget.children:
            self._collect_all_names(child, names)
    
    def _check_layout_references(self, widget, all_names: set, results: List[ValidationResult], path: str):
        """Check layout references recursively."""
        current_path = f"{path}.{widget.name}" if path else widget.name
        
        if widget.layout:
            for item in widget.layout.items:
                if item.widget_name not in all_names:
                    results.append(ValidationResult(
                        level=ValidationLevel.ERROR,
                        message=f"Layout references non-existent widget: {item.widget_name}",
                        path=f"{current_path}.layout",
                        widget_name=widget.name,
                        code="MISSING_WIDGET_REF"
                    ))
        
        for child in widget.children:
            self._check_layout_references(child, all_names, results, current_path)
    
    def _validate_naming_conventions(self, ui_model: UIModel) -> List[ValidationResult]:
        """Validate widget naming conventions."""
        results = []
        
        if not ui_model.root_widget:
            return results
        
        self._check_naming_conventions(ui_model.root_widget, results, "")
        
        return results
    
    def _check_naming_conventions(self, widget, results: List[ValidationResult], path: str):
        """Check naming conventions recursively."""
        current_path = f"{path}.{widget.name}" if path else widget.name
        
        # Check if name is valid Python identifier
        if not widget.name.isidentifier():
            results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                message=f"Widget name is not a valid Python identifier: {widget.name}",
                path=current_path,
                widget_name=widget.name,
                code="INVALID_IDENTIFIER"
            ))
        
        # Check camelCase convention
        if widget.name != widget.name[0].lower() + widget.name[1:]:
            results.append(ValidationResult(
                level=ValidationLevel.WARNING,
                message=f"Widget name should use camelCase: {widget.name}",
                path=current_path,
                widget_name=widget.name,
                code="NAMING_CONVENTION"
            ))
        
        # Check for descriptive names
        if len(widget.name) < 3:
            results.append(ValidationResult(
                level=ValidationLevel.WARNING,
                message=f"Widget name is too short: {widget.name}",
                path=current_path,
                widget_name=widget.name,
                code="SHORT_NAME"
            ))
        
        for child in widget.children:
            self._check_naming_conventions(child, results, current_path)
    
    def _validate_layout_consistency(self, ui_model: UIModel) -> List[ValidationResult]:
        """Validate layout consistency."""
        results = []
        
        if not ui_model.root_widget:
            return results
        
        self._check_layout_consistency(ui_model.root_widget, results, "")
        
        return results
    
    def _check_layout_consistency(self, widget, results: List[ValidationResult], path: str):
        """Check layout consistency recursively."""
        current_path = f"{path}.{widget.name}" if path else widget.name
        
        if widget.layout:
            layout = widget.layout
            
            # Grid layout specific checks
            if layout.type.value == "QGridLayout":
                for item in layout.items:
                    if item.row is None or item.column is None:
                        results.append(ValidationResult(
                            level=ValidationLevel.ERROR,
                            message=f"Grid layout item missing row/column: {item.widget_name}",
                            path=f"{current_path}.layout",
                            widget_name=widget.name,
                            code="MISSING_GRID_POSITION"
                        ))
        
        for child in widget.children:
            self._check_layout_consistency(child, results, current_path)
    
    def _validate_event_handlers(self, ui_model: UIModel) -> List[ValidationResult]:
        """Validate event handlers."""
        results = []
        
        if not ui_model.root_widget:
            return results
        
        self._check_event_handlers(ui_model.root_widget, results, "")
        
        return results
    
    def _check_event_handlers(self, widget, results: List[ValidationResult], path: str):
        """Check event handlers recursively."""
        current_path = f"{path}.{widget.name}" if path else widget.name
        
        for event in widget.events:
            # Check handler naming convention
            expected_prefix = f"on_{widget.name.lower()}_"
            if not event.handler.startswith(expected_prefix) and not event.handler.startswith("lambda"):
                results.append(ValidationResult(
                    level=ValidationLevel.WARNING,
                    message=f"Event handler should follow naming convention: {event.handler}",
                    path=f"{current_path}.events",
                    widget_name=widget.name,
                    code="EVENT_NAMING"
                ))
        
        for child in widget.children:
            self._check_event_handlers(child, results, current_path)
    
    def _validate_basic_structure(self, ui_model: UIModel) -> List[ValidationResult]:
        """Validate basic UI structure."""
        results = []
        
        if not ui_model.root_widget:
            results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                message="No root widget defined",
                path="",
                widget_name="",
                code="NO_ROOT_WIDGET"
            ))
        
        return results 