"""
Integration tests for Phase 2 components
"""

import pytest
import numpy as np
import pandas as pd
from PySide6.QtWidgets import QApplication

from models.coordinate_transformer import CoordinateTransformer, CalibrationPoint
from models.selection_manager import SelectionManager, SelectionStatus
from models.extractor import Extractor, BoundingBox
from components.widgets.scatter_plot import ScatterPlotWidget


class TestPhase2Integration:
    """Test integration of Phase 2 components."""
    
    @pytest.fixture
    def sample_dataframe(self):
        """Create sample DataFrame for testing."""
        np.random.seed(42)
        data = {
            'Intensity_MedianIntensity_Ki67': np.random.uniform(0, 1000, 50),
            'Intensity_MedianIntensity_CK20': np.random.uniform(0, 800, 50),
            'AreaShape_BoundingBoxMinimum_X': np.random.uniform(0, 1000, 50),
            'AreaShape_BoundingBoxMinimum_Y': np.random.uniform(0, 1000, 50),
            'AreaShape_BoundingBoxMaximum_X': np.random.uniform(1010, 1100, 50),
            'AreaShape_BoundingBoxMaximum_Y': np.random.uniform(1010, 1100, 50),
        }
        return pd.DataFrame(data)
    
    @pytest.fixture
    def coordinate_transformer(self):
        """Create coordinate transformer with calibration."""
        transformer = CoordinateTransformer()
        
        # Add calibration points
        transformer.add_calibration_point(100, 100, 1000.0, 2000.0, "Point 1")
        transformer.add_calibration_point(900, 800, 9000.0, 8000.0, "Point 2")
        
        return transformer
    
    @pytest.fixture
    def selection_manager(self):
        """Create selection manager with test data."""
        manager = SelectionManager()
        
        # Add some test selections with indices that exist in our test data
        manager.add_selection([0, 1, 2], "Test Selection 1")
        manager.add_selection([3, 4], "Test Selection 2")
        
        return manager
    
    def test_scatter_plot_widget_basic_functionality(self, qapp, sample_dataframe):
        """Test basic scatter plot widget functionality."""
        widget = ScatterPlotWidget()
        
        # Load data
        widget.load_data(sample_dataframe)
        
        # Check that data was loaded
        assert widget.dataframe is not None
        assert len(widget.numeric_columns) > 0
        assert 'Intensity_MedianIntensity_Ki67' in widget.numeric_columns
        assert 'Intensity_MedianIntensity_CK20' in widget.numeric_columns
        
        # Create plot
        widget.create_plot()
        
        # Check plot was created
        assert widget.canvas.x_data is not None
        assert widget.canvas.y_data is not None
        assert len(widget.canvas.x_data) == len(sample_dataframe)
    
    def test_coordinate_transformer_workflow(self, coordinate_transformer):
        """Test coordinate transformation workflow."""
        # Check calibration is valid
        assert coordinate_transformer.is_calibrated
        assert len(coordinate_transformer.calibration_points) == 2
        
        # Test transformation
        result = coordinate_transformer.pixel_to_stage(500, 400)
        assert result is not None
        assert isinstance(result.stage_x, float)
        assert isinstance(result.stage_y, float)
        assert result.confidence > 0
        
        # Test inverse transformation
        pixel_coords = coordinate_transformer.stage_to_pixel(result.stage_x, result.stage_y)
        assert pixel_coords is not None
        
        # Should be close to original coordinates (within reasonable tolerance)
        assert abs(pixel_coords[0] - 500) < 10
        assert abs(pixel_coords[1] - 400) < 10
    
    def test_selection_manager_workflow(self, selection_manager):
        """Test selection manager workflow."""
        # Check initial state
        assert len(selection_manager.selections) == 2
        assert len(selection_manager.used_colors) == 2
        assert len(selection_manager.used_wells) == 2
        
        # Get selection table data
        table_data = selection_manager.get_selection_table_data()
        assert len(table_data) == 2
        
        # Check first selection
        first_selection = table_data[0]
        assert first_selection['enabled'] == True
        assert first_selection['cell_count'] == 3
        assert first_selection['well'] == 'A01'
        
        # Test statistics
        stats = selection_manager.get_statistics()
        assert stats['total_selections'] == 2
        assert stats['active_selections'] == 2
        assert stats['total_cells'] == 5  # 3 + 2
        
        # Test export data
        export_data = selection_manager.export_selections_data()
        assert len(export_data) == 2
        assert all('cell_indices' in item for item in export_data)
    
    def test_extractor_workflow(self, coordinate_transformer, selection_manager):
        """Test extractor workflow."""
        extractor = Extractor()
        
        # Create test bounding boxes
        bounding_boxes = [
            BoundingBox(100, 100, 150, 150),
            BoundingBox(200, 200, 250, 250),
            BoundingBox(300, 300, 350, 350),
            BoundingBox(400, 400, 450, 450),
            BoundingBox(500, 500, 550, 550),
        ]
        
        # Get selections data
        selections_data = selection_manager.export_selections_data()
        
        # Create extraction points
        extraction_points = extractor.create_extraction_points(
            selections_data, bounding_boxes, coordinate_transformer, (1000, 1000)
        )
        
        # Should have points for all selected cells
        expected_points = sum(len(sel['cell_indices']) for sel in selections_data)
        assert len(extraction_points) == expected_points
        
        # Check extraction point properties
        for point in extraction_points:
            assert hasattr(point, 'id')
            assert hasattr(point, 'label')
            assert hasattr(point, 'color')
            assert hasattr(point, 'well_position')
            assert hasattr(point, 'crop_region')
            assert point.crop_region.size > 0
    
    def test_end_to_end_workflow(self, qapp, sample_dataframe, coordinate_transformer):
        """Test complete end-to-end workflow."""
        # 1. Create components
        scatter_plot = ScatterPlotWidget()
        selection_manager = SelectionManager()
        extractor = Extractor()
        
        # 2. Load data into scatter plot
        scatter_plot.load_data(sample_dataframe)
        scatter_plot.create_plot()
        
        # 3. Simulate selections
        selection_manager.add_selection([0, 1, 2], "High Ki67")
        selection_manager.add_selection([10, 15, 20], "High CK20")
        
        # 4. Create bounding boxes from DataFrame
        bounding_boxes = []
        for _, row in sample_dataframe.iterrows():
            bbox = BoundingBox(
                row['AreaShape_BoundingBoxMinimum_X'],
                row['AreaShape_BoundingBoxMinimum_Y'],
                row['AreaShape_BoundingBoxMaximum_X'],
                row['AreaShape_BoundingBoxMaximum_Y']
            )
            bounding_boxes.append(bbox)
        
        # 5. Generate extraction points
        selections_data = selection_manager.export_selections_data()
        extraction_points = extractor.create_extraction_points(
            selections_data, bounding_boxes, coordinate_transformer, (2048, 2048)
        )
        
        # 6. Verify results
        assert len(extraction_points) == 6  # 3 + 3 cells selected
        
        # Check that each point has valid coordinates in stage space
        for point in extraction_points:
            assert point.crop_region.min_x < point.crop_region.max_x
            assert point.crop_region.min_y < point.crop_region.max_y
            assert point.crop_region.size > 0
            assert point.well_position in ['A01', 'B01']  # First two wells
        
        # 7. Test statistics
        stats = extractor.get_extraction_statistics(extraction_points)
        assert stats['total_points'] == 6
        assert stats['unique_wells'] == 2
        assert stats['unique_colors'] == 2
        assert stats['average_crop_size'] > 0
    
    def test_component_signal_integration(self, qapp, sample_dataframe):
        """Test signal communication between components."""
        # Create components
        scatter_plot = ScatterPlotWidget()
        selection_manager = SelectionManager()
        
        # Track signals
        selection_signals = []
        manager_signals = []
        
        def on_selection_made(indices):
            selection_signals.append(indices)
        
        def on_selection_added(selection_id):
            manager_signals.append(selection_id)
        
        # Connect signals
        scatter_plot.selection_made.connect(on_selection_made)
        selection_manager.selection_added.connect(on_selection_added)
        
        # Load data and create plot
        scatter_plot.load_data(sample_dataframe)
        scatter_plot.create_plot()
        
        # Simulate selection
        test_indices = [0, 1, 2, 3, 4]
        scatter_plot.canvas.selected_indices = test_indices
        scatter_plot.canvas.selection_changed.emit(test_indices)
        
        # Add selection to manager
        selection_id = selection_manager.add_selection(test_indices, "Test Selection")
        
        # Verify signals were emitted
        assert len(selection_signals) == 1
        assert selection_signals[0] == test_indices
        assert len(manager_signals) == 1
        assert manager_signals[0] == selection_id
        
        # Verify selection was added
        selection = selection_manager.get_selection(selection_id)
        assert selection is not None
        assert selection.cell_indices == test_indices
        assert selection.label == "Test Selection"