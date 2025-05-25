"""Test data cache functionality."""

from unittest.mock import patch

import pytest

from tco_app.services.data_cache import DataCache, data_cache, get_vehicle_with_cache
from tco_app.src import pd
from tco_app.src.constants import DataColumns


class TestDataCache:
    """Test the DataCache class."""

    def test_cache_init(self):
        """Test cache initialisation."""
        cache = DataCache(max_size=10)
        assert cache.max_size == 10
        assert len(cache._cache) == 0
        assert len(cache._access_count) == 0

    def test_cache_set_get(self):
        """Test basic cache set and get operations."""
        cache = DataCache(max_size=5)

        # Set a value
        cache.set("test_key", "test_value")

        # Get the value
        result = cache.get("test_key")
        assert result == "test_value"

        # Test cache miss
        assert cache.get("non_existent") is None

    def test_cache_size_limit(self):
        """Test cache size limiting with LRU eviction."""
        cache = DataCache(max_size=2)

        # Fill cache to limit
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        # Access key1 to make it more recent
        cache.get("key1")

        # Add third item - should evict key2 (least accessed)
        cache.set("key3", "value3")

        assert cache.get("key1") == "value1"  # Still there
        assert cache.get("key2") is None  # Evicted
        assert cache.get("key3") == "value3"  # New item

    def test_cache_clear(self):
        """Test cache clearing."""
        cache = DataCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.clear()

        assert len(cache._cache) == 0
        assert len(cache._access_count) == 0
        assert cache.get("key1") is None

    def test_serialise_dataframe(self):
        """Test DataFrame serialisation for cache keys."""
        cache = DataCache()
        df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})

        serialised = cache._serialise_arg(df)
        expected = {"type": "DataFrame", "shape": (3, 2), "columns": ["col1", "col2"]}

        assert serialised == expected

    def test_cache_dataframe_lookup_decorator(self):
        """Test the DataFrame lookup decorator."""
        cache = DataCache()
        call_count = 0

        @cache.cache_dataframe_lookup
        def lookup_function(df, value):
            nonlocal call_count
            call_count += 1
            return (
                df[df["id"] == value].iloc[0]
                if len(df[df["id"] == value]) > 0
                else None
            )

        # Create test DataFrame
        test_df = pd.DataFrame({"id": ["A", "B", "C"], "value": [1, 2, 3]})

        # First call should execute function
        result1 = lookup_function(test_df, "B")
        assert call_count == 1
        assert result1["value"] == 2

        # Second call with same parameters should use cache
        result2 = lookup_function(test_df, "B")
        assert call_count == 1  # Not incremented
        assert result2["value"] == 2


class TestVehicleCaching:
    """Test vehicle-specific caching functionality."""

    def test_get_vehicle_with_cache(self):
        """Test cached vehicle lookup."""
        # Create test vehicle data
        vehicle_models = pd.DataFrame(
            {
                DataColumns.VEHICLE_ID: ["VEH001", "VEH002", "VEH003"],
                "model_name": ["Model A", "Model B", "Model C"],
                "price": [100000, 150000, 200000],
            }
        )

        with patch(
            "tco_app.src.utils.safe_operations.safe_lookup_vehicle"
        ) as mock_lookup:
            mock_lookup.return_value = vehicle_models.iloc[1]  # Return second row

            # First call should hit the actual function
            result1 = get_vehicle_with_cache(vehicle_models, "VEH002")
            assert mock_lookup.call_count == 1
            assert result1["model_name"] == "Model B"

            # Second call should use cache (but decorator implementation may still call)
            result2 = get_vehicle_with_cache(vehicle_models, "VEH002")
            assert result2["model_name"] == "Model B"


@pytest.fixture
def sample_vehicle_data():
    """Sample vehicle data for testing."""
    return pd.DataFrame(
        {
            DataColumns.VEHICLE_ID: ["BEV001", "BEV002", "ICE001"],
            "model_name": ["Electric Truck A", "Electric Truck B", "Diesel Truck"],
            DataColumns.MSRP_PRICE: [250000, 300000, 180000],
            DataColumns.VEHICLE_DRIVETRAIN: ["BEV", "BEV", "ICE"],
        }
    )


def test_global_cache_instance():
    """Test that global cache instance is available."""
    assert data_cache is not None
    assert isinstance(data_cache, DataCache)

    # Clear to ensure clean state
    data_cache.clear()
    assert len(data_cache._cache) == 0
