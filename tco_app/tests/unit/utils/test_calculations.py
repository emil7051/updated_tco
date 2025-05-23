"""Unit tests for calculation utility functions."""
import math
import pandas as pd
import pytest
from tco_app.src.constants import Drivetrain
from tco_app.src.utils import energy as en
from tco_app.src.utils import battery as bat
from tco_app.src.utils import finance as fin


@pytest.fixture
def dummy_financial_params():
    return pd.DataFrame(
        [
            {"finance_description": "diesel_price", "default_value": 2.0},
        ]
    )


@pytest.fixture
def dummy_charging_options():
    return pd.DataFrame(
        [
            {"charging_id": "C1", "per_kwh_price": 0.25},
        ]
    )


@pytest.mark.parametrize(
    "vehicle_drivetrain, expected",
    [
        (Drivetrain.BEV, 0.05),  # 20 kWh/100 km × $0.25 = $0.05 per km
        (Drivetrain.DIESEL, 0.6),  # 30 L/100 km × $2.00 = $0.60 per km
    ],
)
def test_calculate_energy_costs_utils(vehicle_drivetrain, expected, dummy_financial_params, dummy_charging_options):
    """Test energy cost calculation utility function."""
    vehicle_data = {
        "vehicle_drivetrain": vehicle_drivetrain,
        "kwh_per100km": 20,
        "litres_per100km": 30,
    }

    cost = en.calculate_energy_costs(
        vehicle_data,
        fees_data=None,
        charging_data=dummy_charging_options,
        financial_params=dummy_financial_params,
        selected_charging="C1",
        charging_mix=None,
    )

    assert math.isclose(cost, expected, rel_tol=1e-9)


def test_calculate_emissions_utils_bev():
    """Test emissions calculation utility for BEV."""
    vehicle_data = {
        "vehicle_drivetrain": Drivetrain.BEV,
        "kwh_per100km": 20,
    }
    emission_factors = pd.DataFrame(
        [
            {"fuel_type": "electricity", "emission_standard": "Grid", "co2_per_unit": 0.2},
            {"fuel_type": "diesel", "emission_standard": "Euro IV+", "co2_per_unit": 2.7},
        ]
    )
    metrics = en.calculate_emissions(vehicle_data, emission_factors, annual_kms=50_000, truck_life_years=10)
    assert math.isclose(metrics["co2_per_km"], 0.04, rel_tol=1e-9)
    assert math.isclose(metrics["annual_emissions"], 2_000, rel_tol=1e-9)
    assert math.isclose(metrics["lifetime_emissions"], 20_000, rel_tol=1e-9)


def test_calculate_residual_value_utils():
    """Test residual value calculation utility."""
    vehicle_data = {"msrp_price": 200_000}
    years = 5
    initial_dep = 0.1
    annual_dep = 0.05
    expected = 200_000 * (1 - 0.1) * ((1 - 0.05) ** (years - 1))
    assert math.isclose(
        fin.calculate_residual_value(vehicle_data, years, initial_dep, annual_dep), 
        expected, 
        rel_tol=1e-9
    )


def test_calculate_battery_replacement_utils():
    """Test battery replacement calculation utility."""
    vehicle_data = {
        "vehicle_drivetrain": Drivetrain.BEV,
        "battery_capacity_kwh": 400,
    }
    battery_params = pd.DataFrame(
        [
            {"battery_description": "replacement_per_kwh_price", "default_value": 100},
            {"battery_description": "degradation_annual_percent", "default_value": 0.05},
            {"battery_description": "minimum_capacity_percent", "default_value": 0.7},
        ]
    )
    life_years = 8
    rate = 0.07

    # Expected value using the same formula as the util function
    years_until = math.log(0.7) / math.log(1 - 0.05)
    if years_until > life_years:
        expected = 0.0
    else:
        expected = 400 * 100 / ((1 + rate) ** years_until)

    assert math.isclose(
        bat.calculate_battery_replacement(vehicle_data, battery_params, life_years, rate),
        expected,
        rel_tol=1e-9,
    ) 