from __future__ import annotations
from tco_app.src.constants import DataColumns, ParameterKeys

from tco_app.src.utils.safe_operations import safe_get_parameter
"""Multi-parameter tornado-chart helper extracted from the original monolith.
Keeps implementation identical while reducing per-file line-count.
"""

from typing import Any, Dict

import pandas as pd

from .single_param import perform_sensitivity_analysis

__all__ = ['calculate_tornado_data']

# --------------------------------------------------------------------------------------
# calculate_tornado_data – verbatim (save import path updates only)
# --------------------------------------------------------------------------------------

def calculate_tornado_data(
	bev_results: Dict[str, Any],
	diesel_results: Dict[str, Any],
	financial_params: pd.DataFrame,
	battery_params: pd.DataFrame,
	charging_options: pd.DataFrame,
	infrastructure_options: pd.DataFrame,
	emission_factors: pd.DataFrame,
	incentives: pd.DataFrame,
	selected_charging: Any,
	selected_infrastructure: Any,
	annual_kms: int,
	truck_life_years: int,
	discount_rate: float,
	fleet_size: int,
	charging_mix: Dict[int, float] | None = None,
	apply_incentives: bool = True,
) -> Dict[str, Any]:
	bev_vehicle_data = bev_results['vehicle_data']
	diesel_vehicle_data = diesel_results['vehicle_data']
	bev_fees = bev_results.get('fees')
	diesel_fees = diesel_results.get('fees')

	base_tco = bev_results['tco']['tco_per_km']

	sensitivity_data: Dict[str, Dict[str, Any]] = {
		'Annual Distance (km)': {
			'range': [annual_kms * 0.5, annual_kms * 1.5],
			'variation': 0.5,
		},
		'Diesel Price ($/L)': {
			'range': [
				safe_get_parameter(financial_params, ParameterKeys.DIESEL_PRICE) * 0.8,
				safe_get_parameter(financial_params, ParameterKeys.DIESEL_PRICE) * 1.2,
			],
			'variation': 0.2,
		},
		'Vehicle Lifetime (years)': {
			'range': [max(1, truck_life_years - 3), truck_life_years + 3],
			'variation': 3,
		},
		'Discount Rate (%)': {
			'range': [max(0.5, discount_rate * 100 - 3), discount_rate * 100 + 3],
			'variation': 3,
		},
	}

	base_electricity_price = charging_options[
		charging_options[DataColumns.CHARGING_ID] == selected_charging
	].iloc[0][DataColumns.PER_KWH_PRICE]
	if 'weighted_electricity_price' in bev_results:
		base_electricity_price = bev_results['weighted_electricity_price']

	sensitivity_data['Electricity Price ($/kWh)'] = {
		'range': [base_electricity_price * 0.8, base_electricity_price * 1.2],
		'variation': 0.2,
	}

	impacts: Dict[str, Any] = {}

	if bev_fees is None or diesel_fees is None:
		raise ValueError('Vehicle fees data is required for tornado chart analysis')

	for param_name, param_info in sensitivity_data.items():
		param_range = param_info['range']
		results = perform_sensitivity_analysis(
			param_name,
			param_range,
			bev_vehicle_data,
			diesel_vehicle_data,
			bev_fees,
			diesel_fees,
			charging_options,
			infrastructure_options,
			financial_params,
			battery_params,
			emission_factors,
			incentives,
			selected_charging,
			selected_infrastructure,
			annual_kms,
			truck_life_years,
			discount_rate,
			fleet_size,
			charging_mix,
			apply_incentives,
		)
		min_impact = results[0]['bev']['tco_per_km'] - base_tco
		max_impact = results[1]['bev']['tco_per_km'] - base_tco
		impacts[param_name] = {'min_impact': min_impact, 'max_impact': max_impact}

	return {'base_tco': base_tco, 'impacts': impacts} 