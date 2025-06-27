"""
Tests for Expression Filtering System (TASK-020)

Comprehensive tests for mathematical expression parsing, filtering UI,
and integration with scatter plot components.
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.expression_parser import (
    ExpressionParser, ExpressionResult, ExpressionType,
    ParseError, EvaluationError, SecurityError, StatisticalFunctions,
    evaluate_expression, validate_expression
)


class TestStatisticalFunctions:
    """Test statistical functions used in expressions."""
    
    def test_basic_statistics(self):
        """Test basic statistical functions."""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        
        assert StatisticalFunctions.mean(data) == 3.0
        assert StatisticalFunctions.std(data) == pytest.approx(1.41, rel=1e-2)
        assert StatisticalFunctions.min(data) == 1.0
        assert StatisticalFunctions.max(data) == 5.0
        assert StatisticalFunctions.median(data) == 3.0
        assert StatisticalFunctions.sum(data) == 15.0
        assert StatisticalFunctions.count(data) == 5.0
    
    def test_percentile_function(self):
        """Test percentile function."""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        
        assert StatisticalFunctions.percentile(data, 0) == 1.0
        assert StatisticalFunctions.percentile(data, 50) == 3.0
        assert StatisticalFunctions.percentile(data, 100) == 5.0
        
        # Test invalid percentile
        with pytest.raises(ValueError):
            StatisticalFunctions.percentile(data, -1)
        with pytest.raises(ValueError):
            StatisticalFunctions.percentile(data, 101)
    
    def test_nan_handling(self):
        """Test handling of NaN values."""
        data = np.array([1.0, 2.0, np.nan, 4.0, 5.0])
        
        assert StatisticalFunctions.mean(data) == 3.0  # Should ignore NaN
        assert StatisticalFunctions.count(data) == 4.0  # Should count non-NaN
        assert StatisticalFunctions.sum(data) == 12.0


class TestExpressionParser:
    """Test expression parser functionality."""
    
    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return ExpressionParser()
    
    @pytest.fixture
    def sample_data(self):
        """Create sample DataFrame."""
        np.random.seed(42)
        return pd.DataFrame({
            'area': np.random.uniform(50, 500, 100),
            'intensity': np.random.uniform(0, 1000, 100),
            'aspect_ratio': np.random.uniform(0.5, 3.0, 100),
            'circularity': np.random.uniform(0.1, 1.0, 100)
        })
    
    def test_basic_arithmetic(self, parser, sample_data):
        """Test basic arithmetic operations."""
        result = parser.evaluate_expression("area + 10", sample_data)
        
        assert result.error_message is None
        assert result.expression_type == ExpressionType.ARRAY
        assert isinstance(result.value, np.ndarray)
        assert len(result.value) == len(sample_data)
        
        # Check that values are correct
        expected = sample_data['area'].values + 10
        np.testing.assert_array_almost_equal(result.value, expected)
    
    def test_comparison_operations(self, parser, sample_data):
        """Test comparison operations."""
        result = parser.evaluate_expression("area > 200", sample_data)
        
        assert result.error_message is None
        assert result.expression_type == ExpressionType.BOOLEAN
        assert isinstance(result.value, np.ndarray)
        assert result.value.dtype == bool
        
        # Check that comparison is correct
        expected = sample_data['area'].values > 200
        np.testing.assert_array_equal(result.value, expected)
    
    def test_statistical_functions(self, parser, sample_data):
        """Test statistical functions in expressions."""
        result = parser.evaluate_expression("area > mean(area)", sample_data)
        
        assert result.error_message is None
        assert result.expression_type == ExpressionType.BOOLEAN
        
        # Check statistical function
        mean_area = sample_data['area'].mean()
        expected = sample_data['area'] > mean_area
        np.testing.assert_array_equal(result.value, expected.values)
    
    def test_expression_validation(self, parser):
        """Test expression validation."""
        columns = ['area', 'intensity', 'aspect_ratio']
        
        # Valid expression
        validation = parser.validate_expression("area > mean(area)", columns)
        assert validation['valid'] is True
        assert 'area' in validation['referenced_columns']
        
        # Invalid column
        validation = parser.validate_expression("unknown_column > 100", columns)
        assert validation['valid'] is False
        assert 'unknown_column' in validation['unknown_columns']


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_evaluate_expression_function(self):
        """Test standalone evaluate_expression function."""
        data = pd.DataFrame({'x': [1, 2, 3, 4, 5]})
        result = evaluate_expression("x > 3", data)
        
        assert result.error_message is None
        expected = np.array([False, False, False, True, True])
        np.testing.assert_array_equal(result.value, expected)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
