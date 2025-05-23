"""Vehicle selection builder for UI context."""
from typing import Dict, Any
import pandas as pd
import streamlit as st

from tco_app.src.constants import Drivetrain


class VehicleSelectionBuilder:
    """Builds vehicle selection context."""
    
    def __init__(self, data_tables: Dict[str, pd.DataFrame]):
        self.data_tables = data_tables
        self.vehicle_type = None
        self.selected_bev_id = None
        self.comparison_diesel_id = None
    
    def select_vehicles(self) -> 'VehicleSelectionBuilder':
        """Handle vehicle selection UI."""
        vehicle_models = self.data_tables['vehicle_models']
        
        self.vehicle_type = st.selectbox(
            'Vehicle Type',
            ['Light Rigid', 'Medium Rigid', 'Articulated']
        )
        
        # Filter vehicles by type
        type_vehicles = vehicle_models[
            vehicle_models[DataColumns.VEHICLE_TYPE] == self.vehicle_type
        ]
        bev_vehicles = type_vehicles[
            type_vehicles[DataColumns.VEHICLE_DRIVETRAIN] == Drivetrain.BEV
        ]
        
        self.selected_bev_id = st.selectbox(
            'Select BEV Model',
            bev_vehicles[DataColumns.VEHICLE_ID].tolist(),
            format_func=lambda x: vehicle_models[
                vehicle_models[DataColumns.VEHICLE_ID] == x
            ].iloc[0][DataColumns.VEHICLE_MODEL]
        )
        
        # Get comparison diesel
        selected_bev = vehicle_models[
            vehicle_models[DataColumns.VEHICLE_ID] == self.selected_bev_id
        ].iloc[0]
        self.comparison_diesel_id = selected_bev[DataColumns.COMPARISON_PAIR_ID]
        
        # Show diesel info
        diesel_model = vehicle_models[
            vehicle_models[DataColumns.VEHICLE_ID] == self.comparison_diesel_id
        ].iloc[0][DataColumns.VEHICLE_MODEL]
        st.info(f'Comparison Diesel: {diesel_model}')
        
        return self
    
    def build(self) -> Dict[str, Any]:
        """Return vehicle selection context."""
        if not all([self.vehicle_type, self.selected_bev_id, self.comparison_diesel_id]):
            raise ValueError("Vehicle selection must be completed before building context")
            
        return {
            DataColumns.VEHICLE_TYPE: self.vehicle_type,
            'selected_bev_id': self.selected_bev_id,
            'comparison_diesel_id': self.comparison_diesel_id
        } 