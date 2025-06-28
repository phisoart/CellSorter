"""
Test Template Management System in DEV Mode

Tests template management system in headless development mode.
Verifies template creation, storage, retrieval, and application.
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

from src.headless.testing.framework import UITestCase
from src.models.template_manager import (
    TemplateManager, TemplateType, TemplateStatus,
    SelectionTemplate, CalibrationTemplate, WellPlateTemplate, WorkflowTemplate
)
from src.headless.mode_manager import ModeManager
from src.utils.logging_config import get_logger


class TestTemplateManagementDev(UITestCase):
    """Test template management system in DEV mode (headless)."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        
        # Set up DEV mode
        self.mode_manager = Mock(spec=ModeManager)
        self.mode_manager.is_dev_mode.return_value = True
        self.mode_manager.is_gui_mode.return_value = False
        self.mode_manager.is_dual_mode.return_value = False
        
        # Create temporary directory for templates
        self.temp_dir = tempfile.TemporaryDirectory()
        self.template_dir = Path(self.temp_dir.name)
        
        # Create template manager with temporary directory
        self.template_manager = TemplateManager(
            templates_directory=str(self.template_dir)
        )
        
        # Test template data
        self.test_selection_template = {
            'metadata': {
                'name': 'Test Selection Template',
                'description': 'A test selection template for DEV mode',
                'author': 'Headless Test System',
                'tags': ['test', 'headless', 'selection']
            },
            'selection_method': 'expression',
            'x_column': 'AreaShape_Area',
            'y_column': 'Intensity_MedianIntensity_DAPI',
            'expression': 'area > mean(area) + std(area)',
            'min_cell_count': 10,
            'max_cell_count': 1000,
            'label_template': 'High_Area_Cells_{index}',
            'color_scheme': 'default',
            'custom_colors': ['#FF5733']
        }
        
        self.test_calibration_template = {
            'metadata': {
                'name': 'Test Calibration Template',
                'description': 'A test calibration template for DEV mode',
                'author': 'Headless Test System',
                'tags': ['test', 'headless', 'calibration']
            },
            'calibration_method': 'two_point',
            'reference_points': [
                {'pixel': [100, 100], 'stage': [0.0, 0.0], 'label': 'Origin'},
                {'pixel': [500, 300], 'stage': [400.0, 200.0], 'label': 'Reference'}
            ],
            'max_error_threshold': 2.0,
            'auto_apply': True
        }
        
        self.test_well_plate_template = {
            'metadata': {
                'name': 'Test Well Plate Template',
                'description': 'A test well plate template for DEV mode',
                'author': 'Headless Test System',
                'tags': ['test', 'headless', 'well_plate']
            },
            'plate_type': '96_well',
            'assignment_strategy': 'sequential',
            'max_cells_per_well': 1000,
            'min_cells_per_well': 10,
            'well_assignments': {'A01': ['selection_1'], 'A02': ['selection_2']},
            'cell_type_rules': {
                'high_area': {'min_area': 100},
                'medium_area': {'min_area': 50, 'max_area': 100},
                'low_area': {'max_area': 50}
            },
            'well_metadata': {
                'A01': {'priority': 'high', 'notes': 'Test well'},
                'A02': {'priority': 'medium', 'notes': 'Control well'}
            }
        }
        
        self.test_workflow_template = {
            'metadata': {
                'name': 'Test Workflow Template',
                'description': 'A test workflow template for DEV mode',
                'author': 'Headless Test System',
                'tags': ['test', 'headless', 'workflow']
            },
            'image_path_template': '{base_dir}/images/{sample_id}.tiff',
            'csv_path_template': '{base_dir}/data/{sample_id}.csv',
            'output_path_template': '{base_dir}/output/{sample_id}_results.txt',
            'steps': [
                {'type': 'load_image', 'auto_execute': True},
                {'type': 'load_csv', 'auto_execute': True},
                {'type': 'apply_calibration', 'template_ref': 'default_calibration'},
                {'type': 'apply_selection', 'template_ref': 'default_selection'},
                {'type': 'assign_wells', 'template_ref': 'default_well_plate'},
                {'type': 'export_results', 'auto_execute': False}
            ],
            'validate_steps': True,
            'save_intermediate': True,
            'batch_enabled': False,
            'batch_settings': {
                'auto_validate': True,
                'batch_mode': False,
                'error_handling': 'stop_on_error'
            }
        }
        
        self.logger = get_logger('test_template_dev')
    
    def tearDown(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()
        super().tearDown()
    
    def test_template_manager_initialization(self):
        """Test template manager initialization in headless mode."""
        # Verify template manager initialization
        assert self.template_manager.templates_directory == self.template_dir
        
        # Check directory structure was created
        for template_type in [TemplateType.SELECTION, TemplateType.CALIBRATION,
                             TemplateType.WELL_PLATE, TemplateType.WORKFLOW]:
            type_dir = self.template_dir / template_type.value
            assert type_dir.exists()
            assert type_dir.is_dir()
        
        # Verify empty template storage
        for template_type in TemplateType:
            if template_type != TemplateType.EXPRESSION:
                assert len(self.template_manager.templates[template_type]) == 0
    
    def test_create_selection_template_headless(self):
        """Test creating selection template in headless mode."""
        # Create selection template
        template_id = self.template_manager.create_template(
            TemplateType.SELECTION,
            self.test_selection_template,
            'Test Selection Template'
        )
        
        # Verify template creation
        assert template_id is not None
        assert template_id in self.template_manager.templates[TemplateType.SELECTION]
        
        # Retrieve and verify template
        template = self.template_manager.get_template(TemplateType.SELECTION, template_id)
        assert template is not None
        assert template.metadata.name == 'Test Selection Template'
        assert template.selection_method == 'expression'
        assert template.expression == 'area > mean(area) + std(area)'
        assert template.x_column == 'AreaShape_Area'
        assert template.y_column == 'Intensity_MedianIntensity_DAPI'
        
        # Verify file was saved
        template_file = self.template_dir / 'selection' / f'{template_id}.json'
        assert template_file.exists()
    
    def test_create_calibration_template_headless(self):
        """Test creating calibration template in headless mode."""
        # Create calibration template
        template_id = self.template_manager.create_template(
            TemplateType.CALIBRATION,
            self.test_calibration_template,
            'Test Calibration Template'
        )
        
        # Verify template creation
        assert template_id is not None
        assert template_id in self.template_manager.templates[TemplateType.CALIBRATION]
        
        # Retrieve and verify template
        template = self.template_manager.get_template(TemplateType.CALIBRATION, template_id)
        assert template is not None
        assert template.metadata.name == 'Test Calibration Template'
        assert template.calibration_method == 'two_point'
        assert len(template.reference_points) == 2
        assert template.max_error_threshold == 2.0
        assert template.auto_apply is True
        
        # Verify file was saved
        template_file = self.template_dir / 'calibration' / f'{template_id}.json'
        assert template_file.exists()
    
    def test_create_well_plate_template_headless(self):
        """Test creating well plate template in headless mode."""
        # Create well plate template
        template_id = self.template_manager.create_template(
            TemplateType.WELL_PLATE,
            self.test_well_plate_template,
            'Test Well Plate Template'
        )
        
        # Verify template creation
        assert template_id is not None
        assert template_id in self.template_manager.templates[TemplateType.WELL_PLATE]
        
        # Retrieve and verify template
        template = self.template_manager.get_template(TemplateType.WELL_PLATE, template_id)
        assert template is not None
        assert template.metadata.name == 'Test Well Plate Template'
        assert template.plate_type == '96_well'
        assert template.assignment_strategy == 'sequential'
        assert 'high_area' in template.cell_type_rules
        assert 'medium_area' in template.cell_type_rules
        assert 'low_area' in template.cell_type_rules
        
        # Verify file was saved
        template_file = self.template_dir / 'well_plate' / f'{template_id}.json'
        assert template_file.exists()
    
    def test_create_workflow_template_headless(self):
        """Test creating workflow template in headless mode."""
        # Create workflow template
        template_id = self.template_manager.create_template(
            TemplateType.WORKFLOW,
            self.test_workflow_template,
            'Test Workflow Template'
        )
        
        # Verify template creation
        assert template_id is not None
        assert template_id in self.template_manager.templates[TemplateType.WORKFLOW]
        
        # Retrieve and verify template
        template = self.template_manager.get_template(TemplateType.WORKFLOW, template_id)
        assert template is not None
        assert template.metadata.name == 'Test Workflow Template'
        assert template.image_path_template == '{base_dir}/images/{sample_id}.tiff'
        assert template.csv_path_template == '{base_dir}/data/{sample_id}.csv'
        assert template.output_path_template == '{base_dir}/output/{sample_id}_results.txt'
        assert len(template.steps) == 6
        assert template.validate_steps is True
        assert template.save_intermediate is True
        assert template.batch_enabled is False
        
        # Verify file was saved
        template_file = self.template_dir / 'workflow' / f'{template_id}.json'
        assert template_file.exists()
    
    def test_template_application_headless(self):
        """Test template application in headless mode."""
        # Create selection template
        template_id = self.template_manager.create_template(
            TemplateType.SELECTION,
            self.test_selection_template,
            'Application Test Template'
        )
        
        # Apply template
        config = self.template_manager.apply_template(TemplateType.SELECTION, template_id)
        
        # Verify application result
        assert config is not None
        assert config['metadata']['name'] == 'Application Test Template'
        assert config['selection_method'] == 'expression'
        assert config['expression'] == 'area > mean(area) + std(area)'
        
        # Verify usage statistics were updated
        template = self.template_manager.get_template(TemplateType.SELECTION, template_id)
        assert template.metadata.usage_count == 1
        assert template.metadata.last_used is not None
    
    def test_template_persistence_and_loading(self):
        """Test template persistence and loading."""
        # Create templates
        selection_id = self.template_manager.create_template(
            TemplateType.SELECTION,
            self.test_selection_template,
            'Persistence Test Selection'
        )
        
        calibration_id = self.template_manager.create_template(
            TemplateType.CALIBRATION,
            self.test_calibration_template,
            'Persistence Test Calibration'
        )
        
        # Create new template manager to test loading
        new_manager = TemplateManager(templates_directory=str(self.template_dir))
        
        # Verify templates were loaded
        loaded_selection = new_manager.get_template(TemplateType.SELECTION, selection_id)
        assert loaded_selection is not None
        assert loaded_selection.metadata.name == 'Persistence Test Selection'
        
        loaded_calibration = new_manager.get_template(TemplateType.CALIBRATION, calibration_id)
        assert loaded_calibration is not None
        assert loaded_calibration.metadata.name == 'Persistence Test Calibration'
    
    def test_template_deletion_headless(self):
        """Test template deletion in headless mode."""
        # Create template
        template_id = self.template_manager.create_template(
            TemplateType.SELECTION,
            self.test_selection_template,
            'Deletion Test Template'
        )
        
        # Verify template exists
        assert self.template_manager.get_template(TemplateType.SELECTION, template_id) is not None
        template_file = self.template_dir / 'selection' / f'{template_id}.json'
        assert template_file.exists()
        
        # Delete template
        success = self.template_manager.delete_template(TemplateType.SELECTION, template_id)
        assert success is True
        
        # Verify template is gone
        assert self.template_manager.get_template(TemplateType.SELECTION, template_id) is None
        assert not template_file.exists()
    
    def test_get_templates_by_type_filtering(self):
        """Test getting templates by type with filtering."""
        # Create multiple templates
        template_ids = []
        for i in range(3):
            template_data = self.test_selection_template.copy()
            template_data['metadata'] = template_data['metadata'].copy()
            template_data['metadata']['name'] = f'Test Template {i}'
            
            template_id = self.template_manager.create_template(
                TemplateType.SELECTION,
                template_data,
                f'Test Template {i}'
            )
            template_ids.append(template_id)
        
        # Get all selection templates
        selection_templates = self.template_manager.get_templates_by_type(TemplateType.SELECTION)
        assert len(selection_templates) == 3
        
        # Verify templates are sorted by name
        template_names = [t.metadata.name for t in selection_templates]
        assert template_names == sorted(template_names)
    
    def test_template_error_handling(self):
        """Test template error handling in headless mode."""
        # Test invalid template type
        with pytest.raises(ValueError):
            self.template_manager.create_template(
                TemplateType.EXPRESSION,  # Not supported yet
                {},
                'Invalid Template'
            )
        
        # Test saving non-existent template
        success = self.template_manager.save_template(TemplateType.SELECTION, 'non_existent_id')
        assert success is False
        
        # Test getting non-existent template
        template = self.template_manager.get_template(TemplateType.SELECTION, 'non_existent_id')
        assert template is None
        
        # Test deleting non-existent template
        success = self.template_manager.delete_template(TemplateType.SELECTION, 'non_existent_id')
        assert success is False
    
    def test_template_batch_operations(self):
        """Test batch template operations."""
        # Create multiple templates
        template_ids = []
        for template_type in [TemplateType.SELECTION, TemplateType.CALIBRATION, 
                             TemplateType.WELL_PLATE, TemplateType.WORKFLOW]:
            if template_type == TemplateType.SELECTION:
                template_data = self.test_selection_template
            elif template_type == TemplateType.CALIBRATION:
                template_data = self.test_calibration_template
            elif template_type == TemplateType.WELL_PLATE:
                template_data = self.test_well_plate_template
            else:  # WORKFLOW
                template_data = self.test_workflow_template
            
            template_id = self.template_manager.create_template(
                template_type,
                template_data,
                f'Batch {template_type.value} Template'
            )
            template_ids.append((template_type, template_id))
        
        # Verify all templates were created
        assert len(template_ids) == 4
        
        # Apply all templates
        applied_configs = []
        for template_type, template_id in template_ids:
            config = self.template_manager.apply_template(template_type, template_id)
            applied_configs.append(config)
        
        # Verify all applications succeeded
        assert len(applied_configs) == 4
        for config in applied_configs:
            assert config is not None
            assert 'metadata' in config
            assert 'name' in config['metadata']
    
    def test_template_performance_headless(self):
        """Test template system performance in headless mode."""
        import time
        
        # Test creation performance
        start_time = time.time()
        
        template_ids = []
        for i in range(50):  # Create 50 templates
            template_data = self.test_selection_template.copy()
            template_data['metadata'] = template_data['metadata'].copy()
            template_data['metadata']['name'] = f'Performance Test Template {i}'
            
            template_id = self.template_manager.create_template(
                TemplateType.SELECTION,
                template_data,
                f'Performance Test Template {i}'
            )
            template_ids.append(template_id)
        
        creation_time = time.time() - start_time
        
        # Should create 50 templates in reasonable time
        assert creation_time < 10.0, f"Template creation too slow: {creation_time:.2f}s"
        
        # Test application performance
        start_time = time.time()
        
        for template_id in template_ids:
            config = self.template_manager.apply_template(TemplateType.SELECTION, template_id)
            assert config is not None
        
        application_time = time.time() - start_time
        
        # Should apply 50 templates in reasonable time
        assert application_time < 5.0, f"Template application too slow: {application_time:.2f}s"
        
        # Test loading performance (create new manager)
        start_time = time.time()
        new_manager = TemplateManager(templates_directory=str(self.template_dir))
        loading_time = time.time() - start_time
        
        # Should load 50 templates in reasonable time
        assert loading_time < 3.0, f"Template loading too slow: {loading_time:.2f}s"
        
        # Verify all templates were loaded
        loaded_templates = new_manager.get_templates_by_type(TemplateType.SELECTION)
        assert len(loaded_templates) == 50


if __name__ == '__main__':
    pytest.main([__file__]) 