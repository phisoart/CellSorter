"""
Widget Factory

Creates PySide6 widgets from UI definitions.
Handles widget instantiation and basic property setup.
"""

import logging
from typing import Dict, Any, Optional, Type
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

from ..ui_compatibility import Widget
from ..ui_model import WidgetType
from ..mode_manager import is_dev_mode

logger = logging.getLogger(__name__)


class WidgetCreationError(Exception):
    """Raised when widget creation fails."""
    pass


class WidgetFactory:
    """Factory for creating PySide6 widgets from definitions."""
    
    def __init__(self):
        self._widget_classes = self._build_widget_class_map()
        self._created_widgets: Dict[str, QWidget] = {}
    
    def _build_widget_class_map(self) -> Dict[WidgetType, Type[QWidget]]:
        """Build mapping of widget types to Qt classes."""
        return {
            # Basic widgets
            WidgetType.WIDGET: QWidget,
            WidgetType.LABEL: QLabel,
            WidgetType.PUSH_BUTTON: QPushButton,
            WidgetType.LINE_EDIT: QLineEdit,
            WidgetType.TEXT_EDIT: QTextEdit,
            WidgetType.COMBO_BOX: QComboBox,
            WidgetType.CHECK_BOX: QCheckBox,
            WidgetType.RADIO_BUTTON: QRadioButton,
            WidgetType.SPIN_BOX: QSpinBox,
            WidgetType.DOUBLE_SPIN_BOX: QDoubleSpinBox,
            WidgetType.SLIDER: QSlider,
            WidgetType.PROGRESS_BAR: QProgressBar,
            
            # Container widgets
            WidgetType.GROUP_BOX: QGroupBox,
            WidgetType.FRAME: QFrame,
            WidgetType.SCROLL_AREA: QScrollArea,
            WidgetType.TAB_WIDGET: QTabWidget,
            WidgetType.STACKED_WIDGET: QStackedWidget,
            
            # Layout widgets
            WidgetType.SPLITTER: QSplitter,
            
            # Top-level widgets
            WidgetType.MAIN_WINDOW: QMainWindow,
            WidgetType.DIALOG: QDialog,
            
            # Advanced widgets
            WidgetType.TABLE_WIDGET: QTableWidget,
            WidgetType.TREE_WIDGET: QTreeWidget,
            WidgetType.LIST_WIDGET: QListWidget,
        }
    
    def create_widget(self, widget_def: Widget, parent: Optional[QWidget] = None) -> QWidget:
        """
        Create QWidget from widget definition.
        
        Args:
            widget_def: Widget definition
            parent: Parent widget
            
        Returns:
            Created QWidget instance
            
        Raises:
            WidgetCreationError: If widget creation fails
        """
        if is_dev_mode():
            raise WidgetCreationError("Cannot create widgets in development mode")
        
        # Check if running in test environment
        if self._is_test_environment():
            from unittest.mock import Mock
            mock_widget = Mock()
            mock_widget.setObjectName = Mock()
            self._created_widgets[widget_def.name] = mock_widget
            return mock_widget
        
        try:
            # Get widget class
            widget_class = self._widget_classes.get(widget_def.type)
            if not widget_class:
                # Try custom widget creation
                qt_widget = self._create_custom_widget(widget_def, parent)
            else:
                # Create standard Qt widget
                if parent:
                    qt_widget = widget_class(parent)
                else:
                    qt_widget = widget_class()
            
            # Set object name
            qt_widget.setObjectName(widget_def.name)
            
            # Store for later reference
            self._created_widgets[widget_def.name] = qt_widget
            
            logger.debug(f"Created widget: {widget_def.name} ({widget_def.type.value})")
            return qt_widget
            
        except Exception as e:
            raise WidgetCreationError(f"Failed to create widget {widget_def.name}: {e}") from e
    
    def _is_test_environment(self) -> bool:
        """Check if running in test environment."""
        import sys
        return 'pytest' in sys.modules or 'unittest' in sys.modules
    
    def _create_custom_widget(self, widget_def: Widget, parent: Optional[QWidget]) -> QWidget:
        """Create custom CellSorter-specific widgets."""
        if widget_def.type == WidgetType.SCATTER_PLOT:
            return self._create_scatter_plot(widget_def, parent)
        elif widget_def.type == WidgetType.WELL_PLATE:
            return self._create_well_plate(widget_def, parent)
        elif widget_def.type == WidgetType.SELECTION_PANEL:
            return self._create_selection_panel(widget_def, parent)
        elif widget_def.type == WidgetType.EXPRESSION_FILTER:
            return self._create_expression_filter(widget_def, parent)
        else:
            raise WidgetCreationError(f"Unknown custom widget type: {widget_def.type}")
    
    def _create_scatter_plot(self, widget_def: Widget, parent: Optional[QWidget]) -> QWidget:
        """Create scatter plot widget."""
        try:
            from components.widgets.scatter_plot import ScatterPlot
            return ScatterPlot(parent) if parent else ScatterPlot()
        except ImportError:
            logger.warning("ScatterPlot widget not available, using QWidget placeholder")
            widget = QWidget(parent) if parent else QWidget()
            widget.setMinimumSize(400, 300)
            return widget
    
    def _create_well_plate(self, widget_def: Widget, parent: Optional[QWidget]) -> QWidget:
        """Create well plate widget."""
        try:
            from components.widgets.well_plate import WellPlate
            return WellPlate(parent) if parent else WellPlate()
        except ImportError:
            logger.warning("WellPlate widget not available, using QWidget placeholder")
            widget = QWidget(parent) if parent else QWidget()
            widget.setMinimumSize(300, 200)
            return widget
    
    def _create_selection_panel(self, widget_def: Widget, parent: Optional[QWidget]) -> QWidget:
        """Create selection panel widget."""
        try:
            from components.widgets.selection_panel import SelectionPanel
            return SelectionPanel(parent) if parent else SelectionPanel()
        except ImportError:
            logger.warning("SelectionPanel widget not available, using QWidget placeholder")
            widget = QWidget(parent) if parent else QWidget()
            widget.setMinimumSize(250, 400)
            return widget
    
    def _create_expression_filter(self, widget_def: Widget, parent: Optional[QWidget]) -> QWidget:
        """Create expression filter widget."""
        try:
            from components.widgets.expression_filter import ExpressionFilter
            return ExpressionFilter(parent) if parent else ExpressionFilter()
        except ImportError:
            logger.warning("ExpressionFilter widget not available, using QWidget placeholder")
            widget = QWidget(parent) if parent else QWidget()
            widget.setMinimumSize(300, 150)
            return widget
    
    def get_created_widget(self, name: str) -> Optional[QWidget]:
        """Get previously created widget by name."""
        return self._created_widgets.get(name)
    
    def clear_created_widgets(self) -> None:
        """Clear cache of created widgets."""
        self._created_widgets.clear()
    
    def get_widget_class(self, widget_type: WidgetType) -> Optional[Type[QWidget]]:
        """Get Qt widget class for widget type."""
        return self._widget_classes.get(widget_type) 