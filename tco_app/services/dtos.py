"""Data Transfer Objects for the TCO calculation service.

This module contains the dataclasses used to structure input and output
data for the TCO calculation service, promoting type safety and clear interfaces.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
from tco_app.src import pd, datetime, Any

from tco_app.src.constants import DataColumns, Drivetrain

__all__ = [
    "CalculationParameters",
    "CalculationRequest",
    "TCOResult",
    "ComparisonResult",
]


@dataclass
class CalculationParameters:
    """Scalar and UI-level inputs that influence a single calculation run."""

    # Required inputs
    annual_kms: int
    truck_life_years: int
    discount_rate: float
    selected_charging_profile_id: int
    selected_infrastructure_id: int

    # Optional inputs with defaults
    fleet_size: int = 1
    apply_incentives: bool = True
    charging_mix: Optional[Dict[int, float]] = None
    scenario_name: str = "Default"

    # UI overrides – applied further up-stream or by repositories
    diesel_price_override: Optional[float] = None
    carbon_price_override: Optional[float] = None
    degradation_rate_override: Optional[float] = None
    replacement_cost_override: Optional[float] = None


@dataclass
class CalculationRequest:
    """Bundled data inputs for a single-vehicle TCO calculation."""

    vehicle_data: pd.Series
    fees_data: pd.Series
    parameters: CalculationParameters

    # Normalised full data tables
    charging_options: pd.DataFrame
    infrastructure_options: pd.DataFrame
    financial_params: pd.DataFrame
    battery_params: pd.DataFrame
    emission_factors: pd.DataFrame
    externalities_data: pd.DataFrame
    incentives: pd.DataFrame

    @property
    def drivetrain(self) -> str:  # pragma: no cover – simple helper
        """Return the drivetrain ID for conditional logic branches."""
        return self.vehicle_data.get(DataColumns.VEHICLE_DRIVETRAIN, Drivetrain.DIESEL)


@dataclass
class TCOResult:
    """Result payload for a single-vehicle calculation."""

    # Core TCO outputs
    tco_total_lifetime: float
    tco_per_km: float
    tco_per_tonne_km: float
    social_tco_total_lifetime: float

    # Cost breakdowns
    acquisition_cost: float
    residual_value: float
    npv_annual_operating_cost: float
    npv_battery_replacement_cost: float
    npv_infrastructure_cost: float

    # Annual & energy
    annual_operating_cost: float
    energy_cost_per_km: float

    # Emissions
    lifetime_emissions_co2e: float
    annual_emissions_co2e: float
    co2e_per_km: float

    # Identifiers
    vehicle_id: str

    # Detailed breakdowns
    annual_costs_breakdown: Dict[str, float] = field(default_factory=dict)
    tco_breakdown: Dict[str, float] = field(default_factory=dict)
    externalities_breakdown: Dict[str, float] = field(default_factory=dict)
    emissions_breakdown: Dict[str, float] = field(default_factory=dict)

    # BEV-specific
    charging_requirements: Optional[Dict[str, Any]] = None
    infrastructure_costs_breakdown: Optional[Dict[str, Any]] = None
    weighted_electricity_price: Optional[float] = None

    # Meta
    calculation_timestamp: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )
    scenario_meta: Dict[str, str] = field(default_factory=dict)


@dataclass
class ComparisonResult:
    """Container for BEV versus diesel comparison metrics."""

    base_vehicle_result: TCOResult
    comparison_vehicle_result: TCOResult

    tco_savings_lifetime: float
    annual_operating_cost_savings: Optional[float] = None
    emissions_reduction_lifetime_co2e: Optional[float] = None
    payback_period_years: Optional[float] = None

    # Extra comparative metrics
    upfront_cost_difference: Optional[float] = None
    abatement_cost: Optional[float] = None
    bev_to_diesel_tco_ratio: Optional[float] = None

    # Meta
    comparison_timestamp: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )
