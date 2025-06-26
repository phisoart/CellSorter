"""
Test file for Enhanced Calibration Dialog (TASK-022)

This test file covers all the enhanced features of the CalibrationWizardDialog.
"""

import pytest
import sys
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import json
import tempfile
import shutil

# Mock PySide6 modules before importing the dialog
sys.modules["PySide6"] = Mock()
sys.modules["PySide6.QtWidgets"] = Mock()
sys.modules["PySide6.QtCore"] = Mock()
sys.modules["PySide6.QtGui"] = Mock()

# Mock Qt enums and classes
Qt = Mock()
Qt.AlignCenter = 1
Qt.Horizontal = 2

QSizePolicy = Mock()
QSizePolicy.Expanding = 1
QSizePolicy.Minimum = 2

Signal = Mock()

# Set up mocks for all Qt widgets
mock_qt_widgets = {}
for widget_name in [
    "QDialog", "QVBoxLayout", "QHBoxLayout", "QFormLayout", "QLabel", "QPushButton",
    "QDoubleSpinBox", "QDialogButtonBox", "QGroupBox", "QTextEdit", "QProgressBar",
    "QStackedWidget", "QWidget", "QFrame", "QGridLayout", "QSpacerItem", 
    "QCheckBox", "QComboBox", "QLineEdit", "QMessageBox", "QFileDialog", "QScrollArea"
]:
    mock_qt_widgets[widget_name] = Mock()

sys.modules["PySide6.QtWidgets"].__dict__.update(mock_qt_widgets)
sys.modules["PySide6.QtCore"].Qt = Qt
sys.modules["PySide6.QtCore"].Signal = Signal
sys.modules["PySide6.QtCore"].QTimer = Mock()
sys.modules["PySide6.QtGui"].QFont = Mock()
sys.modules["PySide6.QtGui"].QPixmap = Mock()

# Now import the actual classes
from src.components.dialogs.calibration_dialog import CalibrationWizardDialog, CalibrationStep, CalibrationDialog
from src.models.coordinate_transformer import CoordinateTransformer, CalibrationPoint

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

class TestCalibrationWizardDialog:
    """Test cases for CalibrationWizardDialog."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_transformer = Mock(spec=CoordinateTransformer)
        self.mock_transformer.calibration_points = []
        self.mock_transformer.is_calibrated = False
        self.mock_transformer.calibration_quality = {}
        self.mock_transformer.calibration_updated = Mock()
        self.mock_transformer.calibration_updated.connect = Mock()
        
        # Create temporary directory for template tests
        self.temp_dir = tempfile.mkdtemp()
        self.templates_dir = Path(self.temp_dir) / ".taskmaster" / "templates" / "calibration"
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_dialog_initialization(self):
        """Test dialog initializes correctly."""
        with patch("src.components.dialogs.calibration_dialog.LoggerMixin"):
            dialog = CalibrationWizardDialog(
                self.mock_transformer, 
                initial_pixel_x=100, 
                initial_pixel_y=150, 
                initial_label="Test Point"
            )
            
            assert dialog.coordinate_transformer == self.mock_transformer
            assert dialog.initial_pixel_x == 100
            assert dialog.initial_pixel_y == 150
            assert dialog.initial_label == "Test Point"
            assert dialog.current_step == CalibrationStep.INTRODUCTION
    
    def test_step_progression(self):
        """Test wizard step progression."""
        with patch("src.components.dialogs.calibration_dialog.LoggerMixin"):
            dialog = CalibrationWizardDialog(self.mock_transformer)
            
            # Start at introduction
            assert dialog.current_step == CalibrationStep.INTRODUCTION
            
            # Move to first point
            dialog.go_next()
            assert dialog.current_step == CalibrationStep.FIRST_POINT
            
            # Move to second point
            dialog.go_next()
            assert dialog.current_step == CalibrationStep.SECOND_POINT
            
            # Move back
            dialog.go_back()
            assert dialog.current_step == CalibrationStep.FIRST_POINT
    
    def test_point1_validation(self):
        """Test first point validation logic."""
        with patch("src.components.dialogs.calibration_dialog.LoggerMixin"):
            dialog = CalibrationWizardDialog(self.mock_transformer)
            
            # Mock input widgets
            dialog.point1_x_input = Mock()
            dialog.point1_y_input = Mock()
            
            # Test invalid case (both zero)
            dialog.point1_x_input.value.return_value = 0.0
            dialog.point1_y_input.value.return_value = 0.0
            assert not dialog.is_point1_valid()
            
            # Test valid case (non-zero values)
            dialog.point1_x_input.value.return_value = 100.5
            dialog.point1_y_input.value.return_value = 200.3
            assert dialog.is_point1_valid()
    
    def test_point2_validation(self):
        """Test second point validation logic."""
        with patch("src.components.dialogs.calibration_dialog.LoggerMixin"):
            dialog = CalibrationWizardDialog(self.mock_transformer, initial_pixel_x=100, initial_pixel_y=100)
            
            # Mock input widgets
            dialog.point2_x_input = Mock()
            dialog.point2_y_input = Mock()
            
            # Test with pixel coordinates set but too close
            dialog.pixel2_x = 120  # Only 20 pixels from initial (100, 100)
            dialog.pixel2_y = 120
            dialog.point2_x_input.value.return_value = 100.0
            dialog.point2_y_input.value.return_value = 200.0
            assert not dialog.is_point2_valid()  # Should be invalid due to distance
            
            # Test with pixel coordinates set and far enough
            dialog.pixel2_x = 200  # 100+ pixels from initial (100, 100)
            dialog.pixel2_y = 200
            assert dialog.is_point2_valid()  # Should be valid
    
    def test_point2_validation_bug_fix(self):
        """Test fix for second point validation bug: should not validate without pixel coordinates."""
        with patch("src.components.dialogs.calibration_dialog.LoggerMixin"):
            dialog = CalibrationWizardDialog(self.mock_transformer, initial_pixel_x=100, initial_pixel_y=100)
            
            # Mock input widgets
            dialog.point2_x_input = Mock()
            dialog.point2_y_input = Mock()
            
            # Test bug scenario: stage coordinates entered but NO pixel coordinates set
            dialog.point2_x_input.value.return_value = 1000.0  # Valid stage coordinates
            dialog.point2_y_input.value.return_value = 2000.0
            
            # Ensure pixel coordinates are NOT set (the bug scenario)
            if hasattr(dialog, 'pixel2_x'):
                delattr(dialog, 'pixel2_x')
            if hasattr(dialog, 'pixel2_y'):
                delattr(dialog, 'pixel2_y')
            
            # Should be invalid because pixel coordinates are missing
            assert not dialog.is_point2_valid()
            
            # Test after pixel coordinates are properly set
            dialog.pixel2_x = 200  # Far enough from initial (100, 100)
            dialog.pixel2_y = 200
            
            # Now should be valid
            assert dialog.is_point2_valid()
    
    def test_validate_point2_displays_correct_message(self):
        """Test that validate_point2 displays correct message when pixel coordinates are missing."""
        with patch("src.components.dialogs.calibration_dialog.LoggerMixin"):
            dialog = CalibrationWizardDialog(self.mock_transformer, initial_pixel_x=100, initial_pixel_y=100)
            
            # Mock UI components
            dialog.distance_label = Mock()
            dialog.point2_status = Mock()
            dialog.update_ui_state = Mock()
            
            # Ensure pixel coordinates are NOT set
            if hasattr(dialog, 'pixel2_x'):
                delattr(dialog, 'pixel2_x')
            if hasattr(dialog, 'pixel2_y'):
                delattr(dialog, 'pixel2_y')
            
            # Call validate_point2
            dialog.validate_point2()
            
            # Should display message asking to click on image first
            dialog.distance_label.setText.assert_called_with("Distance from first point: Click on image to set second point")
            dialog.point2_status.setText.assert_called_with("⚠️ Please click second point on the image first")
    
    def test_add_calibration_point(self):
        """Test adding calibration points."""
        with patch("src.components.dialogs.calibration_dialog.LoggerMixin"):
            dialog = CalibrationWizardDialog(self.mock_transformer)
            dialog.point_added = Mock()
            dialog.log_info = Mock()
            
            # Test successful addition
            self.mock_transformer.add_calibration_point.return_value = True
            
            dialog.add_calibration_point(100, 150, 1000.5, 2000.3, "Test Point")
            
            self.mock_transformer.add_calibration_point.assert_called_with(100, 150, 1000.5, 2000.3, "Test Point")
            dialog.point_added.emit.assert_called_with(100, 150, 1000.5, 2000.3, "Test Point")
            dialog.log_info.assert_called()
    
    def test_template_save(self):
        """Test template saving functionality."""
        with patch("src.components.dialogs.calibration_dialog.LoggerMixin"):
            with patch("src.components.dialogs.calibration_dialog.Path") as mock_path_class:
                # Setup path mocking
                mock_path_instance = Mock()
                mock_path_class.return_value = mock_path_instance
                mock_path_instance.absolute.return_value = "/test/path"
                
                templates_dir = Mock()
                mock_path_class.side_effect = lambda x: templates_dir if x == ".taskmaster/templates/calibration" else Mock()
                templates_dir.mkdir = Mock()
                
                template_file = Mock()
                templates_dir.__truediv__ = Mock(return_value=template_file)
                
                dialog = CalibrationWizardDialog(self.mock_transformer)
                dialog.template_name_input = Mock()
                dialog.template_name_input.text.return_value = "test_template"
                dialog.refresh_templates = Mock()
                dialog.log_info = Mock()
                
                # Mock the coordinate transformer export
                self.mock_transformer.export_calibration.return_value = {"test": "data"}
                
                with patch("builtins.open", create=True) as mock_open:
                    with patch("json.dump") as mock_json_dump:
                        with patch("src.components.dialogs.calibration_dialog.QMessageBox") as mock_msgbox:
                            dialog.save_template()
                            
                            mock_open.assert_called_once()
                            mock_json_dump.assert_called_once()
                            dialog.refresh_templates.assert_called_once()
    
    def test_set_second_point(self):
        """Test setting second point coordinates."""
        with patch("src.components.dialogs.calibration_dialog.LoggerMixin"):
            dialog = CalibrationWizardDialog(self.mock_transformer)
            dialog.pixel2_x_label = Mock()
            dialog.pixel2_y_label = Mock()
            dialog.validate_point2 = Mock()
            
            dialog.set_second_point(300, 400)
            
            assert dialog.pixel2_x == 300
            assert dialog.pixel2_y == 400
            dialog.pixel2_x_label.setText.assert_called_with("300")
            dialog.pixel2_y_label.setText.assert_called_with("400")
            dialog.validate_point2.assert_called_once()


class TestCalibrationDialogLegacy:
    """Test cases for legacy CalibrationDialog wrapper."""
    
    def test_legacy_dialog_creation(self):
        """Test legacy dialog creates correctly."""
        with patch("src.components.dialogs.calibration_dialog.LoggerMixin"):
            with patch("src.components.dialogs.calibration_dialog.CoordinateTransformer") as mock_transformer_class:
                mock_transformer = Mock()
                mock_transformer_class.return_value = mock_transformer
                mock_transformer.calibration_points = []
                mock_transformer.is_calibrated = False
                mock_transformer.calibration_quality = {}
                mock_transformer.calibration_updated = Mock()
                mock_transformer.calibration_updated.connect = Mock()
                
                dialog = CalibrationDialog(100, 150, "Test Point")
                
                assert dialog.current_step == CalibrationStep.FIRST_POINT
                assert dialog.initial_pixel_x == 100
                assert dialog.initial_pixel_y == 150
                assert dialog.initial_label == "Test Point"
    
    def test_legacy_methods(self):
        """Test legacy compatibility methods."""
        with patch("src.components.dialogs.calibration_dialog.LoggerMixin"):
            with patch("src.components.dialogs.calibration_dialog.CoordinateTransformer") as mock_transformer_class:
                mock_transformer = Mock()
                mock_transformer_class.return_value = mock_transformer
                mock_transformer.calibration_points = []
                mock_transformer.is_calibrated = False
                mock_transformer.calibration_quality = {}
                mock_transformer.calibration_updated = Mock()
                mock_transformer.calibration_updated.connect = Mock()
                
                dialog = CalibrationDialog(100, 150, "Test Point")
                
                # Test get_stage_coordinates with no inputs
                coords = dialog.get_stage_coordinates()
                assert coords == (0.0, 0.0)
                
                # Test set_stage_coordinates does nothing (placeholder)
                dialog.set_stage_coordinates(1000.0, 2000.0)  # Should not raise exception


class TestCalibrationStepEnum:
    """Test cases for CalibrationStep enum."""
    
    def test_step_values(self):
        """Test enum step values."""
        assert CalibrationStep.INTRODUCTION.value == 0
        assert CalibrationStep.FIRST_POINT.value == 1
        assert CalibrationStep.SECOND_POINT.value == 2
        assert CalibrationStep.QUALITY_CHECK.value == 3
        assert CalibrationStep.SAVE_TEMPLATE.value == 4


class TestLegacyCalibrationDialogFixes:
    """Test fixes for legacy CalibrationDialog wrapper bugs."""
    
    @pytest.fixture
    def mock_qt_app(self):
        """Mock QApplication for testing."""
        with patch('PySide6.QtWidgets.QApplication'):
            yield
    
    @pytest.fixture
    def existing_transformer(self):
        """Create a CoordinateTransformer with existing calibration data."""
        transformer = CoordinateTransformer()
        # Add some test calibration points
        transformer.add_calibration_point(100, 100, 1000.0, 2000.0, "Test Point 1")
        transformer.add_calibration_point(200, 200, 3000.0, 4000.0, "Test Point 2")
        return transformer
    
    def test_legacy_dialog_preserves_existing_transformer(self, mock_qt_app, existing_transformer):
        """Test that legacy dialog preserves existing CoordinateTransformer instance."""
        # Create legacy dialog with existing transformer
        dialog = CalibrationDialog(
            pixel_x=50, 
            pixel_y=60, 
            point_label="Legacy Point",
            parent=None,
            coordinate_transformer=existing_transformer
        )
        
        # Verify that the same transformer instance is used
        assert dialog.coordinate_transformer is existing_transformer
        
        # Verify that existing calibration points are preserved
        assert len(dialog.coordinate_transformer.calibration_points) == 2
        assert dialog.coordinate_transformer.calibration_points[0].stage_x == 1000.0
        assert dialog.coordinate_transformer.calibration_points[0].stage_y == 2000.0
    
    def test_legacy_dialog_backward_compatibility(self, mock_qt_app):
        """Test that legacy dialog still works without coordinate_transformer parameter."""
        # Create legacy dialog without transformer (old way)
        dialog = CalibrationDialog(
            pixel_x=50, 
            pixel_y=60, 
            point_label="Legacy Point",
            parent=None
        )
        
        # Should create new transformer instance
        assert dialog.coordinate_transformer is not None
        assert isinstance(dialog.coordinate_transformer, CoordinateTransformer)
        
        # Should start with empty calibration
        assert len(dialog.coordinate_transformer.calibration_points) == 0
    
    def test_get_stage_coordinates_returns_actual_input(self, mock_qt_app):
        """Test that get_stage_coordinates returns actual user input values."""
        dialog = CalibrationDialog(50, 60, "Test Point", parent=None)
        
        # Mock the input fields
        dialog.point1_x_input = Mock()
        dialog.point1_y_input = Mock()
        dialog.point1_x_input.value.return_value = 1234.567
        dialog.point1_y_input.value.return_value = 9876.543
        
        # Test that actual values are returned
        coordinates = dialog.get_stage_coordinates()
        assert coordinates == (1234.567, 9876.543)
    
    def test_get_stage_coordinates_fallback_when_no_inputs(self, mock_qt_app):
        """Test that get_stage_coordinates returns (0.0, 0.0) when inputs don't exist."""
        dialog = CalibrationDialog(50, 60, "Test Point", parent=None)
        
        # Don't set input fields (simulating before UI is fully initialized)
        coordinates = dialog.get_stage_coordinates()
        assert coordinates == (0.0, 0.0)
    
    def test_set_stage_coordinates_updates_inputs(self, mock_qt_app):
        """Test that set_stage_coordinates actually updates the input fields."""
        dialog = CalibrationDialog(50, 60, "Test Point", parent=None)
        
        # Mock the input fields and validation
        dialog.point1_x_input = Mock()
        dialog.point1_y_input = Mock()
        dialog.validate_point1 = Mock()
        
        # Set coordinates
        dialog.set_stage_coordinates(555.123, 777.456)
        
        # Verify inputs were set
        dialog.point1_x_input.setValue.assert_called_once_with(555.123)
        dialog.point1_y_input.setValue.assert_called_once_with(777.456)
        
        # Verify validation was triggered
        dialog.validate_point1.assert_called_once()
    
    def test_set_stage_coordinates_safe_when_no_inputs(self, mock_qt_app):
        """Test that set_stage_coordinates doesn't crash when inputs don't exist."""
        dialog = CalibrationDialog(50, 60, "Test Point", parent=None)
        
        # Should not raise exception
        dialog.set_stage_coordinates(123.456, 789.012)
    
    def test_legacy_dialog_round_trip_coordinates(self, mock_qt_app):
        """Test complete round-trip: set coordinates, then get them back."""
        dialog = CalibrationDialog(50, 60, "Test Point", parent=None)
        
        # Mock the input fields
        dialog.point1_x_input = Mock()
        dialog.point1_y_input = Mock()
        dialog.validate_point1 = Mock()
        
        # Set up mock to return the values that were set
        test_x, test_y = 1111.222, 3333.444
        dialog.point1_x_input.value.return_value = test_x
        dialog.point1_y_input.value.return_value = test_y
        
        # Set coordinates
        dialog.set_stage_coordinates(test_x, test_y)
        
        # Get coordinates back
        result = dialog.get_stage_coordinates()
        
        # Should get back the same values
        assert result == (test_x, test_y)
    
    def test_legacy_dialog_integration_with_wizard(self, mock_qt_app, existing_transformer):
        """Test that legacy dialog properly integrates with the wizard functionality."""
        dialog = CalibrationDialog(
            pixel_x=100, 
            pixel_y=200, 
            point_label="Integration Test",
            parent=None,
            coordinate_transformer=existing_transformer
        )
        
        # Should start at first point step (legacy behavior)
        from components.dialogs.calibration_dialog import CalibrationStep
        assert dialog.current_step == CalibrationStep.FIRST_POINT
        
        # Should preserve existing calibration data
        assert len(dialog.coordinate_transformer.calibration_points) == 2
        
        # Should be properly initialized as wizard dialog
        assert isinstance(dialog, CalibrationWizardDialog)


if __name__ == "__main__":
    pytest.main([__file__])
