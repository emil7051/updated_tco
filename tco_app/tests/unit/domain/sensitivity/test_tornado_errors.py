import pandas as pd
import pytest

from tco_app.domain.sensitivity.tornado import calculate_tornado_data
from tco_app.src.constants import DataColumns, ParameterKeys


def _basic_params():
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
    return financial_params, battery_params, charging_options, infrastructure_options


def test_missing_bev_fees_raises_value_error():
    bev_results = {"vehicle_data": {}, "tco": {"tco_per_km": 1.0}}
    diesel_results = {"vehicle_data": {}, "fees": {}}

    financial_params, battery_params, charging_options, infrastructure_options = _basic_params()

    with pytest.raises(ValueError):
        calculate_tornado_data(
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


def test_missing_diesel_fees_raises_value_error():
    bev_results = {"vehicle_data": {}, "fees": {}, "tco": {"tco_per_km": 1.0}}
    diesel_results = {"vehicle_data": {}}

    financial_params, battery_params, charging_options, infrastructure_options = _basic_params()

    with pytest.raises(ValueError):
        calculate_tornado_data(
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
