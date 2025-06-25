"""
CellSorter Test Configuration and Fixtures

This module provides common test fixtures and configuration for the CellSorter test suite.
Following TDD principles as specified in TESTING_STRATEGY.md and CODING_STYLE_GUIDE.md.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Generator, Dict, Any
import sys
import os

import numpy as np
import pandas as pd
from PIL import Image
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from config.settings import REQUIRED_CSV_COLUMNS


@pytest.fixture(scope="session")
def qapp() -> Generator[QApplication, None, None]:
    """
    Create QApplication instance for GUI tests.
    Required for any Qt widget testing as per pytest-qt documentation.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # Don't call app.quit() as it may affect other tests


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """
    Create temporary directory for test files.
    Automatically cleaned up after test completion.
    """
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_image_data() -> np.ndarray:
    """
    Create sample image data for testing.
    Specifications: Support TIFF/JPG/PNG formats with various bit depths.
    """
    # Create a 512x512 RGB test image with distinctive patterns
    height, width = 512, 512
    image = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Add test patterns for visual verification
    # Red square in top-left
    image[50:150, 50:150, 0] = 255
    
    # Green circle in top-right  
    center_x, center_y = 400, 100
    y, x = np.ogrid[:height, :width]
    mask = (x - center_x)**2 + (y - center_y)**2 <= 50**2
    image[mask] = [0, 255, 0]
    
    # Blue gradient in bottom half
    for i in range(height//2, height):
        intensity = int(255 * (i - height//2) / (height//2))
        image[i, :, 2] = intensity
    
    return image


@pytest.fixture
def sample_grayscale_image() -> np.ndarray:
    """Create sample grayscale image for testing."""
    height, width = 256, 256
    image = np.zeros((height, width), dtype=np.uint8)
    
    # Create checkerboard pattern
    for i in range(0, height, 32):
        for j in range(0, width, 32):
            if (i//32 + j//32) % 2 == 0:
                image[i:i+32, j:j+32] = 255
    
    return image


@pytest.fixture
def sample_tiff_file(temp_dir: Path, sample_image_data: np.ndarray) -> Path:
    """
    Create sample TIFF file for testing.
    Tests requirement: Support TIFF format up to 2GB.
    """
    file_path = temp_dir / "test_sample.tiff"
    
    # Convert numpy array to PIL Image and save as TIFF
    pil_image = Image.fromarray(sample_image_data)
    pil_image.save(file_path, format='TIFF')
    
    return file_path


@pytest.fixture
def sample_jpg_file(temp_dir: Path, sample_image_data: np.ndarray) -> Path:
    """Create sample JPG file for testing."""
    file_path = temp_dir / "test_sample.jpg"
    
    pil_image = Image.fromarray(sample_image_data)
    pil_image.save(file_path, format='JPEG', quality=95)
    
    return file_path


@pytest.fixture
def sample_png_file(temp_dir: Path, sample_image_data: np.ndarray) -> Path:
    """Create sample PNG file for testing."""
    file_path = temp_dir / "test_sample.png"
    
    pil_image = Image.fromarray(sample_image_data)
    pil_image.save(file_path, format='PNG')
    
    return file_path


@pytest.fixture
def large_test_image(temp_dir: Path) -> Path:
    """
    Create larger test image to verify performance requirements.
    Requirement: Load time < 5 seconds for 500MB files.
    """
    file_path = temp_dir / "large_test.tiff"
    
    # Create 2048x2048 image (approximately 12MB uncompressed)
    height, width = 2048, 2048
    image = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
    
    pil_image = Image.fromarray(image)
    pil_image.save(file_path, format='TIFF')
    
    return file_path


@pytest.fixture
def sample_csv_data() -> pd.DataFrame:
    """
    Create sample CellProfiler CSV data for testing.
    Must include all required columns as per REQUIRED_CSV_COLUMNS.
    """
    # Generate synthetic cell data
    n_cells = 1000
    np.random.seed(42)  # For reproducible tests
    
    data = {
        # Required bounding box columns
        'AreaShape_BoundingBoxMinimum_X': np.random.randint(0, 1800, n_cells),
        'AreaShape_BoundingBoxMaximum_X': np.random.randint(200, 2048, n_cells),
        'AreaShape_BoundingBoxMinimum_Y': np.random.randint(0, 1800, n_cells),
        'AreaShape_BoundingBoxMaximum_Y': np.random.randint(200, 2048, n_cells),
        
        # Additional typical CellProfiler columns for testing
        'ObjectNumber': range(1, n_cells + 1),
        'AreaShape_Area': np.random.normal(100, 30, n_cells),
        'AreaShape_Eccentricity': np.random.uniform(0, 1, n_cells),
        'Intensity_MeanIntensity_DAPI': np.random.normal(50, 15, n_cells),
        'Intensity_MeanIntensity_CK7': np.random.normal(30, 20, n_cells),
        'Intensity_MeanIntensity_CK20': np.random.normal(25, 18, n_cells),
        'Intensity_MeanIntensity_CDX2': np.random.normal(35, 25, n_cells),
    }
    
    # Ensure bounding boxes are valid (min < max)
    for i in range(n_cells):
        if data['AreaShape_BoundingBoxMinimum_X'][i] >= data['AreaShape_BoundingBoxMaximum_X'][i]:
            data['AreaShape_BoundingBoxMaximum_X'][i] = data['AreaShape_BoundingBoxMinimum_X'][i] + 50
        if data['AreaShape_BoundingBoxMinimum_Y'][i] >= data['AreaShape_BoundingBoxMaximum_Y'][i]:
            data['AreaShape_BoundingBoxMaximum_Y'][i] = data['AreaShape_BoundingBoxMinimum_Y'][i] + 50
    
    return pd.DataFrame(data)


@pytest.fixture
def sample_csv_file(temp_dir: Path, sample_csv_data: pd.DataFrame) -> Path:
    """Create sample CSV file for testing."""
    file_path = temp_dir / "test_cellprofiler_data.csv"
    sample_csv_data.to_csv(file_path, index=False)
    return file_path


@pytest.fixture
def large_csv_data() -> pd.DataFrame:
    """
    Create large CSV dataset for performance testing.
    Requirement: Parse time < 3 seconds for 50,000 records.
    """
    n_cells = 50000
    np.random.seed(42)
    
    data = {
        # Required columns
        'AreaShape_BoundingBoxMinimum_X': np.random.randint(0, 1800, n_cells),
        'AreaShape_BoundingBoxMaximum_X': np.random.randint(200, 2048, n_cells),
        'AreaShape_BoundingBoxMinimum_Y': np.random.randint(0, 1800, n_cells),
        'AreaShape_BoundingBoxMaximum_Y': np.random.randint(200, 2048, n_cells),
        
        # Many additional columns to simulate real CellProfiler output
        'ObjectNumber': range(1, n_cells + 1),
        'AreaShape_Area': np.random.normal(100, 30, n_cells),
        'AreaShape_Perimeter': np.random.normal(40, 10, n_cells),
        'AreaShape_FormFactor': np.random.uniform(0, 1, n_cells),
        'AreaShape_Eccentricity': np.random.uniform(0, 1, n_cells),
        'AreaShape_Solidity': np.random.uniform(0.5, 1, n_cells),
    }
    
    # Add intensity measurements for multiple channels
    channels = ['DAPI', 'CK7', 'CK20', 'CDX2', 'ER', 'PR', 'HER2']
    measurements = ['MeanIntensity', 'MaxIntensity', 'MinIntensity', 'StdIntensity']
    
    for channel in channels:
        for measurement in measurements:
            col_name = f'Intensity_{measurement}_{channel}'
            data[col_name] = np.random.normal(50, 20, n_cells)
    
    # Ensure valid bounding boxes
    for i in range(n_cells):
        if data['AreaShape_BoundingBoxMinimum_X'][i] >= data['AreaShape_BoundingBoxMaximum_X'][i]:
            data['AreaShape_BoundingBoxMaximum_X'][i] = data['AreaShape_BoundingBoxMinimum_X'][i] + 50
        if data['AreaShape_BoundingBoxMinimum_Y'][i] >= data['AreaShape_BoundingBoxMaximum_Y'][i]:
            data['AreaShape_BoundingBoxMaximum_Y'][i] = data['AreaShape_BoundingBoxMinimum_Y'][i] + 50
    
    return pd.DataFrame(data)


@pytest.fixture
def large_csv_file(temp_dir: Path, large_csv_data: pd.DataFrame) -> Path:
    """Create large CSV file for performance testing."""
    file_path = temp_dir / "large_cellprofiler_data.csv"
    large_csv_data.to_csv(file_path, index=False)
    return file_path


@pytest.fixture
def invalid_csv_file(temp_dir: Path) -> Path:
    """Create invalid CSV file for error testing."""
    file_path = temp_dir / "invalid_data.csv"
    
    # Create CSV missing required columns
    invalid_data = pd.DataFrame({
        'SomeColumn': [1, 2, 3],
        'AnotherColumn': ['a', 'b', 'c']
    })
    
    invalid_data.to_csv(file_path, index=False)
    return file_path


@pytest.fixture
def mock_settings(temp_dir: Path) -> QSettings:
    """Create mock QSettings for testing without affecting real settings."""
    settings_file = temp_dir / "test_settings.ini"
    settings = QSettings(str(settings_file), QSettings.IniFormat)
    return settings


@pytest.fixture
def performance_thresholds() -> Dict[str, float]:
    """
    Performance thresholds from specifications.
    Based on PRODUCT_REQUIREMENTS.md performance requirements.
    """
    return {
        'image_load_time_500mb': 5.0,  # 5 seconds for 500MB
        'csv_parse_time_50k': 3.0,     # 3 seconds for 50K records
        'plot_render_time_50k': 2.0,   # 2 seconds for 50K points
        'memory_limit_gb': 4.0,        # 4GB memory limit
        'coordinate_accuracy_um': 0.1, # 0.1 micrometer accuracy
    }


# Pytest configuration

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests for individual components"
    )
    config.addinivalue_line(
        "markers", "gui: GUI tests requiring Qt widgets"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests for complete workflows"
    )
    config.addinivalue_line(
        "markers", "performance: Performance benchmark tests"
    )
    config.addinivalue_line(
        "markers", "regression: Regression tests for bug fixes"
    )
    config.addinivalue_line(
        "markers", "slow: Long-running tests"
    )