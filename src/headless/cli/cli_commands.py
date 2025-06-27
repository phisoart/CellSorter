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


def main() -> int:
    """Main entry point for the CLI."""
    cli = HeadlessCLI()
    return cli.run()


if __name__ == '__main__':
    sys.exit(main())
