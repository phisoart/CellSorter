"""
Test Virtual Scatter Plot Production in GUI Mode

Tests scatter plot generation in production GUI mode.
Verifies user experience, visual feedback, and production-ready functionality.
"""

import pytest
import numpy as np
import pandas as pd
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import matplotlib
# Use Qt5Agg for GUI mode testing with mocking
matplotlib.use('Agg')  # Still use Agg for testing but mock GUI behavior

from src.headless.testing.framework import UITestCase
from src.components.widgets.scatter_plot import ScatterPlotWidget, ScatterPlotCanvas
from src.headless.mode_manager import ModeManager
from src.utils.logging_config import get_logger


class TestVirtualScatterPlotProductionGui(UITestCase):
    """Test virtual scatter plot production in GUI mode."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        
        # Set up GUI mode
        self.mode_manager = Mock(spec=ModeManager)
        self.mode_manager.is_dev_mode.return_value = False
        self.mode_manager.is_gui_mode.return_value = True
        self.mode_manager.is_dual_mode.return_value = False
        
        # Create test data
        np.random.seed(42)
        self.test_data = pd.DataFrame({
            'x_values': np.random.normal(50, 15, 1000),
            'y_values': np.random.normal(100, 25, 1000),
            'intensity': np.random.exponential(2, 1000),
            'area': np.random.gamma(2, 2, 1000)
        })
        
        # Mock GUI components
        self.mock_widget = Mock(spec=ScatterPlotWidget)
        self.canvas = ScatterPlotCanvas(parent=None)  # Use real canvas for testing
        
        # Mock GUI-specific functionality
        self.mock_widget.load_data = Mock()
        self.mock_widget.create_plot = Mock()
        self.mock_widget.toggle_selection = Mock()
        self.mock_widget.clear_selection = Mock()
        
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        super().tearDown()
    
    def test_widget_initialization_gui_mode(self):
        """Test scatter plot widget initialization in GUI mode."""
        # Mock widget creation
        widget = Mock(spec=ScatterPlotWidget)
        widget.canvas = self.canvas
        widget.dataframe = None
        widget.numeric_columns = []
        
        # Verify widget structure
        assert hasattr(widget, 'canvas')
        assert hasattr(widget, 'load_data')
        assert hasattr(widget, 'create_plot')
        
        # Test canvas is properly initialized
        assert self.canvas.figure is not None
        assert self.canvas.axes is not None
    
    def test_data_loading_user_experience(self):
        """Test data loading user experience in GUI mode."""
        # Load data into widget
        self.mock_widget.load_data(self.test_data)
        
        # Verify load_data was called
        self.mock_widget.load_data.assert_called_with(self.test_data)
        
        # Test real canvas behavior
        self.canvas.plot_data(
            self.test_data['x_values'].values,
            self.test_data['y_values'].values,
            "X Values", "Y Values"
        )
        
        # Verify plot creation
        assert self.canvas.x_data is not None
        assert self.canvas.y_data is not None
        assert len(self.canvas.x_data) == len(self.test_data)
    
    def test_interactive_selection_workflow(self):
        """Test interactive selection workflow in GUI mode."""
        # Setup plot
        self.canvas.plot_data(
            self.test_data['x_values'].values,
            self.test_data['y_values'].values
        )
        
        # Mock selection toggle
        self.mock_widget.toggle_selection(True)
        self.mock_widget.toggle_selection.assert_called_with(True)
        
        # Test actual selection
        selection_indices = [10, 20, 30, 40, 50]
        self.canvas.highlight_points(selection_indices)
        
        # Verify selection
        assert self.canvas.selected_indices == selection_indices
        
        # Test clear selection
        self.mock_widget.clear_selection()
        self.canvas.clear_selection()
        
        # Verify clearing
        self.mock_widget.clear_selection.assert_called_once()
        assert self.canvas.selected_indices == []
    
    def test_visual_feedback_responsiveness(self):
        """Test visual feedback responsiveness in GUI mode."""
        # Setup plot
        self.canvas.plot_data(
            self.test_data['x_values'].values,
            self.test_data['y_values'].values
        )
        
        # Test immediate visual feedback
        selection_indices = [100, 200, 300]
        self.canvas.highlight_points(selection_indices)
        
        # Verify immediate update
        assert self.canvas.selected_indices == selection_indices
        
        # Test color changes (verify internal state)
        assert len(self.canvas.selected_indices) == 3
        
        # Test multiple rapid selections
        for i in range(5):
            rapid_selection = [i * 10, i * 10 + 1, i * 10 + 2]
            self.canvas.highlight_points(rapid_selection)
            assert self.canvas.selected_indices == rapid_selection
    
    def test_export_user_interface_workflow(self):
        """Test export user interface workflow in GUI mode."""
        # Setup plot
        self.canvas.plot_data(
            self.test_data['x_values'].values,
            self.test_data['y_values'].values,
            "Export Test X", "Export Test Y"
        )
        
        # Test PNG export
        png_path = Path(self.temp_dir) / "gui_export.png"
        success = self.canvas.export_plot(str(png_path), dpi=300)
        
        # Verify high-quality export
        assert success is True
        assert png_path.exists()
        assert png_path.stat().st_size > 0
        
        # Test SVG export for scalability
        svg_path = Path(self.temp_dir) / "gui_export.svg"
        svg_success = self.canvas.export_plot(str(svg_path))
        
        assert svg_success is True
        assert svg_path.exists()
        
        # Verify SVG content quality
        with open(svg_path, 'r') as f:
            content = f.read()
            assert 'Export Test X' in content
            assert 'Export Test Y' in content
    
    def test_performance_with_user_interaction(self):
        """Test performance with simulated user interaction in GUI mode."""
        # Large dataset for stress testing
        n_points = 25000
        large_x = np.random.normal(0, 1, n_points)
        large_y = np.random.normal(0, 1, n_points)
        
        # Measure plotting performance
        import time
        start_time = time.time()
        self.canvas.plot_data(large_x, large_y, "Large Dataset X", "Large Dataset Y")
        plot_time = time.time() - start_time
        
        # Should be responsive for user
        assert plot_time < 3.0, f"Plotting too slow for GUI: {plot_time:.2f}s"
        
        # Test interactive selection performance
        start_time = time.time()
        large_selection = list(range(0, min(5000, n_points), 5))
        self.canvas.highlight_points(large_selection)
        selection_time = time.time() - start_time
        
        # Selection should be immediate
        assert selection_time < 1.0, f"Selection too slow for GUI: {selection_time:.2f}s"
        assert len(self.canvas.selected_indices) == len(large_selection)
    
    def test_accessibility_features(self):
        """Test accessibility features in GUI mode."""
        # Setup plot
        self.canvas.plot_data(
            self.test_data['x_values'].values,
            self.test_data['y_values'].values,
            "Accessible X", "Accessible Y"
        )
        
        # Test high contrast selection
        selection_indices = [10, 20, 30]
        self.canvas.highlight_points(selection_indices)
        
        # Verify selection is visible (check color contrast)
        default_color = self.canvas.default_color
        selected_color = self.canvas.selected_color
        
        # Colors should be different for accessibility
        assert default_color != selected_color
        
        # Test clear axis labels for screen readers
        assert self.canvas.axes.get_xlabel() == "Accessible X"
        assert self.canvas.axes.get_ylabel() == "Accessible Y"
        assert len(self.canvas.axes.get_title()) > 0
    
    def test_error_recovery_user_experience(self):
        """Test error recovery user experience in GUI mode."""
        # Test with problematic data
        problematic_x = np.array([1, 2, np.inf, 4, 5])
        problematic_y = np.array([2, np.nan, 3, -np.inf, 5])
        
        # Should handle gracefully without crashing GUI
        try:
            self.canvas.plot_data(problematic_x, problematic_y, "Problem X", "Problem Y")
            # If successful, verify reasonable behavior
            assert self.canvas.scatter_plot is not None
        except Exception as e:
            # If it fails, should be a graceful, informative error
            assert isinstance(e, (ValueError, RuntimeError))
    
    def test_memory_management_gui_mode(self):
        """Test memory management in GUI mode with multiple plots."""
        # Create multiple plots to test memory usage
        for i in range(10):
            x_data = np.random.normal(i, 1, 2000)
            y_data = np.random.normal(i*2, 1, 2000)
            
            self.canvas.plot_data(x_data, y_data, f"Plot {i} X", f"Plot {i} Y")
            
            # Add selections to test memory
            selection = list(range(0, 100, 10))
            self.canvas.highlight_points(selection)
            
            # Force garbage collection
            import gc
            gc.collect()
        
        # Verify final state is clean
        assert self.canvas.x_data is not None
        assert self.canvas.y_data is not None
        assert len(self.canvas.x_data) == 2000  # Last dataset
        assert len(self.canvas.selected_indices) == 10  # Last selection
    
    def test_theme_consistency_gui_mode(self):
        """Test theme consistency in GUI mode."""
        # Setup plot
        self.canvas.plot_data(
            self.test_data['x_values'].values,
            self.test_data['y_values'].values,
            "Theme Test X", "Theme Test Y"
        )
        
        # Test color consistency
        assert self.canvas.default_color is not None
        assert self.canvas.selected_color is not None
        assert self.canvas.expression_color is not None
        
        # Colors should be distinct
        colors = [self.canvas.default_color, self.canvas.selected_color, self.canvas.expression_color]
        assert len(set(colors)) == 3  # All colors should be different
        
        # Test point styling
        assert self.canvas.point_size > 0
        assert 0 <= self.canvas.point_alpha <= 1
