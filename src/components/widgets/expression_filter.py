"""
Expression Filter Widget for CellSorter (TASK-020)

Advanced mathematical expression filtering UI component with expression builder,
real-time validation, templates, and preview functionality.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QSplitter,
    QTextEdit, QLabel, QPushButton, QListWidget, QListWidgetItem,
    QComboBox, QGroupBox, QFrame, QTabWidget, QTableWidget, 
    QTableWidgetItem, QCheckBox, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QTimer, QThread, pyqtSignal
from PySide6.QtGui import QFont, QColor, QSyntaxHighlighter, QTextDocument, QTextCharFormat

import pandas as pd
import numpy as np

from utils.expression_parser import ExpressionParser, ExpressionResult, ExpressionType
from utils.logging_config import LoggerMixin
from utils.error_handler import error_handler


@dataclass
class ExpressionTemplate:
    """Expression template data structure."""
    name: str
    expression: str
    description: str
    category: str


class ExpressionSyntaxHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for mathematical expressions."""
    
    def __init__(self, parent: QTextDocument):
        super().__init__(parent)
        
        # Define formats
        self.keyword_format = QTextCharFormat()
        self.keyword_format.setColor(QColor(137, 89, 168))  # Purple
        self.keyword_format.setFontWeight(QFont.Bold)
        
        self.function_format = QTextCharFormat()
        self.function_format.setColor(QColor(46, 125, 50))  # Green
        self.function_format.setFontWeight(QFont.Bold)
        
        self.operator_format = QTextCharFormat()
        self.operator_format.setColor(QColor(244, 67, 54))  # Red
        
        self.number_format = QTextCharFormat()
        self.number_format.setColor(QColor(33, 150, 243))  # Blue
        
        # Define patterns
        self.keywords = ['and', 'or', 'not', 'AND', 'OR', 'NOT']
        self.functions = ['mean', 'std', 'var', 'min', 'max', 'median', 'percentile', 
                         'count', 'sum', 'abs', 'sqrt', 'log', 'log10']
        self.operators = ['+', '-', '*', '/', '>', '<', '>=', '<=', '==', '!=', '%', '**']
    
    def highlightBlock(self, text: str) -> None:
        """Highlight syntax in text block."""
        # Highlight keywords
        for keyword in self.keywords:
            index = text.find(keyword)
            while index >= 0:
                length = len(keyword)
                self.setFormat(index, length, self.keyword_format)
                index = text.find(keyword, index + length)
        
        # Highlight functions
        for function in self.functions:
            index = text.find(function + '(')
            while index >= 0:
                length = len(function)
                self.setFormat(index, length, self.function_format)
                index = text.find(function + '(', index + length)
        
        # Highlight operators
        for operator in self.operators:
            index = text.find(operator)
            while index >= 0:
                length = len(operator)
                self.setFormat(index, length, self.operator_format)
                index = text.find(operator, index + length)
        
        # Highlight numbers
        import re
        number_pattern = re.compile(r'\b\d+(?:\.\d+)?\b')
        for match in number_pattern.finditer(text):
            self.setFormat(match.start(), match.end() - match.start(), self.number_format)


class ExpressionEvaluationWorker(QThread):
    """Worker thread for expression evaluation."""
    
    evaluation_complete = pyqtSignal(object)  # ExpressionResult
    
    def __init__(self, expression: str, data: pd.DataFrame):
        super().__init__()
        self.expression = expression
        self.data = data
        self.parser = ExpressionParser()
    
    def run(self) -> None:
        """Run expression evaluation in background."""
        try:
            result = self.parser.evaluate_expression(self.expression, self.data)
            self.evaluation_complete.emit(result)
        except Exception as e:
            error_result = ExpressionResult(
                value=False,
                expression_type=ExpressionType.BOOLEAN,
                column_dependencies=[],
                execution_time=0.0,
                error_message=str(e)
            )
            self.evaluation_complete.emit(error_result)


class ExpressionFilterWidget(QWidget, LoggerMixin):
    """
    Advanced mathematical expression filter widget.
    
    Features:
    - Expression builder with syntax highlighting
    - Real-time validation and preview
    - Function and operator helpers
    - Expression templates
    """
    
    # Signals
    expression_changed = Signal(str)
    filter_applied = Signal(object)  # ExpressionResult
    selection_requested = Signal(list)  # indices
    
    # Default templates
    DEFAULT_TEMPLATES = [
        ExpressionTemplate(
            name="Outlier Detection (2σ)",
            expression="abs({column} - mean({column})) > 2 * std({column})",
            description="Detect outliers beyond 2 standard deviations",
            category="Outliers"
        ),
        ExpressionTemplate(
            name="High Intensity Cells",
            expression="{intensity} > percentile({intensity}, 75)",
            description="Select cells in top 25% of intensity",
            category="Intensity"
        ),
        ExpressionTemplate(
            name="Large Cells",
            expression="{area} > mean({area}) + std({area})",
            description="Select cells larger than mean + 1σ",
            category="Morphology"
        ),
        ExpressionTemplate(
            name="Combined Filter",
            expression="{area} > 100 AND {intensity} > mean({intensity})",
            description="Combined area and intensity criteria",
            category="Combined"
        )
    ]
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # Data storage
        self.data: Optional[pd.DataFrame] = None
        self.parser = ExpressionParser()
        self.current_result: Optional[ExpressionResult] = None
        self.templates: List[ExpressionTemplate] = self.DEFAULT_TEMPLATES.copy()
        
        # UI state
        self.validation_timer = QTimer()
        self.validation_timer.setSingleShot(True)
        self.validation_timer.timeout.connect(self._validate_expression)
        
        self.evaluation_worker: Optional[ExpressionEvaluationWorker] = None
        
        self.setup_ui()
        self.connect_signals()
        
        self.log_info("Expression filter widget initialized")
    
    def setup_ui(self) -> None:
        """Set up the widget UI."""
        layout = QVBoxLayout(self)
        
        # Expression editor
        editor_group = QGroupBox("Mathematical Expression")
        editor_layout = QVBoxLayout(editor_group)
        
        self.expression_edit = QTextEdit()
        self.expression_edit.setFont(QFont("Consolas", 10))
        self.expression_edit.setMaximumHeight(80)
        self.expression_edit.setPlaceholderText("Enter expression (e.g., area > mean(area))")
        
        # Set up syntax highlighting
        self.highlighter = ExpressionSyntaxHighlighter(self.expression_edit.document())
        
        editor_layout.addWidget(self.expression_edit)
        
        # Validation status
        self.validation_label = QLabel("Ready")
        self.validation_label.setStyleSheet("color: #6c757d; font-style: italic;")
        editor_layout.addWidget(self.validation_label)
        
        layout.addWidget(editor_group)
        
        # Main content splitter
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel: Helpers
        helpers_panel = self._create_helpers_panel()
        splitter.addWidget(helpers_panel)
        
        # Right panel: Preview
        preview_panel = self._create_preview_panel()
        splitter.addWidget(preview_panel)
        
        # Controls
        controls_panel = self._create_controls_panel()
        layout.addWidget(controls_panel)
        
        # Set splitter proportions
        splitter.setSizes([300, 400])
    
    def _create_helpers_panel(self) -> QWidget:
        """Create helpers panel."""
        tab_widget = QTabWidget()
        
        # Columns tab
        columns_widget = QWidget()
        columns_layout = QVBoxLayout(columns_widget)
        
        columns_layout.addWidget(QLabel("Available Columns:"))
        self.columns_list = QListWidget()
        self.columns_list.setToolTip("Double-click to insert column name")
        columns_layout.addWidget(self.columns_list)
        
        tab_widget.addTab(columns_widget, "Columns")
        
        # Functions tab
        functions_widget = QWidget()
        functions_layout = QVBoxLayout(functions_widget)
        
        functions_layout.addWidget(QLabel("Statistical Functions:"))
        self.functions_list = QListWidget()
        self.functions_list.setToolTip("Double-click to insert function")
        functions_layout.addWidget(self.functions_list)
        
        self.function_description = QLabel("Select a function to see description")
        self.function_description.setWordWrap(True)
        self.function_description.setStyleSheet("color: #6c757d; font-style: italic; font-size: 11px;")
        functions_layout.addWidget(self.function_description)
        
        tab_widget.addTab(functions_widget, "Functions")
        
        # Operators tab
        operators_widget = QWidget()
        operators_layout = QGridLayout(operators_widget)
        
        # Math operators
        math_ops = ['+', '-', '*', '/', '%', '**', '(', ')']
        for i, op in enumerate(math_ops):
            btn = QPushButton(op)
            btn.setMaximumWidth(40)
            btn.clicked.connect(lambda checked, o=op: self._insert_operator(o))
            operators_layout.addWidget(btn, 0, i)
        
        # Comparison operators
        comp_ops = ['>', '<', '>=', '<=', '==', '!=']
        for i, op in enumerate(comp_ops):
            btn = QPushButton(op)
            btn.setMaximumWidth(60)
            btn.clicked.connect(lambda checked, o=op: self._insert_operator(o))
            operators_layout.addWidget(btn, 1, i)
        
        # Logical operators
        logic_ops = ['AND', 'OR', 'NOT']
        for i, op in enumerate(logic_ops):
            btn = QPushButton(op)
            btn.setMaximumWidth(60)
            btn.clicked.connect(lambda checked, o=op: self._insert_operator(o))
            operators_layout.addWidget(btn, 2, i)
        
        tab_widget.addTab(operators_widget, "Operators")
        
        # Templates tab
        templates_widget = QWidget()
        templates_layout = QVBoxLayout(templates_widget)
        
        templates_layout.addWidget(QLabel("Expression Templates:"))
        self.templates_list = QListWidget()
        self.templates_list.setToolTip("Double-click to use template")
        templates_layout.addWidget(self.templates_list)
        
        self.template_description = QLabel("Select a template to see description")
        self.template_description.setWordWrap(True)
        self.template_description.setStyleSheet("color: #6c757d; font-style: italic; font-size: 11px;")
        templates_layout.addWidget(self.template_description)
        
        tab_widget.addTab(templates_widget, "Templates")
        
        return tab_widget
    
    def _create_preview_panel(self) -> QWidget:
        """Create preview panel."""
        preview_group = QGroupBox("Preview Results")
        layout = QVBoxLayout(preview_group)
        
        # Progress bar
        self.validation_progress = QProgressBar()
        self.validation_progress.setVisible(False)
        layout.addWidget(self.validation_progress)
        
        # Preview table
        self.preview_table = QTableWidget()
        self.preview_table.setMaximumHeight(200)
        self.preview_table.setAlternatingRowColors(True)
        layout.addWidget(self.preview_table)
        
        # Statistics
        self.stats_label = QLabel("No results")
        self.stats_label.setStyleSheet("color: #6c757d; font-size: 11px;")
        layout.addWidget(self.stats_label)
        
        return preview_group
    
    def _create_controls_panel(self) -> QWidget:
        """Create controls panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        layout = QHBoxLayout(panel)
        
        # Status label
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # Auto-preview checkbox
        self.auto_preview_check = QCheckBox("Auto Preview")
        self.auto_preview_check.setChecked(True)
        layout.addWidget(self.auto_preview_check)
        
        # Buttons
        self.validate_btn = QPushButton("Validate")
        self.validate_btn.clicked.connect(self._validate_expression)
        layout.addWidget(self.validate_btn)
        
        self.preview_btn = QPushButton("Preview")
        self.preview_btn.clicked.connect(self._preview_expression)
        layout.addWidget(self.preview_btn)
        
        self.apply_btn = QPushButton("Apply Filter")
        self.apply_btn.setStyleSheet("font-weight: bold; color: white; background-color: #007bff;")
        self.apply_btn.clicked.connect(self._apply_filter)
        self.apply_btn.setEnabled(False)
        layout.addWidget(self.apply_btn)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self._clear_expression)
        layout.addWidget(self.clear_btn)
        
        return panel
    
    def connect_signals(self) -> None:
        """Connect widget signals."""
        self.expression_edit.textChanged.connect(self._on_expression_changed)
        self.columns_list.itemDoubleClicked.connect(self._insert_column)
        self.functions_list.itemDoubleClicked.connect(self._insert_function)
        self.functions_list.currentItemChanged.connect(self._show_function_description)
        self.templates_list.itemDoubleClicked.connect(self._use_template)
        self.templates_list.currentItemChanged.connect(self._show_template_description)
    
    @error_handler("Loading data for expression filter")
    def load_data(self, data: pd.DataFrame) -> None:
        """Load data for expression filtering."""
        self.data = data
        
        # Update columns list
        self.columns_list.clear()
        numeric_columns = data.select_dtypes(include=[np.number]).columns.tolist()
        
        for column in numeric_columns:
            item = QListWidgetItem(column)
            item.setToolTip(f"Type: {data[column].dtype}")
            self.columns_list.addItem(item)
        
        # Update functions list
        self._populate_functions_list()
        
        # Update templates
        self._populate_templates()
        
        self.status_label.setText(f"Data loaded: {len(data):,} rows, {len(numeric_columns)} columns")
        self.log_info(f"Loaded data for expression filtering: {len(data):,} rows")
    
    def _populate_functions_list(self) -> None:
        """Populate functions list."""
        self.functions_list.clear()
        functions = self.parser.get_available_functions()
        
        for func_info in functions:
            item = QListWidgetItem(func_info['name'])
            item.setData(Qt.UserRole, func_info)
            item.setToolTip(func_info['description'])
            self.functions_list.addItem(item)
    
    def _populate_templates(self) -> None:
        """Populate templates list."""
        self.templates_list.clear()
        
        for template in self.templates:
            item = QListWidgetItem(template.name)
            item.setData(Qt.UserRole, template)
            item.setToolTip(template.description)
            self.templates_list.addItem(item)
    
    def _on_expression_changed(self) -> None:
        """Handle expression text change."""
        expression = self.expression_edit.toPlainText().strip()
        
        if expression:
            self.validation_timer.start(500)  # 500ms delay
            
            if self.auto_preview_check.isChecked():
                QTimer.singleShot(1000, self._preview_expression)
        else:
            self.validation_label.setText("Ready")
            self.apply_btn.setEnabled(False)
            self._clear_preview()
        
        self.expression_changed.emit(expression)
    
    def _validate_expression(self) -> None:
        """Validate current expression."""
        expression = self.expression_edit.toPlainText().strip()
        
        if not expression:
            self.validation_label.setText("Ready")
            return
        
        if self.data is None:
            self.validation_label.setText("No data loaded")
            self.validation_label.setStyleSheet("color: #dc3545;")
            return
        
        columns = self.data.select_dtypes(include=[np.number]).columns.tolist()
        validation_result = self.parser.validate_expression(expression, columns)
        
        if validation_result['valid']:
            self.validation_label.setText(f"✓ Valid - References: {', '.join(validation_result['referenced_columns'])}")
            self.validation_label.setStyleSheet("color: #28a745;")
            self.apply_btn.setEnabled(True)
        else:
            self.validation_label.setText(f"✗ {validation_result['error_message']}")
            self.validation_label.setStyleSheet("color: #dc3545;")
            self.apply_btn.setEnabled(False)
    
    def _preview_expression(self) -> None:
        """Preview expression results."""
        expression = self.expression_edit.toPlainText().strip()
        
        if not expression or self.data is None:
            return
        
        # Show progress
        self.validation_progress.setVisible(True)
        self.validation_progress.setRange(0, 0)
        
        # Start evaluation
        if self.evaluation_worker and self.evaluation_worker.isRunning():
            self.evaluation_worker.quit()
            self.evaluation_worker.wait()
        
        self.evaluation_worker = ExpressionEvaluationWorker(expression, self.data)
        self.evaluation_worker.evaluation_complete.connect(self._on_evaluation_complete)
        self.evaluation_worker.start()
    
    def _on_evaluation_complete(self, result: ExpressionResult) -> None:
        """Handle evaluation completion."""
        self.validation_progress.setVisible(False)
        self.current_result = result
        
        if result.error_message:
            self.stats_label.setText(f"Error: {result.error_message}")
            self._clear_preview()
            return
        
        # Update preview
        self._update_preview_table(result)
        
        # Update statistics
        if isinstance(result.value, np.ndarray) and result.value.dtype == bool:
            selected_count = np.sum(result.value)
            total_count = len(result.value)
            percentage = (selected_count / total_count) * 100 if total_count > 0 else 0
            
            self.stats_label.setText(
                f"Selected: {selected_count:,} / {total_count:,} cells ({percentage:.1f}%) "
                f"| Time: {result.execution_time:.3f}s"
            )
        else:
            self.stats_label.setText(f"Result: {result.value} | Type: {result.expression_type.value}")
    
    def _update_preview_table(self, result: ExpressionResult) -> None:
        """Update preview table."""
        if self.data is None or result.error_message:
            return
        
        # Show sample of selected data
        if isinstance(result.value, np.ndarray) and result.value.dtype == bool:
            selected_data = self.data[result.value].head(10)
        else:
            selected_data = self.data.head(10)
        
        # Update table
        self.preview_table.setRowCount(len(selected_data))
        self.preview_table.setColumnCount(min(4, len(selected_data.columns)))
        
        # Set headers
        headers = selected_data.columns[:4].tolist()
        self.preview_table.setHorizontalHeaderLabels(headers)
        
        # Populate data
        for row in range(len(selected_data)):
            for col in range(min(4, len(selected_data.columns))):
                value = selected_data.iloc[row, col]
                text = f"{value:.3f}" if isinstance(value, float) else str(value)
                
                item = QTableWidgetItem(text)
                self.preview_table.setItem(row, col, item)
        
        self.preview_table.resizeColumnsToContents()
    
    def _clear_preview(self) -> None:
        """Clear preview table."""
        self.preview_table.setRowCount(0)
        self.stats_label.setText("No results")
    
    def _apply_filter(self) -> None:
        """Apply current expression filter."""
        if self.current_result is None:
            self._preview_expression()
            return
        
        expression = self.expression_edit.toPlainText().strip()
        
        # Emit signals
        self.filter_applied.emit(self.current_result)
        
        if isinstance(self.current_result.value, np.ndarray) and self.current_result.value.dtype == bool:
            selected_indices = np.where(self.current_result.value)[0].tolist()
            self.selection_requested.emit(selected_indices)
        
        self.log_info(f"Applied expression filter: {expression}")
    
    def _clear_expression(self) -> None:
        """Clear expression editor."""
        self.expression_edit.clear()
        self._clear_preview()
        self.validation_label.setText("Ready")
        self.validation_label.setStyleSheet("color: #6c757d; font-style: italic;")
        self.apply_btn.setEnabled(False)
    
    def _insert_column(self, item: QListWidgetItem) -> None:
        """Insert column name."""
        column_name = item.text()
        self._insert_text(column_name)
    
    def _insert_function(self, item: QListWidgetItem) -> None:
        """Insert function."""
        function_name = item.text()
        self._insert_text(f"{function_name}()")
        
        # Move cursor inside parentheses
        cursor = self.expression_edit.textCursor()
        cursor.movePosition(cursor.Left)
        self.expression_edit.setTextCursor(cursor)
    
    def _insert_operator(self, operator: str) -> None:
        """Insert operator."""
        self._insert_text(f" {operator} ")
    
    def _insert_text(self, text: str) -> None:
        """Insert text at cursor."""
        cursor = self.expression_edit.textCursor()
        cursor.insertText(text)
        self.expression_edit.setFocus()
    
    def _show_function_description(self, current: QListWidgetItem, previous: QListWidgetItem) -> None:
        """Show function description."""
        if current:
            func_info = current.data(Qt.UserRole)
            if func_info:
                self.function_description.setText(f"{func_info['signature']}\n{func_info['description']}")
        else:
            self.function_description.setText("Select a function to see description")
    
    def _use_template(self, item: QListWidgetItem) -> None:
        """Use expression template."""
        template = item.data(Qt.UserRole)
        if template:
            self.expression_edit.setPlainText(template.expression)
            self.log_info(f"Used template: {template.name}")
    
    def _show_template_description(self, current: QListWidgetItem, previous: QListWidgetItem) -> None:
        """Show template description."""
        if current:
            template = current.data(Qt.UserRole)
            if template:
                self.template_description.setText(template.description)
        else:
            self.template_description.setText("Select a template to see description")
    
    def get_current_expression(self) -> str:
        """Get current expression text."""
        return self.expression_edit.toPlainText().strip()
    
    def set_expression(self, expression: str) -> None:
        """Set expression text."""
        self.expression_edit.setPlainText(expression)
