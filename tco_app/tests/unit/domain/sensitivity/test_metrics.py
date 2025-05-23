"""Unit tests for sensitivity metrics calculations."""

import pytest
import math
from unittest.mock import Mock
from tco_app.domain.sensitivity.metrics import calculate_comparative_metrics
from tco_app.src.constants import DataColumns


class TestCalculateComparativeMetrics:
    """Test suite for comparative metrics calculation."""

    @pytest.fixture
    def base_bev_results(self):
        """Basic BEV results for testing."""
        return {
            'acquisition_cost': 380000,
            'residual_value': 70000,
            'annual_costs': {
                'annual_operating_cost': 58000,
                'annual_energy_cost': 25000,
                'annual_maintenance_cost': 8000,
            },
            'emissions': {
                'lifetime_emissions': 625000,
                'annual_emissions': 62500,
            },
            'tco': {
                'npv_total_cost': 750000,
            },
            'battery_replacement_year': 8,
            'battery_replacement_cost': 150000,
        }

    @pytest.fixture
    def base_diesel_results(self):
        """Basic diesel results for testing."""
        return {
            'acquisition_cost': 150000,
            'residual_value': 30000,
            'annual_costs': {
                'annual_operating_cost': 75000,
                'annual_energy_cost': 52500,
                'annual_maintenance_cost': 10000,
            },
            'emissions': {
                'lifetime_emissions': 938000,
                'annual_emissions': 93800,
            },
            'tco': {
                'npv_total_cost': 850000,
            },
        }

    def test_basic_comparison(self, base_bev_results, base_diesel_results):
        """Test basic comparison without infrastructure costs."""
        metrics = calculate_comparative_metrics(
            bev_results=base_bev_results,
            diesel_results=base_diesel_results,
            annual_kms=100000,
            truck_life_years=10
        )

        # Test upfront cost difference
        expected_upfront_diff = 380000 - 150000
        assert metrics['upfront_cost_difference'] == expected_upfront_diff

        # Test annual operating savings (diesel cost - bev cost)
        expected_annual_savings = 75000 - 58000
        assert metrics['annual_operating_savings'] == expected_annual_savings

        # Test emission savings
        expected_emission_savings = 938000 - 625000
        assert metrics['emission_savings_lifetime'] == expected_emission_savings

        # Test BEV to diesel ratio
        expected_ratio = 750000 / 850000
        assert metrics['bev_to_diesel_tco_ratio'] == pytest.approx(expected_ratio, rel=1e-5)

        # Test abatement cost
        expected_abatement = (750000 - 850000) / (313)  # emissions in tonnes
        assert metrics['abatement_cost'] == pytest.approx(expected_abatement, rel=1e-2)

    def test_price_parity_calculation(self):
        """Test price parity year calculation with specific cash flows."""
        # Create results where BEV becomes cheaper after year 5
        bev_results = {
            'acquisition_cost': 200000,
            'residual_value': 40000,
            'annual_costs': {'annual_operating_cost': 20000},
            'emissions': {'lifetime_emissions': 500000},
            'tco': {'npv_total_cost': 350000},
        }
        
        diesel_results = {
            'acquisition_cost': 100000,
            'residual_value': 20000,
            'annual_costs': {'annual_operating_cost': 30000},
            'emissions': {'lifetime_emissions': 800000},
            'tco': {'npv_total_cost': 380000},
        }

        metrics = calculate_comparative_metrics(
            bev_results=bev_results,
            diesel_results=diesel_results,
            annual_kms=100000,
            truck_life_years=10
        )

        # With 100k upfront difference and 10k annual savings, parity should be at year 10
        assert metrics['price_parity_year'] == 10.0

    def test_with_infrastructure_costs(self):
        """Test metrics calculation including infrastructure costs."""
        bev_results = {
            'acquisition_cost': 380000,
            'residual_value': 70000,
            'annual_costs': {'annual_operating_cost': 58000},
            'emissions': {'lifetime_emissions': 625000},
            'tco': {'npv_total_cost': 800000},
            'infrastructure_costs': {
                DataColumns.INFRASTRUCTURE_PRICE: 50000,
                'infrastructure_price_with_incentives': 40000,
                'fleet_size': 10,
                'annual_maintenance': 2000,
                'service_life_years': 15,
            }
        }
        
        diesel_results = {
            'acquisition_cost': 150000,
            'residual_value': 30000,
            'annual_costs': {'annual_operating_cost': 75000},
            'emissions': {'lifetime_emissions': 938000},
            'tco': {'npv_total_cost': 850000},
        }

        metrics = calculate_comparative_metrics(
            bev_results=bev_results,
            diesel_results=diesel_results,
            annual_kms=100000,
            truck_life_years=10
        )

        # Infrastructure cost per vehicle (40000 / 10 = 4000) should be added to upfront cost
        expected_upfront_diff = (380000 + 4000) - 150000
        assert metrics['upfront_cost_difference'] == expected_upfront_diff

    def test_battery_replacement_impact(self):
        """Test impact of battery replacement on cumulative costs."""
        bev_results = {
            'acquisition_cost': 380000,
            'residual_value': 70000,
            'annual_costs': {'annual_operating_cost': 58000},
            'emissions': {'lifetime_emissions': 625000},
            'tco': {'npv_total_cost': 900000},
            'battery_replacement_year': 5,
            'battery_replacement_cost': 100000,
        }
        
        diesel_results = {
            'acquisition_cost': 150000,
            'residual_value': 30000,
            'annual_costs': {'annual_operating_cost': 75000},
            'emissions': {'lifetime_emissions': 938000},
            'tco': {'npv_total_cost': 850000},
        }

        metrics = calculate_comparative_metrics(
            bev_results=bev_results,
            diesel_results=diesel_results,
            annual_kms=100000,
            truck_life_years=10
        )

        # The battery replacement should affect the price parity year
        assert metrics['price_parity_year'] > 10  # Should be pushed beyond 10 years

    def test_zero_emission_savings(self):
        """Test handling of zero emission savings."""
        bev_results = {
            'acquisition_cost': 380000,
            'residual_value': 70000,
            'annual_costs': {'annual_operating_cost': 58000},
            'emissions': {'lifetime_emissions': 625000},
            'tco': {'npv_total_cost': 750000},
        }
        
        diesel_results = {
            'acquisition_cost': 150000,
            'residual_value': 30000,
            'annual_costs': {'annual_operating_cost': 75000},
            'emissions': {'lifetime_emissions': 625000},  # Same as BEV
            'tco': {'npv_total_cost': 850000},
        }

        metrics = calculate_comparative_metrics(
            bev_results=bev_results,
            diesel_results=diesel_results,
            annual_kms=100000,
            truck_life_years=10
        )

        # Abatement cost should be infinity when no emission savings
        assert metrics['abatement_cost'] == float('inf')
        assert metrics['emission_savings_lifetime'] == 0

    def test_no_price_parity_within_lifetime(self):
        """Test when BEV never reaches price parity."""
        bev_results = {
            'acquisition_cost': 500000,  # Very expensive BEV
            'residual_value': 100000,
            'annual_costs': {'annual_operating_cost': 70000},  # Only slightly cheaper annually
            'emissions': {'lifetime_emissions': 625000},
            'tco': {'npv_total_cost': 1100000},
        }
        
        diesel_results = {
            'acquisition_cost': 150000,
            'residual_value': 30000,
            'annual_costs': {'annual_operating_cost': 75000},
            'emissions': {'lifetime_emissions': 938000},
            'tco': {'npv_total_cost': 850000},
        }

        metrics = calculate_comparative_metrics(
            bev_results=bev_results,
            diesel_results=diesel_results,
            annual_kms=100000,
            truck_life_years=10
        )

        # Price parity should be infinity if never reached
        assert metrics['price_parity_year'] == math.inf

    def test_infrastructure_replacement_cycle(self):
        """Test infrastructure replacement impact on costs."""
        bev_results = {
            'acquisition_cost': 380000,
            'residual_value': 70000,
            'annual_costs': {'annual_operating_cost': 58000},
            'emissions': {'lifetime_emissions': 625000},
            'tco': {'npv_total_cost': 850000},
            'infrastructure_costs': {
                DataColumns.INFRASTRUCTURE_PRICE: 60000,
                'infrastructure_price_with_incentives': None,  # No incentives
                'fleet_size': 5,
                'annual_maintenance': 3000,
                'service_life_years': 5,  # Replacement every 5 years
            }
        }
        
        diesel_results = {
            'acquisition_cost': 150000,
            'residual_value': 30000,
            'annual_costs': {'annual_operating_cost': 75000},
            'emissions': {'lifetime_emissions': 938000},
            'tco': {'npv_total_cost': 850000},
        }

        metrics = calculate_comparative_metrics(
            bev_results=bev_results,
            diesel_results=diesel_results,
            annual_kms=100000,
            truck_life_years=10
        )

        # With infrastructure replacement at year 5, price parity should be delayed
        assert metrics['price_parity_year'] > 10

    def test_edge_case_single_year_lifetime(self):
        """Test edge case with single year truck lifetime."""
        bev_results = {
            'acquisition_cost': 380000,
            'residual_value': 350000,  # High residual for 1 year
            'annual_costs': {'annual_operating_cost': 58000},
            'emissions': {'lifetime_emissions': 62500},
            'tco': {'npv_total_cost': 88000},
        }
        
        diesel_results = {
            'acquisition_cost': 150000,
            'residual_value': 140000,
            'annual_costs': {'annual_operating_cost': 75000},
            'emissions': {'lifetime_emissions': 93800},
            'tco': {'npv_total_cost': 85000},
        }

        metrics = calculate_comparative_metrics(
            bev_results=bev_results,
            diesel_results=diesel_results,
            annual_kms=100000,
            truck_life_years=1
        )

        # With only 1 year, price parity calculation should handle edge case
        assert 'price_parity_year' in metrics
        assert 'upfront_cost_difference' in metrics

    def test_negative_npv_scenario(self):
        """Test handling of negative NPV values."""
        bev_results = {
            'acquisition_cost': 100000,
            'residual_value': 200000,  # Very high residual value
            'annual_costs': {'annual_operating_cost': 20000},
            'emissions': {'lifetime_emissions': 625000},
            'tco': {'npv_total_cost': -50000},  # Negative NPV
        }
        
        diesel_results = {
            'acquisition_cost': 150000,
            'residual_value': 30000,
            'annual_costs': {'annual_operating_cost': 75000},
            'emissions': {'lifetime_emissions': 938000},
            'tco': {'npv_total_cost': 850000},
        }

        metrics = calculate_comparative_metrics(
            bev_results=bev_results,
            diesel_results=diesel_results,
            annual_kms=100000,
            truck_life_years=10
        )

        # Should handle negative NPV correctly
        assert metrics['bev_to_diesel_tco_ratio'] < 0
