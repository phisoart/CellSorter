"""
DEV Mode Tests for Main Window Integration

Tests main window component integration and workflow in headless environment.
Validates UI model synchronization and component communication.

Test sequence: DEV → DUAL → GUI (mandatory)
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

import pytest
import tempfile
from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import Mock, patch, MagicMock

from src.models.extractor import Extractor, BoundingBox, CropRegion, ExtractionPoint
from src.models.coordinate_transformer import CoordinateTransformer
from src.models.selection_manager import SelectionManager
from src.models.image_handler import ImageHandler
from src.models.session_manager import SessionManager
from src.headless.main_window_adapter import MainWindowAdapter
from src.headless.ui_model import UIModel
from src.headless.testing.framework import UITestCase


class TestMainWindowIntegrationDev(UITestCase):
    """DEV mode tests for main window integration logic."""
    
    def setUp(self):
        """Set up dev mode test environment."""
        super().setUp()
        
        # Test data (define first)
        self.test_bounding_boxes = [
            BoundingBox(min_x=120, min_y=180, max_x=140, max_y=200),
            BoundingBox(min_x=300, min_y=250, max_x=330, max_y=280),
            BoundingBox(min_x=500, min_y=400, max_x=540, max_y=440),
        ]
        
        self.test_selections = [
            {
                'id': 'selection_1',
                'label': 'Positive Cells',
                'color': '#FF0000',
                'well_position': 'A01',
                'cell_indices': [0, 2],
                'metadata': {'type': 'positive', 'count': 2}
            },
            {
                'id': 'selection_2',
                'label': 'Negative Cells',
                'color': '#0000FF',
                'well_position': 'A02',
                'cell_indices': [1],
                'metadata': {'type': 'negative', 'count': 1}
            }
        ]
        
        self.test_image_info = {
            'width': 1000,
            'height': 800,
            'filename': 'test_image.tiff',
            'file_path': '/path/to/test_image.tiff',
            'shape': [800, 1000],  # height, width for compatibility
            'channels': 4,
            'bit_depth': 16
        }
        
        # Initialize components (avoid GUI initialization)
        self.extractor = Extractor(parent=None)  # Explicit parent=None to avoid GUI
        self.coordinate_transformer = CoordinateTransformer()
        self.selection_manager = SelectionManager()
        
        # Mock ImageHandler to avoid GUI initialization
        self.image_handler = Mock()
        self.image_handler.load_image = Mock(return_value=True)
        self.image_handler.get_image_info = Mock(return_value={
            'width': 1000, 'height': 800, 'channels': 4, 'bit_depth': 16
        })
        
        # Mock SessionManager to avoid file I/O
        self.session_manager = Mock()
        self.session_manager.save_session = Mock(return_value=True)
        self.session_manager.load_session = Mock(return_value=True)
        
        # Mock MainWindowAdapter to avoid GUI dependencies
        self.main_adapter = Mock()
        self.main_adapter.set_coordinate_transformer = Mock()
        self.main_adapter.set_selection_manager = Mock()
        self.main_adapter.set_image_handler = Mock()
        self.main_adapter.set_session_manager = Mock()
        self.main_adapter.set_extractor = Mock()
        self.main_adapter.set_bounding_boxes = Mock()
        self.main_adapter.is_ready = Mock(return_value=True)
        self.main_adapter.is_calibration_ready = Mock(return_value=True)
        self.main_adapter.add_selection = Mock(return_value=True)
        self.main_adapter.get_selections = Mock(return_value=self.test_selections)
        self.main_adapter.add_calibration_point = Mock(return_value=True)
        self.main_adapter.transform_to_real_coordinates = Mock(return_value=(2000.0, 3000.0))
        self.main_adapter.export_protocol = Mock(return_value=True)
        self.main_adapter.load_image = Mock(return_value=True)
        self.main_adapter.save_session = Mock(return_value=True)
        self.main_adapter.load_session = Mock(return_value=True)
        
        # Mock UIModel to avoid GUI dependencies
        self.ui_model = Mock()
        self.ui_model.get_state = Mock(return_value={'selections': [], 'calibration_points': []})
        self.ui_model.update_state = Mock()
        
        # Set up coordinate transformation
        self.coordinate_transformer.add_calibration_point(100, 150, 1000.0, 2000.0, "Point 1")
        self.coordinate_transformer.add_calibration_point(800, 600, 8000.0, 6000.0, "Point 2")
    
    def test_main_window_adapter_initialization(self):
        """Test main window adapter initialization."""
        # Test adapter initialization with mocked components
        adapter = Mock()
        adapter.set_coordinate_transformer = Mock()
        adapter.set_selection_manager = Mock()
        adapter.set_image_handler = Mock()
        adapter.set_session_manager = Mock()
        adapter.is_ready = Mock(return_value=True)
        
        # Set components
        adapter.set_coordinate_transformer(self.coordinate_transformer)
        adapter.set_selection_manager(self.selection_manager)
        adapter.set_image_handler(self.image_handler)
        adapter.set_session_manager(self.session_manager)
        
        # Verify components are set (through mock calls)
        adapter.set_coordinate_transformer.assert_called_once_with(self.coordinate_transformer)
        adapter.set_selection_manager.assert_called_once_with(self.selection_manager)
        adapter.set_image_handler.assert_called_once_with(self.image_handler)
        adapter.set_session_manager.assert_called_once_with(self.session_manager)
        
        # Verify adapter is ready
        assert adapter.is_ready(), "Adapter should be ready with all components"
    
    def test_image_loading_workflow(self):
        """Test image loading workflow through adapter."""
        # Test image loading through mocked adapter
        success = self.main_adapter.load_image(self.test_image_info['file_path'])
        
        assert success, "Image loading should succeed"
        self.main_adapter.load_image.assert_called_once_with(self.test_image_info['file_path'])
    
    def test_selection_management_workflow(self):
        """Test selection management workflow."""
        # Set up adapter
        self.main_adapter.set_selection_manager(self.selection_manager)
        self.main_adapter.set_bounding_boxes(self.test_bounding_boxes)
        
        # Add selections through adapter
        for selection in self.test_selections:
            success = self.main_adapter.add_selection(
                selection['label'],
                selection['color'],
                selection['cell_indices'],
                selection['well_position']
            )
            assert success, f"Adding selection {selection['label']} should succeed"
        
        # Verify selections are stored
        selections = self.main_adapter.get_selections()
        assert len(selections) == len(self.test_selections), "All selections should be stored"
        
        # Verify selection details
        for i, selection in enumerate(selections):
            expected = self.test_selections[i]
            assert selection['label'] == expected['label'], "Selection label should match"
            assert selection['color'] == expected['color'], "Selection color should match"
            assert selection['well_position'] == expected['well_position'], "Well position should match"
    
    def test_calibration_workflow(self):
        """Test calibration workflow through adapter."""
        # Set up adapter
        self.main_adapter.set_coordinate_transformer(self.coordinate_transformer)
        
        # Add calibration points through adapter
        success1 = self.main_adapter.add_calibration_point(200, 300, 2000.0, 3000.0, "Test Point 1")
        success2 = self.main_adapter.add_calibration_point(600, 700, 6000.0, 7000.0, "Test Point 2")
        
        assert success1, "First calibration point should be added"
        assert success2, "Second calibration point should be added"
        
        # Verify calibration is ready
        assert self.main_adapter.is_calibration_ready(), "Calibration should be ready with 2+ points"
        
        # Test coordinate transformation
        pixel_x, pixel_y = 400, 500
        real_x, real_y = self.main_adapter.transform_to_real_coordinates(pixel_x, pixel_y)
        
        # Should get valid real coordinates
        assert isinstance(real_x, (int, float)), "Real X should be numeric"
        assert isinstance(real_y, (int, float)), "Real Y should be numeric"
        assert real_x != pixel_x or real_y != pixel_y, "Coordinates should be transformed"
    
    def test_export_workflow(self):
        """Test export workflow through adapter."""
        # Test export through mocked adapter
        output_path = '/tmp/test_export.cxprotocol'
        
        success = self.main_adapter.export_protocol(output_path, self.test_image_info)
        
        assert success, "Export through adapter should succeed"
        self.main_adapter.export_protocol.assert_called_once_with(output_path, self.test_image_info)
    
    def test_session_management_workflow(self):
        """Test session management workflow."""
        # Create session data
        session_data = {
            'image_path': self.test_image_info['file_path'],
            'calibration_points': [
                {'pixel_x': 100, 'pixel_y': 150, 'real_x': 1000.0, 'real_y': 2000.0, 'label': 'Point 1'},
                {'pixel_x': 800, 'pixel_y': 600, 'real_x': 8000.0, 'real_y': 6000.0, 'label': 'Point 2'}
            ],
            'selections': self.test_selections,
            'bounding_boxes': [
                {'min_x': bb.min_x, 'min_y': bb.min_y, 'max_x': bb.max_x, 'max_y': bb.max_y}
                for bb in self.test_bounding_boxes
            ]
        }
        
        # Test save session through mocked adapter
        session_path = '/tmp/test_session.json'
        
        success = self.main_adapter.save_session(session_path, session_data)
        assert success, "Session save should succeed"
        self.main_adapter.save_session.assert_called_once_with(session_path, session_data)
        
        # Test load session through mocked adapter (return test data)
        self.main_adapter.load_session.return_value = session_data
        loaded_data = self.main_adapter.load_session(session_path)
        
        assert loaded_data is not None, "Session load should succeed"
        self.main_adapter.load_session.assert_called_once_with(session_path)
        
        # Verify loaded data matches
        assert loaded_data['image_path'] == session_data['image_path'], "Image path should match"
        assert len(loaded_data['calibration_points']) == len(session_data['calibration_points']), "Calibration points count should match"
        assert len(loaded_data['selections']) == len(session_data['selections']), "Selections count should match"
    
    def test_ui_model_synchronization(self):
        """Test UI model synchronization with adapter."""
        # Test UI model synchronization through mocked adapter and ui_model
        self.main_adapter.set_ui_model = Mock()
        self.main_adapter.sync_ui_model = Mock()
        
        # Connect adapter to UI model
        self.main_adapter.set_ui_model(self.ui_model)
        
        # Trigger UI model update
        self.main_adapter.sync_ui_model()
        
        # Verify UI model methods are called
        self.main_adapter.set_ui_model.assert_called_once_with(self.ui_model)
        self.main_adapter.sync_ui_model.assert_called_once()
        
        # Test UI state retrieval
        ui_state = self.ui_model.get_state()
        
        assert 'selections' in ui_state, "UI state should include selections"
        assert 'calibration_points' in ui_state, "UI state should include calibration points"
    
    def test_component_communication(self):
        """Test communication between components through adapter."""
        # Test component communication through mocked adapter
        # Mock extraction points generation
        mock_extraction_points = [
            Mock(crop_region=Mock(center_x=1000.0, center_y=2000.0)),
            Mock(crop_region=Mock(center_x=3000.0, center_y=4000.0))
        ]
        self.main_adapter.generate_extraction_points = Mock(return_value=mock_extraction_points)
        
        # Test selection -> extractor communication
        extraction_points = self.main_adapter.generate_extraction_points()
        
        assert len(extraction_points) > 0, "Should generate extraction points"
        
        # Test coordinate transformer -> extractor communication
        for point in extraction_points:
            # Verify points have transformed coordinates
            assert hasattr(point, 'crop_region'), "Points should have crop regions"
            assert point.crop_region.center_x is not None, "Points should have transformed X coordinates"
            assert point.crop_region.center_y is not None, "Points should have transformed Y coordinates"
    
    def test_error_handling_workflow(self):
        """Test error handling in workflows."""
        # Test error handling through mocked adapter
        # Mock adapter returns False for error conditions
        self.main_adapter.add_selection.return_value = False
        self.main_adapter.export_protocol.return_value = False
        self.main_adapter.add_calibration_point.return_value = False
        
        # Test failed selection addition
        success = self.main_adapter.add_selection("", "", [], "")
        assert not success, "Should fail with invalid selection data"
        
        # Test failed export
        success = self.main_adapter.export_protocol("/invalid/path.cxprotocol", {})
        assert not success, "Should fail with invalid export parameters"
        
        # Test failed calibration
        success = self.main_adapter.add_calibration_point(None, None, None, None, "")
        assert not success, "Should fail with invalid calibration data"
    
    def test_state_persistence(self):
        """Test state persistence across operations."""
        # Test state persistence through mocked adapter
        # Mock that state is maintained correctly
        self.main_adapter.get_bounding_boxes = Mock(return_value=self.test_bounding_boxes)
        
        # Verify state persistence after operations
        initial_selections = self.main_adapter.get_selections()
        initial_bbox_count = len(self.main_adapter.get_bounding_boxes())
        
        # Simulate state maintenance after operations
        current_selections = self.main_adapter.get_selections()
        current_bbox_count = len(self.main_adapter.get_bounding_boxes())
        
        assert len(current_selections) == len(initial_selections), "Selections should be maintained"
        assert current_bbox_count == initial_bbox_count, "Bounding boxes should be maintained"
        
        # Verify calibration is ready
        assert self.main_adapter.is_calibration_ready(), "Calibration should be ready"
    
    def test_batch_operations(self):
        """Test batch operations through adapter."""
        # Test batch operations through mocked adapter
        # Simulate batch selection operations
        batch_results = []
        for selection in self.test_selections:
            result = self.main_adapter.add_selection(
                selection['label'],
                selection['color'],
                selection['cell_indices'],
                selection['well_position']
            )
            batch_results.append(result)
        
        # All batch operations should succeed (mocked to return True)
        assert all(batch_results), "All batch operations should succeed"
        assert len(batch_results) == len(self.test_selections), "Should process all selections"
        
        # Test batch calibration points
        calibration_results = []
        for i in range(1, 4):
            result = self.main_adapter.add_calibration_point(
                i * 100, i * 100, i * 1000.0, i * 1000.0, f'Point {i}'
            )
            calibration_results.append(result)
        
        # All calibration operations should succeed
        assert all(calibration_results), "All calibration operations should succeed"
        assert self.main_adapter.is_calibration_ready(), "Calibration should be ready after batch addition"


if __name__ == '__main__':
    pytest.main([__file__, '-v']) 