"""
Test Configuration and Settings

Tests for config.settings module to ensure all constants and configurations
are properly defined according to specifications.
"""

import pytest
from pathlib import Path

from config.settings import (
    APP_NAME, APP_VERSION, SUPPORTED_IMAGE_FORMATS, REQUIRED_CSV_COLUMNS,
    MAX_IMAGE_SIZE_MB, MAX_CELL_COUNT, COORDINATE_ACCURACY_MICROMETERS,
    SELECTION_COLORS, WELL_PLATE_LAYOUT, DEFAULT_SETTINGS
)


@pytest.mark.unit
class TestApplicationConstants:
    """Test application-level constants."""
    
    def test_app_name_is_defined(self):
        """Test that application name is properly defined."""
        assert APP_NAME == "CellSorter"
        assert isinstance(APP_NAME, str)
        assert len(APP_NAME) > 0
    
    def test_app_version_format(self):
        """Test that version follows semantic versioning."""
        assert APP_VERSION == "1.0.0"
        parts = APP_VERSION.split('.')
        assert len(parts) == 3
        for part in parts:
            assert part.isdigit()


@pytest.mark.unit
class TestFileFormatSupport:
    """Test file format specifications from PRODUCT_REQUIREMENTS.md."""
    
    def test_supported_image_formats(self):
        """Test that all required image formats are supported."""
        # FR1.1: Support for TIFF, JPG, JPEG, and PNG image formats
        required_formats = ['.tiff', '.tif', '.jpg', '.jpeg', '.png']
        
        for format_ext in required_formats:
            assert format_ext in SUPPORTED_IMAGE_FORMATS, f"Missing support for {format_ext}"
        
        # Ensure all formats are lowercase for consistency
        for format_ext in SUPPORTED_IMAGE_FORMATS:
            assert format_ext.islower(), f"Format {format_ext} should be lowercase"
            assert format_ext.startswith('.'), f"Format {format_ext} should start with dot"
    
    def test_csv_required_columns(self):
        """Test that all required CellProfiler columns are defined."""
        # FR1.2: Required bounding box columns
        expected_columns = [
            'AreaShape_BoundingBoxMaximum_X',
            'AreaShape_BoundingBoxMinimum_X',
            'AreaShape_BoundingBoxMaximum_Y',
            'AreaShape_BoundingBoxMinimum_Y'
        ]
        
        for column in expected_columns:
            assert column in REQUIRED_CSV_COLUMNS, f"Missing required column: {column}"
        
        assert len(REQUIRED_CSV_COLUMNS) == len(expected_columns)


@pytest.mark.unit
class TestPerformanceLimits:
    """Test performance and size limits from specifications."""
    
    def test_image_size_limit(self):
        """Test maximum image size limit."""
        # NFR1.3: Maximum image size: 2GB
        assert MAX_IMAGE_SIZE_MB == 2048  # 2GB in MB
        assert isinstance(MAX_IMAGE_SIZE_MB, int)
    
    def test_cell_count_limit(self):
        """Test maximum cell count limit."""
        # FR1.2: Support up to 100,000 cell records
        assert MAX_CELL_COUNT == 100000
        assert isinstance(MAX_CELL_COUNT, int)
    
    def test_coordinate_accuracy(self):
        """Test coordinate accuracy requirement."""
        # FR4.2: Transform with 0.1 micrometer accuracy
        assert COORDINATE_ACCURACY_MICROMETERS == 0.1
        assert isinstance(COORDINATE_ACCURACY_MICROMETERS, float)


@pytest.mark.unit
class TestSelectionSystem:
    """Test selection and color system specifications."""
    
    def test_selection_colors_defined(self):
        """Test that selection color palette is properly defined."""
        # FR2.3: Assign from 16 predefined colors minimum
        assert len(SELECTION_COLORS) >= 16
        
        # Test that all colors are valid hex codes
        for color_name, color_value in SELECTION_COLORS.items():
            assert isinstance(color_name, str)
            assert isinstance(color_value, str)
            assert color_value.startswith('#')
            assert len(color_value) == 7  # #RRGGBB format
            
            # Test that hex digits are valid
            hex_digits = color_value[1:]
            int(hex_digits, 16)  # Will raise ValueError if invalid
    
    def test_basic_colors_present(self):
        """Test that basic colors are available."""
        basic_colors = ['Red', 'Green', 'Blue', 'Yellow', 'Magenta', 'Cyan']
        
        for color in basic_colors:
            assert color in SELECTION_COLORS, f"Missing basic color: {color}"


@pytest.mark.unit
class TestWellPlateConfiguration:
    """Test 96-well plate configuration."""
    
    def test_well_plate_layout(self):
        """Test 96-well plate layout generation."""
        # FR5.1: Standard 96-well plate layout (A01-H12)
        assert len(WELL_PLATE_LAYOUT) == 96
        
        # Test first few and last few wells
        assert WELL_PLATE_LAYOUT[0] == "A01"
        assert WELL_PLATE_LAYOUT[1] == "A02"
        assert WELL_PLATE_LAYOUT[12] == "B01"  # Second row starts
        assert WELL_PLATE_LAYOUT[-1] == "H12"  # Last well
        
        # Test that all wells are unique
        assert len(set(WELL_PLATE_LAYOUT)) == 96
        
        # Test format consistency
        for well in WELL_PLATE_LAYOUT:
            assert len(well) == 3
            assert well[0] in 'ABCDEFGH'  # Row letters
            assert well[1:].isdigit()  # Column numbers
            assert 1 <= int(well[1:]) <= 12  # Valid column range


@pytest.mark.unit
class TestDefaultSettings:
    """Test default application settings."""
    
    def test_default_settings_structure(self):
        """Test that default settings contain required keys."""
        required_keys = [
            'theme', 'auto_save_interval', 'max_undo_steps',
            'default_image_zoom', 'show_overlays', 'memory_limit_gb'
        ]
        
        for key in required_keys:
            assert key in DEFAULT_SETTINGS, f"Missing default setting: {key}"
    
    def test_default_setting_types(self):
        """Test that default settings have correct types."""
        type_checks = {
            'theme': str,
            'auto_save_interval': int,
            'max_undo_steps': int,
            'default_image_zoom': float,
            'show_overlays': bool,
            'memory_limit_gb': (int, float)
        }
        
        for key, expected_type in type_checks.items():
            setting_value = DEFAULT_SETTINGS[key]
            if isinstance(expected_type, tuple):
                assert isinstance(setting_value, expected_type), f"{key} should be {expected_type}"
            else:
                assert isinstance(setting_value, expected_type), f"{key} should be {expected_type}"
    
    def test_reasonable_default_values(self):
        """Test that default values are reasonable."""
        # Auto-save interval should be reasonable (5 minutes = 300 seconds)
        assert 60 <= DEFAULT_SETTINGS['auto_save_interval'] <= 3600
        
        # Memory limit should be reasonable (4GB as per specs)
        assert DEFAULT_SETTINGS['memory_limit_gb'] == 4
        
        # Zoom should be 100% by default
        assert DEFAULT_SETTINGS['default_image_zoom'] == 1.0
        
        # Overlays should be shown by default
        assert DEFAULT_SETTINGS['show_overlays'] is True


@pytest.mark.unit
class TestPathConfiguration:
    """Test path configuration and directory structure."""
    
    def test_base_directories_exist(self):
        """Test that base directories are properly configured."""
        from config.settings import BASE_DIR, SRC_DIR, TESTS_DIR, DOCS_DIR
        
        # Base directory should exist (project root)
        assert BASE_DIR.exists(), f"Base directory not found: {BASE_DIR}"
        
        # SRC directory should exist
        assert SRC_DIR.exists(), f"Source directory not found: {SRC_DIR}"
        
        # Tests directory should exist
        assert TESTS_DIR.exists(), f"Tests directory not found: {TESTS_DIR}"
        
        # Docs directory should exist
        assert DOCS_DIR.exists(), f"Docs directory not found: {DOCS_DIR}"
    
    def test_directory_relationships(self):
        """Test that directory relationships are correct."""
        from config.settings import BASE_DIR, SRC_DIR, TESTS_DIR, DOCS_DIR
        
        # All directories should be under BASE_DIR
        assert SRC_DIR.is_relative_to(BASE_DIR)
        assert TESTS_DIR.is_relative_to(BASE_DIR)
        assert DOCS_DIR.is_relative_to(BASE_DIR)
        
        # SRC_DIR should contain this config module
        config_file = SRC_DIR / "config" / "settings.py"
        assert config_file.exists(), "Config settings file should exist"