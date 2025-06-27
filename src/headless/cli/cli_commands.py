"""
Command-line interface for headless UI development.

This module provides the main CLI entry points and command processing
for headless UI development and testing.
"""

import argparse
import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..ui_model import UIModel
from ..session_manager import HeadlessSessionManager
from ..main_window_adapter import MainWindowAdapter
from .ui_tools import UITools, UIToolsError
from ..mode_manager import ModeManager


class HeadlessCLI:
    """Main CLI interface for headless UI development."""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.mode_manager = ModeManager()
        self.session_manager = HeadlessSessionManager(self.mode_manager)
        self.ui_tools = UITools()
        self.ui_model: Optional[UIModel] = None
        self.adapter: Optional[MainWindowAdapter] = None
        self._active_session: Optional[str] = None
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Create the main argument parser."""
        parser = argparse.ArgumentParser(
            description="CellSorter Headless UI Development CLI",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Session management commands
        session_parser = subparsers.add_parser('session', help='Session management')
        session_subparsers = session_parser.add_subparsers(dest='session_action')
        
        # Create session
        create_parser = session_subparsers.add_parser('create', help='Create new session')
        create_parser.add_argument('name', nargs='?', help='Session name (optional)')
        create_parser.add_argument('--from-gui', action='store_true',
                                 help='Initialize from current GUI state')
        
        # Load session
        load_parser = session_subparsers.add_parser('load', help='Load existing session')
        load_parser.add_argument('file', help='Session file path')
        
        # Save session
        save_parser = session_subparsers.add_parser('save', help='Save current session')
        save_parser.add_argument('file', nargs='?', help='Output file path (optional)')
        
        # UI model commands
        model_parser = subparsers.add_parser('model', help='UI model operations')
        model_subparsers = model_parser.add_subparsers(dest='model_action')
        
        # Export model
        export_parser = model_subparsers.add_parser('export', help='Export UI model')
        export_parser.add_argument('output', help='Output file path')
        export_parser.add_argument('--format', choices=['json', 'yaml'], default='yaml',
                                 help='Export format')
        
        # Import model
        import_parser = model_subparsers.add_parser('import', help='Import UI model')
        import_parser.add_argument('file', help='Input file path')
        
        # Validate model
        validate_parser = model_subparsers.add_parser('validate', help='Validate UI model')
        validate_parser.add_argument('file', nargs='?', help='File to validate (optional)')
        validate_parser.add_argument('--strict', action='store_true', help='Strict validation')
        
        # Mode info
        subparsers.add_parser('mode-info', help='Show current mode information')
        
        return parser
    
    def run(self, args: Optional[List[str]] = None) -> int:
        """Run the CLI with given arguments."""
        parser = self.create_parser()
        parsed_args = parser.parse_args(args)
        
        try:
            if parsed_args.command == 'session':
                return self._handle_session_command(parsed_args)
            elif parsed_args.command == 'model':
                return self._handle_model_command(parsed_args)
            elif parsed_args.command == 'mode-info':
                return self._handle_mode_info()
            else:
                parser.print_help()
                return 1
        
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
    
    def _handle_session_command(self, args) -> int:
        """Handle session management commands."""
        if args.session_action == 'create':
            session = self.session_manager.create_new_session(args.name)
            if args.from_gui:
                print("GUI state initialization not yet implemented")
            print(f"Created session: {session.session_id}")
            self._active_session = session.session_id
            return 0
        
        elif args.session_action == 'load':
            if self.session_manager.load_session(args.file):
                self._active_session = self.session_manager.current_session.session_id if self.session_manager.current_session else "loaded"
                print(f"Loaded session from: {args.file}")
                return 0
            else:
                print(f"Failed to load session: {args.file}", file=sys.stderr)
                return 1
        
        elif args.session_action == 'save':
            if self.session_manager.save_session(args.file):
                file_path = args.file or "auto-generated path"
                print(f"Saved session to: {file_path}")
                return 0
            else:
                print("Failed to save session", file=sys.stderr)
                return 1
        
        return 1
    
    def _handle_model_command(self, args) -> int:
        """Handle UI model commands."""
        if args.model_action == 'export':
            try:
                if not self.ui_model:
                    # Create a sample UI model for testing
                    self.ui_model = UIModel()
                
                if args.format == 'yaml':
                    from ..serializers import YAMLSerializer
                    serializer = YAMLSerializer()
                else:
                    from ..serializers import JSONSerializer
                    serializer = JSONSerializer()
                
                serializer.save(self.ui_model, args.output)
                print(f"Exported UI model to: {args.output}")
                return 0
            
            except Exception as e:
                print(f"Failed to export model: {e}", file=sys.stderr)
                return 1
        
        elif args.model_action == 'import':
            try:
                if args.file.endswith(('.yaml', '.yml')):
                    from ..serializers import YAMLSerializer
                    serializer = YAMLSerializer()
                else:
                    from ..serializers import JSONSerializer
                    serializer = JSONSerializer()
                
                self.ui_model = serializer.load(args.file)
                print(f"Imported UI model from: {args.file}")
                return 0
            
            except Exception as e:
                print(f"Failed to import model: {e}", file=sys.stderr)
                return 1
        
        elif args.model_action == 'validate':
            try:
                if args.file:
                    results = self.ui_tools.validate_ui_file(args.file, strict=args.strict)
                    target = args.file
                elif self.ui_model:
                    from ..ui_compatibility import UI
                    ui_def = UI()  # Convert ui_model to UI if needed
                    results = self.ui_tools.validate_ui(ui_def, strict=args.strict)
                    target = "current model"
                else:
                    print("No model to validate. Specify file or load a model.", file=sys.stderr)
                    return 1
                
                # Print validation results
                from ..validators.ui_validator import ValidationLevel
                errors = [r for r in results if r.level == ValidationLevel.ERROR]
                warnings = [r for r in results if r.level == ValidationLevel.WARNING]
                
                if errors:
                    print("ERRORS:")
                    for error in errors:
                        print(f"  - {error.message}")
                
                if warnings:
                    print("WARNINGS:")
                    for warning in warnings:
                        print(f"  - {warning.message}")
                
                if not errors and not warnings:
                    print(f"✓ {target} validation passed")
                elif errors:
                    print(f"✗ {target} validation failed with {len(errors)} errors")
                    return 1
                else:
                    print(f"⚠ {target} validation passed with {len(warnings)} warnings")
                
                return 0
            
            except Exception as e:
                print(f"Validation failed: {e}", file=sys.stderr)
                return 1
        
        return 1
    
    def _handle_mode_info(self) -> int:
        """Handle mode info command."""
        try:
            info = self.mode_manager.get_mode_info()
            
            print("Mode Information:")
            print(f"  Current Mode: {info['mode']}")
            print(f"  Dev Mode: {info['dev_mode']}")
            print(f"  Display Available: {info['display_available']}")
            print(f"  Environment Variables:")
            for key, value in info.get('environment', {}).items():
                print(f"    {key}: {value}")
            
            return 0
        
        except Exception as e:
            print(f"Failed to get mode info: {e}", file=sys.stderr)
            return 1
    
    def dump_ui(self, output: Optional[str] = None, format: str = 'yaml') -> None:
        """
        Dump current UI definition to file or stdout.
        
        Args:
            output: Output file path (None for stdout)
            format: Output format ('yaml' or 'json')
        """
        try:
            # Get current UI state
            if not self.ui_model:
                self.ui_model = UIModel()
                
            # Serialize UI
            if format == 'yaml':
                from ..serializers.yaml_serializer import YAMLSerializer
                serializer = YAMLSerializer()
            else:
                from ..serializers.json_serializer import JSONSerializer
                serializer = JSONSerializer()
                
            serialized = serializer.serialize(self.ui_model)
            
            # Output
            if output:
                with open(output, 'w') as f:
                    f.write(serialized)
                print(f"UI definition dumped to {output}")
            else:
                print(serialized)
                
        except Exception as e:
            print(f"Error dumping UI: {e}")
            raise
    
    def load_ui(self, input_path: str) -> None:
        """
        Load UI definition from file.
        
        Args:
            input_path: Path to UI definition file
        """
        try:
            # Determine format from extension
            if input_path.endswith('.yaml') or input_path.endswith('.yml'):
                from ..serializers.yaml_serializer import YAMLSerializer
                serializer = YAMLSerializer()
            else:
                from ..serializers.json_serializer import JSONSerializer
                serializer = JSONSerializer()
            
            # Load and deserialize
            with open(input_path, 'r') as f:
                content = f.read()
                
            self.ui_model = serializer.deserialize(content)
            
            # Apply to adapter if available
            if self.adapter:
                self.adapter.apply_ui_model(self.ui_model)
                
            print(f"UI definition loaded from {input_path}")
            
        except Exception as e:
            print(f"Error loading UI: {e}")
            raise
    
    def validate_ui(self, input_path: str) -> None:
        """
        Validate UI definition file.
        
        Args:
            input_path: Path to UI definition file
        """
        try:
            from ..validators.schema_validator import SchemaValidator
            from ..validators.semantic_validator import SemanticValidator
            
            # Load UI definition
            with open(input_path, 'r') as f:
                content = f.read()
            
            # Validate schema
            schema_validator = SchemaValidator()
            schema_errors = schema_validator.validate(content)
            
            if schema_errors:
                print("Schema validation errors:")
                for error in schema_errors:
                    print(f"  - {error}")
                return
                
            print("✓ Schema validation passed")
            
            # Validate semantics
            semantic_validator = SemanticValidator()
            semantic_errors = semantic_validator.validate(content)
            
            if semantic_errors:
                print("Semantic validation errors:")
                for error in semantic_errors:
                    print(f"  - {error}")
                return
                
            print("✓ Semantic validation passed")
            print("UI definition is valid!")
            
        except Exception as e:
            print(f"Error validating UI: {e}")
            raise
    
    def interactive_mode(self) -> None:
        """
        Start interactive headless session.
        """
        print("CellSorter Interactive Headless Mode")
        print("Type 'help' for available commands or 'exit' to quit")
        
        while True:
            try:
                command = input("\ncellsorter> ").strip()
                
                if command == 'exit':
                    break
                elif command == 'help':
                    self._show_help()
                elif command.startswith('dump'):
                    parts = command.split()
                    output = parts[1] if len(parts) > 1 else None
                    self.dump_ui(output)
                elif command.startswith('load'):
                    parts = command.split()
                    if len(parts) > 1:
                        self.load_ui(parts[1])
                    else:
                        print("Usage: load <file_path>")
                elif command.startswith('validate'):
                    parts = command.split()
                    if len(parts) > 1:
                        self.validate_ui(parts[1])
                    else:
                        print("Usage: validate <file_path>")
                else:
                    print(f"Unknown command: {command}")
                    print("Type 'help' for available commands")
                    
            except KeyboardInterrupt:
                print("\nUse 'exit' to quit")
            except Exception as e:
                print(f"Error: {e}")
    
    def _show_help(self) -> None:
        """Show available commands in interactive mode."""
        print("""
Available commands:
  dump [output_file]      - Dump current UI definition
  load <input_file>       - Load UI definition from file  
  validate <file>         - Validate UI definition file
  help                    - Show this help message
  exit                    - Exit interactive mode
        """)
    
    def run_command(self, args: List[str]) -> int:
        """Execute CLI command based on arguments."""
        try:
            if not args:
                self.interactive_mode()
                return 0
            
            command = args[0]
            if command == "dump-ui":
                self.dump_ui()
                return 0
            elif command == "load-ui" and len(args) > 1:
                self.load_ui(args[1])
                return 0
            elif command == "validate-ui" and len(args) > 1:
                self.validate_ui(args[1])
                return 0
            else:
                print(f"Unknown command or missing arguments: {command}", file=sys.stderr)
                return 1
        except Exception as e:
            print(f"Command failed: {e}", file=sys.stderr)
            return 1


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for the CLI."""
    cli = HeadlessCLI()
    return cli.run(args)


if __name__ == '__main__':
    sys.exit(main())
