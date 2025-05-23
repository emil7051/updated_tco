"""Source package with centralised imports and utilities."""

# Re-export common imports for easy access
from .imports import (
    # Data libraries
    pd,
    np,
    st,
    # Typing
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
    Mapping,
    Sequence,
    Protocol,
    Iterable,
    # Standard library
    logging,
    dataclass,
    field,
    datetime,
    json,
    hashlib,
    lru_cache,
    Path,
)

# Re-export configuration instances
from .config import (
    CALC_DEFAULTS,
    VALIDATION_LIMITS,
    UI_CONFIG,
    PERFORMANCE_CONFIG,
    EMISSION_CONSTANTS,
)

# Keep existing exports available
from . import constants, exceptions, utils

__all__ = [
    # Data libraries
    "pd",
    "np",
    "st",
    # Typing
    "Any",
    "Dict",
    "List",
    "Optional",
    "Tuple",
    "Union",
    "Mapping",
    "Sequence",
    "Protocol",
    "Iterable",
    # Standard library
    "logging",
    "dataclass",
    "field",
    "datetime",
    "json",
    "hashlib",
    "lru_cache",
    "Path",
    # Configuration instances
    "CALC_DEFAULTS",
    "VALIDATION_LIMITS",
    "UI_CONFIG",
    "PERFORMANCE_CONFIG",
    "EMISSION_CONSTANTS",
    # Modules
    "constants",
    "exceptions",
    "utils",
]
