#!/usr/bin/env python3
"""
CellSorter Application Runner

Main entry point for CellSorter application.
Supports both GUI and headless development modes.
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from headless.mode_manager import set_mode, AppMode, is_dev_mode
from headless.display_detector import has_display


def setup_logging(level: str = "INFO") -> None:
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def setup_environment(args: argparse.Namespace) -> None:
    """Setup environment based on command line arguments."""
    if args.dev_mode:
        os.environ['CELLSORTER_DEV_MODE'] = '1'
        set_mode(AppMode.DEV)
    elif args.gui_mode:
        os.environ['CELLSORTER_DEV_MODE'] = '0'
        set_mode(AppMode.GUI)
    # If neither specified, use auto mode
    

def run_gui_mode() -> int:
    """Run CellSorter in GUI mode."""
    try:
        from PySide6.QtWidgets import QApplication
        from src.main import main as gui_main
        
        app = QApplication(sys.argv)
        result = gui_main()
        return app.exec() if result else 1
        
    except ImportError as e:
        print(f"Error: Failed to import GUI dependencies: {e}")
        print("Please ensure PySide6 is installed.")
        return 1
    except Exception as e:
        print(f"Error running GUI: {e}")
        return 1


def run_cli_commands(args: argparse.Namespace) -> int:
    """Run headless CLI commands."""
    try:
        from headless.cli.cli_commands import main as cli_main
        
        # Convert argparse Namespace to list of strings for CLI parser
        cli_args = []
        
        if hasattr(args, 'cli_command') and args.cli_command:
            cli_args.append(args.cli_command)
            
            # Add command-specific arguments
            if args.cli_command == 'dump-ui':
                if hasattr(args, 'input') and args.input:
                    cli_args.append(args.input)
                if hasattr(args, 'output') and args.output:
                    cli_args.append(args.output)
                if hasattr(args, 'format') and args.format:
                    cli_args.extend(['--format', args.format])
                    
            elif args.cli_command == 'load-ui':
                if hasattr(args, 'input') and args.input:
                    cli_args.append(args.input)
                    
            elif args.cli_command == 'validate-ui':
                if hasattr(args, 'input') and args.input:
                    cli_args.append(args.input)
                if hasattr(args, 'strict') and args.strict:
                    cli_args.append('--strict')
        
        return cli_main(cli_args if cli_args else None)
        
    except ImportError as e:
        print(f"Error: Failed to import CLI dependencies: {e}")
        return 1
    except Exception as e:
        print(f"Error running CLI: {e}")
        return 1


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="CellSorter - Cell Sorting and Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Run in GUI mode (default)
  %(prog)s --dev-mode                         # Run in development mode
  %(prog)s --cli dump-ui input.yaml output.json --format json
  %(prog)s --cli validate-ui input.yaml --strict
  %(prog)s --cli mode-info                    # Show current mode information
        """
    )
    
    # Mode selection
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('--dev-mode', action='store_true',
                           help='Run in development mode (headless)')
    mode_group.add_argument('--gui-mode', action='store_true',
                           help='Force GUI mode')
    
    # CLI commands
    parser.add_argument('--cli', dest='cli_command', 
                       choices=['dump-ui', 'load-ui', 'validate-ui', 'mode-info'],
                       help='Run CLI command in headless mode')
    
    # CLI command arguments
    parser.add_argument('input', nargs='?', help='Input file (for CLI commands)')
    parser.add_argument('output', nargs='?', help='Output file (for dump-ui)')
    parser.add_argument('--format', choices=['yaml', 'json'], default='yaml',
                       help='Output format for dump-ui (default: yaml)')
    parser.add_argument('--strict', action='store_true',
                       help='Use strict validation for validate-ui')
    
    # General options
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Set logging level')
    
    return parser


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Setup environment
    setup_environment(args)
    
    # Determine mode and run appropriate handler
    if args.cli_command:
        # CLI command specified - force dev mode
        os.environ['CELLSORTER_DEV_MODE'] = '1'
        set_mode(AppMode.DEV)
        return run_cli_commands(args)
    
    elif is_dev_mode():
        # Development mode - run CLI interface
        print("CellSorter Development Mode")
        print("Use --cli <command> to run specific commands")
        print("Available commands: dump-ui, load-ui, validate-ui, mode-info")
        print("Example: python run.py --cli mode-info")
        return 0
    
    elif has_display():
        # GUI mode
        return run_gui_mode()
    
    else:
        # No display available - suggest dev mode
        print("No display detected. Consider using development mode:")
        print("  python run.py --dev-mode")
        print("Or specific CLI commands:")
        print("  python run.py --cli mode-info")
        return 1


if __name__ == "__main__":
    sys.exit(main())