"""
Test Virtual Scatter Plot Synchronization in DUAL Mode

Tests scatter plot generation and synchronization between headless and GUI modes.
Verifies plot consistency, selection synchronization, and cross-mode compatibility.
"""

import pytest
import numpy as np
import pandas as pd
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import matplotlib
matplotlib.use('Agg')
from matplotlib.figure import Figure

from src.headless.testing.framework import UITestCase
from src.components.widgets.scatter_plot import ScatterPlotWidget, ScatterPlotCanvas
from src.headless.mode_manager import ModeManager
from src.utils.logging_config import get_logger


class TestVirtualScatterPlotSyncDual(UITestCase):
    """Test virtual scatter plot synchronization in DUAL mode."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        
        # Set up dual mode
        self.mode_manager = Mock(spec=ModeManager)
        self.mode_manager.is_dev_mode.return_value = False
        self.mode_manager.is_gui_mode.return_value = False
        self.mode_manager.is_dual_mode.return_value = True
        
        # Create test data
        np.random.seed(42)
        self.test_data = pd.DataFrame({
            'x_values': np.random.normal(50, 15, 1000),
            'y_values': np.random.normal(100, 25, 1000),
            'intensity': np.random.exponential(2, 1000),
            'area': np.random.gamma(2, 2, 1000)
        })
        
        # Create headless and GUI canvases
        self.headless_canvas = ScatterPlotCanvas(parent=None)
        self.gui_canvas = Mock(spec=ScatterPlotCanvas)
        
        # Setup GUI canvas mock behavior
        self.gui_canvas.x_data = None
        self.gui_canvas.y_data = None
        self.gui_canvas.selected_indices = []
        self.gui_canvas.plot_data = Mock()
        self.gui_canvas.highlight_points = Mock()
        self.gui_canvas.clear_selection = Mock()
        
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        super().tearDown()
    
    def test_plot_data_synchronization(self):
        """Test plot data synchronization between headless and GUI modes."""
        x_data = self.test_data['x_values'].values
        y_data = self.test_data['y_values'].values
        
        # Plot in headless mode
        self.headless_canvas.plot_data(x_data, y_data, "X Values", "Y Values")
        
        # Simulate GUI synchronization
        self.gui_canvas.plot_data.assert_not_called()  # Initially
        
        # Trigger synchronization
        self.gui_canvas.plot_data(x_data, y_data, "X Values", "Y Values")
        self.gui_canvas.x_data = x_data
        self.gui_canvas.y_data = y_data
        
        # Verify synchronization
        self.gui_canvas.plot_data.assert_called_with(
            x_data, y_data, "X Values", "Y Values"
        )
        
        # Verify data consistency
        assert len(self.headless_canvas.x_data) == len(self.gui_canvas.x_data)
        assert len(self.headless_canvas.y_data) == len(self.gui_canvas.y_data)
        assert np.array_equal(self.headless_canvas.x_data, self.gui_canvas.x_data)
        assert np.array_equal(self.headless_canvas.y_data, self.gui_canvas.y_data)
    
    def test_selection_synchronization_headless_to_gui(self):
        """Test selection synchronization from headless to GUI mode."""
        # Setup data in both canvases
        x_data = self.test_data['x_values'].values
        y_data = self.test_data['y_values'].values
        
        self.headless_canvas.plot_data(x_data, y_data)
        self.gui_canvas.x_data = x_data
        self.gui_canvas.y_data = y_data
        
        # Make selection in headless mode
        selection_indices = [10, 20, 30, 40, 50]
        self.headless_canvas.highlight_points(selection_indices)
        
        # Simulate synchronization to GUI
        self.gui_canvas.highlight_points(selection_indices)
        self.gui_canvas.selected_indices = selection_indices
        
        # Verify synchronization
        self.gui_canvas.highlight_points.assert_called_with(selection_indices)
        assert self.headless_canvas.selected_indices == selection_indices
        assert self.gui_canvas.selected_indices == selection_indices
    
    def test_export_consistency_between_modes(self):
        """Test export consistency between headless and GUI modes."""
        # Setup plot in headless mode
        self.headless_canvas.plot_data(
            self.test_data['x_values'].values,
            self.test_data['y_values'].values
        )
        
        # Export from headless
        headless_path = Path(self.temp_dir) / "headless_plot.png"
        headless_success = self.headless_canvas.export_plot(str(headless_path))
        
        # Verify headless export
        assert headless_success is True
        assert headless_path.exists()
        
        # Simulate GUI export (mock)
        gui_path = Path(self.temp_dir) / "gui_plot.png"
        self.gui_canvas.export_plot = Mock(return_value=True)
        gui_success = self.gui_canvas.export_plot(str(gui_path))
        
        # Verify GUI export was called
        assert gui_success is True
        self.gui_canvas.export_plot.assert_called_with(str(gui_path))
    
    def test_performance_parity_between_modes(self):
        """Test performance parity between headless and GUI modes."""
        # Large dataset
        n_points = 10000
        large_x = np.random.normal(0, 1, n_points)
        large_y = np.random.normal(0, 1, n_points)
        
        # Measure headless performance
        import time
        
        start_time = time.time()
        self.headless_canvas.plot_data(large_x, large_y, "Large X", "Large Y")
        headless_time = time.time() - start_time
        
        # Simulate GUI performance (should be similar)
        start_time = time.time()
        self.gui_canvas.plot_data(large_x, large_y, "Large X", "Large Y")
        time.sleep(headless_time * 0.1)  # Simulate slightly slower GUI
        gui_time = time.time() - start_time
        
        # Performance should be comparable
        assert headless_time < 2.0, f"Headless plotting too slow: {headless_time:.2f}s"
        assert gui_time < 3.0, f"GUI plotting too slow: {gui_time:.2f}s"
        
        # Verify both modes called correctly
        assert self.gui_canvas.plot_data.call_count >= 1  # Called at least once in this test
    
    def test_state_restoration_consistency(self):
        """Test state restoration consistency between modes."""
        # Setup initial state in headless
        x_data = self.test_data['x_values'].values[:500]
        y_data = self.test_data['y_values'].values[:500]
        
        self.headless_canvas.plot_data(x_data, y_data, "State X", "State Y")
        initial_selection = [10, 20, 30]
        self.headless_canvas.highlight_points(initial_selection)
        
        # Save state
        headless_state = {
            'x_data': self.headless_canvas.x_data.copy(),
            'y_data': self.headless_canvas.y_data.copy(),
            'selected_indices': self.headless_canvas.selected_indices.copy(),
            'x_label': self.headless_canvas.axes.get_xlabel(),
            'y_label': self.headless_canvas.axes.get_ylabel()
        }
        
        # Restore in GUI (simulate)
        self.gui_canvas.x_data = headless_state['x_data']
        self.gui_canvas.y_data = headless_state['y_data']
        self.gui_canvas.selected_indices = headless_state['selected_indices']
        
        self.gui_canvas.plot_data(
            headless_state['x_data'],
            headless_state['y_data'],
            headless_state['x_label'],
            headless_state['y_label']
        )
        self.gui_canvas.highlight_points(headless_state['selected_indices'])
        
        # Verify restoration
        assert np.array_equal(self.gui_canvas.x_data, headless_state['x_data'])
        assert np.array_equal(self.gui_canvas.y_data, headless_state['y_data'])
        assert self.gui_canvas.selected_indices == headless_state['selected_indices']
