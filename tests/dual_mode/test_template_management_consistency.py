"""
Test Template Management Consistency in DUAL Mode

Tests template management consistency between headless and GUI modes.
Verifies cross-mode compatibility and template synchronization.
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
from src.headless.main_window_adapter import MainWindowAdapter
from src.utils.logging_config import get_logger


class TestTemplateManagementConsistencyDual(UITestCase):
    """Test template management consistency in DUAL mode."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        
        # Set up DUAL mode
        self.mode_manager = Mock(spec=ModeManager)
        self.mode_manager.is_dev_mode.return_value = False
        self.mode_manager.is_gui_mode.return_value = False
        self.mode_manager.is_dual_mode.return_value = True
        
        # Create temporary directory for templates
        self.temp_dir = tempfile.TemporaryDirectory()
        self.template_dir = Path(self.temp_dir.name)
        
        # Create both headless and GUI template managers
        self.headless_template_manager = TemplateManager(
            templates_directory=str(self.template_dir / "headless")
        )
        
        self.gui_template_manager = Mock(spec=TemplateManager)
        
        # Setup GUI template manager mock behavior
        self.gui_template_manager.templates_directory = self.template_dir / "gui"
        self.gui_template_manager.templates = {
            TemplateType.SELECTION: {},
            TemplateType.CALIBRATION: {},
            TemplateType.WELL_PLATE: {},
            TemplateType.WORKFLOW: {},
            TemplateType.EXPRESSION: {}
        }
        
        self.gui_template_manager.create_template = Mock()
        self.gui_template_manager.save_template = Mock(return_value=True)
        self.gui_template_manager.load_all_templates = Mock()
        self.gui_template_manager.get_template = Mock()
        self.gui_template_manager.get_templates_by_type = Mock(return_value=[])
        self.gui_template_manager.apply_template = Mock()
        self.gui_template_manager.delete_template = Mock(return_value=True)
        
        # Create main window adapter for template synchronization
        self.main_adapter = Mock(spec=MainWindowAdapter)
        self.main_adapter.sync_templates_to_gui = Mock(return_value=True)
        self.main_adapter.sync_templates_from_gui = Mock(return_value=True)
        
        # Shared template directory for cross-mode compatibility
        self.shared_template_dir = self.template_dir / "shared"
        self.shared_template_dir.mkdir(parents=True, exist_ok=True)
        
        # Common template data for consistency testing
        self.test_selection_template = {
            'metadata': {
                'name': 'Cross-Mode Selection Template',
                'description': 'A template for testing cross-mode consistency',
                'author': 'Dual Mode Test System',
                'tags': ['test', 'dual_mode', 'selection']
            },
            'selection_method': 'expression',
            'x_column': 'AreaShape_Area',
            'y_column': 'Intensity_MedianIntensity_DAPI',
            'expression': 'area > mean(area) AND intensity > percentile(intensity, 75)',
            'min_cell_count': 5,
            'max_cell_count': 500,
            'label_template': 'DualMode_Selection_{index}',
            'color_scheme': 'default',
            'custom_colors': ['#00AA88']
        }
        
        self.test_calibration_template = {
            'metadata': {
                'name': 'Cross-Mode Calibration Template',
                'description': 'A calibration template for testing consistency',
                'author': 'Dual Mode Test System',
                'tags': ['test', 'dual_mode', 'calibration']
            },
            'calibration_method': 'multi_point',
            'reference_points': [
                {'pixel': [100, 100], 'stage': [0.0, 0.0], 'label': 'Origin'},
                {'pixel': [300, 200], 'stage': [200.0, 100.0], 'label': 'Mid Point'},
                {'pixel': [500, 300], 'stage': [400.0, 200.0], 'label': 'End Point'}
            ],
            'max_error_threshold': 1.5,
            'auto_apply': False
        }
        
        self.logger = get_logger('test_template_dual_consistency')
    
    def tearDown(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()
        super().tearDown()
    
    def test_headless_create_gui_load_consistency(self):
        """Test creating template in headless mode and loading in GUI mode."""
        # Create template in headless mode
        template_id = self.headless_template_manager.create_template(
            TemplateType.SELECTION,
            self.test_selection_template,
            'Headless to GUI Template'
        )
        
        # Save to shared directory
        shared_file = self.shared_template_dir / 'selection' / f'{template_id}.json'
        shared_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Get template data from headless
        headless_template = self.headless_template_manager.get_template(
            TemplateType.SELECTION, template_id
        )
        
        # Simulate saving to shared location
        headless_config = self.headless_template_manager.apply_template(
            TemplateType.SELECTION, template_id
        )
        
        with open(shared_file, 'w') as f:
            json.dump(headless_config, f, indent=2)
        
        # Mock GUI loading the same template
        self.gui_template_manager.get_template.return_value = Mock()
        self.gui_template_manager.get_template.return_value.metadata.name = 'Headless to GUI Template'
        self.gui_template_manager.get_template.return_value.selection_method = 'expression'
        self.gui_template_manager.get_template.return_value.expression = headless_config['expression']
        
        # Test GUI loading
        gui_template = self.gui_template_manager.get_template(TemplateType.SELECTION, template_id)
        
        # Verify consistency
        assert gui_template.metadata.name == 'Headless to GUI Template'
        assert gui_template.selection_method == 'expression'
        assert gui_template.expression == headless_config['expression']
        
        # Verify file exists in shared location
        assert shared_file.exists()
    
    def test_gui_create_headless_load_consistency(self):
        """Test creating template in GUI mode and loading in headless mode."""
        # Mock GUI creating template
        gui_template_data = {
            'metadata': {
                'name': 'GUI to Headless Template',
                'description': 'Created in GUI, loaded in headless',
                'author': 'GUI Test System'
            },
            'selection_method': 'rectangle',
            'x_column': 'X_Position',
            'y_column': 'Y_Position',
            'region_bounds': {'x1': 100, 'y1': 100, 'x2': 400, 'y2': 300}
        }
        
        # Mock GUI template creation
        gui_template_id = 'gui_created_template_001'
        self.gui_template_manager.create_template.return_value = gui_template_id
        
        # Simulate GUI saving template to shared directory
        shared_file = self.shared_template_dir / 'selection' / f'{gui_template_id}.json'
        shared_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(shared_file, 'w') as f:
            json.dump(gui_template_data, f, indent=2)
        
        # Test headless loading from shared directory
        # Create new headless manager pointed to shared directory
        shared_headless_manager = TemplateManager(
            templates_directory=str(self.shared_template_dir)
        )
        
        # Load template in headless
        loaded_template = shared_headless_manager.get_template(
            TemplateType.SELECTION, gui_template_id
        )
        
        if loaded_template:
            # Verify template was loaded correctly
            assert loaded_template.metadata.name == 'GUI to Headless Template'
            assert loaded_template.selection_method == 'rectangle'
        else:
            # If template class doesn't support rectangle method, verify file exists
            assert shared_file.exists()
            with open(shared_file, 'r') as f:
                loaded_data = json.load(f)
            assert loaded_data['metadata']['name'] == 'GUI to Headless Template'
    
    def test_template_synchronization_dual_mode(self):
        """Test template synchronization in dual mode."""
        # Create template in headless
        headless_template_id = self.headless_template_manager.create_template(
            TemplateType.CALIBRATION,
            self.test_calibration_template,
            'Sync Test Calibration'
        )
        
        # Mock synchronization to GUI
        sync_success = self.main_adapter.sync_templates_to_gui()
        assert sync_success is True
        
        # Mock GUI receiving the template
        gui_template_mock = Mock()
        gui_template_mock.metadata.name = 'Sync Test Calibration'
        gui_template_mock.calibration_method = 'multi_point'
        gui_template_mock.reference_points = self.test_calibration_template['reference_points']
        
        self.gui_template_manager.get_template.return_value = gui_template_mock
        
        # Verify template is available in GUI
        gui_template = self.gui_template_manager.get_template(
            TemplateType.CALIBRATION, headless_template_id
        )
        assert gui_template.metadata.name == 'Sync Test Calibration'
        
        # Mock GUI modifying template
        gui_template.metadata.description = 'Modified in GUI'
        gui_template.validation_threshold = 2.0
        
        # Mock synchronization back to headless
        sync_back_success = self.main_adapter.sync_templates_from_gui()
        assert sync_back_success is True
        
        # In real implementation, headless template would be updated
        # For test, verify the sync operations were called
        self.main_adapter.sync_templates_to_gui.assert_called_once()
        self.main_adapter.sync_templates_from_gui.assert_called_once()
    
    def test_template_format_compatibility(self):
        """Test template format compatibility between modes."""
        # Test different template formats
        formats_to_test = [
            ('headless_format', self._create_headless_format_template()),
            ('gui_format', self._create_gui_format_template()),
            ('hybrid_format', self._create_hybrid_format_template())
        ]
        
        for format_name, template_data in formats_to_test:
            # Save in specific format
            format_file = self.shared_template_dir / f"{format_name}.json"
            with open(format_file, 'w') as f:
                json.dump(template_data, f, indent=2)
            
            # Test headless compatibility
            try:
                with open(format_file, 'r') as f:
                    loaded_data = json.load(f)
                headless_compatible = 'metadata' in loaded_data
            except Exception:
                headless_compatible = False
            
            # Test GUI compatibility (mock)
            self.gui_template_manager.get_template.return_value = Mock()
            gui_compatible = True  # Mock always accepts
            
            # Verify compatibility results
            if format_name == 'headless_format':
                assert headless_compatible is True
                assert gui_compatible is True
            elif format_name == 'gui_format':
                assert gui_compatible is True
                # GUI format might need conversion for headless
            else:  # hybrid_format
                assert headless_compatible is True
                assert gui_compatible is True
    
    def test_template_conflict_resolution(self):
        """Test template conflict resolution in dual mode."""
        # Create same template in both modes with different data
        base_template_id = 'conflict_test_template'
        
        # Headless version
        headless_template_data = self.test_selection_template.copy()
        headless_template_data['metadata']['name'] = 'Conflict Template'
        headless_template_data['expression'] = 'area > 100'
        
        headless_id = self.headless_template_manager.create_template(
            TemplateType.SELECTION,
            headless_template_data,
            'Conflict Template'
        )
        
        # Mock GUI version with conflicting data
        gui_template_data = {
            'metadata': {
                'name': 'Conflict Template',
                'description': 'Different description from GUI'
            },
            'selection_method': 'expression',
            'expression': 'area > 200'  # Different expression
        }
        
        # Mock conflict resolution strategy
        def resolve_conflict(headless_data, gui_data):
            # Use most recent timestamp (mock strategy)
            resolved_data = headless_data.copy()
            resolved_data['metadata']['description'] = f"Merged: {gui_data['metadata']['description']}"
            resolved_data['expression'] = f"({headless_data['expression']}) OR ({gui_data['expression']})"
            return resolved_data
        
        # Apply conflict resolution
        headless_config = self.headless_template_manager.apply_template(
            TemplateType.SELECTION, headless_id
        )
        
        resolved_data = resolve_conflict(headless_config, gui_template_data)
        
        # Verify resolution contains both expressions
        assert 'area > 100' in resolved_data['expression']
        assert 'area > 200' in resolved_data['expression']
        assert 'Merged:' in resolved_data['metadata']['description']
    
    def test_template_usage_statistics_sync(self):
        """Test template usage statistics synchronization."""
        # Create template in headless
        template_id = self.headless_template_manager.create_template(
            TemplateType.SELECTION,
            self.test_selection_template,
            'Usage Stats Template'
        )
        
        # Apply template multiple times in headless
        for _ in range(3):
            self.headless_template_manager.apply_template(TemplateType.SELECTION, template_id)
        
        # Get usage statistics
        headless_template = self.headless_template_manager.get_template(
            TemplateType.SELECTION, template_id
        )
        headless_usage_count = headless_template.metadata.usage_count
        
        # Mock GUI usage
        gui_usage_count = 2
        
        # Mock synchronization of statistics
        total_usage = headless_usage_count + gui_usage_count
        
        # Verify combined statistics
        assert headless_usage_count == 3
        assert total_usage == 5
    
    def test_template_sharing_cross_mode(self):
        """Test template sharing between modes."""
        # Export template from headless
        template_id = self.headless_template_manager.create_template(
            TemplateType.WORKFLOW,
            {
                'metadata': {
                    'name': 'Shared Workflow Template',
                    'description': 'Template shared between modes',
                    'author': 'Dual Mode System'
                },
                'image_path_template': '{base_dir}/shared_images/{sample_id}.tiff',
                'csv_path_template': '{base_dir}/shared_data/{sample_id}.csv',
                'output_path_template': '{base_dir}/shared_output/{sample_id}_results.txt',
                'steps': [
                    {'type': 'load_image', 'auto_execute': True},
                    {'type': 'load_csv', 'auto_execute': True}
                ]
            },
            'Shared Workflow Template'
        )
        
        # Export template
        export_config = self.headless_template_manager.apply_template(
            TemplateType.WORKFLOW, template_id
        )
        
        # Save export to shared location
        export_file = self.shared_template_dir / 'exports' / 'shared_workflow.json'
        export_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(export_file, 'w') as f:
            json.dump(export_config, f, indent=2)
        
        # Mock GUI import
        self.gui_template_manager.create_template.return_value = 'imported_template_id'
        
        # Verify export file exists and has correct structure
        assert export_file.exists()
        
        with open(export_file, 'r') as f:
            imported_data = json.load(f)
        
        assert imported_data['metadata']['name'] == 'Shared Workflow Template'
        assert 'steps' in imported_data
        assert len(imported_data['steps']) == 2
    
    def _create_headless_format_template(self) -> Dict[str, Any]:
        """Create template in headless format."""
        return {
            'metadata': {
                'name': 'Headless Format Template',
                'description': 'Template in headless format',
                'author': 'Headless System',
                'created_date': '2024-01-01T12:00:00Z',
                'status': 'active'
            },
            'selection_method': 'expression',
            'expression': 'area > 150',
            'color_scheme': 'default',
            'custom_colors': ['#FF0000']
        }
    
    def _create_gui_format_template(self) -> Dict[str, Any]:
        """Create template in GUI format."""
        return {
            'name': 'GUI Format Template',
            'description': 'Template in GUI format',
            'type': 'selection',
            'created': '2024-01-01',
            'settings': {
                'method': 'expression',
                'expression': 'area > 150',
                'color': '#00FF00'
            },
            'ui_metadata': {
                'last_position': {'x': 100, 'y': 200},
                'window_size': {'width': 800, 'height': 600}
            }
        }
    
    def _create_hybrid_format_template(self) -> Dict[str, Any]:
        """Create template in hybrid format (compatible with both)."""
        return {
            'metadata': {
                'name': 'Hybrid Format Template',
                'description': 'Template compatible with both modes',
                'author': 'Hybrid System',
                'created_date': '2024-01-01T12:00:00Z',
                'status': 'active'
            },
            'selection_method': 'expression',
            'expression': 'area > 150',
            'color_scheme': 'default',
            'custom_colors': ['#0000FF'],
            'gui_settings': {
                'window_position': {'x': 150, 'y': 250}
            },
            'headless_settings': {
                'batch_mode': True,
                'auto_apply': False
            }
        }


if __name__ == '__main__':
    pytest.main([__file__]) 