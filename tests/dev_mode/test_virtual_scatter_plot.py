"""
Test Virtual Scatter Plot Generation in DEV Mode

Tests scatter plot generation and interaction in headless development mode.
Verifies matplotlib backend configuration, virtual selection simulation,
and plot export functionality without GUI dependencies.
"""

import pytest
import numpy as np
import pandas as pd
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO, StringIO

import matplotlib
matplotlib.use('Agg')  # Force headless backend
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg

from src.headless.testing.framework import UITestCase
from src.components.widgets.scatter_plot import ScatterPlotWidget, ScatterPlotCanvas
from src.utils.exceptions import DataValidationError
from src.utils.logging_config import get_logger
from src.headless.mode_manager import ModeManager


class TestVirtualScatterPlotDev(UITestCase):
    """Test virtual scatter plot generation in DEV mode (headless)."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        
        # Ensure Agg backend is used
        matplotlib.use('Agg')
        
        # Set up headless mode
        self.mode_manager = Mock(spec=ModeManager)
        self.mode_manager.is_dev_mode.return_value = True
        self.mode_manager.is_gui_mode.return_value = False
        self.mode_manager.is_dual_mode.return_value = False
        
        # Create test data
        np.random.seed(42)  # For reproducible tests
        n_points = 1000
        self.test_data = pd.DataFrame({
            'x_values': np.random.normal(50, 15, n_points),
            'y_values': np.random.normal(100, 25, n_points),
            'intensity': np.random.exponential(2, n_points),
            'area': np.random.gamma(2, 2, n_points)
        })
        
        # Create temporary directory for exports
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock logger
        self.logger = get_logger('test_scatter_plot')
    
    def tearDown(self):
        """Clean up test environment."""
        # Clean up temporary files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        super().tearDown()
    
    def test_agg_backend_configuration(self):
        """Test matplotlib Agg backend configuration for headless operation."""
        # Verify Agg backend is active
        current_backend = matplotlib.get_backend()
        assert current_backend == 'Agg', f"Expected Agg backend, got {current_backend}"
        
        # Test figure creation without display
        fig = Figure(figsize=(8, 6))
        canvas = FigureCanvasAgg(fig)
        
        # Verify canvas was created successfully
        assert canvas is not None
        assert isinstance(canvas, FigureCanvasAgg)
        
        # Test axes creation
        ax = fig.add_subplot(111)
        assert ax is not None
        
        # Test basic plotting
        x = np.linspace(0, 10, 100)
        y = np.sin(x)
        ax.plot(x, y)
        
        # Verify plot was created
        assert len(ax.lines) == 1
    
    def test_scatter_plot_canvas_headless_creation(self):
        """Test scatter plot canvas creation in headless mode."""
        # Create canvas without parent (headless)
        canvas = ScatterPlotCanvas(parent=None, width=10, height=8, dpi=100)
        
        # Verify canvas properties
        assert canvas.figure is not None
        assert canvas.axes is not None
        assert canvas.x_data is None
        assert canvas.y_data is None
        assert canvas.selected_indices == []
        
        # Verify backend is Agg
        assert matplotlib.get_backend() == 'Agg'
    
    def test_virtual_data_plotting(self):
        """Test plotting data points in virtual environment."""
        canvas = ScatterPlotCanvas(parent=None)
        
        # Plot test data
        x_data = self.test_data['x_values'].values
        y_data = self.test_data['y_values'].values
        
        canvas.plot_data(x_data, y_data, "X Values", "Y Values")
        
        # Verify data was stored
        assert canvas.x_data is not None
        assert canvas.y_data is not None
        assert len(canvas.x_data) == len(x_data)
        assert len(canvas.y_data) == len(y_data)
        
        # Verify plot was created
        assert canvas.scatter_plot is not None
        assert len(canvas.axes.collections) > 0  # Scatter plot creates a collection
        
        # Verify axes labels
        assert canvas.axes.get_xlabel() == "X Values"
        assert canvas.axes.get_ylabel() == "Y Values"
        assert "Y Values vs X Values" in canvas.axes.get_title()
    
    def test_programmatic_selection_simulation(self):
        """Test programmatic selection area setting without mouse interaction."""
        canvas = ScatterPlotCanvas(parent=None)
        
        # Plot data
        x_data = self.test_data['x_values'].values
        y_data = self.test_data['y_values'].values
        canvas.plot_data(x_data, y_data)
        
        # Define selection rectangle programmatically
        x_min, x_max = 40, 60
        y_min, y_max = 80, 120
        
        # Find points within rectangle (simulate selection)
        mask = ((x_data >= x_min) & (x_data <= x_max) & 
                (y_data >= y_min) & (y_data <= y_max))
        expected_indices = np.where(mask)[0].tolist()
        
        # Apply selection programmatically
        canvas.highlight_points(expected_indices)
        
        # Verify selection
        assert canvas.selected_indices == expected_indices
        assert len(canvas.selected_indices) > 0
        
        # Verify visual update occurred (color change)
        # In headless mode, we verify the internal state
        selection_colors = [canvas.selected_color if i in expected_indices 
                          else canvas.default_color 
                          for i in range(len(x_data))]
        
        # Count selected vs unselected points
        selected_count = sum(1 for i in canvas.selected_indices)
        assert selected_count == len(expected_indices)
    
    def test_virtual_mouse_event_simulation(self):
        """Test virtual mouse event simulation for selection."""
        canvas = ScatterPlotCanvas(parent=None)
        
        # Plot data
        canvas.plot_data(self.test_data['x_values'].values, 
                        self.test_data['y_values'].values)
        
        # Mock mouse events for rectangle selection
        mock_eclick = Mock()
        mock_eclick.xdata = 30
        mock_eclick.ydata = 70
        
        mock_erelease = Mock()
        mock_erelease.xdata = 70
        mock_erelease.ydata = 130
        
        # Simulate rectangle selection callback
        canvas._on_rectangle_select(mock_eclick, mock_erelease)
        
        # Verify selection occurred
        assert len(canvas.selected_indices) > 0
        
        # Verify selection bounds
        selected_x = canvas.x_data[canvas.selected_indices]
        selected_y = canvas.y_data[canvas.selected_indices]
        
        assert np.all(selected_x >= 30)
        assert np.all(selected_x <= 70)
        assert np.all(selected_y >= 70)
        assert np.all(selected_y <= 130)
    
    def test_png_export_headless(self):
        """Test PNG export functionality in headless mode."""
        canvas = ScatterPlotCanvas(parent=None)
        
        # Create plot
        canvas.plot_data(self.test_data['x_values'].values,
                        self.test_data['y_values'].values,
                        "Test X", "Test Y")
        
        # Export to PNG
        output_path = Path(self.temp_dir) / "test_plot.png"
        success = canvas.export_plot(str(output_path), dpi=150)
        
        # Verify export success
        assert success is True
        assert output_path.exists()
        assert output_path.stat().st_size > 0
        
        # Verify it's a valid PNG file
        assert output_path.suffix == '.png'
        
        # Try to read the file to verify it's valid
        with open(output_path, 'rb') as f:
            header = f.read(8)
            # PNG signature: 89 50 4E 47 0D 0A 1A 0A
            assert header == b'\x89PNG\r\n\x1a\n'
    
    def test_svg_export_headless(self):
        """Test SVG export functionality in headless mode."""
        canvas = ScatterPlotCanvas(parent=None)
        
        # Create plot
        canvas.plot_data(self.test_data['x_values'].values,
                        self.test_data['y_values'].values,
                        "Test X", "Test Y")
        
        # Export to SVG
        output_path = Path(self.temp_dir) / "test_plot.svg"
        success = canvas.export_plot(str(output_path))
        
        # Verify export success
        assert success is True
        assert output_path.exists()
        assert output_path.stat().st_size > 0
        
        # Verify it's a valid SVG file
        assert output_path.suffix == '.svg'
        
        # Check SVG content
        with open(output_path, 'r') as f:
            content = f.read()
            assert content.startswith('<?xml version="1.0" encoding="utf-8" standalone="no"?>')
            assert '<svg' in content
            assert '</svg>' in content
    
    def test_large_dataset_performance(self):
        """Test performance with large datasets in headless mode."""
        # Create large dataset
        n_points = 50000
        large_x = np.random.normal(0, 1, n_points)
        large_y = np.random.normal(0, 1, n_points)
        
        canvas = ScatterPlotCanvas(parent=None)
        
        # Measure plotting time
        import time
        start_time = time.time()
        canvas.plot_data(large_x, large_y, "Large X", "Large Y")
        plot_time = time.time() - start_time
        
        # Verify plot was created
        assert canvas.scatter_plot is not None
        assert len(canvas.x_data) == n_points
        
        # Performance should be reasonable (less than 5 seconds)
        assert plot_time < 5.0, f"Plotting took too long: {plot_time:.2f}s"
    
    def test_multiple_datasets_plotting(self):
        """Test plotting multiple datasets sequentially."""
        canvas = ScatterPlotCanvas(parent=None)
        
        # First dataset
        dataset1_x = np.random.normal(0, 1, 500)
        dataset1_y = np.random.normal(0, 1, 500)
        canvas.plot_data(dataset1_x, dataset1_y, "Dataset 1 X", "Dataset 1 Y")
        
        # Verify first plot
        assert len(canvas.x_data) == 500
        assert canvas.axes.get_xlabel() == "Dataset 1 X"
        
        # Second dataset (should replace first)
        dataset2_x = np.random.normal(10, 2, 300)
        dataset2_y = np.random.normal(5, 1.5, 300)
        canvas.plot_data(dataset2_x, dataset2_y, "Dataset 2 X", "Dataset 2 Y")
        
        # Verify replacement
        assert len(canvas.x_data) == 300
        assert canvas.axes.get_xlabel() == "Dataset 2 X"
        assert canvas.axes.get_ylabel() == "Dataset 2 Y"
        assert canvas.selected_indices == []  # Selection should be cleared
    
    def test_selection_persistence_across_operations(self):
        """Test that selection persists across plot operations."""
        canvas = ScatterPlotCanvas(parent=None)
        
        # Plot data
        canvas.plot_data(self.test_data['x_values'].values,
                        self.test_data['y_values'].values)
        
        # Make selection
        initial_selection = [10, 20, 30, 40, 50]
        canvas.highlight_points(initial_selection)
        
        # Verify selection
        assert canvas.selected_indices == initial_selection
        
        # Clear selection
        canvas.clear_selection()
        assert canvas.selected_indices == []
        
        # Make new selection
        new_selection = [100, 200, 300]
        canvas.highlight_points(new_selection)
        assert canvas.selected_indices == new_selection
    
    def test_error_handling_invalid_data(self):
        """Test error handling with invalid data."""
        canvas = ScatterPlotCanvas(parent=None)
        
        # Test with NaN values
        x_with_nan = np.array([1, 2, np.nan, 4, 5])
        y_with_nan = np.array([2, np.nan, 3, 4, 5])
        
        # Should handle NaN gracefully
        canvas.plot_data(x_with_nan, y_with_nan, "X with NaN", "Y with NaN")
        
        # Verify plot was created (matplotlib handles NaN automatically)
        assert canvas.scatter_plot is not None
        
        # Test with mismatched array lengths
        x_short = np.array([1, 2, 3])
        y_long = np.array([1, 2, 3, 4, 5])
        
        # This should either handle gracefully or raise appropriate error
        try:
            canvas.plot_data(x_short, y_long, "Mismatched X", "Mismatched Y")
            # If no error, verify data was truncated appropriately
            assert len(canvas.x_data) == min(len(x_short), len(y_long))
        except (ValueError, DataValidationError):
            # Expected behavior for mismatched data
            pass
    
    def test_memory_cleanup_headless(self):
        """Test memory cleanup in headless mode."""
        canvas = ScatterPlotCanvas(parent=None)
        
        # Create multiple plots to test memory usage
        for i in range(5):
            x_data = np.random.normal(i, 1, 1000)
            y_data = np.random.normal(i*2, 1, 1000)
            canvas.plot_data(x_data, y_data, f"Test {i} X", f"Test {i} Y")
            
            # Force garbage collection
            import gc
            gc.collect()
        
        # Final verification
        assert canvas.x_data is not None
        assert canvas.y_data is not None
        assert len(canvas.x_data) == 1000  # Last dataset 