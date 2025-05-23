"""Data access utilities for structured DataFrames."""
from typing import Any, Optional, Dict
from tco_app.src.constants import DataColumns, ParameterKeys
from tco_app.src import pd
from .pandas_helpers import get_parameter_value


class ParameterRepository:
    """Repository pattern for accessing parameter DataFrames."""
    
    def __init__(self, df: pd.DataFrame, key_column: str, value_column: str):
        """Initialize repository with DataFrame and column mappings.
        
        Args:
            df: DataFrame containing parameters
            key_column: Column name containing parameter keys
            value_column: Column name containing parameter values
        """
        self.df = df
        self.key_column = key_column
        self.value_column = value_column
        self._cache: Dict[str, Any] = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get parameter value by key.
        
        Args:
            key: Parameter key to look up
            default: Default value if key not found
            
        Returns:
            Parameter value or default
        """
        if key in self._cache:
            return self._cache[key]
        
        value = get_parameter_value(
            self.df, 
            self.key_column, 
            key, 
            self.value_column, 
            default
        )
        self._cache[key] = value
        return value
    
    def get_all(self) -> Dict[str, Any]:
        """Get all parameters as a dictionary."""
        return dict(zip(
            self.df[self.key_column], 
            self.df[self.value_column]
        ))
    
    def clear_cache(self) -> None:
        """Clear the internal cache."""
        self._cache.clear()


class FinancialParameters(ParameterRepository):
    """Specialised repository for financial parameters."""
    
    def __init__(self, df: pd.DataFrame):
        super().__init__(df, DataColumns.FINANCE_DESCRIPTION, DataColumns.FINANCE_DEFAULT_VALUE)
    
    @property
    def diesel_price(self) -> float:
        """Get diesel price parameter."""
        return self.get(ParameterKeys.DIESEL_PRICE, 2.03)
    
    @property
    def discount_rate(self) -> float:
        """Get discount rate as decimal."""
        return self.get(ParameterKeys.DISCOUNT_RATE, 0.05)
    
    @property
    def carbon_price(self) -> float:
        """Get carbon price per tonne."""
        return self.get(ParameterKeys.CARBON_PRICE, 0.0)


class BatteryParameters(ParameterRepository):
    """Specialised repository for battery parameters."""
    
    def __init__(self, df: pd.DataFrame):
        super().__init__(df, DataColumns.BATTERY_DESCRIPTION, DataColumns.BATTERY_DEFAULT_VALUE)
    
    @property
    def replacement_cost_per_kwh(self) -> float:
        """Get battery replacement cost per kWh."""
        return self.get(ParameterKeys.REPLACEMENT_COST, 150.0)
    
    @property
    def degradation_rate(self) -> float:
        """Get annual degradation rate as decimal."""
        return self.get(ParameterKeys.DEGRADATION_RATE, 0.025)
    
    @property
    def minimum_capacity(self) -> float:
        """Get minimum capacity threshold as decimal."""
        return self.get(ParameterKeys.MINIMUM_CAPACITY, 0.7) 