"""Unit tests for externalities domain module."""

import pytest
import pandas as pd
import numpy as np

from tco_app.domain.externalities import (
    calculate_externalities,
    calculate_social_tco,
    prepare_externality_comparison,
    calculate_social_benefit_metrics,
)
from tco_app.tests.fixtures.vehicles import (
    articulated_bev_vehicle,
    articulated_diesel_vehicle,
    standard_fees,
    standard_externalities,
    standard_financial_params,
)
from tco_app.src.constants import DataColumns, Drivetrain


class TestExternalitiesCalculations:
    """Test externalities calculations."""

    def test_calculate_externalities_comparison(
        self,
        articulated_bev_vehicle,
        articulated_diesel_vehicle,
        standard_externalities,
    ):
        """Test externalities calculation comparison between BEV and diesel."""
        bev_ext = calculate_externalities(
            articulated_bev_vehicle, standard_externalities, 100_000, 10, 0.07
        )
        diesel_ext = calculate_externalities(
            articulated_diesel_vehicle, standard_externalities, 100_000, 10, 0.07
        )

        assert bev_ext["externality_per_km"] < diesel_ext["externality_per_km"]

    def test_calculate_social_tco(
        self, articulated_bev_vehicle, standard_externalities
    ):
        """Test social TCO calculation."""
        bev_ext = calculate_externalities(
            articulated_bev_vehicle, standard_externalities, 100_000, 10, 0.07
        )
        bev_social = calculate_social_tco(
            {
                "npv_total_cost": 1_000_000,
                "annual_kms": 100_000,
                "truck_life_years": 10,
                "payload_t": 42,
            },
            bev_ext,
        )

        assert bev_social["social_tco_lifetime"] > 1_000_000  # Adds externality


class TestExternalityComparison:
    """Test externality comparison functionality."""

    def test_externality_comparison_and_social_benefit(
        self,
        articulated_bev_vehicle,
        articulated_diesel_vehicle,
        standard_externalities,
        standard_financial_params,
    ):
        """Test externality comparison and social benefit metrics."""
        bev_ext = calculate_externalities(
            articulated_bev_vehicle, standard_externalities, 50_000, 5, 0.05
        )
        diesel_ext = calculate_externalities(
            articulated_diesel_vehicle, standard_externalities, 50_000, 5, 0.05
        )
        comparison = prepare_externality_comparison(bev_ext, diesel_ext)
        assert comparison["total_savings"] > 0

        bev_results = {
            "acquisition_cost": 400_000,
            "annual_costs": {"annual_operating_cost": 40_000},
            "externalities": bev_ext,
        }
        diesel_results = {
            "acquisition_cost": 320_000,
            "annual_costs": {"annual_operating_cost": 60_000},
            "externalities": diesel_ext,
        }

        metrics = calculate_social_benefit_metrics(
            bev_results, diesel_results, 50_000, 5, 0.05
        )
        assert metrics["social_benefit_cost_ratio"] > 0


class TestDetailedExternalities:
    """Comprehensive tests for externality calculations."""

    @pytest.fixture
    def externality_params(self):
        """Create comprehensive externality parameters."""
        return pd.Series(
            {
                DataColumns.CONGESTION_COST: 0.05,  # per km
                DataColumns.NOISE_COST: 0.02,  # per km
                DataColumns.POLLUTION_COST: 0.03,  # per km
                DataColumns.ACCIDENT_COST: 0.01,  # per km
                DataColumns.INFRASTRUCTURE_WEAR_COST: 0.02,  # per km
            }
        )

    def test_bev_lower_externalities(self, externality_params):
        """Test that BEVs have lower externalities than diesel."""
        bev_vehicle = pd.Series(
            {
                DataColumns.VEHICLE_DRIVETRAIN: Drivetrain.BEV,
                DataColumns.VEHICLE_WEIGHT: 25000,  # kg
                DataColumns.NOISE_REDUCTION_FACTOR: 0.7,  # 30% quieter
            }
        )

        diesel_vehicle = pd.Series(
            {
                DataColumns.VEHICLE_DRIVETRAIN: Drivetrain.DIESEL,
                DataColumns.VEHICLE_WEIGHT: 20000,  # kg
            }
        )

        bev_ext = calculate_externalities(
            bev_vehicle, externality_params, 100000, 10, 0.05
        )

        diesel_ext = calculate_externalities(
            diesel_vehicle, externality_params, 100000, 10, 0.05
        )

        # BEV should have lower total externalities
        assert bev_ext["externality_per_km"] < diesel_ext["externality_per_km"]

        # BEV should have lower noise costs specifically
        assert bev_ext["noise_cost_per_km"] < diesel_ext["noise_cost_per_km"]

        # BEV should have zero local pollution
        assert bev_ext.get("local_pollution_cost_per_km", 0) == 0

    def test_phev_externalities(self, externality_params):
        """Test PHEV externalities (between BEV and diesel)."""
        phev_vehicle = pd.Series(
            {
                DataColumns.VEHICLE_DRIVETRAIN: Drivetrain.PHEV,
                DataColumns.VEHICLE_WEIGHT: 22000,
                DataColumns.ELECTRIC_RANGE: 80,  # km
                DataColumns.DAILY_DISTANCE: 120,  # km
            }
        )

        phev_ext = calculate_externalities(
            phev_vehicle, externality_params, 100000, 10, 0.05
        )

        # PHEV should have some pollution (when using diesel)
        assert phev_ext["externality_per_km"] > 0

        # Electric portion should reduce overall externalities
        electric_fraction = min(80 / 120, 1.0)  # About 67% electric
        assert phev_ext.get("electric_driving_fraction", 0) > 0.5

    def test_weight_based_infrastructure_wear(self, externality_params):
        """Test that heavier vehicles cause more infrastructure wear."""
        light_vehicle = pd.Series(
            {
                DataColumns.VEHICLE_DRIVETRAIN: Drivetrain.BEV,
                DataColumns.VEHICLE_WEIGHT: 18000,  # Light truck
            }
        )

        heavy_vehicle = pd.Series(
            {
                DataColumns.VEHICLE_DRIVETRAIN: Drivetrain.BEV,
                DataColumns.VEHICLE_WEIGHT: 40000,  # Heavy truck
            }
        )

        light_ext = calculate_externalities(
            light_vehicle, externality_params, 100000, 10, 0.05
        )

        heavy_ext = calculate_externalities(
            heavy_vehicle, externality_params, 100000, 10, 0.05
        )

        # Heavier vehicle should have higher infrastructure wear cost
        assert heavy_ext.get("infrastructure_wear_per_km", 0) > light_ext.get(
            "infrastructure_wear_per_km", 0
        )

    def test_total_externality_cost_calculation(self, externality_params):
        """Test total externality cost over vehicle lifetime."""
        vehicle = pd.Series(
            {
                DataColumns.VEHICLE_DRIVETRAIN: Drivetrain.DIESEL,
                DataColumns.VEHICLE_WEIGHT: 25000,
            }
        )

        annual_kms = 80000
        truck_life_years = 8
        discount_rate = 0.05

        externalities = calculate_externalities(
            vehicle, externality_params, annual_kms, truck_life_years, discount_rate
        )

        total_cost = calculate_total_externality_cost(
            externalities, annual_kms, truck_life_years, discount_rate
        )

        # Total cost should include all components
        assert "annual_externality_cost" in total_cost
        assert "lifetime_externality_cost" in total_cost
        assert "npv_externality_cost" in total_cost

        # Annual cost calculation
        expected_annual = externalities["externality_per_km"] * annual_kms
        assert abs(total_cost["annual_externality_cost"] - expected_annual) < 0.01

        # Lifetime cost (undiscounted)
        expected_lifetime = expected_annual * truck_life_years
        assert abs(total_cost["lifetime_externality_cost"] - expected_lifetime) < 1.0

        # NPV should be less than lifetime due to discounting
        assert (
            total_cost["npv_externality_cost"] < total_cost["lifetime_externality_cost"]
        )

    def test_social_tco_integration(self, externality_params):
        """Test integration of externalities into social TCO."""
        vehicle = pd.Series(
            {
                DataColumns.VEHICLE_DRIVETRAIN: Drivetrain.BEV,
                DataColumns.VEHICLE_WEIGHT: 24000,
            }
        )

        externalities = calculate_externalities(
            vehicle, externality_params, 100000, 10, 0.05
        )

        total_ext = calculate_total_externality_cost(externalities, 100000, 10, 0.05)

        # Mock TCO results
        tco_results = {
            "npv_total_cost": 800000,
            "cost_per_km": 0.80,
            "annual_kms": 100000,
            "truck_life_years": 10,
            "payload_t": 25,
        }

        social_tco = calculate_social_tco(tco_results, total_ext)

        # Social TCO should add externalities to private TCO
        assert social_tco["social_tco_lifetime"] > tco_results["npv_total_cost"]
        assert social_tco["social_tco_lifetime"] == (
            tco_results["npv_total_cost"] + total_ext["npv_externality_cost"]
        )

        # Cost per km should also increase
        assert social_tco["social_cost_per_km"] > tco_results["cost_per_km"]

        # Cost per ton-km calculation
        assert social_tco["social_cost_per_t_km"] == (
            social_tco["social_cost_per_km"] / tco_results["payload_t"]
        )

    def test_externality_comparison(self, externality_params):
        """Test comparison of externalities between vehicles."""
        bev_ext = {
            "externality_per_km": 0.08,
            "congestion_cost_per_km": 0.05,
            "noise_cost_per_km": 0.014,  # 30% reduction
            "pollution_cost_per_km": 0.0,
            "npv_externality_cost": 50000,
        }

        diesel_ext = {
            "externality_per_km": 0.13,
            "congestion_cost_per_km": 0.05,
            "noise_cost_per_km": 0.02,
            "pollution_cost_per_km": 0.03,
            "npv_externality_cost": 80000,
        }

        comparison = prepare_externality_comparison(bev_ext, diesel_ext)

        # BEV should have savings
        assert comparison["total_savings"] == 0.05  # per km
        assert comparison["noise_savings"] == 0.006
        assert comparison["pollution_savings"] == 0.03
        assert comparison["congestion_savings"] == 0.0  # Same for both
        assert comparison["lifetime_savings"] == 30000  # NPV difference

    def test_social_benefit_metrics(self):
        """Test calculation of social benefit metrics."""
        bev_results = {
            "acquisition_cost": 400000,
            "annual_costs": {"annual_operating_cost": 40000},
            "externalities": {"npv_externality_cost": 50000},
            "tco": {"npv_total_cost": 700000},
        }

        diesel_results = {
            "acquisition_cost": 300000,
            "annual_costs": {"annual_operating_cost": 55000},
            "externalities": {"npv_externality_cost": 80000},
            "tco": {"npv_total_cost": 750000},
        }

        metrics = calculate_social_benefit_metrics(
            bev_results, diesel_results, 100000, 10, 0.05
        )

        # Social benefit = externality savings
        assert metrics["social_benefit"] == 30000  # 80000 - 50000

        # Private cost difference
        assert metrics["private_cost_difference"] == -50000  # 700000 - 750000

        # Social benefit cost ratio
        # Ratio = social benefit / private cost increase
        # But here BEV has lower private cost too, so ratio should be very high
        assert metrics["social_benefit_cost_ratio"] > 1.0

        # Net social value = social benefit + private savings
        assert metrics["net_social_value"] == 80000  # 30000 + 50000

    def test_zero_externality_parameters(self):
        """Test handling of zero externality costs."""
        zero_params = pd.Series(
            {
                DataColumns.CONGESTION_COST: 0.0,
                DataColumns.NOISE_COST: 0.0,
                DataColumns.POLLUTION_COST: 0.0,
            }
        )

        vehicle = pd.Series(
            {
                DataColumns.VEHICLE_DRIVETRAIN: Drivetrain.DIESEL,
                DataColumns.VEHICLE_WEIGHT: 25000,
            }
        )

        externalities = calculate_externalities(vehicle, zero_params, 100000, 10, 0.05)

        assert externalities["externality_per_km"] == 0.0
        assert externalities.get("npv_externality_cost", 0) == 0.0

    def test_negative_discount_rate(self, externality_params):
        """Test handling of negative discount rates (unusual but possible)."""
        vehicle = pd.Series(
            {
                DataColumns.VEHICLE_DRIVETRAIN: Drivetrain.BEV,
                DataColumns.VEHICLE_WEIGHT: 25000,
            }
        )

        # Negative discount rate means future costs are worth more
        externalities = calculate_externalities(
            vehicle, externality_params, 100000, 10, -0.02
        )

        total_cost = calculate_total_externality_cost(externalities, 100000, 10, -0.02)

        # NPV should be higher than undiscounted lifetime cost
        assert (
            total_cost["npv_externality_cost"] > total_cost["lifetime_externality_cost"]
        )

    def test_very_long_vehicle_life(self, externality_params):
        """Test calculations with very long vehicle lifetime."""
        vehicle = pd.Series(
            {
                DataColumns.VEHICLE_DRIVETRAIN: Drivetrain.BEV,
                DataColumns.VEHICLE_WEIGHT: 25000,
            }
        )

        # 25-year vehicle life
        externalities = calculate_externalities(
            vehicle, externality_params, 100000, 25, 0.05
        )

        total_cost = calculate_total_externality_cost(externalities, 100000, 25, 0.05)

        # Should handle long timeframes correctly
        assert total_cost["lifetime_externality_cost"] > 0
        assert total_cost["npv_externality_cost"] > 0

        # Discounting effect should be stronger with longer timeframe
        discount_factor = (
            total_cost["npv_externality_cost"] / total_cost["lifetime_externality_cost"]
        )
        assert discount_factor < 0.7  # Significant discounting over 25 years
