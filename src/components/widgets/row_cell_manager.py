"""
Row-by-Row Cell Management Interface

Provides interface for examining and managing individual cells within each selection row.
Allows users to inspect cell quality and toggle cell inclusion/exclusion.
"""

from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QScrollArea, QListWidget, QListWidgetItem,
    QCheckBox, QSplitter, QTextEdit, QGroupBox, QSizePolicy
)
from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont, QMouseEvent, QImage
import numpy as np

from components.base.base_button import BaseButton, ButtonVariant, ButtonSize
from config.design_tokens import Colors, Spacing, BorderRadius, Typography
from utils.logging_config import LoggerMixin
from utils.error_handler import error_handler
from models.coordinate_transformer import CoordinateTransformer


@dataclass
class CellRowData:
    """Data structure for cell row management."""
    selection_id: str
    selection_label: str
    selection_color: str
    cell_indices: List[int]
    cell_metadata: Dict[int, Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.cell_metadata is None:
            self.cell_metadata = {}


class CellRowItem(QFrame, LoggerMixin):
    """Individual cell item widget for row management."""
    
    # Signals
    cell_toggled = Signal(int, bool)  # cell_index, is_included
    cell_selected = Signal(int)  # cell_index
    
    def __init__(self, cell_index: int, cell_metadata: Dict[str, Any], 
                 is_included: bool = True, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.cell_index = cell_index
        self.cell_metadata = cell_metadata
        self.is_included = is_included
        self._is_selected = False
        
        self.setup_ui()
        self.update_appearance()
    
    def setup_ui(self) -> None:
        """Set up the cell item UI."""
        self.setFixedHeight(40)  # Reduced from 80 to 40 (50% reduction)
        self.setFrameStyle(QFrame.StyledPanel)
        self.setCursor(Qt.PointingHandCursor)
        
        layout = QHBoxLayout(self)
        layout.setSpacing(8)  # Reduced spacing
        layout.setContentsMargins(8, 4, 8, 4)  # Reduced margins
        
        # Inclusion checkbox
        self.inclusion_checkbox = QCheckBox()
        self.inclusion_checkbox.setChecked(self.is_included)
        self.inclusion_checkbox.stateChanged.connect(self.on_inclusion_changed)
        self.inclusion_checkbox.setToolTip("Include/exclude this cell from selection")
        
        # Cell info section - single line layout
        # Cell index label
        self.index_label = QLabel(f"Cell {self.cell_index}")
        self.index_label.setStyleSheet("""
            QLabel {
                font-weight: 600;
                font-size: 12px;
                color: var(--foreground);
            }
        """)
        
        # Cell metadata display (simplified)
        metadata_text = self._format_metadata_compact()
        self.metadata_label = QLabel(metadata_text)
        self.metadata_label.setStyleSheet("""
            QLabel {
                font-size: 10px;
                color: var(--muted-foreground);
                margin-left: 8px;
            }
        """)
        
        layout.addWidget(self.inclusion_checkbox)
        layout.addWidget(self.index_label)
        layout.addWidget(self.metadata_label)
        layout.addStretch()
        # Removed thumbnail_label (image button)
    
    def _format_metadata(self) -> str:
        """Format cell metadata for display."""
        if not self.cell_metadata:
            return "No metadata available"
        
        parts = []
        if 'area' in self.cell_metadata:
            parts.append(f"Area: {self.cell_metadata['area']:.1f}")
        if 'intensity' in self.cell_metadata:
            parts.append(f"Intensity: {self.cell_metadata['intensity']:.1f}")
        if 'perimeter' in self.cell_metadata:
            parts.append(f"Perimeter: {self.cell_metadata['perimeter']:.1f}")
        
        return " | ".join(parts) if parts else "Cell properties available"
    
    def _format_metadata_compact(self) -> str:
        """Format cell metadata for compact display."""
        if not self.cell_metadata:
            return ""
        
        # Show only the most important metric in compact form
        if 'area' in self.cell_metadata:
            return f"A:{self.cell_metadata['area']:.0f}"
        elif 'intensity' in self.cell_metadata:
            return f"I:{self.cell_metadata['intensity']:.0f}"
        
        return ""
    
    def set_thumbnail(self, pixmap: QPixmap) -> None:
        """Set the thumbnail image for the cell."""
        if pixmap and not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                60, 60, 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            self.thumbnail_label.setPixmap(scaled_pixmap)
    
    def set_selected(self, selected: bool) -> None:
        """Set the selected state of the cell item."""
        self._is_selected = selected
        self.update_appearance()
    
    def update_appearance(self) -> None:
        """Update visual appearance based on state."""
        if self._is_selected:
            border_color = "var(--primary)"
            background_color = "var(--primary)/10"
        elif not self.is_included:
            border_color = "var(--muted)"
            background_color = "var(--muted)/30"
        else:
            border_color = "var(--border)"
            background_color = "var(--background)"
        
        self.setStyleSheet(f"""
            CellRowItem {{
                border: 2px solid {border_color};
                border-radius: 8px;
                background-color: {background_color};
            }}
            CellRowItem:hover {{
                border-color: var(--ring);
                background-color: var(--accent);
            }}
        """)
    
    def on_inclusion_changed(self, state: int) -> None:
        """Handle inclusion checkbox state change."""
        self.is_included = bool(state)
        self.cell_toggled.emit(self.cell_index, self.is_included)
        self.update_appearance()
        
        status = "included" if self.is_included else "excluded"
        self.log_info(f"Cell {self.cell_index} {status}")
    
    def mousePressEvent(self, event) -> None:
        """Handle mouse press events."""
        if event.button() == Qt.LeftButton:
            self.cell_selected.emit(self.cell_index)
        super().mousePressEvent(event)


class RowCellManager(QWidget, LoggerMixin):
    """
    Row-by-Row Cell Management Interface.
    
    Provides functionality to:
    - Display individual cells within a selected row/selection
    - Allow inclusion/exclusion of specific cells
    - Show cell metadata and thumbnails
    - Navigate to cells in main image view
    """
    
    # Signals
    cell_inclusion_changed = Signal(str, int, bool)  # selection_id, cell_index, is_included
    cell_navigation_requested = Signal(int)  # cell_index for main image navigation
    row_management_closed = Signal()
    
    def __init__(self, 
                 image_handler=None, 
                 csv_parser=None, 
                 coordinate_transformer: Optional[CoordinateTransformer] = None,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.image_handler = image_handler
        self.csv_parser = csv_parser
        self.coordinate_transformer = coordinate_transformer
        
        self.current_row_data: Optional[CellRowData] = None
        self.cell_items: List[CellRowItem] = []
        self.selected_cell_index: Optional[int] = None
        
        self.setup_ui()
        self.connect_signals()
        
        self.log_info("Row cell manager initialized")
    
    def setup_ui(self) -> None:
        """Set up the row cell manager UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Header section
        self.setup_header(layout)
        
        # Main content area with splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        
        # Cell list section
        self.setup_cell_list(splitter)
        
        # Cell details section  
        self.setup_cell_details(splitter)
        
        # Set splitter proportions
        splitter.setSizes([400, 300])
        layout.addWidget(splitter)
        
        # Action buttons
        self.setup_action_buttons(layout)
        
        # Apply overall styling
        self.setStyleSheet("""
            RowCellManager {
                background-color: var(--card);
                border: 1px solid var(--border);
                border-radius: 12px;
            }
        """)
    
    def setup_header(self, parent_layout: QVBoxLayout) -> None:
        """Set up the header section."""
        header_layout = QHBoxLayout()
        
        # Title and selection info
        self.title_label = QLabel("Manage ROIs")
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: 600;
                color: var(--foreground);
            }
        """)
        
        self.selection_info_label = QLabel("No selection")
        self.selection_info_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: var(--muted-foreground);
                margin-left: 16px;
            }
        """)
        
        header_layout.addWidget(self.title_label)
        header_layout.addWidget(self.selection_info_label)
        header_layout.addStretch()
        
        parent_layout.addLayout(header_layout)
    
    def setup_cell_list(self, splitter: QSplitter) -> None:
        """Set up the cell list section."""
        list_frame = QGroupBox("Cells in Selection")
        list_frame.setStyleSheet("""
            QGroupBox {
                font-weight: 600;
                border: 1px solid var(--border);
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 8px 0 8px;
            }
        """)
        
        list_layout = QVBoxLayout(list_frame)
        list_layout.setSpacing(8)
        list_layout.setContentsMargins(8, 16, 8, 8)
        
        # Statistics bar
        self.stats_layout = QHBoxLayout()
        self.total_cells_label = QLabel("Total: 0")
        self.included_cells_label = QLabel("Included: 0")
        self.excluded_cells_label = QLabel("Excluded: 0")
        
        for label in [self.total_cells_label, self.included_cells_label, self.excluded_cells_label]:
            label.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    font-weight: 500;
                    padding: 4px 8px;
                    background-color: var(--muted);
                    border-radius: 4px;
                }
            """)
        
        self.included_cells_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: 500;
                padding: 4px 8px;
                background-color: var(--primary)/20;
                color: var(--primary);
                border-radius: 4px;
            }
        """)
        
        self.stats_layout.addWidget(self.total_cells_label)
        self.stats_layout.addWidget(self.included_cells_label)
        self.stats_layout.addWidget(self.excluded_cells_label)
        self.stats_layout.addStretch()
        
        list_layout.addLayout(self.stats_layout)
        
        # Scrollable cell list
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setMinimumHeight(300)
        
        self.cell_list_widget = QWidget()
        self.cell_list_layout = QVBoxLayout(self.cell_list_widget)
        self.cell_list_layout.setSpacing(4)
        self.cell_list_layout.setContentsMargins(0, 0, 0, 0)
        self.cell_list_layout.addStretch()  # Push items to top
        
        scroll_area.setWidget(self.cell_list_widget)
        list_layout.addWidget(scroll_area)
        
        splitter.addWidget(list_frame)
    
    def setup_cell_details(self, splitter: QSplitter) -> None:
        """Set up the cell image display section."""
        image_frame = QGroupBox("Cell Image")
        image_frame.setStyleSheet("""
            QGroupBox {
                font-weight: 600;
                border: 1px solid var(--border);
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 8px 0 8px;
            }
        """)
        
        image_layout = QVBoxLayout(image_frame)
        image_layout.setSpacing(12)
        image_layout.setContentsMargins(8, 16, 8, 8)
        
        # Selected cell info
        self.selected_cell_label = QLabel("No cell selected")
        self.selected_cell_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 600;
                color: var(--foreground);
                padding: 8px;
                background-color: var(--muted);
                border-radius: 6px;
                text-align: center;
            }
        """)
        
        # Cell image display
        self.cell_image_label = QLabel("No cell selected")
        self.cell_image_label.setAlignment(Qt.AlignCenter)
        self.cell_image_label.setFrameShape(QFrame.StyledPanel)
        self.cell_image_label.setWordWrap(True)
        # 고정 크기 설정
        self.cell_image_label.setFixedSize(256, 256)
        self.cell_image_label.setStyleSheet("""
            QLabel {
                border: 2px dashed var(--border);
                border-radius: 8px;
                background-color: var(--muted);
                color: var(--muted-foreground);
                font-size: 12px;
            }
        """)
        self.cell_image_label.setScaledContents(True)
        
        # Navigation button
        self.navigate_button = BaseButton(
            text="Navigate to Cell",
            variant=ButtonVariant.DEFAULT,
            size=ButtonSize.DEFAULT
        )
        self.navigate_button.setEnabled(False)
        
        image_layout.addWidget(self.selected_cell_label)
        image_layout.addWidget(self.cell_image_label)
        image_layout.addWidget(self.navigate_button)
        image_layout.addStretch()
        
        splitter.addWidget(image_frame)
    
    def setup_action_buttons(self, parent_layout: QVBoxLayout) -> None:
        """Set up the action buttons."""
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)
        
        # Bulk actions
        self.select_all_button = BaseButton(
            text="Include All",
            variant=ButtonVariant.OUTLINE,
            size=ButtonSize.DEFAULT
        )
        
        self.exclude_all_button = BaseButton(
            text="Exclude All", 
            variant=ButtonVariant.OUTLINE,
            size=ButtonSize.DEFAULT
        )
        
        # Close button
        self.close_button = BaseButton(
            text="Close",
            variant=ButtonVariant.SECONDARY,
            size=ButtonSize.DEFAULT
        )
        
        buttons_layout.addWidget(self.select_all_button)
        buttons_layout.addWidget(self.exclude_all_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.close_button)
        
        parent_layout.addLayout(buttons_layout)
    
    def connect_signals(self) -> None:
        """Connect widget signals."""
        self.navigate_button.clicked.connect(self.on_navigate_clicked)
        self.select_all_button.clicked.connect(self.on_select_all_clicked)
        self.exclude_all_button.clicked.connect(self.on_exclude_all_clicked)
        self.close_button.clicked.connect(self.on_close_clicked)
    
    @error_handler("Loading row data")
    def load_row_data(self, row_data: CellRowData) -> None:
        """
        Load row data for cell management.
        
        Args:
            row_data: Row data containing selection and cell information
        """
        self.current_row_data = row_data
        
        # Update header
        self.selection_info_label.setText(
            f"Selection: {row_data.selection_label} ({len(row_data.cell_indices)} cells)"
        )
        
        # Clear existing cell items
        self.clear_cell_items()
        
        # Create cell items
        for cell_index in row_data.cell_indices:
            cell_metadata = row_data.cell_metadata.get(cell_index, {})
            cell_item = CellRowItem(cell_index, cell_metadata, is_included=True)
            
            # Connect signals
            cell_item.cell_toggled.connect(self.on_cell_toggled)
            cell_item.cell_selected.connect(self.on_cell_selected)
            
            # Add to layout (before stretch)
            self.cell_list_layout.insertWidget(
                self.cell_list_layout.count() - 1, 
                cell_item
            )
            self.cell_items.append(cell_item)
        
        # Update statistics
        self.update_statistics()
        
        self.log_info(f"Loaded row data: {row_data.selection_label} with {len(row_data.cell_indices)} cells")
    
    def clear_cell_items(self) -> None:
        """Clear all cell items."""
        for item in self.cell_items:
            item.deleteLater()
        
        self.cell_items.clear()
        self.selected_cell_index = None
        self.selected_cell_label.setText("No cell selected")
        self.cell_image_label.setText("Click a cell to view its image")
        self.cell_image_label.setPixmap(QPixmap())  # Clear image
        self.navigate_button.setEnabled(False)
    
    def update_statistics(self) -> None:
        """Update the statistics display."""
        if not self.current_row_data:
            return
        
        total_count = len(self.cell_items)
        included_count = sum(1 for item in self.cell_items if item.is_included)
        excluded_count = total_count - included_count
        
        self.total_cells_label.setText(f"Total: {total_count}")
        self.included_cells_label.setText(f"Included: {included_count}")
        self.excluded_cells_label.setText(f"Excluded: {excluded_count}")
    
    def on_cell_toggled(self, cell_index: int, is_included: bool) -> None:
        """Handle cell item inclusion toggle."""
        # Find the corresponding cell item and explicitly update its state.
        # This ensures the manager and the item are always in sync.
        for item in self.cell_items:
            if item.cell_index == cell_index:
                item.is_included = is_included
                item.update_appearance() # Visually reflect the change
                break
        
        self.update_statistics()
        
        # Emit signal for parent widget
        if self.current_row_data:
            self.cell_inclusion_changed.emit(
                self.current_row_data.selection_id, 
                cell_index, 
                is_included
            )
        
        status = "included" if is_included else "excluded"
        self.log_info(f"Cell {cell_index} {status}")
    
    def on_cell_selected(self, cell_index: int) -> None:
        """Handle cell selection."""
        # Update visual selection
        for item in self.cell_items:
            item.set_selected(item.cell_index == cell_index)
        
        self.selected_cell_index = cell_index
        
        # Update image panel
        self.selected_cell_label.setText(f"Cell {cell_index}")
        
        # Load and display cell image
        self.load_cell_image(cell_index)
        
        self.navigate_button.setEnabled(True)
        
        self.log_info(f"Cell {cell_index} selected")
    
    def _numpy_to_qpixmap(self, array: np.ndarray) -> QPixmap:
        """Convert a numpy array to a QPixmap."""
        if array is None:
            return QPixmap()

        # Handle different array types
        if array.dtype == np.uint8:
            if len(array.shape) == 2:  # Grayscale
                h, w = array.shape
                image = QImage(array.data, w, h, w, QImage.Format_Grayscale8)
            elif len(array.shape) == 3 and array.shape[2] == 3:  # RGB
                h, w, ch = array.shape
                image = QImage(array.data, w, h, w * ch, QImage.Format_RGB888)
            else:
                self.log_warning("Unsupported numpy array shape for QPixmap conversion.")
                return QPixmap()
        else:
            # Normalize and convert for other types (e.g., float)
            # Ensure array is not empty and has a max value > 0 to avoid division by zero
            if array.size > 0 and np.max(array) > 0:
                array = (array / np.max(array) * 255).astype(np.uint8)
            else:
                array = array.astype(np.uint8) # or return a blank image

            h, w = array.shape
            image = QImage(array.data, w, h, w, QImage.Format_Grayscale8)

        # Make a copy of the image data to avoid potential memory issues
        return QPixmap.fromImage(image.copy())


    def load_cell_image(self, cell_index: int) -> None:
        """Load and display the image for a specific cell."""
        if not self.image_handler or not self.current_row_data:
            self.cell_image_label.setText("Image Handler or data not available.")
            return

        try:
            pixel_coords = self.get_cell_coordinates(cell_index)

            if pixel_coords is None:
                self.cell_image_label.setText(f"No coordinates for cell {cell_index}")
                return
            
            pixel_x, pixel_y = pixel_coords

            # Get cropped image
            crop_size = 100  # pixels
            cropped_image_np = self.image_handler.get_image_region(
                int(pixel_x), int(pixel_y), crop_size, crop_size
            )

            if cropped_image_np is not None:
                pixmap = self._numpy_to_qpixmap(cropped_image_np)
                if not pixmap.isNull():
                    self.cell_image_label.setPixmap(pixmap.scaled(
                        self.cell_image_label.size(),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    ))
                else:
                    self.cell_image_label.setText(f"Could not display\nimage for cell {cell_index}")
            else:
                self.cell_image_label.setText(f"Could not load\nimage for cell {cell_index}")

        except Exception as e:
            self.log_error(f"Failed to load image for cell {cell_index}: {e}", exc_info=True)
            self.cell_image_label.setText(f"Error loading image\nfor cell {cell_index}")


    def _format_cell_properties(self, metadata: Dict[str, Any]) -> str:
        """Formats cell properties into a readable string."""
        if not metadata:
            return "No properties available for this cell"
        
        lines = [f"Cell Index: {self.selected_cell_index}"]
        lines.append("")
        
        for key, value in metadata.items():
            if isinstance(value, float):
                lines.append(f"{key.replace('_', ' ').title()}: {value:.2f}")
            else:
                lines.append(f"{key.replace('_', ' ').title()}: {value}")
        
        return "\n".join(lines)
    
    def on_navigate_clicked(self) -> None:
        """Handle navigate to cell click."""
        if self.selected_cell_index is not None:
            # 네비게이션은 변환된 좌표가 아닌 원본 CSV 인덱스를 사용해야 함
            # 메인 윈도우의 navigate_to_cell이 인덱스를 기반으로 좌표를 다시 계산
            self.cell_navigation_requested.emit(self.selected_cell_index)
            self.log_info(f"Navigation requested to cell {self.selected_cell_index}")
    
    def on_select_all_clicked(self) -> None:
        """Handle select all cells click."""
        for item in self.cell_items:
            if not item.is_included:
                item.inclusion_checkbox.setChecked(True)
        
        self.log_info("All cells included")
    
    def on_exclude_all_clicked(self) -> None:
        """Handle exclude all cells click."""
        for item in self.cell_items:
            if item.is_included:
                item.inclusion_checkbox.setChecked(False)
        
        self.log_info("All cells excluded")
    
    def get_cell_coordinates(self, cell_index: int) -> Optional[tuple[int, int]]:
        """Get transformed coordinates for a given cell index."""
        if not self.csv_parser:
            return None
            
        try:
            cell_data = self.csv_parser.get_data_by_index(cell_index)
            if cell_data is None: return None

            x_col, y_col = self.csv_parser.get_xy_columns()
            if not x_col or not y_col: return None

            raw_x, raw_y = int(cell_data[x_col]), int(cell_data[y_col])
            
            if self.coordinate_transformer and self.coordinate_transformer.is_calibrated():
                return self.coordinate_transformer.transform(raw_x, raw_y)
            
            return raw_x, raw_y
        except Exception as e:
            self.log_error(f"Error getting coordinates for cell {cell_index}: {e}")
            return None

    def on_close_clicked(self) -> None:
        """Handle close button click."""
        self.row_management_closed.emit()
        
        # 위젯을 실제로 닫거나 숨깁니다
        if self.parent():
            # 부모가 있으면 숨김
            self.hide()
        else:
            # 독립 위젯이면 닫음
            self.close()
        
        self.log_info("Row management closed")
    
    def get_included_cells(self) -> List[int]:
        """Get list of included cell indices."""
        return [item.cell_index for item in self.cell_items if item.is_included]
    
    def get_excluded_cells(self) -> List[int]:
        """Get list of excluded cell indices."""
        return [item.cell_index for item in self.cell_items if not item.is_included] 