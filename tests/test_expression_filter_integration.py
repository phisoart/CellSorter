"""
Test Expression Filter Integration

Tests to verify that expression filter is properly integrated with scatter plot widget
and main window.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock

from src.components.widgets.scatter_plot import ScatterPlotWidget, EXPRESSION_FILTER_AVAILABLE


class TestExpressionFilterIntegration:
    """Test cases for expression filter integration."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        return pd.DataFrame({
            'AreaShape_Area': [100, 200, 150, 300, 250],
            'Intensity_Mean': [50, 75, 60, 90, 80],
            'Location_Center_X': [10, 20, 15, 30, 25],
            'Location_Center_Y': [5, 10, 7, 15, 12]
        })
    
    @pytest.fixture
    def scatter_plot_widget(self):
        """Create scatter plot widget instance."""
        widget = ScatterPlotWidget()
        return widget
    
    def test_expression_filter_widget_initialization(self, scatter_plot_widget):
        """Test that expression filter widget is properly initialized if available."""
        if EXPRESSION_FILTER_AVAILABLE:
            assert scatter_plot_widget.expression_filter_widget is not None
            assert hasattr(scatter_plot_widget, 'tab_widget')
            # Should have both scatter plot and expression filter tabs
            assert scatter_plot_widget.tab_widget.count() == 2
        else:
            assert scatter_plot_widget.expression_filter_widget is None
            # Should only have scatter plot tab
            assert scatter_plot_widget.tab_widget.count() == 1
    
    def test_data_loading_to_expression_filter(self, scatter_plot_widget, sample_data):
        """Test that data is loaded into expression filter when available."""
        if EXPRESSION_FILTER_AVAILABLE and scatter_plot_widget.expression_filter_widget:
            # Mock the expression filter's load_data method
            scatter_plot_widget.expression_filter_widget.load_data = Mock()
            
            # Load data into scatter plot widget
            scatter_plot_widget.load_data(sample_data)
            
            # Verify expression filter received the data
            scatter_plot_widget.expression_filter_widget.load_data.assert_called_once_with(sample_data)
    
    def test_expression_selection_signal_connection(self, scatter_plot_widget):
        """Test that expression filter selection signal is properly connected."""
        if EXPRESSION_FILTER_AVAILABLE and scatter_plot_widget.expression_filter_widget:
            # Mock the selection_requested signal
            mock_signal = Mock()
            scatter_plot_widget.expression_filter_widget.selection_requested = mock_signal
            
            # Reconnect signals
            scatter_plot_widget.connect_signals()
            
            # Verify signal was connected
            mock_signal.connect.assert_called()
    
    def test_expression_selection_handling(self, scatter_plot_widget, sample_data):
        """Test that expression selections are properly handled."""
        # Load data first
        scatter_plot_widget.load_data(sample_data)
        
        # Mock canvas methods
        scatter_plot_widget.canvas.highlight_points = Mock()
        scatter_plot_widget.canvas.clear_selection = Mock()
        scatter_plot_widget.canvas.expression_color = '#2ca02c'
        
        # Test non-empty selection
        selected_indices = [1, 3, 4]
        scatter_plot_widget._on_expression_selection(selected_indices)
        
        # Verify highlighting was called
        scatter_plot_widget.canvas.highlight_points.assert_called_once_with(
            selected_indices, '#2ca02c'
        )
        
        # Verify status was updated
        assert "Expression filter selected 3 points" in scatter_plot_widget.status_label.text()
        
        # Reset mocks
        scatter_plot_widget.canvas.highlight_points.reset_mock()
        scatter_plot_widget.canvas.clear_selection.reset_mock()
        
        # Test empty selection
        scatter_plot_widget._on_expression_selection([])
        
        # Verify selection was cleared
        scatter_plot_widget.canvas.clear_selection.assert_called_once()
        assert "No points matched expression filter" in scatter_plot_widget.status_label.text()
    
    def test_get_current_expression(self, scatter_plot_widget):
        """Test getting current expression from expression filter."""
        if EXPRESSION_FILTER_AVAILABLE and scatter_plot_widget.expression_filter_widget:
            # Mock the get_current_expression method
            scatter_plot_widget.expression_filter_widget.get_current_expression = Mock(
                return_value="AreaShape_Area > 150"
            )
            
            result = scatter_plot_widget.get_current_expression()
            assert result == "AreaShape_Area > 150"
        else:
            # Should return empty string when expression filter not available
            result = scatter_plot_widget.get_current_expression()
            assert result == ""
    
    def test_tab_widget_structure(self, scatter_plot_widget):
        """Test that tab widget is properly structured."""
        assert hasattr(scatter_plot_widget, 'tab_widget')
        
        # First tab should always be scatter plot
        assert scatter_plot_widget.tab_widget.tabText(0) == "Scatter Plot"
        
        if EXPRESSION_FILTER_AVAILABLE:
            # Second tab should be expression filter
            if scatter_plot_widget.tab_widget.count() > 1:
                assert scatter_plot_widget.tab_widget.tabText(1) == "Expression Filter"
    
    @patch('src.components.widgets.scatter_plot.EXPRESSION_FILTER_AVAILABLE', False)
    def test_graceful_degradation_without_expression_filter(self):
        """Test that widget works properly when expression filter is not available."""
        widget = ScatterPlotWidget()
        
        # Should not have expression filter widget
        assert widget.expression_filter_widget is None
        
        # Should still be able to load data
        sample_data = pd.DataFrame({
            'AreaShape_Area': [100, 200, 150],
            'Intensity_Mean': [50, 75, 60]
        })
        
        # Should not raise any exceptions
        widget.load_data(sample_data)
        
        # get_current_expression should return empty string
        assert widget.get_current_expression() == ""


if __name__ == "__main__":
    pytest.main([__file__]) 