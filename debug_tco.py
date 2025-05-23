#!/usr/bin/env python3
"""Debug script to trace the KeyError: True issue in TCO calculations."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from tco_app.src.data_loading import load_data
from tco_app.repositories import VehicleRepository, ParametersRepository
from tco_app.services.tco_calculation_service import TCOCalculationService
from tco_app.services.dtos import CalculationRequest, CalculationParameters
from tco_app.src.constants import DataColumns

def debug_vehicle_data():
    """Debug the vehicle data access issue."""
    print("Loading data tables...")
    data_tables = load_data()
    
    print("\nChecking vehicle_models structure:")
    if 'vehicle_models' in data_tables:
        vm_df = data_tables['vehicle_models']
        print(f"Columns: {list(vm_df.columns)}")
        print(f"Shape: {vm_df.shape}")
        print(f"First few rows:\n{vm_df.head(2)}")
        
        # Check if BEV001 exists
        if 'vehicle_id' in vm_df.columns:
            bev_mask = vm_df['vehicle_id'] == 'BEV001'
            print(f"\nBEV001 exists: {bev_mask.any()}")
            if bev_mask.any():
                bev_data = vm_df[bev_mask].iloc[0]
                print(f"BEV001 data type: {type(bev_data)}")
                print(f"BEV001 data:\n{bev_data}")
                
                # Try to access data as the code does
                print(f"\nTrying to access VEHICLE_ID: {bev_data.get(DataColumns.VEHICLE_ID, 'N/A')}")
    
    print("\n" + "="*50 + "\n")
    
    # Now test the actual calculation flow
    print("Testing calculation flow...")
    
    vehicle_repo = VehicleRepository(data_tables)
    params_repo = ParametersRepository(data_tables)
    
    # Get vehicle data
    vehicle_data = vehicle_repo.get_vehicle_by_id('BEV001')
    print(f"\nVehicle data type: {type(vehicle_data)}")
    print(f"Vehicle data index: {vehicle_data.index.tolist()}")
    
    # Create minimal calculation parameters
    parameters = CalculationParameters(
        annual_kms=100000,
        truck_life_years=10,
        discount_rate=0.05,
        fleet_size=1,
        apply_incentives=True,  # This might be the issue
        charging_mix={1: 0.7, 2: 0.3},
        selected_charging_profile_id=1,
        selected_infrastructure_id=1,
        scenario_name='Debug'
    )
    
    # Try to access vehicle data in different ways
    print("\nTesting different access methods:")
    
    # Method 1: Direct column name
    try:
        print(f"vehicle_data['vehicle_id']: {vehicle_data['vehicle_id']}")
    except Exception as e:
        print(f"Error with ['vehicle_id']: {type(e).__name__}: {e}")
    
    # Method 2: Using .get()
    try:
        print(f"vehicle_data.get('vehicle_id'): {vehicle_data.get('vehicle_id')}")
    except Exception as e:
        print(f"Error with .get('vehicle_id'): {type(e).__name__}: {e}")
    
    # Method 3: Using DataColumns enum
    try:
        print(f"vehicle_data[DataColumns.VEHICLE_ID]: {vehicle_data[DataColumns.VEHICLE_ID]}")
    except Exception as e:
        print(f"Error with [DataColumns.VEHICLE_ID]: {type(e).__name__}: {e}")
    
    # Method 4: Check if True is somehow in the index
    if True in vehicle_data.index:
        print(f"\nWARNING: Boolean True found in vehicle_data index!")
        print(f"Value at True: {vehicle_data[True]}")
    
    # Check the apply_incentives parameter
    print(f"\napply_incentives value: {parameters.apply_incentives}")
    print(f"apply_incentives type: {type(parameters.apply_incentives)}")

if __name__ == "__main__":
    debug_vehicle_data()
