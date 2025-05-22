from __future__ import annotations

"""Payload-penalty cost helper previously housed in `domain.finance`.
Separated to keep each module under 300 lines.
"""

from typing import Any, Dict

import pandas as pd

__all__ = ['calculate_payload_penalty_costs']


def calculate_payload_penalty_costs(
	bev_results: Dict[str, Any],
	diesel_results: Dict[str, Any],
	financial_params: pd.DataFrame,
) -> Dict[str, Any]:
	"""Compute economic impact of BEV payload deficit (logic unchanged)."""
	bev_payload = bev_results['vehicle_data']['payload_t']
	diesel_payload = diesel_results['vehicle_data']['payload_t']

	payload_difference = diesel_payload - bev_payload
	payload_difference_percentage = (
		payload_difference / diesel_payload * 100 if diesel_payload else 0
	)
	if payload_difference <= 0:
		return {
			'has_penalty': False,
			'payload_difference': payload_difference,
			'payload_difference_percentage': payload_difference_percentage,
		}

	annual_kms = bev_results.get('annual_kms', 0)
	truck_life_years = bev_results.get('truck_life_years', 0)
	trips_multiplier = diesel_payload / bev_payload if bev_payload else 1
	additional_trips_percentage = (trips_multiplier - 1) * 100

	get_param = lambda key, default: (
		financial_params[financial_params['finance_description'] == key].iloc[0]['default_value']
		if key in financial_params['finance_description'].values else default
	)
	freight_value_per_tonne = get_param('freight_value_per_tonne', 120)
	driver_cost_hourly = get_param('driver_cost_hourly', 35)
	avg_trip_distance = get_param('avg_trip_distance', 100)
	avg_loadunload_time = get_param('avg_loadunload_time', 1)

	# Additional operating cost
	additional_operational_cost_annual = (
		trips_multiplier - 1
	) * bev_results['annual_costs']['annual_operating_cost']
	additional_operational_cost_lifetime = additional_operational_cost_annual * truck_life_years

	# Labour
	avg_speed_kmh = 60
	baseline_driving_hours = annual_kms / avg_speed_kmh
	baseline_trips = annual_kms / avg_trip_distance
	baseline_loadunload_hours = baseline_trips * avg_loadunload_time
	baseline_total_hours = baseline_driving_hours + baseline_loadunload_hours
	additional_hours_annual = baseline_total_hours * (trips_multiplier - 1)
	additional_labour_cost_annual = additional_hours_annual * driver_cost_hourly
	additional_labour_cost_lifetime = additional_labour_cost_annual * truck_life_years

	# Opportunity cost
	lost_carrying_capacity_annual = payload_difference * baseline_trips
	opportunity_cost_annual = lost_carrying_capacity_annual * freight_value_per_tonne
	opportunity_cost_lifetime = opportunity_cost_annual * truck_life_years

	effective_payload_ratio = bev_payload / diesel_payload
	bev_tco_per_effective_tonnekm = bev_results['tco']['tco_per_tonne_km'] / effective_payload_ratio
	bev_adjusted_lifetime_tco = bev_results['tco']['npv_total_cost'] + additional_operational_cost_lifetime

	return {
		'has_penalty': True,
		'payload_difference': payload_difference,
		'payload_difference_percentage': payload_difference_percentage,
		'trips_multiplier': trips_multiplier,
		'additional_trips_percentage': additional_trips_percentage,
		'fleet_ratio': diesel_payload / bev_payload if bev_payload else 1,
		'additional_bevs_needed_per_diesel': (diesel_payload / bev_payload) - 1 if bev_payload else 0,
		'additional_operational_cost_annual': additional_operational_cost_annual,
		'additional_operational_cost_lifetime': additional_operational_cost_lifetime,
		'additional_hours_annual': additional_hours_annual,
		'additional_labour_cost_annual': additional_labour_cost_annual,
		'additional_labour_cost_lifetime': additional_labour_cost_lifetime,
		'lost_carrying_capacity_annual': lost_carrying_capacity_annual,
		'opportunity_cost_annual': opportunity_cost_annual,
		'opportunity_cost_lifetime': opportunity_cost_lifetime,
		'bev_tco_per_effective_tonnekm': bev_tco_per_effective_tonnekm,
		'bev_adjusted_lifetime_tco': bev_adjusted_lifetime_tco,
	} 