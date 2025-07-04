import os
import sys
from pathlib import Path

# Set an environment variable to indicate GUI-only mode
os.environ['GUI_ONLY_MODE'] = '1'

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.main import main

if __name__ == "__main__":
    # This entry point is specifically for the bundled GUI application.
    # It forces the application to run in GUI mode.
    sys.argv.append('--gui-mode')
    main() 