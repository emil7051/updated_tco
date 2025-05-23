"""Test optimised calculation utilities."""

import pytest
from tco_app.src import np
from tco_app.src import pd
from unittest.mock import patch

from tco_app.src.utils.calculation_optimisations import (
    fast_npv,
    vectorised_annual_costs,
    batch_vehicle_lookup,
    fast_discount_factors,
    optimised_tco_calculation,
    batch_parameter_lookup,
    fast_cumulative_sum,
    optimised_emissions_calculation,
)
from tco_app.src.constants import DataColumns


class TestFastNPV:
    """Test fast NPV calculations."""

    def test_fast_npv_basic(self):
        """Test basic NPV calculation."""
        cash_flows = np.array([1000, 1000, 1000])
        discount_rate = 0.05

        result = fast_npv(cash_flows, discount_rate)

        # Manual calculation for verification
        expected = (1000 / 1.05) + (1000 / 1.05**2) + (1000 / 1.05**3)
        assert abs(result - expected) < 0.01

    def test_fast_npv_zero_rate(self):
        """Test NPV with zero discount rate."""
        cash_flows = np.array([1000, 1000, 1000])
        discount_rate = 0.0

        result = fast_npv(cash_flows, discount_rate)
        expected = 3000  # Simple sum when no discounting

        assert abs(result - expected) < 0.01

    def test_fast_npv_empty_array(self):
        """Test NPV with empty cash flows."""
        cash_flows = np.array([])
        discount_rate = 0.05

        result = fast_npv(cash_flows, discount_rate)
        assert result == 0.0


class TestVectorisedCalculations:
    """Test vectorised calculation utilities."""

    def test_vectorised_annual_costs(self):
        """Test vectorised annual cost calculation."""
        base_cost = 10000
        growth_rate = 0.03
        years = 5

        result = vectorised_annual_costs(base_cost, growth_rate, years)

        # Manual calculation for verification
        expected = np.array(
            [
                10000 * (1.03**0),  # Year 0
                10000 * (1.03**1),  # Year 1
                10000 * (1.03**2),  # Year 2
                10000 * (1.03**3),  # Year 3
                10000 * (1.03**4),  # Year 4
            ]
        )

        np.testing.assert_array_almost_equal(result, expected, decimal=2)

    def test_vectorised_annual_costs_zero_growth(self):
        """Test with zero growth rate."""
        base_cost = 5000
        growth_rate = 0.0
        years = 3

        result = vectorised_annual_costs(base_cost, growth_rate, years)
        expected = np.array([5000, 5000, 5000])

        np.testing.assert_array_equal(result, expected)


class TestBatchOperations:
    """Test batch operation utilities."""

    def test_batch_vehicle_lookup(self):
        """Test batch vehicle lookup."""
        vehicle_models = pd.DataFrame(
            {
                DataColumns.VEHICLE_ID: ["VEH001", "VEH002", "VEH003", "VEH004"],
                "model_name": ["Model A", "Model B", "Model C", "Model D"],
                "price": [100000, 150000, 200000, 250000],
            }
        )

        vehicle_ids = ["VEH002", "VEH004"]
        result = batch_vehicle_lookup(vehicle_models, vehicle_ids)

        assert len(result) == 2
        assert list(result[DataColumns.VEHICLE_ID]) == ["VEH002", "VEH004"]
        assert list(result["model_name"]) == ["Model B", "Model D"]

    def test_batch_parameter_lookup(self):
        """Test batch parameter lookup."""
        params_df = pd.DataFrame(
            {
                "param_key": ["discount_rate", "inflation_rate", "tax_rate"],
                "param_value": [0.07, 0.025, 0.30],
            }
        )

        param_keys = ["discount_rate", "tax_rate"]
        result = batch_parameter_lookup(
            params_df, param_keys, "param_key", "param_value"
        )

        expected = {"discount_rate": 0.07, "tax_rate": 0.30}
        assert result == expected

    def test_batch_parameter_lookup_missing_keys(self):
        """Test batch parameter lookup with missing keys."""
        params_df = pd.DataFrame(
            {
                "param_key": ["discount_rate", "inflation_rate"],
                "param_value": [0.07, 0.025],
            }
        )

        param_keys = ["discount_rate", "missing_key"]
        result = batch_parameter_lookup(
            params_df, param_keys, "param_key", "param_value"
        )

        # Should only return found keys
        expected = {"discount_rate": 0.07}
        assert result == expected


class TestDiscountFactors:
    """Test discount factor calculations."""

    def test_fast_discount_factors(self):
        """Test fast discount factor calculation."""
        discount_rate = 0.05
        years = 3

        result = fast_discount_factors(discount_rate, years)

        expected = np.array(
            [
                1 / 1.05,  # Year 1
                1 / (1.05**2),  # Year 2
                1 / (1.05**3),  # Year 3
            ]
        )

        np.testing.assert_array_almost_equal(result, expected, decimal=6)

    def test_fast_discount_factors_zero_rate(self):
        """Test discount factors with zero rate."""
        discount_rate = 0.0
        years = 3

        result = fast_discount_factors(discount_rate, years)
        expected = np.array([1.0, 1.0, 1.0])

        np.testing.assert_array_equal(result, expected)


class TestOptimisedTCO:
    """Test optimised TCO calculation."""

    def test_optimised_tco_calculation(self):
        """Test optimised TCO calculation."""
        annual_costs = np.array([50000, 52000, 54000])
        acquisition_cost = 200000
        residual_value = 50000
        discount_rate = 0.07

        result = optimised_tco_calculation(
            annual_costs, acquisition_cost, residual_value, discount_rate
        )

        # Manual verification
        discount_factors = fast_discount_factors(discount_rate, 3)
        npv_annual = np.sum(annual_costs * discount_factors)
        npv_residual = residual_value / (1.07**3)
        expected = acquisition_cost + npv_annual - npv_residual

        assert abs(result - expected) < 0.01


class TestUtilityFunctions:
    """Test utility functions."""

    def test_fast_cumulative_sum(self):
        """Test fast cumulative sum."""
        values = np.array([10, 20, 30, 40])
        result = fast_cumulative_sum(values)
        expected = np.array([10, 30, 60, 100])

        np.testing.assert_array_equal(result, expected)

    def test_optimised_emissions_calculation(self):
        """Test optimised emissions calculation."""
        annual_kms = 50000
        emission_factor = 0.85  # kg CO2/km
        years = 10

        annual_emissions, lifetime_emissions = optimised_emissions_calculation(
            annual_kms, emission_factor, years
        )

        expected_annual = 50000 * 0.85
        expected_lifetime = expected_annual * 10

        assert annual_emissions == expected_annual
        assert lifetime_emissions == expected_lifetime


@pytest.fixture
def sample_vehicle_data():
    """Sample vehicle data for testing."""
    return pd.DataFrame(
        {
            DataColumns.VEHICLE_ID: ["BEV001", "BEV002", "ICE001"],
            "model_name": ["Electric Truck A", "Electric Truck B", "Diesel Truck"],
            DataColumns.MSRP_PRICE: [250000, 300000, 180000],
        }
    )


def test_performance_comparison():
    """Test that optimised functions are available (even if not faster in small cases)."""
    # This is more of a smoke test to ensure functions are callable
    cash_flows = np.array([1000] * 100)
    discount_rate = 0.05

    # Should not raise any errors
    result = fast_npv(cash_flows, discount_rate)
    assert result > 0

    # Test vectorised operations
    annual_costs = vectorised_annual_costs(10000, 0.03, 20)
    assert len(annual_costs) == 20
    assert annual_costs[0] == 10000
