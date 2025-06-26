"""
Tests for Template Management System (TASK-021)

Comprehensive test suite for template creation, storage, management,
and application functionality.
"""

import os
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject

from models.template_manager import (
    TemplateManager, TemplateType, TemplateStatus,
    SelectionTemplate, CalibrationTemplate, WellPlateTemplate, WorkflowTemplate
)
from components.dialogs.template_management_dialog import TemplateManagementDialog


class TestTemplateManager:
    """Test cases for TemplateManager core functionality."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test templates."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def template_manager(self, temp_dir, qtbot):
        """Create TemplateManager instance for testing."""
        manager = TemplateManager(templates_directory=temp_dir)
        qtbot.addWidget(manager)
        return manager
    
    def test_template_manager_initialization(self, template_manager, temp_dir):
        """Test TemplateManager initialization."""
        assert template_manager.templates_directory == Path(temp_dir)
        
        # Check directory structure creation
        for template_type in [TemplateType.SELECTION, TemplateType.CALIBRATION,
                             TemplateType.WELL_PLATE, TemplateType.WORKFLOW]:
            type_dir = Path(temp_dir) / template_type.value
            assert type_dir.exists()
            assert type_dir.is_dir()
    
    def test_create_selection_template(self, template_manager):
        """Test creation of selection template."""
        template_data = {
            'metadata': {
                'name': 'Test Selection Template',
                'description': 'A test selection template',
                'author': 'Test User'
            },
            'selection_method': 'expression',
            'x_column': 'AreaShape_Area',
            'y_column': 'Intensity_MedianIntensity_DAPI',
            'expression': 'area > 200 AND intensity > mean(intensity)',
            'min_cell_count': 10,
            'max_cell_count': 1000
        }
        
        template_id = template_manager.create_template(
            TemplateType.SELECTION, 
            template_data,
            'Test Selection Template'
        )
        
        assert template_id is not None
        assert template_id in template_manager.templates[TemplateType.SELECTION]
        
        # Verify template properties
        template = template_manager.get_template(TemplateType.SELECTION, template_id)
        assert template.metadata.name == 'Test Selection Template'
        assert template.selection_method == 'expression'
        assert template.expression == 'area > 200 AND intensity > mean(intensity)'
    
    def test_save_and_load_template(self, template_manager):
        """Test template persistence."""
        template_data = {
            'metadata': {
                'name': 'Persistence Test',
                'description': 'Testing template persistence',
                'author': 'Test User'
            },
            'selection_method': 'rectangle',
            'x_column': 'X',
            'y_column': 'Y'
        }
        
        # Create template
        template_id = template_manager.create_template(
            TemplateType.SELECTION,
            template_data,
            'Persistence Test'
        )
        
        # Create new manager instance to test loading
        new_manager = TemplateManager(templates_directory=str(template_manager.templates_directory))
        
        # Verify template was loaded
        loaded_template = new_manager.get_template(TemplateType.SELECTION, template_id)
        assert loaded_template is not None
        assert loaded_template.metadata.name == 'Persistence Test'
        assert loaded_template.selection_method == 'rectangle'
    
    def test_apply_template(self, template_manager):
        """Test template application."""
        template_data = {
            'metadata': {
                'name': 'Application Test',
                'description': 'Testing template application',
                'author': 'Test User'
            },
            'selection_method': 'expression',
            'expression': 'area > 100'
        }
        
        template_id = template_manager.create_template(
            TemplateType.SELECTION,
            template_data,
            'Application Test'
        )
        
        # Apply template
        config = template_manager.apply_template(TemplateType.SELECTION, template_id)
        
        assert config is not None
        assert config['metadata']['name'] == 'Application Test'
        assert config['selection_method'] == 'expression'
        assert config['expression'] == 'area > 100'
        
        # Check usage statistics updated
        template = template_manager.get_template(TemplateType.SELECTION, template_id)
        assert template.metadata.usage_count == 1
        assert template.metadata.last_used is not None
    
    def test_delete_template(self, template_manager):
        """Test template deletion."""
        template_data = {
            'metadata': {
                'name': 'Deletion Test',
                'description': 'Testing template deletion',
                'author': 'Test User'
            }
        }
        
        template_id = template_manager.create_template(
            TemplateType.SELECTION,
            template_data,
            'Deletion Test'
        )
        
        # Verify template exists
        assert template_manager.get_template(TemplateType.SELECTION, template_id) is not None
        
        # Delete template
        success = template_manager.delete_template(TemplateType.SELECTION, template_id)
        assert success is True
        
        # Verify template is gone
        assert template_manager.get_template(TemplateType.SELECTION, template_id) is None


if __name__ == '__main__':
    pytest.main([__file__])
