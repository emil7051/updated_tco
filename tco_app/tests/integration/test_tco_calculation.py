"""Integration tests for TCO calculation using modern service architecture."""

from unittest.mock import Mock

import pytest

from tco_app.repositories import ParametersRepository, VehicleRepository
from tco_app.services.dtos import CalculationParameters, CalculationRequest
from tco_app.services.tco_calculation_service import TCOCalculationService
from tco_app.src import pd
from tco_app.src.constants import DataColumns, Drivetrain


class TestTCOCalculationIntegration:
    """Integration tests for the complete TCO calculation process using modern service architecture."""

    @pytest.fixture
    def mock_vehicle_repo(self):
        """Mock vehicle repository for testing."""
        return Mock(spec=VehicleRepository)

    @pytest.fixture
    def mock_params_repo(self):
        """Mock parameters repository for testing."""
        return Mock(spec=ParametersRepository)

    @pytest.fixture
    def tco_service(self, mock_vehicle_repo, mock_params_repo):
        """TCO calculation service instance for testing."""
        return TCOCalculationService(mock_vehicle_repo, mock_params_repo)

    @pytest.fixture
    def bev_vehicle_data(self):
        """BEV vehicle data for testing."""
        return pd.Series(
            {
                DataColumns.VEHICLE_ID: "BEV001",
                DataColumns.VEHICLE_TYPE: "Articulated",
                DataColumns.VEHICLE_DRIVETRAIN: Drivetrain.BEV,
                DataColumns.VEHICLE_MODEL: "Test BEV Truck",
                DataColumns.PAYLOAD_T: 42.0,
                DataColumns.MSRP_PRICE: 400000,
                DataColumns.RANGE_KM: 300,
                DataColumns.BATTERY_CAPACITY_KWH: 400,
                DataColumns.KWH_PER100KM: 130,
                DataColumns.COMPARISON_PAIR_ID: "DSL001",
            }
        )

    @pytest.fixture
    def diesel_vehicle_data(self):
        """Diesel vehicle data for testing."""
        return pd.Series(
            {
                DataColumns.VEHICLE_ID: "DSL001",
                DataColumns.VEHICLE_TYPE: "Articulated",
                DataColumns.VEHICLE_DRIVETRAIN: Drivetrain.DIESEL,
                DataColumns.VEHICLE_MODEL: "Test Diesel Truck",
                DataColumns.PAYLOAD_T: 42.0,
                DataColumns.MSRP_PRICE: 320000,
                DataColumns.RANGE_KM: 600,
                DataColumns.LITRES_PER100KM: 28,
                DataColumns.COMPARISON_PAIR_ID: "BEV001",
            }
        )

    @pytest.fixture
    def bev_fees_data(self):
        """BEV fees data for testing."""
        return pd.Series(
            {
                "vehicle_id": "BEV001",
                "maintenance_perkm_price": 0.12,
                "registration_annual_price": 900,
                "insurance_annual_price": 2400,
                "stamp_duty_price": 8000,
            }
        )

    @pytest.fixture
    def diesel_fees_data(self):
        """Diesel fees data for testing."""
        return pd.Series(
            {
                "vehicle_id": "DSL001",
                "maintenance_perkm_price": 0.10,
                "registration_annual_price": 850,
                "insurance_annual_price": 2000,
                "stamp_duty_price": 5000,
            }
        )

    @pytest.fixture
    def calculation_parameters(self):
        """Standard calculation parameters for testing."""
        return CalculationParameters(
            annual_kms=100000,
            truck_life_years=10,
            discount_rate=0.07,
            selected_charging_profile_id=1,
            selected_infrastructure_id=1,
            fleet_size=1,
            apply_incentives=True,
            scenario_name="Integration Test",
        )

    @pytest.fixture
    def charging_options(self):
        """Charging options DataFrame for testing."""
        return pd.DataFrame(
            [
                {
                    DataColumns.CHARGING_ID: 1,
                    DataColumns.PER_KWH_PRICE: 0.25,
                    DataColumns.CHARGING_APPROACH: "Depot 80 kW",
                },
                {
                    DataColumns.CHARGING_ID: 2,
                    DataColumns.PER_KWH_PRICE: 0.60,
                    DataColumns.CHARGING_APPROACH: "Public 150 kW",
                },
            ]
        )

    @pytest.fixture
    def infrastructure_options(self):
        """Infrastructure options DataFrame for testing."""
        return pd.DataFrame(
            [
                {
                    DataColumns.INFRASTRUCTURE_ID: 1,
                    DataColumns.INFRASTRUCTURE_DESCRIPTION: "80 kW depot charger",
                    DataColumns.CHARGER_POWER: 80,
                    DataColumns.CHARGER_EFFICIENCY: 0.95,
                    DataColumns.UTILIZATION_HOURS: 8,
                    DataColumns.INFRASTRUCTURE_PRICE: 80000,
                    DataColumns.SERVICE_LIFE_YEARS: 8,
                    DataColumns.MAINTENANCE_PERCENT: 0.02,
                },
            ]
        )

    @pytest.fixture
    def financial_params(self):
        """Financial parameters DataFrame for testing."""
        return pd.DataFrame(
            [
                {
                    "finance_description": "diesel_price",
                    "default_value": 2.0,
                },
                {
                    "finance_description": "discount_rate_percent",
                    "default_value": 0.07,
                },
                {
                    "finance_description": "carbon_price",
                    "default_value": 25.0,
                },
                {
                    "finance_description": "truck_life_years",
                    "default_value": 10,
                },
                {
                    "finance_description": "annual_kms",
                    "default_value": 100000,
                },
                {
                    "finance_description": "initial_depreciation_percent",
                    "default_value": 0.20,
                },
            ]
        )

    @pytest.fixture
    def battery_params(self):
        """Battery parameters DataFrame for testing."""
        return pd.DataFrame(
            [
                {
                    DataColumns.BATTERY_DESCRIPTION: "replacement_per_kwh_price",
                    DataColumns.BATTERY_DEFAULT_VALUE: 100,
                },
                {
                    DataColumns.BATTERY_DESCRIPTION: "degradation_annual_percent",
                    DataColumns.BATTERY_DEFAULT_VALUE: 0.02,
                },
                {
                    DataColumns.BATTERY_DESCRIPTION: "minimum_capacity_percent",
                    DataColumns.BATTERY_DEFAULT_VALUE: 0.7,
                },
            ]
        )

    @pytest.fixture
    def emission_factors(self):
        """Emission factors DataFrame for testing."""
        return pd.DataFrame(
            [
                {
                    DataColumns.FUEL_TYPE: "electricity",
                    DataColumns.EMISSION_STANDARD: "Grid",
                    DataColumns.GRID_EMISSION_FACTOR: 0.5,  # kg CO2/kWh
                    DataColumns.CO2_PER_UNIT: 0.5,
                },
                {
                    DataColumns.FUEL_TYPE: "diesel",
                    DataColumns.EMISSION_STANDARD: "Euro IV+",
                    DataColumns.DIESEL_EMISSION_FACTOR: 2.68,  # kg CO2/L
                    DataColumns.CO2_PER_UNIT: 2.68,
                },
            ]
        )

    @pytest.fixture
    def externalities_data(self):
        """Externalities data DataFrame for testing."""
        return pd.DataFrame(
            [
                {
                    "vehicle_class": "Articulated",
                    "drivetrain": Drivetrain.BEV,
                    "pollutant_type": "externalities_total",
                    "cost_per_km": 0.03,
                },
                {
                    "vehicle_class": "Articulated",
                    "drivetrain": Drivetrain.DIESEL,
                    "pollutant_type": "externalities_total",
                    "cost_per_km": 0.07,
                },
            ]
        )

    @pytest.fixture
    def incentives(self):
        """Incentives DataFrame for testing."""
        return pd.DataFrame(
            [
                {
                    "incentive_flag": 1,
                    "incentive_type": "charging_infrastructure_subsidy",
                    "drivetrain": Drivetrain.BEV,
                    "incentive_rate": 0.25,
                },
                {
                    "incentive_flag": 1,
                    "incentive_type": "purchase_rebate_aud",
                    "drivetrain": Drivetrain.BEV,
                    "incentive_rate": 40000,
                },
                {
                    "incentive_flag": 1,
                    "incentive_type": "stamp_duty_exemption",
                    "drivetrain": Drivetrain.BEV,
                    "incentive_rate": 1.0,
                },
            ]
        )

    @pytest.fixture
    def bev_calculation_request(
        self,
        bev_vehicle_data,
        bev_fees_data,
        calculation_parameters,
        charging_options,
        infrastructure_options,
        financial_params,
        battery_params,
        emission_factors,
        externalities_data,
        incentives,
    ):
        """Complete BEV calculation request for testing."""
        return CalculationRequest(
            vehicle_data=bev_vehicle_data,
            fees_data=bev_fees_data,
            parameters=calculation_parameters,
            charging_options=charging_options,
            infrastructure_options=infrastructure_options,
            financial_params=financial_params,
            battery_params=battery_params,
            emission_factors=emission_factors,
            externalities_data=externalities_data,
            incentives=incentives,
        )

    @pytest.fixture
    def diesel_calculation_request(
        self,
        diesel_vehicle_data,
        diesel_fees_data,
        calculation_parameters,
        charging_options,
        infrastructure_options,
        financial_params,
        battery_params,
        emission_factors,
        externalities_data,
        incentives,
    ):
        """Complete diesel calculation request for testing."""
        return CalculationRequest(
            vehicle_data=diesel_vehicle_data,
            fees_data=diesel_fees_data,
            parameters=calculation_parameters,
            charging_options=charging_options,
            infrastructure_options=infrastructure_options,
            financial_params=financial_params,
            battery_params=battery_params,
            emission_factors=emission_factors,
            externalities_data=externalities_data,
            incentives=incentives,
        )

    def test_complete_tco_calculation_integration(
        self, tco_service, bev_calculation_request
    ):
        """Test the complete TCO calculation process for a single vehicle."""
        # Execute the calculation
        result = tco_service.calculate_single_vehicle_tco(bev_calculation_request)

        # Validate result structure and basic properties
        assert result is not None
        assert hasattr(result, "tco_total_lifetime")
        assert hasattr(result, "tco_per_km")
        assert hasattr(result, "acquisition_cost")
        assert hasattr(result, "annual_operating_cost")
        assert hasattr(result, "lifetime_emissions_co2e")

        # Validate reasonable values
        assert result.tco_total_lifetime > 0
        assert result.tco_per_km > 0
        assert result.acquisition_cost > 0
        assert result.annual_operating_cost >= 0
        assert result.lifetime_emissions_co2e >= 0

        # BEV-specific validations
        assert result.npv_battery_replacement_cost >= 0
        assert result.npv_infrastructure_cost >= 0
        assert result.charging_requirements is not None
        assert result.infrastructure_costs_breakdown is not None

        # Validate social TCO includes externalities
        assert result.social_tco_total_lifetime > result.tco_total_lifetime

        # Validate emission metrics are reasonable
        assert result.co2e_per_km >= 0
        assert result.annual_emissions_co2e >= 0

    def test_tco_comparison_integration(
        self, tco_service, bev_calculation_request, diesel_calculation_request
    ):
        """Test TCO comparison between BEV and diesel vehicles."""
        # Calculate TCO for both vehicles
        bev_result = tco_service.calculate_single_vehicle_tco(bev_calculation_request)
        diesel_result = tco_service.calculate_single_vehicle_tco(
            diesel_calculation_request
        )

        # Execute comparison
        comparison = tco_service.compare_vehicles(
            bev_calculation_request, diesel_calculation_request
        )

        # Validate comparison structure
        assert comparison is not None
        assert hasattr(comparison, "base_vehicle_result")
        assert hasattr(comparison, "comparison_vehicle_result")
        assert hasattr(comparison, "tco_savings_lifetime")
        assert hasattr(comparison, "upfront_cost_difference")
        assert hasattr(comparison, "annual_operating_cost_savings")
        assert hasattr(comparison, "emissions_reduction_lifetime_co2e")

        # Validate logical relationships
        assert comparison.base_vehicle_result.vehicle_id == bev_result.vehicle_id
        assert (
            comparison.comparison_vehicle_result.vehicle_id == diesel_result.vehicle_id
        )

        # BEV should have higher acquisition cost in this scenario
        assert bev_result.acquisition_cost > diesel_result.acquisition_cost
        assert comparison.upfront_cost_difference is not None

        # BEV should have lower lifetime emissions
        assert (
            bev_result.lifetime_emissions_co2e < diesel_result.lifetime_emissions_co2e
        )
        assert comparison.emissions_reduction_lifetime_co2e > 0

        # Both should have positive TCO values
        assert bev_result.tco_total_lifetime > 0
        assert diesel_result.tco_total_lifetime > 0

        # Both should have reasonable cost per km (under $10/km for trucks)
        assert 0 < bev_result.tco_per_km < 10
        assert 0 < diesel_result.tco_per_km < 10

        # Validate social TCO values
        assert bev_result.social_tco_total_lifetime > bev_result.tco_total_lifetime
        assert (
            diesel_result.social_tco_total_lifetime > diesel_result.tco_total_lifetime
        )

    def test_calculation_with_incentives_toggle(
        self, tco_service, bev_calculation_request
    ):
        """Test that incentives can be toggled on/off and affect results."""
        # Calculate with incentives enabled (default)
        request_with_incentives = bev_calculation_request
        request_with_incentives.parameters.apply_incentives = True
        result_with_incentives = tco_service.calculate_single_vehicle_tco(
            request_with_incentives
        )

        # Calculate with incentives disabled
        request_without_incentives = bev_calculation_request
        request_without_incentives.parameters.apply_incentives = False
        result_without_incentives = tco_service.calculate_single_vehicle_tco(
            request_without_incentives
        )

        # With incentives should result in lower acquisition cost
        assert (
            result_with_incentives.acquisition_cost
            < result_without_incentives.acquisition_cost
        )

        # Infrastructure costs should also be affected by incentives
        assert (
            result_with_incentives.npv_infrastructure_cost
            < result_without_incentives.npv_infrastructure_cost
        )

        # Overall TCO should be lower with incentives
        assert (
            result_with_incentives.tco_total_lifetime
            < result_without_incentives.tco_total_lifetime
        )

    def test_error_handling_with_invalid_vehicle_data(
        self, tco_service, bev_calculation_request
    ):
        """Test error handling with invalid vehicle data."""
        # Create invalid request with missing required fields
        invalid_request = bev_calculation_request
        invalid_request.vehicle_data = pd.Series(
            {
                DataColumns.VEHICLE_ID: "INVALID",
                # Missing required fields like MSRP_PRICE, KWH_PER100KM, etc.
            }
        )

        # Should handle errors gracefully
        with pytest.raises(Exception):  # Expect some form of validation error
            tco_service.calculate_single_vehicle_tco(invalid_request)
