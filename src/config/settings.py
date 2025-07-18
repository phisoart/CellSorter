"""
CellSorter Application Settings and Constants

This module contains application-wide settings, constants, and configuration.
"""

from typing import Dict, List
from pathlib import Path

# Application Information
APP_NAME = "CellSorter"
APP_VERSION = "2.0.0"
APP_ORGANIZATION = "CellSorter Team"
APP_DESCRIPTION = "Advanced Cell Sorting and Tissue Extraction Software"

# File Format Support
SUPPORTED_IMAGE_FORMATS = [".tiff", ".tif", ".jpg", ".jpeg", ".png"]
SUPPORTED_CSV_FORMATS = [".csv"]
EXPORT_PROTOCOL_FORMAT = ".cxprotocol"

# Performance Limits
MAX_IMAGE_SIZE_MB = 2048  # 2GB
MAX_CELL_COUNT = 100000
TYPICAL_CELL_COUNT = 50000
PERFORMANCE_TARGET_SECONDS = 2

# Accuracy Requirements
COORDINATE_ACCURACY_MICROMETERS = 0.1
CALIBRATION_ERROR_THRESHOLD = 0.01  # 1%
EXTRACTION_SUCCESS_RATE = 0.98  # 98%

# UI Layout Constants
DEFAULT_WINDOW_WIDTH = 1200
DEFAULT_WINDOW_HEIGHT = 800
MIN_WINDOW_WIDTH = 800
MIN_WINDOW_HEIGHT = 600

# Panel Proportions (as percentages)
IMAGE_PANEL_WIDTH = 40
PLOT_PANEL_WIDTH = 35
SELECTION_PANEL_WIDTH = 25

# Minimum Panel Sizes (in pixels)
MIN_IMAGE_PANEL_WIDTH = 200
MIN_PLOT_PANEL_WIDTH = 300
MIN_SELECTION_PANEL_WIDTH = 250

# Layout Spacing and Margins
PANEL_MARGIN = 8
COMPONENT_SPACING = 12
BUTTON_SPACING = 8
BUTTON_HEIGHT = 32
BUTTON_MIN_WIDTH = 100

# Responsive Breakpoints
BREAKPOINT_MOBILE = 768
BREAKPOINT_TABLET = 1024
BREAKPOINT_DESKTOP = 1280

# Well Plate Configuration
WELL_PLATE_ROWS = 8  # A-H
WELL_PLATE_COLUMNS = 12  # 01-12
WELL_PLATE_TOTAL = WELL_PLATE_ROWS * WELL_PLATE_COLUMNS

# Well plate layout (A01, A02, ..., H12)
WELL_PLATE_LAYOUT = [
    f"{chr(65 + row)}{col:02d}" 
    for row in range(WELL_PLATE_ROWS) 
    for col in range(1, WELL_PLATE_COLUMNS + 1)
]

# Required CellProfiler CSV Columns
REQUIRED_CSV_COLUMNS: List[str] = [
    "AreaShape_BoundingBoxMaximum_X",
    "AreaShape_BoundingBoxMinimum_X",
    "AreaShape_BoundingBoxMaximum_Y", 
    "AreaShape_BoundingBoxMinimum_Y"
]

# Color Palette for Selections (Based on design system)
SELECTION_COLORS: Dict[str, str] = {
    "Red": "#FF0000",
    "Green": "#00FF00",
    "Blue": "#0000FF",
    "Yellow": "#FFFF00",
    "Magenta": "#FF00FF",
    "Cyan": "#00FFFF",
    "LightGray": "#C0C0C0",
    "DarkRed": "#800000",
    "DarkGreen": "#008000",
    "DarkBlue": "#000080",
    "DarkYellow": "#808000",
    "DarkMagenta": "#800080",
    "DarkCyan": "#008080",
    "DarkGray": "#808080",
    "White": "#FFFFFF",
    "Black": "#000000"
}

# Application Paths
BASE_DIR = Path(__file__).parent.parent.parent
SRC_DIR = BASE_DIR / "src"
ASSETS_DIR = SRC_DIR / "assets"
TESTS_DIR = BASE_DIR / "tests"
DOCS_DIR = BASE_DIR / "docs"

# Default Settings
DEFAULT_SETTINGS: Dict[str, any] = {
    "theme": "light",
    "auto_save_interval": 300,  # 5 minutes
    "max_undo_steps": 50,
    "default_image_zoom": 1.0,
    "plot_point_size": 3,
    "plot_alpha": 0.7,
    "show_overlays": True,
    "enable_gpu_acceleration": True,
    "memory_limit_gb": 4,
    "recent_files_limit": 10
}

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5