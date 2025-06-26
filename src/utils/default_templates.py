"""
Default Template Generator for CellSorter (TASK-021)

Creates a comprehensive set of default templates covering common use cases
for different user personas and workflows.
"""

from typing import Dict, List, Any
from models.template_manager import TemplateManager, TemplateType
from utils.logging_config import LoggerMixin


class DefaultTemplateGenerator(LoggerMixin):
    """Generator for default template library."""
    
    def __init__(self, template_manager: TemplateManager):
        self.template_manager = template_manager
    
    def create_all_default_templates(self) -> Dict[str, List[str]]:
        """Create all default templates."""
        created_templates = {
            'selection': self.create_selection_templates(),
            'calibration': self.create_calibration_templates(),
            'well_plate': self.create_well_plate_templates(),
            'workflow': self.create_workflow_templates()
        }
        
        total_created = sum(len(ids) for ids in created_templates.values())
        self.log_info(f"Created {total_created} default templates")
        
        return created_templates
    
    def create_selection_templates(self) -> List[str]:
        """Create default selection templates."""
        templates = [
            {
                'metadata': {
                    'name': 'Basic Rectangle Selection',
                    'description': 'Simple rectangle-based cell selection',
                    'author': 'CellSorter',
                    'tags': ['basic', 'manual', 'beginner']
                },
                'selection_method': 'rectangle',
                'x_column': 'AreaShape_Area',
                'y_column': 'Intensity_MedianIntensity_DAPI',
                'min_cell_count': 1,
                'max_cell_count': 10000
            },
            {
                'metadata': {
                    'name': 'High Area Cells',
                    'description': 'Cells with area above population mean',
                    'author': 'CellSorter',
                    'tags': ['expression', 'area']
                },
                'selection_method': 'expression',
                'x_column': 'AreaShape_Area',
                'y_column': 'Intensity_MedianIntensity_DAPI',
                'expression': 'area > mean(area)',
                'min_cell_count': 5,
                'max_cell_count': 50000
            },
            {
                'metadata': {
                    'name': 'Advanced Pathology Selection',
                    'description': 'Complex expression for cancer research',
                    'author': 'CellSorter',
                    'tags': ['expression', 'pathology', 'expert']
                },
                'selection_method': 'expression',
                'x_column': 'AreaShape_Area',
                'y_column': 'Intensity_MedianIntensity_DAPI',
                'expression': 'area > mean(area) + 2*std(area) AND intensity > percentile(intensity, 80)',
                'min_cell_count': 10,
                'max_cell_count': 1000
            }
        ]
        
        created_ids = []
        for template_data in templates:
            template_id = self.template_manager.create_template(
                TemplateType.SELECTION,
                template_data,
                template_data['metadata']['name']
            )
            created_ids.append(template_id)
        
        return created_ids
    
    def create_calibration_templates(self) -> List[str]:
        """Create default calibration templates."""
        templates = [
            {
                'metadata': {
                    'name': 'Standard Two-Point Calibration',
                    'description': 'Standard calibration for most setups',
                    'author': 'CellSorter',
                    'tags': ['calibration', 'standard']
                },
                'calibration_method': 'two_point',
                'min_distance_pixels': 100,
                'max_error_threshold': 2.0
            }
        ]
        
        created_ids = []
        for template_data in templates:
            template_id = self.template_manager.create_template(
                TemplateType.CALIBRATION,
                template_data,
                template_data['metadata']['name']
            )
            created_ids.append(template_id)
        
        return created_ids
    
    def create_well_plate_templates(self) -> List[str]:
        """Create default well plate templates."""
        templates = [
            {
                'metadata': {
                    'name': 'Standard 96-Well Sequential',
                    'description': 'Sequential filling of 96-well plate',
                    'author': 'CellSorter',
                    'tags': ['96-well', 'sequential']
                },
                'plate_type': '96_well',
                'assignment_strategy': 'sequential',
                'max_cells_per_well': 1000,
                'min_cells_per_well': 10
            }
        ]
        
        created_ids = []
        for template_data in templates:
            template_id = self.template_manager.create_template(
                TemplateType.WELL_PLATE,
                template_data,
                template_data['metadata']['name']
            )
            created_ids.append(template_id)
        
        return created_ids
    
    def create_workflow_templates(self) -> List[str]:
        """Create default workflow templates."""
        templates = [
            {
                'metadata': {
                    'name': 'Standard Analysis Workflow',
                    'description': 'Complete workflow for standard analysis',
                    'author': 'CellSorter',
                    'tags': ['workflow', 'standard']
                },
                'image_path_template': 'images/{sample_id}.tiff',
                'csv_path_template': 'data/{sample_id}_features.csv',
                'output_path_template': 'protocols/{sample_id}.cxprotocol',
                'auto_execute': False,
                'validate_steps': True
            }
        ]
        
        created_ids = []
        for template_data in templates:
            template_id = self.template_manager.create_template(
                TemplateType.WORKFLOW,
                template_data,
                template_data['metadata']['name']
            )
            created_ids.append(template_id)
        
        return created_ids


def initialize_default_templates(template_manager: TemplateManager) -> Dict[str, int]:
    """Initialize default templates for new installation."""
    generator = DefaultTemplateGenerator(template_manager)
    
    # Check if templates already exist
    existing_count = sum(
        len(template_manager.get_templates_by_type(template_type))
        for template_type in [TemplateType.SELECTION, TemplateType.CALIBRATION,
                             TemplateType.WELL_PLATE, TemplateType.WORKFLOW]
    )
    
    if existing_count == 0:
        created = generator.create_all_default_templates()
        return {
            'selection': len(created['selection']),
            'calibration': len(created['calibration']),
            'well_plate': len(created['well_plate']),
            'workflow': len(created['workflow'])
        }
    
    return {'selection': 0, 'calibration': 0, 'well_plate': 0, 'workflow': 0}
