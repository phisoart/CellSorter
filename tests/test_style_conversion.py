"""
Style Conversion Tests

Tests for CSS variable to Qt stylesheet conversion functionality.
"""

import pytest
from unittest.mock import Mock, patch

from src.components.base.base_button import BaseButton, ButtonVariant, ButtonSize
from src.components.base.base_input import BaseInput
from src.components.base.base_card import BaseCard
from src.utils.style_converter import convert_css_to_qt
from src.utils.theme_manager import ThemeManager


class TestStyleConversion:
    """Test CSS variable conversion in components."""
    
    def test_css_variable_conversion(self):
        """Test that CSS variables are properly converted to Qt values."""
        css_with_vars = """
        QPushButton {
            background-color: var(--primary);
            color: var(--primary-foreground);
            border: 1px solid var(--border);
        }
        """
        
        color_vars = {
            'primary': 'hsl(222.2, 47.4%, 11.2%)',
            'primary_foreground': 'hsl(210, 40%, 98%)',
            'border': 'hsl(214.3, 31.8%, 91.4%)'
        }
        
        result = convert_css_to_qt(css_with_vars, color_vars)
        
        # Check that CSS variables are replaced with actual colors
        assert 'var(--primary)' not in result
        assert 'var(--primary-foreground)' not in result
        assert 'var(--border)' not in result
        # Check that hex colors are present (actual converted values)
        assert '#0f172a' in result  # primary color
        assert '#f7f9fb' in result  # primary-foreground color  
        assert '#e2e8f0' in result  # border color
    
    def test_base_button_uses_converted_styles(self):
        """Test that BaseButton uses converted styles without CSS variables."""
        with patch('src.components.base.base_button.DesignTokens') as mock_tokens:
            mock_tokens.return_value.get_font_string.return_value = "Inter"
            mock_tokens.BUTTON_SIZES = {
                'default': {'height': 40, 'padding_h': 16, 'font_size': 14}
            }
            mock_tokens.TYPOGRAPHY = {'font_medium': 500}
            mock_tokens.BORDER_RADIUS = {'radius_default': 6}
            mock_tokens.FOCUS_STYLES = {'ring_width': 2, 'ring_offset': 2}
            mock_tokens.TRANSITIONS = {'default': 'all 0.2s ease'}
            
            button = BaseButton("Test Button")
            
            # Get the applied stylesheet
            stylesheet = button.styleSheet()
            
            # Check that no CSS variables remain
            assert 'var(--' not in stylesheet
    
    def test_base_input_uses_converted_styles(self):
        """Test that BaseInput uses converted styles without CSS variables."""
        with patch('src.components.base.base_input.DesignTokens') as mock_tokens:
            mock_tokens.return_value.get_font_string.return_value = "Inter"
            mock_tokens.TYPOGRAPHY = {'text_sm': 14}
            mock_tokens.BORDER_RADIUS = {'radius_default': 6}
            mock_tokens.SPACING = {'spacing_2': 8, 'spacing_3': 12}
            mock_tokens.DIMENSIONS = {'input_height': 40}
            mock_tokens.FOCUS_STYLES = {'ring_width': 2, 'ring_offset': 2}
            mock_tokens.TRANSITIONS = {'default': 'all 0.2s ease'}
            
            input_field = BaseInput("Test Input")
            
            # Get the applied stylesheet
            stylesheet = input_field.styleSheet()
            
            # Check that no CSS variables remain
            assert 'var(--' not in stylesheet
    
    def test_base_card_uses_converted_styles(self):
        """Test that BaseCard uses converted styles without CSS variables."""
        with patch('src.components.base.base_card.DesignTokens') as mock_tokens:
            mock_tokens.return_value.get_font_string.return_value = "Inter"
            mock_tokens.SPACING = {'spacing_6': 24}
            mock_tokens.TYPOGRAPHY = {'text_lg': 18, 'font_semibold': 600}
            mock_tokens.BORDER_RADIUS = {'radius_lg': 8}
            mock_tokens.SHADOWS = {'shadow': 'box-shadow: 0 1px 3px rgba(0,0,0,0.1)', 'shadow_md': 'box-shadow: 0 4px 6px rgba(0,0,0,0.1)'}
            
            card = BaseCard("Test Card")
            
            # Get the applied stylesheet
            stylesheet = card.styleSheet()
            
            # Check that no CSS variables remain
            assert 'var(--' not in stylesheet
    
    def test_theme_manager_integration(self):
        """Test that components can get color values from theme manager."""
        with patch('PySide6.QtWidgets.QApplication') as mock_app:
            theme_manager = ThemeManager(mock_app)
            
            # Test getting color values
            primary_color = theme_manager.get_color('primary')
            assert primary_color.startswith('hsl(')
            
            # Test that theme changes emit signals
            with patch.object(theme_manager, 'theme_changed') as mock_signal:
                theme_manager.apply_theme('dark')
                mock_signal.emit.assert_called_once_with('dark') 