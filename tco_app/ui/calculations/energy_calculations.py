"""Energy calculation modules for TCO analysis."""
from typing import Dict, Any
from tco_app.src.constants import DataColumns, ParameterKeys
import pandas as pd

from tco_app.domain.energy import calculate_energy_costs, calculate_emissions


class EnergyCalculator:
    """Handles energy-related calculations."""
    
    def __init__(self, data_tables: Dict[str, pd.DataFrame], ui_context: Dict[str, Any]):
        self.data_tables = data_tables
        self.ui_context = ui_context
    
    def calculate_energy_costs(self, vehicle_data: Dict[str, pd.Series]) -> Dict[str, Any]:
        """Calculate energy costs for both vehicles."""
        vehicle_fees = self.data_tables['vehicle_fees']
        charging_options = self.data_tables['charging_options']
        modified_tables = self.ui_context['modified_tables']
        financial_params = modified_tables['financial_params']
        
        bev_fees = vehicle_fees[vehicle_fees[DataColumns.VEHICLE_ID] == self.ui_context['selected_bev_id']]
        diesel_fees = vehicle_fees[vehicle_fees[DataColumns.VEHICLE_ID] == self.ui_context['comparison_diesel_id']]
        
        bev_energy_cost = calculate_energy_costs(
            vehicle_data['bev'],
            bev_fees,
            charging_options,
            financial_params,
            self.ui_context['selected_charging'],
            self.ui_context['charging_mix'],
        )
        
        diesel_energy_cost = calculate_energy_costs(
            vehicle_data['diesel'],
            diesel_fees,
            charging_options,
            financial_params,
            self.ui_context['selected_charging'],
        )
        
        return {
            'bev': bev_energy_cost,
            'diesel': diesel_energy_cost,
            'bev_fees': bev_fees,
            'diesel_fees': diesel_fees
        }
    
    def calculate_emissions(self, vehicle_data: Dict[str, pd.Series]) -> Dict[str, Any]:
        """Calculate emissions for both vehicles."""
        emission_factors = self.data_tables['emission_factors']
        
        bev_emissions = calculate_emissions(
            vehicle_data['bev'], 
            emission_factors, 
            self.ui_context['annual_kms'], 
            self.ui_context['truck_life_years']
        )
        
        diesel_emissions = calculate_emissions(
            vehicle_data['diesel'], 
            emission_factors, 
            self.ui_context['annual_kms'], 
            self.ui_context['truck_life_years']
        )
        
        return {
            'bev': bev_emissions,
            'diesel': diesel_emissions
        } 