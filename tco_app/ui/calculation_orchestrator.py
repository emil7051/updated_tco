"""Orchestrates TCO calculations after UI context is built."""
from typing import Dict, Any
from tco_app.src.constants import DataColumns, ParameterKeys
import pandas as pd

from tco_app.domain.energy import calculate_charging_requirements
from tco_app.domain.finance import (
    calculate_infrastructure_costs,
    apply_infrastructure_incentives,
    integrate_infrastructure_with_tco,
)
from tco_app.domain.externalities import (
    calculate_externalities,
    calculate_social_tco,
)
from tco_app.domain.sensitivity import calculate_comparative_metrics
from tco_app.src.utils.energy import weighted_electricity_price
from tco_app.ui.calculations.energy_calculations import EnergyCalculator
from tco_app.ui.calculations.financial_calculations import FinancialCalculator
from tco_app.services.data_cache import get_vehicle_with_cache


class CalculationOrchestrator:
    """Orchestrates TCO calculations using UI context."""
    
    def __init__(self, data_tables: Dict[str, pd.DataFrame], ui_context: Dict[str, Any]):
        self.data_tables = data_tables
        self.ui_context = ui_context
        self.modified_tables = ui_context['modified_tables']
        
        # Initialize calculators
        self.energy_calculator = EnergyCalculator(data_tables, ui_context)
        self.financial_calculator = FinancialCalculator(data_tables, ui_context)
    
    def perform_calculations(self) -> Dict[str, Any]:
        """Perform all TCO calculations and return complete context."""
        print("Starting core TCO calculations...")
        
        # Extract vehicle data
        vehicle_data = self._get_vehicle_data()
        
        # Use calculator classes
        energy_costs = self.energy_calculator.calculate_energy_costs(vehicle_data)
        emissions = self.energy_calculator.calculate_emissions(vehicle_data)
        annual_costs = self.financial_calculator.calculate_annual_costs(vehicle_data, energy_costs)
        acquisition_costs = self.financial_calculator.calculate_acquisition_costs(vehicle_data)
        residual_values = self.financial_calculator.calculate_residual_values(vehicle_data)
        battery_replacement = self.financial_calculator.calculate_battery_replacement(vehicle_data)
        npv_annual_costs = self.financial_calculator.calculate_npv_annual_costs(annual_costs)
        tco_results = self.financial_calculator.calculate_tco_results(
            vehicle_data, annual_costs, acquisition_costs, 
            residual_values, battery_replacement, npv_annual_costs
        )
        
        # Calculate externalities
        externalities = self._calculate_externalities(vehicle_data)
        
        # Calculate infrastructure costs
        infrastructure_costs = self._calculate_infrastructure_costs(vehicle_data)
        
        # Build final results
        results = self._build_results(
            vehicle_data, energy_costs, annual_costs, emissions,
            acquisition_costs, residual_values, battery_replacement,
            npv_annual_costs, tco_results, externalities, infrastructure_costs
        )
        
        print("Core TCO calculations complete.")
        return results
    
    def _get_vehicle_data(self) -> Dict[str, pd.Series]:
        """Extract vehicle data for BEV and diesel with caching optimisation."""
        vehicle_models = self.modified_tables['vehicle_models']
        
        # Use cached vehicle lookups for better performance
        bev_vehicle_data = get_vehicle_with_cache(
            vehicle_models, 
            self.ui_context['selected_bev_id']
        )
        
        diesel_vehicle_data = get_vehicle_with_cache(
            vehicle_models, 
            self.ui_context['comparison_diesel_id']
        )
        
        return {
            'bev': bev_vehicle_data,
            'diesel': diesel_vehicle_data
        }
    
    def _calculate_externalities(self, vehicle_data: Dict[str, pd.Series]) -> Dict[str, Any]:
        """Calculate externalities for both vehicles."""
        externalities = self.data_tables['externalities']
        
        bev_externalities = calculate_externalities(
            vehicle_data['bev'],
            externalities,
            self.ui_context['annual_kms'],
            self.ui_context['truck_life_years'],
            self.ui_context['discount_rate'],
        )
        
        diesel_externalities = calculate_externalities(
            vehicle_data['diesel'],
            externalities,
            self.ui_context['annual_kms'],
            self.ui_context['truck_life_years'],
            self.ui_context['discount_rate'],
        )
        
        return {
            'bev': bev_externalities,
            'diesel': diesel_externalities
        }
    
    def _calculate_infrastructure_costs(self, vehicle_data: Dict[str, pd.Series]) -> Dict[str, Any]:
        """Calculate infrastructure costs and charging requirements."""
        infrastructure_options = self.data_tables['infrastructure_options']
        
        selected_infra_data = infrastructure_options[
            infrastructure_options[DataColumns.INFRASTRUCTURE_ID] == self.ui_context['selected_infrastructure']
        ].iloc[0]
        
        bev_charging_requirements = calculate_charging_requirements(
            vehicle_data['bev'], 
            self.ui_context['annual_kms'], 
            selected_infra_data
        )
        
        infrastructure_costs = calculate_infrastructure_costs(
            selected_infra_data, 
            self.ui_context['truck_life_years'], 
            self.ui_context['discount_rate'], 
            self.ui_context['fleet_size']
        )
        
        incentives = self.modified_tables['incentives']
        infra_costs_with_incentives = apply_infrastructure_incentives(
            infrastructure_costs, 
            incentives, 
            self.ui_context['apply_incentives']
        )
        infra_costs_with_incentives['fleet_size'] = self.ui_context['fleet_size']
        
        return {
            'charging_requirements': bev_charging_requirements,
            'costs': infra_costs_with_incentives,
            'selected_infra_data': selected_infra_data
        }
    
    def _build_results(self, vehicle_data: Dict[str, pd.Series], 
                      energy_costs: Dict[str, Any], 
                      annual_costs: Dict[str, Any],
                      emissions: Dict[str, Any], 
                      acquisition_costs: Dict[str, Any],
                      residual_values: Dict[str, Any], 
                      battery_replacement: Dict[str, Any],
                      npv_annual_costs: Dict[str, float], 
                      tco_results: Dict[str, Any],
                      externalities: Dict[str, Any], 
                      infrastructure_costs: Dict[str, Any]) -> Dict[str, Any]:
        """Build final results dictionary."""
        # Integrate infrastructure with BEV TCO
        bev_tco_with_infra = integrate_infrastructure_with_tco(
            tco_results['bev'], 
            infrastructure_costs['costs'], 
            self.ui_context['apply_incentives']
        )
        
        # Build BEV results
        bev_results = {
            'vehicle_data': vehicle_data['bev'],
            'fees': energy_costs['bev_fees'],
            'energy_cost_per_km': energy_costs['bev'],
            'annual_costs': annual_costs['bev'],
            'emissions': emissions['bev'],
            'acquisition_cost': acquisition_costs['bev'],
            'residual_value': residual_values['bev'],
            'battery_replacement': battery_replacement['bev'],
            'npv_annual_cost': npv_annual_costs['bev'],
            'tco': bev_tco_with_infra,
            'externalities': externalities['bev'],
            'social_tco': calculate_social_tco(bev_tco_with_infra, externalities['bev']),
            'annual_kms': self.ui_context['annual_kms'],
            'truck_life_years': self.ui_context['truck_life_years'],
            'charging_requirements': infrastructure_costs['charging_requirements'],
            'infrastructure_costs': infrastructure_costs['costs'],
            'selected_infrastructure_description': infrastructure_costs['selected_infra_data'][DataColumns.INFRASTRUCTURE_DESCRIPTION],
            'charging_options': self.data_tables['charging_options'],
            'discount_rate': self.ui_context['discount_rate'],
            'scenario': self.ui_context['scenario_meta'],
        }
        
        # Add charging mix info if applicable
        if self.ui_context['charging_mix']:
            bev_results['charging_mix'] = self.ui_context['charging_mix']
            bev_results['weighted_electricity_price'] = weighted_electricity_price(
                self.ui_context['charging_mix'], 
                self.data_tables['charging_options']
            )
        
        # Build diesel results
        diesel_results = {
            'vehicle_data': vehicle_data['diesel'],
            'fees': energy_costs['diesel_fees'],
            'energy_cost_per_km': energy_costs['diesel'],
            'annual_costs': annual_costs['diesel'],
            'emissions': emissions['diesel'],
            'acquisition_cost': acquisition_costs['diesel'],
            'residual_value': residual_values['diesel'],
            'battery_replacement': 0,
            'npv_annual_cost': npv_annual_costs['diesel'],
            'tco': tco_results['diesel'],
            'externalities': externalities['diesel'],
            'social_tco': calculate_social_tco(tco_results['diesel'], externalities['diesel']),
            'annual_kms': self.ui_context['annual_kms'],
            'truck_life_years': self.ui_context['truck_life_years'],
            'discount_rate': self.ui_context['discount_rate'],
            'scenario': self.ui_context['scenario_meta'],
        }
        
        # Calculate comparison metrics
        comparison_metrics = calculate_comparative_metrics(
            bev_results, diesel_results, 
            self.ui_context['annual_kms'], 
            self.ui_context['truck_life_years']
        )
        bev_results['comparison'] = comparison_metrics
        
        # Apply UI parameter overrides for return context
        financial_params_with_ui = self.modified_tables['financial_params'].copy()
        mask = financial_params_with_ui[DataColumns.FINANCE_DESCRIPTION] == ParameterKeys.DIESEL_PRICE
        financial_params_with_ui.loc[mask, DataColumns.FINANCE_DEFAULT_VALUE] = self.ui_context[ParameterKeys.DIESEL_PRICE]
        mask = financial_params_with_ui[DataColumns.FINANCE_DESCRIPTION] == ParameterKeys.CARBON_PRICE
        financial_params_with_ui.loc[mask, DataColumns.FINANCE_DEFAULT_VALUE] = self.ui_context[ParameterKeys.CARBON_PRICE]
        
        battery_params_with_ui = self.financial_calculator._apply_ui_battery_parameters()
        
        return {
            'bev_results': bev_results,
            'diesel_results': diesel_results,
            'comparison_metrics': comparison_metrics,
            'bev_vehicle_data': vehicle_data['bev'],
            'diesel_vehicle_data': vehicle_data['diesel'],
            'bev_fees': energy_costs['bev_fees'],
            'diesel_fees': energy_costs['diesel_fees'],
            'charging_options': self.data_tables['charging_options'],
            'infrastructure_options': self.data_tables['infrastructure_options'],
            'financial_params_with_ui': financial_params_with_ui,
            'battery_params_with_ui': battery_params_with_ui,
            'emission_factors': self.data_tables['emission_factors'],
            'incentives': self.modified_tables['incentives'],
            'selected_charging': self.ui_context['selected_charging'],
            'selected_infrastructure': self.ui_context['selected_infrastructure'],
            'annual_kms': self.ui_context['annual_kms'],
            'truck_life_years': self.ui_context['truck_life_years'],
            'discount_rate': self.ui_context['discount_rate'],
            'fleet_size': self.ui_context['fleet_size'],
            'charging_mix': self.ui_context['charging_mix'],
            'apply_incentives': self.ui_context['apply_incentives'],
        } 