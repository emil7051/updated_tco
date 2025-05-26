"""Source package with centralised imports and utilities."""

# Re-export common imports for easy access
# Keep existing exports available
from . import constants, exceptions, utils

# Re-export configuration instances
from .config import (
    CALC_DEFAULTS,
    EXTERNALITY_CONSTANTS,
    PERFORMANCE_CONFIG,
    UI_CONFIG,
    UNIT_CONVERSIONS,
    VALIDATION_LIMITS,
)
from .imports import (
    Any,
    Dict,  # Data libraries; Typing; Standard library
    Iterable,
    List,
    Mapping,
    Optional,
    Path,
    Protocol,
    Sequence,
    Tuple,
    Union,
    dataclass,
    datetime,
    field,
    hashlib,
    json,
    logging,
    lru_cache,
    np,
    pd,
    st,
)

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
    "UNIT_CONVERSIONS",
    "EXTERNALITY_CONSTANTS",
    # Modules
    "constants",
    "exceptions",
    "utils",
]
