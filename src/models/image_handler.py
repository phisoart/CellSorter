"""
CellSorter Image Handler

This module handles loading, processing, and displaying microscopy images
with support for multiple formats (TIFF, JPG, JPEG, PNG) and large files.
"""

import time
from typing import Optional, Tuple, List, Dict, Any
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageFile
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QProgressBar
from PySide6.QtCore import Qt, Signal, QThread, QObject, QTimer
from PySide6.QtGui import QPixmap, QImage, QPainter, QPen, QBrush

from config.settings import (
    SUPPORTED_IMAGE_FORMATS, MAX_IMAGE_SIZE_MB, COORDINATE_ACCURACY_MICROMETERS
)
from utils.exceptions import ImageLoadError, MemoryError, PerformanceError
from utils.error_handler import error_handler
from utils.logging_config import LoggerMixin

# Enable loading of large images
ImageFile.LOAD_TRUNCATED_IMAGES = True


class ImageLoadWorker(QObject, LoggerMixin):
    """
    Worker thread for loading large images without blocking the UI.
    """
    
    # Signals
    progress_updated = Signal(int)  # percentage
    loading_finished = Signal(np.ndarray, dict)  # image_data, metadata
    loading_failed = Signal(str)  # error_message
    
    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path
        self.is_cancelled = False
    
    def cancel(self) -> None:
        """Cancel the loading operation."""
        self.is_cancelled = True
    
    @error_handler("Loading image")
    def load_image(self) -> None:
        """Load image in worker thread."""
        try:
            start_time = time.time()
            file_path = Path(self.file_path)
            
            # Validate file
            if not file_path.exists():
                raise ImageLoadError(f"File not found: {file_path}")
            
            if file_path.suffix.lower() not in SUPPORTED_IMAGE_FORMATS:
                raise ImageLoadError(f"Unsupported format: {file_path.suffix}")
            
            # Check file size
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            if file_size_mb > MAX_IMAGE_SIZE_MB:
                raise ImageLoadError(f"File too large: {file_size_mb:.1f}MB > {MAX_IMAGE_SIZE_MB}MB")
            
            self.progress_updated.emit(10)
            
            if self.is_cancelled:
                return
            
            # Load image based on format
            if file_path.suffix.lower() in ['.tiff', '.tif']:
                image_data, metadata = self._load_tiff(file_path)
            else:
                image_data, metadata = self._load_standard_format(file_path)
            
            self.progress_updated.emit(90)
            
            if self.is_cancelled:
                return
            
            # Validate loading performance
            load_time = time.time() - start_time
            target_time = 5.0  # 5 seconds for 500MB
            adjusted_target = target_time * (file_size_mb / 500)
            
            if load_time > adjusted_target:
                self.log_warning(f"Image loading took {load_time:.2f}s, target was {adjusted_target:.2f}s")
            
            # Add timing metadata
            metadata.update({
                'load_time_seconds': load_time,
                'file_size_mb': file_size_mb,
                'performance_target_met': load_time <= adjusted_target
            })
            
            self.progress_updated.emit(100)
            self.loading_finished.emit(image_data, metadata)
            
            self.log_info(f"Image loaded successfully: {file_path.name} "
                         f"({file_size_mb:.1f}MB, {load_time:.2f}s)")
            
        except Exception as e:
            self.log_error(f"Failed to load image {self.file_path}: {e}")
            self.loading_failed.emit(str(e))
    
    def _load_tiff(self, file_path: Path) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Load TIFF image with support for multi-channel and large files.
        
        Args:
            file_path: Path to TIFF file
        
        Returns:
            Tuple of (image_data, metadata)
        """
        try:
            # Try OpenCV first for standard TIFF files
            image = cv2.imread(str(file_path), cv2.IMREAD_UNCHANGED)
            
            if image is not None:
                self.progress_updated.emit(50)
                
                # Convert BGR to RGB if color image
                if len(image.shape) == 3 and image.shape[2] == 3:
                    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                
                metadata = {
                    'format': 'TIFF',
                    'shape': image.shape,
                    'dtype': str(image.dtype),
                    'channels': 1 if len(image.shape) == 2 else image.shape[2],
                    'bit_depth': image.dtype.itemsize * 8,
                    'loader': 'opencv'
                }
                
                return image, metadata
            
            # Fallback to PIL for complex TIFF files
            self.progress_updated.emit(30)
            
            with Image.open(file_path) as pil_image:
                # Handle multi-frame TIFF (take first frame)
                if hasattr(pil_image, 'n_frames') and pil_image.n_frames > 1:
                    self.log_info(f"Multi-frame TIFF detected: {pil_image.n_frames} frames, using first frame")
                    pil_image.seek(0)
                
                self.progress_updated.emit(60)
                
                # Convert to numpy array
                image = np.array(pil_image)
                
                metadata = {
                    'format': 'TIFF',
                    'shape': image.shape,
                    'dtype': str(image.dtype),
                    'channels': 1 if len(image.shape) == 2 else image.shape[2],
                    'mode': pil_image.mode,
                    'frames': getattr(pil_image, 'n_frames', 1),
                    'loader': 'pillow'
                }
                
                return image, metadata
                
        except Exception as e:
            raise ImageLoadError(f"Failed to load TIFF file: {e}")
    
    def _load_standard_format(self, file_path: Path) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Load standard format images (JPG, JPEG, PNG).
        
        Args:
            file_path: Path to image file
        
        Returns:
            Tuple of (image_data, metadata)
        """
        try:
            # Use OpenCV for standard formats
            image = cv2.imread(str(file_path), cv2.IMREAD_UNCHANGED)
            
            if image is None:
                raise ImageLoadError(f"Failed to load image: {file_path}")
            
            self.progress_updated.emit(50)
            
            # Convert BGR to RGB for color images
            if len(image.shape) == 3 and image.shape[2] == 3:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            metadata = {
                'format': file_path.suffix.upper().lstrip('.'),
                'shape': image.shape,
                'dtype': str(image.dtype),
                'channels': 1 if len(image.shape) == 2 else image.shape[2],
                'bit_depth': image.dtype.itemsize * 8,
                'loader': 'opencv'
            }
            
            return image, metadata
            
        except Exception as e:
            raise ImageLoadError(f"Failed to load {file_path.suffix} file: {e}")


class ImageHandler(QWidget, LoggerMixin):
    """
    Image handler for loading, displaying, and managing microscopy images.
    
    Features:
    - Multi-format support (TIFF, JPG, JPEG, PNG)
    - Large file handling (up to 2GB)
    - Progressive loading with progress indication
    - Memory-efficient image display
    - Zoom and pan functionality
    - Overlay support for cell highlighting
    """
    
    # Signals
    image_loaded = Signal(str)  # file_path
    image_load_failed = Signal(str)  # error_message
    zoom_changed = Signal(float)  # zoom_level
    coordinates_changed = Signal(float, float)  # x, y
    calibration_point_clicked = Signal(int, int, str)  # x, y, label
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # State
        self.image_data: Optional[np.ndarray] = None
        self.image_metadata: Dict[str, Any] = {}
        self.current_file_path: Optional[str] = None
        self.zoom_level: float = 1.0
        self.pan_offset: Tuple[int, int] = (0, 0)
        
        # Overlay data
        self.overlays: List[Dict[str, Any]] = []
        self.show_overlays: bool = True
        self.cell_overlays: Dict[str, List[Dict[str, Any]]] = {}  # selection_id -> overlays
        self.bounding_boxes: List[Tuple[int, int, int, int]] = []  # (min_x, min_y, max_x, max_y)
        
        # Calibration mode
        self.calibration_mode: bool = False
        self.calibration_points: List[Dict[str, Any]] = []  # {x, y, label}
        self.current_mouse_pos: Tuple[int, int] = (0, 0)
        
        # Performance tracking
        self.load_start_time: Optional[float] = None
        
        # Worker thread
        self.load_worker: Optional[ImageLoadWorker] = None
        self.load_thread: Optional[QThread] = None
        
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Set up the image handler UI."""
        layout = QVBoxLayout(self)
        
        # Image display label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                border: 1px solid #dee2e6;
                background-color: #f8f9fa;
                min-height: 400px;
            }
        """)
        self.image_label.setText("No image loaded")
        
        # Enable mouse tracking for coordinate display
        self.image_label.setMouseTracking(True)
        self.image_label.mousePressEvent = self._mouse_press_event
        self.image_label.mouseMoveEvent = self._mouse_move_event
        
        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        
        # Coordinate display label
        self.coord_label = QLabel("Coordinates: (0, 0)")
        self.coord_label.setStyleSheet("QLabel { font-family: monospace; }")
        
        layout.addWidget(self.image_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.coord_label)
    
    @error_handler("Loading image file")
    def load_image(self, file_path: str) -> None:
        """
        Load an image file asynchronously.
        
        Args:
            file_path: Path to the image file
        """
        if self.load_thread and self.load_thread.isRunning():
            self.cancel_loading()
        
        self.current_file_path = file_path
        self.load_start_time = time.time()
        
        # Show progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Loading image...")
        
        # Create worker and thread
        self.load_worker = ImageLoadWorker(file_path)
        self.load_thread = QThread()
        
        # Connect signals
        self.load_worker.moveToThread(self.load_thread)
        self.load_thread.started.connect(self.load_worker.load_image)
        self.load_worker.progress_updated.connect(self.progress_bar.setValue)
        self.load_worker.loading_finished.connect(self._on_image_loaded)
        self.load_worker.loading_failed.connect(self._on_image_load_failed)
        self.load_worker.loading_finished.connect(self.load_thread.quit)
        self.load_worker.loading_failed.connect(self.load_thread.quit)
        self.load_thread.finished.connect(lambda: self.progress_bar.setVisible(False))
        
        # Start loading
        self.load_thread.start()
        
        self.log_info(f"Started loading image: {Path(file_path).name}")
    
    def cancel_loading(self) -> None:
        """Cancel current image loading operation."""
        if self.load_worker:
            self.load_worker.cancel()
        
        if self.load_thread and self.load_thread.isRunning():
            self.load_thread.quit()
            self.load_thread.wait(1000)  # Wait up to 1 second
        
        self.progress_bar.setVisible(False)
        self.log_info("Image loading cancelled")
    
    def _on_image_loaded(self, image_data: np.ndarray, metadata: Dict[str, Any]) -> None:
        """
        Handle successful image loading.
        
        Args:
            image_data: Loaded image as numpy array
            metadata: Image metadata dictionary
        """
        self.image_data = image_data
        self.image_metadata = metadata
        self.zoom_level = 1.0
        self.pan_offset = (0, 0)
        
        # Update display
        self._update_display()
        
        # Emit signal
        self.image_loaded.emit(self.current_file_path)
        
        # Log performance
        if self.load_start_time:
            total_time = time.time() - self.load_start_time
            self.log_info(f"Image loading completed in {total_time:.2f}s")
            
            if not metadata.get('performance_target_met', True):
                self.log_warning("Image loading exceeded performance target")
    
    def _on_image_load_failed(self, error_message: str) -> None:
        """
        Handle failed image loading.
        
        Args:
            error_message: Error description
        """
        self.image_data = None
        self.image_metadata = {}
        self.image_label.setText(f"Failed to load image:\n{error_message}")
        
        # Emit signal
        self.image_load_failed.emit(error_message)
        
        self.log_error(f"Image loading failed: {error_message}")
    
    def _update_display(self) -> None:
        """Update the image display with current image data and overlays."""
        if self.image_data is None:
            return
        
        try:
            # Convert numpy array to QImage
            qimage = self._numpy_to_qimage(self.image_data)
            
            # Apply zoom and create pixmap
            if self.zoom_level != 1.0:
                qimage = qimage.scaled(
                    int(qimage.width() * self.zoom_level),
                    int(qimage.height() * self.zoom_level),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
            
            pixmap = QPixmap.fromImage(qimage)
            
            # Draw overlays if enabled
            if self.show_overlays and (self.overlays or self.cell_overlays):
                pixmap = self._draw_overlays(pixmap)
            
            # Update label
            self.image_label.setPixmap(pixmap)
            
        except Exception as e:
            self.log_error(f"Failed to update display: {e}")
            self.image_label.setText(f"Display error: {e}")
    
    def _numpy_to_qimage(self, image: np.ndarray) -> QImage:
        """
        Convert numpy array to QImage.
        
        Args:
            image: Image as numpy array
        
        Returns:
            QImage object
        """
        if len(image.shape) == 2:
            # Grayscale image
            height, width = image.shape
            bytes_per_line = width

            if image.dtype == np.uint8:
                return QImage(image.data, width, height, bytes_per_line, QImage.Format_Grayscale8)
            else:
                # Convert to uint8, handle uniform value (no division by zero)
                min_val = image.min()
                max_val = image.max()
                if max_val == min_val:
                    image_uint8 = np.full_like(image, 0 if min_val == 0 else 255, dtype=np.uint8)
                else:
                    image_uint8 = ((image - min_val) / (max_val - min_val) * 255).astype(np.uint8)
                return QImage(image_uint8.data, width, height, bytes_per_line, QImage.Format_Grayscale8)
        
        elif len(image.shape) == 3:
            # Color image
            height, width, channels = image.shape
            bytes_per_line = width * channels

            if channels == 3:
                # RGB image
                if image.dtype != np.uint8:
                    min_val = image.min()
                    max_val = image.max()
                    if max_val == min_val:
                        image = np.full_like(image, 0 if min_val == 0 else 255, dtype=np.uint8)
                    else:
                        image = ((image - min_val) / (max_val - min_val) * 255).astype(np.uint8)
                return QImage(image.data, width, height, bytes_per_line, QImage.Format_RGB888)
            
            elif channels == 4:
                # RGBA image
                if image.dtype != np.uint8:
                    min_val = image.min()
                    max_val = image.max()
                    if max_val == min_val:
                        image = np.full_like(image, 0 if min_val == 0 else 255, dtype=np.uint8)
                    else:
                        image = ((image - min_val) / (max_val - min_val) * 255).astype(np.uint8)
                return QImage(image.data, width, height, bytes_per_line, QImage.Format_RGBA8888)
        
        raise ValueError(f"Unsupported image shape: {image.shape}")
    
    def _draw_overlays(self, pixmap: QPixmap) -> QPixmap:
        """
        Draw overlays on the pixmap.
        
        Args:
            pixmap: Base pixmap
        
        Returns:
            Pixmap with overlays drawn
        """
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw general overlays
        for overlay in self.overlays:
            self._draw_single_overlay(painter, overlay)
        
        # Draw cell highlight overlays
        for selection_id, overlays in self.cell_overlays.items():
            for overlay in overlays:
                self._draw_single_overlay(painter, overlay)
        
        painter.end()
        return pixmap
    
    def _draw_single_overlay(self, painter: QPainter, overlay: Dict[str, Any]) -> None:
        """
        Draw a single overlay.
        
        Args:
            painter: QPainter instance
            overlay: Overlay data dictionary
        """
        overlay_type = overlay.get('type', 'rectangle')
        color = overlay.get('color', '#FF0000')
        alpha = overlay.get('alpha', 0.3)
        
        # Parse hex color
        if color.startswith('#'):
            color_val = int(color[1:], 16)
            r = (color_val >> 16) & 255
            g = (color_val >> 8) & 255
            b = color_val & 255
        else:
            # Fallback to red
            r, g, b = 255, 0, 0
        
        # Create color with alpha
        from PySide6.QtGui import QColor
        qt_color = QColor(r, g, b, int(alpha * 255))
        
        # Set up pen and brush
        pen = QPen(qt_color)
        pen.setWidth(2)
        brush = QBrush(qt_color)
        
        painter.setPen(pen)
        painter.setBrush(brush)
        
        if overlay_type in ['rectangle', 'cell_highlight']:
            x = int(overlay['x'] * self.zoom_level)
            y = int(overlay['y'] * self.zoom_level) 
            width = int(overlay['width'] * self.zoom_level)
            height = int(overlay['height'] * self.zoom_level)
            painter.drawRect(x, y, width, height)
    
    def set_zoom(self, zoom_level: float) -> None:
        """
        Set zoom level and update display.
        
        Args:
            zoom_level: New zoom level (1.0 = 100%)
        """
        self.zoom_level = max(0.1, min(10.0, zoom_level))  # Clamp between 10% and 1000%
        self._update_display()
        self.zoom_changed.emit(self.zoom_level)
    
    def zoom_in(self) -> None:
        """Zoom in by 25%."""
        self.set_zoom(self.zoom_level * 1.25)
    
    def zoom_out(self) -> None:
        """Zoom out by 25%."""
        self.set_zoom(self.zoom_level * 0.8)
    
    def zoom_fit(self) -> None:
        """Fit image to window size."""
        # TODO: Calculate zoom to fit window
        self.set_zoom(1.0)
    
    def fit_to_window(self) -> None:
        """Alias for zoom_fit for consistency."""
        self.zoom_fit()
    
    def reset_view(self) -> None:
        """Reset view to default state."""
        self.zoom_level = 1.0
        self.pan_offset = (0, 0)
        self._update_display()
        self.zoom_changed.emit(self.zoom_level)
    
    def pan(self, dx: int, dy: int) -> None:
        """
        Pan the image view.
        
        Args:
            dx: Horizontal pan distance in pixels
            dy: Vertical pan distance in pixels
        """
        if self.image_data is None:
            return
        
        # Update pan offset
        self.pan_offset = (
            self.pan_offset[0] + dx,
            self.pan_offset[1] + dy
        )
        
        # TODO: Implement actual panning in display
        self._update_display()
    
    def set_selection_mode(self, enabled: bool) -> None:
        """
        Enable or disable selection mode.
        
        Args:
            enabled: Whether to enable selection mode
        """
        # TODO: Implement selection mode
        self.log_info(f"Selection mode: {'enabled' if enabled else 'disabled'}")
    
    def get_visible_rect(self) -> Tuple[int, int, int, int]:
        """
        Get the currently visible rectangle in image coordinates.
        
        Returns:
            Tuple of (x, y, width, height) in image coordinates
        """
        if self.image_data is None:
            return (0, 0, 0, 0)
        
        # Calculate visible area based on widget size and zoom
        widget_width = self.image_label.width()
        widget_height = self.image_label.height()
        
        # Image dimensions
        img_height, img_width = self.image_data.shape[:2]
        
        # Visible dimensions in image coordinates
        visible_width = min(widget_width / self.zoom_level, img_width)
        visible_height = min(widget_height / self.zoom_level, img_height)
        
        # Calculate position based on pan offset
        x = max(0, -self.pan_offset[0] / self.zoom_level)
        y = max(0, -self.pan_offset[1] / self.zoom_level)
        
        return (int(x), int(y), int(visible_width), int(visible_height))
    
    def navigate_to_position(self, norm_x: float, norm_y: float) -> None:
        """
        Navigate to a normalized position in the image.
        
        Args:
            norm_x: Normalized X position (0-1)
            norm_y: Normalized Y position (0-1)
        """
        if self.image_data is None:
            return
        
        # Get image dimensions
        img_height, img_width = self.image_data.shape[:2]
        
        # Calculate target position in image coordinates
        target_x = int(norm_x * img_width)
        target_y = int(norm_y * img_height)
        
        # Calculate pan offset to center on target
        widget_width = self.image_label.width()
        widget_height = self.image_label.height()
        
        # Calculate offset to center the target point
        self.pan_offset = (
            int(widget_width / 2 - target_x * self.zoom_level),
            int(widget_height / 2 - target_y * self.zoom_level)
        )
        
        self._update_display()
        self.log_info(f"Navigated to position: ({norm_x:.2f}, {norm_y:.2f})")
    
    def add_overlay(self, overlay_type: str, x: float, y: float, 
                   width: float, height: float, color: str = '#FF0000', 
                   alpha: float = 0.3) -> None:
        """
        Add an overlay to the image.
        
        Args:
            overlay_type: Type of overlay ('rectangle', 'circle', etc.)
            x, y: Position coordinates
            width, height: Overlay dimensions
            color: Overlay color
            alpha: Transparency level
        """
        overlay = {
            'type': overlay_type,
            'x': x,
            'y': y,
            'width': width,
            'height': height,
            'color': color,
            'alpha': alpha
        }
        
        self.overlays.append(overlay)
        self._update_display()
    
    def clear_overlays(self) -> None:
        """Clear all overlays."""
        self.overlays.clear()
        self._update_display()
    
    def toggle_overlays(self, show: bool) -> None:
        """
        Toggle overlay visibility.
        
        Args:
            show: Whether to show overlays
        """
        self.show_overlays = show
        self._update_display()
    
    def get_image_info(self) -> Dict[str, Any]:
        """
        Get information about the current image.
        
        Returns:
            Dictionary with image information
        """
        if self.image_data is None:
            return {}
        
        info = {
            'file_path': self.current_file_path,
            'shape': self.image_data.shape,
            'dtype': str(self.image_data.dtype),
            'zoom_level': self.zoom_level,
            'overlay_count': len(self.overlays),
            'overlays_visible': self.show_overlays
        }
        
        info.update(self.image_metadata)
        return info
    
    def set_bounding_boxes(self, bounding_boxes: List[Tuple[int, int, int, int]]) -> None:
        """
        Set bounding boxes for cell highlighting.
        
        Args:
            bounding_boxes: List of (min_x, min_y, max_x, max_y) tuples
        """
        self.bounding_boxes = bounding_boxes
        self.log_info(f"Set {len(bounding_boxes)} bounding boxes for cell highlighting")
    
    def highlight_cells(self, selection_id: str, cell_indices: List[int], 
                       color: str, alpha: float = 0.5) -> None:
        """
        Highlight selected cells on the image.
        
        Args:
            selection_id: Unique selection identifier
            cell_indices: List of cell indices to highlight
            color: Highlight color (hex format)
            alpha: Transparency level
        """
        if not self.bounding_boxes:
            self.log_warning("No bounding boxes available for cell highlighting")
            return
        
        # Clear previous overlays for this selection
        self.cell_overlays.pop(selection_id, None)
        
        # Create new overlays for selected cells
        overlays = []
        for cell_index in cell_indices:
            if 0 <= cell_index < len(self.bounding_boxes):
                min_x, min_y, max_x, max_y = self.bounding_boxes[cell_index]
                overlay = {
                    'type': 'cell_highlight',
                    'x': min_x,
                    'y': min_y,
                    'width': max_x - min_x,
                    'height': max_y - min_y,
                    'color': color,
                    'alpha': alpha,
                    'cell_index': cell_index
                }
                overlays.append(overlay)
        
        self.cell_overlays[selection_id] = overlays
        self._update_display()
        
        self.log_info(f"Highlighted {len(overlays)} cells for selection {selection_id}")
    
    def remove_cell_highlights(self, selection_id: str) -> None:
        """
        Remove cell highlights for a specific selection.
        
        Args:
            selection_id: Selection identifier
        """
        if selection_id in self.cell_overlays:
            del self.cell_overlays[selection_id]
            self._update_display()
            self.log_info(f"Removed cell highlights for selection {selection_id}")
    
    def clear_all_cell_highlights(self) -> None:
        """Clear all cell highlights."""
        self.cell_overlays.clear()
        self._update_display()
        self.log_info("Cleared all cell highlights")
    
    def set_calibration_mode(self, enabled: bool) -> None:
        """
        Enable or disable calibration mode for clicking reference points.
        
        Args:
            enabled: Whether to enable calibration mode
        """
        self.calibration_mode = enabled
        if enabled:
            self.image_label.setCursor(Qt.CrossCursor)
            self.update_status("Calibration mode: Click on reference points")
        else:
            self.image_label.setCursor(Qt.ArrowCursor)
            self.update_status("Calibration mode disabled")
        
        self.log_info(f"Calibration mode {'enabled' if enabled else 'disabled'}")
    
    def clear_calibration_points(self) -> None:
        """Clear all calibration points."""
        self.calibration_points.clear()
        self._update_display()
        self.log_info("Cleared calibration points")
    
    def _mouse_press_event(self, event) -> None:
        """Handle mouse press events on the image."""
        if not self.image_data is None and event.button() == Qt.LeftButton:
            # Get image coordinates from label coordinates
            label_x = event.x()
            label_y = event.y()
            
            # Convert to image coordinates (accounting for zoom and pan)
            image_x, image_y = self._label_to_image_coords(label_x, label_y)
            
            if self.calibration_mode:
                # Add calibration point
                point_label = f"Point_{len(self.calibration_points) + 1}"
                calibration_point = {
                    'x': image_x,
                    'y': image_y,
                    'label': point_label
                }
                self.calibration_points.append(calibration_point)
                self._update_display()
                
                # Emit signal for UI to handle
                self.calibration_point_clicked.emit(image_x, image_y, point_label)
                
                self.log_info(f"Added calibration point: {point_label} at ({image_x}, {image_y})")
    
    def _mouse_move_event(self, event) -> None:
        """Handle mouse move events for coordinate tracking."""
        if not self.image_data is None:
            # Get image coordinates from label coordinates
            label_x = event.x()
            label_y = event.y()
            
            # Convert to image coordinates
            image_x, image_y = self._label_to_image_coords(label_x, label_y)
            
            # Update coordinate display
            self.current_mouse_pos = (image_x, image_y)
            self.coord_label.setText(f"Coordinates: ({image_x}, {image_y})")
            
            # Emit coordinate change signal
            self.coordinates_changed.emit(float(image_x), float(image_y))
    
    def _label_to_image_coords(self, label_x: int, label_y: int) -> Tuple[int, int]:
        """
        Convert label coordinates to image coordinates, accounting for Qt.KeepAspectRatio scaling and label padding.

        Args:
            label_x: X coordinate in label
            label_y: Y coordinate in label

        Returns:
            Tuple of (image_x, image_y)
        """
        if self.image_data is None:
            return (0, 0)

        label_size = self.image_label.size()
        image_height, image_width = self.image_data.shape[:2]
        label_width, label_height = label_size.width(), label_size.height()

        # ZeroDivisionError 방지
        if label_width == 0 or label_height == 0:
            return (0, 0)

        # 이미지와 라벨의 종횡비 계산
        image_aspect = image_width / image_height
        label_aspect = label_width / label_height

        # QLabel 내 실제 이미지 표시 영역 크기 계산 (aspect ratio 유지)
        if image_aspect > label_aspect:
            scaled_width = label_width
            scaled_height = int(label_width / image_aspect)
        else:
            scaled_height = label_height
            scaled_width = int(label_height * image_aspect)

        offset_x = (label_width - scaled_width) // 2
        offset_y = (label_height - scaled_height) // 2

        # 이미지 표시 영역 내에 있는지 확인
        if not (offset_x <= label_x < offset_x + scaled_width and offset_y <= label_y < offset_y + scaled_height):
            return (0, 0)

        # 라벨 내 이미지 표시 영역 좌표 → 원본 이미지 좌표
        rel_x = label_x - offset_x
        rel_y = label_y - offset_y
        image_x = int(rel_x * image_width / scaled_width)
        image_y = int(rel_y * image_height / scaled_height)

        # Clamp
        image_x = max(0, min(image_x, image_width - 1))
        image_y = max(0, min(image_y, image_height - 1))
        return (image_x, image_y)
    
    def update_status(self, message: str) -> None:
        """Update status message (placeholder for main window integration)."""
        pass  # Will be connected to main window status bar
    
    def cleanup(self) -> None:
        """Clean up resources."""
        self.cancel_loading()
        self.image_data = None
        self.image_metadata = {}
        self.overlays.clear()
        self.cell_overlays.clear()
        self.bounding_boxes.clear()