from enum import Enum, unique


@unique
class Drivetrain(str, Enum):
    """Enumeration of valid drivetrain identifiers used throughout the codebase.
    Keeping them centralised avoids magic strings and naming drift.
    """

    BEV = "BEV"
    DIESEL = "Diesel"
    PHEV = "PHEV"  # Plug-in Hybrid Electric Vehicle
    ALL = "All"


@unique
class FuelType(str, Enum):
    """Enumeration of fuel-type identifiers used in the emissions tables."""

    ELECTRICITY = "electricity"
    DIESEL = "diesel"


@unique
class EmissionStandard(str, Enum):
    """Enumeration of emission standard identifiers."""

    GRID = "Grid"
    EURO_IV_PLUS = "Euro IV+"


class DataColumns(str, Enum):
    """Column names used across DataFrames.

    Note: Not using @unique decorator as some columns like 'default_value'
    are used in multiple table types.
    """

    # Financial parameters
    FINANCE_DESCRIPTION = "finance_description"
    FINANCE_DEFAULT_VALUE = "default_value"

    # Battery parameters
    BATTERY_DESCRIPTION = "battery_description"
    BATTERY_DEFAULT_VALUE = "default_value"

    # Vehicle columns
    VEHICLE_ID = "vehicle_id"
    VEHICLE_TYPE = "vehicle_type"
    VEHICLE_DRIVETRAIN = "vehicle_drivetrain"
    VEHICLE_MODEL = "vehicle_model"
    VEHICLE_NAME = "vehicle_model"  # Alias for backward compatibility
    BODY_TYPE = "body_type"  # Vehicle body type (e.g., Articulated, Rigid)
    PAYLOAD_T = "payload_t"
    PAYLOAD_TONNES = "payload_t"  # Alias for backward compatibility
    MSRP_PRICE = "msrp_price"
    VEHICLE_PRICE = "msrp_price"  # Alias for backward compatibility
    RANGE_KM = "range_km"
    MAX_ANNUAL_DISTANCE_KM = "max_annual_distance_km"  # Maximum annual distance
    BATTERY_CAPACITY_KWH = "battery_capacity_kwh"
    VEHICLE_BATTERY_CAPACITY_KWH = "battery_capacity_kwh"  # Alias for backward compatibility
    BATTERY_EFFICIENCY = "battery_efficiency"  # Battery charging/discharging efficiency
    KWH_PER100KM = "kwh_per100km"
    LITRES_PER100KM = "litres_per100km"
    COMPARISON_PAIR_ID = "comparison_pair_id"

    # Charging options
    CHARGING_ID = "charging_id"
    CHARGING_APPROACH = "charging_approach"
    CHARGING_NAME = "charging_name"  # Human-readable charging option name
    PER_KWH_PRICE = "per_kwh_price"

    # Infrastructure
    INFRASTRUCTURE_ID = "infrastructure_id"
    INFRASTRUCTURE_DESCRIPTION = "infrastructure_description"
    INFRASTRUCTURE_PRICE = "infrastructure_price"
    SERVICE_LIFE_YEARS = "service_life_years"
    MAINTENANCE_PERCENT = "maintenance_percent"
    CHARGER_POWER = "charger_power"  # Charger power in kW
    CHARGER_EFFICIENCY = "charger_efficiency"  # Charging efficiency (0-1)
    UTILIZATION_HOURS = "utilization_hours"  # Daily utilization hours
    ANNUAL_MAINTENANCE_COST = "annual_maintenance_cost"  # Annual maintenance cost for infrastructure

    # Emissions
    FUEL_TYPE = "fuel_type"
    EMISSION_STANDARD = "emission_standard"
    CO2_PER_UNIT = "co2_per_unit"
    GRID_EMISSION_FACTOR = "grid_emission_factor"
    DIESEL_EMISSION_FACTOR = "diesel_emission_factor"

    # Fees and registration
    REGISTRATION_ANNUAL_PRICE = "registration_annual_price"
    REGISTRATION_UPFRONT_PRICE = "registration_upfront_price"
    INSURANCE_ANNUAL_PRICE = "insurance_annual_price"
    INSURANCE = "insurance"  # Legacy alias for INSURANCE_ANNUAL_PRICE
    MAINTENANCE_ANNUAL_PRICE = "maintenance_annual_price"

    # Financial parameters (legacy compatibility)
    DISCOUNT_RATE = "discount_rate"
    DIESEL_PRICE = "diesel_price"
    TRUCK_LIFE = "truck_life"
    ANNUAL_KMS = "annual_kms"
    RESIDUAL_VALUE_PCT = "residual_value_pct"

    # Maintenance parameters
    MAINTENANCE_BASE_COST = "maintenance_base_cost"
    MAINTENANCE_COST_PER_KM = "maintenance_cost_per_km"

    # Incentives
    INCENTIVE_FLAG = "incentive_flag"
    INCENTIVE_TYPE = "incentive_type"
    INCENTIVE_RATE = "incentive_rate"

    # Scenarios
    SCENARIO_ID = "scenario_id"
    SCENARIO_NAME = "scenario_name"
    SCENARIO_DESCRIPTION = "scenario_description"

    # Externalities
    VEHICLE_CLASS = "vehicle_class"
    POLLUTANT_TYPE = "pollutant_type"
    COST_PER_KM = "cost_per_km"


@unique
class ParameterKeys(str, Enum):
    """Parameter key values used in lookups."""

    # Financial parameters
    DIESEL_PRICE = "diesel_price"
    DISCOUNT_RATE = "discount_rate_percent"
    CARBON_PRICE = "carbon_price"
    INITIAL_DEPRECIATION = "initial_depreciation_percent"
    ANNUAL_DEPRECIATION = "annual_depreciation_percent"
    ROAD_USER_CHARGE = "road_user_charge"
    ANNUAL_INSURANCE_COST = "annual_insurance_cost"
    ANNUAL_TYRE_COST = "annual_tyre_cost"
    ANNUAL_MAINTENANCE_COST = "annual_maintenance_cost"
    ANNUAL_REGISTRATION_COST = "annual_registration_cost"

    # Battery parameters
    REPLACEMENT_COST = "replacement_per_kwh_price"
    BATTERY_PRICE_PER_KWH = "battery_price_per_kwh"
    DEGRADATION_RATE = "degradation_annual_percent"
    BATTERY_ANNUAL_DECAY_RATE = "battery_annual_decay_rate"
    MINIMUM_CAPACITY = "minimum_capacity_percent"
    BATTERY_MIN_SOH = "battery_min_soh"
    RECYCLING_VALUE = "recycling_value_percent"

    # Operating parameters
    ANNUAL_KMS = "annual_kms"
    TRUCK_LIFE_YEARS = "truck_life_years"


@unique
class IncentiveTypes(str, Enum):
    """Incentive type identifiers."""

    STAMP_DUTY_EXEMPTION = "stamp_duty_exemption"
    REGISTRATION_EXEMPTION = "registration_exemption"
    PURCHASE_REBATE_AUD = "purchase_rebate_aud"
    INFRASTRUCTURE_SUBSIDY = "charging_infrastructure_subsidy"
    ELECTRICITY_DISCOUNT = "electricity_rate_discount"
    INSURANCE_DISCOUNT = "insurance_discount"


# Common data-frame column names (only a few to start; extend as the codebase is refactored)
# VEHICLE_DRIVETRAIN_COL = "vehicle_drivetrain"
# VEHICLE_TYPE_COL = "vehicle_type"
# CHARGING_ID_COL = "charging_id"
# INFRASTRUCTURE_ID_COL = "infrastructure_id"

__all__ = [
    "Drivetrain",
    "FuelType",
    "DataColumns",
    "ParameterKeys",
    "IncentiveTypes",
    "EmissionStandard",
    # "BatteryParameterKeys",
    # "VEHICLE_DRIVETRAIN_COL",
    # "VEHICLE_TYPE_COL",
    # "CHARGING_ID_COL",
    # "INFRASTRUCTURE_ID_COL",
]
