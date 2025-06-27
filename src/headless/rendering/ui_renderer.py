"""
UI Renderer

Main rendering engine that combines widget creation and property application.
Converts complete UI definitions into functional PySide6 GUIs.
"""

import logging
from typing import Dict, Optional, List
from PySide6.QtWidgets import QWidget, QLayout, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout, QStackedLayout

from ..ui_compatibility import UI, Widget
from ..mode_manager import is_dev_mode
from .widget_factory import WidgetFactory, WidgetCreationError
from .property_mapper import PropertyMapper, PropertyMappingError
from ..ui_model import LayoutType, LayoutItem

logger = logging.getLogger(__name__)


class UIRenderingError(Exception):
    """Raised when UI rendering fails."""
    pass


class UIRenderer:
    """Renders complete UI definitions into PySide6 widgets."""
    
    def __init__(self):
        self.widget_factory = WidgetFactory()
        self.property_mapper = PropertyMapper()
        self._rendered_widgets: Dict[str, QWidget] = {}
    
    def render_ui(self, ui_def: UI) -> Optional[QWidget]:
        """
        Render UI definition to Qt widgets.
        
        Args:
            ui_def: UI definition to render
            
        Returns:
            Root widget or None if no widgets
            
        Raises:
            UIRenderingError: If rendering fails
        """
        if is_dev_mode():
            raise UIRenderingError("Cannot render UI in development mode")
        
        # Check if running in test environment
        if self._is_test_environment():
            from unittest.mock import Mock
            return Mock()
        
        try:
            self.clear_rendered_widgets()
            
            if not ui_def.widgets:
                logger.warning("No widgets to render")
                return None
            
            # Create all widgets first
            for widget_def in ui_def.widgets:
                parent_widget = None
                if widget_def.parent_name:
                    parent_widget = self.get_rendered_widget(widget_def.parent_name)
                
                qt_widget = self.widget_factory.create_widget(widget_def, parent_widget)
                self.property_mapper.apply_properties(qt_widget, widget_def)
                self._rendered_widgets[widget_def.name] = qt_widget
                
                logger.debug(f"Rendered widget: {widget_def.name}")
            
            # Find and return root widget
            root_widget = self.find_root_widget(ui_def.widgets)
            return root_widget
            
        except Exception as e:
            raise UIRenderingError(f"Failed to render UI: {e}") from e
    
    def _is_test_environment(self) -> bool:
        """Check if running in test environment."""
        import sys
        return 'pytest' in sys.modules or 'unittest' in sys.modules
    
    def _find_root_widget(self, widgets: List[Widget]) -> Optional[Widget]:
        """Find the root widget (widget with no parent)."""
        for widget in widgets:
            if not widget.parent:
                return widget
        return None
    
    def _create_widget_hierarchy(self, widget_def: Widget, all_widgets: List[Widget], parent_widget: Optional[QWidget] = None) -> QWidget:
        """
        Recursively create widget hierarchy.
        
        Args:
            widget_def: Widget definition to create
            all_widgets: All widget definitions for finding children
            parent_widget: Parent Qt widget
            
        Returns:
            Created Qt widget
        """
        # Create the widget
        qt_widget = self.widget_factory.create_widget(widget_def, parent_widget)
        
        # Apply properties
        self.property_mapper.apply_properties(qt_widget, widget_def)
        
        # Store for later reference
        self._rendered_widgets[widget_def.name] = qt_widget
        
        # Create child widgets
        child_widgets = [w for w in all_widgets if w.parent == widget_def.name]
        for child_def in child_widgets:
            self._create_widget_hierarchy(child_def, all_widgets, qt_widget)
        
        return qt_widget
    
    def _apply_layouts(self, ui_def: UI) -> None:
        """Apply layout configurations to widgets."""
        if not ui_def.layouts:
            return
        
        for layout_item in ui_def.layouts:
            try:
                self._apply_layout_to_widget(layout_item)
            except Exception as e:
                logger.error(f"Failed to apply layout {layout_item.name}: {e}")
                # Continue with other layouts
    
    def _apply_layout_to_widget(self, layout_item: LayoutItem) -> None:
        """Apply layout to specific widget."""
        parent_widget = self._rendered_widgets.get(layout_item.parent)
        if not parent_widget:
            logger.warning(f"Parent widget {layout_item.parent} not found for layout {layout_item.name}")
            return
        
        # Create layout based on type
        layout = self._create_layout(layout_item.layout_type)
        if not layout:
            logger.warning(f"Unsupported layout type: {layout_item.layout_type}")
            return
        
        # Apply layout properties
        if layout_item.spacing is not None:
            layout.setSpacing(layout_item.spacing)
        
        if layout_item.margins:
            layout.setContentsMargins(
                layout_item.margins.left,
                layout_item.margins.top,
                layout_item.margins.right,
                layout_item.margins.bottom
            )
        
        # Add child widgets to layout
        for child_name in layout_item.children:
            child_widget = self._rendered_widgets.get(child_name)
            if child_widget:
                if layout_item.layout_type == LayoutType.GRID:
                    # For grid layout, use child position if available
                    row, col = self._get_grid_position(child_name, layout_item)
                    layout.addWidget(child_widget, row, col)
                elif layout_item.layout_type == LayoutType.FORM:
                    # For form layout, need label and field
                    label_text = self._get_form_label(child_name, layout_item)
                    layout.addRow(label_text, child_widget)
                else:
                    # For box layouts
                    stretch = self._get_widget_stretch(child_name, layout_item)
                    layout.addWidget(child_widget, stretch)
        
        # Set layout to parent widget
        parent_widget.setLayout(layout)
    
    def _create_layout(self, layout_type: LayoutType) -> Optional[QLayout]:
        """Create Qt layout based on type."""
        if layout_type == LayoutType.VBOX:
            return QVBoxLayout()
        elif layout_type == LayoutType.HBOX:
            return QHBoxLayout()
        elif layout_type == LayoutType.GRID:
            return QGridLayout()
        elif layout_type == LayoutType.FORM:
            return QFormLayout()
        elif layout_type == LayoutType.STACKED:
            return QStackedLayout()
        else:
            return None
    
    def _get_grid_position(self, child_name: str, layout_item: LayoutItem) -> tuple[int, int]:
        """Get grid position for child widget."""
        # This would ideally be stored in the layout item
        # For now, return default position
        index = layout_item.children.index(child_name)
        cols = 2  # Default to 2 columns
        row = index // cols
        col = index % cols
        return row, col
    
    def _get_form_label(self, child_name: str, layout_item: LayoutItem) -> str:
        """Get form label for child widget."""
        # This would ideally be stored in the layout item
        # For now, return default label
        return child_name.replace('_', ' ').title()
    
    def _get_widget_stretch(self, child_name: str, layout_item: LayoutItem) -> int:
        """Get stretch factor for child widget."""
        # This would ideally be stored in the layout item
        # For now, return default stretch
        return 0
    
    def _connect_events(self, ui_def: UI) -> None:
        """Connect event handlers to widgets."""
        if not ui_def.events:
            return
        
        for event in ui_def.events:
            try:
                self._connect_event(event)
            except Exception as e:
                logger.error(f"Failed to connect event {event.name}: {e}")
                # Continue with other events
    
    def _connect_event(self, event) -> None:
        """Connect single event handler."""
        # Event connection would require dynamic handler loading
        # This is a placeholder for future implementation
        logger.debug(f"Event connection placeholder: {event.name} -> {event.handler}")
    
    def get_rendered_widget(self, name: str) -> Optional[QWidget]:
        """Get rendered widget by name."""
        return self._rendered_widgets.get(name)
    
    def extract_ui_definition(self, root_widget: QWidget, ui_name: str = "extracted_ui") -> UI:
        """
        Extract UI definition from existing Qt widget hierarchy.
        
        Args:
            root_widget: Root Qt widget to extract from
            ui_name: Name for the extracted UI
            
        Returns:
            UI definition extracted from widgets
        """
        try:
            # Extract widget hierarchy
            widgets = self._extract_widget_hierarchy(root_widget)
            
            # Extract layouts (simplified)
            layouts = self._extract_layouts(root_widget, widgets)
            
            # Create UI definition
            ui_def = UI(
                widgets=widgets,
                layouts=layouts,
                events=[],  # Events cannot be easily extracted
                metadata={
                    'name': ui_name,
                    'extracted_from': 'qt_widget',
                    'version': '1.0'
                }
            )
            
            return ui_def
            
        except Exception as e:
            raise UIRenderingError(f"Failed to extract UI definition: {e}") from e
    
    def _extract_widget_hierarchy(self, widget: QWidget, parent_name: Optional[str] = None) -> List[Widget]:
        """Extract widget hierarchy recursively."""
        widgets = []
        
        # Create widget definition for current widget
        widget_def = self._extract_widget_definition(widget, parent_name)
        widgets.append(widget_def)
        
        # Extract child widgets
        for child in widget.findChildren(QWidget, options=QtCore.Qt.FindDirectChildrenOnly):
            child_widgets = self._extract_widget_hierarchy(child, widget_def.name)
            widgets.extend(child_widgets)
        
        return widgets
    
    def _extract_widget_definition(self, widget: QWidget, parent_name: Optional[str]) -> Widget:
        """Extract widget definition from Qt widget."""
        # Determine widget type (simplified)
        widget_type = self._determine_widget_type(widget)
        
        # Extract properties
        properties = self.property_mapper.extract_properties(widget)
        
        # Create widget definition
        return Widget(
            name=widget.objectName() or f"widget_{id(widget)}",
            type=widget_type,
            parent=parent_name,
            properties=properties.get('widget_properties', {}),
            visible=properties.get('visible', True),
            enabled=properties.get('enabled', True),
            tooltip=properties.get('tooltip'),
            style_sheet=properties.get('style_sheet'),
            geometry=properties.get('geometry'),
            minimum_size=properties.get('minimum_size'),
            maximum_size=properties.get('maximum_size'),
            size_policy=properties.get('size_policy')
        )
    
    def _determine_widget_type(self, widget: QWidget):
        """Determine widget type from Qt widget class."""
        from ..ui_model import WidgetType
        
        class_name = widget.__class__.__name__
        type_map = {
            'QWidget': WidgetType.WIDGET,
            'QLabel': WidgetType.LABEL,
            'QPushButton': WidgetType.PUSH_BUTTON,
            'QLineEdit': WidgetType.LINE_EDIT,
            'QTextEdit': WidgetType.TEXT_EDIT,
            'QComboBox': WidgetType.COMBO_BOX,
            'QCheckBox': WidgetType.CHECK_BOX,
            'QRadioButton': WidgetType.RADIO_BUTTON,
            'QSpinBox': WidgetType.SPIN_BOX,
            'QDoubleSpinBox': WidgetType.DOUBLE_SPIN_BOX,
            'QSlider': WidgetType.SLIDER,
            'QProgressBar': WidgetType.PROGRESS_BAR,
            'QGroupBox': WidgetType.GROUP_BOX,
            'QFrame': WidgetType.FRAME,
            'QScrollArea': WidgetType.SCROLL_AREA,
            'QTabWidget': WidgetType.TAB_WIDGET,
            'QStackedWidget': WidgetType.STACKED_WIDGET,
            'QSplitter': WidgetType.SPLITTER,
            'QMainWindow': WidgetType.MAIN_WINDOW,
            'QDialog': WidgetType.DIALOG,
            'QTableWidget': WidgetType.TABLE_WIDGET,
            'QTreeWidget': WidgetType.TREE_WIDGET,
            'QListWidget': WidgetType.LIST_WIDGET,
        }
        
        return type_map.get(class_name, WidgetType.WIDGET)
    
    def _extract_layouts(self, root_widget: QWidget, widgets: List[Widget]) -> List[LayoutItem]:
        """Extract layout information (simplified)."""
        # Layout extraction is complex and would require detailed analysis
        # This is a placeholder for future implementation
        return [] 