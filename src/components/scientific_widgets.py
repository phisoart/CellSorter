"""
Scientific Widget Components for CellSorter

Based on the design specifications in docs/design/DESIGN_SYSTEM.md
Implements specialized widgets for scientific data visualization.
"""

from typing import Optional, List, Dict, Any, Callable
from PySide6.QtWidgets import (
    QWidget, QLabel, QGridLayout, QPushButton, QVBoxLayout,
    QHBoxLayout, QFrame
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPainter, QColor, QFont

from components.design_system import DesignTokens
from services.theme_manager import ThemeManager


class ScatterPlotWidget(QWidget):
    """
    Interactive scatter plot for cell data visualization.
    
    Based on the design specifications in DESIGN_SYSTEM.md
    """
    
    # Signals
    plot_created = Signal(str, str)  # x_column, y_column
    selection_made = Signal(list)    # selected_indices
    column_changed = Signal(str, str)  # axis, column_name
    
    PLOT_STYLES = {
        'background': 'var(--card)',
        'grid_color': 'var(--border)',
        'axis_color': 'var(--muted-foreground)',
        'selection_color': 'var(--primary)',
        'selection_alpha': 0.3,
    }
    
    POINT_STYLES = {
        'default': {'size': 3, 'alpha': 0.7},
        'selected': {'size': 4, 'alpha': 1.0, 'outline': True},
        'highlighted': {'size': 5, 'alpha': 1.0},
    }
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setProperty("role", "scatter-plot")
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the widget UI following design specifications."""
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # This is a placeholder - actual implementation would integrate
        # with the existing scatter_plot.py widget but apply design system styling
        placeholder = QLabel("Scatter Plot Widget")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet(f"""
            QLabel {{
                background-color: var(--muted);
                color: var(--muted-foreground);
                border: 1px solid var(--border);
                border-radius: {DesignTokens.RADIUS_LG}px;
                font-size: {DesignTokens.TEXT_LG}px;
                padding: {DesignTokens.SPACING_12}px;
            }}
        """)
        layout.addWidget(placeholder)


class ImageViewerWidget(QLabel):
    """
    Microscopy image viewer with overlay support.
    
    Based on the design specifications in DESIGN_SYSTEM.md
    """
    
    # Signals
    coordinates_changed = Signal(float, float)
    calibration_point_clicked = Signal(int, int, str)
    
    OVERLAY_STYLES = {
        'cell_boundary': {
            'color': 'var(--primary)',
            'width': 1,
            'style': 'solid',
        },
        'selection_highlight': {
            'color': 'var(--accent)',
            'width': 2,
            'fill_alpha': 0.2,
        },
        'calibration_point': {
            'color': 'var(--destructive)',
            'size': 8,
            'shape': 'cross',
        }
    }
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setProperty("role", "image-viewer")
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the widget UI following design specifications."""
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(f"""
            QLabel[role="image-viewer"] {{
                background-color: var(--card);
                border: 1px solid var(--border);
                border-radius: {DesignTokens.RADIUS_LG}px;
            }}
        """)
        
        # Placeholder text
        self.setText("Image Viewer")
        self.setMinimumSize(400, 300)


class WellPlateWidget(QWidget):
    """
    96-well plate visualization and selection.
    
    Based on the design specifications in DESIGN_SYSTEM.md
    """
    
    # Signals
    well_clicked = Signal(str)  # well_id (e.g., "A01")
    well_assigned = Signal(str, str)  # well_id, selection_id
    
    WELL_STYLES = {
        'empty': {
            'background': 'var(--muted)',
            'border': '1px solid var(--border)',
        },
        'assigned': {
            'background': 'var(--primary)',
            'color': 'var(--primary-foreground)',
        },
        'selected': {
            'border': '2px solid var(--ring)',
        }
    }
    
    LAYOUT = {
        'rows': 8,  # A-H
        'columns': 12,  # 01-12
        'well_size': 32,
        'spacing': 2,
    }
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.wells: Dict[str, QPushButton] = {}
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the 96-well plate layout."""
        self.setProperty("role", "well-plate")
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(
            DesignTokens.SPACING_4,
            DesignTokens.SPACING_4,
            DesignTokens.SPACING_4,
            DesignTokens.SPACING_4
        )
        
        # Create frame for the plate
        plate_frame = QFrame()
        plate_frame.setProperty("role", "well-plate-frame")
        plate_frame.setStyleSheet(f"""
            QFrame[role="well-plate-frame"] {{
                background-color: var(--card);
                border: 1px solid var(--border);
                border-radius: {DesignTokens.RADIUS_LG}px;
                padding: {DesignTokens.SPACING_4}px;
            }}
        """)
        
        # Grid layout for wells
        grid_layout = QGridLayout(plate_frame)
        grid_layout.setSpacing(self.LAYOUT['spacing'])
        
        # Add column labels (1-12)
        for col in range(self.LAYOUT['columns']):
            label = QLabel(f"{col + 1:02d}")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet(f"""
                QLabel {{
                    font-size: {DesignTokens.TEXT_XS}px;
                    font-weight: {DesignTokens.FONT_MEDIUM};
                    color: var(--muted-foreground);
                }}
            """)
            grid_layout.addWidget(label, 0, col + 1)
        
        # Add row labels (A-H) and wells
        for row in range(self.LAYOUT['rows']):
            # Row label
            row_label = QLabel(chr(65 + row))
            row_label.setAlignment(Qt.AlignCenter)
            row_label.setStyleSheet(f"""
                QLabel {{
                    font-size: {DesignTokens.TEXT_XS}px;
                    font-weight: {DesignTokens.FONT_MEDIUM};
                    color: var(--muted-foreground);
                }}
            """)
            grid_layout.addWidget(row_label, row + 1, 0)
            
            # Wells
            for col in range(self.LAYOUT['columns']):
                well_id = f"{chr(65 + row)}{col + 1:02d}"
                well_button = self._create_well_button(well_id)
                self.wells[well_id] = well_button
                grid_layout.addWidget(well_button, row + 1, col + 1)
        
        main_layout.addWidget(plate_frame)
        
    def _create_well_button(self, well_id: str) -> QPushButton:
        """Create a single well button."""
        button = QPushButton()
        button.setProperty("role", "well")
        button.setProperty("state", "empty")
        button.setFixedSize(QSize(self.LAYOUT['well_size'], self.LAYOUT['well_size']))
        button.setCursor(Qt.PointingHandCursor)
        
        # Styling
        button.setStyleSheet(f"""
            QPushButton[role="well"] {{
                border-radius: {self.LAYOUT['well_size'] // 2}px;
                font-size: {DesignTokens.TEXT_XS - 2}px;
                font-weight: {DesignTokens.FONT_SEMIBOLD};
            }}
            
            QPushButton[role="well"][state="empty"] {{
                background-color: var(--muted);
                color: var(--muted-foreground);
                border: 1px solid var(--border);
            }}
            
            QPushButton[role="well"][state="assigned"] {{
                background-color: var(--primary);
                color: var(--primary-foreground);
                border: 1px solid var(--primary);
            }}
            
            QPushButton[role="well"]:hover {{
                transform: scale(1.1);
            }}
        """)
        
        # Connect click signal
        button.clicked.connect(lambda: self.well_clicked.emit(well_id))
        
        return button
    
    def set_well_state(self, well_id: str, state: str, color: Optional[str] = None):
        """
        Set the state of a well.
        
        Args:
            well_id: Well identifier (e.g., "A01")
            state: State ("empty", "assigned", "selected")
            color: Optional color for assigned wells
        """
        if well_id in self.wells:
            button = self.wells[well_id]
            button.setProperty("state", state)
            
            if state == "assigned" and color:
                # Apply custom color if provided
                button.setStyleSheet(button.styleSheet() + f"""
                    QPushButton[role="well"][state="assigned"] {{
                        background-color: {color};
                    }}
                """)
            
            button.style().unpolish(button)
            button.style().polish(button)
    
    def get_empty_wells(self) -> List[str]:
        """Get list of empty wells."""
        empty_wells = []
        for well_id, button in self.wells.items():
            if button.property("state") == "empty":
                empty_wells.append(well_id)
        return empty_wells
    
    def clear_all_wells(self):
        """Clear all well assignments."""
        for well_id in self.wells:
            self.set_well_state(well_id, "empty")