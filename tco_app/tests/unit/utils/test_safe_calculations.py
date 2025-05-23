"""Tests for safe calculation operations."""
import pytest
from unittest.mock import patch

from tco_app.src.exceptions import CalculationError
from tco_app.src.utils.safe_operations import (
    safe_division,
    safe_calculate
)


class TestSafeDivision:
    """Test safe_division function."""
    
    def test_normal_division(self):
        """Test normal division operation."""
        result = safe_division(10, 2)
        assert result == 5.0
    
    def test_division_by_zero_default(self):
        """Test division by zero with default return value."""
        with patch('tco_app.src.utils.safe_operations.logger') as mock_logger:
            result = safe_division(10, 0, default=999.0, context="test")
            
            assert result == 999.0
            mock_logger.warning.assert_called_once_with(
                "Division by zero in test, returning 999.0"
            )
    
    def test_division_by_zero_custom_default(self):
        """Test division by zero with custom default."""
        result = safe_division(5, 0, default=-1.0)
        assert result == -1.0
    
    def test_float_inputs(self):
        """Test with float inputs."""
        result = safe_division(7.5, 2.5)
        assert result == 3.0
    
    def test_negative_numbers(self):
        """Test with negative numbers."""
        result = safe_division(-10, 2)
        assert result == -5.0
        
        result = safe_division(10, -2)
        assert result == -5.0
    
    def test_return_type_is_float(self):
        """Test that result is always float."""
        result = safe_division(10, 2)
        assert isinstance(result, float)


class TestSafeCalculate:
    """Test safe_calculate function."""
    
    def test_successful_calculation(self):
        """Test successful function execution."""
        def add_numbers(a, b):
            return a + b
        
        result = safe_calculate(add_numbers, 5, 3, context="addition")
        assert result == 8
    
    def test_calculation_with_kwargs(self):
        """Test function execution with keyword arguments."""
        def multiply_with_factor(value, factor=2):
            return value * factor
        
        result = safe_calculate(
            multiply_with_factor, 
            5, 
            factor=3, 
            context="multiplication"
        )
        assert result == 15
    
    def test_function_raises_exception(self):
        """Test when the wrapped function raises an exception."""
        def failing_function():
            raise ValueError("Something went wrong")
        
        with patch('tco_app.src.utils.safe_operations.logger') as mock_logger:
            with pytest.raises(CalculationError) as exc_info:
                safe_calculate(failing_function, context="test calculation")
            
            assert "Failed to calculate test calculation" in str(exc_info.value)
            assert exc_info.value.calculation_type == "test calculation"
            assert isinstance(exc_info.value.__cause__, ValueError)
            
            mock_logger.error.assert_called_once()
    
    def test_lambda_function(self):
        """Test with lambda function."""
        result = safe_calculate(lambda x: x ** 2, 4, context="square")
        assert result == 16 