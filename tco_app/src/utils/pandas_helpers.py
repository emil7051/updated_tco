"""Shared pandas utility functions for the TCO application."""
from typing import Union, Any
import pandas as pd
import numpy as np


def to_scalar(value: Union[float, int, pd.Series, np.ndarray]) -> float:
    """Convert various types to a scalar float value.
    
    Args:
        value: Input value which could be a scalar, Series, or array
        
    Returns:
        float: Scalar representation of the value
        
    Examples:
        >>> to_scalar(42.0)
        42.0
        >>> to_scalar(pd.Series([10.0]))
        10.0
        >>> to_scalar(pd.Series([]))  # Empty series
        0.0
    """
    if isinstance(value, pd.Series):
        if value.empty:
            return 0.0
        return float(value.iloc[0])
    
    if isinstance(value, np.ndarray):
        if value.size == 0:
            return 0.0
        return float(value.flat[0])
    
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def safe_get_first(
    df: pd.DataFrame, 
    condition: Union[pd.Series, bool],
    default: Any = None
) -> Union[pd.Series, Any]:
    """Safely get the first row matching a condition.
    
    Args:
        df: DataFrame to query
        condition: Boolean mask or condition
        default: Value to return if no rows match
        
    Returns:
        First matching row as Series, or default if none found
        
    Raises:
        ValueError: If condition is not boolean type
    """
    if not isinstance(condition, (pd.Series, bool)):
        raise ValueError("Condition must be a boolean Series or bool value")
    
    filtered = df[condition]
    if filtered.empty:
        return default
    return filtered.iloc[0]


def get_parameter_value(
    df: pd.DataFrame,
    key_column: str,
    key_value: str,
    value_column: str,
    default: Any = None
) -> Any:
    """Extract a parameter value from a key-value structured DataFrame.
    
    Args:
        df: DataFrame with parameter data
        key_column: Name of the column containing keys
        key_value: The key to look up
        value_column: Name of the column containing values
        default: Default value if key not found
        
    Returns:
        The value associated with the key, or default
        
    Examples:
        >>> df = pd.DataFrame({
        ...     'param_name': ['discount_rate', 'inflation_rate'],
        ...     'value': [0.07, 0.03]
        ... })
        >>> get_parameter_value(df, 'param_name', 'discount_rate', 'value')
        0.07
    """
    mask = df[key_column] == key_value
    if not mask.any():
        return default
    return df.loc[mask, value_column].iloc[0] 