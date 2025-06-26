"""
CellSorter Scatter Plot Widget

Interactive matplotlib scatter plot embedded in Qt widget for cell selection
and analysis with rectangle selection tool.
"""

from typing import Optional, List, Tuple, Dict, Any, Callable
import numpy as np
import pandas as pd

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QLabel
from PySide6.QtCore import Signal, QObject

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.widgets import RectangleSelector
import matplotlib.pyplot as plt

from utils.logging_config import LoggerMixin
from utils.error_handler import error_handler


class ScatterPlotCanvas(FigureCanvas, LoggerMixin):
    """
    Matplotlib canvas for interactive scatter plots with rectangle selection.
    """
    
    # Signals
    selection_changed = Signal(list)  # List of selected indices
    
    def __init__(self, parent=None, width=8, height=6, dpi=100):
        self.figure = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.figure.add_subplot(111)
        
        super().__init__(self.figure)
        self.setParent(parent)
        
        # Data storage
        self.x_data: Optional[np.ndarray] = None
        self.y_data: Optional[np.ndarray] = None
        self.scatter_plot = None
        self.selected_indices: List[int] = []
        
        # Selection tool
        self.rectangle_selector: Optional[RectangleSelector] = None
        self.selection_enabled = False
        
        # Color configuration
        self.default_color = '#1f77b4'  # matplotlib default blue
        self.selected_color = '#ff7f0e'  # orange for selected points
        self.point_size = 20
        self.point_alpha = 0.6
        
        # Setup figure style
        self.figure.patch.set_facecolor('white')
        self.axes.set_facecolor('white')
        self.figure.tight_layout()
        
        self.log_info("Scatter plot canvas initialized")
    
    @error_handler("Plotting scatter data")
    def plot_data(self, x_data: np.ndarray, y_data: np.ndarray, 
                  x_label: str = "X", y_label: str = "Y") -> None:
        """
        Plot scatter data on the canvas.
        
        Args:
            x_data: X coordinate data
            y_data: Y coordinate data  
            x_label: Label for X axis
            y_label: Label for Y axis
        """
        self.x_data = x_data
        self.y_data = y_data
        self.selected_indices = []
        
        # Clear previous plot
        self.axes.clear()
        
        # Create scatter plot
        self.scatter_plot = self.axes.scatter(
            x_data, y_data,
            c=self.default_color,
            s=self.point_size,
            alpha=self.point_alpha,
            edgecolors='none'
        )
        
        # Set labels and title
        self.axes.set_xlabel(x_label, fontsize=11)
        self.axes.set_ylabel(y_label, fontsize=11)
        self.axes.set_title(f"{y_label} vs {x_label}", fontsize=12, fontweight='bold')
        
        # Style the plot
        self.axes.grid(True, alpha=0.3)
        self.axes.spines['top'].set_visible(False)
        self.axes.spines['right'].set_visible(False)
        
        # Refresh canvas
        self.figure.tight_layout()
        self.draw()
        
        self.log_info(f"Plotted {len(x_data):,} data points")
    
    def enable_rectangle_selection(self, enabled: bool = True) -> None:
        """
        Enable or disable rectangle selection tool.
        
        Args:
            enabled: Whether to enable selection
        """
        if enabled and self.x_data is not None:
            if self.rectangle_selector is None:
                self.rectangle_selector = RectangleSelector(
                    self.axes,
                    self._on_rectangle_select,
                    useblit=True,
                    button=[1],  # Left mouse button
                    minspanx=5, minspany=5,  # Minimum selection size
                    spancoords='pixels',
                    interactive=True
                )
            self.rectangle_selector.set_active(True)
            self.selection_enabled = True
            self.log_info("Rectangle selection enabled")
        else:
            if self.rectangle_selector:
                self.rectangle_selector.set_active(False)
            self.selection_enabled = False
            self.log_info("Rectangle selection disabled")
    
    def _on_rectangle_select(self, eclick, erelease) -> None:
        """
        Handle rectangle selection callback.
        
        Args:
            eclick: Mouse button press event
            erelease: Mouse button release event
        """
        if self.x_data is None or self.y_data is None:
            return
        
        # Get rectangle bounds
        x1, x2 = sorted([eclick.xdata, erelease.xdata])
        y1, y2 = sorted([eclick.ydata, erelease.ydata])
        
        # Find points within rectangle
        mask = ((self.x_data >= x1) & (self.x_data <= x2) & 
                (self.y_data >= y1) & (self.y_data <= y2))
        
        self.selected_indices = np.where(mask)[0].tolist()
        
        # Update visual highlighting
        self._update_selection_visual()
        
        # Emit signal
        self.selection_changed.emit(self.selected_indices)
        
        self.log_info(f"Selected {len(self.selected_indices)} points in rectangle")
    
    def _update_selection_visual(self) -> None:
        """Update visual highlighting of selected points."""
        if self.scatter_plot is None or self.x_data is None:
            return
        
        # Reset all colors to default
        colors = [self.default_color] * len(self.x_data)
        
        # Highlight selected points
        for idx in self.selected_indices:
            if 0 <= idx < len(colors):
                colors[idx] = self.selected_color
        
        # Update scatter plot colors
        self.scatter_plot.set_color(colors)
        self.draw_idle()
    
    def highlight_points(self, indices: List[int], color: str = None) -> None:
        """
        Highlight specific points with a given color.
        
        Args:
            indices: List of point indices to highlight
            color: Color for highlighting (defaults to selected_color)
        """
        if self.scatter_plot is None or self.x_data is None:
            return
        
        if color is None:
            color = self.selected_color
        
        self.selected_indices = indices
        self._update_selection_visual()
        
        self.log_info(f"Highlighted {len(indices)} points")
    
    def clear_selection(self) -> None:
        """Clear current selection."""
        self.selected_indices = []
        self._update_selection_visual()
        self.selection_changed.emit([])
        
        self.log_info("Selection cleared")
    
    def get_selected_indices(self) -> List[int]:
        """
        Get currently selected point indices.
        
        Returns:
            List of selected point indices
        """
        return self.selected_indices.copy()
    
    def export_plot(self, file_path: str, dpi: int = 300) -> bool:
        """
        Export the current plot to an image file.
        
        Args:
            file_path: Output file path
            dpi: Image resolution
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.figure.savefig(file_path, dpi=dpi, bbox_inches='tight')
            self.log_info(f"Plot exported to {file_path}")
            return True
        except Exception as e:
            self.log_error(f"Failed to export plot: {e}")
            return False


class ScatterPlotWidget(QWidget, LoggerMixin):
    """
    Complete scatter plot widget with controls and interactive canvas.
    """
    
    # Signals
    plot_created = Signal(str, str)  # x_column, y_column
    selection_made = Signal(list)  # selected_indices
    column_changed = Signal(str, str)  # axis, column_name
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # Data storage
        self.dataframe: Optional[pd.DataFrame] = None
        self.numeric_columns: List[str] = []
        
        self.setup_ui()
        self.connect_signals()
        
        self.log_info("Scatter plot widget initialized")
    
    def setup_ui(self) -> None:
        """Set up the widget UI."""
        layout = QVBoxLayout(self)
        
        # Controls section
        controls_layout = QHBoxLayout()
        
        # X-axis column selector
        x_label = QLabel("X-axis:")
        self.x_combo = QComboBox()
        self.x_combo.setMinimumWidth(150)
        
        # Y-axis column selector  
        y_label = QLabel("Y-axis:")
        self.y_combo = QComboBox()
        self.y_combo.setMinimumWidth(150)
        
        # Action buttons
        self.plot_button = QPushButton("Create Plot")
        self.plot_button.setEnabled(False)
        
        self.select_button = QPushButton("Enable Selection")
        self.select_button.setCheckable(True)
        self.select_button.setEnabled(False)
        
        self.clear_button = QPushButton("Clear Selection")
        self.clear_button.setEnabled(False)
        
        # Add to layout
        controls_layout.addWidget(x_label)
        controls_layout.addWidget(self.x_combo)
        controls_layout.addWidget(y_label)
        controls_layout.addWidget(self.y_combo)
        controls_layout.addWidget(self.plot_button)
        controls_layout.addWidget(self.select_button)
        controls_layout.addWidget(self.clear_button)
        controls_layout.addStretch()
        
        # Canvas
        self.canvas = ScatterPlotCanvas(self)
        
        # Status label
        self.status_label = QLabel("No data loaded")
        self.status_label.setStyleSheet("color: #6c757d; font-style: italic;")
        
        # Add to main layout
        layout.addLayout(controls_layout)
        layout.addWidget(self.canvas)
        layout.addWidget(self.status_label)
    
    def connect_signals(self) -> None:
        """Connect widget signals."""
        self.plot_button.clicked.connect(self.create_plot)
        self.select_button.toggled.connect(self.toggle_selection)
        self.clear_button.clicked.connect(self.clear_selection)
        self.canvas.selection_changed.connect(self._on_selection_changed)
    
    @error_handler("Loading data for scatter plot")
    def load_data(self, dataframe: pd.DataFrame) -> None:
        """
        Load data for plotting.
        
        Args:
            dataframe: Data to load
        """
        self.dataframe = dataframe
        self.numeric_columns = dataframe.select_dtypes(include=[np.number]).columns.tolist()
        
        # Update combo boxes
        self.x_combo.clear()
        self.y_combo.clear()
        
        if self.numeric_columns:
            self.x_combo.addItems(self.numeric_columns)
            self.y_combo.addItems(self.numeric_columns)
            
            # Set default selections (first two columns if available)
            if len(self.numeric_columns) >= 2:
                self.x_combo.setCurrentText(self.numeric_columns[0])
                self.y_combo.setCurrentText(self.numeric_columns[1])
            
            self.plot_button.setEnabled(True)
            self.status_label.setText(f"Data loaded: {len(dataframe):,} rows, {len(self.numeric_columns)} numeric columns")
        else:
            self.plot_button.setEnabled(False)
            self.status_label.setText("No numeric columns found for plotting")
        
        self.log_info(f"Loaded data: {len(dataframe):,} rows, {len(self.numeric_columns)} numeric columns")
    
    @error_handler("Creating scatter plot")
    def create_plot(self) -> None:
        """Create a new scatter plot with selected columns."""
        if self.dataframe is None or not self.numeric_columns:
            return
        
        x_column = self.x_combo.currentText()
        y_column = self.y_combo.currentText()
        
        if not x_column or not y_column:
            self.status_label.setText("Please select both X and Y columns")
            return
        
        # Get data
        x_data = self.dataframe[x_column].values
        y_data = self.dataframe[y_column].values
        
        # Remove NaN values
        mask = ~(np.isnan(x_data) | np.isnan(y_data))
        x_data = x_data[mask]
        y_data = y_data[mask]
        
        if len(x_data) == 0:
            self.status_label.setText("No valid data points to plot")
            return
        
        # Create plot
        self.canvas.plot_data(x_data, y_data, x_column, y_column)
        
        # Enable controls
        self.select_button.setEnabled(True)
        self.clear_button.setEnabled(True)
        
        # Update status
        self.status_label.setText(f"Plot created: {len(x_data):,} points")
        
        # Emit signal
        self.plot_created.emit(x_column, y_column)
        
        self.log_info(f"Created scatter plot: {x_column} vs {y_column} ({len(x_data):,} points)")
    
    def toggle_selection(self, enabled: bool) -> None:
        """
        Toggle rectangle selection mode.
        
        Args:
            enabled: Whether selection is enabled
        """
        self.canvas.enable_rectangle_selection(enabled)
        
        if enabled:
            self.select_button.setText("Disable Selection")
            self.status_label.setText("Selection mode enabled - drag to select points")
        else:
            self.select_button.setText("Enable Selection")
            self.status_label.setText("Selection mode disabled")
        
        self.log_info(f"Selection mode {'enabled' if enabled else 'disabled'}")
    
    def clear_selection(self) -> None:
        """Clear current selection."""
        self.canvas.clear_selection()
        self.status_label.setText("Selection cleared")
        
        self.log_info("Selection cleared")
    
    def _on_selection_changed(self, indices: List[int]) -> None:
        """
        Handle selection change from canvas.
        
        Args:
            indices: Selected point indices
        """
        if indices:
            self.status_label.setText(f"Selected {len(indices):,} points")
        else:
            self.status_label.setText("No points selected")
        
        # Emit signal
        self.selection_made.emit(indices)
    
    def highlight_indices(self, indices: List[int], color: str = None) -> None:
        """
        Highlight specific data point indices.
        
        Args:
            indices: Indices to highlight
            color: Color for highlighting
        """
        self.canvas.highlight_points(indices, color)
    
    def get_selected_data(self) -> Optional[pd.DataFrame]:
        """
        Get DataFrame of currently selected data points.
        
        Returns:
            DataFrame with selected rows or None
        """
        if self.dataframe is None:
            return None
        
        indices = self.canvas.get_selected_indices()
        if not indices:
            return None
        
        return self.dataframe.iloc[indices].copy()
    
    def export_plot(self, file_path: str) -> bool:
        """
        Export current plot to file.
        
        Args:
            file_path: Output file path
        
        Returns:
            True if successful, False otherwise
        """
        return self.canvas.export_plot(file_path)