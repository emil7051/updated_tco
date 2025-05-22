from __future__ import annotations

"""Externalities domain – emissions & societal cost helpers."""

from typing import Dict, Any, Union

import pandas as pd

from tco_app.domain.energy import calculate_emissions  # Reuse shared impl
from tco_app.domain.finance import calculate_npv

__all__ = [
	'calculate_emissions',
	'calculate_externalities',
	'calculate_social_tco',
	'prepare_externality_comparison',
	'calculate_social_benefit_metrics',
]

# --------------------------------------------------------------------------------------
# Externality helpers – migrated from the monolith
# --------------------------------------------------------------------------------------

def calculate_externalities(
	vehicle_data: pd.Series | dict,
	externalities_data: pd.DataFrame,
	annual_kms: int,
	truck_life_years: int,
	discount_rate: float,
) -> Dict[str, Any]:
	vehicle_class = vehicle_data['vehicle_type']
	drivetrain = vehicle_data['vehicle_drivetrain']
	vehicle_externalities = externalities_data[
		(externalities_data['vehicle_class'] == vehicle_class)
		& (externalities_data['drivetrain'] == drivetrain)
	]

	total_entry = vehicle_externalities[vehicle_externalities['pollutant_type'] == 'externalities_total']
	total_externality_per_km = (
		total_entry.iloc[0]['cost_per_km'] if not total_entry.empty else vehicle_externalities['cost_per_km'].sum()
	)

	annual_externality_cost = total_externality_per_km * annual_kms
	lifetime_externality_cost = annual_externality_cost * truck_life_years
	
	npv_externality = calculate_npv(annual_externality_cost, discount_rate, truck_life_years)

	externality_breakdown: Dict[str, Any] = {}
	for _, row in vehicle_externalities.iterrows():
		if row['pollutant_type'] == 'externalities_total':
			continue
		pollutant = row['pollutant_type']
		cost_per_km = row['cost_per_km']
		annual_cost = cost_per_km * annual_kms
		lifetime_cost = annual_cost * truck_life_years
		npv_cost = calculate_npv(annual_cost, discount_rate, truck_life_years)
		externality_breakdown[pollutant] = {
			'cost_per_km': cost_per_km,
			'annual_cost': annual_cost,
			'lifetime_cost': lifetime_cost,
			'npv_cost': npv_cost,
		}

	return {
		'externality_per_km': total_externality_per_km,
		'annual_externality_cost': annual_externality_cost,
		'lifetime_externality_cost': lifetime_externality_cost,
		'npv_externality': npv_externality,
		'breakdown': externality_breakdown,
	}


def _to_scalar(value: Union[int, float, pd.Series]) -> float:
	"""Return numeric scalar from possible Pandas scalar/Series."""
	if isinstance(value, pd.Series):
		if value.empty:
			return 0.0
		# Assume first element represents intended scalar
		return float(value.iloc[0])
	return float(value)


def calculate_social_tco(
	tco_metrics: Dict[str, Any],
	externality_metrics: Dict[str, Any],
) -> Dict[str, Any]:
	social_lifetime = (
		_to_scalar(tco_metrics['npv_total_cost'])
		+ _to_scalar(externality_metrics['npv_externality'])
	)
	annual_kms = _to_scalar(tco_metrics.get('annual_kms', 0))
	truck_life_years = _to_scalar(tco_metrics.get('truck_life_years', 0))
	payload_t = _to_scalar(tco_metrics.get('payload_t', 0))

	social_per_km = 0.0
	social_per_tonne_km = 0.0
	if annual_kms and truck_life_years:
		total_kms = annual_kms * truck_life_years
		social_per_km = social_lifetime / total_kms
		if payload_t:
			social_per_tonne_km = social_per_km / payload_t

	return {
		'social_tco_lifetime': social_lifetime,
		'social_tco_per_km': social_per_km,
		'social_tco_per_tonne_km': social_per_tonne_km,
		'externality_percentage': (
			_to_scalar(externality_metrics['npv_externality']) / social_lifetime * 100
		) if social_lifetime != 0 else 0,
	}


def prepare_externality_comparison(
	bev_externalities: Dict[str, Any],
	diesel_externalities: Dict[str, Any],
) -> Dict[str, Any]:
	bev_break = bev_externalities.get('breakdown', {})
	diesel_break = diesel_externalities.get('breakdown', {})
	all_pollutants = set(bev_break.keys()) | set(diesel_break.keys())

	comparison = []
	for pollutant in all_pollutants:
		bev_cost = bev_break.get(pollutant, {}).get('cost_per_km', 0)
		diesel_cost = diesel_break.get(pollutant, {}).get('cost_per_km', 0)
		savings = diesel_cost - bev_cost
		savings_pct = savings / diesel_cost * 100 if diesel_cost else 0
		comparison.append({
			'pollutant_type': pollutant,
			'bev_cost_per_km': bev_cost,
			'diesel_cost_per_km': diesel_cost,
			'savings_per_km': savings,
			'savings_percent': savings_pct,
		})

	comparison.sort(key=lambda x: x['savings_per_km'], reverse=True)
	bev_total = bev_externalities['externality_per_km']
	diesel_total = diesel_externalities['externality_per_km']
	total_savings = diesel_total - bev_total
	return {
		'breakdown': comparison,
		'bev_total': bev_total,
		'diesel_total': diesel_total,
		'total_savings': total_savings,
		'total_savings_percent': total_savings / diesel_total * 100 if diesel_total else 0,
	}


def calculate_social_benefit_metrics(
	bev_results: Dict[str, Any],
	diesel_results: Dict[str, Any],
	annual_kms: int,
	truck_life_years: int,
	discount_rate: float,
) -> Dict[str, Any]:
	bev_premium = bev_results['acquisition_cost'] - diesel_results['acquisition_cost']
	annual_operating_savings = (
		diesel_results['annual_costs']['annual_operating_cost']
		- bev_results['annual_costs']['annual_operating_cost']
	)
	annual_externality_savings = (
		diesel_results['externalities']['annual_externality_cost']
		- bev_results['externalities']['annual_externality_cost']
	)
	total_benefits = annual_operating_savings + annual_externality_savings
	
	npv_benefits = calculate_npv(total_benefits, discount_rate, truck_life_years)
	bcr = npv_benefits / bev_premium if bev_premium else float('inf')

	if total_benefits:
		simple_payback = bev_premium / total_benefits
		cum_benefits = 0.0
		payback_disc = truck_life_years
		for year in range(1, truck_life_years + 1):
			cum_benefits += total_benefits / ((1 + discount_rate) ** year)
			if cum_benefits >= bev_premium:
				if year > 1:
					prev = cum_benefits - total_benefits / ((1 + discount_rate) ** year)
					frac = (bev_premium - prev) / (total_benefits / ((1 + discount_rate) ** year))
					payback_disc = year - 1 + frac
				else:
					payback_disc = bev_premium / (total_benefits / ((1 + discount_rate) ** year))
				break
	else:
		simple_payback = float('inf')
		payback_disc = float('inf')

	return {
		'bev_premium': bev_premium,
		'annual_operating_savings': annual_operating_savings,
		'annual_externality_savings': annual_externality_savings,
		'total_annual_benefits': total_benefits,
		'npv_benefits': npv_benefits,
		'social_benefit_cost_ratio': bcr,
		'simple_payback_period': simple_payback,
		'social_payback_period': payback_disc,
	} 