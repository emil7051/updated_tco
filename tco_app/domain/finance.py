from __future__ import annotations

import math
from typing import Dict, Any

import pandas as pd

from tco_app.src.constants import Drivetrain
from tco_app.src.utils.finance import (
	npv_constant as calculate_npv,
	cumulative_cost_curve,
	price_parity_year,
	calculate_residual_value,
)
from tco_app.domain.finance_payload import calculate_payload_penalty_costs as _impl

__all__ = [
	'calculate_npv',
	'cumulative_cost_curve',
	'price_parity_year',
	'calculate_residual_value',
	'calculate_annual_costs',
	'calculate_acquisition_cost',
	'calculate_tco',
	'calculate_infrastructure_costs',
	'apply_infrastructure_incentives',
	'integrate_infrastructure_with_tco',
	'calculate_payload_penalty_costs',
]

# --------------------------------------------------------------------------------------
# Annual & acquisition cost helpers
# --------------------------------------------------------------------------------------

def calculate_annual_costs(
	vehicle_data: pd.Series | dict,
	fees_data: pd.DataFrame,
	energy_cost_per_km: float,
	annual_kms: int,
	incentives_data: pd.DataFrame | None = None,
	apply_incentives: bool = False,
) -> Dict[str, float]:
	maintenance_data = fees_data[fees_data['vehicle_id'] == vehicle_data['vehicle_id']].iloc[0]
	maintenance_per_km = maintenance_data['maintenance_perkm_price']

	annual_maintenance_cost = maintenance_per_km * annual_kms
	annual_energy_cost = energy_cost_per_km * annual_kms

	registration_annual = maintenance_data['registration_annual_price']
	insurance_annual = maintenance_data['insurance_annual_price']

	if apply_incentives and incentives_data is not None and vehicle_data['vehicle_drivetrain'] == Drivetrain.BEV:
		active = incentives_data[(incentives_data['incentive_flag'] == 1) & ((incentives_data['drivetrain'] == Drivetrain.BEV) | (incentives_data['drivetrain'] == Drivetrain.ALL))]

		registration_exemption = active[active['incentive_type'] == 'registration_exemption']
		if not registration_exemption.empty:
			registration_annual *= 1 - registration_exemption.iloc[0]['incentive_rate']

		insurance_discount = active[active['incentive_type'] == 'insurance_discount']
		if not insurance_discount.empty:
			insurance_annual *= 1 - insurance_discount.iloc[0]['incentive_rate']

		electricity_discount = active[active['incentive_type'] == 'electricity_rate_discount']
		if not electricity_discount.empty:
			annual_energy_cost *= 1 - electricity_discount.iloc[0]['incentive_rate']

	annual_operating_cost = annual_energy_cost + annual_maintenance_cost + registration_annual + insurance_annual

	return {
		'annual_energy_cost': annual_energy_cost,
		'annual_maintenance_cost': annual_maintenance_cost,
		'registration_annual': registration_annual,
		'insurance_annual': insurance_annual,
		'annual_operating_cost': annual_operating_cost,
	}


def calculate_acquisition_cost(
	vehicle_data: pd.Series | dict,
	fees_data: pd.DataFrame,
	incentives_data: pd.DataFrame,
	apply_incentives: bool = True,
) -> float:
	msrp = vehicle_data['msrp_price']
	fees = fees_data[fees_data['vehicle_id'] == vehicle_data['vehicle_id']].iloc[0]
	stamp_duty = fees['stamp_duty_price']
	acquisition_cost = msrp + stamp_duty

	if apply_incentives and vehicle_data['vehicle_drivetrain'] == Drivetrain.BEV:
		active = incentives_data[(incentives_data['incentive_flag'] == 1) & ((incentives_data['drivetrain'] == Drivetrain.BEV) | (incentives_data['drivetrain'] == Drivetrain.ALL))]

		purchase_rebate = active[active['incentive_type'] == 'purchase_rebate_aud']
		if not purchase_rebate.empty:
			acquisition_cost -= purchase_rebate.iloc[0]['incentive_rate']

		stamp_duty_exemption = active[active['incentive_type'] == 'stamp_duty_exemption']
		if not stamp_duty_exemption.empty:
			acquisition_cost -= stamp_duty * stamp_duty_exemption.iloc[0]['incentive_rate']

	return acquisition_cost

# --------------------------------------------------------------------------------------
# TCO & infrastructure helpers
# --------------------------------------------------------------------------------------

def calculate_tco(
	vehicle_data: pd.Series | dict,
	fees_data: pd.DataFrame,
	annual_costs: Dict[str, float],
	acquisition_cost: float,
	residual_value: float,
	battery_replacement: float,
	npv_annual_cost: float,
	annual_kms: int,
	truck_life_years: int,
) -> Dict[str, float]:
	npv_total_cost = acquisition_cost + npv_annual_cost - residual_value + battery_replacement
	tco_per_km = npv_total_cost / (annual_kms * truck_life_years)
	tco_per_tonne_km = tco_per_km / vehicle_data['payload_t']

	return {
		'npv_total_cost': npv_total_cost,
		'tco_per_km': tco_per_km,
		'tco_per_tonne_km': tco_per_tonne_km,
		'tco_lifetime': npv_total_cost,
		'tco_annual': npv_total_cost / truck_life_years,
	}


def calculate_infrastructure_costs(
	infrastructure_option: pd.Series | dict,
	truck_life_years: int,
	discount_rate: float,
	fleet_size: int = 1,
) -> Dict[str, Any]:
	price = infrastructure_option['infrastructure_price']
	service_life = infrastructure_option['service_life_years']
	maint_pct = infrastructure_option['maintenance_percent']

	annual_maintenance = price * maint_pct
	annual_capital = price / service_life
	total_annual_cost = annual_capital + annual_maintenance
	per_vehicle_annual = total_annual_cost / fleet_size

	replacement_cycles = max(1, math.ceil(truck_life_years / service_life))
	npv_infra = 0.0
	for cycle in range(replacement_cycles):
		start_year = cycle * service_life
		if start_year >= truck_life_years:
			break

		npv_infra += price if cycle == 0 else price / ((1 + discount_rate) ** start_year)

		years_in_cycle = min(service_life, truck_life_years - start_year)
		for year in range(years_in_cycle):
			current_year = start_year + year + 1
			npv_infra += annual_maintenance / ((1 + discount_rate) ** current_year)

	npv_per_vehicle = npv_infra / fleet_size

	return {
		'infrastructure_price': price,
		'service_life_years': service_life,
		'annual_maintenance': annual_maintenance,
		'annual_capital_cost': annual_capital,
		'total_annual_cost': total_annual_cost,
		'per_vehicle_annual_cost': per_vehicle_annual,
		'replacement_cycles': replacement_cycles,
		'npv_infrastructure': npv_infra,
		'npv_per_vehicle': npv_per_vehicle,
		'fleet_size': fleet_size,
	}


def apply_infrastructure_incentives(
	infrastructure_costs: Dict[str, Any],
	incentives_data: pd.DataFrame,
	apply_incentives: bool = True,
) -> Dict[str, Any]:
	if not apply_incentives:
		return infrastructure_costs

	costs = infrastructure_costs.copy()
	active = incentives_data[(incentives_data['incentive_flag'] == 1) & (incentives_data['incentive_type'] == 'charging_infrastructure_subsidy')]

	if not active.empty:
		rate = active.iloc[0]['incentive_rate']
		costs['infrastructure_price_with_incentives'] = costs['infrastructure_price'] * (1 - rate)
		costs['npv_infrastructure_with_incentives'] = costs['npv_infrastructure'] * (1 - rate)
		costs['npv_per_vehicle_with_incentives'] = costs['npv_per_vehicle'] * (1 - rate)
		costs['subsidy_rate'] = rate
	else:
		costs['infrastructure_price_with_incentives'] = costs['infrastructure_price']
		costs['npv_infrastructure_with_incentives'] = costs['npv_infrastructure']
		costs['npv_per_vehicle_with_incentives'] = costs['npv_per_vehicle']
		costs['subsidy_rate'] = 0

	return costs


def integrate_infrastructure_with_tco(
	tco_data: Dict[str, Any],
	infrastructure_costs: Dict[str, Any],
	apply_incentives: bool = True,
) -> Dict[str, Any]:
	updated = tco_data.copy()
	infra_npv = (
		infrastructure_costs['npv_per_vehicle_with_incentives'] if apply_incentives else infrastructure_costs['npv_per_vehicle']
	)
	updated['npv_total_cost'] += infra_npv

	annual_kms = updated.get('annual_kms', 0)
	truck_life_years = updated.get('truck_life_years', 0)
	payload_t = updated.get('payload_t', 0)

	if annual_kms and truck_life_years:
		total_kms = annual_kms * truck_life_years
		updated['tco_per_km'] = updated['npv_total_cost'] / total_kms
		if payload_t:
			updated['tco_per_tonne_km'] = updated['tco_per_km'] / payload_t

	updated['infrastructure_costs'] = infrastructure_costs
	return updated

# --------------------------------------------------------------------------------------
# Payload penalty – delegate to legacy impl for now (low usage outside plotters)
# --------------------------------------------------------------------------------------

def calculate_payload_penalty_costs(
	bev_results: Dict[str, Any],
	diesel_results: Dict[str, Any],
	financial_params: pd.DataFrame,
) -> Dict[str, Any]:
	"""Proxy to :pyfunc:`tco_app.domain.finance_payload.calculate_payload_penalty_costs`."""
	return _impl(bev_results, diesel_results, financial_params) 