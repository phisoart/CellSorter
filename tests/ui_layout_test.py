"""
UI Layout 3-Mode Tests

Tests for UI layout improvements including:
- Minimum panel size constraints
- Button layout and sizing
- Responsive layout behavior
- Component spacing and alignment
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import QRect, Qt
from PySide6.QtTest import QTest

# Import test targets
from headless.mode_manager import set_dev_mode, set_dual_mode, set_gui_mode, get_mode_info
from pages.main_window import MainWindow
from components.widgets.selection_panel import SelectionPanel
from services.theme_manager import ThemeManager
from config.settings import (
    MIN_IMAGE_PANEL_WIDTH, MIN_PLOT_PANEL_WIDTH, MIN_SELECTION_PANEL_WIDTH,
    BUTTON_HEIGHT, BUTTON_MIN_WIDTH, BREAKPOINT_TABLET, BREAKPOINT_DESKTOP
)


class TestUILayoutDEVMode:
    """DEV Mode: Headless UI layout simulation and validation tests"""
    
    @pytest.fixture(autouse=True)
    def setup_dev_mode(self):
        """Setup DEV mode for headless testing"""
        set_dev_mode(True)
        yield
        set_dev_mode(False)
    
    @pytest.fixture
    def mock_app(self):
        """Create mock QApplication for headless testing"""
        if not QApplication.instance():
            app = QApplication([])
        else:
            app = QApplication.instance()
        yield app
    
    @pytest.fixture
    def main_window(self, mock_app):
        """Create main window in DEV mode"""
        theme_manager = ThemeManager()
        window = MainWindow(theme_manager)
        yield window
        window.close()
    
    def test_dev_mode_panel_minimum_sizes(self, main_window):
        """Test minimum panel size constraints in DEV mode"""
        # Verify mode
        mode_info = get_mode_info()
        assert mode_info['current_mode'] == 'dev'
        assert mode_info['is_headless'] == True
        
        # Check minimum widths are applied
        assert main_window.image_handler.minimumWidth() == MIN_IMAGE_PANEL_WIDTH
        assert main_window.scatter_plot_widget.minimumWidth() == MIN_PLOT_PANEL_WIDTH
        assert main_window.selection_panel.minimumWidth() == MIN_SELECTION_PANEL_WIDTH
        
        # Simulate very small window resize
        main_window.resize(400, 300)  # Below minimum viable size
        QTest.qWait(50)  # Allow layout to update
        
        # Verify panels don't disappear
        splitter_sizes = main_window.main_splitter.sizes()
        assert all(size >= MIN_IMAGE_PANEL_WIDTH for size in splitter_sizes[:1])
        assert all(size >= MIN_PLOT_PANEL_WIDTH for size in splitter_sizes[1:2])
        assert all(size >= MIN_SELECTION_PANEL_WIDTH for size in splitter_sizes[2:])
    
    def test_dev_mode_button_layout_simulation(self, main_window):
        """Test button layout in selection panel for DEV mode"""
        selection_panel = main_window.selection_panel
        
        # Check button properties
        assert selection_panel.delete_button.minimumHeight() == BUTTON_HEIGHT
        assert selection_panel.delete_button.minimumWidth() == BUTTON_MIN_WIDTH
        assert selection_panel.clear_all_button.minimumHeight() == BUTTON_HEIGHT
        assert selection_panel.clear_all_button.minimumWidth() == BUTTON_MIN_WIDTH
        
        # Check export buttons
        assert selection_panel.export_csv_button.minimumHeight() == BUTTON_HEIGHT
        assert selection_panel.export_csv_button.minimumWidth() == BUTTON_MIN_WIDTH
        assert selection_panel.export_protocol_button.minimumHeight() == BUTTON_HEIGHT
        assert selection_panel.export_protocol_button.minimumWidth() >= 120
    
    def test_dev_mode_responsive_layout_simulation(self, main_window):
        """Test responsive layout behavior in DEV mode"""
        # Test different window sizes
        window_sizes = [
            (600, 400),   # Mobile-like
            (1000, 600),  # Tablet-like  
            (1400, 800),  # Desktop-like
        ]
        
        for width, height in window_sizes:
            main_window.resize(width, height)
            main_window.setup_responsive_layout()
            QTest.qWait(20)
            
            # Verify layout responds appropriately
            splitter_sizes = main_window.main_splitter.sizes()
            total_width = sum(splitter_sizes)
            
            # All panels should have reasonable sizes
            assert total_width > 0
            assert all(size >= 150 for size in splitter_sizes)  # Reasonable minimum
    
    def test_dev_mode_component_spacing(self, main_window):
        """Test component spacing and margins in DEV mode"""
        selection_panel = main_window.selection_panel
        
        # Check layout spacing
        layout = selection_panel.layout()
        assert layout.spacing() == 12  # COMPONENT_SPACING equivalent
        
        # Check margins
        margins = layout.contentsMargins()
        assert margins.left() == 8   # PANEL_MARGIN equivalent
        assert margins.right() == 8
        assert margins.top() == 8
        assert margins.bottom() == 8


class TestUILayoutDUALMode:
    """DUAL Mode: GUI synchronization and layout consistency tests"""
    
    @pytest.fixture(autouse=True)
    def setup_dual_mode(self):
        """Setup DUAL mode for synchronization testing"""
        set_dual_mode(True)
        yield
        set_dual_mode(False)
    
    @pytest.fixture
    def mock_app(self):
        if not QApplication.instance():
            app = QApplication([])
        else:
            app = QApplication.instance()
        yield app
    
    @pytest.fixture
    def main_window(self, mock_app):
        """Create main window in DUAL mode"""
        theme_manager = ThemeManager()
        window = MainWindow(theme_manager)
        yield window
        window.close()
    
    def test_dual_mode_layout_consistency(self, main_window):
        """Test layout consistency between headless and GUI in DUAL mode"""
        mode_info = get_mode_info()
        assert mode_info['current_mode'] == 'dual'
        
        # Verify GUI elements exist and have proper configuration
        assert hasattr(main_window, 'main_splitter')
        assert main_window.main_splitter.childrenCollapsible() == False
        assert main_window.main_splitter.handleWidth() == 6
        
        # Test splitter behavior
        initial_sizes = main_window.main_splitter.sizes()
        
        # Simulate resizing panels
        new_sizes = [300, 400, 300]
        main_window.main_splitter.setSizes(new_sizes)
        QTest.qWait(50)
        
        current_sizes = main_window.main_splitter.sizes()
        # Verify sizes are applied but respect minimums
        for i, size in enumerate(current_sizes):
            min_sizes = [MIN_IMAGE_PANEL_WIDTH, MIN_PLOT_PANEL_WIDTH, MIN_SELECTION_PANEL_WIDTH]
            assert size >= min_sizes[i]
    
    def test_dual_mode_button_synchronization(self, main_window):
        """Test button state synchronization in DUAL mode"""
        selection_panel = main_window.selection_panel
        
        # Test button enablement/disablement synchronization
        initial_delete_state = selection_panel.delete_button.isEnabled()
        assert initial_delete_state == False  # Should start disabled
        
        # Simulate selection
        selection_panel.delete_button.setEnabled(True)
        assert selection_panel.delete_button.isEnabled() == True
        
        # Test style application
        button_style = selection_panel.delete_button.styleSheet()
        assert "var(--destructive)" in button_style
        assert "border-radius: 6px" in button_style
    
    def test_dual_mode_responsive_sync(self, main_window):
        """Test responsive layout synchronization in DUAL mode"""
        # Test window resize handling
        original_width = main_window.width()
        
        # Resize to tablet size
        main_window.resize(BREAKPOINT_TABLET - 100, 600)
        QTest.qWait(100)  # Allow resize event to process
        
        # Verify layout adapted
        current_sizes = main_window.main_splitter.sizes()
        assert all(size > 0 for size in current_sizes)
        
        # Resize to desktop size
        main_window.resize(BREAKPOINT_DESKTOP + 100, 800)
        QTest.qWait(100)
        
        new_sizes = main_window.main_splitter.sizes()
        assert all(size > 0 for size in new_sizes)


class TestUILayoutGUIMode:
    """GUI Mode: Production UI behavior and user experience tests"""
    
    @pytest.fixture(autouse=True)
    def setup_gui_mode(self):
        """Setup GUI mode for production testing"""
        set_gui_mode(True)
        yield
        set_gui_mode(False)
    
    @pytest.fixture
    def app(self):
        if not QApplication.instance():
            app = QApplication([])
        else:
            app = QApplication.instance()
        yield app
    
    @pytest.fixture
    def main_window(self, app):
        """Create main window in GUI mode"""
        theme_manager = ThemeManager()
        window = MainWindow(theme_manager)
        window.show()
        QTest.qWaitForWindowExposed(window)
        yield window
        window.close()
    
    def test_gui_mode_visual_layout(self, main_window):
        """Test visual layout appearance in GUI mode"""
        mode_info = get_mode_info()
        assert mode_info['current_mode'] == 'gui'
        assert mode_info['is_headless'] == False
        
        # Verify window is visible
        assert main_window.isVisible()
        assert main_window.width() >= MIN_WINDOW_WIDTH
        assert main_window.height() >= MIN_WINDOW_HEIGHT
        
        # Check panel visibility
        assert main_window.image_handler.isVisible()
        assert main_window.scatter_plot_widget.isVisible()
        assert main_window.selection_panel.isVisible()
    
    def test_gui_mode_button_interaction(self, main_window):
        """Test button click interactions in GUI mode"""
        selection_panel = main_window.selection_panel
        
        # Test button click simulation
        clear_button = selection_panel.clear_all_button
        assert clear_button.isVisible()
        assert clear_button.isEnabled()
        
        # Simulate button click
        QTest.mouseClick(clear_button, Qt.LeftButton)
        QTest.qWait(50)
        
        # Button should remain functional (no crash)
        assert clear_button.isEnabled()
    
    def test_gui_mode_panel_resizing(self, main_window):
        """Test interactive panel resizing in GUI mode"""
        splitter = main_window.main_splitter
        initial_sizes = splitter.sizes()
        
        # Simulate dragging splitter handle
        # This tests that the splitter handles are functional
        handle = splitter.handle(1)  # Between first and second panel
        assert handle is not None
        assert handle.isVisible()
        
        # Verify minimum size constraints are working
        # Try to set unreasonably small sizes
        splitter.setSizes([50, 50, 50])
        QTest.qWait(50)
        
        actual_sizes = splitter.sizes()
        assert actual_sizes[0] >= MIN_IMAGE_PANEL_WIDTH
        assert actual_sizes[1] >= MIN_PLOT_PANEL_WIDTH  
        assert actual_sizes[2] >= MIN_SELECTION_PANEL_WIDTH
    
    def test_gui_mode_theme_integration(self, main_window):
        """Test theme integration with UI layout in GUI mode"""
        selection_panel = main_window.selection_panel
        
        # Check that CSS variables are applied correctly
        delete_button = selection_panel.delete_button
        style = delete_button.styleSheet()
        
        # Verify design system colors are used
        assert "var(--destructive)" in style
        assert "var(--destructive-foreground)" in style
        
        export_button = selection_panel.export_csv_button
        export_style = export_button.styleSheet()
        assert "var(--primary)" in export_style
        assert "var(--primary-foreground)" in export_style


@pytest.mark.ui_layout
class TestUILayoutIntegration:
    """Integration tests for UI layout across all modes"""
    
    def test_layout_mode_switching(self):
        """Test layout consistency when switching between modes"""
        app = QApplication.instance() or QApplication([])
        theme_manager = ThemeManager()
        
        # Test DEV mode
        set_dev_mode(True)
        dev_window = MainWindow(theme_manager)
        dev_sizes = dev_window.main_splitter.sizes()
        dev_window.close()
        set_dev_mode(False)
        
        # Test GUI mode  
        set_gui_mode(True)
        gui_window = MainWindow(theme_manager)
        gui_sizes = gui_window.main_splitter.sizes()
        gui_window.close()
        set_gui_mode(False)
        
        # Layouts should be consistent
        assert len(dev_sizes) == len(gui_sizes) == 3
        
        # All panels should respect minimum sizes in both modes
        for i, (dev_size, gui_size) in enumerate(zip(dev_sizes, gui_sizes)):
            min_sizes = [MIN_IMAGE_PANEL_WIDTH, MIN_PLOT_PANEL_WIDTH, MIN_SELECTION_PANEL_WIDTH]
            assert dev_size >= min_sizes[i]
            assert gui_size >= min_sizes[i]
    
    def test_button_consistency_across_modes(self):
        """Test button layout consistency across all modes"""
        app = QApplication.instance() or QApplication([])
        theme_manager = ThemeManager()
        
        modes = ['dev', 'dual', 'gui']
        button_properties = []
        
        for mode in modes:
            if mode == 'dev':
                set_dev_mode(True)
            elif mode == 'dual':
                set_dual_mode(True) 
            else:
                set_gui_mode(True)
            
            window = MainWindow(theme_manager)
            selection_panel = window.selection_panel
            
            # Collect button properties
            props = {
                'delete_height': selection_panel.delete_button.minimumHeight(),
                'delete_width': selection_panel.delete_button.minimumWidth(),
                'export_height': selection_panel.export_csv_button.minimumHeight(),
                'export_width': selection_panel.export_csv_button.minimumWidth(),
            }
            button_properties.append(props)
            
            window.close()
            
            # Reset mode
            set_dev_mode(False)
            set_dual_mode(False)
            set_gui_mode(False)
        
        # All modes should have consistent button sizing
        for prop_name in button_properties[0].keys():
            values = [props[prop_name] for props in button_properties]
            assert all(v == values[0] for v in values), f"Inconsistent {prop_name}: {values}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"]) 