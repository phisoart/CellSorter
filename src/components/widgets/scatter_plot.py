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
    QTabWidget, QSplitter, QCheckBox, QDialog, QListWidget, QListWidgetItem,
    QDialogButtonBox
)
from PySide6.QtCore import Signal, QObject, Qt

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.widgets import RectangleSelector
import matplotlib.pyplot as plt

from utils.logging_config import LoggerMixin
from utils.error_handler import error_handler


class ColumnSelectionDialog(QDialog):
    """다이얼로그를 통한 컬럼 선택 위젯"""
    
    def __init__(self, columns: List[str], current_selection: str = "", title: str = "Select Column", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(400, 500)
        
        # 선택된 컬럼
        self.selected_column = current_selection
        
        layout = QVBoxLayout(self)
        
        # 검색 가능한 리스트
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SingleSelection)
        
        # 컬럼들을 리스트에 추가
        for column in columns:
            item = QListWidgetItem(column)
            self.list_widget.addItem(item)
            if column == current_selection:
                item.setSelected(True)
                self.list_widget.setCurrentItem(item)
        
        layout.addWidget(QLabel(f"Available columns ({len(columns)}):"))
        layout.addWidget(self.list_widget)
        
        # 버튼들
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # 더블클릭으로도 선택 가능
        self.list_widget.itemDoubleClicked.connect(self.accept)
    
    def accept(self):
        """선택 확인"""
        current_item = self.list_widget.currentItem()
        if current_item:
            self.selected_column = current_item.text()
        super().accept()
    
    def get_selected_column(self) -> str:
        """선택된 컬럼 반환"""
        return self.selected_column


class CustomAxisComboBox(QPushButton):
    """다이얼로그를 띄우는 커스텀 축 선택 위젯"""
    
    currentTextChanged = Signal(str)
    
    def __init__(self, axis_name: str = "X", parent=None):
        super().__init__(parent)
        self.axis_name = axis_name
        self.columns = []
        self.current_text = ""
        
        self.setMinimumWidth(180)
        self.setMinimumHeight(32)
        self.clicked.connect(self._show_selection_dialog)
        
        # 스타일 설정
        self.setStyleSheet("""
            QPushButton {
                background-color: var(--background);
                color: var(--foreground);
                border: 1px solid var(--border);
                border-radius: 6px;
                padding: 6px 12px;
                text-align: left;
                font-weight: 400;
            }
            QPushButton:hover {
                border-color: var(--primary);
                background-color: var(--accent);
            }
            QPushButton:pressed {
                background-color: var(--accent)/80;
            }
        """)
        
        self._update_text()
    
    def addItems(self, items: List[str]):
        """아이템들 추가"""
        self.columns = items.copy()
        if items and not self.current_text:
            self.setCurrentText(items[0])
    
    def setCurrentText(self, text: str):
        """현재 텍스트 설정"""
        if text in self.columns:
            self.current_text = text
            self._update_text()
            self.currentTextChanged.emit(text)
    
    def currentText(self) -> str:
        """현재 텍스트 반환"""
        return self.current_text
    
    def _update_text(self):
        """버튼 텍스트 업데이트"""
        if self.current_text:
            # 텍스트가 너무 길면 잘라서 표시
            display_text = self.current_text
            if len(display_text) > 20:
                display_text = display_text[:17] + "..."
            self.setText(f"{display_text} ▼")
        else:
            self.setText(f"Select {self.axis_name}-Axis ▼")
    
    def _show_selection_dialog(self):
        """선택 다이얼로그 표시"""
        if not self.columns:
            return
        
        dialog = ColumnSelectionDialog(
            self.columns, 
            self.current_text, 
            f"Select {self.axis_name}-Axis Column",
            self
        )
        
        if dialog.exec() == QDialog.Accepted:
            new_selection = dialog.get_selected_column()
            if new_selection != self.current_text:
                self.setCurrentText(new_selection)


class ScatterPlotCanvas(FigureCanvas, LoggerMixin):
    """
    Matplotlib canvas for interactive scatter plots with rectangle selection.
    """
    
    # Signals
    selection_changed = Signal(list)  # List of selected indices
    
    def __init__(self, parent=None, width=10, height=8, dpi=100):
        self.figure = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.figure.add_subplot(111)
        
        super().__init__(self.figure)
        self.setParent(parent)
        
        # Set minimum size for the canvas
        self.setMinimumSize(600, 480)  # 10*60 x 8*60 pixels minimum
        
        # Data storage
        self.x_data: Optional[np.ndarray] = None
        self.y_data: Optional[np.ndarray] = None
        self.scatter_plot = None
        self.selected_indices: List[int] = []
        
        # Selection tool
        self.rectangle_selector: Optional[RectangleSelector] = None
        self.selection_enabled = False
        self.point_selection_enabled = False
        
        # Prevent infinite signal loops
        self._updating_highlights = False
        
        # Multiple selection mode management
        self._multiple_selection_mode = False
        self._current_selections: Dict[str, Dict[str, Any]] = {}  # Track multiple selections
        
        # Mouse events connected for rectangle selection only
        
        # Color configuration - will be set by theme manager
        self.theme_manager = None  # Will be injected
        self.default_color = '#1f77b4'  # matplotlib default blue
        self.selected_color = '#ff7f0e'  # orange for selected points
        self.expression_color = '#2ca02c'  # green for expression selection
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
        
        # Exit multiple selection mode when making new rectangle selection
        self._multiple_selection_mode = False
        self._current_selections.clear()
        
        # Set flag to prevent _update_selection_visual from emitting signals
        self._updating_highlights = True
        
        # Update visual highlighting (without signal emission)
        self._update_selection_visual()
        
        # Reset flag
        self._updating_highlights = False
        
        # Clear the rectangle selector to remove the visual rectangle
        if self.rectangle_selector:
            self.rectangle_selector.set_visible(False)
            self.draw_idle()
        
        # Emit signal only once
        self.selection_changed.emit(self.selected_indices)
        
        self.log_info(f"Selected {len(self.selected_indices)} points in rectangle")
    
    def _update_selection_visual(self) -> None:
        """Update visual highlighting of selected points."""
        if self.scatter_plot is None or self.x_data is None:
            return
        
        # If in multiple selection mode, don't override existing colors
        if self._multiple_selection_mode and self._current_selections:
            self.log_info("Skipping visual update - multiple selection mode active")
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
        
        # Don't emit signals during programmatic updates to avoid infinite loops
        if not self._updating_highlights:
            self.selection_changed.emit(self.selected_indices)
    
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
        
        # Set flag to prevent signal emission (avoid infinite loops)
        self._updating_highlights = True
        
        # Exit multiple selection mode when switching to single selection
        self._multiple_selection_mode = False
        self._current_selections.clear()
        
        self.selected_indices = indices
        
        # Update visual highlighting with custom color
        colors = [self.default_color] * len(self.x_data)
        for idx in self.selected_indices:
            if 0 <= idx < len(colors):
                colors[idx] = color
        
        # Update scatter plot colors
        self.scatter_plot.set_color(colors)
        self.draw_idle()
        
        # Reset flag
        self._updating_highlights = False
        
        self.log_info(f"Highlighted {len(indices)} points with color {color}")
    
    def highlight_multiple_selections(self, selections: Dict[str, Dict[str, Any]]) -> None:
        """
        Highlight multiple selections with different colors.
        
        Args:
            selections: Dictionary with selection_id as key and dict with 'indices' and 'color' as value
        """
        if self.scatter_plot is None or self.x_data is None:
            return
        
        # Set flag to prevent signal emission (avoid infinite loops)
        self._updating_highlights = True
        
        # Enable multiple selection mode
        self._multiple_selection_mode = len(selections) > 1
        self._current_selections = selections.copy()
        
        # Reset all colors to default
        colors = [self.default_color] * len(self.x_data)
        
        # Apply colors for each selection (later selections will override earlier ones if there are conflicts)
        all_selected_indices = []
        for selection_id, selection_data in selections.items():
            indices = selection_data.get('indices', [])
            color = selection_data.get('color', self.selected_color)
            all_selected_indices.extend(indices)
            
            for idx in indices:
                if 0 <= idx < len(colors):
                    colors[idx] = color
        
        # Only update selected_indices if not in multiple selection mode
        # This prevents single-selection methods from overriding multiple selections
        if not self._multiple_selection_mode:
            self.selected_indices = all_selected_indices
        else:
            # Clear single selection state when in multiple selection mode
            self.selected_indices = []
        
        # Update scatter plot colors
        self.scatter_plot.set_color(colors)
        self.draw_idle()
        
        # Reset flag
        self._updating_highlights = False
        
        total_highlighted = sum(len(sel_data.get('indices', [])) for sel_data in selections.values())
        self.log_info(f"Highlighted {total_highlighted} points across {len(selections)} selections")
    
    def clear_selection(self) -> None:
        """Clear current selection."""
        self.canvas.clear_selection()
    
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
    
    def _create_controls_panel(self) -> QWidget:
        """Create the controls panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Axis selection and log scale options in one row
        axis_layout = QHBoxLayout()
        
        # X-Axis 선택
        axis_layout.addWidget(QLabel("X-Axis:"))
        self.x_combo = CustomAxisComboBox("X")
        axis_layout.addWidget(self.x_combo)
        
        # X Log Scale 체크박스
        self.x_log_checkbox = QCheckBox("X Log")
        self.x_log_checkbox.setStyleSheet("""
            QCheckBox {
                font-weight: 500;
                spacing: 6px;
            }
            QCheckBox:hover {
                color: var(--primary);
            }
        """)
        axis_layout.addWidget(self.x_log_checkbox)
        
        # 약간의 간격
        axis_layout.addSpacing(20)
        
        # Y-Axis 선택
        axis_layout.addWidget(QLabel("Y-Axis:"))
        self.y_combo = CustomAxisComboBox("Y")
        axis_layout.addWidget(self.y_combo)
        
        # Y Log Scale 체크박스
        self.y_log_checkbox = QCheckBox("Y Log")
        self.y_log_checkbox.setStyleSheet("""
            QCheckBox {
                font-weight: 500;
                spacing: 6px;
            }
            QCheckBox:hover {
                color: var(--primary);
            }
        """)
        axis_layout.addWidget(self.y_log_checkbox)
        
        # 약간의 간격
        axis_layout.addSpacing(20)
        
        # Cell Selection button - placed in the same row as axis controls
        self.rect_button = QPushButton("Cell Selection")
        self.rect_button.setCheckable(True)
        self.rect_button.setStyleSheet("""
            QPushButton {
                background-color: var(--background);
                color: var(--foreground);
                border: 1px solid var(--border);
                border-radius: 8px;
                padding: 10px 16px;
                font-weight: 500;
                min-height: 36px;
                transition: all 0.2s ease;
            }
            QPushButton:hover {
                background-color: var(--primary);
                color: var(--primary-foreground);
                border-color: var(--primary);
                transform: translateY(-2px);
                box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
            }
            QPushButton:pressed {
                background-color: var(--primary)/80;
                transform: translateY(0px);
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }
            QPushButton:disabled {
                opacity: 0.5;
                transform: none;
                box-shadow: none;
            }
            QPushButton:checked {
                background-color: var(--primary);
                color: var(--primary-foreground);
                border-color: var(--primary);
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            }
            QPushButton:checked:hover {
                background-color: var(--primary)/90;
                transform: translateY(-1px);
                box-shadow: 0 6px 12px rgba(0, 0, 0, 0.2);
            }
        """)
        axis_layout.addWidget(self.rect_button)
        
        axis_layout.addStretch()
        layout.addLayout(axis_layout)
        
        # Minimal spacing after controls
        layout.addSpacing(8)
        
        # Add stretch to push canvas to fill remaining space
        layout.addStretch()
        
        return panel

    def connect_signals(self) -> None:
        """Connect widget signals."""
        self.rect_button.toggled.connect(self.toggle_rectangle_selection)
        self.canvas.selection_changed.connect(self._on_selection_changed)
        
        # Connect custom combo boxes - auto refresh plot when axis changes
        self.x_combo.currentTextChanged.connect(lambda text: self.create_plot())
        self.y_combo.currentTextChanged.connect(lambda text: self.create_plot())
        
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
        
        # Populate custom combo boxes
        self.x_combo.addItems(numeric_columns)
        self.y_combo.addItems(numeric_columns)
        
        # Set default selections if available
        if len(numeric_columns) >= 2:
            self.x_combo.setCurrentText(numeric_columns[0])
            self.y_combo.setCurrentText(numeric_columns[1])
        elif len(numeric_columns) == 1:
            self.x_combo.setCurrentText(numeric_columns[0])
            self.y_combo.setCurrentText(numeric_columns[0])
        
        # Enable controls
        self.x_combo.setEnabled(True)
        self.y_combo.setEnabled(True)
        self.rect_button.setEnabled(True)
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
            self.rect_button.setText("Disable Selection")
            self.log_info("Cell selection enabled - drag to select points")
        else:
            self.rect_button.setText("Cell Selection")
            self.log_info("Cell selection disabled")
    
    def update_plot_scales(self) -> None:
        """Update plot scales when log scale checkboxes are toggled."""
        if self.data is not None and not self.available_columns:
            return
        
        # Re-create the plot with updated scales
        self.create_plot()
    
    def _on_selection_changed(self, indices: List[int]) -> None:
        """
        Handle selection changes from canvas.
        
        Args:
            indices: List of selected row indices
        """
        # Skip signal emission if we're updating highlights programmatically
        if self.canvas._updating_highlights:
            self.log_info(f"Skipping signal emission during programmatic highlight update: {len(indices)} points")
            return
            
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
    
    def highlight_multiple_selections(self, selections: Dict[str, Dict[str, Any]]) -> None:
        """
        Highlight multiple selections with different colors.
        
        Args:
            selections: Dictionary with selection_id as key and dict with 'indices' and 'color' as value
        """
        self.canvas.highlight_multiple_selections(selections)
    
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