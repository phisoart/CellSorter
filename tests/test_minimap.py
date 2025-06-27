"""
Tests for Minimap Navigation Widget
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from PySide6.QtCore import Qt, QRect, QSize, QPoint
from PySide6.QtGui import QImage, QColor
from PySide6.QtTest import QTest

from src.components.widgets.minimap import MinimapWidget


@pytest.fixture
def minimap_widget(qtbot):
    """Create a minimap widget for testing."""
    widget = MinimapWidget()
    qtbot.addWidget(widget)
    return widget


@pytest.fixture
def test_image():
    """Create a test image."""
    image = QImage(800, 600, QImage.Format_RGB888)
    image.fill(QColor(100, 100, 100))
    return image


class TestMinimapWidget:
    """Test suite for MinimapWidget."""
    
    def test_initialization(self, minimap_widget):
        """Test widget initialization."""
        assert minimap_widget.minimap_size == QSize(200, 150)
        assert minimap_widget.full_image is None
        assert minimap_widget.thumbnail is None
        assert minimap_widget.viewport_rect.isEmpty()
        assert minimap_widget.scale_factor == 1.0
    
    def test_set_image(self, minimap_widget, test_image):
        """Test setting an image."""
        minimap_widget.set_image(test_image)
        
        assert minimap_widget.full_image is not None
        assert minimap_widget.thumbnail is not None
        assert not minimap_widget.image_rect.isEmpty()
        assert minimap_widget.scale_factor < 1.0
    
    def test_set_null_image(self, minimap_widget):
        """Test setting a null image."""
        null_image = QImage()
        minimap_widget.set_image(null_image)
        
        assert minimap_widget.full_image is None
        assert minimap_widget.thumbnail is None
    
    def test_update_viewport(self, minimap_widget, test_image):
        """Test viewport update."""
        minimap_widget.set_image(test_image)
        
        # Set viewport to upper left quarter
        viewport = QRect(0, 0, 400, 300)
        minimap_widget.update_viewport(viewport, QSize(800, 600))
        
        assert not minimap_widget.viewport_rect.isEmpty()
        assert minimap_widget.viewport_rect.width() < minimap_widget.image_rect.width()
        assert minimap_widget.viewport_rect.height() < minimap_widget.image_rect.height()
    
    def test_navigation_signal(self, minimap_widget, test_image, qtbot):
        """Test navigation signal emission."""
        minimap_widget.set_image(test_image)
        
        # Set up signal spy
        with qtbot.waitSignal(minimap_widget.navigation_requested) as blocker:
            # Click in the center of the minimap
            center = minimap_widget.image_rect.center()
            QTest.mouseClick(minimap_widget, Qt.LeftButton, pos=center)
        
        # Check signal was emitted with normalized coordinates
        assert len(blocker.args) == 2
        norm_x, norm_y = blocker.args
        assert 0.0 <= norm_x <= 1.0
        assert 0.0 <= norm_y <= 1.0
    
    def test_drag_navigation(self, minimap_widget, test_image, qtbot):
        """Test drag navigation in viewport."""
        minimap_widget.set_image(test_image)
        
        # Set initial viewport
        viewport = QRect(50, 50, 100, 75)
        minimap_widget.update_viewport(viewport, QSize(800, 600))
        
        # Start drag from viewport center
        start_pos = minimap_widget.viewport_rect.center()
        
        # Simulate drag
        QTest.mousePress(minimap_widget, Qt.LeftButton, pos=start_pos)
        assert minimap_widget.is_dragging
        
        # Move mouse
        end_pos = start_pos + QPoint(20, 20)
        QTest.mouseMove(minimap_widget, pos=end_pos)
        
        # Release
        QTest.mouseRelease(minimap_widget, Qt.LeftButton, pos=end_pos)
        assert not minimap_widget.is_dragging
    
    def test_viewport_constraints(self, minimap_widget, test_image):
        """Test viewport stays within image bounds."""
        minimap_widget.set_image(test_image)
        
        # Try to set viewport outside image bounds
        oversized_viewport = QRect(-100, -100, 1000, 1000)
        minimap_widget.update_viewport(oversized_viewport, QSize(800, 600))
        
        # Check viewport is constrained
        assert minimap_widget.viewport_rect.left() >= minimap_widget.image_rect.left()
        assert minimap_widget.viewport_rect.top() >= minimap_widget.image_rect.top()
        assert minimap_widget.viewport_rect.right() <= minimap_widget.image_rect.right()
        assert minimap_widget.viewport_rect.bottom() <= minimap_widget.image_rect.bottom()
    
    def test_minimap_resize(self, minimap_widget, test_image):
        """Test changing minimap size."""
        minimap_widget.set_image(test_image)
        old_scale = minimap_widget.scale_factor
        
        # Resize minimap
        new_size = QSize(300, 200)
        minimap_widget.set_minimap_size(new_size)
        
        assert minimap_widget.size() == new_size
        assert minimap_widget.scale_factor != old_scale
    
    def test_cursor_changes(self, minimap_widget, test_image):
        """Test cursor changes based on mouse position."""
        minimap_widget.set_image(test_image)
        
        # Set viewport
        viewport = QRect(50, 50, 100, 75)
        minimap_widget.update_viewport(viewport, QSize(800, 600))
        
        # Move over viewport - should show open hand
        QTest.mouseMove(minimap_widget, pos=minimap_widget.viewport_rect.center())
        assert minimap_widget.cursor().shape() == Qt.OpenHandCursor
        
        # Move over image (not viewport) - should show pointing hand
        image_pos = minimap_widget.image_rect.topLeft() + QPoint(10, 10)
        QTest.mouseMove(minimap_widget, pos=image_pos)
        assert minimap_widget.cursor().shape() == Qt.PointingHandCursor
        
        # Move outside image - should show arrow
        outside_pos = QPoint(0, 0)
        QTest.mouseMove(minimap_widget, pos=outside_pos)
        assert minimap_widget.cursor().shape() == Qt.ArrowCursor
    
    def test_set_zero_sized_image(self, minimap_widget):
        """width 또는 height가 0인 이미지를 set_image에 전달할 때 안전하게 동작하는지 테스트"""
        # width=0, height>0
        zero_width_image = QImage(0, 100, QImage.Format_RGB888)
        minimap_widget.set_image(zero_width_image)
        assert minimap_widget.full_image is None
        assert minimap_widget.thumbnail is None

        # width>0, height=0
        zero_height_image = QImage(100, 0, QImage.Format_RGB888)
        minimap_widget.set_image(zero_height_image)
        assert minimap_widget.full_image is None
        assert minimap_widget.thumbnail is None

        # width=0, height=0
        zero_both_image = QImage(0, 0, QImage.Format_RGB888)
        minimap_widget.set_image(zero_both_image)
        assert minimap_widget.full_image is None
        assert minimap_widget.thumbnail is None 