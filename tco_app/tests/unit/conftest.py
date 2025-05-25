"""Pytest configuration for unit tests."""

# Import all fixtures from the fixtures module to make them available
from tco_app.tests.fixtures import (
    articulated_bev_vehicle,
    articulated_diesel_vehicle,
    bev_vehicle_data,
    diesel_vehicle_data,
    minimal_financial_params,
    standard_charging_options,
    standard_emission_factors,
    standard_externalities,
    standard_fees,
    standard_financial_params,
    standard_incentives,
    standard_infrastructure_options,
    vehicle_models_df,
)

__all__ = [
    "articulated_bev_vehicle",
    "articulated_diesel_vehicle",
    "bev_vehicle_data",
    "diesel_vehicle_data",
    "minimal_financial_params",
    "standard_charging_options",
    "standard_emission_factors",
    "standard_externalities",
    "standard_fees",
    "standard_financial_params",
    "standard_incentives",
    "standard_infrastructure_options",
    "vehicle_models_df",
]
