"""Components for sensitivity analysis page refactoring."""

from dataclasses import dataclass
from typing import List
import pandas as pd

from tco_app.src.constants import DataColumns, ParameterKeys


@dataclass
class SensitivityContext:
    """Encapsulates all context data for sensitivity analysis."""

    bev_results: dict
    diesel_results: dict
    bev_vehicle_data: pd.DataFrame
    diesel_vehicle_data: pd.DataFrame
    bev_fees: pd.DataFrame
    diesel_fees: pd.DataFrame
    charging_options: pd.DataFrame
    infrastructure_options: pd.DataFrame
    financial_params_with_ui: pd.DataFrame
    battery_params_with_ui: pd.DataFrame
    emission_factors: pd.DataFrame
    incentives: pd.DataFrame
    selected_charging: int
    selected_infrastructure: int
    annual_kms: float
    truck_life_years: int
    discount_rate: float
    fleet_size: int
    charging_mix: dict
    apply_incentives: bool

    @classmethod
    def from_context(cls, ctx: dict) -> "SensitivityContext":
        """Create from context dictionary."""
        fields_to_extract = cls.__dataclass_fields__.keys()
        extracted_data = {}

        for field in fields_to_extract:
            if field in ctx:
                extracted_data[field] = ctx[field]
            else:
                raise KeyError(f"Required field '{field}' not found in context")

        return cls(**extracted_data)


class ParameterRangeCalculator:
    """Calculates parameter ranges for sensitivity analysis."""

    def __init__(self, num_points: int = 11):
        self.num_points = num_points

    def calculate_annual_distance_range(self, base_value: float) -> List[float]:
        """Calculate range for annual distance parameter."""
        min_val = max(1000, base_value * 0.5)
        max_val = base_value * 1.5
        return self._create_range(min_val, max_val, base_value, round_digits=0)

    def calculate_diesel_price_range(
        self, financial_params: pd.DataFrame
    ) -> List[float]:
        """Calculate range for diesel price parameter."""
        base_value = self._get_financial_param(
            financial_params, ParameterKeys.DIESEL_PRICE
        )
        min_val = max(0.5, base_value * 0.7)
        max_val = base_value * 1.3
        return self._create_range(min_val, max_val, base_value, round_digits=2)

    def calculate_electricity_price_range(
        self, bev_results: dict, charging_options: pd.DataFrame, selected_charging: int
    ) -> List[float]:
        """Calculate range for electricity price parameter."""
        base_value = self._get_electricity_base_price(
            bev_results, charging_options, selected_charging
        )
        min_val = max(0.05, base_value * 0.7)
        max_val = base_value * 1.3
        return self._create_range(min_val, max_val, base_value, round_digits=2)

    def calculate_vehicle_lifetime_range(self, base_value: int) -> List[int]:
        """Calculate range for vehicle lifetime parameter."""
        min_val = max(1, base_value - 3)
        max_val = base_value + 3
        param_range = list(range(int(min_val), int(max_val + 1)))
        if base_value not in param_range:
            param_range.append(base_value)
            param_range.sort()
        return param_range

    def calculate_discount_rate_range(self, base_value: float) -> List[float]:
        """Calculate range for discount rate parameter."""
        discount_base = base_value * 100  # Convert to percentage
        min_val = max(0.5, discount_base - 3)
        max_val = min(15, discount_base + 3)
        return self._create_range(min_val, max_val, discount_base, round_digits=1)

    def _create_range(
        self, min_val: float, max_val: float, base_value: float, round_digits: int
    ) -> List[float]:
        """Create parameter range with base value included."""
        step = (max_val - min_val) / (self.num_points - 1)
        param_range = [
            round(min_val + i * step, round_digits) for i in range(self.num_points)
        ]
        rounded_base = round(base_value, round_digits)
        if rounded_base not in param_range:
            param_range.append(rounded_base)
            param_range.sort()
        return param_range

    def _get_financial_param(
        self, financial_params: pd.DataFrame, param_key: str
    ) -> float:
        """Extract financial parameter value."""
        param_row = financial_params[
            financial_params[DataColumns.FINANCE_DESCRIPTION] == param_key
        ]
        if param_row.empty:
            raise ValueError(f"Financial parameter '{param_key}' not found")
        return param_row.iloc[0][DataColumns.FINANCE_DEFAULT_VALUE]

    def _get_electricity_base_price(
        self, bev_results: dict, charging_options: pd.DataFrame, selected_charging: int
    ) -> float:
        """Get electricity base price with fallback logic."""
        if "weighted_electricity_price" in bev_results:
            electricity_base = bev_results["weighted_electricity_price"]
            if electricity_base is not None and isinstance(
                electricity_base, (int, float)
            ):
                return electricity_base

        try:
            charging_row = charging_options[
                charging_options[DataColumns.CHARGING_ID] == selected_charging
            ]
            if not charging_row.empty:
                electricity_base = charging_row.iloc[0][DataColumns.PER_KWH_PRICE]
                if electricity_base is not None and isinstance(
                    electricity_base, (int, float)
                ):
                    return electricity_base
        except (IndexError, KeyError):
            pass

        return 0.20
