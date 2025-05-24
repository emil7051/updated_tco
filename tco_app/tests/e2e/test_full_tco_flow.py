"""End-to-end tests for the complete TCO calculation flow."""

import pytest
import pandas as pd
from unittest.mock import Mock

from tco_app.src.constants import DataColumns, Drivetrain
from tco_app.repositories import VehicleRepository, ParametersRepository
from tco_app.services.tco_calculation_service import TCOCalculationService
from tco_app.ui.calculation_orchestrator import CalculationOrchestrator
from tco_app.services.dtos import (
    CalculationRequest,
    CalculationParameters,
    TCOResult,
    ComparisonResult,
)


class TestFullTCOFlow:
    """Test complete TCO calculation flow from UI to results."""

    @pytest.fixture
    def mock_repositories(self):
        """Mock all required repositories."""
        vehicle_repo = Mock(spec=VehicleRepository)
        params_repo = Mock(spec=ParametersRepository)

        # Mock vehicle data
        bev_vehicle = pd.Series(
            {
                DataColumns.VEHICLE_ID: "MFTBC6X4BEV1",
                DataColumns.VEHICLE_MODEL: "E-Actros 300",
                DataColumns.VEHICLE_TYPE: "Medium Rigid",
                DataColumns.VEHICLE_DRIVETRAIN: Drivetrain.BEV,
                DataColumns.BODY_TYPE: "Articulated",
                DataColumns.BATTERY_CAPACITY_KWH: 540.0,
                DataColumns.RANGE_KM: 300.0,
                DataColumns.MSRP_PRICE: 380000,
                DataColumns.BATTERY_EFFICIENCY: 0.9,
                DataColumns.KWH_PER100KM: 80.0,  # Add energy consumption for BEV
                DataColumns.PAYLOAD_T: 15.0,  # Add payload in tonnes
            }
        )

        diesel_vehicle = pd.Series(
            {
                DataColumns.VEHICLE_ID: "MFTBC6X4DIESEL1",
                DataColumns.VEHICLE_MODEL: "Actros",
                DataColumns.VEHICLE_TYPE: "Medium Rigid",
                DataColumns.VEHICLE_DRIVETRAIN: Drivetrain.DIESEL,
                DataColumns.BODY_TYPE: "Articulated",
                DataColumns.LITRES_PER100KM: 28.0,
                DataColumns.MSRP_PRICE: 150000,
                DataColumns.PAYLOAD_T: 15.0,  # Add payload in tonnes
            }
        )

        vehicle_repo.get_vehicle_by_id.side_effect = lambda id: (
            bev_vehicle if "BEV" in id else diesel_vehicle
        )

        # Mock fees
        bev_fees = pd.Series(
            {
                DataColumns.VEHICLE_ID: "MFTBC6X4BEV1",
                "maintenance_perkm_price": 0.10,
                DataColumns.REGISTRATION_ANNUAL_PRICE: 2000,
                DataColumns.INSURANCE_ANNUAL_PRICE: 5000,
                DataColumns.REGISTRATION_UPFRONT_PRICE: 500,
                "stamp_duty_price": 3000,
            }
        )

        diesel_fees = pd.Series(
            {
                DataColumns.VEHICLE_ID: "MFTBC6X4DIESEL1",
                "maintenance_perkm_price": 0.12,
                DataColumns.REGISTRATION_ANNUAL_PRICE: 1800,
                DataColumns.INSURANCE_ANNUAL_PRICE: 4500,
                DataColumns.REGISTRATION_UPFRONT_PRICE: 450,
                "stamp_duty_price": 2000,
            }
        )

        vehicle_repo.get_fees_by_vehicle_id.side_effect = lambda id: (
            bev_fees if "BEV" in id else diesel_fees
        )

        # Mock financial parameters as DataFrame
        financial_params = pd.DataFrame(
            {
                "financial_id": ["FP001", "FP008", "FP009", "FP011", "FP020"],
                "finance_description": [
                    "discount_rate_percent",
                    "diesel_price",
                    "truck_life_years",
                    "annual_kms",
                    "residual_value_pct",
                ],
                "default_value": [0.05, 2.0, 10, 100000, 0.2],
            }
        )
        params_repo.get_financial_params.return_value = financial_params

        # Mock emission factors as DataFrame
        emission_factors = pd.DataFrame(
            {
                "emissions_id": ["EF004", "EF001"],
                "fuel_type": ["electricity", "diesel"],
                "emission_standard": ["Grid", "Euro IV+"],
                "co2_per_unit": [0.7, 3.384],
                "emissions_unit": ["kg_per_kwh", "kg_per_litre"],
            }
        )
        params_repo.get_emission_factors.return_value = emission_factors

        # Mock battery parameters as DataFrame
        battery_params = pd.DataFrame(
            {
                "battery_id": ["BP001", "BP002", "BP003", "BP004"],
                "battery_description": [
                    "replacement_per_kwh_price",
                    "degradation_annual_percent",
                    "minimum_capacity_percent",
                    "recycling_value_percent",
                ],
                "default_value": [150.0, 0.025, 0.7, 0.1],
            }
        )
        params_repo.get_battery_params.return_value = battery_params

        # Mock externalities data as DataFrame
        externalities = pd.DataFrame(
            {
                "externality_id": [
                    "EC003",
                    "EC004",
                    "EC009",
                    "EC010",
                    "EC021",
                    "EC022",
                    "EC025",
                    "EC026",
                ],
                "pollutant_type": [
                    "noise_pollution",
                    "noise_pollution",
                    "pm25_pollution",
                    "pm25_pollution",
                    "air_pollution_total",
                    "air_pollution_total",
                    "externalities_total",
                    "externalities_total",
                ],
                "vehicle_class": [
                    "Medium Rigid",
                    "Medium Rigid",
                    "Medium Rigid",
                    "Medium Rigid",
                    "Medium Rigid",
                    "Medium Rigid",
                    "Medium Rigid",
                    "Medium Rigid",
                ],
                "drivetrain": [
                    "Diesel",
                    "BEV",
                    "Diesel",
                    "BEV",
                    "Diesel",
                    "BEV",
                    "Diesel",
                    "BEV",
                ],
                "cost_per_km": [0.017, 0.006, 0.048, 0.0, 0.113, 0.0, 0.150, 0.006],
                "cost_unit": [
                    "AUD/km",
                    "AUD/km",
                    "AUD/km",
                    "AUD/km",
                    "AUD/km",
                    "AUD/km",
                    "AUD/km",
                    "AUD/km",
                ],
                "year": [2025, 2025, 2025, 2025, 2025, 2025, 2025, 2025],
                "calculation_basis": [
                    "desc1",
                    "desc2",
                    "desc3",
                    "desc4",
                    "desc5",
                    "desc6",
                    "desc7",
                    "desc8",
                ],
            }
        )
        params_repo.get_externalities_data.return_value = externalities

        # Mock charging options
        charging_options = pd.DataFrame(
            {
                "charging_id": [1, 2, 3],
                "charging_approach": ["Retail", "Retail off-peak", "Solar & Storage"],
                "per_kwh_price": [0.3, 0.15, 0.04],
                "charging_proportion": [0.2, 0.5, 0.3],
            }
        )
        params_repo.get_charging_options.return_value = charging_options

        # Mock infrastructure options
        infrastructure_options = pd.DataFrame(
            {
                "infrastructure_id": [1, 2, 3],
                "infrastructure_description": [
                    "No Infrastructure",
                    "DC Fast Charger 80 kW",
                    "DC Fast Charger 160 kW",
                ],
                "infrastructure_price": [0, 55000, 90000],
                "service_life_years": [15, 15, 15],
                "maintenance_percent": [0, 0.03, 0.03],
            }
        )
        params_repo.get_infrastructure_options.return_value = infrastructure_options

        # Mock incentives data
        incentives = pd.DataFrame(
            {
                "incentive_type": [
                    "purchase_rebate",
                    "stamp_duty_exemption",
                    "registration_exemption",
                ],
                "incentive_value": [15000, 1.0, 1.0],
                "incentive_rate": [0.0, 1.0, 1.0],
                "drivetrain": ["BEV", "BEV", "BEV"],
                "effective_date": ["2023-01-01", "2023-01-01", "2023-01-01"],
                "expiry_date": ["2025-12-31", "2025-12-31", "2025-12-31"],
                "incentive_flag": [1, 1, 1],
            }
        )
        params_repo.get_incentives.return_value = incentives

        return vehicle_repo, params_repo

    @pytest.fixture
    def calculation_service(self, mock_repositories):
        """Create calculation service with mocked repositories."""
        vehicle_repo, params_repo = mock_repositories
        return TCOCalculationService(vehicle_repo, params_repo)

    @pytest.fixture
    def calculation_orchestrator(self, mock_repositories):
        """Create calculation orchestrator with mocked repositories."""
        vehicle_repo, params_repo = mock_repositories

        # Create mock data tables - the CalculationOrchestrator will create its own repositories
        # but we'll mock them out
        data_tables = {}
        ui_context = {"modified_tables": data_tables}

        orchestrator = CalculationOrchestrator(data_tables, ui_context)

        # Replace the repositories with our mocks
        orchestrator.vehicle_repo = vehicle_repo
        orchestrator.params_repo = params_repo
        orchestrator.tco_service = TCOCalculationService(vehicle_repo, params_repo)

        return orchestrator

    def test_single_vehicle_calculation_flow(self, calculation_orchestrator):
        """Test end-to-end flow for single vehicle calculation."""
        # Set UI context
        calculation_orchestrator.ui_context = {
            "annual_kms": 100000,
            "truck_life_years": 10,
            "discount_rate": 0.05,
            "selected_charging": 1,  # Should be an ID
            "selected_infrastructure": 1,  # Should be an ID
            "fleet_size": 10,
        }

        # Build calculation request for BEV
        bev_request = calculation_orchestrator._build_calculation_request(
            "MFTBC6X4BEV1"
        )

        # Validate request structure
        assert bev_request.vehicle_data[DataColumns.VEHICLE_ID] == "MFTBC6X4BEV1"
        assert bev_request.parameters.annual_kms == 100000
        assert bev_request.parameters.truck_life_years == 10

        # Perform calculation
        result = calculation_orchestrator.tco_service.calculate_single_vehicle_tco(
            bev_request
        )

        # Validate result
        assert isinstance(result, TCOResult)
        assert result.vehicle_id == "MFTBC6X4BEV1"
        assert result.tco_total_lifetime > 0
        assert result.tco_per_km > 0

    def test_comparison_calculation_flow(self, calculation_orchestrator):
        """Test end-to-end flow for vehicle comparison."""
        # Set UI context
        calculation_orchestrator.ui_context = {
            "annual_kms": 100000,
            "truck_life_years": 10,
            "discount_rate": 0.05,
            "selected_charging": 1,
            "selected_infrastructure": 1,
            "fleet_size": 10,
        }

        # Build calculation requests for both vehicles
        bev_request = calculation_orchestrator._build_calculation_request(
            "MFTBC6X4BEV1"
        )
        diesel_request = calculation_orchestrator._build_calculation_request(
            "MFTBC6X4DIESEL1"
        )

        # Compare BEV vs Diesel
        comparison = calculation_orchestrator.tco_service.compare_vehicles(
            bev_request, diesel_request
        )

        # Validate comparison results
        assert isinstance(comparison, ComparisonResult)
        assert comparison.base_vehicle_result.vehicle_id == "MFTBC6X4BEV1"
        assert comparison.comparison_vehicle_result.vehicle_id == "MFTBC6X4DIESEL1"
        assert comparison.tco_savings_lifetime != 0

        # Validate TCO difference calculation
        expected_savings = (
            comparison.comparison_vehicle_result.tco_total_lifetime
            - comparison.base_vehicle_result.tco_total_lifetime
        )
        assert abs(comparison.tco_savings_lifetime - expected_savings) < 0.01

    def test_sensitivity_analysis_flow(self, calculation_orchestrator):
        """Test sensitivity analysis with parameter variations."""
        # Set UI context
        calculation_orchestrator.ui_context = {
            "annual_kms": 100000,
            "truck_life_years": 10,
            "discount_rate": 0.05,
            "selected_charging": 1,
            "selected_infrastructure": 1,
            "fleet_size": 10,
        }

        # Calculate baseline
        baseline_result = (
            calculation_orchestrator.tco_service.calculate_single_vehicle_tco(
                calculation_orchestrator._build_calculation_request("MFTBC6X4BEV1")
            )
        )

        # Update context with higher kms
        calculation_orchestrator.ui_context["annual_kms"] = 150000

        # Calculate with higher kms
        high_kms_result = (
            calculation_orchestrator.tco_service.calculate_single_vehicle_tco(
                calculation_orchestrator._build_calculation_request("MFTBC6X4BEV1")
            )
        )

        # Validate sensitivity impact
        assert high_kms_result.tco_total_lifetime > baseline_result.tco_total_lifetime
        # Cost per km should be lower with higher utilization
        assert high_kms_result.tco_per_km < baseline_result.tco_per_km

    def test_fleet_size_impact(self, calculation_orchestrator):
        """Test impact of fleet size on infrastructure costs."""
        fleet_sizes = [1, 10, 50]
        previous_infra_cost = 0

        for fleet_size in fleet_sizes:
            calculation_orchestrator.ui_context = {
                "annual_kms": 100000,
                "truck_life_years": 10,
                "discount_rate": 0.05,
                "selected_charging": 1,
                "selected_infrastructure": 1,
                "fleet_size": fleet_size,
            }

            result = calculation_orchestrator.tco_service.calculate_single_vehicle_tco(
                calculation_orchestrator._build_calculation_request("MFTBC6X4BEV1")
            )

            # Infrastructure cost per vehicle should decrease with fleet size
            infra_cost_per_vehicle = result.npv_infrastructure_cost
            if previous_infra_cost > 0:
                assert infra_cost_per_vehicle < previous_infra_cost
            previous_infra_cost = infra_cost_per_vehicle
