"""Energy consumption and emissions calculations."""

from typing import Optional, Union

from tco_app.src import CALC_DEFAULTS, Dict, pd, np
from tco_app.src.constants import DataColumns, Drivetrain, EmissionStandard, FuelType, ParameterKeys
from tco_app.src.utils.energy import weighted_electricity_price
from tco_app.src.utils.safe_operations import (
    safe_division,
    safe_get_charging_option,
    safe_get_parameter,
    safe_iloc_zero,
)
from tco_app.src.config import UNIT_CONVERSIONS
from tco_app.src.utils.pandas_helpers import safe_get_first, to_scalar

__all__ = [
    "weighted_electricity_price",
    "calculate_energy_costs",
    "calculate_emissions",
    "calculate_charging_requirements",
]

# --------------------------------------------------------------------------------------
# Energy-domain helpers – migrated from *tco_app.src.calculations*
# --------------------------------------------------------------------------------------


def calculate_energy_costs(
    vehicle_data: Union[pd.Series, dict],
    fees_data: Optional[pd.DataFrame],
    charging_data: pd.DataFrame,
    financial_params: pd.DataFrame,
    selected_charging,
    charging_mix: Optional[Dict[int, float]] = None,
) -> float:  # noqa: D401
    """Return the energy cost per km for the supplied vehicle."""
    if vehicle_data[DataColumns.VEHICLE_DRIVETRAIN] == Drivetrain.BEV:
        if charging_mix and len(charging_mix) > 0:
            electricity_price = weighted_electricity_price(charging_mix, charging_data)
        else:
            charging_option = safe_get_charging_option(charging_data, selected_charging)
            electricity_price = charging_option[DataColumns.PER_KWH_PRICE]
        energy_cost_per_km = (
            vehicle_data[DataColumns.KWH_PER100KM] / UNIT_CONVERSIONS.PERCENTAGE_TO_DECIMAL * electricity_price
        )
    elif vehicle_data[DataColumns.VEHICLE_DRIVETRAIN] == Drivetrain.PHEV:
        # PHEV uses both electricity and diesel
        # Get electricity price
        if charging_mix and len(charging_mix) > 0:
            electricity_price = weighted_electricity_price(charging_mix, charging_data)
        else:
            charging_option = safe_get_charging_option(charging_data, selected_charging)
            electricity_price = charging_option[DataColumns.PER_KWH_PRICE]

        # Get diesel price
        diesel_price = safe_get_parameter(financial_params, ParameterKeys.DIESEL_PRICE)

        # Calculate electric range ratio (assuming electric range is used first)
        electric_range = vehicle_data.get(
            DataColumns.RANGE_KM, 50
        )  # Default 50km if not specified
        # Assume typical daily driving of 100km, so electric portion is electric_range/100
        electric_ratio = min(electric_range / UNIT_CONVERSIONS.PERCENTAGE_TO_DECIMAL, 1.0)
        diesel_ratio = 1.0 - electric_ratio

        # Calculate combined cost
        electric_cost = (
            vehicle_data[DataColumns.KWH_PER100KM]
            / UNIT_CONVERSIONS.PERCENTAGE_TO_DECIMAL
            * electricity_price
            * electric_ratio
        )
        diesel_cost = (
            vehicle_data[DataColumns.LITRES_PER100KM]
            / UNIT_CONVERSIONS.PERCENTAGE_TO_DECIMAL
            * diesel_price
            * (1 - electric_ratio)
        )
        energy_cost_per_km = electric_cost + diesel_cost
    else:
        diesel_price = safe_get_parameter(financial_params, ParameterKeys.DIESEL_PRICE)
        energy_cost_per_km = (
            vehicle_data[DataColumns.LITRES_PER100KM] / UNIT_CONVERSIONS.PERCENTAGE_TO_DECIMAL * diesel_price
        )
    return energy_cost_per_km


def calculate_emissions(
    vehicle_data: Union[pd.Series, dict],
    emission_factors: pd.DataFrame,
    annual_kms: int,
    truck_life_years: int,
) -> Dict[str, float]:  # noqa: D401
    """Return per-km, annual and lifetime CO₂-equivalent emissions."""
    if vehicle_data[DataColumns.VEHICLE_DRIVETRAIN] == Drivetrain.BEV:
        electricity_ef_condition = (emission_factors[DataColumns.FUEL_TYPE] == FuelType.ELECTRICITY) & (
            emission_factors[DataColumns.EMISSION_STANDARD]
            == EmissionStandard.GRID
        )
        electricity_ef_row = safe_iloc_zero(
            emission_factors,
            electricity_ef_condition,
            context="electricity emission factor",
        )
        electricity_ef = electricity_ef_row[DataColumns.CO2_PER_UNIT]
        co2_per_km = vehicle_data[DataColumns.KWH_PER100KM] / UNIT_CONVERSIONS.PERCENTAGE_TO_DECIMAL * electricity_ef
    else:
        diesel_ef_condition = (emission_factors[DataColumns.FUEL_TYPE] == FuelType.DIESEL) & (
            emission_factors[DataColumns.EMISSION_STANDARD]
            == EmissionStandard.EURO_IV_PLUS
        )
        diesel_ef_row = safe_iloc_zero(
            emission_factors, diesel_ef_condition, context="diesel emission factor"
        )
        diesel_ef = diesel_ef_row[DataColumns.CO2_PER_UNIT]
        co2_per_km = vehicle_data[DataColumns.LITRES_PER100KM] / UNIT_CONVERSIONS.PERCENTAGE_TO_DECIMAL * diesel_ef

    annual_emissions = co2_per_km * annual_kms
    lifetime_emissions = annual_emissions * truck_life_years
    return {
        "co2_per_km": co2_per_km,
        "annual_emissions": annual_emissions,
        "lifetime_emissions": lifetime_emissions,
    }


def calculate_charging_requirements(
    vehicle_data: Union[pd.Series, dict],
    annual_kms: int,
    infrastructure_option: Optional[Union[pd.Series, dict]] = None,
) -> Dict[str, float]:  # noqa: D401
    """Estimate daily charging demand and utilisation metrics."""
    if vehicle_data[DataColumns.VEHICLE_DRIVETRAIN] != Drivetrain.BEV:
        return {
            "daily_distance": 0,
            "daily_kwh_required": 0,
            "charger_power": 0,
            "charging_time_per_day": 0,
            "max_vehicles_per_charger": 0,
        }

    daily_distance = annual_kms / CALC_DEFAULTS.DAYS_PER_YEAR
    daily_kwh_required = daily_distance * vehicle_data[DataColumns.KWH_PER100KM] / UNIT_CONVERSIONS.PERCENTAGE_TO_DECIMAL

    charger_power = CALC_DEFAULTS.DEFAULT_CHARGER_POWER_KW
    if infrastructure_option is not None:
        description = infrastructure_option[DataColumns.INFRASTRUCTURE_DESCRIPTION]
        if "kW" in description:
            try:
                charger_power = float(description.split("kW")[0].strip().split(" ")[-1])
            except (ValueError, IndexError):
                pass

    charging_time_per_day = (
        safe_division(
            daily_kwh_required,
            charger_power,
            context="daily_kwh_required/charger_power calculation",
        )
        if charger_power > 0
        else 0
    )
    max_vehicles_per_charger = (
        safe_division(
            24, charging_time_per_day, context="24/charging_time_per_day calculation"
        )
        if charging_time_per_day > 0
        else 0
    )

    return {
        "daily_distance": daily_distance,
        "daily_kwh_required": daily_kwh_required,
        "charger_power": charger_power,
        "charging_time_per_day": charging_time_per_day,
        "max_vehicles_per_charger": max_vehicles_per_charger,
    }
