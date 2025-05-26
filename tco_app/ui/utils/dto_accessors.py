"""DTO accessor utilities for gradual migration from dictionaries to DTOs.

These utilities provide safe access to data that works with both DTO objects
and dictionary structures during the migration period.
"""

from typing import Dict, Optional, Union
from tco_app.services.dtos import TCOResult, ComparisonResult
from tco_app.src.constants import Drivetrain, DataColumns


def get_tco_per_km(result: Union[TCOResult, Dict]) -> float:
    """Safe accessor for TCO per km that works with both DTOs and dicts."""
    if isinstance(result, TCOResult):
        return result.tco_per_km
    return result.get("tco", {}).get("tco_per_km", 0.0)


def get_tco_per_tonne_km(result: Union[TCOResult, Dict]) -> float:
    """Safe accessor for TCO per tonne-km that works with both DTOs and dicts."""
    if isinstance(result, TCOResult):
        return result.tco_per_tonne_km
    return result.get("tco", {}).get("tco_per_tonne_km", 0.0)


def get_tco_lifetime(result: Union[TCOResult, Dict]) -> float:
    """Safe accessor for lifetime TCO that works with both DTOs and dicts."""
    if isinstance(result, TCOResult):
        return result.tco_total_lifetime
    return result.get("tco", {}).get("tco_lifetime", 0.0)


def get_tco_annual(result: Union[TCOResult, Dict]) -> float:
    """Safe accessor for annual TCO that works with both DTOs and dicts."""
    if isinstance(result, TCOResult):
        # Calculate annual from lifetime if not directly available
        if hasattr(result, "tco_annual"):
            return result.tco_annual
        elif result.truck_life_years and result.truck_life_years > 0:
            return result.tco_total_lifetime / result.truck_life_years
        return 0.0
    return result.get("tco", {}).get("tco_annual", 0.0)


def get_acquisition_cost(result: Union[TCOResult, Dict]) -> float:
    """Safe accessor for acquisition cost that works with both DTOs and dicts."""
    if isinstance(result, TCOResult):
        return result.acquisition_cost
    return result.get("acquisition_cost", 0.0)


def get_energy_cost_per_km(result: Union[TCOResult, Dict]) -> float:
    """Safe accessor for energy cost per km that works with both DTOs and dicts."""
    if isinstance(result, TCOResult):
        return result.energy_cost_per_km
    return result.get("energy_cost_per_km", 0.0)


def get_annual_energy_cost(result: Union[TCOResult, Dict]) -> float:
    """Safe accessor for annual energy cost that works with both DTOs and dicts."""
    if isinstance(result, TCOResult):
        return result.annual_costs_breakdown.get("annual_energy_cost", 0.0)
    return result.get("annual_costs", {}).get("annual_energy_cost", 0.0)


def get_annual_maintenance_cost(result: Union[TCOResult, Dict]) -> float:
    """Safe accessor for annual maintenance cost that works with both DTOs and dicts."""
    if isinstance(result, TCOResult):
        return result.annual_costs_breakdown.get("annual_maintenance_cost", 0.0)
    return result.get("annual_costs", {}).get("annual_maintenance_cost", 0.0)


def get_annual_operating_cost(result: Union[TCOResult, Dict]) -> float:
    """Safe accessor for annual operating cost that works with both DTOs and dicts."""
    if isinstance(result, TCOResult):
        return result.annual_operating_cost
    return result.get("annual_costs", {}).get("annual_operating_cost", 0.0)


def get_battery_replacement_cost(result: Union[TCOResult, Dict]) -> float:
    """Safe accessor for battery replacement cost that works with both DTOs and dicts."""
    if isinstance(result, TCOResult):
        return result.npv_battery_replacement_cost
    return result.get("battery_replacement", 0.0)


def get_residual_value(result: Union[TCOResult, Dict]) -> float:
    """Safe accessor for residual value that works with both DTOs and dicts."""
    if isinstance(result, TCOResult):
        return result.residual_value
    return result.get("residual_value", 0.0)


def get_co2_per_km(result: Union[TCOResult, Dict]) -> float:
    """Safe accessor for CO2 per km that works with both DTOs and dicts."""
    if isinstance(result, TCOResult):
        return result.emissions_breakdown.get("co2_per_km", 0.0)
    return result.get("emissions", {}).get("co2_per_km", 0.0)


def get_annual_emissions(result: Union[TCOResult, Dict]) -> float:
    """Safe accessor for annual emissions that works with both DTOs and dicts."""
    if isinstance(result, TCOResult):
        return result.emissions_breakdown.get("annual_emissions", 0.0)
    return result.get("emissions", {}).get("annual_emissions", 0.0)


def get_lifetime_emissions(result: Union[TCOResult, Dict]) -> float:
    """Safe accessor for lifetime emissions that works with both DTOs and dicts."""
    if isinstance(result, TCOResult):
        return result.emissions_breakdown.get("lifetime_emissions", 0.0)
    return result.get("emissions", {}).get("lifetime_emissions", 0.0)


def get_social_tco_lifetime(result: Union[TCOResult, Dict]) -> float:
    """Safe accessor for social TCO lifetime that works with both DTOs and dicts."""
    if isinstance(result, TCOResult):
        return result.social_tco_total_lifetime
    return result.get("social_tco", {}).get("social_tco_lifetime", 0.0)


def get_infrastructure_npv_per_vehicle(result: Union[TCOResult, Dict]) -> Optional[float]:
    """Safe accessor for infrastructure NPV per vehicle that works with both DTOs and dicts."""
    if isinstance(result, TCOResult):
        if result.infrastructure_costs_breakdown:
            return result.infrastructure_costs_breakdown.get("npv_per_vehicle")
        return None
    
    infra = result.get("infrastructure_costs", {})
    if infra:
        return infra.get("npv_per_vehicle")
    return None


def get_weighted_electricity_price(result: Union[TCOResult, Dict]) -> Optional[float]:
    """Safe accessor for weighted electricity price that works with both DTOs and dicts."""
    if isinstance(result, TCOResult):
        return result.weighted_electricity_price
    return result.get("weighted_electricity_price")


def get_vehicle_name(result: Union[TCOResult, Dict]) -> str:
    """Safe accessor for vehicle name that works with both DTOs and dicts."""
    if isinstance(result, TCOResult):
        return result.vehicle_id
    
    vehicle_data = result.get("vehicle_data", {})
    if isinstance(vehicle_data, dict):
        return vehicle_data.get("name", "Unknown")
    # If it's a Series, access it differently
    if hasattr(vehicle_data, "get"):
        return vehicle_data.get("name", "Unknown")
    return "Unknown"


def get_drivetrain(result: Union[TCOResult, Dict]) -> str:
    """Safe accessor for drivetrain that works with both DTOs and dicts."""
    if isinstance(result, TCOResult):
        # The orchestrator adds vehicle_data to the DTO dynamically
        if hasattr(result, 'vehicle_data') and result.vehicle_data is not None:
            vehicle_data = result.vehicle_data
            if hasattr(vehicle_data, "get"):
                return vehicle_data.get(DataColumns.VEHICLE_DRIVETRAIN, "Unknown")
        return "Unknown"
    
    vehicle_data = result.get("vehicle_data", {})
    if isinstance(vehicle_data, dict):
        return vehicle_data.get(DataColumns.VEHICLE_DRIVETRAIN, "Unknown")
    # If it's a Series, access it differently
    if hasattr(vehicle_data, "get"):
        return vehicle_data.get(DataColumns.VEHICLE_DRIVETRAIN, "Unknown")
    return "Unknown"


# Comparison-specific accessors
def get_tco_savings(comparison: Union[ComparisonResult, Dict]) -> float:
    """Safe accessor for TCO savings that works with both DTOs and dicts."""
    if isinstance(comparison, ComparisonResult):
        return comparison.tco_savings_lifetime
    return comparison.get("comparison_metrics", {}).get("emission_savings_lifetime", 0.0)


def get_emissions_reduction(comparison: Union[ComparisonResult, Dict]) -> float:
    """Safe accessor for emissions reduction that works with both DTOs and dicts."""
    if isinstance(comparison, ComparisonResult):
        return comparison.emissions_reduction_lifetime_co2e
    return comparison.get("comparison_metrics", {}).get("emission_savings_lifetime", 0.0)


def get_payback_period(comparison: Union[ComparisonResult, Dict]) -> Optional[float]:
    """Safe accessor for payback period that works with both DTOs and dicts."""
    if isinstance(comparison, ComparisonResult):
        return comparison.payback_period_years
    return comparison.get("comparison_metrics", {}).get("price_parity_year")


def get_upfront_cost_difference(comparison: Union[ComparisonResult, Dict]) -> float:
    """Safe accessor for upfront cost difference that works with both DTOs and dicts."""
    if isinstance(comparison, ComparisonResult):
        return comparison.upfront_cost_difference
    return comparison.get("comparison_metrics", {}).get("upfront_cost_difference", 0.0)


# Infrastructure cost accessors
def get_infrastructure_cost(result: Union[TCOResult, Dict], key: str, default: float = 0.0) -> float:
    """Safe accessor for infrastructure cost fields that works with both DTOs and dicts."""
    if isinstance(result, TCOResult):
        if result.infrastructure_costs_breakdown:
            return result.infrastructure_costs_breakdown.get(key, default)
        return default
    
    infra = result.get("infrastructure_costs", {})
    if infra:
        return infra.get(key, default)
    return default


def get_infrastructure_price(result: Union[TCOResult, Dict]) -> float:
    """Safe accessor for infrastructure price."""
    if isinstance(result, TCOResult):
        if result.infrastructure_costs_breakdown:
            # First check for incentives-adjusted price
            price = result.infrastructure_costs_breakdown.get("infrastructure_price_with_incentives")
            if price is not None:
                return price
            # Fall back to base price
            return result.infrastructure_costs_breakdown.get(DataColumns.INFRASTRUCTURE_PRICE, 0.0)
        return 0.0
    
    infra = result.get("infrastructure_costs", {})
    if infra:
        # First check for incentives-adjusted price
        price = infra.get("infrastructure_price_with_incentives")
        if price is not None:
            return price
        # Fall back to base price
        return infra.get(DataColumns.INFRASTRUCTURE_PRICE, 0.0)
    return 0.0


def get_infrastructure_annual_maintenance(result: Union[TCOResult, Dict]) -> float:
    """Safe accessor for infrastructure annual maintenance."""
    return get_infrastructure_cost(result, "annual_maintenance")


def get_infrastructure_service_life(result: Union[TCOResult, Dict]) -> int:
    """Safe accessor for infrastructure service life in years."""
    return int(get_infrastructure_cost(result, "service_life_years", 10))


def get_infrastructure_replacement_cycles(result: Union[TCOResult, Dict]) -> int:
    """Safe accessor for infrastructure replacement cycles."""
    return int(get_infrastructure_cost(result, "replacement_cycles", 0))


def get_infrastructure_subsidy_rate(result: Union[TCOResult, Dict]) -> float:
    """Safe accessor for infrastructure subsidy rate."""
    return get_infrastructure_cost(result, "subsidy_rate", 0.0)


def get_infrastructure_subsidy_amount(result: Union[TCOResult, Dict]) -> float:
    """Safe accessor for infrastructure subsidy amount."""
    return get_infrastructure_cost(result, "subsidy_amount", 0.0)


# Charging requirement accessors
def get_charging_requirement(result: Union[TCOResult, Dict], key: str, default: float = 0.0) -> float:
    """Safe accessor for charging requirement fields that works with both DTOs and dicts."""
    if isinstance(result, TCOResult):
        if result.charging_requirements:
            return result.charging_requirements.get(key, default)
        return default
    
    charging = result.get("charging_requirements", {})
    if charging:
        return charging.get(key, default)
    return default


def get_daily_kwh_required(result: Union[TCOResult, Dict]) -> float:
    """Safe accessor for daily kWh required."""
    return get_charging_requirement(result, "daily_kwh_required", 0.0)


def get_charging_time_per_day(result: Union[TCOResult, Dict]) -> float:
    """Safe accessor for charging time per day in hours."""
    return get_charging_requirement(result, "charging_time_per_day", 0.0)


def get_charger_power(result: Union[TCOResult, Dict]) -> float:
    """Safe accessor for charger power in kW."""
    return get_charging_requirement(result, "charger_power", 0.0)


def get_max_vehicles_per_charger(result: Union[TCOResult, Dict]) -> float:
    """Safe accessor for maximum vehicles per charger."""
    return get_charging_requirement(result, "max_vehicles_per_charger", 1.0)


# Check if vehicle is BEV
def is_bev(result: Union[TCOResult, Dict]) -> bool:
    """Check if the vehicle is a BEV."""
    if isinstance(result, TCOResult):
        # The orchestrator adds vehicle_data to the DTO dynamically
        if hasattr(result, 'vehicle_data') and result.vehicle_data is not None:
            vehicle_data = result.vehicle_data
            if hasattr(vehicle_data, "get"):
                return vehicle_data.get(DataColumns.VEHICLE_DRIVETRAIN) == Drivetrain.BEV
        return False
    
    vehicle_data = result.get("vehicle_data", {})
    if isinstance(vehicle_data, dict):
        return vehicle_data.get(DataColumns.VEHICLE_DRIVETRAIN) == Drivetrain.BEV
    # If it's a Series, access it differently
    if hasattr(vehicle_data, "get"):
        return vehicle_data.get(DataColumns.VEHICLE_DRIVETRAIN) == Drivetrain.BEV
    return False


# Check if has charging mix
def has_charging_mix(result: Union[TCOResult, Dict]) -> bool:
    """Check if result has charging mix data."""
    if isinstance(result, TCOResult):
        # The orchestrator adds charging_mix to the DTO dynamically
        if hasattr(result, 'charging_mix') and result.charging_mix is not None:
            return len(result.charging_mix) > 0
        return False
    return "charging_mix" in result and result["charging_mix"] 