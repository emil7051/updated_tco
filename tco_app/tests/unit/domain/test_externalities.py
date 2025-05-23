"""Unit tests for externalities domain module."""
import pytest
from tco_app.domain.externalities import (
    calculate_externalities,
    calculate_social_tco,
    prepare_externality_comparison,
    calculate_social_benefit_metrics,
)
from tco_app.tests.fixtures.vehicles import *


class TestExternalitiesCalculations:
    """Test externalities calculations."""
    
    def test_calculate_externalities_comparison(
        self, articulated_bev_vehicle, articulated_diesel_vehicle, standard_externalities
    ):
        """Test externalities calculation comparison between BEV and diesel."""
        bev_ext = calculate_externalities(articulated_bev_vehicle, standard_externalities, 100_000, 10, 0.07)
        diesel_ext = calculate_externalities(articulated_diesel_vehicle, standard_externalities, 100_000, 10, 0.07)

        assert bev_ext['externality_per_km'] < diesel_ext['externality_per_km']
    
    def test_calculate_social_tco(self, articulated_bev_vehicle, standard_externalities):
        """Test social TCO calculation."""
        bev_ext = calculate_externalities(articulated_bev_vehicle, standard_externalities, 100_000, 10, 0.07)
        bev_social = calculate_social_tco(
            {'npv_total_cost': 1_000_000, 'annual_kms': 100_000, 'truck_life_years': 10, 'payload_t': 42}, 
            bev_ext
        )

        assert bev_social['social_tco_lifetime'] > 1_000_000  # Adds externality


class TestExternalityComparison:
    """Test externality comparison functionality."""
    
    def test_externality_comparison_and_social_benefit(
        self, articulated_bev_vehicle, articulated_diesel_vehicle, standard_externalities, standard_financial_params
    ):
        """Test externality comparison and social benefit metrics."""
        bev_ext = calculate_externalities(articulated_bev_vehicle, standard_externalities, 50_000, 5, 0.05)
        diesel_ext = calculate_externalities(articulated_diesel_vehicle, standard_externalities, 50_000, 5, 0.05)
        comparison = prepare_externality_comparison(bev_ext, diesel_ext)
        assert comparison['total_savings'] > 0

        bev_results = {
            'acquisition_cost': 400_000,
            'annual_costs': {'annual_operating_cost': 40_000},
            'externalities': bev_ext,
        }
        diesel_results = {
            'acquisition_cost': 320_000,
            'annual_costs': {'annual_operating_cost': 60_000},
            'externalities': diesel_ext,
        }

        metrics = calculate_social_benefit_metrics(bev_results, diesel_results, 50_000, 5, 0.05)
        assert metrics['social_benefit_cost_ratio'] > 0 