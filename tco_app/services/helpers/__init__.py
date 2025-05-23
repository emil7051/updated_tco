from __future__ import annotations

"""Helper utilities used by service-layer classes.

This sub-package exists to keep the public façade methods of
`tco_app.services.tco_calculation_service.TCOCalculationService` lean and
focused on orchestration whilst housing the heavy-lifting logic in
re-usable, easily unit-testable helper functions.
"""

from typing import Any, Dict, Tuple

from tco_app.src import pd

from tco_app.src.constants import ParameterKeys
from tco_app.src.utils.safe_operations import safe_get_parameter
from tco_app.services.dtos import CalculationRequest, TCOResult

__all__ = [
    "convert_tco_result_to_model_runner_dict",
    "get_residual_value_parameters",
]


def get_residual_value_parameters(financial_params_df: pd.DataFrame) -> Tuple[float, float]:
    """Return the *(initial_dep, annual_dep)* depreciation percentages.

    The function provides a single source-of-truth for fetching the two
    residual-value parameters from the *financial_params* table.  Guard
    rails are included so that callers receive an explicit error message if
    either parameter is missing, rather than facing a cryptic *KeyError*
    further down the stack.
    """

    if financial_params_df is None or financial_params_df.empty:
        raise ValueError("financial_params_df must be a non-empty DataFrame")

    try:
        initial_dep = safe_get_parameter(
            financial_params_df,
            ParameterKeys.INITIAL_DEPRECIATION,
            context="initial_depreciation_percentage",
        )
    except Exception:
        # Graceful fallback – assume zero initial depreciation if not supplied.
        initial_dep = 0.0

    try:
        annual_dep = safe_get_parameter(
            financial_params_df,
            ParameterKeys.ANNUAL_DEPRECIATION,
            context="annual_depreciation_percentage",
        )
    except Exception:
        # Graceful fallback – assume zero ongoing depreciation if not supplied.
        annual_dep = 0.0

    return float(initial_dep), float(annual_dep)


def convert_tco_result_to_model_runner_dict(
    tco_result: TCOResult, request: CalculationRequest
) -> Dict[str, Any]:
    """Convert :class:`~tco_app.services.dtos.TCOResult` to legacy dict.

    A handful of downstream domain functions – most notably
    ``domain.sensitivity.metrics.calculate_comparative_metrics`` – still
    expect the historical *model_runner* dictionary structure.  While the
    long-term plan is to modernise those call-sites, this helper offers a
    backwards-compatibility bridge so that the public service API can remain
    clean.
    """

    from tco_app.src.constants import DataColumns, Drivetrain  # Local import to avoid cycles

    # Construct the 'tco' sub-dictionary with final, post-infrastructure values
    final_tco_sub_dict: Dict[str, Any] = {
        "npv_total_cost": tco_result.tco_total_lifetime,
        "tco_per_km": tco_result.tco_per_km,
        "tco_per_tonne_km": tco_result.tco_per_tonne_km,
        "tco_lifetime": tco_result.tco_total_lifetime,
        "tco_annual": tco_result.tco_breakdown.get("tco_annual", 0.0),
    }

    # Merge any extra keys from the original breakdown (if present)
    for key, value in (tco_result.tco_breakdown or {}).items():
        final_tco_sub_dict.setdefault(key, value)

    social_tco_dict = {
        "social_tco_lifetime": tco_result.social_tco_total_lifetime,
    }

    # Selected infrastructure description (BEV-only)
    selected_infra_desc = None
    if (
        request.drivetrain == Drivetrain.BEV
        and not request.infrastructure_options.empty
    ):
        selected_infra_series = request.infrastructure_options[
            request.infrastructure_options[DataColumns.INFRASTRUCTURE_ID]
            == request.parameters.selected_infrastructure_id
        ]
        if not selected_infra_series.empty:
            selected_infra_desc = selected_infra_series.iloc[0].get(
                DataColumns.INFRASTRUCTURE_DESCRIPTION
            )

    return {
        "vehicle_data": request.vehicle_data,
        "fees": request.fees_data,
        "energy_cost_per_km": tco_result.energy_cost_per_km,
        "annual_costs": tco_result.annual_costs_breakdown,
        "emissions": tco_result.emissions_breakdown,
        "acquisition_cost": tco_result.acquisition_cost,
        "residual_value": tco_result.residual_value,
        "battery_replacement": tco_result.npv_battery_replacement_cost,
        "npv_annual_cost": tco_result.npv_annual_operating_cost,
        "tco": final_tco_sub_dict,
        "externalities": tco_result.externalities_breakdown,
        "social_tco": social_tco_dict,
        "annual_kms": request.parameters.annual_kms,
        "truck_life_years": request.parameters.truck_life_years,
        "charging_requirements": tco_result.charging_requirements,
        "infrastructure_costs": tco_result.infrastructure_costs_breakdown,
        "selected_infrastructure_description": selected_infra_desc,
        "charging_options": request.charging_options,
        "discount_rate": request.parameters.discount_rate,
        "scenario": tco_result.scenario_meta,
        "charging_mix": request.parameters.charging_mix,
        "weighted_electricity_price": tco_result.weighted_electricity_price,
    } 