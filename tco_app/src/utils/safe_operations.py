"""Safe operations for DataFrame access and calculations."""
from typing import Any, Optional, Union, List
import pandas as pd
import logging

from tco_app.src.exceptions import DataNotFoundError, CalculationError
from tco_app.src.utils.pandas_helpers import safe_get_first

logger = logging.getLogger(__name__)


def safe_iloc_zero(
    df: pd.DataFrame,
    condition: pd.Series,
    context: str = "data"
) -> pd.Series:
    """Safely get first row with proper error handling.
    
    Args:
        df: DataFrame to query
        condition: Boolean condition for filtering
        context: Context for error message
        
    Returns:
        First matching row
        
    Raises:
        DataNotFoundError: If no rows match condition
    """
    result = safe_get_first(df, condition)
    if result is None:
        # Build helpful error message
        true_count = condition.sum() if isinstance(condition, pd.Series) else 0
        msg = (f"No {context} found matching the condition. "
               f"DataFrame has {len(df)} rows, {true_count} match condition.")
        raise DataNotFoundError(msg, dataframe_name=context)
    
    return result


def safe_lookup_vehicle(
    vehicle_models: pd.DataFrame,
    vehicle_id: str
) -> pd.Series:
    """Safely lookup a vehicle by ID.
    
    Args:
        vehicle_models: DataFrame containing vehicle data
        vehicle_id: Vehicle ID to lookup
        
    Returns:
        Vehicle data as Series
        
    Raises:
        DataNotFoundError: If vehicle not found
    """
    from tco_app.src.constants import DataColumns
    
    condition = vehicle_models[DataColumns.VEHICLE_ID] == vehicle_id
    try:
        return safe_iloc_zero(
            vehicle_models,
            condition,
            context=f"vehicle with ID '{vehicle_id}'"
        )
    except DataNotFoundError as e:
        # Add available IDs to help debugging
        available_ids = vehicle_models[DataColumns.VEHICLE_ID].tolist()
        e.args = (f"{e.args[0]} Available IDs: {available_ids[:5]}...",)
        raise


def safe_division(
    numerator: Union[float, int],
    denominator: Union[float, int],
    default: float = 0.0,
    context: str = "division"
) -> float:
    """Safely perform division with zero handling.
    
    Args:
        numerator: The numerator
        denominator: The denominator  
        default: Value to return if denominator is zero
        context: Context for logging
        
    Returns:
        Result of division or default
    """
    if denominator == 0:
        logger.warning(f"Division by zero in {context}, returning {default}")
        return default
    
    return float(numerator) / float(denominator)


def safe_calculate(
    func: callable,
    *args,
    context: str = "calculation",
    **kwargs
) -> Any:
    """Safely execute a calculation function with error handling.
    
    Args:
        func: Function to execute
        *args: Positional arguments for func
        context: Context for error message
        **kwargs: Keyword arguments for func
        
    Returns:
        Result of func
        
    Raises:
        CalculationError: If func raises any exception
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Calculation failed in {context}: {str(e)}", exc_info=True)
        raise CalculationError(
            f"Failed to calculate {context}: {str(e)}",
            calculation_type=context
        ) from e


def validate_dataframe_columns(
    df: pd.DataFrame,
    required_columns: List[str],
    context: str = "DataFrame"
) -> None:
    """Validate that DataFrame has required columns.
    
    Args:
        df: DataFrame to validate
        required_columns: List of required column names
        context: Context for error message
        
    Raises:
        ValueError: If any required columns are missing
    """
    missing_columns = set(required_columns) - set(df.columns)
    if missing_columns:
        raise ValueError(
            f"{context} is missing required columns: {missing_columns}. "
            f"Available columns: {list(df.columns)}"
        )


def safe_get_parameter(
    financial_params: pd.DataFrame,
    parameter_key: str,
    context: str = "financial parameter"
) -> float:
    """Safely get a financial parameter value.
    
    Args:
        financial_params: DataFrame with financial parameters
        parameter_key: Parameter key to lookup
        context: Context for error message
        
    Returns:
        Parameter value
        
    Raises:
        DataNotFoundError: If parameter not found
    """
    from tco_app.src.constants import DataColumns
    
    condition = financial_params[DataColumns.FINANCE_DESCRIPTION] == parameter_key
    param_row = safe_iloc_zero(
        financial_params,
        condition,
        context=f"{context} '{parameter_key}'"
    )
    return param_row[DataColumns.FINANCE_DEFAULT_VALUE]


def safe_get_charging_option(
    charging_data: pd.DataFrame,
    charging_id: str
) -> pd.Series:
    """Safely get charging option data.
    
    Args:
        charging_data: DataFrame with charging options
        charging_id: Charging option ID to lookup
        
    Returns:
        Charging option data as Series
        
    Raises:
        DataNotFoundError: If charging option not found
    """
    from tco_app.src.constants import DataColumns
    
    condition = charging_data[DataColumns.CHARGING_ID] == charging_id
    return safe_iloc_zero(
        charging_data,
        condition,
        context=f"charging option with ID '{charging_id}'"
    ) 