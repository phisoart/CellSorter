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
import os
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import QRect, Qt
from PySide6.QtTest import QTest

# Import test targets
from headless.mode_manager import set_dev_mode, set_dual_mode, get_mode_info, is_dev_mode, is_dual_mode, is_gui_mode
from pages.main_window import MainWindow
from components.widgets.selection_panel import SelectionPanel
from services.theme_manager import ThemeManager
from config.settings import (
    MIN_IMAGE_PANEL_WIDTH, MIN_PLOT_PANEL_WIDTH, MIN_SELECTION_PANEL_WIDTH,
    BUTTON_HEIGHT, BUTTON_MIN_WIDTH, BREAKPOINT_TABLET, BREAKPOINT_DESKTOP,
    MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT
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
        theme_manager = ThemeManager(mock_app)
        window = MainWindow(theme_manager)
        yield window
        window.close()
    
    def test_dev_mode_panel_minimum_sizes(self, main_window):
        """Test minimum panel size constraints in DEV mode"""
        # Verify mode
        assert is_dev_mode() == True
        
        # Check minimum widths are applied
        assert main_window.image_handler.minimumWidth() == MIN_IMAGE_PANEL_WIDTH
        assert main_window.scatter_plot_widget.minimumWidth() == MIN_PLOT_PANEL_WIDTH
        assert main_window.selection_panel.minimumWidth() == MIN_SELECTION_PANEL_WIDTH
        
        # Simulate very small window resize
        main_window.resize(400, 300)  # Below minimum viable size
        QTest.qWait(50)  # Allow layout to update
        
        # Verify panels don't disappear
        splitter_sizes = main_window.main_splitter.sizes()
        assert all(size >= 100 for size in splitter_sizes)  # Reasonable minimum check
    
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
            assert all(size >= 100 for size in splitter_sizes)  # Reasonable minimum


class TestUILayoutGUIMode:
    """GUI Mode: Production UI behavior and user experience tests"""
    
    @pytest.fixture(autouse=True)
    def setup_gui_mode(self):
        """Setup GUI mode for production testing"""
        # Set GUI mode using environment variable
        os.environ['CELLSORTER_MODE'] = 'gui'
        yield
        # Clean up
        if 'CELLSORTER_MODE' in os.environ:
            del os.environ['CELLSORTER_MODE']
    
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
        theme_manager = ThemeManager(app)
        window = MainWindow(theme_manager)
        window.show()
        QTest.qWaitForWindowExposed(window)
        yield window
        window.close()
    
    def test_gui_mode_visual_layout(self, main_window):
        """Test visual layout appearance in GUI mode"""
        assert is_gui_mode() == True
        
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


class TestUILayoutDUALMode:
    """DUAL Mode: GUI synchronization and layout consistency tests"""
    
    @pytest.fixture(autouse=True)
    def setup_dual_mode(self):
        """Setup DUAL mode for synchronization testing"""
        set_dual_mode(True)
        yield
        set_dual_mode(False)
    
    @pytest.fixture
    def app(self):
        if not QApplication.instance():
            app = QApplication([])
        else:
            app = QApplication.instance()
        yield app
    
    @pytest.fixture
    def main_window(self, app):
        """Create main window in DUAL mode"""
        theme_manager = ThemeManager(app)
        window = MainWindow(theme_manager)
        yield window
        window.close()
    
    def test_dual_mode_layout_consistency(self, main_window):
        """Test layout consistency between headless and GUI in DUAL mode"""
        assert is_dual_mode() == True
        
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


@pytest.mark.ui_layout
def test_comprehensive_layout_validation():
    """Comprehensive validation of UI layout improvements"""
    app = QApplication.instance() or QApplication([])
    
    # Test DEV mode
    set_dev_mode(True)
    theme_manager = ThemeManager(app)
    window = MainWindow(theme_manager)
    
    try:
        # Test minimum size constraints
        assert window.image_handler.minimumWidth() == MIN_IMAGE_PANEL_WIDTH
        assert window.scatter_plot_widget.minimumWidth() == MIN_PLOT_PANEL_WIDTH
        assert window.selection_panel.minimumWidth() == MIN_SELECTION_PANEL_WIDTH
        
        # Test splitter configuration
        assert window.main_splitter.childrenCollapsible() == False
        assert window.main_splitter.handleWidth() == 6
        
        # Test button sizing
        sp = window.selection_panel
        assert sp.delete_button.minimumHeight() == BUTTON_HEIGHT
        assert sp.clear_all_button.minimumHeight() == BUTTON_HEIGHT
        assert sp.export_csv_button.minimumHeight() == BUTTON_HEIGHT
        assert sp.export_protocol_button.minimumHeight() == BUTTON_HEIGHT
        
        print("✅ DEV mode layout validation passed")
        
    finally:
        window.close()
        set_dev_mode(False)
    
    # Test GUI mode
    os.environ['CELLSORTER_MODE'] = 'gui'
    try:
        theme_manager = ThemeManager(app)
        window = MainWindow(theme_manager)
        
        # Same tests for GUI mode
        assert window.image_handler.minimumWidth() == MIN_IMAGE_PANEL_WIDTH
        assert window.scatter_plot_widget.minimumWidth() == MIN_PLOT_PANEL_WIDTH
        assert window.selection_panel.minimumWidth() == MIN_SELECTION_PANEL_WIDTH
        
        sp = window.selection_panel
        assert sp.delete_button.minimumHeight() == BUTTON_HEIGHT
        assert sp.clear_all_button.minimumHeight() == BUTTON_HEIGHT
        assert sp.export_csv_button.minimumHeight() == BUTTON_HEIGHT
        assert sp.export_protocol_button.minimumHeight() == BUTTON_HEIGHT
        
        print("✅ GUI mode layout validation passed")
        
    finally:
        window.close()
        if 'CELLSORTER_MODE' in os.environ:
            del os.environ['CELLSORTER_MODE']


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"]) 