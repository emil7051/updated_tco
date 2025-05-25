"""Caching layer for expensive data operations."""

from tco_app.src import (
    PERFORMANCE_CONFIG,
    Any,
    Dict,
    Optional,
    hashlib,
    json,
    logging,
    pd,
)

logger = logging.getLogger(__name__)


class DataCache:
    """Cache for data operations and calculations."""

    def __init__(self, max_size: int = PERFORMANCE_CONFIG.DEFAULT_CACHE_SIZE):
        """Initialise cache with maximum size."""
        self.max_size = max_size
        self._cache: Dict[str, Any] = {}
        self._access_count: Dict[str, int] = {}

    def _make_key(self, *args, **kwargs) -> str:
        """Create cache key from arguments."""
        # Convert args and kwargs to stable string representation
        key_data = {
            "args": [self._serialise_arg(arg) for arg in args],
            "kwargs": {k: self._serialise_arg(v) for k, v in kwargs.items()},
        }

        # Create hash
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _serialise_arg(self, arg: Any) -> Any:
        """Serialise argument for cache key."""
        if isinstance(arg, pd.DataFrame):
            # Use shape and column names for DataFrames
            return {
                "type": "DataFrame",
                "shape": arg.shape,
                "columns": list(arg.columns),
            }
        elif isinstance(arg, pd.Series):
            return {"type": "Series", "name": arg.name, "shape": arg.shape}
        elif hasattr(arg, "__dict__"):
            # For objects, use their dict representation
            return {"type": type(arg).__name__, "data": str(arg.__dict__)}
        else:
            return arg

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key in self._cache:
            self._access_count[key] = self._access_count.get(key, 0) + 1
            logger.debug(f"Cache hit for key {key[:8]}...")
            return self._cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        # Check size limit
        if len(self._cache) >= self.max_size:
            # Remove least accessed item
            if self._access_count:
                least_accessed = min(self._access_count.items(), key=lambda x: x[1])[0]
                del self._cache[least_accessed]
                del self._access_count[least_accessed]

        self._cache[key] = value
        self._access_count[key] = 1

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._access_count.clear()
        logger.info("Cache cleared")

    def cache_dataframe_lookup(self, func):
        """Decorator for caching DataFrame lookups."""

        def wrapper(df: pd.DataFrame, *args, **kwargs):
            # Create cache key
            cache_key = self._make_key(
                func.__name__, df.shape, list(df.columns), *args, **kwargs
            )

            # Check cache
            result = self.get(cache_key)
            if result is not None:
                return result

            # Calculate and cache
            result = func(df, *args, **kwargs)
            self.set(cache_key, result)
            return result

        return wrapper


# Global cache instance
data_cache = DataCache()


def get_vehicle_with_cache(vehicle_models: pd.DataFrame, vehicle_id: str) -> pd.Series:
    """Get vehicle with caching.

    Args:
        vehicle_models: DataFrame with vehicle data
        vehicle_id: Vehicle ID to lookup

    Returns:
        Vehicle data as Series
    """

    # Use cached lookup
    @data_cache.cache_dataframe_lookup
    def _lookup(df, vid):
        from tco_app.src.utils.safe_operations import safe_lookup_vehicle

        return safe_lookup_vehicle(df, vid)

    return _lookup(vehicle_models, vehicle_id)
