"""
CellSorter Selection Panel Widget

Selection management panel with table view and well plate visualization.
"""

from typing import Optional, List, Dict, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QLabel, QCheckBox, QFrame, QSplitter,
    QComboBox, QLineEdit, QMessageBox, QSizePolicy
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor

from components.widgets.well_plate import WellPlateWidget
from components.base.base_button import BaseButton
from config.settings import BUTTON_HEIGHT, BUTTON_MIN_WIDTH, BUTTON_SPACING, COMPONENT_SPACING
from utils.logging_config import LoggerMixin
from utils.error_handler import error_handler


class SelectionPanel(QWidget, LoggerMixin):
    """
    Selection management panel with table and well plate views.
    
    Features:
    - Selection table with enable/disable checkboxes
    - Color and label editing
    - Well plate visualization and assignment
    - Export capabilities
    """
    
    # Signals
    selection_toggled = Signal(str, bool)  # selection_id, enabled
    selection_updated = Signal(str, dict)  # selection_id, updated_data
    selection_deleted = Signal(str)  # selection_id
    export_requested = Signal()  # Request export dialog
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # Data storage
        self.selections_data: Dict[str, Dict[str, Any]] = {}
        
        self.setup_ui()
        self.connect_signals()
        
        self.log_info("Selection panel initialized")
    
    def setup_ui(self) -> None:
        """Set up the panel UI with improved button layout and spacing."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)  # COMPONENT_SPACING equivalent
        layout.setContentsMargins(8, 8, 8, 8)  # PANEL_MARGIN equivalent
        
        # Title with better styling
        title_label = QLabel("Cell Selections")
        title_label.setStyleSheet("""
            font-weight: bold; 
            font-size: 14px; 
            margin-bottom: 8px;
            color: var(--foreground);
        """)
        layout.addWidget(title_label)
        
        # Create splitter for table and well plate
        splitter = QSplitter(Qt.Vertical)
        splitter.setChildrenCollapsible(False)
        
        # Selection table section
        table_frame = QFrame()
        table_frame.setFrameStyle(QFrame.StyledPanel)
        table_layout = QVBoxLayout(table_frame)
        table_layout.setSpacing(8)  # BUTTON_SPACING equivalent
        table_layout.setContentsMargins(8, 8, 8, 8)
        
        # Table header
        table_header = QLabel("Selections")
        table_header.setStyleSheet("font-weight: bold; margin-bottom: 4px;")
        table_layout.addWidget(table_header)
        
        # Selection table
        self.selection_table = QTableWidget()
        self.setup_table()
        table_layout.addWidget(self.selection_table)
        
        # Table buttons with improved layout
        table_buttons = QHBoxLayout()
        table_buttons.setSpacing(8)  # BUTTON_SPACING equivalent
        
        # Use consistent button sizing
        self.delete_button = QPushButton("Delete Selected")
        self.delete_button.setMinimumHeight(32)  # BUTTON_HEIGHT equivalent
        self.delete_button.setMinimumWidth(100)  # BUTTON_MIN_WIDTH equivalent
        self.delete_button.clicked.connect(self.delete_selected)
        self.delete_button.setEnabled(False)
        self.delete_button.setStyleSheet("""
            QPushButton {
                background-color: var(--destructive);
                color: var(--destructive-foreground);
                border: none;
                border-radius: 6px;
                padding: 4px 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: var(--destructive)/90;
            }
            QPushButton:disabled {
                opacity: 0.5;
            }
        """)
        
        self.clear_all_button = QPushButton("Clear All")
        self.clear_all_button.setMinimumHeight(32)
        self.clear_all_button.setMinimumWidth(100)
        self.clear_all_button.clicked.connect(self.clear_all_selections)
        self.clear_all_button.setStyleSheet("""
            QPushButton {
                background-color: var(--secondary);
                color: var(--secondary-foreground);
                border: 1px solid var(--border);
                border-radius: 6px;
                padding: 4px 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: var(--secondary)/80;
            }
        """)
        
        table_buttons.addWidget(self.delete_button)
        table_buttons.addWidget(self.clear_all_button)
        table_buttons.addStretch()  # Push buttons to the left
        
        table_layout.addLayout(table_buttons)
        
        # Well plate section
        well_frame = QFrame()
        well_frame.setFrameStyle(QFrame.StyledPanel)
        well_layout = QVBoxLayout(well_frame)
        well_layout.setSpacing(8)
        well_layout.setContentsMargins(8, 8, 8, 8)
        
        # Well plate header
        well_header = QLabel("96-Well Plate")
        well_header.setStyleSheet("font-weight: bold; margin-bottom: 4px;")
        well_layout.addWidget(well_header)
        
        # Well plate widget
        self.well_plate = WellPlateWidget()
        self.well_plate.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        well_layout.addWidget(self.well_plate)
        
        # Add sections to splitter with better proportions
        splitter.addWidget(table_frame)
        splitter.addWidget(well_frame)
        splitter.setSizes([250, 350])  # Adjust proportions
        splitter.setStretchFactor(0, 1)  # Table section can shrink
        splitter.setStretchFactor(1, 2)  # Well plate gets more priority
        
        layout.addWidget(splitter)
        
        # Export section with improved button layout
        export_frame = QFrame()
        export_frame.setFrameStyle(QFrame.StyledPanel)
        export_frame.setMaximumHeight(80)
        export_layout = QVBoxLayout(export_frame)
        export_layout.setContentsMargins(8, 8, 8, 8)
        
        export_label = QLabel("Export")
        export_label.setStyleSheet("font-weight: bold; margin-bottom: 4px;")
        export_layout.addWidget(export_label)
        
        export_buttons = QHBoxLayout()
        export_buttons.setSpacing(8)
        
        self.export_csv_button = QPushButton("Export CSV")
        self.export_csv_button.setMinimumHeight(32)
        self.export_csv_button.setMinimumWidth(100)
        self.export_csv_button.clicked.connect(self.export_csv)
        self.export_csv_button.setStyleSheet("""
            QPushButton {
                background-color: var(--primary);
                color: var(--primary-foreground);
                border: none;
                border-radius: 6px;
                padding: 4px 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: var(--primary)/90;
            }
        """)
        
        self.export_protocol_button = QPushButton("Export Protocol")
        self.export_protocol_button.setMinimumHeight(32)
        self.export_protocol_button.setMinimumWidth(120)
        self.export_protocol_button.clicked.connect(self.export_protocol)
        self.export_protocol_button.setStyleSheet("""
            QPushButton {
                background-color: var(--primary);
                color: var(--primary-foreground);
                border: none;
                border-radius: 6px;
                padding: 4px 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: var(--primary)/90;
            }
        """)
        
        export_buttons.addWidget(self.export_csv_button)
        export_buttons.addWidget(self.export_protocol_button)
        export_buttons.addStretch()  # Push buttons to the left
        
        export_layout.addLayout(export_buttons)
        
        layout.addWidget(export_frame)
    
    def setup_table(self) -> None:
        """Set up the selection table."""
        self.selection_table.setColumnCount(6)
        self.selection_table.setHorizontalHeaderLabels([
            "Enabled", "Label", "Color", "Well", "Cells", "Actions"
        ])
        
        # Set column widths
        header = self.selection_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # Enabled
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Label
        header.setSectionResizeMode(2, QHeaderView.Fixed)  # Color
        header.setSectionResizeMode(3, QHeaderView.Fixed)  # Well
        header.setSectionResizeMode(4, QHeaderView.Fixed)  # Cells
        
        # Set fixed column widths
        self.selection_table.setColumnWidth(0, 60)   # Enabled
        self.selection_table.setColumnWidth(2, 60)   # Color
        self.selection_table.setColumnWidth(3, 60)   # Well
        self.selection_table.setColumnWidth(4, 60)   # Cells
        
        # Table properties
        self.selection_table.setAlternatingRowColors(True)
        self.selection_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.selection_table.setSelectionMode(QTableWidget.SingleSelection)
    
    def connect_signals(self) -> None:
        """Connect widget signals."""
        self.selection_table.cellChanged.connect(self.on_table_cell_changed)
        self.selection_table.itemSelectionChanged.connect(self.on_table_selection_changed)
        self.well_plate.well_clicked.connect(self.on_well_clicked)
    
    @error_handler("Loading selections data")
    def load_selections(self, selections: List[Dict[str, Any]]) -> None:
        """
        Load selections data into the panel.
        
        Args:
            selections: List of selection data dictionaries
        """
        # Clear existing data
        self.selections_data.clear()
        self.selection_table.setRowCount(0)
        
        # Load new data
        for selection_data in selections:
            selection_id = selection_data.get('id', '')
            if selection_id:
                self.selections_data[selection_id] = selection_data.copy()
        
        # Update displays
        self.refresh_table()
        self.refresh_well_plate()
        
        self.log_info(f"Loaded {len(selections)} selections")
    
    def refresh_table(self) -> None:
        """Refresh the selection table display."""
        self.selection_table.setRowCount(len(self.selections_data))
        
        for row, (selection_id, data) in enumerate(self.selections_data.items()):
            # Enabled checkbox
            enabled_checkbox = QCheckBox()
            enabled_checkbox.setChecked(data.get('enabled', True))
            enabled_checkbox.stateChanged.connect(
                lambda state, sid=selection_id: self.on_enabled_changed(sid, state == Qt.Checked)
            )
            self.selection_table.setCellWidget(row, 0, enabled_checkbox)
            
            # Label (editable)
            label_item = QTableWidgetItem(data.get('label', ''))
            label_item.setData(Qt.UserRole, selection_id)
            self.selection_table.setItem(row, 1, label_item)
            
            # Color display
            color_frame = QFrame()
            color_frame.setFixedSize(40, 20)
            color_hex = data.get('color', '#FF0000')
            color_frame.setStyleSheet(f"background-color: {color_hex}; border: 1px solid black;")
            self.selection_table.setCellWidget(row, 2, color_frame)
            
            # Well position
            well_item = QTableWidgetItem(data.get('well_position', ''))
            well_item.setData(Qt.UserRole, selection_id)
            self.selection_table.setItem(row, 3, well_item)
            
            # Cell count
            cell_count = len(data.get('cell_indices', []))
            count_item = QTableWidgetItem(str(cell_count))
            count_item.setFlags(count_item.flags() & ~Qt.ItemIsEditable)  # Read-only
            self.selection_table.setItem(row, 4, count_item)
            
            # Actions (delete button)
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(
                lambda checked, sid=selection_id: self.delete_selection(sid)
            )
            self.selection_table.setCellWidget(row, 5, delete_btn)
    
    def refresh_well_plate(self) -> None:
        """Refresh the well plate display."""
        # Convert selections data for well plate
        well_assignments = {}
        for selection_id, data in self.selections_data.items():
            well_position = data.get('well_position', '')
            if well_position and data.get('enabled', True):
                well_assignments[well_position] = {
                    'selection_id': selection_id,
                    'color': data.get('color', '#FF0000'),
                    'label': data.get('label', 'Unknown')
                }
        
        self.well_plate.set_well_assignments(well_assignments)
    
    def on_enabled_changed(self, selection_id: str, enabled: bool) -> None:
        """Handle selection enabled/disabled."""
        if selection_id in self.selections_data:
            self.selections_data[selection_id]['enabled'] = enabled
            self.refresh_well_plate()  # Update well plate display
            self.selection_toggled.emit(selection_id, enabled)
            self.log_info(f"Selection {selection_id} {'enabled' if enabled else 'disabled'}")
    
    def on_table_cell_changed(self, row: int, column: int) -> None:
        """Handle table cell changes."""
        if column == 1:  # Label column
            item = self.selection_table.item(row, column)
            if item:
                selection_id = item.data(Qt.UserRole)
                new_label = item.text()
                if selection_id in self.selections_data:
                    self.selections_data[selection_id]['label'] = new_label
                    self.refresh_well_plate()
                    self.selection_updated.emit(selection_id, {'label': new_label})
                    self.log_info(f"Updated label for selection {selection_id}: {new_label}")
        
        elif column == 3:  # Well position column
            item = self.selection_table.item(row, column)
            if item:
                selection_id = item.data(Qt.UserRole)
                new_well = item.text()
                if selection_id in self.selections_data:
                    self.selections_data[selection_id]['well_position'] = new_well
                    self.refresh_well_plate()
                    self.selection_updated.emit(selection_id, {'well_position': new_well})
                    self.log_info(f"Updated well for selection {selection_id}: {new_well}")
    
    def on_table_selection_changed(self) -> None:
        """Handle table selection changes."""
        selected_rows = self.selection_table.selectionModel().selectedRows()
        self.delete_button.setEnabled(len(selected_rows) > 0)
    
    def on_well_clicked(self, well_position: str) -> None:
        """Handle well plate clicks."""
        self.log_info(f"Well {well_position} clicked")
        # Could implement well assignment dialog here
    
    def delete_selected(self) -> None:
        """Delete selected table rows."""
        selected_rows = self.selection_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        # Get selection IDs to delete
        selection_ids = []
        for index in selected_rows:
            row = index.row()
            label_item = self.selection_table.item(row, 1)
            if label_item:
                selection_id = label_item.data(Qt.UserRole)
                selection_ids.append(selection_id)
        
        # Confirm deletion
        if len(selection_ids) == 1:
            msg = f"Delete selection '{self.selections_data[selection_ids[0]]['label']}'?"
        else:
            msg = f"Delete {len(selection_ids)} selections?"
        
        reply = QMessageBox.question(
            self, "Confirm Deletion", msg,
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            for selection_id in selection_ids:
                self.delete_selection(selection_id)
    
    def delete_selection(self, selection_id: str) -> None:
        """Delete a specific selection."""
        if selection_id in self.selections_data:
            del self.selections_data[selection_id]
            self.refresh_table()
            self.refresh_well_plate()
            self.selection_deleted.emit(selection_id)
            self.log_info(f"Deleted selection {selection_id}")
    
    def clear_all_selections(self) -> None:
        """Clear all selections."""
        reply = QMessageBox.question(
            self, "Confirm Clear All", "Clear all selections?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            selection_ids = list(self.selections_data.keys())
            self.selections_data.clear()
            self.refresh_table()
            self.refresh_well_plate()
            
            for selection_id in selection_ids:
                self.selection_deleted.emit(selection_id)
            
            self.log_info("Cleared all selections")
    
    def export_csv(self) -> None:
        """Export selections as CSV."""
        from PySide6.QtWidgets import QFileDialog
        import csv
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Selections CSV", "selections.csv", "CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # Write header
                    writer.writerow(['Selection ID', 'Label', 'Color', 'Well Position', 'Cell Count', 'Cell Indices'])
                    
                    # Write data
                    for selection_id, data in self.selections_data.items():
                        if data.get('enabled', True):
                            writer.writerow([
                                selection_id,
                                data.get('label', ''),
                                data.get('color', ''),
                                data.get('well_position', ''),
                                len(data.get('cell_indices', [])),
                                ';'.join(map(str, data.get('cell_indices', [])))
                            ])
                
                self.log_info(f"Exported selections to {file_path}")
                QMessageBox.information(self, "Export Complete", f"Selections exported to {file_path}")
                
            except Exception as e:
                self.log_error(f"Failed to export CSV: {e}")
                QMessageBox.critical(self, "Export Error", f"Failed to export CSV: {e}")
    
    def export_protocol(self) -> None:
        """Request protocol export."""
        self.export_requested.emit()
    
    def add_selection(self, selection_data: Dict[str, Any]) -> None:
        """
        Add a new selection to the panel.
        
        Args:
            selection_data: Selection data dictionary
        """
        selection_id = selection_data.get('id', '')
        if selection_id:
            self.selections_data[selection_id] = selection_data.copy()
            self.refresh_table()
            self.refresh_well_plate()
            self.log_info(f"Added selection {selection_id}")
    
    def update_selection(self, selection_id: str, data: Dict[str, Any]) -> None:
        """
        Update an existing selection.
        
        Args:
            selection_id: Selection identifier
            data: Updated data
        """
        if selection_id in self.selections_data:
            self.selections_data[selection_id].update(data)
            self.refresh_table()
            self.refresh_well_plate()
            self.log_info(f"Updated selection {selection_id}")
    
    def get_active_selections(self) -> List[Dict[str, Any]]:
        """
        Get list of active (enabled) selections.
        
        Returns:
            List of active selection data
        """
        return [
            data for data in self.selections_data.values()
            if data.get('enabled', True)
        ]