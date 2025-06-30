"""
CellSorter Scatter Plot Widget

Interactive matplotlib scatter plot embedded in Qt widget for cell selection
and analysis with rectangle selection tool.
"""

from typing import Optional, List, Tuple, Dict, Any, Callable
import numpy as np
import pandas as pd

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QLabel,
    QTabWidget, QSplitter, QCheckBox
)
from PySide6.QtCore import Signal, QObject

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.widgets import RectangleSelector
import matplotlib.pyplot as plt

from utils.logging_config import LoggerMixin
from utils.error_handler import error_handler
from utils.design_tokens import DesignTokens


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
        self.point_selection_enabled = False
        
        # Mouse events connected for rectangle selection only
        
        # Color configuration - will be set by theme manager
        self.theme_manager = None  # Will be injected
        palette = DesignTokens.SELECTION_COLORS
        self.default_color = palette['blue']['primary']
        self.selected_color = palette['orange']['primary']
        self.expression_color = palette['green']['primary']
        self.point_size = 20
        self.point_alpha = 0.6
        
        # Setup figure style
        self.figure.patch.set_facecolor('white')
        self.axes.set_facecolor('white')
        self.figure.tight_layout()
        
        self.log_info("Scatter plot canvas initialized")
    
    @error_handler("Plotting scatter data")
    def plot_data(self, x_data: np.ndarray, y_data: np.ndarray, 
                  x_label: str = "X", y_label: str = "Y", 
                  x_log: bool = False, y_log: bool = False) -> None:
        """
        Plot scatter data on the canvas.
        
        Args:
            x_data: X coordinate data
            y_data: Y coordinate data  
            x_label: Label for X axis
            y_label: Label for Y axis
            x_log: Whether to use log scale for X axis
            y_log: Whether to use log scale for Y axis
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
        
        # Set log scales if requested
        if x_log:
            self.axes.set_xscale('log')
        if y_log:
            self.axes.set_yscale('log')
        
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
        
        self.log_info(f"Plotted {len(x_data):,} data points (X log: {x_log}, Y log: {y_log})")
    
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
    
    # Point selection removed as per design specification
    
    def _on_mouse_click(self, event) -> None:
        """
        Handle mouse click events for point selection.
        
        Args:
            event: Mouse click event
        """
        if not self.point_selection_enabled or event.inaxes != self.axes:
            return
        
        if self.x_data is None or self.y_data is None:
            return
        
        # Find the closest point to the click
        if event.xdata is None or event.ydata is None:
            return
        
        # Calculate distances to all points
        distances = np.sqrt((self.x_data - event.xdata)**2 + (self.y_data - event.ydata)**2)
        
        # Find the closest point
        closest_idx = np.argmin(distances)
        
        # Check if the click is close enough (within reasonable distance)
        # Convert to display coordinates for distance check
        xy_pixels = self.axes.transData.transform(np.column_stack([self.x_data, self.y_data]))
        click_pixels = self.axes.transData.transform([event.xdata, event.ydata])
        
        distances_pixels = np.sqrt(np.sum((xy_pixels - click_pixels)**2, axis=1))
        
        # Only select if click is within 10 pixels of the point
        if distances_pixels[closest_idx] <= 10:
            # Toggle selection of the clicked point
            if closest_idx in self.selected_indices:
                self.selected_indices.remove(closest_idx)
                self.log_info(f"Deselected point {closest_idx}")
            else:
                self.selected_indices.append(closest_idx)
                self.log_info(f"Selected point {closest_idx}")
            
            # Update visual highlighting
            self._update_selection_visual()
            
            # Emit signal
            self.selection_changed.emit(self.selected_indices)
            
            self.log_info(f"Point selection: {len(self.selected_indices)} points selected")
    
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
        # 선택 박스 숨김
        if self.rectangle_selector:
            self.rectangle_selector.set_visible(False)
            self.rectangle_selector.set_active(False)
    
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
        """팔레트 내 색상만 허용하도록 수정"""
        palette_hex = [info['primary'].lower() for info in DesignTokens.SELECTION_COLORS.values()]
        if color and color.lower() not in palette_hex:
            color = self.selected_color  # 팔레트 외 색상은 기본 선택색으로 대체
        if self.scatter_plot is None or self.x_data is None:
            return
        
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
    selection_made = Signal(list)  # selected_indices (for backward compatibility)
    selection_made_with_method = Signal(list, str)  # selected_indices, selection_method
    column_changed = Signal(str, str)  # axis, column_name
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # Data storage
        self.data: Optional[pd.DataFrame] = None
        self.available_columns: List[str] = []
        
        # UI setup
        self.setup_ui()
        self.connect_signals()
        
        self.log_info("Scatter plot widget initialized (without expression filter)")
    
    def setup_ui(self) -> None:
        """Set up the widget UI."""
        layout = QVBoxLayout(self)
        
        # Control panel
        controls_panel = self._create_controls_panel()
        layout.addWidget(controls_panel)
        
        # Main content area
        self.canvas = ScatterPlotCanvas(self)
        layout.addWidget(self.canvas)
        
        # Initially disable controls
        self.x_combo.setEnabled(False)
        self.y_combo.setEnabled(False)
        self.rect_button.setEnabled(False)
        self.clear_button.setEnabled(False)
    
    def _create_controls_panel(self) -> QWidget:
        """Create the controls panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Axis selection
        axis_layout = QHBoxLayout()
        
        axis_layout.addWidget(QLabel("X-Axis:"))
        self.x_combo = QComboBox()
        self.x_combo.setMinimumWidth(150)
        axis_layout.addWidget(self.x_combo)
        
        axis_layout.addWidget(QLabel("Y-Axis:"))
        self.y_combo = QComboBox()
        self.y_combo.setMinimumWidth(150)
        axis_layout.addWidget(self.y_combo)
        
        # Refresh button
        self.refresh_button = QPushButton("Refresh Plot")
        axis_layout.addWidget(self.refresh_button)
        
        axis_layout.addStretch()
        layout.addLayout(axis_layout)
        
        # Log scale options
        scale_layout = QHBoxLayout()
        
        self.x_log_checkbox = QCheckBox("X Log Scale")
        self.y_log_checkbox = QCheckBox("Y Log Scale")
        
        scale_layout.addWidget(self.x_log_checkbox)
        scale_layout.addWidget(self.y_log_checkbox)
        scale_layout.addStretch()
        layout.addLayout(scale_layout)
        
        # Selection tools (removed Point Selection)
        tools_layout = QHBoxLayout()
        
        self.rect_button = QPushButton("Rectangle Selection")
        self.rect_button.setCheckable(True)
        tools_layout.addWidget(self.rect_button)
        
        self.clear_button = QPushButton("Clear Selection")
        tools_layout.addWidget(self.clear_button)
        
        tools_layout.addStretch()
        layout.addLayout(tools_layout)
        
        return panel

    def connect_signals(self) -> None:
        """Connect widget signals."""
        self.refresh_button.clicked.connect(self.create_plot)
        self.rect_button.toggled.connect(self.toggle_rectangle_selection)
        self.clear_button.clicked.connect(self.clear_selection)
        self.canvas.selection_changed.connect(self._on_selection_changed)
        
        # Connect log scale checkboxes
        self.x_log_checkbox.toggled.connect(self.update_plot_scales)
        self.y_log_checkbox.toggled.connect(self.update_plot_scales)
    
    @error_handler("Loading data for scatter plot")
    def load_data(self, dataframe: pd.DataFrame) -> None:
        """
        Load data into the scatter plot widget.
        
        Args:
            dataframe: Pandas DataFrame containing cell data
        """
        self.data = dataframe.copy()
        
        # Get numeric columns for plotting
        numeric_columns = self.data.select_dtypes(include=[np.number]).columns.tolist()
        self.available_columns = numeric_columns
        
        # Populate combo boxes
        self.x_combo.clear()
        self.y_combo.clear()
        self.x_combo.addItems(numeric_columns)
        self.y_combo.addItems(numeric_columns)
        
        # Set default selections if available
        if len(numeric_columns) >= 2:
            self.x_combo.setCurrentIndex(0)
            self.y_combo.setCurrentIndex(1)
        elif len(numeric_columns) == 1:
            self.x_combo.setCurrentIndex(0)
            self.y_combo.setCurrentIndex(0)
        
        # Enable controls
        self.x_combo.setEnabled(True)
        self.y_combo.setEnabled(True)
        self.rect_button.setEnabled(True)
        self.clear_button.setEnabled(True)
        self.refresh_button.setEnabled(True)
        self.x_log_checkbox.setEnabled(True)
        self.y_log_checkbox.setEnabled(True)
        
        # Create initial plot
        if numeric_columns:
            self.create_plot()
        
        self.log_info(f"Loaded data with {len(dataframe)} rows and {len(numeric_columns)} numeric columns")
    
    @error_handler("Creating scatter plot")
    def create_plot(self) -> None:
        """Create a new scatter plot with selected columns."""
        if self.data is None or not self.available_columns:
            return
        
        x_column = self.x_combo.currentText()
        y_column = self.y_combo.currentText()
        
        if not x_column or not y_column:
            return
        
        # Get data
        x_data = self.data[x_column].values
        y_data = self.data[y_column].values
        
        # Remove NaN values
        mask = ~(np.isnan(x_data) | np.isnan(y_data))
        x_data = x_data[mask]
        y_data = y_data[mask]
        
        if len(x_data) == 0:
            return
        
        # Get log scale settings
        x_log = self.x_log_checkbox.isChecked()
        y_log = self.y_log_checkbox.isChecked()
        
        # Create plot
        self.canvas.plot_data(x_data, y_data, x_column, y_column, x_log, y_log)
        
        # Enable controls
        self.rect_button.setEnabled(True)
        self.clear_button.setEnabled(True)
        
        self.log_info(f"Created scatter plot: {x_column} vs {y_column} ({len(x_data):,} points)")
        
        # Emit signal
        self.plot_created.emit(x_column, y_column)
    
    def toggle_rectangle_selection(self, enabled: bool) -> None:
        """
        Toggle rectangle selection mode.
        
        Args:
            enabled: Whether rectangle selection is enabled
        """
        self.canvas.enable_rectangle_selection(enabled)
        
        if enabled:
            self.rect_button.setText("Disable Rectangle")
            self.log_info("Rectangle selection enabled - drag to select points")
        else:
            self.rect_button.setText("Rectangle Selection")
            self.log_info("Rectangle selection disabled")
    
    def update_plot_scales(self) -> None:
        """Update plot scales when log scale checkboxes are toggled."""
        if self.data is not None and not self.available_columns:
            return
        
        # Re-create the plot with updated scales
        self.create_plot()
    
    def clear_selection(self) -> None:
        """Clear current selection."""
        self.canvas.clear_selection()
        self.log_info("Selection cleared")
    
    def _on_selection_changed(self, indices: List[int]) -> None:
        """
        Handle selection changes from canvas.
        
        Args:
            indices: List of selected row indices
        """
        self.log_info(f"Selection changed: {len(indices)} points selected")
        
        # Determine selection method based on active tool
        method = "unknown"
        if self.rect_button.isChecked():
            method = "rectangle_selection"
        else:
            method = "programmatic_selection"
        
        # Emit signals
        self.selection_made.emit(indices)
        self.selection_made_with_method.emit(indices, method)
    
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
        if self.data is None:
            return None
        
        indices = self.canvas.get_selected_indices()
        if not indices:
            return None
        
        return self.data.iloc[indices].copy()
    
    def export_plot(self, file_path: str) -> bool:
        """
        Export current plot to file.
        
        Args:
            file_path: Output file path
        
        Returns:
            True if successful, False otherwise
        """
        return self.canvas.export_plot(file_path)