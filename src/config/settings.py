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

# Color Palette for Selections (Based on design system)
SELECTION_COLORS: Dict[str, str] = {
    "Red": "hsl(0, 84.2%, 60.2%)",         # Destructive color
    "Green": "hsl(142.1, 76.2%, 36.3%)",   # Normal tissue color
    "Blue": "hsl(221.2, 83.2%, 53.3%)",    # Stroma color
    "Yellow": "hsl(47.9, 95.8%, 53.1%)",   # Necrosis color
    "Magenta": "hsl(300, 100%, 50%)",
    "Cyan": "hsl(180, 100%, 50%)",
    "Orange": "hsl(24.6, 95%, 53.1%)",     # Blood vessels color
    "Purple": "hsl(262.1, 83.3%, 57.8%)",  # Immune cells color
    "Pink": "hsl(350, 100%, 88%)",
    "Brown": "hsl(25, 76%, 47%)",
    "Gray": "hsl(0, 0%, 50%)",
    "Lime": "hsl(150, 100%, 50%)",
    "Navy": "hsl(240, 100%, 25%)",
    "Maroon": "hsl(0, 100%, 25%)",
    "Olive": "hsl(60, 100%, 25%)",
    "Teal": "hsl(180, 100%, 25%)"
}

# Medical/Scientific Colors (Based on design system)
MEDICAL_COLORS: Dict[str, str] = {
    "cancer_primary": "hsl(0, 84.2%, 60.2%)",       # Red
    "normal_tissue": "hsl(142.1, 76.2%, 36.3%)",   # Green  
    "stroma": "hsl(221.2, 83.2%, 53.3%)",          # Blue
    "immune_cells": "hsl(262.1, 83.3%, 57.8%)",    # Purple
    "blood_vessels": "hsl(24.6, 95%, 53.1%)",      # Orange
    "necrosis": "hsl(47.9, 95.8%, 53.1%)"          # Yellow
}

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