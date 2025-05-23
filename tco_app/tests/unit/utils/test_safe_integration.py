"""Integration tests for safe operations working together."""
import pytest
from tco_app.src import pd

from tco_app.src.exceptions import DataNotFoundError
from tco_app.src.utils.safe_operations import (
    safe_lookup_vehicle,
    safe_get_parameter,
    safe_division
)
from tco_app.src.constants import DataColumns, ParameterKeys


class TestIntegrationScenarios:
    """Integration tests for safe operations working together."""
    
    def test_chained_safe_operations(self):
        """Test multiple safe operations working together."""
        # Create test data
        vehicle_df = pd.DataFrame({
            DataColumns.VEHICLE_ID: ['VEH001'],
            DataColumns.VEHICLE_MODEL: ['Test Model'],
            DataColumns.PAYLOAD_T: [5.0]
        })
        
        financial_df = pd.DataFrame({
            DataColumns.FINANCE_DESCRIPTION: [ParameterKeys.DIESEL_PRICE],
            DataColumns.FINANCE_DEFAULT_VALUE: [2.0]
        })
        
        # Chain operations
        vehicle = safe_lookup_vehicle(vehicle_df, 'VEH001')
        diesel_price = safe_get_parameter(financial_df, ParameterKeys.DIESEL_PRICE)
        
        # Use safe division
        cost_per_tonne = safe_division(
            diesel_price * 100,  # Cost per 100km
            vehicle[DataColumns.PAYLOAD_T],  # Payload
            context="cost per tonne calculation"
        )
        
        assert cost_per_tonne == 40.0  # (2.0 * 100) / 5.0
    
    def test_error_propagation(self):
        """Test that errors propagate correctly through chained operations."""
        # Create test data with missing vehicle
        vehicle_df = pd.DataFrame({
            DataColumns.VEHICLE_ID: ['VEH001'],
            DataColumns.VEHICLE_MODEL: ['Test Model']
        })
        
        # This should raise DataNotFoundError
        with pytest.raises(DataNotFoundError):
            vehicle = safe_lookup_vehicle(vehicle_df, 'MISSING_VEH')
            # This would not execute due to the exception above
            safe_division(100, vehicle[DataColumns.PAYLOAD_T]) 