from enum import Enum, unique


@unique
class Drivetrain(str, Enum):
    """Enumeration of valid drivetrain identifiers used throughout the codebase.
    Keeping them centralised avoids magic strings and naming drift.
    """

    BEV = "BEV"
    DIESEL = "Diesel"
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
    PAYLOAD_T = "payload_t"
    MSRP_PRICE = "msrp_price"
    RANGE_KM = "range_km"
    BATTERY_CAPACITY_KWH = "battery_capacity_kwh"
    KWH_PER100KM = "kwh_per100km"
    LITRES_PER100KM = "litres_per100km"
    COMPARISON_PAIR_ID = "comparison_pair_id"

    # Charging options
    CHARGING_ID = "charging_id"
    CHARGING_APPROACH = "charging_approach"
    PER_KWH_PRICE = "per_kwh_price"

    # Infrastructure
    INFRASTRUCTURE_ID = "infrastructure_id"
    INFRASTRUCTURE_DESCRIPTION = "infrastructure_description"
    INFRASTRUCTURE_PRICE = "infrastructure_price"
    SERVICE_LIFE_YEARS = "service_life_years"
    MAINTENANCE_PERCENT = "maintenance_percent"

    # Emissions
    FUEL_TYPE = "fuel_type"
    EMISSION_STANDARD = "emission_standard"
    CO2_PER_UNIT = "co2_per_unit"

    # Incentives
    INCENTIVE_FLAG = "incentive_flag"
    INCENTIVE_TYPE = "incentive_type"
    INCENTIVE_RATE = "incentive_rate"

    # Scenarios
    SCENARIO_ID = "scenario_id"
    SCENARIO_NAME = "scenario_name"
    SCENARIO_DESCRIPTION = "scenario_description"


@unique
class ParameterKeys(str, Enum):
    """Parameter key values used in lookups."""

    # Financial parameters
    DIESEL_PRICE = "diesel_price"
    DISCOUNT_RATE = "discount_rate_percent"
    CARBON_PRICE = "carbon_price"
    INITIAL_DEPRECIATION = "initial_depreciation_percent"
    ANNUAL_DEPRECIATION = "annual_depreciation_percent"

    # Battery parameters
    REPLACEMENT_COST = "replacement_per_kwh_price"
    DEGRADATION_RATE = "degradation_annual_percent"
    MINIMUM_CAPACITY = "minimum_capacity_percent"
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
