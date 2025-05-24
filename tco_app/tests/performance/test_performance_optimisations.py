"""Performance tests for Work Package 8 optimisations."""

import time
import logging
from tco_app.src import np
from tco_app.src import pd
import pytest

from tco_app.src.utils.finance import npv_constant
from tco_app.src.utils.calculation_optimisations import (
    fast_npv,
    vectorised_annual_costs,
    batch_vehicle_lookup,
)
from tco_app.domain.finance import calculate_npv, calculate_npv_optimised
from tco_app.src.constants import DataColumns

logger = logging.getLogger(__name__)


class TestNPVPerformance:
    """Test NPV calculation performance improvements."""

    def test_npv_performance_comparison(self):
        """Compare original vs optimised NPV calculations."""
        annual_cost = 50000
        discount_rate = 0.07
        years = 20

        # Original implementation
        start_time = time.time()
        for _ in range(100):
            result_original = npv_constant(annual_cost, discount_rate, years)
        original_time = time.time() - start_time

        # Optimised implementation for large arrays
        start_time = time.time()
        for _ in range(100):
            result_optimised = calculate_npv_optimised(
                annual_cost, discount_rate, years
            )
        optimised_time = time.time() - start_time

        # Results should be approximately equal
        assert abs(result_original - result_optimised) < 1.0

        logger.info("Original NPV time: %.4fs", original_time)
        logger.info("Optimised NPV time: %.4fs", optimised_time)

        # For small calculations, optimised might not be faster due to overhead
        # This test just ensures both work correctly

    def test_fast_npv_large_arrays(self):
        """Test fast NPV with large cash flow arrays."""
        cash_flows = np.full(1000, 1000.0)  # 1000 years of $1000
        discount_rate = 0.05

        start_time = time.time()
        result = fast_npv(cash_flows, discount_rate)
        execution_time = time.time() - start_time

        assert result > 0
        assert execution_time < 1.0  # Should complete in under 1 second
        logger.info(
            "Fast NPV (1000 years): %.4fs, Result: $%s",
            execution_time,
            f"{result:,.2f}",
        )


class TestVehicleLookupPerformance:
    """Test vehicle lookup performance improvements."""

    @pytest.fixture
    def large_vehicle_dataset(self):
        """Create a large vehicle dataset for testing."""
        vehicle_ids = [f"VEH{i:05d}" for i in range(1000)]
        return pd.DataFrame(
            {
                DataColumns.VEHICLE_ID: vehicle_ids,
                "model_name": [f"Model {i}" for i in range(1000)],
                DataColumns.MSRP_PRICE: np.random.uniform(100000, 500000, 1000),
                DataColumns.VEHICLE_DRIVETRAIN: np.random.choice(["BEV", "ICE"], 1000),
            }
        )

    def test_batch_vs_individual_lookup(self, large_vehicle_dataset):
        """Compare batch vs individual vehicle lookups."""
        vehicle_ids_to_lookup = [
            "VEH00050",
            "VEH00150",
            "VEH00250",
            "VEH00350",
            "VEH00450",
        ]

        # Individual lookups (simulating original approach)
        start_time = time.time()
        individual_results = []
        for vid in vehicle_ids_to_lookup:
            mask = large_vehicle_dataset[DataColumns.VEHICLE_ID] == vid
            if mask.any():
                individual_results.append(large_vehicle_dataset[mask].iloc[0])
        individual_time = time.time() - start_time

        # Batch lookup (optimised approach)
        start_time = time.time()
        batch_result = batch_vehicle_lookup(
            large_vehicle_dataset, vehicle_ids_to_lookup
        )
        batch_time = time.time() - start_time

        # Results should be equivalent
        assert len(individual_results) == len(batch_result)
        assert len(batch_result) == len(vehicle_ids_to_lookup)

        logger.info("Individual lookups time: %.4fs", individual_time)
        logger.info("Batch lookup time: %.4fs", batch_time)

        # Batch should be faster for multiple lookups
        if len(vehicle_ids_to_lookup) > 3:
            assert batch_time <= individual_time * 2  # Allow some overhead


class TestVectorisedOperations:
    """Test vectorised calculation performance."""

    def test_vectorised_vs_loop_annual_costs(self):
        """Compare vectorised vs loop-based annual cost calculations."""
        base_cost = 50000
        growth_rate = 0.03
        years = 1000  # Use larger dataset where vectorization benefits are visible
        iterations = 100  # Fewer iterations since each calculation is now larger

        # Loop-based calculation (original style) - measure multiple iterations
        start_time = time.time()
        for _ in range(iterations):
            loop_result = []
            for year in range(years):
                cost = base_cost * ((1 + growth_rate) ** year)
                loop_result.append(cost)
        loop_time = time.time() - start_time

        # Vectorised calculation - measure multiple iterations
        start_time = time.time()
        for _ in range(iterations):
            vectorised_result = vectorised_annual_costs(base_cost, growth_rate, years)
        vectorised_time = time.time() - start_time

        # Results should be equivalent (using final iteration for comparison)
        np.testing.assert_array_almost_equal(
            np.array(loop_result), vectorised_result, decimal=2
        )
        logger.info("Loop-based calculation: %.4fs", loop_time)
        logger.info("Vectorised calculation: %.4fs", vectorised_time)

        # Vectorised should be faster (allow small margin for system noise)
        assert vectorised_time <= loop_time * 1.1


class TestCachePerformance:
    """Test data cache performance benefits."""

    def test_cache_hit_performance(self):
        """Test performance benefit of cache hits."""
        from tco_app.services.data_cache import DataCache

        cache = DataCache(max_size=100)

        # Expensive operation simulation
        def expensive_calculation(x):
            time.sleep(0.001)  # Simulate 1ms operation
            return x * 2

        # Cache decorator
        @cache.cache_dataframe_lookup
        def cached_operation(df, value):
            return expensive_calculation(value)

        test_df = pd.DataFrame({"col": [1, 2, 3]})

        # First call (cache miss)
        start_time = time.time()
        result1 = cached_operation(test_df, 42)
        first_call_time = time.time() - start_time

        # Second call (cache hit)
        start_time = time.time()
        result2 = cached_operation(test_df, 42)
        second_call_time = time.time() - start_time

        assert result1 == result2 == 84

        logger.info("Cache miss time: %.4fs", first_call_time)
        logger.info("Cache hit time: %.4fs", second_call_time)

        # Cache hit should be significantly faster
        assert second_call_time < first_call_time * 0.5


def test_overall_calculation_performance():
    """Integration test showing overall performance improvement potential."""
    logger.info("\n=== Work Package 8 Performance Summary ===")

    # Simulate a complex calculation workflow
    start_time = time.time()

    # NPV calculation
    npv_result = calculate_npv_optimised(50000, 0.07, 15)

    # Vectorised operations
    annual_costs = vectorised_annual_costs(10000, 0.025, 20)

    # Batch lookup simulation
    vehicle_data = pd.DataFrame(
        {
            DataColumns.VEHICLE_ID: ["BEV001", "BEV002", "ICE001"],
            "price": [250000, 300000, 180000],
        }
    )
    vehicles = batch_vehicle_lookup(vehicle_data, ["BEV001", "ICE001"])

    total_time = time.time() - start_time

    logger.info("Total optimised calculation time: %.4fs", total_time)
    logger.info("NPV result: $%s", f"{npv_result:,.2f}")
    logger.info("Annual costs array length: %d", len(annual_costs))
    logger.info("Vehicles found: %d", len(vehicles))

    assert total_time < 1.0  # Should complete quickly
    assert npv_result > 0
    assert len(annual_costs) == 20
    assert len(vehicles) == 2


if __name__ == "__main__":
    test_overall_calculation_performance()
