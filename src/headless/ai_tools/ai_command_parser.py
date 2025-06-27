"""
AI Command Parser

Parses natural language commands from AI agents and converts them into
structured UI operations for the headless system.
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class CommandType(Enum):
    """Types of UI commands that can be parsed."""
    WIDGET_SEARCH = "widget_search"
    WIDGET_MODIFY = "widget_modify"
    WIDGET_CREATE = "widget_create"
    WIDGET_DELETE = "widget_delete"
    PROPERTY_SET = "property_set"
    PROPERTY_GET = "property_get"
    LAYOUT_MODIFY = "layout_modify"
    ACTION_TRIGGER = "action_trigger"
    BATCH_OPERATION = "batch_operation"
    VALIDATION = "validation"
    EXPORT = "export"
    IMPORT = "import"


@dataclass
class ParsedCommand:
    """Represents a parsed AI command."""
    command_type: CommandType
    target: str
    action: str
    parameters: Dict[str, Any]
    confidence: float
    original_text: str
    suggested_syntax: Optional[str] = None


class AICommandParser:
    """
    Parses natural language commands from AI agents into structured operations.
    
    Designed to be forgiving and helpful, providing suggestions when commands
    are ambiguous or incomplete.
    """
    
    def __init__(self):
        self._patterns = self._build_command_patterns()
        self._widget_aliases = self._build_widget_aliases()
        self._property_aliases = self._build_property_aliases()
    
    def parse(self, command_text: str) -> List[ParsedCommand]:
        """
        Parse a natural language command into structured operations.
        
        Args:
            command_text: Natural language command from AI agent
            
        Returns:
            List of parsed commands (may be multiple for complex operations)
        """
        command_text = command_text.strip().lower()
        logger.debug(f"Parsing command: {command_text}")
        
        # Try each pattern in order of specificity
        for pattern_name, (pattern, parser_func) in self._patterns.items():
            match = re.search(pattern, command_text, re.IGNORECASE)
            if match:
                try:
                    commands = parser_func(match, command_text)
                    if commands:
                        logger.debug(f"Successfully parsed with pattern: {pattern_name}")
                        return commands
                except Exception as e:
                    logger.debug(f"Parser {pattern_name} failed: {e}")
                    continue
        
        # If no pattern matched, try to provide helpful suggestions
        return self._handle_unknown_command(command_text)
    
    def _build_command_patterns(self) -> Dict[str, Tuple[str, callable]]:
        """Build regex patterns for different command types."""
        return {
            # Widget search patterns
            'find_widget': (
                r'(?:find|search|locate|get)\s+(?:widget|component|element)\s+(?:called|named|with\s+name)?\s*["\']?(\w+)["\']?',
                self._parse_widget_search
            ),
            
            # Property modification patterns
            'set_property': (
                r'(?:set|change|update|modify)\s+(?:the\s+)?(\w+)\s+(?:property\s+)?(?:of\s+)?["\']?(\w+)["\']?\s+to\s+["\']?([^"\']+)["\']?',
                self._parse_property_set
            ),
            
            # Widget creation patterns
            'create_widget': (
                r'(?:create|add|insert)\s+(?:a\s+|an\s+)?(\w+)\s+(?:widget|component|element)?\s*(?:named|called)?\s*["\']?(\w*)["\']?',
                self._parse_widget_create
            ),
            
            # Widget deletion patterns
            'delete_widget': (
                r'(?:delete|remove|destroy)\s+(?:widget|component|element)?\s*["\']?(\w+)["\']?',
                self._parse_widget_delete
            ),
            
            # Layout modification patterns
            'modify_layout': (
                r'(?:move|arrange|position)\s+["\']?(\w+)["\']?\s+(?:to|in|at)\s+(.+)',
                self._parse_layout_modify
            ),
            
            # Action trigger patterns
            'trigger_action': (
                r'(?:trigger|execute|run|perform)\s+(?:action|command)?\s*["\']?(\w+)["\']?',
                self._parse_action_trigger
            ),
            
            # Batch operation patterns
            'batch_operation': (
                r'(?:batch|bulk)\s+(\w+)\s+(?:on|for)\s+(.+)',
                self._parse_batch_operation
            ),
            
            # Export/Import patterns
            'export_ui': (
                r'(?:export|save|dump)\s+(?:ui|interface|definition)\s*(?:to\s+["\']?([^"\']+)["\']?)?',
                self._parse_export
            ),
            
            'import_ui': (
                r'(?:import|load)\s+(?:ui|interface|definition)\s*(?:from\s+["\']?([^"\']+)["\']?)?',
                self._parse_import
            ),
        }
    
    def _build_widget_aliases(self) -> Dict[str, str]:
        """Build mapping of common widget aliases to Qt widget types."""
        return {
            'button': 'QPushButton',
            'btn': 'QPushButton',
            'pushbutton': 'QPushButton',
            'label': 'QLabel',
            'text': 'QLabel',
            'textlabel': 'QLabel',
            'edit': 'QLineEdit',
            'lineedit': 'QLineEdit',
            'textbox': 'QLineEdit',
            'input': 'QLineEdit',
            'textarea': 'QTextEdit',
            'textedit': 'QTextEdit',
            'multiline': 'QTextEdit',
            'combo': 'QComboBox',
            'combobox': 'QComboBox',
            'dropdown': 'QComboBox',
            'list': 'QListWidget',
            'listbox': 'QListWidget',
            'listwidget': 'QListWidget',
            'tree': 'QTreeWidget',
            'treeview': 'QTreeWidget',
            'table': 'QTableWidget',
            'tableview': 'QTableWidget',
            'grid': 'QTableWidget',
            'checkbox': 'QCheckBox',
            'check': 'QCheckBox',
            'radio': 'QRadioButton',
            'radiobutton': 'QRadioButton',
            'slider': 'QSlider',
            'scroll': 'QScrollArea',
            'scrollarea': 'QScrollArea',
            'tab': 'QTabWidget',
            'tabs': 'QTabWidget',
            'tabwidget': 'QTabWidget',
            'group': 'QGroupBox',
            'groupbox': 'QGroupBox',
            'frame': 'QFrame',
            'panel': 'QFrame',
            'splitter': 'QSplitter',
            'layout': 'QLayout',
            'hlayout': 'QHBoxLayout',
            'vlayout': 'QVBoxLayout',
            'gridlayout': 'QGridLayout',
        }
    
    def _build_property_aliases(self) -> Dict[str, str]:
        """Build mapping of common property aliases to Qt property names."""
        return {
            'title': 'windowTitle',
            'caption': 'windowTitle',
            'name': 'objectName',
            'id': 'objectName',
            'width': 'width',
            'height': 'height',
            'size': 'size',
            'position': 'geometry',
            'pos': 'geometry',
            'visible': 'visible',
            'shown': 'visible',
            'hidden': 'visible',
            'enabled': 'enabled',
            'disabled': 'enabled',
            'text': 'text',
            'content': 'text',
            'value': 'value',
            'color': 'color',
            'background': 'styleSheet',
            'style': 'styleSheet',
            'font': 'font',
            'fontsize': 'font',
            'tooltip': 'toolTip',
            'hint': 'toolTip',
            'shortcut': 'shortcut',
            'icon': 'icon',
        }
    
    def _parse_widget_search(self, match, original_text: str) -> List[ParsedCommand]:
        """Parse widget search commands."""
        widget_name = match.group(1)
        
        return [ParsedCommand(
            command_type=CommandType.WIDGET_SEARCH,
            target=widget_name,
            action="find",
            parameters={"name": widget_name},
            confidence=0.9,
            original_text=original_text,
            suggested_syntax=f'find_widget("{widget_name}")'
        )]
    
    def _parse_property_set(self, match, original_text: str) -> List[ParsedCommand]:
        """Parse property setting commands."""
        property_name = match.group(1)
        widget_name = match.group(2)
        value = match.group(3)
        
        # Resolve property alias
        qt_property = self._property_aliases.get(property_name, property_name)
        
        # Try to convert value to appropriate type
        converted_value = self._convert_value(value, qt_property)
        
        return [ParsedCommand(
            command_type=CommandType.PROPERTY_SET,
            target=widget_name,
            action="set_property",
            parameters={
                "property": qt_property,
                "value": converted_value,
                "original_property": property_name
            },
            confidence=0.85,
            original_text=original_text,
            suggested_syntax=f'set_property("{widget_name}", "{qt_property}", {repr(converted_value)})'
        )]
    
    def _parse_widget_create(self, match, original_text: str) -> List[ParsedCommand]:
        """Parse widget creation commands."""
        widget_type = match.group(1)
        widget_name = match.group(2) or f"new_{widget_type}"
        
        # Resolve widget type alias
        qt_widget_type = self._widget_aliases.get(widget_type, widget_type)
        
        return [ParsedCommand(
            command_type=CommandType.WIDGET_CREATE,
            target=widget_name,
            action="create",
            parameters={
                "type": qt_widget_type,
                "name": widget_name,
                "original_type": widget_type
            },
            confidence=0.8,
            original_text=original_text,
            suggested_syntax=f'create_widget("{qt_widget_type}", name="{widget_name}")'
        )]
    
    def _parse_widget_delete(self, match, original_text: str) -> List[ParsedCommand]:
        """Parse widget deletion commands."""
        widget_name = match.group(1)
        
        return [ParsedCommand(
            command_type=CommandType.WIDGET_DELETE,
            target=widget_name,
            action="delete",
            parameters={"name": widget_name},
            confidence=0.9,
            original_text=original_text,
            suggested_syntax=f'delete_widget("{widget_name}")'
        )]
    
    def _parse_layout_modify(self, match, original_text: str) -> List[ParsedCommand]:
        """Parse layout modification commands."""
        widget_name = match.group(1)
        position_desc = match.group(2)
        
        return [ParsedCommand(
            command_type=CommandType.LAYOUT_MODIFY,
            target=widget_name,
            action="move",
            parameters={
                "widget": widget_name,
                "position": position_desc
            },
            confidence=0.7,
            original_text=original_text,
            suggested_syntax=f'move_widget("{widget_name}", "{position_desc}")'
        )]
    
    def _parse_action_trigger(self, match, original_text: str) -> List[ParsedCommand]:
        """Parse action trigger commands."""
        action_name = match.group(1)
        
        return [ParsedCommand(
            command_type=CommandType.ACTION_TRIGGER,
            target=action_name,
            action="trigger",
            parameters={"action": action_name},
            confidence=0.85,
            original_text=original_text,
            suggested_syntax=f'trigger_action("{action_name}")'
        )]
    
    def _parse_batch_operation(self, match, original_text: str) -> List[ParsedCommand]:
        """Parse batch operation commands."""
        operation = match.group(1)
        targets = match.group(2)
        
        return [ParsedCommand(
            command_type=CommandType.BATCH_OPERATION,
            target=targets,
            action=operation,
            parameters={
                "operation": operation,
                "targets": targets
            },
            confidence=0.75,
            original_text=original_text,
            suggested_syntax=f'batch_{operation}("{targets}")'
        )]
    
    def _parse_export(self, match, original_text: str) -> List[ParsedCommand]:
        """Parse export commands."""
        file_path = match.group(1) if match.groups() and match.group(1) else "ui_export.yaml"
        
        return [ParsedCommand(
            command_type=CommandType.EXPORT,
            target=file_path,
            action="export",
            parameters={"file_path": file_path},
            confidence=0.9,
            original_text=original_text,
            suggested_syntax=f'export_ui("{file_path}")'
        )]
    
    def _parse_import(self, match, original_text: str) -> List[ParsedCommand]:
        """Parse import commands."""
        file_path = match.group(1) if match.groups() and match.group(1) else ""
        
        return [ParsedCommand(
            command_type=CommandType.IMPORT,
            target=file_path,
            action="import",
            parameters={"file_path": file_path},
            confidence=0.9 if file_path else 0.5,
            original_text=original_text,
            suggested_syntax=f'import_ui("{file_path}")' if file_path else 'import_ui("path/to/file")'
        )]
    
    def _convert_value(self, value: str, property_name: str) -> Any:
        """Convert string value to appropriate type based on property."""
        value = value.strip()
        
        # Boolean values
        if value.lower() in ('true', 'yes', 'on', '1'):
            return True
        elif value.lower() in ('false', 'no', 'off', '0'):
            return False
        
        # Numeric values
        try:
            # Try integer first
            if '.' not in value:
                return int(value)
            else:
                return float(value)
        except ValueError:
            pass
        
        # Color values
        if property_name.lower() in ('color', 'background', 'foreground'):
            if value.startswith('#'):
                return value
            elif value.lower() in ('red', 'blue', 'green', 'black', 'white', 'gray', 'yellow'):
                return value.lower()
        
        # Default to string
        return value
    
    def _handle_unknown_command(self, command_text: str) -> List[ParsedCommand]:
        """Handle unknown commands by providing helpful suggestions."""
        # Look for keywords to suggest command types
        suggestions = []
        
        if any(word in command_text for word in ['find', 'search', 'get', 'locate']):
            suggestions.append("Did you mean to search for a widget? Try: 'find widget named <name>'")
        
        if any(word in command_text for word in ['set', 'change', 'update', 'modify']):
            suggestions.append("Did you mean to modify a property? Try: 'set <property> of <widget> to <value>'")
        
        if any(word in command_text for word in ['create', 'add', 'new']):
            suggestions.append("Did you mean to create a widget? Try: 'create <type> widget named <name>'")
        
        if any(word in command_text for word in ['delete', 'remove', 'destroy']):
            suggestions.append("Did you mean to delete a widget? Try: 'delete widget <name>'")
        
        if not suggestions:
            suggestions.append(
                "Available commands: find widget, set property, create widget, delete widget, "
                "export ui, import ui, trigger action"
            )
        
        return [ParsedCommand(
            command_type=CommandType.VALIDATION,
            target="unknown",
            action="suggest",
            parameters={"suggestions": suggestions},
            confidence=0.1,
            original_text=command_text,
            suggested_syntax=None
        )]