"""
Tests for widget rendering engine
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os
import sys

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from headless.ui_compatibility import Widget, UI
from headless.ui_model import WidgetType, Size, Geometry
from headless.rendering.widget_factory import WidgetFactory, WidgetCreationError
from headless.rendering.property_mapper import PropertyMapper
from headless.rendering.ui_renderer import UIRenderer


class TestWidgetFactory:
    """Test widget factory functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.factory = WidgetFactory()
    
    @patch('headless.mode_manager.is_dev_mode', return_value=True)
    def test_create_widget_in_dev_mode_raises_error(self, mock_dev_mode):
        """Test that widget creation fails in dev mode."""
        widget_def = Widget(
            name="test_widget",
            type=WidgetType.WIDGET,
            parent=None
        )
        
        with pytest.raises(WidgetCreationError, match="Cannot create widgets in development mode"):
            self.factory.create_widget(widget_def)
    
    @patch('headless.mode_manager.is_dev_mode', return_value=False)
    @patch('PySide6.QtWidgets.QWidget')
    def test_create_basic_widget(self, mock_qwidget, mock_dev_mode):
        """Test creating basic Qt widget."""
        mock_widget_instance = Mock()
        mock_qwidget.return_value = mock_widget_instance
        
        widget_def = Widget(
            name="test_widget",
            type=WidgetType.WIDGET,
            parent=None
        )
        
        result = self.factory.create_widget(widget_def)
        
        assert result == mock_widget_instance
        mock_widget_instance.setObjectName.assert_called_once_with("test_widget")
        assert self.factory.get_created_widget("test_widget") == mock_widget_instance
    
    @patch('headless.mode_manager.is_dev_mode', return_value=False)
    @patch('PySide6.QtWidgets.QPushButton')
    def test_create_push_button(self, mock_button, mock_dev_mode):
        """Test creating push button widget."""
        mock_button_instance = Mock()
        mock_button.return_value = mock_button_instance
        
        widget_def = Widget(
            name="test_button",
            type=WidgetType.PUSH_BUTTON,
            parent=None
        )
        
        result = self.factory.create_widget(widget_def)
        
        assert result == mock_button_instance
        mock_button.assert_called_once_with()
        mock_button_instance.setObjectName.assert_called_once_with("test_button")
    
    @patch('headless.mode_manager.is_dev_mode', return_value=False)
    def test_create_custom_widget_fallback(self, mock_dev_mode):
        """Test creating custom widget with fallback to placeholder."""
        widget_def = Widget(
            name="test_scatter",
            type=WidgetType.SCATTER_PLOT,
            parent=None
        )
        
        with patch('PySide6.QtWidgets.QWidget') as mock_qwidget:
            mock_widget_instance = Mock()
            mock_qwidget.return_value = mock_widget_instance
            
            result = self.factory.create_widget(widget_def)
            
            assert result == mock_widget_instance
            mock_widget_instance.setMinimumSize.assert_called_once_with(400, 300)
    
    def test_get_widget_class(self):
        """Test getting widget class for widget type."""
        from PySide6.QtWidgets import QWidget, QPushButton
        
        with patch.dict('sys.modules', {'PySide6.QtWidgets': Mock(QWidget=QWidget, QPushButton=QPushButton)}):
            assert self.factory.get_widget_class(WidgetType.WIDGET) == QWidget
            assert self.factory.get_widget_class(WidgetType.PUSH_BUTTON) == QPushButton
    
    def test_clear_created_widgets(self):
        """Test clearing created widgets cache."""
        self.factory._created_widgets["test"] = Mock()
        assert len(self.factory._created_widgets) == 1
        
        self.factory.clear_created_widgets()
        assert len(self.factory._created_widgets) == 0


class TestPropertyMapper:
    """Test property mapper functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.mapper = PropertyMapper()
    
    def test_apply_basic_properties(self):
        """Test applying basic widget properties."""
        mock_widget = Mock()
        widget_def = Widget(
            name="test_widget",
            type=WidgetType.WIDGET,
            parent=None,
            visible=False,
            enabled=False,
            tooltip="Test tooltip",
            style_sheet="color: red;"
        )
        
        self.mapper.apply_properties(mock_widget, widget_def)
        
        mock_widget.setVisible.assert_called_once_with(False)
        mock_widget.setEnabled.assert_called_once_with(False)
        mock_widget.setToolTip.assert_called_once_with("Test tooltip")
        mock_widget.setStyleSheet.assert_called_once_with("color: red;")
    
    def test_apply_geometry(self):
        """Test applying geometry to widget."""
        mock_widget = Mock()
        geometry = Geometry(x=10, y=20, width=300, height=200)
        widget_def = Widget(
            name="test_widget",
            type=WidgetType.WIDGET,
            parent=None,
            geometry=geometry
        )
        
        self.mapper.apply_properties(mock_widget, widget_def)
        
        mock_widget.setGeometry.assert_called_once_with(10, 20, 300, 200)
    
    def test_apply_size_constraints(self):
        """Test applying size constraints."""
        mock_widget = Mock()
        min_size = Size(width=100, height=50)
        max_size = Size(width=500, height=300)
        widget_def = Widget(
            name="test_widget",
            type=WidgetType.WIDGET,
            parent=None,
            minimum_size=min_size,
            maximum_size=max_size
        )
        
        self.mapper.apply_properties(mock_widget, widget_def)
        
        mock_widget.setMinimumSize.assert_called_once_with(100, 50)
        mock_widget.setMaximumSize.assert_called_once_with(500, 300)
    
    def test_apply_widget_specific_properties(self):
        """Test applying widget-specific properties."""
        mock_widget = Mock()
        mock_widget.setText = Mock()
        mock_widget.setChecked = Mock()
        
        widget_def = Widget(
            name="test_widget",
            type=WidgetType.PUSH_BUTTON,
            parent=None,
            properties={
                'text': 'Click me',
                'checked': True
            }
        )
        
        self.mapper.apply_properties(mock_widget, widget_def)
        
        mock_widget.setText.assert_called_once_with('Click me')
        mock_widget.setChecked.assert_called_once_with(True)
    
    def test_extract_properties(self):
        """Test extracting properties from Qt widget."""
        mock_widget = Mock()
        mock_widget.isVisible.return_value = True
        mock_widget.isEnabled.return_value = True
        mock_widget.toolTip.return_value = "Test tooltip"
        mock_widget.styleSheet.return_value = "color: blue;"
        
        # Mock geometry
        mock_geom = Mock()
        mock_geom.x.return_value = 5
        mock_geom.y.return_value = 10
        mock_geom.width.return_value = 250
        mock_geom.height.return_value = 150
        mock_widget.geometry.return_value = mock_geom
        
        # Mock minimum size
        mock_min_size = Mock()
        mock_min_size.width.return_value = 50
        mock_min_size.height.return_value = 25
        mock_widget.minimumSize.return_value = mock_min_size
        
        # Mock maximum size (use Qt's max values to indicate no constraint)
        mock_max_size = Mock()
        mock_max_size.width.return_value = 16777215
        mock_max_size.height.return_value = 16777215
        mock_widget.maximumSize.return_value = mock_max_size
        
        properties = self.mapper.extract_properties(mock_widget)
        
        assert properties['visible'] == True
        assert properties['enabled'] == True
        assert properties['tooltip'] == "Test tooltip"
        assert properties['style_sheet'] == "color: blue;"
        assert properties['geometry'] == {'x': 5, 'y': 10, 'width': 250, 'height': 150}
        assert properties['minimum_size'] == {'width': 50, 'height': 25}
        assert 'maximum_size' not in properties  # Should be excluded for Qt max values


class TestUIRenderer:
    """Test UI renderer functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.renderer = UIRenderer()
    
    @patch('headless.mode_manager.is_dev_mode', return_value=True)
    def test_render_ui_in_dev_mode_raises_error(self, mock_dev_mode):
        """Test that UI rendering fails in dev mode."""
        ui_def = UI(
            widgets=[],
            layouts=[],
            events=[],
            metadata={}
        )
        
        from headless.rendering.ui_renderer import UIRenderingError
        with pytest.raises(UIRenderingError, match="Cannot render UI in development mode"):
            self.renderer.render_ui(ui_def)
    
    def test_find_root_widget(self):
        """Test finding root widget from widget list."""
        widgets = [
            Widget(name="child1", type=WidgetType.WIDGET, parent="root"),
            Widget(name="root", type=WidgetType.WIDGET, parent=None),
            Widget(name="child2", type=WidgetType.WIDGET, parent="root")
        ]
        
        root = self.renderer._find_root_widget(widgets)
        
        assert root is not None
        assert root.name == "root"
        assert root.parent is None
    
    def test_find_root_widget_no_root(self):
        """Test finding root widget when none exists."""
        widgets = [
            Widget(name="child1", type=WidgetType.WIDGET, parent="nonexistent"),
            Widget(name="child2", type=WidgetType.WIDGET, parent="nonexistent")
        ]
        
        root = self.renderer._find_root_widget(widgets)
        
        assert root is None
    
    @patch('headless.mode_manager.is_dev_mode', return_value=False)
    def test_render_simple_ui(self, mock_dev_mode):
        """Test rendering simple UI with one widget."""
        with patch.object(self.renderer.widget_factory, 'create_widget') as mock_create, \
             patch.object(self.renderer.property_mapper, 'apply_properties') as mock_apply:
            
            mock_qt_widget = Mock()
            mock_create.return_value = mock_qt_widget
            
            widgets = [
                Widget(name="root", type=WidgetType.WIDGET, parent=None)
            ]
            
            ui_def = UI(
                widgets=widgets,
                layouts=[],
                events=[],
                metadata={'name': 'test_ui'}
            )
            
            result = self.renderer.render_ui(ui_def)
            
            assert result == mock_qt_widget
            mock_create.assert_called_once()
            mock_apply.assert_called_once()
            assert self.renderer.get_rendered_widget("root") == mock_qt_widget
    
    def test_get_rendered_widget(self):
        """Test getting rendered widget by name."""
        mock_widget = Mock()
        self.renderer._rendered_widgets["test"] = mock_widget
        
        result = self.renderer.get_rendered_widget("test")
        assert result == mock_widget
        
        result = self.renderer.get_rendered_widget("nonexistent")
        assert result is None


if __name__ == '__main__':
    pytest.main([__file__]) 