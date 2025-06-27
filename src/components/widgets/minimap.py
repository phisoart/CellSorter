"""
Minimap Navigation Widget for CellSorter

This module provides a miniature overview of the full image with navigation capabilities,
enabling quick navigation in large microscopy images.
"""

from typing import Optional, Tuple
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PySide6.QtCore import Qt, Signal, QRect, QPoint, QSize
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QImage, QPixmap, QMouseEvent

from utils.logging_config import LoggerMixin


class MinimapWidget(QWidget, LoggerMixin):
    """
    Minimap widget for large image navigation.
    
    Features:
    - Miniature view of full image
    - Navigation rectangle overlay showing current viewport
    - Click-to-navigate functionality
    - Drag navigation support
    - Performance optimization for large images
    """
    
    # Signals
    navigation_requested = Signal(float, float)  # Normalized x, y coordinates (0-1)
    viewport_changed = Signal(QRect)  # New viewport rectangle
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configuration
        self.minimap_size = QSize(200, 150)  # Default minimap size
        self.border_color = QColor(100, 100, 100)
        self.viewport_color = QColor(50, 150, 250, 100)
        self.viewport_border_color = QColor(50, 150, 250)
        self.background_color = QColor(240, 240, 240)
        
        # State
        self.full_image: Optional[QImage] = None
        self.thumbnail: Optional[QPixmap] = None
        self.viewport_rect = QRect()  # Current viewport in minimap coordinates
        self.image_rect = QRect()  # Full image bounds in minimap coordinates
        self.scale_factor = 1.0
        
        # Interaction state
        self.is_dragging = False
        self.drag_start_pos = QPoint()
        self.drag_start_viewport = QRect()
        
        # Setup UI
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Initialize the UI."""
        self.setFixedSize(self.minimap_size)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setMouseTracking(True)
        self.setCursor(Qt.PointingHandCursor)
        
        # Set widget style
        self.setStyleSheet("""
            MinimapWidget {
                border: 1px solid #646464;
                border-radius: 4px;
                background-color: #f0f0f0;
            }
        """)
    
    def set_image(self, image: QImage) -> None:
        """
        Set the full image for minimap display.
        
        Args:
            image: Full resolution image
        """
        if image.isNull():
            self.full_image = None
            self.thumbnail = None
            self.update()
            return
        
        self.full_image = image
        
        # Create thumbnail maintaining aspect ratio
        thumbnail_size = self.minimap_size - QSize(4, 4)  # Account for border
        scaled_image = image.scaled(
            thumbnail_size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        
        self.thumbnail = QPixmap.fromImage(scaled_image)
        
        # Calculate image rect within minimap
        x = (self.width() - self.thumbnail.width()) // 2
        y = (self.height() - self.thumbnail.height()) // 2
        self.image_rect = QRect(x, y, self.thumbnail.width(), self.thumbnail.height())
        
        # Calculate scale factor
        self.scale_factor = min(
            self.thumbnail.width() / image.width(),
            self.thumbnail.height() / image.height()
        )
        
        self.update()
        self.log_info(f"Minimap image set: {image.width()}x{image.height()} -> {self.thumbnail.width()}x{self.thumbnail.height()}")
    
    def update_viewport(self, viewport_rect: QRect, image_size: QSize) -> None:
        """
        Update the current viewport rectangle.
        
        Args:
            viewport_rect: Current viewport in image coordinates
            image_size: Full image size
        """
        if not self.thumbnail or image_size.isEmpty():
            return
        
        # Convert viewport to minimap coordinates
        x = int(viewport_rect.x() * self.scale_factor) + self.image_rect.x()
        y = int(viewport_rect.y() * self.scale_factor) + self.image_rect.y()
        width = int(viewport_rect.width() * self.scale_factor)
        height = int(viewport_rect.height() * self.scale_factor)
        
        # Ensure viewport stays within image bounds
        x = max(self.image_rect.x(), min(x, self.image_rect.right() - width))
        y = max(self.image_rect.y(), min(y, self.image_rect.bottom() - height))
        
        self.viewport_rect = QRect(x, y, width, height)
        self.update()
    
    def set_minimap_size(self, size: QSize) -> None:
        """
        Set the minimap widget size.
        
        Args:
            size: New minimap size
        """
        self.minimap_size = size
        self.setFixedSize(size)
        
        # Re-generate thumbnail if image is set
        if self.full_image:
            self.set_image(self.full_image)
    
    def paintEvent(self, event) -> None:
        """Paint the minimap."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background
        painter.fillRect(self.rect(), self.background_color)
        
        # Draw thumbnail
        if self.thumbnail:
            painter.drawPixmap(self.image_rect, self.thumbnail)
            
            # Draw image border
            painter.setPen(QPen(self.border_color, 1))
            painter.drawRect(self.image_rect.adjusted(0, 0, -1, -1))
            
            # Draw viewport rectangle
            if not self.viewport_rect.isEmpty():
                # Fill
                painter.fillRect(self.viewport_rect, self.viewport_color)
                
                # Border
                painter.setPen(QPen(self.viewport_border_color, 2))
                painter.drawRect(self.viewport_rect)
        else:
            # Draw placeholder text
            painter.setPen(QPen(self.border_color))
            painter.drawText(self.rect(), Qt.AlignCenter, "No Image")
    
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press events."""
        if event.button() == Qt.LeftButton and self.thumbnail:
            pos = event.pos()
            
            # Check if clicking inside viewport
            if self.viewport_rect.contains(pos):
                # Start dragging
                self.is_dragging = True
                self.drag_start_pos = pos
                self.drag_start_viewport = QRect(self.viewport_rect)
                self.setCursor(Qt.ClosedHandCursor)
            elif self.image_rect.contains(pos):
                # Navigate to clicked position
                self._navigate_to_position(pos)
    
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse move events."""
        if self.is_dragging and event.buttons() & Qt.LeftButton:
            # Calculate drag delta
            delta = event.pos() - self.drag_start_pos
            
            # Move viewport
            new_rect = self.drag_start_viewport.translated(delta)
            
            # Constrain to image bounds
            new_rect = self._constrain_viewport_to_image(new_rect)
            
            if new_rect != self.viewport_rect:
                self.viewport_rect = new_rect
                self.update()
                
                # Emit navigation signal
                self._emit_navigation_from_viewport()
        else:
            # Update cursor based on position
            if self.viewport_rect.contains(event.pos()):
                self.setCursor(Qt.OpenHandCursor)
            elif self.image_rect.contains(event.pos()):
                self.setCursor(Qt.PointingHandCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
    
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle mouse release events."""
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
            
            # Restore cursor
            if self.viewport_rect.contains(event.pos()):
                self.setCursor(Qt.OpenHandCursor)
            else:
                self.setCursor(Qt.PointingHandCursor)
    
    def wheelEvent(self, event) -> None:
        """Handle wheel events for zooming."""
        # Pass wheel events to parent (main image view)
        event.ignore()
    
    def _navigate_to_position(self, pos: QPoint) -> None:
        """
        Navigate to the clicked position.
        
        Args:
            pos: Click position in minimap coordinates
        """
        if not self.image_rect.contains(pos):
            return
        
        # Center viewport on clicked position
        viewport_center = QPoint(
            pos.x() - self.viewport_rect.width() // 2,
            pos.y() - self.viewport_rect.height() // 2
        )
        
        # Create new viewport rect
        new_rect = QRect(
            viewport_center.x(),
            viewport_center.y(),
            self.viewport_rect.width(),
            self.viewport_rect.height()
        )
        
        # Constrain to image bounds
        new_rect = self._constrain_viewport_to_image(new_rect)
        
        if new_rect != self.viewport_rect:
            self.viewport_rect = new_rect
            self.update()
            
            # Emit navigation signal
            self._emit_navigation_from_viewport()
    
    def _constrain_viewport_to_image(self, viewport: QRect) -> QRect:
        """
        Constrain viewport rectangle to image bounds.
        
        Args:
            viewport: Viewport rectangle to constrain
        
        Returns:
            Constrained viewport rectangle
        """
        # Ensure viewport stays within image bounds
        x = max(self.image_rect.x(), 
                min(viewport.x(), self.image_rect.right() - viewport.width()))
        y = max(self.image_rect.y(), 
                min(viewport.y(), self.image_rect.bottom() - viewport.height()))
        
        return QRect(x, y, viewport.width(), viewport.height())
    
    def _emit_navigation_from_viewport(self) -> None:
        """Emit navigation signal based on current viewport position."""
        if not self.thumbnail or self.viewport_rect.isEmpty():
            return
        
        # Calculate normalized position (0-1) of viewport center
        center_x = self.viewport_rect.center().x() - self.image_rect.x()
        center_y = self.viewport_rect.center().y() - self.image_rect.y()
        
        # Prevent division by zero
        if self.image_rect.width() <= 0 or self.image_rect.height() <= 0:
            self.log_warning("Cannot calculate navigation: invalid image dimensions")
            return
            
        norm_x = center_x / self.image_rect.width()
        norm_y = center_y / self.image_rect.height()
        
        # Clamp to valid range
        norm_x = max(0.0, min(1.0, norm_x))
        norm_y = max(0.0, min(1.0, norm_y))
        
        self.navigation_requested.emit(norm_x, norm_y)
    
    def get_viewport_in_image_coords(self) -> QRect:
        """
        Get current viewport in original image coordinates.
        
        Returns:
            Viewport rectangle in image coordinates
        """
        if not self.thumbnail or self.viewport_rect.isEmpty():
            return QRect()
        
        # Convert from minimap to image coordinates
        x = int((self.viewport_rect.x() - self.image_rect.x()) / self.scale_factor)
        y = int((self.viewport_rect.y() - self.image_rect.y()) / self.scale_factor)
        width = int(self.viewport_rect.width() / self.scale_factor)
        height = int(self.viewport_rect.height() / self.scale_factor)
        
        return QRect(x, y, width, height) 