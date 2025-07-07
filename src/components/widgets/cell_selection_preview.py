"""
Cell Selection Preview Component

Shows a preview of selected cells before final save operation.
Provides visual feedback to users and allows confirmation/cancellation.
"""

from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QScrollArea, QFrame, QPushButton, QSizePolicy
)
from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtGui import QPixmap, QPainter, QColor, QBrush

from components.base.base_button import BaseButton, ButtonVariant, ButtonSize
from config.design_tokens import Colors, Spacing, BorderRadius, Typography
from utils.logging_config import LoggerMixin
from utils.error_handler import error_handler


@dataclass
class CellThumbnailData:
    """Data structure for cell thumbnail preview."""
    cell_index: int
    thumbnail_pixmap: Optional[QPixmap] = None
    bounding_box: tuple = None  # (min_x, min_y, max_x, max_y)
    is_included: bool = True
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class CellThumbnailWidget(QFrame, LoggerMixin):
    """Individual cell thumbnail widget for preview."""
    
    # Signals
    clicked = Signal(int)  # cell_index
    inclusion_changed = Signal(int, bool)  # cell_index, is_included
    
    def __init__(self, cell_data: CellThumbnailData, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.cell_data = cell_data
        self._is_selected = False
        
        self.setup_ui()
        self.update_appearance()
    
    def setup_ui(self) -> None:
        """Set up the thumbnail widget UI."""
        self.setFixedSize(120, 120)  # Standard thumbnail size
        self.setFrameStyle(QFrame.StyledPanel)
        self.setCursor(Qt.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Thumbnail image area
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(80, 80)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: var(--muted);
                border: 1px solid var(--border);
                border-radius: 4px;
            }
        """)
        
        # Cell index label
        self.index_label = QLabel(f"Cell {self.cell_data.cell_index}")
        self.index_label.setAlignment(Qt.AlignCenter)
        self.index_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: var(--muted-foreground);
                font-weight: 500;
            }
        """)
        
        layout.addWidget(self.image_label)
        layout.addWidget(self.index_label)
        
        # Load thumbnail if available
        if self.cell_data.thumbnail_pixmap:
            self.set_thumbnail(self.cell_data.thumbnail_pixmap)
        else:
            self.set_placeholder()
    
    def set_thumbnail(self, pixmap: QPixmap) -> None:
        """Set the thumbnail image."""
        if pixmap and not pixmap.isNull():
            # Scale pixmap to fit while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(
                80, 80, 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
        else:
            self.set_placeholder()
    
    def set_placeholder(self) -> None:
        """Set placeholder when no thumbnail is available."""
        self.image_label.setText("No Image")
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: var(--muted);
                border: 1px solid var(--border);
                border-radius: 4px;
                color: var(--muted-foreground);
                font-size: 10px;
            }
        """)
    
    def set_selected(self, selected: bool) -> None:
        """Set the selected state of the thumbnail."""
        self._is_selected = selected
        self.update_appearance()
    
    def update_appearance(self) -> None:
        """Update the visual appearance based on state."""
        if self._is_selected:
            border_color = "var(--primary)"
            background_color = "var(--primary)/10"
        elif not self.cell_data.is_included:
            border_color = "var(--muted)"
            background_color = "var(--muted)/50"
        else:
            border_color = "var(--border)"
            background_color = "var(--background)"
        
        self.setStyleSheet(f"""
            CellThumbnailWidget {{
                border: 2px solid {border_color};
                border-radius: 8px;
                background-color: {background_color};
            }}
            CellThumbnailWidget:hover {{
                border-color: var(--ring);
                background-color: var(--accent);
            }}
        """)
    
    def mousePressEvent(self, event) -> None:
        """Handle mouse press events."""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.cell_data.cell_index)
        super().mousePressEvent(event)
    
    def mouseDoubleClickEvent(self, event) -> None:
        """Handle double-click to toggle inclusion."""
        if event.button() == Qt.LeftButton:
            self.cell_data.is_included = not self.cell_data.is_included
            self.inclusion_changed.emit(self.cell_data.cell_index, self.cell_data.is_included)
            self.update_appearance()
        super().mouseDoubleClickEvent(event)


class CellSelectionPreview(QWidget, LoggerMixin):
    """
    Cell selection preview component showing thumbnails before save.
    
    Features:
    - Grid layout of cell thumbnails
    - Visual feedback for selected cells  
    - Confirmation and cancellation buttons
    - Statistics display
    - Responsive layout
    """
    
    # Signals
    selection_confirmed = Signal(list)  # List of cell indices to save
    selection_cancelled = Signal()
    cell_clicked = Signal(int)  # For navigation to main image
    preview_closed = Signal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # Data storage
        self.cell_thumbnails: List[CellThumbnailData] = []
        self.thumbnail_widgets: List[CellThumbnailWidget] = []
        self.selected_cell_index: Optional[int] = None
        
        # Configuration
        self.thumbnails_per_row = 6
        self.max_thumbnails = 50  # Performance limit
        
        self.setup_ui()
        self.connect_signals()
        
        self.log_info("Cell selection preview component initialized")
    
    def setup_ui(self) -> None:
        """Set up the preview component UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Header section
        self.setup_header(layout)
        
        # Thumbnails grid section
        self.setup_thumbnails_grid(layout)
        
        # Statistics section
        self.setup_statistics(layout)
        
        # Action buttons section
        self.setup_action_buttons(layout)
        
        # Apply overall styling
        self.setStyleSheet("""
            CellSelectionPreview {
                background-color: var(--card);
                border: 1px solid var(--border);
                border-radius: 12px;
            }
        """)
    
    def setup_header(self, parent_layout: QVBoxLayout) -> None:
        """Set up the header section."""
        header_layout = QHBoxLayout()
        
        # Title
        self.title_label = QLabel("Cell Selection Preview")
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: 600;
                color: var(--foreground);
                margin-bottom: 4px;
            }
        """)
        
        # Subtitle
        self.subtitle_label = QLabel("Review and confirm your cell selection")
        self.subtitle_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: var(--muted-foreground);
            }
        """)
        
        header_text_layout = QVBoxLayout()
        header_text_layout.setSpacing(0)
        header_text_layout.addWidget(self.title_label)
        header_text_layout.addWidget(self.subtitle_label)
        
        header_layout.addLayout(header_text_layout)
        header_layout.addStretch()
        
        parent_layout.addLayout(header_layout)
    
    def setup_thumbnails_grid(self, parent_layout: QVBoxLayout) -> None:
        """Set up the scrollable thumbnails grid."""
        # Scroll area for thumbnails
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setMinimumHeight(300)
        scroll_area.setMaximumHeight(500)
        
        # Grid container widget
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(12)
        self.grid_layout.setContentsMargins(8, 8, 8, 8)
        
        scroll_area.setWidget(self.grid_container)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid var(--border);
                border-radius: 8px;
                background-color: var(--background);
            }
        """)
        
        parent_layout.addWidget(scroll_area)
    
    def setup_statistics(self, parent_layout: QVBoxLayout) -> None:
        """Set up the statistics display."""
        stats_frame = QFrame()
        stats_frame.setFrameStyle(QFrame.StyledPanel)
        stats_frame.setStyleSheet("""
            QFrame {
                background-color: var(--muted);
                border-radius: 8px;
                padding: 12px;
            }
        """)
        
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setSpacing(24)
        
        # Total cells stat
        self.total_cells_label = QLabel("Total: 0")
        self.total_cells_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 500;
                color: var(--foreground);
            }
        """)
        
        # Included cells stat
        self.included_cells_label = QLabel("Included: 0")
        self.included_cells_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 500;
                color: var(--primary);
            }
        """)
        
        # Excluded cells stat
        self.excluded_cells_label = QLabel("Excluded: 0")
        self.excluded_cells_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 500;
                color: var(--muted-foreground);
            }
        """)
        
        stats_layout.addWidget(self.total_cells_label)
        stats_layout.addWidget(self.included_cells_label)
        stats_layout.addWidget(self.excluded_cells_label)
        stats_layout.addStretch()
        
        parent_layout.addWidget(stats_frame)
    
    def setup_action_buttons(self, parent_layout: QVBoxLayout) -> None:
        """Set up the action buttons."""
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)
        
        # Cancel button
        self.cancel_button = BaseButton(
            text="Cancel",
            variant=ButtonVariant.OUTLINE,
            size=ButtonSize.DEFAULT
        )
        
        # Confirm button
        self.confirm_button = BaseButton(
            text="Confirm Selection",
            variant=ButtonVariant.DEFAULT,
            size=ButtonSize.DEFAULT
        )
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.confirm_button)
        
        parent_layout.addLayout(buttons_layout)
    
    def connect_signals(self) -> None:
        """Connect widget signals."""
        self.cancel_button.clicked.connect(self.on_cancel_clicked)
        self.confirm_button.clicked.connect(self.on_confirm_clicked)
    
    @error_handler("Loading cell selection preview")
    def load_cells(self, cell_data: List[CellThumbnailData]) -> None:
        """
        Load cells for preview display.
        
        Args:
            cell_data: List of cell thumbnail data
        """
        # Clear existing thumbnails
        self.clear_thumbnails()
        
        # Limit thumbnails for performance
        if len(cell_data) > self.max_thumbnails:
            self.log_warning(f"Too many cells ({len(cell_data)}), limiting to {self.max_thumbnails}")
            cell_data = cell_data[:self.max_thumbnails]
        
        self.cell_thumbnails = cell_data
        
        # Create thumbnail widgets
        for i, cell_data in enumerate(self.cell_thumbnails):
            thumbnail_widget = CellThumbnailWidget(cell_data)
            thumbnail_widget.clicked.connect(self.on_thumbnail_clicked)
            thumbnail_widget.inclusion_changed.connect(self.on_inclusion_changed)
            
            # Add to grid layout
            row = i // self.thumbnails_per_row
            col = i % self.thumbnails_per_row
            self.grid_layout.addWidget(thumbnail_widget, row, col)
            
            self.thumbnail_widgets.append(thumbnail_widget)
        
        # Update statistics
        self.update_statistics()
        
        self.log_info(f"Loaded {len(self.cell_thumbnails)} cells for preview")
    
    def clear_thumbnails(self) -> None:
        """Clear all thumbnail widgets."""
        for widget in self.thumbnail_widgets:
            widget.deleteLater()
        
        self.thumbnail_widgets.clear()
        self.cell_thumbnails.clear()
        self.selected_cell_index = None
        
        # Clear grid layout
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def update_statistics(self) -> None:
        """Update the statistics display."""
        total_count = len(self.cell_thumbnails)
        included_count = sum(1 for cell in self.cell_thumbnails if cell.is_included)
        excluded_count = total_count - included_count
        
        self.total_cells_label.setText(f"Total: {total_count}")
        self.included_cells_label.setText(f"Included: {included_count}")
        self.excluded_cells_label.setText(f"Excluded: {excluded_count}")
        
        # Enable/disable confirm button based on included count
        self.confirm_button.setEnabled(included_count > 0)
    
    def on_thumbnail_clicked(self, cell_index: int) -> None:
        """Handle thumbnail click."""
        # Update selected state
        for widget in self.thumbnail_widgets:
            widget.set_selected(widget.cell_data.cell_index == cell_index)
        
        self.selected_cell_index = cell_index
        
        # Emit signal for main image navigation
        self.cell_clicked.emit(cell_index)
        
        self.log_info(f"Cell {cell_index} selected for navigation")
    
    def on_inclusion_changed(self, cell_index: int, is_included: bool) -> None:
        """Handle cell inclusion/exclusion change."""
        # Update data
        for cell_data in self.cell_thumbnails:
            if cell_data.cell_index == cell_index:
                cell_data.is_included = is_included
                break
        
        # Update statistics
        self.update_statistics()
        
        status = "included" if is_included else "excluded"
        self.log_info(f"Cell {cell_index} {status}")
    
    def on_cancel_clicked(self) -> None:
        """Handle cancel button click."""
        self.selection_cancelled.emit()
        self.preview_closed.emit()
        self.log_info("Selection cancelled")
    
    def on_confirm_clicked(self) -> None:
        """Handle confirm button click."""
        # Get included cell indices
        included_indices = [
            cell.cell_index for cell in self.cell_thumbnails 
            if cell.is_included
        ]
        
        if included_indices:
            self.selection_confirmed.emit(included_indices)
            self.preview_closed.emit()
            self.log_info(f"Selection confirmed: {len(included_indices)} cells")
        else:
            self.log_warning("No cells selected for confirmation")
    
    def get_included_cells(self) -> List[int]:
        """Get list of included cell indices."""
        return [cell.cell_index for cell in self.cell_thumbnails if cell.is_included]
    
    def set_thumbnails_per_row(self, count: int) -> None:
        """Set the number of thumbnails per row."""
        if count > 0:
            self.thumbnails_per_row = count
            # Rebuild layout if cells are loaded
            if self.cell_thumbnails:
                current_data = self.cell_thumbnails.copy()
                self.load_cells(current_data) 