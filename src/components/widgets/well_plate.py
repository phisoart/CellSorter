"""
CellSorter Well Plate Widget

96-well plate visualization widget with color-coded wells and click-to-select functionality.
"""

from typing import Optional, Dict, Any, List, Tuple
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PySide6.QtCore import Signal, Qt, QRect
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QMouseEvent

from utils.logging_config import LoggerMixin
from utils.error_handler import error_handler


class WellPlateWidget(QWidget, LoggerMixin):
    """
    96-well plate visualization widget.
    
    Features:
    - Standard 96-well plate layout (8x12)
    - Color-coded wells matching selection colors
    - Click-to-select well functionality
    - Export well plate map as image
    """
    
    # Signals
    well_clicked = Signal(str)  # well_position
    well_assignment_changed = Signal(str, str)  # old_well, new_well
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # Well plate configuration
        self.rows = 8  # A-H
        self.cols = 12  # 1-12
        self.row_labels = list("ABCDEFGH")
        self.col_labels = [f"{i:02d}" for i in range(1, 13)]
        
        # Well data storage
        self.well_assignments: Dict[str, Dict[str, Any]] = {}  # well_position -> {color, label, selection_id}
        self.selected_well: Optional[str] = None
        
        # Visual configuration
        self.well_size = 35
        self.well_spacing = 40
        self.margin = 30
        self.label_size = 20
        
        # Colors
        self.empty_well_color = QColor(240, 240, 240)  # Light gray
        self.border_color = QColor(100, 100, 100)  # Dark gray
        self.selected_border_color = QColor(0, 0, 255)  # Blue
        self.text_color = QColor(0, 0, 0)  # Black
        
        self.setup_ui()
        
        self.log_info("Well plate widget initialized")
    
    def setup_ui(self) -> None:
        """Set up the widget UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("96-Well Plate Layout")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; margin: 5px;")
        layout.addWidget(title_label)
        
        # Calculate widget size
        plate_width = self.margin * 2 + self.label_size + self.cols * self.well_spacing
        plate_height = self.margin * 2 + self.label_size + self.rows * self.well_spacing
        
        self.setMinimumSize(plate_width, plate_height)
        self.setMaximumSize(plate_width, plate_height)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.clear_button = QPushButton("Clear All")
        self.clear_button.clicked.connect(self.clear_all_wells)
        
        self.export_button = QPushButton("Export Image")
        self.export_button.clicked.connect(self.export_plate_image)
        
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.export_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
    
    def paintEvent(self, event) -> None:
        """Paint the well plate."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Set font
        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        
        # Draw row labels (A-H)
        for i, label in enumerate(self.row_labels):
            x = self.margin
            y = self.margin + self.label_size + i * self.well_spacing + self.well_size // 2
            painter.setPen(self.text_color)
            painter.drawText(x, y, label)
        
        # Draw column labels (01-12)
        for j, label in enumerate(self.col_labels):
            x = self.margin + self.label_size + j * self.well_spacing + self.well_size // 2 - 8
            y = self.margin + 15
            painter.setPen(self.text_color)
            painter.drawText(x, y, label)
        
        # Draw wells
        for i in range(self.rows):
            for j in range(self.cols):
                well_position = f"{self.row_labels[i]}{self.col_labels[j]}"
                self._draw_well(painter, i, j, well_position)
    
    def _draw_well(self, painter: QPainter, row: int, col: int, well_position: str) -> None:
        """
        Draw a single well.
        
        Args:
            painter: QPainter instance
            row: Row index
            col: Column index
            well_position: Well position string (e.g., "A01")
        """
        # Calculate position
        x = self.margin + self.label_size + col * self.well_spacing
        y = self.margin + self.label_size + row * self.well_spacing
        
        # Get well data
        well_data = self.well_assignments.get(well_position, {})
        
        # Determine colors
        if well_data:
            # Well has assignment - use selection color
            color_hex = well_data.get('color', '#FF0000')
            if color_hex.startswith('#'):
                color_val = int(color_hex[1:], 16)
                r = (color_val >> 16) & 255
                g = (color_val >> 8) & 255
                b = color_val & 255
                well_color = QColor(r, g, b, 180)  # Semi-transparent
            else:
                well_color = QColor(255, 0, 0, 180)  # Default red
        else:
            # Empty well
            well_color = self.empty_well_color
        
        # Determine border color
        if well_position == self.selected_well:
            border_color = self.selected_border_color
            border_width = 3
        else:
            border_color = self.border_color
            border_width = 1
        
        # Draw well circle
        painter.setBrush(QBrush(well_color))
        painter.setPen(QPen(border_color, border_width))
        
        well_rect = QRect(x, y, self.well_size, self.well_size)
        painter.drawEllipse(well_rect)
        
        # Draw well label if assigned
        if well_data and well_data.get('label'):
            painter.setPen(QPen(self.text_color))
            # Use smaller font for well labels
            small_font = QFont()
            small_font.setPointSize(6)
            painter.setFont(small_font)
            
            label = well_data['label'][:6]  # Truncate if too long
            text_rect = QRect(x, y + self.well_size + 2, self.well_size, 12)
            painter.drawText(text_rect, Qt.AlignCenter, label)
            
            # Restore normal font
            normal_font = QFont()
            normal_font.setPointSize(10)
            painter.setFont(normal_font)
    
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse clicks on wells."""
        if event.button() == Qt.LeftButton:
            well_position = self._get_well_at_position(event.pos())
            if well_position:
                self.selected_well = well_position
                self.well_clicked.emit(well_position)
                self.update()  # Redraw to show selection
                self.log_info(f"Well {well_position} clicked")
    
    def _get_well_at_position(self, pos) -> Optional[str]:
        """
        Get well position from mouse coordinates.
        
        Args:
            pos: Mouse position (QPoint)
        
        Returns:
            Well position string or None
        """
        x = pos.x()
        y = pos.y()
        
        # Check if click is in well area
        for i in range(self.rows):
            for j in range(self.cols):
                well_x = self.margin + self.label_size + j * self.well_spacing
                well_y = self.margin + self.label_size + i * self.well_spacing
                
                # Check if click is within well bounds
                if (well_x <= x <= well_x + self.well_size and 
                    well_y <= y <= well_y + self.well_size):
                    return f"{self.row_labels[i]}{self.col_labels[j]}"
        
        return None
    
    @error_handler("Assigning well")
    def assign_well(self, well_position: str, selection_id: str, 
                   color: str, label: str) -> bool:
        """
        Assign a selection to a well.
        
        Args:
            well_position: Well position (e.g., "A01")
            selection_id: Selection identifier
            color: Selection color
            label: Selection label
        
        Returns:
            True if successful, False otherwise
        """
        if well_position not in [f"{r}{c}" for r in self.row_labels for c in self.col_labels]:
            self.log_warning(f"Invalid well position: {well_position}")
            return False
        
        # Check if well is already assigned
        if well_position in self.well_assignments:
            old_assignment = self.well_assignments[well_position]
            self.log_info(f"Well {well_position} reassigned from {old_assignment['label']} to {label}")
        
        # Assign well
        self.well_assignments[well_position] = {
            'selection_id': selection_id,
            'color': color,
            'label': label
        }
        
        self.update()  # Redraw
        self.log_info(f"Assigned well {well_position} to selection {label}")
        return True
    
    def unassign_well(self, well_position: str) -> bool:
        """
        Remove assignment from a well.
        
        Args:
            well_position: Well position
        
        Returns:
            True if successful, False otherwise
        """
        if well_position in self.well_assignments:
            del self.well_assignments[well_position]
            self.update()
            self.log_info(f"Unassigned well {well_position}")
            return True
        return False
    
    def clear_all_wells(self) -> None:
        """Clear all well assignments."""
        self.well_assignments.clear()
        self.selected_well = None
        self.update()
        self.log_info("Cleared all well assignments")
    
    def get_well_assignments(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all well assignments.
        
        Returns:
            Dictionary of well assignments
        """
        return self.well_assignments.copy()
    
    def set_well_assignments(self, assignments: Dict[str, Dict[str, Any]]) -> None:
        """
        Set well assignments from data.
        
        Args:
            assignments: Well assignment data
        """
        self.well_assignments = assignments.copy()
        self.update()
        self.log_info(f"Set {len(assignments)} well assignments")
    
    def get_assigned_wells(self) -> List[str]:
        """
        Get list of assigned well positions.
        
        Returns:
            List of well position strings
        """
        return list(self.well_assignments.keys())
    
    def get_available_wells(self) -> List[str]:
        """
        Get list of available (unassigned) well positions.
        
        Returns:
            List of available well position strings
        """
        all_wells = [f"{r}{c}" for r in self.row_labels for c in self.col_labels]
        assigned = set(self.well_assignments.keys())
        return [w for w in all_wells if w not in assigned]
    
    def export_plate_image(self) -> bool:
        """
        Export the well plate as an image.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            from PySide6.QtWidgets import QFileDialog
            from PySide6.QtGui import QPixmap
            
            # Get save location
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Well Plate Image",
                "well_plate.png",
                "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)"
            )
            
            if not file_path:
                return False
            
            # Create pixmap and render widget
            pixmap = QPixmap(self.size())
            pixmap.fill(Qt.white)
            
            painter = QPainter(pixmap)
            self.render(painter)
            painter.end()
            
            # Save image
            success = pixmap.save(file_path)
            
            if success:
                self.log_info(f"Exported well plate image to {file_path}")
            else:
                self.log_error(f"Failed to export well plate image to {file_path}")
            
            return success
            
        except Exception as e:
            self.log_error(f"Error exporting well plate image: {e}")
            return False
    
    def update_selection_assignments(self, selections: List[Dict[str, Any]]) -> None:
        """
        Update well assignments from selection data.
        
        Args:
            selections: List of selection dictionaries with well_position, color, label
        """
        # Clear existing assignments
        self.well_assignments.clear()
        
        # Add new assignments
        for selection in selections:
            well_position = selection.get('well_position', '')
            if well_position:
                self.assign_well(
                    well_position,
                    selection.get('id', ''),
                    selection.get('color', '#FF0000'),
                    selection.get('label', 'Unknown')
                )
        
        self.log_info(f"Updated well assignments from {len(selections)} selections")