"""Financial calculation modules for TCO analysis."""
from typing import Dict, Any
from tco_app.src.constants import DataColumns, ParameterKeys
import pandas as pd

from tco_app.domain.finance import (
    calculate_annual_costs,
    calculate_acquisition_cost,
    calculate_npv,
    calculate_residual_value,
    calculate_tco,
)
from tco_app.src.utils.battery import calculate_battery_replacement


class FinancialCalculator:
    """Handles financial calculations."""
    
    def __init__(self, data_tables: Dict[str, pd.DataFrame], ui_context: Dict[str, Any]):
        self.data_tables = data_tables
        self.ui_context = ui_context
        self.modified_tables = ui_context['modified_tables']
    
    def calculate_annual_costs(self, vehicle_data: Dict[str, pd.Series], 
                              energy_costs: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate annual costs for both vehicles."""
        incentives = self.modified_tables['incentives']
        
        bev_annual_costs = calculate_annual_costs(
            vehicle_data['bev'],
            energy_costs['bev_fees'],
            energy_costs['bev'],
            self.ui_context['annual_kms'],
            incentives,
            self.ui_context['apply_incentives'],
        )
        
        diesel_annual_costs = calculate_annual_costs(
            vehicle_data['diesel'],
            energy_costs['diesel_fees'],
            energy_costs['diesel'],
            self.ui_context['annual_kms'],
            incentives,
            self.ui_context['apply_incentives'],
        )
        
        return {
            'bev': bev_annual_costs,
            'diesel': diesel_annual_costs
        }
    
    def calculate_acquisition_costs(self, vehicle_data: Dict[str, pd.Series]) -> Dict[str, Any]:
        """Calculate acquisition costs for both vehicles."""
        bev_fees = self.data_tables['vehicle_fees'][
            self.data_tables['vehicle_fees'][DataColumns.VEHICLE_ID] == self.ui_context['selected_bev_id']
        ]
        diesel_fees = self.data_tables['vehicle_fees'][
            self.data_tables['vehicle_fees'][DataColumns.VEHICLE_ID] == self.ui_context['comparison_diesel_id']
        ]
        incentives = self.modified_tables['incentives']
        
        bev_acquisition = calculate_acquisition_cost(
            vehicle_data['bev'], 
            bev_fees, 
            incentives, 
            self.ui_context['apply_incentives']
        )
        
        diesel_acquisition = calculate_acquisition_cost(
            vehicle_data['diesel'], 
            diesel_fees, 
            incentives, 
            self.ui_context['apply_incentives']
        )
        
        return {
            'bev': bev_acquisition,
            'diesel': diesel_acquisition
        }
    
    def calculate_residual_values(self, vehicle_data: Dict[str, pd.Series]) -> Dict[str, Any]:
        """Calculate residual values for both vehicles."""
        financial_params = self.modified_tables['financial_params']
        
        # Get depreciation parameters
        init_dep = financial_params[
            financial_params[DataColumns.FINANCE_DESCRIPTION] == 'initial_deprecation_percent'
        ].get(DataColumns.FINANCE_DEFAULT_VALUE, 0)
        
        annual_dep = financial_params[
            financial_params[DataColumns.FINANCE_DESCRIPTION] == ParameterKeys.ANNUAL_DEPRECIATION
        ].iloc[0][DataColumns.FINANCE_DEFAULT_VALUE]
        
        bev_residual = calculate_residual_value(
            vehicle_data['bev'], 
            self.ui_context['truck_life_years'], 
            init_dep, 
            annual_dep
        )
        
        diesel_residual = calculate_residual_value(
            vehicle_data['diesel'], 
            self.ui_context['truck_life_years'], 
            init_dep, 
            annual_dep
        )
        
        return {
            'bev': bev_residual,
            'diesel': diesel_residual
        }
    
    def calculate_battery_replacement(self, vehicle_data: Dict[str, pd.Series]) -> Dict[str, Any]:
        """Calculate battery replacement costs (BEV only)."""
        battery_params = self._apply_ui_battery_parameters()
        
        bev_battery_replacement = calculate_battery_replacement(
            vehicle_data['bev'],
            battery_params,
            self.ui_context['truck_life_years'],
            self.ui_context['discount_rate'],
        )
        
        return {
            'bev': bev_battery_replacement,
            'diesel': 0  # No battery replacement for diesel
        }
    
    def calculate_npv_annual_costs(self, annual_costs: Dict[str, Any]) -> Dict[str, float]:
        """Calculate NPV of annual costs."""
        bev_npv = calculate_npv(
            annual_costs['bev']['annual_operating_cost'], 
            self.ui_context['discount_rate'], 
            self.ui_context['truck_life_years']
        )
        
        diesel_npv = calculate_npv(
            annual_costs['diesel']['annual_operating_cost'], 
            self.ui_context['discount_rate'], 
            self.ui_context['truck_life_years']
        )
        
        return {
            'bev': bev_npv,
            'diesel': diesel_npv
        }
    
    def calculate_tco_results(self, vehicle_data: Dict[str, pd.Series], 
                             annual_costs: Dict[str, Any], 
                             acquisition_costs: Dict[str, Any],
                             residual_values: Dict[str, Any], 
                             battery_replacement: Dict[str, Any],
                             npv_annual_costs: Dict[str, float]) -> Dict[str, Any]:
        """Calculate TCO for both vehicles."""
        bev_fees = self.data_tables['vehicle_fees'][
            self.data_tables['vehicle_fees'][DataColumns.VEHICLE_ID] == self.ui_context['selected_bev_id']
        ]
        diesel_fees = self.data_tables['vehicle_fees'][
            self.data_tables['vehicle_fees'][DataColumns.VEHICLE_ID] == self.ui_context['comparison_diesel_id']
        ]
        
        bev_tco = calculate_tco(
            vehicle_data['bev'],
            bev_fees,
            annual_costs['bev'],
            acquisition_costs['bev'],
            residual_values['bev'],
            battery_replacement['bev'],
            npv_annual_costs['bev'],
            self.ui_context['annual_kms'],
            self.ui_context['truck_life_years'],
        )
        
        diesel_tco = calculate_tco(
            vehicle_data['diesel'],
            diesel_fees,
            annual_costs['diesel'],
            acquisition_costs['diesel'],
            residual_values['diesel'],
            battery_replacement['diesel'],
            npv_annual_costs['diesel'],
            self.ui_context['annual_kms'],
            self.ui_context['truck_life_years'],
        )
        
        return {
            'bev': bev_tco,
            'diesel': diesel_tco
        }
    
    def _apply_ui_battery_parameters(self) -> pd.DataFrame:
        """Apply UI overrides to battery parameters."""
        battery_params = self.modified_tables['battery_params'].copy()
        
        # Apply degradation rate
        mask = battery_params[DataColumns.BATTERY_DESCRIPTION] == ParameterKeys.DEGRADATION_RATE
        battery_params.loc[mask, DataColumns.FINANCE_DEFAULT_VALUE] = self.ui_context['degradation_rate']
        
        # Apply replacement cost
        mask = battery_params[DataColumns.BATTERY_DESCRIPTION] == ParameterKeys.REPLACEMENT_COST
        battery_params.loc[mask, DataColumns.FINANCE_DEFAULT_VALUE] = self.ui_context['replacement_cost']
        
        return battery_params 