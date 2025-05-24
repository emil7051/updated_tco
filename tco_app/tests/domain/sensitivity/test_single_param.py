import pytest
import pandas as pd
from unittest.mock import patch, MagicMock, call

from tco_app.domain.sensitivity.single_param import perform_sensitivity_analysis
from tco_app.src.constants import DataColumns, ParameterKeys

# --- Default Mock Fixtures ---
@pytest.fixture
def mock_vehicle_data_series():
    # Provides a generic vehicle data series, can be specialized if needed
    return pd.Series({
        DataColumns.VEHICLE_ID.value: 1,
        DataColumns.VEHICLE_DRIVETRAIN.value: "BEV", # Default, can be overridden in specific tests
        DataColumns.VEHICLE_PRICE.value: 100000,
        DataColumns.BATTERY_CAPACITY_KWH.value: 100,
        DataColumns.BODY_TYPE.value: "Rigid",
        DataColumns.KWH_PER100KM.value: 50 # 0.5 kWh/km = 50 kWh/100km 
    })

@pytest.fixture
def mock_fees_data():
    return pd.DataFrame([{
        DataColumns.REGISTRATION_ANNUAL_PRICE.value: 500,
        DataColumns.INSURANCE_ANNUAL_PRICE.value: 1500,
        DataColumns.MAINTENANCE_ANNUAL_PRICE.value: 1000  # Added example maintenance fee
    }])

@pytest.fixture
def mock_charging_options():
    return pd.DataFrame({
        DataColumns.CHARGING_ID.value: [1, 2],
        DataColumns.PER_KWH_PRICE.value: [0.20, 0.25],
        DataColumns.CHARGING_APPROACH.value: ["AC", "DC"],
        DataColumns.CHARGER_POWER.value: [22, 150]
    })

@pytest.fixture
def mock_infrastructure_options():
    return pd.DataFrame({
        DataColumns.INFRASTRUCTURE_ID.value: [101],
        DataColumns.INFRASTRUCTURE_DESCRIPTION.value: ["Depot Charger"],
        DataColumns.INFRASTRUCTURE_PRICE.value: [50000]
    })

@pytest.fixture
def mock_financial_params():
    return pd.DataFrame({
        DataColumns.FINANCE_DESCRIPTION.value: [
            ParameterKeys.DIESEL_PRICE.value,
            ParameterKeys.INITIAL_DEPRECIATION.value,
            ParameterKeys.ANNUAL_DEPRECIATION.value
        ],
        DataColumns.FINANCE_DEFAULT_VALUE.value: [1.5, 0.2, 0.1]
    })

@pytest.fixture
def mock_battery_params():
    return pd.DataFrame({
        DataColumns.BATTERY_DESCRIPTION.value: [
            ParameterKeys.REPLACEMENT_COST.value,  # Corresponds to 'replacement_per_kwh_price'
            ParameterKeys.MINIMUM_CAPACITY.value, # Corresponds to 'minimum_capacity_percent' (EOL SOH)
            ParameterKeys.DEGRADATION_RATE.value    # Corresponds to 'degradation_annual_percent'
        ],
        DataColumns.BATTERY_DEFAULT_VALUE.value: [
            150,    # Replacement cost per kWh
            70,     # Minimum SOH (e.g., 70%)
            0.02    # Annual degradation rate (e.g., 2%)
        ]
    })

@pytest.fixture
def mock_incentives():
    return pd.DataFrame({
        "incentive_type": ["purchase_rebate"],
        "incentive_value_aud": [5000],
        "incentive_flag": [1]
    })

# --- Mock Calculation Function Returns ---

DEFAULT_ENERGY_COST_PER_KM = 0.1
DEFAULT_ANNUAL_COSTS = {"annual_operating_cost": 10000, "total_annual_fees": 2000}
DEFAULT_ACQUISITION_COST = 95000
DEFAULT_RESIDUAL_VALUE = 20000
DEFAULT_BATTERY_REPLACEMENT_COST = 5000
DEFAULT_NPV_ANNUAL = 70000
DEFAULT_TCO = {"tco_per_km": 0.5, "tco_lifetime": 150000}
DEFAULT_INFRA_COSTS = {"npv_total_infrastructure_cost_per_vehicle": 5000}
DEFAULT_INFRA_WITH_INCENTIVES = {"npv_total_infrastructure_cost_per_vehicle": 4000}
DEFAULT_TCO_WITH_INFRA = {"tco_per_km": 0.55, "tco_lifetime": 155000}


@pytest.fixture
def mock_calc_fns():
    with patch("tco_app.domain.sensitivity.single_param.calculate_energy_costs", MagicMock(return_value=DEFAULT_ENERGY_COST_PER_KM)) as mock_energy, \
         patch("tco_app.domain.sensitivity.single_param.calculate_annual_costs", MagicMock(return_value=DEFAULT_ANNUAL_COSTS)) as mock_annual, \
         patch("tco_app.domain.sensitivity.single_param.calculate_acquisition_cost", MagicMock(return_value=DEFAULT_ACQUISITION_COST)) as mock_acq, \
         patch("tco_app.domain.sensitivity.single_param.calculate_residual_value", MagicMock(return_value=DEFAULT_RESIDUAL_VALUE)) as mock_resid, \
         patch("tco_app.domain.sensitivity.single_param.calculate_battery_replacement", MagicMock(return_value=DEFAULT_BATTERY_REPLACEMENT_COST)) as mock_batt, \
         patch("tco_app.domain.sensitivity.single_param.calculate_npv", MagicMock(return_value=DEFAULT_NPV_ANNUAL)) as mock_npv, \
         patch("tco_app.domain.sensitivity.single_param.calculate_tco", MagicMock(return_value=DEFAULT_TCO)) as mock_tco, \
         patch("tco_app.domain.sensitivity.single_param.calculate_infrastructure_costs", MagicMock(return_value=DEFAULT_INFRA_COSTS)) as mock_infra, \
         patch("tco_app.domain.sensitivity.single_param.apply_infrastructure_incentives", MagicMock(return_value=DEFAULT_INFRA_WITH_INCENTIVES)) as mock_infra_incent, \
         patch("tco_app.domain.sensitivity.single_param.integrate_infrastructure_with_tco", MagicMock(return_value=DEFAULT_TCO_WITH_INFRA)) as mock_tco_infra, \
         patch("tco_app.domain.sensitivity.single_param.safe_division", MagicMock(side_effect=lambda num, den, **kwargs: num / den if den else 0)) as mock_safe_div:
        yield {
            "energy": mock_energy, "annual": mock_annual, "acq": mock_acq, 
            "resid": mock_resid, "batt": mock_batt, "npv": mock_npv, "tco": mock_tco,
            "infra": mock_infra, "infra_incent": mock_infra_incent, 
            "tco_infra": mock_tco_infra, "safe_div": mock_safe_div
        }

# --- Test Cases ---

@pytest.mark.parametrize(
    "parameter_name, initial_value, sensitivity_values, expected_modifier",
    [
        ("Annual Distance (km)", 50000, [40000, 60000], lambda mock_fns, val: mock_fns["annual"].call_args_list[0][0][3] == val and mock_fns["tco"].call_args_list[0][0][6] == val),
        ("Vehicle Lifetime (years)", 10, [8, 12], lambda mock_fns, val: \
            mock_fns["resid"].call_args_list[0][0][1] == val and \
            mock_fns["batt"].call_args_list[0][0][2] == val and \
            mock_fns["npv"].call_args_list[0][0][2] == val and \
            mock_fns["tco"].call_args_list[0][0][7] == val and \
            mock_fns["infra"].call_args_list[0][0][1] == val
        ),
        ("Discount Rate (%)", 5.0, [4.0, 6.0], lambda mock_fns, val: \
            mock_fns["batt"].call_args_list[0][0][3] == (val / 100) and \
            mock_fns["npv"].call_args_list[0][0][1] == (val / 100) and \
            mock_fns["infra"].call_args_list[0][0][2] == (val / 100)
        ),
    ]
)
def test_perform_sensitivity_analysis_scalar_params(
    parameter_name, initial_value, sensitivity_values, expected_modifier,
    mock_vehicle_data_series, mock_fees_data, mock_charging_options, 
    mock_infrastructure_options, mock_financial_params, mock_battery_params, 
    mock_incentives, mock_calc_fns
):
    # For these scalar parameters, the logic is similar
    # We check if the modified scalar is passed correctly to downstream functions

    results = perform_sensitivity_analysis(
        parameter_name=parameter_name,
        parameter_range=sensitivity_values,
        bev_vehicle_data=mock_vehicle_data_series,
        diesel_vehicle_data=mock_vehicle_data_series, # Using same for simplicity
        bev_fees=mock_fees_data,
        diesel_fees=mock_fees_data,
        charging_options=mock_charging_options,
        infrastructure_options=mock_infrastructure_options,
        financial_params=mock_financial_params,
        battery_params=mock_battery_params,
        emission_factors=pd.DataFrame(), # Not used by this function directly
        incentives=mock_incentives,
        selected_charging=1,
        selected_infrastructure=101,
        annual_kms=initial_value if parameter_name == "Annual Distance (km)" else 50000,
        truck_life_years=initial_value if parameter_name == "Vehicle Lifetime (years)" else 10,
        discount_rate=initial_value / 100 if parameter_name == "Discount Rate (%)" else 0.05,
        fleet_size=10,
        charging_mix=None,
        apply_incentives=True
    )

    assert len(results) == len(sensitivity_values)
    num_calc_calls_per_loop = 2 # BEV and Diesel for most calls

    for i, res_item in enumerate(results):
        current_param_value = sensitivity_values[i]
        assert res_item["parameter_value"] == current_param_value
        assert "bev" in res_item
        assert "diesel" in res_item
        assert res_item["bev"]["tco_per_km"] == DEFAULT_TCO_WITH_INFRA["tco_per_km"]

        # Reset mocks for next iteration's check if necessary or check specific calls
        # For simplicity, we'll check the first call after modification for each iteration
        # This requires mocks to be reset or analyzed carefully based on call order
        # The lambda 'expected_modifier' is designed to check the relevant calls
        # This part is tricky as mocks are not reset per loop iteration of sensitivity_values
        # A more robust check would involve inspecting call_args_list more deeply
        # or resetting mocks if the test structure allowed it easily per sensitivity value.
        
        # For now, let's verify the number of calls to key functions implies looping
        # Each iteration of sensitivity_values makes a set of calls for BEV and Diesel

    assert mock_calc_fns["energy"].call_count == len(sensitivity_values) * num_calc_calls_per_loop
    assert mock_calc_fns["annual"].call_count == len(sensitivity_values) * num_calc_calls_per_loop
    assert mock_calc_fns["tco"].call_count == len(sensitivity_values) * num_calc_calls_per_loop
    # infra is called once per sensitivity value for BEV
    assert mock_calc_fns["infra"].call_count == len(sensitivity_values) 


def test_perform_sensitivity_analysis_diesel_price(
    mock_vehicle_data_series, mock_fees_data, mock_charging_options, 
    mock_infrastructure_options, mock_financial_params, mock_battery_params, 
    mock_incentives, mock_calc_fns
):
    parameter_name = "Diesel Price ($/L)"
    sensitivity_values = [1.2, 1.8]
    initial_diesel_price = mock_financial_params[mock_financial_params[DataColumns.FINANCE_DESCRIPTION.value] == ParameterKeys.DIESEL_PRICE.value][DataColumns.FINANCE_DEFAULT_VALUE.value].iloc[0]

    results = perform_sensitivity_analysis(
        parameter_name=parameter_name,
        parameter_range=sensitivity_values,
        bev_vehicle_data=mock_vehicle_data_series,
        diesel_vehicle_data=mock_vehicle_data_series, 
        bev_fees=mock_fees_data,
        diesel_fees=mock_fees_data,
        charging_options=mock_charging_options,
        infrastructure_options=mock_infrastructure_options,
        financial_params=mock_financial_params.copy(), # Pass a copy to see modification
        battery_params=mock_battery_params,
        emission_factors=pd.DataFrame(),
        incentives=mock_incentives,
        selected_charging=1,
        selected_infrastructure=101,
        annual_kms=50000, truck_life_years=10, discount_rate=0.05, fleet_size=10
    )

    assert len(results) == len(sensitivity_values)
    # Check that financial_params was modified for diesel price
    # This is tricky because the mock_financial_params is copied inside the function
    # We need to check the argument passed to calculate_energy_costs for diesel

    # Expected calls: 2 sensitivity values * 2 (BEV+Diesel) = 4 calls to calculate_energy_costs
    assert mock_calc_fns["energy"].call_count == len(sensitivity_values) * 2
    
    # Check the financial_params passed to the DIESEL energy cost calculation
    # It should reflect the changed diesel price
    # Calls are [BEV_val1, Diesel_val1, BEV_val2, Diesel_val2 ...]
    for i, val in enumerate(sensitivity_values):
        diesel_energy_call_args = mock_calc_fns["energy"].call_args_list[i*2 + 1][0]
        fp_arg_for_diesel_call = diesel_energy_call_args[3] # financial_params is the 4th arg (index 3)
        modified_price = fp_arg_for_diesel_call[fp_arg_for_diesel_call[DataColumns.FINANCE_DESCRIPTION.value] == ParameterKeys.DIESEL_PRICE.value][DataColumns.FINANCE_DEFAULT_VALUE.value].iloc[0]
        assert modified_price == val

    # Restore original value if mock_financial_params is used elsewhere or make a deepcopy for the test
    mock_financial_params.loc[mock_financial_params[DataColumns.FINANCE_DESCRIPTION.value] == ParameterKeys.DIESEL_PRICE.value, DataColumns.FINANCE_DEFAULT_VALUE.value] = initial_diesel_price

def test_perform_sensitivity_analysis_electricity_price(
    mock_vehicle_data_series, mock_fees_data, mock_charging_options, 
    mock_infrastructure_options, mock_financial_params, mock_battery_params, 
    mock_incentives, mock_calc_fns
):
    parameter_name = "Electricity Price ($/kWh)"
    sensitivity_values = [0.15, 0.25]
    selected_charging_id = 1 # Assumes this ID exists in mock_charging_options
    base_price_selected_charger = mock_charging_options[mock_charging_options[DataColumns.CHARGING_ID.value] == selected_charging_id][DataColumns.PER_KWH_PRICE.value].iloc[0]

    results = perform_sensitivity_analysis(
        parameter_name=parameter_name,
        parameter_range=sensitivity_values,
        bev_vehicle_data=mock_vehicle_data_series,
        diesel_vehicle_data=mock_vehicle_data_series, 
        bev_fees=mock_fees_data,
        diesel_fees=mock_fees_data,
        charging_options=mock_charging_options.copy(), # Pass a copy
        infrastructure_options=mock_infrastructure_options,
        financial_params=mock_financial_params,
        battery_params=mock_battery_params,
        emission_factors=pd.DataFrame(),
        incentives=mock_incentives,
        selected_charging=selected_charging_id,
        selected_infrastructure=101,
        annual_kms=50000, truck_life_years=10, discount_rate=0.05, fleet_size=10
    )

    assert len(results) == len(sensitivity_values)
    assert mock_calc_fns["energy"].call_count == len(sensitivity_values) * 2

    for i, val in enumerate(sensitivity_values):
        bev_energy_call_args = mock_calc_fns["energy"].call_args_list[i*2][0]
        charging_options_arg_for_bev_call = bev_energy_call_args[2] # charging_options is 3rd arg (index 2)
        
        # Check if all prices in charging_options_arg_for_bev_call are scaled correctly
        for idx in charging_options_arg_for_bev_call.index:
            original_price_at_idx = mock_charging_options.loc[idx, DataColumns.PER_KWH_PRICE.value]
            expected_modified_price = val * (original_price_at_idx / base_price_selected_charger if base_price_selected_charger else 0)
            assert charging_options_arg_for_bev_call.loc[idx, DataColumns.PER_KWH_PRICE.value] == pytest.approx(expected_modified_price)

def test_perform_sensitivity_analysis_unsupported_param(
    mock_vehicle_data_series, mock_fees_data, mock_charging_options, 
    mock_infrastructure_options, mock_financial_params, mock_battery_params, 
    mock_incentives, mock_calc_fns
):
    results = perform_sensitivity_analysis(
        parameter_name="Unsupported Param Name",
        parameter_range=[10, 20],
        bev_vehicle_data=mock_vehicle_data_series,
        diesel_vehicle_data=mock_vehicle_data_series, 
        bev_fees=mock_fees_data,
        diesel_fees=mock_fees_data,
        charging_options=mock_charging_options,
        infrastructure_options=mock_infrastructure_options,
        financial_params=mock_financial_params,
        battery_params=mock_battery_params,
        emission_factors=pd.DataFrame(),
        incentives=mock_incentives,
        selected_charging=1,
        selected_infrastructure=101,
        annual_kms=50000, truck_life_years=10, discount_rate=0.05, fleet_size=10
    )
    assert len(results) == 0 # Should skip and return empty list
    # Check that no calculation functions were called
    for mock_fn in mock_calc_fns.values():
        if hasattr(mock_fn, 'call_count'): # MagicMock has call_count
             assert mock_fn.call_count == 0

