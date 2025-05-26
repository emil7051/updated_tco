"""Test payload penalty integration in TCO calculation service."""

import pytest
import pandas as pd

from tco_app.services.tco_calculation_service import TCOCalculationService
from tco_app.services.dtos import CalculationRequest, CalculationParameters
from tco_app.repositories import VehicleRepository, ParametersRepository
from tco_app.src.constants import DataColumns, Drivetrain


@pytest.fixture
def mock_data_tables():
    """Create mock data tables for testing."""
    vehicle_data = pd.DataFrame({
        DataColumns.VEHICLE_ID: ["BEV001", "DSL001"],
        DataColumns.VEHICLE_DRIVETRAIN: [Drivetrain.BEV, Drivetrain.DIESEL],
        DataColumns.PAYLOAD_T: [10.0, 12.0],  # BEV has less payload
        DataColumns.MSRP_PRICE: [150000, 100000],
        DataColumns.COMPARISON_PAIR_ID: ["DSL001", "BEV001"],
    })
    
    fees_data = pd.DataFrame({
        DataColumns.VEHICLE_ID: ["BEV001", "DSL001"],
        "maintenance_perkm_price": [0.10, 0.15],
        "registration_annual_price": [1000, 1000],
        "insurance_annual_price": [2000, 2000],
        "stamp_duty_price": [5000, 3000],
    })
    
    financial_params = pd.DataFrame({
        DataColumns.FINANCE_DESCRIPTION: [
            "freight_value_per_tonne",
            "driver_cost_hourly",
            "avg_trip_distance",
            "avg_loadunload_time",
            "avg_speed_kmh",
            "residual_value_initial_percentage",
            "residual_value_annual_percentage",
        ],
        DataColumns.FINANCE_DEFAULT_VALUE: [120, 35, 100, 1, 60, 0.9, 0.95],
    })
    
    return {
        "vehicle_models": vehicle_data,
        "vehicle_fees": fees_data,
        "financial_params": financial_params,
        "charging_options": pd.DataFrame(),
        "infrastructure_options": pd.DataFrame({
            DataColumns.INFRASTRUCTURE_ID: [1],
            DataColumns.INFRASTRUCTURE_PRICE: [50000],
            "service_life_years": [10],
            "maintenance_percent": [0.05],
        }),
        "battery_params": pd.DataFrame(),
        "emission_factors": pd.DataFrame(),
        "externalities_params": pd.DataFrame(),
        "incentives": pd.DataFrame(),
    }


def test_payload_penalty_calculation_in_comparison(mock_data_tables):
    """Test that payload penalties are calculated correctly in vehicle comparison."""
    # Initialize service
    vehicle_repo = VehicleRepository(mock_data_tables)
    params_repo = ParametersRepository(mock_data_tables)
    tco_service = TCOCalculationService(vehicle_repo, params_repo)
    
    # Create calculation parameters
    params = CalculationParameters(
        annual_kms=50000,
        truck_life_years=10,
        discount_rate=0.07,
        selected_charging_profile_id=1,
        selected_infrastructure_id=1,
        fleet_size=1,
        apply_incentives=False,
    )
    
    # Create BEV request
    bev_request = CalculationRequest(
        vehicle_data=vehicle_repo.get_vehicle_by_id("BEV001"),
        fees_data=vehicle_repo.get_fees_by_vehicle_id("BEV001"),
        parameters=params,
        charging_options=mock_data_tables["charging_options"],
        infrastructure_options=mock_data_tables["infrastructure_options"],
        financial_params=mock_data_tables["financial_params"],
        battery_params=mock_data_tables["battery_params"],
        emission_factors=mock_data_tables["emission_factors"],
        externalities_data=mock_data_tables["externalities_params"],
        incentives=mock_data_tables["incentives"],
    )
    
    # Create Diesel request
    diesel_request = CalculationRequest(
        vehicle_data=vehicle_repo.get_vehicle_by_id("DSL001"),
        fees_data=vehicle_repo.get_fees_by_vehicle_id("DSL001"),
        parameters=params,
        charging_options=mock_data_tables["charging_options"],
        infrastructure_options=mock_data_tables["infrastructure_options"],
        financial_params=mock_data_tables["financial_params"],
        battery_params=mock_data_tables["battery_params"],
        emission_factors=mock_data_tables["emission_factors"],
        externalities_data=mock_data_tables["externalities_params"],
        incentives=mock_data_tables["incentives"],
    )
    
    # Perform comparison
    comparison_result = tco_service.compare_vehicles(bev_request, diesel_request)
    
    # Verify payload penalties are calculated
    assert hasattr(comparison_result, "payload_penalties")
    assert comparison_result.payload_penalties is not None
    assert comparison_result.payload_penalties["has_penalty"] is True
    assert comparison_result.payload_penalties["payload_difference"] == 2.0  # 12 - 10
    assert comparison_result.payload_penalties["payload_difference_percentage"] == pytest.approx(16.67, rel=0.01)
    assert comparison_result.payload_penalties["additional_operational_cost_lifetime"] > 0
    
    # Verify TCO savings reflect payload penalty
    # Without payload penalty, BEV might have lower TCO, but with penalty it should be adjusted
    assert comparison_result.tco_savings_lifetime < comparison_result.comparison_vehicle_result.tco_total_lifetime - comparison_result.base_vehicle_result.tco_total_lifetime


def test_no_payload_penalty_when_bev_has_more_capacity(mock_data_tables):
    """Test that no payload penalty is applied when BEV has equal or more capacity."""
    # Modify BEV to have more payload
    mock_data_tables["vehicle_models"].loc[
        mock_data_tables["vehicle_models"][DataColumns.VEHICLE_ID] == "BEV001",
        DataColumns.PAYLOAD_T
    ] = 15.0
    
    # Initialize service
    vehicle_repo = VehicleRepository(mock_data_tables)
    params_repo = ParametersRepository(mock_data_tables)
    tco_service = TCOCalculationService(vehicle_repo, params_repo)
    
    # Create calculation parameters
    params = CalculationParameters(
        annual_kms=50000,
        truck_life_years=10,
        discount_rate=0.07,
        selected_charging_profile_id=1,
        selected_infrastructure_id=1,
        fleet_size=1,
        apply_incentives=False,
    )
    
    # Create requests
    bev_request = CalculationRequest(
        vehicle_data=vehicle_repo.get_vehicle_by_id("BEV001"),
        fees_data=vehicle_repo.get_fees_by_vehicle_id("BEV001"),
        parameters=params,
        charging_options=mock_data_tables["charging_options"],
        infrastructure_options=mock_data_tables["infrastructure_options"],
        financial_params=mock_data_tables["financial_params"],
        battery_params=mock_data_tables["battery_params"],
        emission_factors=mock_data_tables["emission_factors"],
        externalities_data=mock_data_tables["externalities_params"],
        incentives=mock_data_tables["incentives"],
    )
    
    diesel_request = CalculationRequest(
        vehicle_data=vehicle_repo.get_vehicle_by_id("DSL001"),
        fees_data=vehicle_repo.get_fees_by_vehicle_id("DSL001"),
        parameters=params,
        charging_options=mock_data_tables["charging_options"],
        infrastructure_options=mock_data_tables["infrastructure_options"],
        financial_params=mock_data_tables["financial_params"],
        battery_params=mock_data_tables["battery_params"],
        emission_factors=mock_data_tables["emission_factors"],
        externalities_data=mock_data_tables["externalities_params"],
        incentives=mock_data_tables["incentives"],
    )
    
    # Perform comparison
    comparison_result = tco_service.compare_vehicles(bev_request, diesel_request)
    
    # Verify no payload penalty
    assert comparison_result.payload_penalties["has_penalty"] is False
    assert comparison_result.payload_penalties["payload_difference"] == -3.0  # 12 - 15 