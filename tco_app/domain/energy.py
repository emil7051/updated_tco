from __future__ import annotations

import math
from typing import Dict, Any

import pandas as pd

from tco_app.src.constants import DataColumns, ParameterKeys, Drivetrain
from tco_app.src.utils.energy import weighted_electricity_price
from tco_app.src.utils.safe_operations import (
    safe_division, safe_get_charging_option, safe_get_parameter, safe_iloc_zero
)
__all__ = [
	'weighted_electricity_price',
	'calculate_energy_costs',
	'calculate_emissions',
	'calculate_charging_requirements',
]

# --------------------------------------------------------------------------------------
# Energy-domain helpers – migrated from *tco_app.src.calculations*
# --------------------------------------------------------------------------------------

def calculate_energy_costs(
	vehicle_data: pd.Series | dict,
	fees_data: pd.DataFrame | None,
	charging_data: pd.DataFrame,
	financial_params: pd.DataFrame,
	selected_charging,
	charging_mix: Dict[int, float] | None = None,
) -> float:  # noqa: D401
	"""Return the energy cost per km for the supplied vehicle."""
	if vehicle_data[DataColumns.VEHICLE_DRIVETRAIN] == Drivetrain.BEV:
		if charging_mix and len(charging_mix) > 0:
			electricity_price = weighted_electricity_price(charging_mix, charging_data)
		else:
			charging_option = safe_get_charging_option(charging_data, selected_charging)
			electricity_price = charging_option[DataColumns.PER_KWH_PRICE]
		energy_cost_per_km = vehicle_data[DataColumns.KWH_PER100KM] / 100 * electricity_price
	else:
		diesel_price = safe_get_parameter(financial_params, ParameterKeys.DIESEL_PRICE)
		energy_cost_per_km = vehicle_data[DataColumns.LITRES_PER100KM] / 100 * diesel_price
	return energy_cost_per_km


def calculate_emissions(
	vehicle_data: pd.Series | dict,
	emission_factors: pd.DataFrame,
	annual_kms: int,
	truck_life_years: int,
) -> Dict[str, float]:  # noqa: D401
	"""Return per-km, annual and lifetime CO₂-equivalent emissions."""
	if vehicle_data[DataColumns.VEHICLE_DRIVETRAIN] == Drivetrain.BEV:
		electricity_ef_condition = (
			(emission_factors['fuel_type'] == 'electricity') 
			& (emission_factors['emission_standard'] == 'Grid')
		)
		electricity_ef_row = safe_iloc_zero(
			emission_factors, 
			electricity_ef_condition, 
			context="electricity emission factor"
		)
		electricity_ef = electricity_ef_row['co2_per_unit']
		co2_per_km = vehicle_data[DataColumns.KWH_PER100KM] / 100 * electricity_ef
	else:
		diesel_ef_condition = (
			(emission_factors['fuel_type'] == 'diesel') 
			& (emission_factors['emission_standard'] == 'Euro IV+')
		)
		diesel_ef_row = safe_iloc_zero(
			emission_factors, 
			diesel_ef_condition, 
			context="diesel emission factor"
		)
		diesel_ef = diesel_ef_row['co2_per_unit']
		co2_per_km = vehicle_data[DataColumns.LITRES_PER100KM] / 100 * diesel_ef

	annual_emissions = co2_per_km * annual_kms
	lifetime_emissions = annual_emissions * truck_life_years
	return {
		'co2_per_km': co2_per_km,
		'annual_emissions': annual_emissions,
		'lifetime_emissions': lifetime_emissions,
	}


def calculate_charging_requirements(
	vehicle_data: pd.Series | dict,
	annual_kms: int,
	infrastructure_option: pd.Series | dict | None = None,
) -> Dict[str, float]:  # noqa: D401
	"""Estimate daily charging demand and utilisation metrics."""
	if vehicle_data[DataColumns.VEHICLE_DRIVETRAIN] != Drivetrain.BEV:
		return {
			'daily_distance': 0,
			'daily_kwh_required': 0,
			'charger_power': 0,
			'charging_time_per_day': 0,
			'max_vehicles_per_charger': 0,
		}

	daily_distance = annual_kms / 365
	daily_kwh_required = daily_distance * vehicle_data[DataColumns.KWH_PER100KM] / 100

	charger_power = 80.0  # Default 80 kW DC fast charger
	if infrastructure_option is not None:
		description = infrastructure_option[DataColumns.INFRASTRUCTURE_DESCRIPTION]
		if 'kW' in description:
			try:
				charger_power = float(description.split('kW')[0].strip().split(' ')[-1])
			except (ValueError, IndexError):
				pass

	charging_time_per_day = (
		safe_division(daily_kwh_required, charger_power, context="daily_kwh_required/charger_power calculation") if charger_power > 0 else 0
	)
	max_vehicles_per_charger = (
		safe_division(24, charging_time_per_day, context="24/charging_time_per_day calculation") if charging_time_per_day > 0 else 0
	)

	return {
		'daily_distance': daily_distance,
		'daily_kwh_required': daily_kwh_required,
		'charger_power': charger_power,
		'charging_time_per_day': charging_time_per_day,
		'max_vehicles_per_charger': max_vehicles_per_charger,
	} 