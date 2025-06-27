"""
Template Management Dialog for CellSorter (TASK-021)

Provides a comprehensive interface for managing analysis templates including
selection criteria, calibration settings, well plate configurations, and
complete workflow templates.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QTabWidget,
    QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem,
    QTextEdit, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QPushButton, QLabel, QFrame, QGroupBox, QFormLayout,
    QCheckBox, QMessageBox, QFileDialog, QProgressBar,
    QSplitter, QStackedWidget, QScrollArea, QGridLayout
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QIcon, QFont, QPixmap

from models.template_manager import (
    TemplateManager, TemplateType, TemplateStatus,
    SelectionTemplate, CalibrationTemplate, WellPlateTemplate, WorkflowTemplate
)
from components.base.base_button import BaseButton
from components.base.base_card import BaseCard
from components.base.base_input import BaseInput
from utils.logging_config import LoggerMixin
from utils.error_handler import error_handler


class TemplateLibraryWidget(QWidget, LoggerMixin):
    """Widget for browsing and managing template library."""
    
    template_selected = Signal(str, str)  # template_type, template_id
    template_applied = Signal(str, str)   # template_type, template_id
    
    def __init__(self, template_manager: TemplateManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.template_manager = template_manager
        self.setup_ui()
        self.connect_signals()
        self.refresh_templates()
    
    def setup_ui(self) -> None:
        """Setup the library widget UI."""
        layout = QVBoxLayout(self)
        
        # Search and filter section
        filter_layout = QHBoxLayout()
        
        self.search_input = BaseInput()
        self.search_input.setPlaceholderText("Search templates...")
        filter_layout.addWidget(QLabel("Search:"))
        filter_layout.addWidget(self.search_input)
        
        self.type_filter = QComboBox()
        self.type_filter.addItem("All Types", "")
        for template_type in TemplateType:
            self.type_filter.addItem(template_type.value.replace("_", " ").title(), template_type.value)
        filter_layout.addWidget(QLabel("Type:"))
        filter_layout.addWidget(self.type_filter)
        
        layout.addLayout(filter_layout)
        
        # Template tree view
        self.template_tree = QTreeWidget()
        self.template_tree.setHeaderLabels([
            "Name", "Type", "Status", "Author", "Created", "Used"
        ])
        self.template_tree.setAlternatingRowColors(True)
        layout.addWidget(self.template_tree)
        
        # Template details section
        details_frame = QFrame()
        details_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        details_layout = QVBoxLayout(details_frame)
        
        self.template_name_label = QLabel("Select a template to view details")
        self.template_name_label.setFont(QFont("", 12, QFont.Weight.Bold))
        details_layout.addWidget(self.template_name_label)
        
        self.template_description = QTextEdit()
        self.template_description.setMaximumHeight(100)
        self.template_description.setReadOnly(True)
        details_layout.addWidget(self.template_description)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.apply_button = BaseButton("Apply Template")
        self.apply_button.setEnabled(False)
        button_layout.addWidget(self.apply_button)
        
        self.delete_button = BaseButton("Delete")
        self.delete_button.setEnabled(False)
        button_layout.addWidget(self.delete_button)
        
        button_layout.addStretch()
        
        details_layout.addLayout(button_layout)
        layout.addWidget(details_frame)
    
    def connect_signals(self) -> None:
        """Connect widget signals."""
        self.search_input.textChanged.connect(self.filter_templates)
        self.type_filter.currentTextChanged.connect(self.filter_templates)
        
        self.template_tree.itemSelectionChanged.connect(self.on_template_selected)
        self.template_tree.itemDoubleClicked.connect(self.on_template_double_clicked)
        
        self.apply_button.clicked.connect(self.apply_selected_template)
        self.delete_button.clicked.connect(self.delete_selected_template)
        
        # Template manager signals
        self.template_manager.template_created.connect(self.refresh_templates)
        self.template_manager.template_updated.connect(self.refresh_templates)
        self.template_manager.template_deleted.connect(self.refresh_templates)
    
    def refresh_templates(self) -> None:
        """Refresh the template list."""
        self.template_tree.clear()
        
        for template_type in TemplateType:
            if template_type == TemplateType.EXPRESSION:
                continue  # Skip for now
            
            templates = self.template_manager.get_templates_by_type(template_type)
            
            if templates:
                # Create type group
                type_item = QTreeWidgetItem(self.template_tree)
                type_item.setText(0, template_type.value.replace("_", " ").title())
                type_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "group", "template_type": template_type})
                
                # Add templates
                for template in templates:
                    template_item = QTreeWidgetItem(type_item)
                    template_item.setText(0, template.metadata.name)
                    template_item.setText(1, template_type.value)
                    template_item.setText(2, template.metadata.status.value)
                    template_item.setText(3, template.metadata.author)
                    template_item.setText(4, template.metadata.created_date.split('T')[0])
                    template_item.setText(5, str(template.metadata.usage_count))
                    
                    template_item.setData(0, Qt.ItemDataRole.UserRole, {
                        "type": "template",
                        "template_type": template_type,
                        "template_id": template.metadata.id,
                        "template": template
                    })
        
        self.template_tree.expandAll()
        self.filter_templates()
    
    def filter_templates(self) -> None:
        """Filter templates based on search and filter criteria."""
        search_text = self.search_input.text().lower()
        type_filter = self.type_filter.currentData()
        
        for i in range(self.template_tree.topLevelItemCount()):
            type_item = self.template_tree.topLevelItem(i)
            type_data = type_item.data(0, Qt.ItemDataRole.UserRole)
            
            # Check type filter
            if type_filter and type_data.get("template_type", "").value != type_filter:
                type_item.setHidden(True)
                continue
            
            visible_children = 0
            
            for j in range(type_item.childCount()):
                template_item = type_item.child(j)
                template_data = template_item.data(0, Qt.ItemDataRole.UserRole)
                template = template_data.get("template")
                
                if not template:
                    continue
                
                # Apply filters
                show_item = True
                
                # Search filter
                if search_text:
                    searchable_text = (
                        f"{template.metadata.name} "
                        f"{template.metadata.description} "
                        f"{' '.join(template.metadata.tags)}"
                    ).lower()
                    
                    if search_text not in searchable_text:
                        show_item = False
                
                template_item.setHidden(not show_item)
                if show_item:
                    visible_children += 1
            
            # Hide type group if no visible children
            type_item.setHidden(visible_children == 0)
    
    def on_template_selected(self) -> None:
        """Handle template selection."""
        current_item = self.template_tree.currentItem()
        
        if not current_item:
            self.clear_details()
            return
        
        item_data = current_item.data(0, Qt.ItemDataRole.UserRole)
        
        if item_data.get("type") != "template":
            self.clear_details()
            return
        
        template = item_data.get("template")
        if not template:
            self.clear_details()
            return
        
        # Update details
        self.template_name_label.setText(template.metadata.name)
        self.template_description.setText(template.metadata.description)
        
        # Enable buttons
        self.apply_button.setEnabled(True)
        self.delete_button.setEnabled(True)
        
        # Emit selection signal
        template_type = item_data.get("template_type")
        template_id = item_data.get("template_id")
        if template_type and template_id:
            self.template_selected.emit(template_type.value, template_id)
    
    def clear_details(self) -> None:
        """Clear template details."""
        self.template_name_label.setText("Select a template to view details")
        self.template_description.clear()
        
        # Disable buttons
        self.apply_button.setEnabled(False)
        self.delete_button.setEnabled(False)
    
    def on_template_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle template double-click."""
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        
        if item_data.get("type") == "template":
            self.apply_selected_template()
    
    def apply_selected_template(self) -> None:
        """Apply the selected template."""
        current_item = self.template_tree.currentItem()
        if not current_item:
            return
        
        item_data = current_item.data(0, Qt.ItemDataRole.UserRole)
        if item_data.get("type") != "template":
            return
        
        template_type = item_data.get("template_type")
        template_id = item_data.get("template_id")
        
        if template_type and template_id:
            self.template_applied.emit(template_type.value, template_id)
    
    def delete_selected_template(self) -> None:
        """Delete the selected template."""
        current_item = self.template_tree.currentItem()
        if not current_item:
            return
        
        item_data = current_item.data(0, Qt.ItemDataRole.UserRole)
        template = item_data.get("template")
        template_type = item_data.get("template_type")
        template_id = item_data.get("template_id")
        
        if not template or not template_type or not template_id:
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the template '{template.metadata.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.template_manager.delete_template(template_type, template_id):
                QMessageBox.information(self, "Success", "Template deleted successfully.")
            else:
                QMessageBox.warning(self, "Error", "Failed to delete template.")


class TemplateManagementDialog(QDialog, LoggerMixin):
    """Main dialog for template management."""
    
    template_applied = Signal(str, str, dict)  # template_type, template_id, config
    
    def __init__(self, template_manager: TemplateManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.template_manager = template_manager
        self.setup_ui()
        self.connect_signals()
        self.setModal(True)
        self.resize(1000, 700)
    
    def setup_ui(self) -> None:
        """Setup the dialog UI."""
        self.setWindowTitle("Template Management")
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Template Library tab
        self.library_widget = TemplateLibraryWidget(self.template_manager)
        self.tab_widget.addTab(self.library_widget, "Template Library")
        
        # Create Template tab  
        self.create_widget = self.create_template_creation_widget()
        self.tab_widget.addTab(self.create_widget, "Create Template")
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.close_button = BaseButton("Close")
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
    
    def create_template_creation_widget(self) -> QWidget:
        """Create the template creation widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Template type selection
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Template Type:"))
        
        self.template_type_combo = QComboBox()
        for template_type in [TemplateType.SELECTION, TemplateType.CALIBRATION, 
                             TemplateType.WELL_PLATE, TemplateType.WORKFLOW]:
            self.template_type_combo.addItem(
                template_type.value.replace("_", " ").title(),
                template_type
            )
        type_layout.addWidget(self.template_type_combo)
        type_layout.addStretch()
        
        layout.addLayout(type_layout)
        
        # Template metadata form
        metadata_group = QGroupBox("Template Information")
        metadata_layout = QFormLayout(metadata_group)
        
        self.template_name_input = BaseInput()
        self.template_name_input.setPlaceholderText("Enter template name...")
        metadata_layout.addRow("Name:", self.template_name_input)
        
        self.template_description_input = QTextEdit()
        self.template_description_input.setMaximumHeight(100)
        self.template_description_input.setPlaceholderText("Enter template description...")
        metadata_layout.addRow("Description:", self.template_description_input)
        
        self.template_author_input = BaseInput()
        self.template_author_input.setPlaceholderText("Enter author name...")
        metadata_layout.addRow("Author:", self.template_author_input)
        
        layout.addWidget(metadata_group)
        
        layout.addStretch()
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.save_template_button = BaseButton("Save Template")
        button_layout.addWidget(self.save_template_button)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        return widget
    
    def connect_signals(self) -> None:
        """Connect dialog signals."""
        self.close_button.clicked.connect(self.accept)
        
        # Library widget signals
        self.library_widget.template_applied.connect(self.on_template_applied)
        
        # Template creation signals
        self.save_template_button.clicked.connect(self.save_template)
    
    def on_template_applied(self, template_type_str: str, template_id: str) -> None:
        """Handle template application."""
        try:
            template_type = TemplateType(template_type_str)
            config = self.template_manager.apply_template(template_type, template_id)
            
            if config:
                self.template_applied.emit(template_type_str, template_id, config)
                QMessageBox.information(self, "Success", "Template applied successfully.")
            else:
                QMessageBox.warning(self, "Error", "Failed to apply template.")
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to apply template: {e}")
    
    @error_handler("Saving template")
    def save_template(self) -> None:
        """Save the current template configuration."""
        template_type = self.template_type_combo.currentData()
        
        if not self.template_name_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter a template name.")
            return
        
        # Collect template data
        template_data = {
            'metadata': {
                'name': self.template_name_input.text().strip(),
                'description': self.template_description_input.toPlainText().strip(),
                'author': self.template_author_input.text().strip(),
            }
        }
        
        try:
            template_id = self.template_manager.create_template(
                template_type,
                template_data,
                self.template_name_input.text().strip()
            )
            
            QMessageBox.information(self, "Success", "Template saved successfully.")
            
            # Clear form
            self.template_name_input.clear()
            self.template_description_input.clear()
            self.template_author_input.clear()
            
            # Switch to library tab
            self.tab_widget.setCurrentIndex(0)
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save template: {e}")
