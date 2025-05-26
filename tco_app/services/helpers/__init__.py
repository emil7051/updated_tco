from __future__ import annotations

"""Helper utilities used by service-layer classes.

This sub-package exists to keep the public façade methods of
`tco_app.services.tco_calculation_service.TCOCalculationService` lean and
focused on orchestration whilst housing the heavy-lifting logic in
re-usable, easily unit-testable helper functions.
"""

from typing import Any, Dict, Tuple

from tco_app.services.dtos import CalculationRequest, TCOResult
from tco_app.src import pd
from tco_app.src.constants import ParameterKeys
from tco_app.src.utils.safe_operations import safe_get_parameter

__all__ = [
    "get_residual_value_parameters",
]


def get_residual_value_parameters(
    financial_params_df: pd.DataFrame,
) -> Tuple[float, float]:
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
