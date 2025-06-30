"""
Widget Factory for Headless UI Rendering

Creates Qt widgets for the headless UI system.
Handles widget instantiation with proper parent-child relationships.
"""

from typing import Optional, Dict, Any, Type
import importlib

try:
    from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QLabel, QPushButton
    from PySide6.QtCore import QObject
except ImportError:
    # Headless fallback
    QWidget = object
    QVBoxLayout = object
    QHBoxLayout = object
    QSplitter = object
    QLabel = object
    QPushButton = object
    QObject = object

from utils.logging_config import LoggerMixin


class WidgetFactory(LoggerMixin):
    """Factory for creating UI widgets in headless mode."""
    
    def __init__(self):
        super().__init__()
        self.widget_cache: Dict[str, Type] = {}
    
    def create_widget(self, widget_type: str, parent: Optional[QWidget] = None, **kwargs) -> QWidget:
        """
        Create a widget of the specified type.
        
        Args:
            widget_type: Type of widget to create
            parent: Parent widget
            **kwargs: Additional arguments for widget creation
            
        Returns:
            Created widget instance
        """
        try:
            if widget_type == "MainWindow":
                return self._create_main_window(parent, **kwargs)
            elif widget_type == "ScatterPlotWidget":
                return self._create_scatter_plot(parent, **kwargs)
            elif widget_type == "ImageHandler":
                return self._create_image_handler(parent, **kwargs)
            elif widget_type == "SelectionPanel":
                return self._create_selection_panel(parent, **kwargs)
            elif widget_type == "WellPlateWidget":
                return self._create_well_plate(parent, **kwargs)
            elif widget_type == "MinimapWidget":
                return self._create_minimap(parent, **kwargs)
            # DEPRECATED: ExpressionFilter widget removed
            elif widget_type == "ExpressionFilter":
                self.log_warning("ExpressionFilter widget is deprecated and not available")
                return QWidget(parent) if parent else QWidget()
            else:
                self.log_warning(f"Unknown widget type: {widget_type}")
                return QWidget(parent) if parent else QWidget()
                
        except Exception as e:
            self.log_error(f"Failed to create widget {widget_type}: {e}")
            # Return placeholder widget
            return QWidget(parent) if parent else QWidget()
    
    def _create_main_window(self, parent: Optional[QWidget] = None, **kwargs) -> QWidget:
        """Create main window widget."""
        try:
            from pages.main_window import MainWindow
            from services.theme_manager import ThemeManager
            from PySide6.QtWidgets import QApplication
            # theme_manager 우선순위: kwargs > 기존 인스턴스 > 새로 생성
            theme_manager = kwargs.pop('theme_manager', None)
            if theme_manager is None:
                app = QApplication.instance()
                if app is None:
                    # Headless fallback: QApplication이 없으면 생성 시도
                    try:
                        from PySide6.QtWidgets import QApplication
                        import sys
                        app = QApplication(sys.argv)
                    except Exception:
                        app = None
                if app is not None:
                    theme_manager = ThemeManager(app)
                else:
                    # 완전 headless fallback: ThemeManager 없이 생성 시도
                    return MainWindow(None, None, parent)
            update_checker = kwargs.pop('update_checker', None)
            # MainWindow(theme_manager, update_checker=None, parent=None)
            return MainWindow(theme_manager, update_checker, parent)
        except ImportError as e:
            self.log_warning(f"MainWindow not available: {e}, using QWidget placeholder")
            return QWidget(parent) if parent else QWidget()
        except Exception as e:
            self.log_error(f"Failed to instantiate MainWindow: {e}")
            return QWidget(parent) if parent else QWidget()
    
    def _create_scatter_plot(self, parent: Optional[QWidget] = None, **kwargs) -> QWidget:
        """Create scatter plot widget."""
        try:
            from components.widgets.scatter_plot import ScatterPlotWidget
            return ScatterPlotWidget(parent) if parent else ScatterPlotWidget()
        except ImportError as e:
            self.log_warning(f"ScatterPlotWidget not available: {e}, using QWidget placeholder")
            return QWidget(parent) if parent else QWidget()
    
    def _create_image_handler(self, parent: Optional[QWidget] = None, **kwargs) -> QWidget:
        """Create image handler widget."""
        try:
            from models.image_handler import ImageHandler
            return ImageHandler(parent) if parent else ImageHandler()
        except ImportError as e:
            self.log_warning(f"ImageHandler not available: {e}, using QWidget placeholder")
            return QWidget(parent) if parent else QWidget()
    
    def _create_selection_panel(self, parent: Optional[QWidget] = None, **kwargs) -> QWidget:
        """Create selection panel widget."""
        try:
            from components.widgets.selection_panel import SelectionPanel
            return SelectionPanel(parent) if parent else SelectionPanel()
        except ImportError as e:
            self.log_warning(f"SelectionPanel not available: {e}, using QWidget placeholder")
            return QWidget(parent) if parent else QWidget()
    
    def _create_well_plate(self, parent: Optional[QWidget] = None, **kwargs) -> QWidget:
        """Create well plate widget."""
        try:
            from components.widgets.well_plate import WellPlateWidget
            return WellPlateWidget(parent) if parent else WellPlateWidget()
        except ImportError as e:
            self.log_warning(f"WellPlateWidget not available: {e}, using QWidget placeholder")
            return QWidget(parent) if parent else QWidget()
    
    def _create_minimap(self, parent: Optional[QWidget] = None, **kwargs) -> QWidget:
        """Create minimap widget."""
        try:
            from components.widgets.minimap import MinimapWidget
            return MinimapWidget(parent) if parent else MinimapWidget()
        except ImportError as e:
            self.log_warning(f"MinimapWidget not available: {e}, using QWidget placeholder")
            return QWidget(parent) if parent else QWidget()
    
    # DEPRECATED METHODS - Marked for removal
    def _create_expression_filter(self, parent: Optional[QWidget] = None, **kwargs) -> QWidget:
        """DEPRECATED: Expression filter widget is no longer available."""
        self.log_warning("ExpressionFilter widget is deprecated and not available")
        return QWidget(parent) if parent else QWidget()
    
    def get_widget_types(self) -> list:
        """Get list of available widget types."""
        return [
            "MainWindow",
            "ScatterPlotWidget", 
            "ImageHandler",
            "SelectionPanel",
            "WellPlateWidget",
            "MinimapWidget"
            # "ExpressionFilter" - DEPRECATED
        ]
    
    def clear_cache(self) -> None:
        """Clear the widget cache."""
        self.widget_cache.clear()
        self.log_info("Widget cache cleared")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get widget cache statistics."""
        return {
            "cached_types": len(self.widget_cache),
            "total_widgets": sum(1 for _ in self.widget_cache.values())
        } 