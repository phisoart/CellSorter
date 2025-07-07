"""
ROI Management Dialog for CellSorter

A modal dialog that wraps the RowCellManager component to provide
dedicated cell management functionality in a dialog format.
"""

from typing import Optional, Dict, Any
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFrame, QWidget
)
from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtGui import QKeyEvent

from components.widgets.row_cell_manager import RowCellManager, CellRowData
from utils.logging_config import LoggerMixin
from utils.error_handler import error_handler


class ROIManagementDialog(QDialog, LoggerMixin):
    """
    ROI Management Dialog for individual cell management.
    
    Provides a modal interface for:
    - Viewing all cells in a selected row/selection
    - Including/excluding specific cells via checkboxes
    - Navigating to cells in the main image view
    - Managing cell selection state
    
    Features:
    - Modal dialog with proper focus management
    - Embedded RowCellManager component
    - Confirm/Cancel button functionality
    - Signal forwarding for cell operations
    """
    
    # Signals
    cell_inclusion_changed = Signal(str, int, bool)  # selection_id, cell_index, is_included
    cell_navigation_requested = Signal(int)  # cell_index for main image navigation
    changes_confirmed = Signal(str, dict)  # selection_id, changes_data
    
    def __init__(self, parent: Optional[QWidget] = None, row_data: Optional[CellRowData] = None):
        super().__init__(parent)
        
        self.row_data = row_data
        self.initial_states: Dict[int, bool] = {}
        self.changes_made = False
        
        self.setup_dialog_properties()
        self.setup_ui()
        self.connect_signals()
        
        if row_data:
            self.load_row_data(row_data)
        
        self.log_info(f"ROI Management Dialog initialized for {row_data.selection_id if row_data else 'unknown'}")
    
    def setup_dialog_properties(self) -> None:
        """Configure dialog properties and appearance."""
        self.setModal(True)
        self.setWindowTitle("Manage ROIs")
        self.resize(900, 700)  # Optimal size for cell management
        
        # Set dialog styling following CellSorter design system
        self.setStyleSheet("""
            QDialog {
                background-color: var(--background);
                border-radius: 12px;
            }
        """)
    
    def setup_ui(self) -> None:
        """Set up the dialog user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(24, 24, 24, 24)
        
        # Header section
        self.setup_header(main_layout)
        
        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("""
            QFrame {
                color: var(--border);
                margin: 8px 0;
            }
        """)
        main_layout.addWidget(separator)
        
        # Cell management content area
        self.setup_content_area(main_layout)
        
        # Dialog buttons
        self.setup_dialog_buttons(main_layout)
    
    def setup_header(self, parent_layout: QVBoxLayout) -> None:
        """Set up the dialog header with title and row information."""
        header_layout = QVBoxLayout()
        header_layout.setSpacing(8)
        
        # Main title
        self.title_label = QLabel("Manage ROIs")
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: 600;
                color: var(--foreground);
                margin-bottom: 8px;
            }
        """)
        self.title_label.setAlignment(Qt.AlignCenter)
        
        # Row subtitle (will be updated when data loads)
        self.subtitle_label = QLabel("Select a row to manage its cells")
        self.subtitle_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: var(--muted-foreground);
                margin-bottom: 16px;
            }
        """)
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        
        header_layout.addWidget(self.title_label)
        header_layout.addWidget(self.subtitle_label)
        
        parent_layout.addLayout(header_layout)
    
    def setup_content_area(self, parent_layout: QVBoxLayout) -> None:
        """Set up the main content area with the RowCellManager component."""
        # Create and embed the RowCellManager
        self.cell_manager = RowCellManager()
        
        # Style the cell manager to fit dialog context
        self.cell_manager.setStyleSheet("""
            RowCellManager {
                background-color: var(--card);
                border: 1px solid var(--border);
                border-radius: 8px;
                padding: 16px;
            }
        """)
        
        parent_layout.addWidget(self.cell_manager)
    
    def setup_dialog_buttons(self, parent_layout: QVBoxLayout) -> None:
        """Set up the dialog action buttons (Cancel/Confirm)."""
        # Add some space before buttons
        parent_layout.addSpacing(16)
        
        # Button container
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(16)
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setFixedSize(120, 40)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: var(--secondary);
                color: var(--secondary-foreground);
                border: 1px solid var(--border);
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: var(--secondary)/80;
                border-color: var(--ring);
            }
            QPushButton:pressed {
                background-color: var(--secondary)/70;
            }
        """)
        
        # Confirm button
        self.confirm_button = QPushButton("Confirm")
        self.confirm_button.setFixedSize(120, 40)
        self.confirm_button.setDefault(True)
        self.confirm_button.setStyleSheet("""
            QPushButton {
                background-color: var(--primary);
                color: var(--primary-foreground);
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: var(--primary)/90;
            }
            QPushButton:pressed {
                background-color: var(--primary)/80;
            }
            QPushButton:default {
                border: 2px solid var(--ring);
            }
        """)
        
        self.confirm_button.setEnabled(False)  # Initially disabled
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.confirm_button)
        
        # Add stretch to right-align buttons
        button_layout.addStretch()
        
        parent_layout.addWidget(button_container)
    
    def connect_signals(self) -> None:
        """Connect internal signals and slots."""
        # Button connections
        self.cancel_button.clicked.connect(self.on_cancel_clicked)
        self.confirm_button.clicked.connect(self.on_confirm_clicked)
        
        # Cell manager signal forwarding
        if hasattr(self, 'cell_manager'):
            self.cell_manager.cell_inclusion_changed.connect(self.on_cell_inclusion_changed)
            self.cell_manager.cell_navigation_requested.connect(self.on_cell_navigation_requested)
    
    @error_handler("Loading row data")
    def load_row_data(self, row_data: CellRowData) -> None:
        """Load row data into the dialog."""
        self.row_data = row_data
        
        # Update header with row information
        self.subtitle_label.setText(
            f'Row: {row_data.selection_label} • '
            f'{len(row_data.cell_indices)} cells • '
            f'Color: {row_data.selection_color}'
        )
        
        # Store initial cell states for change tracking
        self.initial_states = {}
        for cell_index in row_data.cell_indices:
            self.initial_states[cell_index] = True  # Default to included
        
        # Load data into cell manager
        self.cell_manager.load_row_data(row_data)
        
        # After loading, manually check for initial state consistency
        self.changes_made = self._has_changes_from_initial()
        self.confirm_button.setEnabled(self.changes_made)
        
        self.log_info(f"Loaded row data: {row_data.selection_label} with {len(row_data.cell_indices)} cells")
    
    def on_cell_inclusion_changed(self, selection_id: str, cell_index: int, is_included: bool) -> None:
        """Handle cell inclusion state changes."""
        # Forward the signal first
        self.cell_inclusion_changed.emit(selection_id, cell_index, is_included)
        
        # Then, update the change state. Schedule with a single shot timer 
        # to ensure the cell_manager's internal state has updated before we check it.
        QTimer.singleShot(0, self._update_change_state)
        
        self.log_info(f"Cell {cell_index} inclusion changed: {is_included}")
    
    def _update_change_state(self):
        """Update the changes_made flag and button state."""
        self.changes_made = self._has_changes_from_initial()
        self.confirm_button.setEnabled(self.changes_made)
    
    def on_cell_navigation_requested(self, cell_index: int) -> None:
        """Handle cell navigation requests."""
        self.cell_navigation_requested.emit(cell_index)
        self.log_info(f"Navigation requested for cell {cell_index}")
    
    def _has_changes_from_initial(self) -> bool:
        """Check if any cells have been changed from their initial state."""
        if not hasattr(self.cell_manager, 'cell_items') or not self.cell_manager.cell_items:
            return False

        for cell_item in self.cell_manager.cell_items:
            cell_index = cell_item.cell_index
            if cell_index in self.initial_states:
                initial_state = self.initial_states[cell_index]
                if initial_state != cell_item.is_included:
                    return True # A change was found
        return False # No changes found
    
    def on_cancel_clicked(self) -> None:
        """Handle cancel button click."""
        self.log_info("ROI Management Dialog cancelled")
        self.reject()
    
    def on_confirm_clicked(self) -> None:
        """Handle confirm button click."""
        if self.row_data:
            changes_data = self.get_cell_states()
            # Ensure the final 'changes_made' status is accurate
            changes_data['changes_made'] = self._has_changes_from_initial()
            
            self.changes_confirmed.emit(self.row_data.selection_id, changes_data)
            self.log_info(f"ROI Management confirmed: {len(changes_data['included_cells'])} included, {len(changes_data['excluded_cells'])} excluded")
            self.accept()
        else:
            self.log_warning("Confirm clicked with no row data.")
            self.reject()
    
    def get_cell_states(self) -> Dict[str, Any]:
        """Get the current states of cells in the dialog."""
        if not self.row_data:
            return {}
        
        states = {}
        if self.row_data:
            states['selection_id'] = self.row_data.selection_id
            states['included_cells'] = self.cell_manager.get_included_cells()
            states['excluded_cells'] = self.cell_manager.get_excluded_cells()
        
        states['changes_made'] = self.changes_made
        return states
    
    def closeEvent(self, event) -> None:
        """Handle dialog close event."""
        self.log_info("ROI Management Dialog closed")
        super().closeEvent(event)
    
    def keyPressEvent(self, event) -> None:
        """Handle keyboard events."""
        if event.key() == Qt.Key_Escape:
            self.on_cancel_clicked()
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            # Only confirm on Enter if confirm button has focus or no specific focus
            focused_widget = self.focusWidget()
            if focused_widget is None or focused_widget == self.confirm_button:
                self.on_confirm_clicked()
        else:
            super().keyPressEvent(event)


# Convenience function for dialog usage
def show_roi_management_dialog(parent: Optional[QWidget] = None, 
                             row_data: Optional[CellRowData] = None) -> Optional[Dict[str, Any]]:
    """
    Show the ROI Management Dialog and return the result.
    
    Args:
        parent: Parent widget
        row_data: CellRowData to manage
    
    Returns:
        Dictionary with cell states if accepted, None if cancelled
    """
    dialog = ROIManagementDialog(parent, row_data)
    
    if dialog.exec() == QDialog.Accepted:
        return dialog.get_cell_states()
    
    return None 