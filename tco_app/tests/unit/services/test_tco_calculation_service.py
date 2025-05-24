"""Comprehensive unit tests for TCO Calculation Service."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import numpy as np
from datetime import datetime

from tco_app.services.tco_calculation_service import TCOCalculationService
from tco_app.services.dtos import (
    CalculationRequest,
    CalculationParameters,
    TCOResult,
    ComparisonResult,
)
from tco_app.repositories import VehicleRepository, ParametersRepository
from tco_app.src.constants import DataColumns, Drivetrain, ParameterKeys
from tco_app.src.exceptions import CalculationError


class TestTCOCalculationService:
    """Test suite for TCO Calculation Service."""

    @pytest.fixture
    def mock_vehicle_repo(self):
        """Create a mock vehicle repository."""
        return Mock(spec=VehicleRepository)

    @pytest.fixture
    def mock_params_repo(self):
        """Create a mock parameters repository."""
        return Mock(spec=ParametersRepository)

    @pytest.fixture
    def service(self, mock_vehicle_repo, mock_params_repo):
        """Create TCO calculation service instance."""
        return TCOCalculationService(mock_vehicle_repo, mock_params_repo)

    @pytest.fixture
    def bev_vehicle_data(self):
        """Sample BEV vehicle data."""
        return pd.Series(
            {
                DataColumns.VEHICLE_ID: 1,
                DataColumns.VEHICLE_NAME: "Test BEV Truck",
                DataColumns.VEHICLE_DRIVETRAIN: Drivetrain.BEV,
                DataColumns.KWH_PER100KM: 125.0,
                DataColumns.VEHICLE_PRICE: 350000,
                DataColumns.PAYLOAD_TONNES: 20,
                DataColumns.VEHICLE_BATTERY_CAPACITY_KWH: 300,
                DataColumns.MAX_ANNUAL_DISTANCE_KM: 150000,
            }
        )

    @pytest.fixture
    def diesel_vehicle_data(self):
        """Sample diesel vehicle data."""
        return pd.Series(
            {
                DataColumns.VEHICLE_ID: 2,
                DataColumns.VEHICLE_NAME: "Test Diesel Truck",
                DataColumns.VEHICLE_DRIVETRAIN: Drivetrain.DIESEL,
                DataColumns.LITRES_PER100KM: 35.0,
                DataColumns.VEHICLE_PRICE: 150000,
                DataColumns.PAYLOAD_TONNES: 20,
                DataColumns.VEHICLE_BATTERY_CAPACITY_KWH: 0,
                DataColumns.MAX_ANNUAL_DISTANCE_KM: 200000,
            }
        )

    @pytest.fixture
    def financial_params(self):
        """Sample financial parameters."""
        return pd.DataFrame(
            {
                ParameterKeys.PARAMETER_KEY: [
                    ParameterKeys.DISCOUNT_RATE,
                    ParameterKeys.DIESEL_PRICE,
                    ParameterKeys.CARBON_PRICE,
                    ParameterKeys.ROAD_USER_CHARGE,
                    ParameterKeys.ANNUAL_INSURANCE_COST,
                    ParameterKeys.ANNUAL_TYRE_COST,
                    ParameterKeys.ANNUAL_MAINTENANCE_COST,
                    ParameterKeys.ANNUAL_REGISTRATION_COST,
                ],
                "value": [0.05, 1.50, 50.0, 15000, 5000, 3000, 8000, 2000],
            }
        )

    @pytest.fixture
    def battery_params(self):
        """Sample battery parameters."""
        return pd.DataFrame(
            {
                ParameterKeys.PARAMETER_KEY: [
                    ParameterKeys.BATTERY_PRICE_PER_KWH,
                    ParameterKeys.BATTERY_ANNUAL_DECAY_RATE,
                    ParameterKeys.BATTERY_MIN_SOH,
                ],
                "value": [500, 0.025, 0.8],
            }
        )

    @pytest.fixture
    def charging_data(self):
        """Sample charging options data."""
        return pd.DataFrame(
            {
                DataColumns.CHARGING_ID: [1, 2, 3],
                DataColumns.CHARGING_NAME: [
                    "Depot Slow",
                    "Depot Fast",
                    "Public Ultra-Fast",
                ],
                DataColumns.PER_KWH_PRICE: [0.20, 0.25, 0.35],
            }
        )

    @pytest.fixture
    def bev_calculation_request(
        self, bev_vehicle_data, financial_params, battery_params, charging_data
    ):
        """Create a BEV calculation request."""
        parameters = CalculationParameters(
            annual_kms=100000,
            truck_life_years=10,
            discount_rate=0.05,
            diesel_price=1.50,
            carbon_price=50.0,
        )

        return CalculationRequest(
            vehicle_data=bev_vehicle_data,
            fees_data=pd.DataFrame(),
            financial_params=financial_params,
            battery_params=battery_params,
            emission_factors=pd.DataFrame(
                {
                    "fuel_type": ["electricity", "diesel"],
                    "emission_standard": ["Grid Average", "Euro VI"],
                    "co2_per_unit": [0.5, 2.68],
                }
            ),
            charging_options=charging_data,
            infrastructure_options=pd.DataFrame(
                {
                    DataColumns.INFRASTRUCTURE_ID: [1],
                    DataColumns.INFRASTRUCTURE_DESCRIPTION: ["Depot Charger 150kW"],
                    DataColumns.INFRASTRUCTURE_PRICE: [50000],
                    DataColumns.ANNUAL_MAINTENANCE_COST: [2000],
                    DataColumns.SERVICE_LIFE_YEARS: [15],
                }
            ),
            parameters=parameters,
            selected_charging_id=1,
            selected_infrastructure_id=1,
            charging_mix={1: 0.8, 2: 0.2},
            fleet_size=10,
        )

    @pytest.fixture
    def diesel_calculation_request(
        self, diesel_vehicle_data, financial_params, battery_params
    ):
        """Create a diesel calculation request."""
        parameters = CalculationParameters(
            annual_kms=100000,
            truck_life_years=10,
            discount_rate=0.05,
            diesel_price=1.50,
            carbon_price=50.0,
        )

        return CalculationRequest(
            vehicle_data=diesel_vehicle_data,
            fees_data=pd.DataFrame(),
            financial_params=financial_params,
            battery_params=battery_params,
            emission_factors=pd.DataFrame(
                {
                    "fuel_type": ["electricity", "diesel"],
                    "emission_standard": ["Grid Average", "Euro VI"],
                    "co2_per_unit": [0.5, 2.68],
                }
            ),
            charging_options=pd.DataFrame(),
            infrastructure_options=pd.DataFrame(),
            parameters=parameters,
            selected_charging_id=None,
            selected_infrastructure_id=None,
            charging_mix=None,
            fleet_size=1,
        )

    def test_service_initialization(self, service, mock_vehicle_repo, mock_params_repo):
        """Test service is initialized correctly."""
        assert service.vehicle_repo == mock_vehicle_repo
        assert service.params_repo == mock_params_repo

    @patch("tco_app.services.tco_calculation_service.energy")
    @patch("tco_app.services.tco_calculation_service.finance")
    @patch("tco_app.services.tco_calculation_service.externalities")
    def test_calculate_single_vehicle_tco_bev(
        self,
        mock_externalities,
        mock_finance,
        mock_energy,
        service,
        bev_calculation_request,
    ):
        """Test TCO calculation for a BEV vehicle."""
        # Mock energy calculations
        mock_energy.calculate_energy_costs.return_value = 0.25  # $/km
        mock_energy.calculate_emissions.return_value = {
            "co2_per_km": 0.625,
            "annual_emissions": 62500,
            "lifetime_emissions": 625000,
        }
        mock_energy.calculate_charging_requirements.return_value = {
            "daily_distance": 273.97,
            "daily_kwh_required": 342.47,
            "charger_power": 150,
            "charging_time_per_day": 2.28,
            "max_vehicles_per_charger": 10.5,
        }

        # Mock finance calculations
        mock_finance.calculate_annual_operating_cost.return_value = 58000
        mock_finance.calculate_acquisition_cost.return_value = 380000
        mock_finance.calculate_residual_value.return_value = 70000
        mock_finance.calculate_npv.return_value = 750000

        # Mock externalities
        mock_externalities.calculate_externality_costs.return_value = {
            "annual_externality_cost": 3125,
            "lifetime_externality_cost": 31250,
            "externality_cost_per_km": 0.03125,
            "externality_npv": 24123,
        }

        # Call the service
        result = service.calculate_single_vehicle_tco(bev_calculation_request)

        # Verify result structure
        assert isinstance(result, TCOResult)
        assert result.vehicle_id == 1
        assert result.vehicle_name == "Test BEV Truck"
        assert result.drivetrain == Drivetrain.BEV

        # Verify calculations were called correctly
        mock_energy.calculate_energy_costs.assert_called_once()
        mock_energy.calculate_emissions.assert_called_once()
        mock_finance.calculate_annual_operating_cost.assert_called_once()
        mock_finance.calculate_acquisition_cost.assert_called_once()

        # Verify TCO metrics
        assert result.tco_per_km > 0
        assert result.tco_per_tonne_km > 0
        assert result.tco_total_lifetime > 0
        assert result.npv_total_cost > 0

    def test_calculate_single_vehicle_tco_error_handling(
        self, service, bev_calculation_request
    ):
        """Test error handling in TCO calculation."""
        # Mock an error in energy calculation
        with patch(
            "tco_app.services.tco_calculation_service.energy.calculate_energy_costs"
        ) as mock_energy:
            mock_energy.side_effect = Exception("Energy calculation failed")

            with pytest.raises(CalculationError) as exc_info:
                service.calculate_single_vehicle_tco(bev_calculation_request)

            assert "TCO calculation failed" in str(exc_info.value)

    @patch("tco_app.services.tco_calculation_service.calculate_battery_replacement")
    def test_battery_cost_calculation_bev(
        self, mock_battery_calc, service, bev_calculation_request
    ):
        """Test battery cost calculation for BEV."""
        mock_battery_calc.return_value = {
            "battery_replacement_year": 8,
            "battery_replacement_cost": 150000,
            "battery_replacement_needed": True,
        }

        battery_costs = service._calculate_battery_costs(bev_calculation_request)

        assert battery_costs["battery_replacement_needed"] is True
        assert battery_costs["battery_replacement_year"] == 8
        assert battery_costs["battery_replacement_cost"] == 150000

    def test_battery_cost_calculation_diesel(self, service, diesel_calculation_request):
        """Test battery cost calculation for diesel (should return empty)."""
        battery_costs = service._calculate_battery_costs(diesel_calculation_request)

        assert battery_costs["battery_replacement_needed"] is False
        assert battery_costs["battery_replacement_year"] is None
        assert battery_costs["battery_replacement_cost"] == 0

    def test_infrastructure_cost_calculation_bev(
        self, service, bev_calculation_request
    ):
        """Test infrastructure cost calculation for BEV."""
        infra_costs = service._calculate_infrastructure_costs(bev_calculation_request)

        # Verify infrastructure costs are calculated
        assert "infrastructure_price" in infra_costs
        assert infra_costs["infrastructure_price"] == 50000
        assert infra_costs["annual_maintenance"] == 2000
        assert infra_costs["service_life_years"] == 15
        assert infra_costs["fleet_size"] == 10

        # Verify charging requirements
        assert "daily_distance" in infra_costs
        assert infra_costs["daily_distance"] > 0
        assert "daily_kwh_required" in infra_costs

    def test_infrastructure_cost_calculation_diesel(
        self, service, diesel_calculation_request
    ):
        """Test infrastructure cost calculation for diesel (should return empty)."""
        infra_costs = service._calculate_infrastructure_costs(
            diesel_calculation_request
        )

        assert infra_costs == {}

    @patch(
        "tco_app.services.tco_calculation_service.sensitivity_metrics.calculate_comparative_metrics"
    )
    def test_compare_vehicles(
        self,
        mock_comparative_metrics,
        service,
        bev_calculation_request,
        diesel_calculation_request,
    ):
        """Test vehicle comparison functionality."""
        # Mock TCO results
        bev_result = TCOResult(
            vehicle_id=1,
            vehicle_name="Test BEV",
            drivetrain=Drivetrain.BEV,
            tco_total_lifetime=800000,
            tco_per_km=0.80,
            tco_per_tonne_km=0.04,
            npv_total_cost=750000,
            acquisition_cost=380000,
            residual_value=70000,
            annual_operating_cost=58000,
            annual_energy_cost=25000,
            energy_cost_per_km=0.25,
            annual_maintenance_cost=8000,
            annual_insurance_cost=5000,
            annual_tyre_cost=3000,
            annual_registration_cost=2000,
            annual_ruc_cost=15000,
            battery_replacement_year=8,
            battery_replacement_cost=150000,
            co2_per_km=0.625,
            annual_emissions=62500,
            lifetime_emissions=625000,
            annual_externality_cost=3125,
            lifetime_externality_cost=31250,
            externality_npv=24123,
            charging_requirements={"daily_kwh_required": 342.47},
            infrastructure_costs={"infrastructure_price": 50000},
            weighted_electricity_price=0.22,
            annual_carbon_cost=3125,
        )

        diesel_result = TCOResult(
            vehicle_id=2,
            vehicle_name="Test Diesel",
            drivetrain=Drivetrain.DIESEL,
            tco_total_lifetime=900000,
            tco_per_km=0.90,
            tco_per_tonne_km=0.045,
            npv_total_cost=850000,
            acquisition_cost=150000,
            residual_value=30000,
            annual_operating_cost=75000,
            annual_energy_cost=52500,
            energy_cost_per_km=0.525,
            annual_maintenance_cost=10000,
            annual_insurance_cost=5000,
            annual_tyre_cost=3000,
            annual_registration_cost=2000,
            annual_ruc_cost=2500,
            battery_replacement_year=None,
            battery_replacement_cost=0,
            co2_per_km=0.938,
            annual_emissions=93800,
            lifetime_emissions=938000,
            annual_externality_cost=4690,
            lifetime_externality_cost=46900,
            externality_npv=36234,
            charging_requirements={},
            infrastructure_costs={},
            weighted_electricity_price=None,
            annual_carbon_cost=4690,
        )

        # Mock comparative metrics
        mock_comparative_metrics.return_value = {
            "upfront_cost_difference": 230000,
            "annual_operating_savings": 17000,
            "price_parity_year": 13.5,
            "emission_savings_lifetime": 313000,
            "abatement_cost": -318.85,
            "bev_to_diesel_tco_ratio": 0.88,
        }

        # Patch the individual TCO calculations
        with patch.object(service, "calculate_single_vehicle_tco") as mock_calc:
            mock_calc.side_effect = [bev_result, diesel_result]

            comparison = service.compare_vehicles(
                bev_calculation_request, diesel_calculation_request
            )

        # Verify comparison results
        assert isinstance(comparison, ComparisonResult)
        assert comparison.base_vehicle_result == bev_result
        assert comparison.comparison_vehicle_result == diesel_result
        assert comparison.tco_savings_lifetime == 100000  # 900000 - 800000
        assert comparison.annual_operating_cost_savings == 17000
        assert comparison.emissions_reduction_lifetime_co2e == 313000
        assert comparison.payback_period_years == 13.5
        assert comparison.upfront_cost_difference == 230000
        assert comparison.abatement_cost == -318.85
        assert comparison.bev_to_diesel_tco_ratio == 0.88

    def test_tco_metrics_calculation(self, service, bev_calculation_request):
        """Test TCO per-km and per-tonne-km metrics calculation."""
        tco_total = 800000
        metrics = service._calculate_tco_metrics(tco_total, bev_calculation_request)

        expected_per_km = tco_total / (100000 * 10)  # annual_kms * truck_life_years
        expected_per_tonne_km = expected_per_km / 20  # payload_tonnes

        assert metrics["tco_per_km"] == pytest.approx(expected_per_km)
        assert metrics["tco_per_tonne_km"] == pytest.approx(expected_per_tonne_km)

    def test_annual_costs_calculation(self, service, bev_calculation_request):
        """Test annual costs aggregation."""
        energy_costs = {
            "energy_cost_per_km": 0.25,
            "annual_emissions": 62500,
        }

        with patch(
            "tco_app.services.tco_calculation_service.finance.calculate_annual_operating_cost"
        ) as mock_annual:
            mock_annual.return_value = 58000

            annual_costs = service._calculate_annual_costs(
                bev_calculation_request, energy_costs
            )

            assert "annual_operating_cost" in annual_costs
            assert annual_costs["annual_operating_cost"] == 58000
            assert "annual_energy_cost" in annual_costs
            assert annual_costs["annual_energy_cost"] == 25000  # 0.25 * 100000
