#!/usr/bin/env python3
"""Validation script to check safe operations implementation."""

import pandas as pd
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from tco_app.src.exceptions import DataNotFoundError, CalculationError
from tco_app.src.utils.safe_operations import (
    safe_iloc_zero,
    safe_lookup_vehicle,
    safe_division,
    safe_calculate,
    safe_get_parameter,
    safe_get_charging_option,
    validate_dataframe_columns
)
from tco_app.src.constants import DataColumns, ParameterKeys


def test_safe_operations():
    """Test all safe operations functions."""
    print("Testing safe operations...")
    
    # Test data
    test_df = pd.DataFrame({
        DataColumns.VEHICLE_ID: ['VEH001', 'VEH002'],
        DataColumns.VEHICLE_TYPE: ['Light', 'Heavy'],
        DataColumns.PAYLOAD_T: [2.0, 5.0]
    })
    
    financial_params = pd.DataFrame({
        DataColumns.FINANCE_DESCRIPTION: [ParameterKeys.DIESEL_PRICE, ParameterKeys.DISCOUNT_RATE],
        DataColumns.FINANCE_DEFAULT_VALUE: [2.0, 0.07]
    })
    
    charging_data = pd.DataFrame({
        DataColumns.CHARGING_ID: ['CHG001', 'CHG002'],
        DataColumns.PER_KWH_PRICE: [0.25, 0.30]
    })
    
    # Test 1: safe_iloc_zero with valid condition
    try:
        condition = test_df[DataColumns.VEHICLE_ID] == 'VEH001'
        result = safe_iloc_zero(test_df, condition, "test vehicle")
        assert result[DataColumns.VEHICLE_ID] == 'VEH001'
        print("✓ safe_iloc_zero with valid condition")
    except Exception as e:
        print(f"✗ safe_iloc_zero with valid condition: {e}")
    
    # Test 2: safe_iloc_zero with no matches
    try:
        condition = test_df[DataColumns.VEHICLE_ID] == 'NONEXISTENT'
        safe_iloc_zero(test_df, condition, "nonexistent vehicle")
        print("✗ safe_iloc_zero should have raised DataNotFoundError")
    except DataNotFoundError:
        print("✓ safe_iloc_zero properly raised DataNotFoundError")
    except Exception as e:
        print(f"✗ safe_iloc_zero unexpected error: {e}")
    
    # Test 3: safe_lookup_vehicle
    try:
        result = safe_lookup_vehicle(test_df, 'VEH002')
        assert result[DataColumns.PAYLOAD_T] == 5.0
        print("✓ safe_lookup_vehicle found vehicle")
    except Exception as e:
        print(f"✗ safe_lookup_vehicle: {e}")
    
    # Test 4: safe_division with valid denominator
    try:
        result = safe_division(10, 2, context="test division")
        assert result == 5.0
        print("✓ safe_division with valid denominator")
    except Exception as e:
        print(f"✗ safe_division: {e}")
    
    # Test 5: safe_division with zero denominator
    try:
        result = safe_division(10, 0, default=999.0, context="zero division test")
        assert result == 999.0
        print("✓ safe_division with zero denominator")
    except Exception as e:
        print(f"✗ safe_division with zero: {e}")
    
    # Test 6: safe_get_parameter
    try:
        price = safe_get_parameter(financial_params, ParameterKeys.DIESEL_PRICE)
        assert price == 2.0
        print("✓ safe_get_parameter found parameter")
    except Exception as e:
        print(f"✗ safe_get_parameter: {e}")
    
    # Test 7: safe_get_charging_option
    try:
        option = safe_get_charging_option(charging_data, 'CHG001')
        assert option[DataColumns.PER_KWH_PRICE] == 0.25
        print("✓ safe_get_charging_option found option")
    except Exception as e:
        print(f"✗ safe_get_charging_option: {e}")
    
    # Test 8: safe_calculate with successful function
    try:
        def test_func(a, b):
            return a + b
        
        result = safe_calculate(test_func, 5, 3, context="addition test")
        assert result == 8
        print("✓ safe_calculate with successful function")
    except Exception as e:
        print(f"✗ safe_calculate: {e}")
    
    # Test 9: safe_calculate with failing function
    try:
        def failing_func():
            raise ValueError("Test error")
        
        safe_calculate(failing_func, context="failing test")
        print("✗ safe_calculate should have raised CalculationError")
    except CalculationError:
        print("✓ safe_calculate properly raised CalculationError")
    except Exception as e:
        print(f"✗ safe_calculate unexpected error: {e}")
    
    # Test 10: validate_dataframe_columns
    try:
        validate_dataframe_columns(
            test_df, 
            [DataColumns.VEHICLE_ID, DataColumns.VEHICLE_TYPE], 
            "test DataFrame"
        )
        print("✓ validate_dataframe_columns with valid columns")
    except Exception as e:
        print(f"✗ validate_dataframe_columns: {e}")
    
    # Test 11: validate_dataframe_columns with missing columns
    try:
        validate_dataframe_columns(
            test_df, 
            [DataColumns.VEHICLE_ID, 'MISSING_COLUMN'], 
            "test DataFrame"
        )
        print("✗ validate_dataframe_columns should have raised ValueError")
    except ValueError:
        print("✓ validate_dataframe_columns properly raised ValueError")
    except Exception as e:
        print(f"✗ validate_dataframe_columns unexpected error: {e}")


def check_imports():
    """Check that safe operations can be imported from key modules."""
    print("\nChecking imports in updated modules...")
    
    try:
        # Test that domain modules can import and use safe operations
        from tco_app.domain.energy import calculate_energy_costs
        print("✓ tco_app.domain.energy imports successfully")
    except Exception as e:
        print(f"✗ tco_app.domain.energy import error: {e}")
    
    try:
        from tco_app.domain.finance import calculate_annual_costs
        print("✓ tco_app.domain.finance imports successfully")
    except Exception as e:
        print(f"✗ tco_app.domain.finance import error: {e}")
    
    try:
        from tco_app.domain.finance_payload import calculate_payload_penalty_costs
        print("✓ tco_app.domain.finance_payload imports successfully")
    except Exception as e:
        print(f"✗ tco_app.domain.finance_payload import error: {e}")


def main():
    """Run all validation tests."""
    print("=== Safe Operations Validation ===\n")
    
    test_safe_operations()
    check_imports()
    
    print("\n=== Validation Complete ===")


if __name__ == "__main__":
    main() 