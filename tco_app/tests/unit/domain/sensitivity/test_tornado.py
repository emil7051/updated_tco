import pandas as pd
import pytest
from unittest.mock import patch

from tco_app.domain.sensitivity.tornado import calculate_tornado_data
from tco_app.src.constants import DataColumns, ParameterKeys


def test_calculate_tornado_data_basic():
    bev_results = {"vehicle_data": {}, "fees": {}, "tco": {"tco_per_km": 1.0}}
    diesel_results = {"vehicle_data": {}, "fees": {}}

    financial_params = pd.DataFrame({
        DataColumns.FINANCE_DESCRIPTION: [ParameterKeys.DIESEL_PRICE],
        DataColumns.FINANCE_DEFAULT_VALUE: [2.0],
    })
    battery_params = pd.DataFrame({
        DataColumns.BATTERY_DESCRIPTION: [ParameterKeys.REPLACEMENT_COST],
        DataColumns.BATTERY_DEFAULT_VALUE: [100],
    })
    charging_options = pd.DataFrame({
        DataColumns.CHARGING_ID: [1],
        DataColumns.PER_KWH_PRICE: [0.30],
    })
    infrastructure_options = pd.DataFrame({
        DataColumns.INFRASTRUCTURE_ID: [1],
        DataColumns.INFRASTRUCTURE_PRICE: [1000],
    })

    with patch("tco_app.domain.sensitivity.tornado.perform_sensitivity_analysis") as mock_perf:
        mock_perf.return_value = [
            {"bev": {"tco_per_km": 0.8}},
            {"bev": {"tco_per_km": 1.2}},
        ]
        result = calculate_tornado_data(
            bev_results=bev_results,
            diesel_results=diesel_results,
            financial_params=financial_params,
            battery_params=battery_params,
            charging_options=charging_options,
            infrastructure_options=infrastructure_options,
            emission_factors=pd.DataFrame(),
            incentives=pd.DataFrame(),
            selected_charging=1,
            selected_infrastructure=1,
            annual_kms=1000,
            truck_life_years=5,
            discount_rate=0.1,
            fleet_size=1,
        )

    assert result["base_tco"] == 1.0
    assert len(result["impacts"]) == 5
    for impact in result["impacts"].values():
        assert impact["min_impact"] == pytest.approx(-0.2)
        assert impact["max_impact"] == pytest.approx(0.2)


def test_electricity_price_range_uses_weighted_value():
    """Ensure weighted electricity price is used for sensitivity analysis."""
    bev_results = {
        "vehicle_data": {},
        "fees": {},
        "tco": {"tco_per_km": 1.5},
        "weighted_electricity_price": 0.4,
    }
    diesel_results = {"vehicle_data": {}, "fees": {}}

    financial_params = pd.DataFrame({
        DataColumns.FINANCE_DESCRIPTION: [ParameterKeys.DIESEL_PRICE],
        DataColumns.FINANCE_DEFAULT_VALUE: [2.0],
    })
    battery_params = pd.DataFrame({
        DataColumns.BATTERY_DESCRIPTION: [ParameterKeys.REPLACEMENT_COST],
        DataColumns.BATTERY_DEFAULT_VALUE: [100],
    })
    charging_options = pd.DataFrame({
        DataColumns.CHARGING_ID: [1],
        DataColumns.PER_KWH_PRICE: [0.30],
    })
    infrastructure_options = pd.DataFrame({
        DataColumns.INFRASTRUCTURE_ID: [1],
        DataColumns.INFRASTRUCTURE_PRICE: [1000],
    })

    def side_effect(param_name, param_range, *args, **kwargs):
        if param_name == "Electricity Price ($/kWh)":
            assert param_range == [0.4 * 0.8, 0.4 * 1.2]
        return [
            {"bev": {"tco_per_km": 1.2}},
            {"bev": {"tco_per_km": 1.8}},
        ]

    with patch("tco_app.domain.sensitivity.tornado.perform_sensitivity_analysis") as mock_perf:
        mock_perf.side_effect = side_effect
        result = calculate_tornado_data(
            bev_results=bev_results,
            diesel_results=diesel_results,
            financial_params=financial_params,
            battery_params=battery_params,
            charging_options=charging_options,
            infrastructure_options=infrastructure_options,
            emission_factors=pd.DataFrame(),
            incentives=pd.DataFrame(),
            selected_charging=1,
            selected_infrastructure=1,
            annual_kms=1000,
            truck_life_years=5,
            discount_rate=0.1,
            fleet_size=1,
        )

    assert result["base_tco"] == 1.5
    assert len(result["impacts"]) == 5
    for impact in result["impacts"].values():
        assert impact["min_impact"] == pytest.approx(-0.3)
        assert impact["max_impact"] == pytest.approx(0.3)
