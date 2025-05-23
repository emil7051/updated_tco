"""Centralised configuration management for the TCO application.

This module provides configuration classes that consolidate scattered constants
and magic numbers, improving maintainability and discoverability.
"""

from tco_app.src import dataclass


@dataclass(frozen=True)
class CalculationDefaults:
    """Default values for financial and operational calculations."""

    # Financial defaults
    DEFAULT_DISCOUNT_RATE: float = 0.07  # 7%
    DEFAULT_TRUCK_LIFE_YEARS: int = 10
    DEFAULT_ANNUAL_KMS: int = 50000

    # Time constants
    DAYS_PER_YEAR: int = 365

    # Infrastructure defaults
    DEFAULT_CHARGER_POWER_KW: float = 80.0  # DC fast charger
    DEFAULT_FLEET_SIZE: int = 1


@dataclass(frozen=True)
class ValidationLimits:
    """Validation limits for user inputs and calculations."""

    # Annual distance limits
    MIN_ANNUAL_KMS: int = 1000
    MAX_ANNUAL_KMS: int = 200000
    ANNUAL_KMS_STEP: int = 1000

    # Vehicle lifetime limits
    MIN_TRUCK_LIFE_YEARS: int = 1
    MAX_TRUCK_LIFE_YEARS: int = 30
    TRUCK_LIFE_STEP: int = 1

    # Fleet size limits
    MIN_FLEET_SIZE: int = 1
    MAX_FLEET_SIZE: int = 1000
    FLEET_SIZE_STEP: int = 1

    # Financial limits
    MIN_DISCOUNT_RATE: float = 0.01  # 1%
    MAX_DISCOUNT_RATE: float = 0.20  # 20%

    # Sensitivity analysis
    SENSITIVITY_VARIANCE_FACTOR: float = 0.5  # ±50% from base value
    DEFAULT_SENSITIVITY_POINTS: int = 11


@dataclass(frozen=True)
class UIConfig:
    """Configuration for Streamlit UI appearance and behaviour."""

    # Page configuration
    PAGE_TITLE: str = "Electric vs. Diesel Truck TCO Model"
    PAGE_ICON: str = "🚚"
    PAGE_LAYOUT: str = "wide"
    SIDEBAR_STATE: str = "expanded"

    # UI behaviour
    USE_CONTAINER_WIDTH: bool = True

    # Default number input steps
    DEFAULT_KM_STEP: int = 1000
    DEFAULT_YEAR_STEP: int = 1
    DEFAULT_FLEET_STEP: int = 1

    # Percentage allocation for charging mix
    CHARGING_MIX_STEP: int = 5  # 5% increments
    CHARGING_MIX_TOTAL: int = 100  # Must sum to 100%


@dataclass(frozen=True)
class PerformanceConfig:
    """Configuration for performance optimization and caching."""

    # NPV optimization threshold
    NPV_OPTIMIZATION_THRESHOLD: int = 10  # Use fast calculation for > 10 years

    # Cache configuration
    DEFAULT_CACHE_SIZE: int = 128
    LRU_CACHE_SIZE: int = 256

    # Calculation precision
    CURRENCY_PRECISION: int = 2  # Decimal places for currency
    PERCENTAGE_PRECISION: int = 1  # Decimal places for percentages
    RATIO_PRECISION: int = 3  # Decimal places for ratios


@dataclass(frozen=True)
class EmissionConstants:
    """Constants for emission calculations."""

    # Grid emission standards
    DEFAULT_ELECTRICITY_STANDARD: str = "Grid"
    DEFAULT_DIESEL_STANDARD: str = "Euro IV+"

    # Unit conversions
    KG_TO_TONNES: float = 1000.0
    PERCENTAGE_TO_DECIMAL: float = 100.0


# Create singleton instances for easy access
CALC_DEFAULTS = CalculationDefaults()
VALIDATION_LIMITS = ValidationLimits()
UI_CONFIG = UIConfig()
PERFORMANCE_CONFIG = PerformanceConfig()
EMISSION_CONSTANTS = EmissionConstants()


# Export all configuration instances
__all__ = [
    "CalculationDefaults",
    "ValidationLimits",
    "UIConfig",
    "PerformanceConfig",
    "EmissionConstants",
    "CALC_DEFAULTS",
    "VALIDATION_LIMITS",
    "UI_CONFIG",
    "PERFORMANCE_CONFIG",
    "EMISSION_CONSTANTS",
]
