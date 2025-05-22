from __future__ import annotations

"""Comparative BEV-vs-Diesel KPI helper, extracted to its own file."""

from typing import Any, Dict, List, Union
import pandas as pd

import math

__all__ = ['calculate_comparative_metrics']


def calculate_comparative_metrics(
	bev_results: Dict[str, Any],
	diesel_results: Dict[str, Any],
	annual_kms: int,
	truck_life_years: int,
) -> Dict[str, Any]:
	"""Return parity & abatement KPIs for BEV vs diesel (unchanged logic)."""

	upfront_diff = bev_results['acquisition_cost'] - diesel_results['acquisition_cost']
	annual_savings = (
		diesel_results['annual_costs']['annual_operating_cost']
		- bev_results['annual_costs']['annual_operating_cost']
	)

	years = list(range(1, truck_life_years + 1))
	bev_cum: List[float] = [bev_results['acquisition_cost']]
	diesel_cum: List[float] = [diesel_results['acquisition_cost']]

	if 'infrastructure_costs' in bev_results:
		infra_price = (
			bev_results['infrastructure_costs'].get('infrastructure_price_with_incentives')
			or bev_results['infrastructure_costs']['infrastructure_price']
		)
		bev_cum[0] += infra_price / bev_results['infrastructure_costs'].get('fleet_size', 1)

	for year in range(1, truck_life_years):
		bev_annual = bev_results['annual_costs']['annual_operating_cost']
		diesel_annual = diesel_results['annual_costs']['annual_operating_cost']

		if bev_results.get('battery_replacement_year') == year:
			bev_annual += bev_results.get('battery_replacement_cost', 0)

		if 'infrastructure_costs' in bev_results:
			infra_maint = bev_results['infrastructure_costs']['annual_maintenance'] / bev_results['infrastructure_costs'].get('fleet_size', 1)
			bev_annual += infra_maint
			service_life = bev_results['infrastructure_costs']['service_life_years']
			if year % service_life == 0 and year < truck_life_years:
				infra_rep = (
					bev_results['infrastructure_costs'].get('infrastructure_price_with_incentives')
					or bev_results['infrastructure_costs']['infrastructure_price']
				) / bev_results['infrastructure_costs'].get('fleet_size', 1)
				bev_annual += infra_rep

		bev_cum.append(bev_cum[-1] + bev_annual)
		diesel_cum.append(diesel_cum[-1] + diesel_annual)

	bev_cum[-1] -= _to_scalar(bev_results['residual_value'])
	diesel_cum[-1] -= _to_scalar(diesel_results['residual_value'])

	price_parity_year = math.inf
	for i in range(len(years) - 1):
		if (bev_cum[i] - diesel_cum[i]) * (bev_cum[i+1] - diesel_cum[i+1]) <= 0:
			delta_bev = bev_cum[i+1] - bev_cum[i]
			delta_diesel = diesel_cum[i+1] - diesel_cum[i]
			if delta_bev != delta_diesel:
				t = (diesel_cum[i] - bev_cum[i]) / (delta_bev - delta_diesel)
				price_parity_year = years[i] + t
				break

	emission_savings = _to_scalar(diesel_results['emissions']['lifetime_emissions']) - _to_scalar(bev_results['emissions']['lifetime_emissions'])
	bev_npv = _to_scalar(bev_results['tco']['npv_total_cost'])
	diesel_npv = _to_scalar(diesel_results['tco']['npv_total_cost'])
	abatement_cost = (
		(bev_npv - diesel_npv) / (emission_savings / 1000)
	) if emission_savings > 0 else float('inf')

	bev_to_diesel_ratio = bev_npv / diesel_npv if diesel_npv else float('inf')

	return {
		'upfront_cost_difference': upfront_diff,
		'annual_operating_savings': annual_savings,
		'price_parity_year': price_parity_year,
		'emission_savings_lifetime': emission_savings,
		'abatement_cost': abatement_cost,
		'bev_to_diesel_tco_ratio': bev_to_diesel_ratio,
	}

def _to_scalar(val: Union[int, float, pd.Series]):
	"""Return numeric scalar from possible Pandas scalar/Series."""
	if isinstance(val, pd.Series):
		if val.empty:
			return 0.0
		return float(val.iloc[0])
	return float(val) 