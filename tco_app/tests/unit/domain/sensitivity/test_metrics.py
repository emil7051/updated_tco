"""Unit tests for sensitivity metrics calculations."""

import math

import pytest

from tco_app.domain.sensitivity.metrics import (
    compute_price_parity,
    calculate_comparative_metrics_from_dto,
)
from tco_app.services.dtos import ComparisonResult, TCOResult


class TestCalculateComparativeMetricsFromDTO:
    """Test suite for DTO-based comparative metrics calculation."""

    @pytest.fixture
    def bev_tco_result(self):
        """Create a BEV TCOResult for testing."""
        return TCOResult(
            vehicle_id="BEV001",
            tco_per_km=0.75,
            tco_per_tonne_km=0.05,
            tco_total_lifetime=750000,
            annual_operating_cost=58000,
            npv_annual_operating_cost=500000,
            acquisition_cost=380000,
            residual_value=70000,
            npv_battery_replacement_cost=100000,
            energy_cost_per_km=0.25,
            lifetime_emissions_co2e=625000,
            annual_emissions_co2e=62500,
            co2e_per_km=0.625,
            npv_infrastructure_cost=5000,
            social_tco_total_lifetime=800000,
            annual_costs_breakdown={
                "annual_energy_cost": 25000,
                "annual_maintenance_cost": 8000,
                "registration_annual": 5000,
                "insurance_annual": 20000,
            },
            emissions_breakdown={
                "co2_per_km": 0.625,
                "annual_emissions": 62500,
                "lifetime_emissions": 625000,
            },
            infrastructure_costs_breakdown={
                "initial_capital": 50000,
                "infrastructure_price_with_incentives": 40000,
                "fleet_size": 10,
                "annual_maintenance": 2000,
                "service_life_years": 15,
                "npv_per_vehicle": 5000,
            },
            charging_requirements={
                "daily_kwh_required": 100,
                "charging_time_per_day": 2,
                "charger_power": 50,
                "max_vehicles_per_charger": 5,
            },
            weighted_electricity_price=0.15,
            externalities_breakdown={},
            scenario_meta={"name": "Default"},
        )

    @pytest.fixture
    def diesel_tco_result(self):
        """Create a diesel TCOResult for testing."""
        return TCOResult(
            vehicle_id="DSL001",
            tco_per_km=0.85,
            tco_per_tonne_km=0.057,
            tco_total_lifetime=850000,
            annual_operating_cost=75000,
            npv_annual_operating_cost=650000,
            acquisition_cost=150000,
            residual_value=30000,
            npv_battery_replacement_cost=0,
            energy_cost_per_km=0.525,
            lifetime_emissions_co2e=938000,
            annual_emissions_co2e=93800,
            co2e_per_km=0.938,
            npv_infrastructure_cost=0,
            social_tco_total_lifetime=950000,
            annual_costs_breakdown={
                "annual_energy_cost": 52500,
                "annual_maintenance_cost": 10000,
                "registration_annual": 5000,
                "insurance_annual": 7500,
            },
            emissions_breakdown={
                "co2_per_km": 0.938,
                "annual_emissions": 93800,
                "lifetime_emissions": 938000,
            },
            infrastructure_costs_breakdown=None,
            charging_requirements=None,
            weighted_electricity_price=None,
            externalities_breakdown={},
            scenario_meta={"name": "Default"},
        )

    @pytest.fixture
    def comparison_result(self, bev_tco_result, diesel_tco_result):
        """Create a ComparisonResult for testing."""
        return ComparisonResult(
            base_vehicle_result=bev_tco_result,
            comparison_vehicle_result=diesel_tco_result,
            tco_savings_lifetime=100000,  # diesel - bev
            annual_operating_cost_savings=17000,  # diesel - bev
            emissions_reduction_lifetime_co2e=313000,  # diesel - bev
            upfront_cost_difference=234000,  # bev - diesel including infra
            payback_period_years=None,  # To be calculated
            abatement_cost=None,  # To be calculated
            bev_to_diesel_tco_ratio=None,  # To be calculated
            annual_kms=100000,
            truck_life_years=10,
        )

    def test_basic_comparison_dto(self, comparison_result):
        """Test basic comparison using DTOs."""
        metrics = calculate_comparative_metrics_from_dto(comparison_result)

        # Test upfront cost difference (380k + 4k infra - 150k)
        assert metrics["upfront_cost_difference"] == 234000

        # Test annual operating savings (75k - 58k)
        assert metrics["annual_operating_savings"] == 17000

        # Test emission savings (938k - 625k)
        assert metrics["emission_savings_lifetime"] == 313000

        # Test BEV to diesel ratio (750k / 850k)
        expected_ratio = 750000 / 850000
        assert metrics["bev_to_diesel_tco_ratio"] == pytest.approx(
            expected_ratio, rel=1e-5
        )

        # Test abatement cost
        expected_abatement = (750000 - 850000) / (313000 / 1000)  # emissions in tonnes
        assert metrics["abatement_cost"] == pytest.approx(expected_abatement, rel=1e-2)

    def test_price_parity_calculation_dto(self):
        """Test price parity year calculation with DTOs."""
        # Create simplified results for easier calculation
        bev_result = TCOResult(
            vehicle_id="BEV001",
            tco_per_km=0.35,
            tco_per_tonne_km=0.023,
            tco_total_lifetime=350000,
            annual_operating_cost=20000,
            npv_annual_operating_cost=180000,
            acquisition_cost=200000,
            residual_value=40000,
            npv_battery_replacement_cost=0,
            energy_cost_per_km=0.2,
            lifetime_emissions_co2e=500000,
            annual_emissions_co2e=50000,
            co2e_per_km=0.5,
            npv_infrastructure_cost=0,
            social_tco_total_lifetime=400000,
            annual_costs_breakdown={},
            emissions_breakdown={},
            infrastructure_costs_breakdown=None,
            charging_requirements=None,
            weighted_electricity_price=0.15,
            externalities_breakdown={},
            scenario_meta={"name": "Default"},
        )

        diesel_result = TCOResult(
            vehicle_id="DSL001",
            tco_per_km=0.38,
            tco_per_tonne_km=0.025,
            tco_total_lifetime=380000,
            annual_operating_cost=30000,
            npv_annual_operating_cost=280000,
            acquisition_cost=100000,
            residual_value=20000,
            npv_battery_replacement_cost=0,
            energy_cost_per_km=0.3,
            lifetime_emissions_co2e=800000,
            annual_emissions_co2e=80000,
            co2e_per_km=0.8,
            npv_infrastructure_cost=0,
            social_tco_total_lifetime=450000,
            annual_costs_breakdown={},
            emissions_breakdown={},
            infrastructure_costs_breakdown=None,
            charging_requirements=None,
            weighted_electricity_price=None,
            externalities_breakdown={},
            scenario_meta={"name": "Default"},
        )

        comparison = ComparisonResult(
            base_vehicle_result=bev_result,
            comparison_vehicle_result=diesel_result,
            tco_savings_lifetime=30000,
            annual_operating_cost_savings=10000,
            emissions_reduction_lifetime_co2e=300000,
            upfront_cost_difference=100000,
            payback_period_years=None,
            abatement_cost=None,
            bev_to_diesel_tco_ratio=None,
            annual_kms=100000,
            truck_life_years=10,
        )

        metrics = calculate_comparative_metrics_from_dto(comparison)

        # With 100k upfront difference and 10k annual savings, parity should be at year 10
        # However, due to residual value adjustments, actual crossover is slightly earlier
        assert pytest.approx(metrics["price_parity_year"], rel=1e-3) == 9.666666666666666

    def test_zero_emission_savings_dto(self, bev_tco_result, diesel_tco_result):
        """Test handling of zero emission savings with DTOs."""
        # Make emissions equal
        diesel_tco_result.lifetime_emissions_co2e = 625000

        comparison = ComparisonResult(
            base_vehicle_result=bev_tco_result,
            comparison_vehicle_result=diesel_tco_result,
            tco_savings_lifetime=100000,
            annual_operating_cost_savings=17000,
            emissions_reduction_lifetime_co2e=0,  # No emission savings
            upfront_cost_difference=234000,
            payback_period_years=None,
            abatement_cost=None,
            bev_to_diesel_tco_ratio=None,
            annual_kms=100000,
            truck_life_years=10,
        )

        metrics = calculate_comparative_metrics_from_dto(comparison)

        # Abatement cost should be infinity when no emission savings
        assert metrics["abatement_cost"] == float("inf")
        assert metrics["emission_savings_lifetime"] == 0


class TestPriceParity:
    """Unit tests for price parity calculation helper."""

    def test_compute_price_parity_basic(self):
        """Test basic price parity calculation."""
        # BEV starts higher but becomes cheaper
        bev_cum = [200000, 220000, 240000, 260000, 280000]
        diesel_cum = [100000, 130000, 160000, 190000, 220000]
        years = [1, 2, 3, 4, 5]

        parity = compute_price_parity(bev_cum, diesel_cum, years)

        # BEV catches up between year 3 and 4
        assert 3 < parity < 4

    def test_compute_price_parity_no_crossing(self):
        """Test when lines never cross."""
        # BEV always more expensive
        bev_cum = [200000, 250000, 300000, 350000, 400000]
        diesel_cum = [100000, 130000, 160000, 190000, 220000]
        years = [1, 2, 3, 4, 5]

        parity = compute_price_parity(bev_cum, diesel_cum, years)

        assert parity == math.inf

    def test_compute_price_parity_immediate(self):
        """Test when BEV is cheaper from the start."""
        # BEV starts cheaper
        bev_cum = [100000, 120000, 140000, 160000, 180000]
        diesel_cum = [150000, 180000, 210000, 240000, 270000]
        years = [1, 2, 3, 4, 5]

        parity = compute_price_parity(bev_cum, diesel_cum, years)

        # Should return infinity as BEV is always cheaper
        assert parity == math.inf
