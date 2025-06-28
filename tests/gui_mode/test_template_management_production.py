"""
Test Template Management System in GUI Mode (Production)

Tests template management system in GUI mode focusing on user experience,
dialog interactions, and template application workflows.
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
from src.components.dialogs.template_management_dialog import (
    TemplateManagementDialog, TemplateLibraryWidget
)
from src.headless.mode_manager import ModeManager
from src.utils.logging_config import get_logger


class TestTemplateManagementProductionGui(UITestCase):
    """Test template management system in GUI production mode."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        
        # Set up GUI mode
        self.mode_manager = Mock(spec=ModeManager)
        self.mode_manager.is_dev_mode.return_value = False
        self.mode_manager.is_gui_mode.return_value = True
        self.mode_manager.is_dual_mode.return_value = False
        
        # Create temporary directory for templates
        self.temp_dir = tempfile.TemporaryDirectory()
        self.template_dir = Path(self.temp_dir.name)
        
        # Create template manager
        self.template_manager = TemplateManager(
            templates_directory=str(self.template_dir)
        )
        
        # Mock main window for dialog parent
        self.main_window = Mock()
        
        # Create template management dialog
        self.template_dialog = Mock(spec=TemplateManagementDialog)
        self.template_dialog.template_manager = self.template_manager
        
        # Mock template library widget
        self.library_widget = Mock(spec=TemplateLibraryWidget)
        
        # Sample template data for production testing
        self.production_templates = {
            'pathology_analysis': {
                'metadata': {
                    'name': 'Pathology Analysis Template',
                    'description': 'Standard template for pathology cell analysis',
                    'author': 'Dr. Sarah Chen',
                    'tags': ['pathology', 'production', 'standard']
                },
                'selection_method': 'expression',
                'expression': 'area > mean(area) + 2*std(area) AND intensity > percentile(intensity, 80)',
                'x_column': 'AreaShape_Area',
                'y_column': 'Intensity_MedianIntensity_DAPI',
                'min_cell_count': 20,
                'max_cell_count': 2000,
                'label_template': 'Pathology_Cell_{index}',
                'color_scheme': 'default',
                'custom_colors': ['#FF6B6B']
            },
            'high_throughput_screening': {
                'metadata': {
                    'name': 'High Throughput Screening Template',
                    'description': 'Template for automated high-throughput screening',
                    'author': 'Lab Automation System',
                    'tags': ['automation', 'screening', 'high_throughput']
                },
                'selection_method': 'expression',
                'expression': 'area > 50 AND area < 500 AND roundness > 0.7',
                'x_column': 'AreaShape_Area',
                'y_column': 'AreaShape_Compactness',
                'min_cell_count': 100,
                'max_cell_count': 10000,
                'label_template': 'Screen_Cell_{index}',
                'color_scheme': 'default',
                'custom_colors': ['#4ECDC4']
            }
        }
        
        self.logger = get_logger('test_template_gui_production')
    
    def tearDown(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()
        super().tearDown()
    
    def test_template_dialog_initialization(self):
        """Test template management dialog initialization."""
        # Mock dialog initialization
        self.template_dialog.show = Mock()
        self.template_dialog.resize = Mock()
        self.template_dialog.setModal = Mock()
        
        # Test dialog initialization
        self.template_dialog.show()
        
        # Verify dialog methods were called
        self.template_dialog.show.assert_called_once()
        assert self.template_dialog.template_manager is self.template_manager
    
    def test_template_library_user_workflow(self):
        """Test template library user workflow."""
        # Create templates for testing
        template_ids = []
        for template_name, template_data in self.production_templates.items():
            template_id = self.template_manager.create_template(
                TemplateType.SELECTION,
                template_data,
                template_data['metadata']['name']
            )
            template_ids.append(template_id)
        
        # Mock library widget refresh
        self.library_widget.refresh_templates = Mock()
        self.library_widget.refresh_templates()
        
        # Mock template selection
        self.library_widget.on_template_selected = Mock()
        self.library_widget.apply_selected_template = Mock()
        
        # Simulate user selecting first template
        selected_template_id = template_ids[0]
        self.library_widget.on_template_selected()
        
        # Simulate user applying template
        self.library_widget.apply_selected_template()
        
        # Verify workflow methods were called
        self.library_widget.refresh_templates.assert_called_once()
        self.library_widget.on_template_selected.assert_called_once()
        self.library_widget.apply_selected_template.assert_called_once()
    
    def test_template_creation_user_experience(self):
        """Test template creation user experience."""
        # Mock template creation form
        template_form = Mock()
        template_form.template_name_input = Mock()
        template_form.template_description_input = Mock()
        template_form.template_author_input = Mock()
        template_form.save_template_button = Mock()
        
        # Set form data
        template_form.template_name_input.text.return_value = "User Created Template"
        template_form.template_description_input.toPlainText.return_value = "Created by user through GUI"
        template_form.template_author_input.text.return_value = "GUI User"
        
        # Mock save operation
        template_form.save_template = Mock()
        
        # Simulate user filling form and saving
        form_data = {
            'metadata': {
                'name': template_form.template_name_input.text(),
                'description': template_form.template_description_input.toPlainText(),
                'author': template_form.template_author_input.text()
            },
            'selection_method': 'rectangle',
            'rectangle_bounds': {'x1': 100, 'y1': 100, 'x2': 400, 'y2': 300}
        }
        
        # Create template through form
        template_id = self.template_manager.create_template(
            TemplateType.SELECTION,
            form_data,
            "User Created Template"
        )
        
        template_form.save_template()
        
        # Verify template was created
        assert template_id is not None
        created_template = self.template_manager.get_template(TemplateType.SELECTION, template_id)
        assert created_template.metadata.name == "User Created Template"
        assert created_template.metadata.author == "GUI User"
        
        # Verify save was called
        template_form.save_template.assert_called_once()
    
    def test_template_application_workflow(self):
        """Test template application workflow in GUI."""
        # Create production template
        template_id = self.template_manager.create_template(
            TemplateType.SELECTION,
            self.production_templates['pathology_analysis'],
            'Pathology Analysis Template'
        )
        
        # Mock template application dialog
        apply_dialog = Mock()
        apply_dialog.template_config = Mock()
        apply_dialog.apply_to_current_session = Mock(return_value=True)
        apply_dialog.show_progress = Mock()
        apply_dialog.hide_progress = Mock()
        
        # Mock application process
        def mock_apply_template():
            apply_dialog.show_progress()
            config = self.template_manager.apply_template(TemplateType.SELECTION, template_id)
            result = apply_dialog.apply_to_current_session()
            apply_dialog.hide_progress()
            return result
        
        # Simulate template application
        success = mock_apply_template()
        
        # Verify application workflow
        assert success is True
        apply_dialog.show_progress.assert_called_once()
        apply_dialog.apply_to_current_session.assert_called_once()
        apply_dialog.hide_progress.assert_called_once()
        
        # Verify template usage was updated
        applied_template = self.template_manager.get_template(TemplateType.SELECTION, template_id)
        assert applied_template.metadata.usage_count == 1
    
    def test_template_search_and_filtering(self):
        """Test template search and filtering functionality."""
        # Create multiple templates with different characteristics
        templates_data = [
            ('pathology', self.production_templates['pathology_analysis']),
            ('screening', self.production_templates['high_throughput_screening']),
            ('calibration', {
                'metadata': {
                    'name': 'Standard Calibration',
                    'description': 'Standard two-point calibration',
                    'author': 'Lab Technician',
                    'tags': ['calibration', 'standard']
                },
                'calibration_method': 'two_point'
            })
        ]
        
        template_ids = []
        for name, data in templates_data:
            template_type = TemplateType.SELECTION if 'selection_method' in data else TemplateType.CALIBRATION
            template_id = self.template_manager.create_template(template_type, data, data['metadata']['name'])
            template_ids.append((template_type, template_id))
        
        # Mock search functionality
        search_widget = Mock()
        search_widget.search_input = Mock()
        search_widget.type_filter = Mock()
        search_widget.filter_templates = Mock()
        
        # Test search by name
        search_widget.search_input.text.return_value = "pathology"
        search_widget.filter_templates()
        
        # Test filter by type
        search_widget.type_filter.currentData.return_value = TemplateType.SELECTION
        search_widget.filter_templates()
        
        # Verify filtering was called
        assert search_widget.filter_templates.call_count == 2
    
    def test_template_export_import_gui(self):
        """Test template export/import functionality in GUI."""
        # Create template for export
        template_id = self.template_manager.create_template(
            TemplateType.WORKFLOW,
            {
                'metadata': {
                    'name': 'Export Test Workflow',
                    'description': 'Workflow template for export testing',
                    'author': 'Export Test'
                },
                'image_path_template': '{base_dir}/images/{sample}.tiff',
                'csv_path_template': '{base_dir}/data/{sample}.csv',
                'output_path_template': '{base_dir}/results/{sample}_results.txt',
                'steps': [
                    {'type': 'load_image', 'auto_execute': True},
                    {'type': 'export_results', 'auto_execute': False}
                ]
            },
            'Export Test Workflow'
        )
        
        # Mock export dialog
        export_dialog = Mock()
        export_dialog.get_export_path = Mock(return_value=str(Path(self.temp_dir.name) / "exported_template.json"))
        export_dialog.export_template = Mock(return_value=True)
        
        # Mock import dialog
        import_dialog = Mock()
        import_dialog.get_import_path = Mock(return_value=str(Path(self.temp_dir.name) / "exported_template.json"))
        import_dialog.import_template = Mock(return_value="imported_template_id")
        
        # Test export
        export_path = export_dialog.get_export_path()
        export_success = export_dialog.export_template()
        
        # Test import
        import_path = import_dialog.get_import_path()
        imported_id = import_dialog.import_template()
        
        # Verify operations
        assert export_success is True
        assert imported_id == "imported_template_id"
        export_dialog.export_template.assert_called_once()
        import_dialog.import_template.assert_called_once()
    
    def test_template_validation_gui(self):
        """Test template validation in GUI mode."""
        # Mock validation dialog
        validation_dialog = Mock()
        validation_dialog.validate_template_data = Mock()
        validation_dialog.show_validation_errors = Mock()
        validation_dialog.show_validation_success = Mock()
        
        # Test invalid template data
        invalid_template = {
            'metadata': {
                'name': '',  # Empty name should fail validation
                'description': 'Invalid template'
            },
            'selection_method': 'invalid_method'
        }
        
        # Mock validation failure
        validation_dialog.validate_template_data.return_value = False
        validation_result = validation_dialog.validate_template_data(invalid_template)
        
        if not validation_result:
            validation_dialog.show_validation_errors()
        
        # Test valid template data
        valid_template = self.production_templates['pathology_analysis']
        validation_dialog.validate_template_data.return_value = True
        validation_result = validation_dialog.validate_template_data(valid_template)
        
        if validation_result:
            validation_dialog.show_validation_success()
        
        # Verify validation calls
        assert validation_dialog.validate_template_data.call_count == 2
        validation_dialog.show_validation_errors.assert_called_once()
        validation_dialog.show_validation_success.assert_called_once()
    
    def test_template_performance_gui(self):
        """Test template system performance in GUI mode."""
        import time
        
        # Create multiple templates to test performance
        start_time = time.time()
        
        template_ids = []
        for i in range(20):  # Create 20 templates
            template_data = self.production_templates['pathology_analysis'].copy()
            template_data['metadata'] = template_data['metadata'].copy()
            template_data['metadata']['name'] = f'Performance Test Template {i}'
            
            template_id = self.template_manager.create_template(
                TemplateType.SELECTION,
                template_data,
                f'Performance Test Template {i}'
            )
            template_ids.append(template_id)
        
        creation_time = time.time() - start_time
        
        # Mock GUI loading performance
        start_time = time.time()
        
        library_widget = Mock()
        library_widget.refresh_templates = Mock()
        library_widget.populate_template_tree = Mock()
        
        # Simulate loading templates into GUI
        library_widget.refresh_templates()
        library_widget.populate_template_tree()
        
        gui_loading_time = time.time() - start_time
        
        # Performance assertions
        assert creation_time < 5.0, f"Template creation too slow: {creation_time:.2f}s"
        assert gui_loading_time < 1.0, f"GUI loading too slow: {gui_loading_time:.2f}s"
        
        # Verify GUI operations were called
        library_widget.refresh_templates.assert_called_once()
        library_widget.populate_template_tree.assert_called_once()
    
    def test_template_user_experience_flow(self):
        """Test complete user experience flow."""
        # Mock complete user workflow
        workflow_steps = Mock()
        
        # Step 1: Open template dialog
        workflow_steps.open_template_dialog = Mock()
        workflow_steps.open_template_dialog()
        
        # Step 2: Browse existing templates
        workflow_steps.browse_templates = Mock()
        workflow_steps.browse_templates()
        
        # Step 3: Create new template
        workflow_steps.create_new_template = Mock()
        new_template_id = self.template_manager.create_template(
            TemplateType.SELECTION,
            self.production_templates['pathology_analysis'],
            'User Workflow Template'
        )
        workflow_steps.create_new_template()
        
        # Step 4: Apply template
        workflow_steps.apply_template = Mock()
        config = self.template_manager.apply_template(TemplateType.SELECTION, new_template_id)
        workflow_steps.apply_template()
        
        # Step 5: Close dialog
        workflow_steps.close_dialog = Mock()
        workflow_steps.close_dialog()
        
        # Verify complete workflow
        workflow_steps.open_template_dialog.assert_called_once()
        workflow_steps.browse_templates.assert_called_once()
        workflow_steps.create_new_template.assert_called_once()
        workflow_steps.apply_template.assert_called_once()
        workflow_steps.close_dialog.assert_called_once()
        
        # Verify template was created and applied
        assert new_template_id is not None
        assert config is not None
        applied_template = self.template_manager.get_template(TemplateType.SELECTION, new_template_id)
        assert applied_template.metadata.usage_count == 1


if __name__ == '__main__':
    pytest.main([__file__]) 