"""Shared vehicle fixtures for tests."""
import pytest
import pandas as pd
from tco_app.src.constants import Drivetrain, DataColumns, ParameterKeys


@pytest.fixture
def bev_vehicle_data():
    """Standard BEV vehicle for testing."""
    return pd.Series({
        DataColumns.VEHICLE_ID: 'BEV001',
        DataColumns.VEHICLE_TYPE: 'Light Rigid',
        DataColumns.VEHICLE_DRIVETRAIN: Drivetrain.BEV,
        DataColumns.VEHICLE_MODEL: 'Test BEV Model',
        DataColumns.PAYLOAD_T: 4.5,
        DataColumns.MSRP_PRICE: 150000,
        DataColumns.RANGE_KM: 200,
        DataColumns.BATTERY_CAPACITY_KWH: 100,
        DataColumns.KWH_PER100KM: 50,
        DataColumns.COMPARISON_PAIR_ID: 'DSL001'
    })


@pytest.fixture
def diesel_vehicle_data():
    """Standard diesel vehicle for testing."""
    return pd.Series({
        DataColumns.VEHICLE_ID: 'DSL001',
        DataColumns.VEHICLE_TYPE: 'Light Rigid',
        DataColumns.VEHICLE_DRIVETRAIN: Drivetrain.DIESEL,
        DataColumns.VEHICLE_MODEL: 'Test Diesel Model',
        DataColumns.PAYLOAD_T: 5.0,
        DataColumns.MSRP_PRICE: 100000,
        DataColumns.RANGE_KM: 600,
        DataColumns.LITRES_PER100KM: 25,
        DataColumns.COMPARISON_PAIR_ID: 'BEV001'
    })


@pytest.fixture
def articulated_bev_vehicle():
    """Articulated BEV vehicle for testing (compatible with existing tests)."""
    return {
        'vehicle_id': 1,
        'vehicle_type': 'Articulated',
        'vehicle_drivetrain': Drivetrain.BEV,
        'kwh_per100km': 130,  # kWh / 100 km
        'payload_t': 42,
        'msrp_price': 400_000,
        'battery_capacity_kwh': 400,  # Added for battery calculations
    }


@pytest.fixture
def articulated_diesel_vehicle():
    """Articulated diesel vehicle for testing (compatible with existing tests)."""
    return {
        'vehicle_id': 2,
        'vehicle_type': 'Articulated',
        'vehicle_drivetrain': Drivetrain.DIESEL,
        'litres_per100km': 28,  # l / 100 km
        'payload_t': 42,
        'msrp_price': 320_000,
    }


@pytest.fixture
def vehicle_models_df(bev_vehicle_data, diesel_vehicle_data):
    """DataFrame with test vehicles."""
    return pd.DataFrame([bev_vehicle_data, diesel_vehicle_data])


@pytest.fixture
def minimal_financial_params():
    """Minimal financial parameters for testing."""
    return pd.DataFrame([
        {
            DataColumns.FINANCE_DESCRIPTION: ParameterKeys.DIESEL_PRICE,
            DataColumns.FINANCE_DEFAULT_VALUE: 2.0
        },
        {
            DataColumns.FINANCE_DESCRIPTION: ParameterKeys.DISCOUNT_RATE,
            DataColumns.FINANCE_DEFAULT_VALUE: 0.07
        },
        {
            DataColumns.FINANCE_DESCRIPTION: ParameterKeys.CARBON_PRICE,
            DataColumns.FINANCE_DEFAULT_VALUE: 0.0
        }
    ])


@pytest.fixture
def standard_fees():
    """Standard fees data for testing."""
    return pd.DataFrame([
        {
            'vehicle_id': 1,
            'maintenance_perkm_price': 0.12,
            'registration_annual_price': 900,
            'insurance_annual_price': 2400,
            'stamp_duty_price': 8000,
        },
        {
            'vehicle_id': 2,
            'maintenance_perkm_price': 0.10,
            'registration_annual_price': 850,
            'insurance_annual_price': 2000,
            'stamp_duty_price': 5000,
        },
    ])


@pytest.fixture
def standard_charging_options():
    """Standard charging options for testing."""
    return pd.DataFrame([
        {'charging_id': 'Depot', 'per_kwh_price': 0.25, 'charging_approach': 'Depot 80 kW'},
        {'charging_id': 'Fast', 'per_kwh_price': 0.60, 'charging_approach': 'Public 150 kW'},
    ])


@pytest.fixture
def standard_financial_params():
    """Standard financial parameters for testing."""
    return pd.DataFrame([
        {'finance_description': 'diesel_price', 'default_value': 2.0},
        {'finance_description': 'discount_rate_percent', 'default_value': 0.07},
        {'finance_description': 'initial_depreciation_percent', 'default_value': 0.1},
        {'finance_description': 'annual_depreciation_percent', 'default_value': 0.05},
    ])


@pytest.fixture
def standard_emission_factors():
    """Standard emission factors for testing."""
    return pd.DataFrame([
        {'fuel_type': 'electricity', 'emission_standard': 'Grid', 'co2_per_unit': 0.2},
        {'fuel_type': 'diesel', 'emission_standard': 'Euro IV+', 'co2_per_unit': 2.68},
    ])


@pytest.fixture
def standard_externalities():
    """Standard externalities data for testing."""
    return pd.DataFrame([
        {
            'vehicle_class': 'Articulated',
            'drivetrain': Drivetrain.BEV,
            'pollutant_type': 'externalities_total',
            'cost_per_km': 0.03,
        },
        {
            'vehicle_class': 'Articulated',
            'drivetrain': Drivetrain.DIESEL,
            'pollutant_type': 'externalities_total',
            'cost_per_km': 0.07,
        },
    ])


@pytest.fixture
def standard_infrastructure_options():
    """Standard infrastructure options for testing."""
    return pd.DataFrame([
        {
            'infrastructure_id': 'INFRA1',
            'infrastructure_description': '80 kW depot charger',
            'infrastructure_price': 80000,
            'service_life_years': 8,
            'maintenance_percent': 0.02,
        },
    ])


@pytest.fixture
def standard_incentives():
    """Standard incentives for testing."""
    return pd.DataFrame([
        {
            'incentive_flag': 1,
            'incentive_type': 'charging_infrastructure_subsidy',
            'drivetrain': Drivetrain.BEV,
            'incentive_rate': 0.25,
        },
        {
            'incentive_flag': 1,
            'incentive_type': 'purchase_rebate_aud',
            'drivetrain': Drivetrain.BEV,
            'incentive_rate': 40_000,  # flat dollar rebate
        },
        {
            'incentive_flag': 1,
            'incentive_type': 'stamp_duty_exemption',
            'drivetrain': Drivetrain.BEV,
            'incentive_rate': 1.0,  # 100% exemption
        },
    ]) 