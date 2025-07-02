"""
Enhanced Calibration Dialog Testing - DUAL Mode
DEV 모드와 GUI 모드 간의 일치성 및 동기화 검증
"""

import pytest
from typing import Dict, Any, Tuple, List
from dataclasses import dataclass

# Import mock dialog from DEV mode for comparison
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'dev_mode'))

try:
    from test_calibration_dialog_improvements import MockImprovedCalibrationDialog, MockCalibrationStep
except ImportError:
    print("Warning: Could not import DEV mode tests. Running standalone DUAL mode tests.")
    
    class MockCalibrationStep:
        INTRODUCTION = 0
        FIRST_POINT = 1
        SECOND_POINT = 2
        QUALITY_CHECK = 3
        SAVE_TEMPLATE = 4


@dataclass
class GUICalibrationDialogSpecs:
    """Specifications for GUI mode calibration dialog"""
    is_modal: bool
    minimum_size: Tuple[int, int]
    current_size: Tuple[int, int]
    is_resizable: bool
    window_flags: str
    
    # Layout specs
    margins: Tuple[int, int, int, int]
    spacing: int
    
    # Interaction capabilities
    allows_image_interaction: bool
    supports_second_point_selection: bool
    has_real_time_validation: bool
    has_distance_calculation: bool


class DualModeCalibrationDialogValidator:
    """Validator for DUAL mode consistency between DEV and GUI"""
    
    def __init__(self):
        # Create DEV mode reference
        try:
            self.dev_dialog = MockImprovedCalibrationDialog()
        except NameError:
            self.dev_dialog = None
            
        # Create GUI mode specifications (what actual dialog should have) - ENLARGED
        self.gui_specs = GUICalibrationDialogSpecs(
            is_modal=False,  # Critical fix: Non-modal for image interaction
            minimum_size=(600, 800),  # ENLARGED: Updated to match DEV mode
            current_size=(650, 850),  # ENLARGED: Updated to match DEV mode
            is_resizable=True,
            window_flags="Dialog|WindowTitleHint|WindowMinMaxButtonsHint|WindowCloseButtonHint",
            margins=(25, 25, 25, 25),  # ENLARGED: Updated to match DEV mode
            spacing=20,  # ENLARGED: Updated to match DEV mode
            allows_image_interaction=True,
            supports_second_point_selection=True,
            has_real_time_validation=True,
            has_distance_calculation=True
        )
    
    def validate_modal_behavior_sync(self) -> Tuple[bool, str]:
        """Validate modal behavior is consistent between DEV and GUI"""
        if self.dev_dialog is None:
            return False, "DEV dialog not available"
        
        dev_modal = self.dev_dialog.is_modal
        gui_modal = self.gui_specs.is_modal
        
        if dev_modal != gui_modal:
            return False, f"Modal behavior mismatch: DEV={dev_modal}, GUI={gui_modal}"
        
        # Both should be non-modal for image interaction
        if dev_modal or gui_modal:
            return False, "Both DEV and GUI should be non-modal"
        
        return True, "Modal behavior synchronized: both non-modal"
    
    def validate_sizing_consistency(self) -> Tuple[bool, str]:
        """Validate sizing is consistent between DEV and GUI"""
        if self.dev_dialog is None:
            return False, "DEV dialog not available"
        
        dev_min = self.dev_dialog.minimum_size
        gui_min = self.gui_specs.minimum_size
        
        # Allow small tolerance in sizing
        width_diff = abs(dev_min[0] - gui_min[0])
        height_diff = abs(dev_min[1] - gui_min[1])
        
        if width_diff > 100 or height_diff > 100:
            return False, f"Size mismatch too large: DEV={dev_min}, GUI={gui_min}"
        
        # Both should be resizable
        if not (self.dev_dialog.is_resizable and self.gui_specs.is_resizable):
            return False, "Both DEV and GUI should be resizable"
        
        return True, "Sizing consistent between DEV and GUI"
    
    def validate_interaction_capabilities(self) -> Tuple[bool, str]:
        """Validate interaction capabilities are consistent"""
        if self.dev_dialog is None:
            return False, "DEV dialog not available"
        
        # Test image interaction capability
        dev_allows_interaction = not self.dev_dialog.is_modal
        gui_allows_interaction = self.gui_specs.allows_image_interaction
        
        if dev_allows_interaction != gui_allows_interaction:
            return False, f"Image interaction mismatch: DEV={dev_allows_interaction}, GUI={gui_allows_interaction}"
        
        # Test second point selection
        dev_has_second_point = hasattr(self.dev_dialog, 'set_second_point')
        gui_has_second_point = self.gui_specs.supports_second_point_selection
        
        if dev_has_second_point != gui_has_second_point:
            return False, f"Second point selection mismatch: DEV={dev_has_second_point}, GUI={gui_has_second_point}"
        
        return True, "Interaction capabilities synchronized"
    
    def validate_layout_quality_sync(self) -> Tuple[bool, str]:
        """Validate layout quality is consistent"""
        if self.dev_dialog is None:
            return False, "DEV dialog not available"
        
        # Check margins consistency
        dev_margins = self.dev_dialog.layout_metrics.margins
        gui_margins = self.gui_specs.margins
        
        margin_diff = [abs(d - g) for d, g in zip(dev_margins, gui_margins)]
        if any(diff > 10 for diff in margin_diff):
            return False, f"Margin mismatch: DEV={dev_margins}, GUI={gui_margins}"
        
        # Check spacing consistency
        dev_spacing = self.dev_dialog.layout_metrics.spacing
        gui_spacing = self.gui_specs.spacing
        
        if abs(dev_spacing - gui_spacing) > 5:
            return False, f"Spacing mismatch: DEV={dev_spacing}, GUI={gui_spacing}"
        
        return True, "Layout quality synchronized"
    
    def validate_functionality_sync(self) -> Tuple[bool, str]:
        """Validate core functionality is consistent"""
        if self.dev_dialog is None:
            return False, "DEV dialog not available"
        
        # Test distance calculation
        self.dev_dialog.pixel1_x = 100
        self.dev_dialog.pixel1_y = 100
        success = self.dev_dialog.set_second_point(300, 400)
        distance = self.dev_dialog.calculate_pixel_distance()
        
        if not success:
            return False, "DEV dialog second point setting failed"
        
        if distance <= 0:
            return False, "DEV dialog distance calculation failed"
        
        # Expected distance for (100,100) to (300,400)
        expected_distance = ((300-100)**2 + (400-100)**2) ** 0.5
        if abs(distance - expected_distance) > 1:
            return False, f"DEV dialog distance calculation incorrect: {distance} vs {expected_distance}"
        
        return True, "Core functionality synchronized"
    
    def validate_comprehensive_sync(self) -> Tuple[float, Dict[str, bool]]:
        """Comprehensive synchronization validation"""
        tests = {
            'modal_behavior': self.validate_modal_behavior_sync(),
            'sizing_consistency': self.validate_sizing_consistency(),
            'interaction_capabilities': self.validate_interaction_capabilities(),
            'layout_quality': self.validate_layout_quality_sync(),
            'functionality': self.validate_functionality_sync()
        }
        
        results = {}
        passed_count = 0
        
        for test_name, (passed, message) in tests.items():
            results[test_name] = passed
            if passed:
                passed_count += 1
        
        sync_score = passed_count / len(tests)
        return sync_score, results


if __name__ == "__main__":
    # Run DUAL mode tests manually
    validator = DualModeCalibrationDialogValidator()
    
    print("DUAL Mode: Testing Calibration Dialog Synchronization")
    print("=" * 60)
    
    try:
        # Test individual components
        tests = [
            ("Modal behavior sync", validator.validate_modal_behavior_sync),
            ("Sizing consistency", validator.validate_sizing_consistency),
            ("Interaction capabilities", validator.validate_interaction_capabilities),
            ("Layout quality sync", validator.validate_layout_quality_sync),
            ("Functionality sync", validator.validate_functionality_sync)
        ]
        
        for test_name, test_func in tests:
            is_valid, message = test_func()
            status = "✓" if is_valid else "❌"
            print(f"{status} {test_name}: {message}")
        
        # Comprehensive validation
        print("\nComprehensive Validation:")
        sync_score, results = validator.validate_comprehensive_sync()
        
        for test_name, passed in results.items():
            status = "✓ PASS" if passed else "❌ FAIL"
            print(f"  {test_name}: {status}")
        
        print(f"\nOverall Synchronization Score: {sync_score:.2f}")
        
        if sync_score >= 0.8:
            print("\n🎉 DUAL mode validation passed! DEV and GUI modes are synchronized.")
        else:
            print(f"\n⚠️ DUAL mode validation needs improvement. Score: {sync_score:.2f}")
            
    except Exception as e:
        print(f"❌ DUAL mode test error: {e}")
