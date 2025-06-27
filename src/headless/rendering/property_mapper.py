"""
Property Mapper

Maps UI definition properties to PySide6 widget properties.
Handles property conversion and application to widgets.
"""

import logging
from typing import Any, Dict, Optional
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QSize

from ..ui_compatibility import Widget
from ..ui_model import Geometry, SizePolicy, LayoutType

logger = logging.getLogger(__name__)


class PropertyMappingError(Exception):
    """Raised when property mapping fails."""
    pass


class PropertyMapper:
    """Maps UI definition properties to Qt widget properties."""
    
    def apply_properties(self, qt_widget: QWidget, widget_def: Widget) -> None:
        """
        Apply all properties from widget definition to Qt widget.
        
        Args:
            qt_widget: Qt widget to configure
            widget_def: Widget definition containing properties
            
        Raises:
            PropertyMappingError: If property application fails
        """
        try:
            # Apply basic properties
            if widget_def.visible is not None:
                qt_widget.setVisible(widget_def.visible)
            
            if widget_def.enabled is not None:
                qt_widget.setEnabled(widget_def.enabled)
            
            if widget_def.tooltip:
                qt_widget.setToolTip(widget_def.tooltip)
            
            if widget_def.style_sheet:
                qt_widget.setStyleSheet(widget_def.style_sheet)
            
            # Apply geometry
            if widget_def.geometry:
                self._apply_geometry(qt_widget, widget_def.geometry)
            
            # Apply size constraints
            if widget_def.minimum_size:
                qt_widget.setMinimumSize(
                    widget_def.minimum_size.width,
                    widget_def.minimum_size.height
                )
            
            if widget_def.maximum_size:
                qt_widget.setMaximumSize(
                    widget_def.maximum_size.width,
                    widget_def.maximum_size.height
                )
            
            # Apply size policy
            if widget_def.size_policy:
                self._apply_size_policy(qt_widget, widget_def.size_policy)
            
            # Apply widget-specific properties
            self._apply_widget_specific_properties(qt_widget, widget_def)
            
            logger.debug(f"Applied properties to widget: {widget_def.name}")
            
        except Exception as e:
            raise PropertyMappingError(f"Failed to apply properties to {widget_def.name}: {e}") from e
    
    def _apply_geometry(self, qt_widget: QWidget, geometry: Geometry) -> None:
        """Apply geometry to widget."""
        qt_widget.setGeometry(
            geometry.x,
            geometry.y,
            geometry.width,
            geometry.height
        )
    
    def _apply_size_policy(self, qt_widget: QWidget, size_policy: SizePolicy) -> None:
        """Apply size policy to widget."""
        from PySide6.QtWidgets import QSizePolicy
        
        # Map string values to Qt constants
        policy_map = {
            'fixed': QSizePolicy.Policy.Fixed,
            'minimum': QSizePolicy.Policy.Minimum,
            'maximum': QSizePolicy.Policy.Maximum,
            'preferred': QSizePolicy.Policy.Preferred,
            'expanding': QSizePolicy.Policy.Expanding,
            'minimum_expanding': QSizePolicy.Policy.MinimumExpanding,
            'ignored': QSizePolicy.Policy.Ignored,
        }
        
        h_policy = policy_map.get(size_policy.horizontal_policy, QSizePolicy.Policy.Preferred)
        v_policy = policy_map.get(size_policy.vertical_policy, QSizePolicy.Policy.Preferred)
        
        qt_size_policy = QSizePolicy(h_policy, v_policy)
        
        if size_policy.horizontal_stretch is not None:
            qt_size_policy.setHorizontalStretch(size_policy.horizontal_stretch)
        
        if size_policy.vertical_stretch is not None:
            qt_size_policy.setVerticalStretch(size_policy.vertical_stretch)
        
        qt_widget.setSizePolicy(qt_size_policy)
    
    def _apply_widget_specific_properties(self, qt_widget: QWidget, widget_def: Widget) -> None:
        """Apply widget-type specific properties."""
        properties = widget_def.properties or {}
        
        # Apply text property for text-based widgets
        if 'text' in properties:
            if hasattr(qt_widget, 'setText'):
                qt_widget.setText(str(properties['text']))
            elif hasattr(qt_widget, 'setPlainText'):
                qt_widget.setPlainText(str(properties['text']))
        
        # Apply placeholder text
        if 'placeholder_text' in properties and hasattr(qt_widget, 'setPlaceholderText'):
            qt_widget.setPlaceholderText(str(properties['placeholder_text']))
        
        # Apply checked state for checkable widgets
        if 'checked' in properties and hasattr(qt_widget, 'setChecked'):
            qt_widget.setChecked(bool(properties['checked']))
        
        # Apply value for value-based widgets
        if 'value' in properties:
            if hasattr(qt_widget, 'setValue'):
                qt_widget.setValue(properties['value'])
            elif hasattr(qt_widget, 'setCurrentText'):
                qt_widget.setCurrentText(str(properties['value']))
        
        # Apply minimum and maximum for range widgets
        if 'minimum' in properties and hasattr(qt_widget, 'setMinimum'):
            qt_widget.setMinimum(properties['minimum'])
        
        if 'maximum' in properties and hasattr(qt_widget, 'setMaximum'):
            qt_widget.setMaximum(properties['maximum'])
        
        # Apply step for spin boxes
        if 'step' in properties and hasattr(qt_widget, 'setSingleStep'):
            qt_widget.setSingleStep(properties['step'])
        
        # Apply items for combo boxes and lists
        if 'items' in properties:
            if hasattr(qt_widget, 'addItems'):
                qt_widget.addItems([str(item) for item in properties['items']])
        
        # Apply orientation for sliders
        if 'orientation' in properties and hasattr(qt_widget, 'setOrientation'):
            orientation = Qt.Orientation.Horizontal if properties['orientation'] == 'horizontal' else Qt.Orientation.Vertical
            qt_widget.setOrientation(orientation)
        
        # Apply read-only state
        if 'read_only' in properties and hasattr(qt_widget, 'setReadOnly'):
            qt_widget.setReadOnly(bool(properties['read_only']))
        
        # Apply word wrap for text widgets
        if 'word_wrap' in properties and hasattr(qt_widget, 'setWordWrap'):
            qt_widget.setWordWrap(bool(properties['word_wrap']))
        
        # Apply selection mode for list widgets
        if 'selection_mode' in properties and hasattr(qt_widget, 'setSelectionMode'):
            selection_map = {
                'single': qt_widget.SingleSelection,
                'multi': qt_widget.MultiSelection,
                'extended': qt_widget.ExtendedSelection,
                'none': qt_widget.NoSelection,
            }
            mode = selection_map.get(properties['selection_mode'], qt_widget.SingleSelection)
            qt_widget.setSelectionMode(mode)
    
    def extract_properties(self, qt_widget: QWidget) -> Dict[str, Any]:
        """
        Extract properties from Qt widget to create widget definition.
        
        Args:
            qt_widget: Qt widget to extract properties from
            
        Returns:
            Dictionary of extracted properties
        """
        properties = {}
        
        try:
            # Extract basic properties
            properties['visible'] = qt_widget.isVisible()
            properties['enabled'] = qt_widget.isEnabled()
            
            if qt_widget.toolTip():
                properties['tooltip'] = qt_widget.toolTip()
            
            if qt_widget.styleSheet():
                properties['style_sheet'] = qt_widget.styleSheet()
            
            # Extract geometry
            geom = qt_widget.geometry()
            properties['geometry'] = {
                'x': geom.x(),
                'y': geom.y(),
                'width': geom.width(),
                'height': geom.height()
            }
            
            # Extract size constraints
            min_size = qt_widget.minimumSize()
            if min_size.width() > 0 or min_size.height() > 0:
                properties['minimum_size'] = {
                    'width': min_size.width(),
                    'height': min_size.height()
                }
            
            max_size = qt_widget.maximumSize()
            if max_size.width() < 16777215 or max_size.height() < 16777215:  # Qt's QWIDGETSIZE_MAX
                properties['maximum_size'] = {
                    'width': max_size.width(),
                    'height': max_size.height()
                }
            
            # Extract widget-specific properties
            widget_props = self._extract_widget_specific_properties(qt_widget)
            properties.update(widget_props)
            
            return properties
            
        except Exception as e:
            logger.warning(f"Failed to extract some properties from widget: {e}")
            return properties
    
    def _extract_widget_specific_properties(self, qt_widget: QWidget) -> Dict[str, Any]:
        """Extract widget-type specific properties."""
        properties = {}
        
        # Extract text
        if hasattr(qt_widget, 'text'):
            text = qt_widget.text()
            if text:
                properties['text'] = text
        elif hasattr(qt_widget, 'plainText'):
            text = qt_widget.plainText()
            if text:
                properties['text'] = text
        
        # Extract placeholder text
        if hasattr(qt_widget, 'placeholderText'):
            placeholder = qt_widget.placeholderText()
            if placeholder:
                properties['placeholder_text'] = placeholder
        
        # Extract checked state
        if hasattr(qt_widget, 'isChecked'):
            properties['checked'] = qt_widget.isChecked()
        
        # Extract value
        if hasattr(qt_widget, 'value'):
            properties['value'] = qt_widget.value()
        elif hasattr(qt_widget, 'currentText'):
            current = qt_widget.currentText()
            if current:
                properties['value'] = current
        
        # Extract range properties
        if hasattr(qt_widget, 'minimum'):
            properties['minimum'] = qt_widget.minimum()
        
        if hasattr(qt_widget, 'maximum'):
            properties['maximum'] = qt_widget.maximum()
        
        if hasattr(qt_widget, 'singleStep'):
            properties['step'] = qt_widget.singleStep()
        
        # Extract read-only state
        if hasattr(qt_widget, 'isReadOnly'):
            properties['read_only'] = qt_widget.isReadOnly()
        
        # Extract word wrap
        if hasattr(qt_widget, 'wordWrap'):
            properties['word_wrap'] = qt_widget.wordWrap()
        
        return properties 