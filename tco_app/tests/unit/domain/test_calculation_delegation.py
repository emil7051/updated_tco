"""Unit tests for domain calculation delegation."""
import math
from tco_app.src import pd
import pytest
from tco_app.src.constants import Drivetrain
from tco_app.src.utils import energy as en_utils
from tco_app.src.utils import finance as fin_utils
from tco_app.src.utils.battery import calculate_battery_replacement as battery_utils
from tco_app.domain.energy import calculate_energy_costs as energy_cost_domain
from tco_app.domain.finance import calculate_residual_value as residual_domain


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


def test_energy_cost_delegation(dummy_financial_params, dummy_charging_options):
    """Test that domain energy cost function delegates properly to utils."""
    vehicle_data = {
        "vehicle_drivetrain": Drivetrain.BEV,
        "kwh_per100km": 18,
    }
    
    expected = en_utils.calculate_energy_costs(
        vehicle_data,
        None,
        dummy_charging_options,
        dummy_financial_params,
        "C1",
        None,
    )
    
    delegated = energy_cost_domain(
        vehicle_data,
        None,
        dummy_charging_options,
        dummy_financial_params,
        "C1",
        None,
    )
    
    assert math.isclose(expected, delegated, rel_tol=1e-12)


def test_residual_value_delegation():
    """Test that domain residual value function delegates properly to utils."""
    vehicle_data = {"msrp_price": 200_000}
    years = 5
    initial_dep = 0.1
    annual_dep = 0.05
    
    expected = fin_utils.calculate_residual_value(vehicle_data, years, initial_dep, annual_dep)
    delegated = residual_domain(vehicle_data, years, initial_dep, annual_dep)
    
    assert math.isclose(expected, delegated, rel_tol=1e-9)


def test_battery_replacement_delegation():
    """Test that domain battery replacement function delegates properly to utils."""
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

    expected = battery_utils(vehicle_data, battery_params, life_years, rate)
    
    # Import the domain function
    from tco_app.src.utils.battery import calculate_battery_replacement as battery_domain
    delegated = battery_domain(vehicle_data, battery_params, life_years, rate)
    
    assert math.isclose(expected, delegated, rel_tol=1e-9) 