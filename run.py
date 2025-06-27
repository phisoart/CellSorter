#!/usr/bin/env python3
"""
CellSorter Application Runner

Main entry point for CellSorter application.
Supports three operation modes:
1. GUI Mode (Production) - Only GUI
2. Dev Mode (Headless) - Only Headless  
3. Dual Mode (Debug) - Both Headless and GUI
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from headless.mode_manager import set_mode, AppMode, is_dev_mode, is_dual_mode, requires_gui, requires_headless
from headless.display_detector import has_display


def setup_logging(level: str = "INFO") -> None:
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def main():
    """Main entry point for CellSorter application."""
    parser = argparse.ArgumentParser(description='CellSorter - Cell Analysis Platform')
    
    # Mode selection arguments (mutually exclusive)
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('--gui-mode', action='store_true',
                           help='실제사용모드 - GUI만 실행 (Production mode - GUI only)')
    mode_group.add_argument('--dev-mode', action='store_true',
                           help='디버깅모드 - Headless만 실행 (Debug mode - Headless only)')
    mode_group.add_argument('--dual-mode', action='store_true',
                           help='디버깅모드 - Headless와 GUI 동시 실행 (Debug mode - Both Headless and GUI)')
    
    # Legacy compatibility
    mode_group.add_argument('--headless', action='store_true',
                           help='(Legacy) Same as --dev-mode')
    
    # Other arguments
    parser.add_argument('--log-level', default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                       help='Set logging level')
    
    # Headless-specific commands
    subparsers = parser.add_subparsers(dest='command', help='Headless commands')
    
    # Dump UI command
    dump_parser = subparsers.add_parser('dump-ui', help='Dump UI definition to file')
    dump_parser.add_argument('--output', '-o', help='Output file path')
    dump_parser.add_argument('--format', choices=['yaml', 'json'], default='yaml',
                           help='Output format')
    
    # Load UI command
    load_parser = subparsers.add_parser('load-ui', help='Load UI from file')
    load_parser.add_argument('input', help='Input file path')
    
    # Validate UI command
    validate_parser = subparsers.add_parser('validate-ui', help='Validate UI definition')
    validate_parser.add_argument('input', help='Input file path')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # Set application mode based on arguments
    if args.gui_mode:
        set_mode(AppMode.GUI)
        logger.info("Starting in GUI mode (실제사용모드)")
    elif args.dev_mode or args.headless:
        set_mode(AppMode.DEV)
        logger.info("Starting in Dev mode (디버깅모드 - Headless only)")
    elif args.dual_mode:
        set_mode(AppMode.DUAL)
        logger.info("Starting in Dual mode (디버깅모드 - Both Headless and GUI)")
    else:
        # Auto-detect mode if not specified
        logger.info("Auto-detecting mode...")
    
    # Check display availability
    if not has_display() and requires_gui():
        logger.error("No display available but GUI is required. Please use --dev-mode instead.")
        sys.exit(1)
    
    # Handle headless commands
    if args.command and requires_headless():
        from headless.cli.cli_commands import HeadlessCLI
        cli = HeadlessCLI()
        
        if args.command == 'dump-ui':
            cli.dump_ui(output=args.output, format=args.format)
        elif args.command == 'load-ui':
            cli.load_ui(args.input)
        elif args.command == 'validate-ui':
            cli.validate_ui(args.input)
        
        # In dual mode, continue to GUI after command
        if not is_dual_mode():
            return
    
    # Import and run appropriate interface
    if requires_gui():
        try:
            from PySide6.QtWidgets import QApplication
            from pages.main_window import MainWindow
            
            logger.info("Initializing GUI...")
            app = QApplication(sys.argv)
            
            # In dual mode, also initialize headless components
            if is_dual_mode():
                logger.info("Initializing headless components for dual mode...")
                from headless.main_window_adapter import MainWindowAdapter
                from headless.session_manager import HeadlessSessionManager
                from headless.mode_manager import get_mode_info
                
                # Create headless adapter
                adapter = MainWindowAdapter(get_mode_info())
                
                # Connect to real-time synchronization
                logger.info("Enabling real-time synchronization between headless and GUI...")
                
            window = MainWindow()
            
            # In dual mode, connect the window to headless adapter
            if is_dual_mode() and 'adapter' in locals():
                # This allows AI agent operations to be reflected in GUI in real-time
                adapter.connect_to_window(window)
                logger.info("Connected GUI to headless adapter for real-time updates")
            
            window.show()
            
            logger.info("Starting GUI event loop...")
            sys.exit(app.exec())
            
        except ImportError as e:
            logger.error(f"Failed to import GUI components: {e}")
            logger.error("Please install PySide6: pip install PySide6")
            sys.exit(1)
    
    elif requires_headless():
        # Headless-only mode
        from headless.cli.cli_commands import HeadlessCLI
        
        logger.info("Running in headless mode...")
        cli = HeadlessCLI()
        
        if not args.command:
            # Interactive headless mode
            logger.info("Starting interactive headless session...")
            cli.interactive_mode()
        else:
            logger.info("Command completed in headless mode.")


if __name__ == '__main__':
    main()