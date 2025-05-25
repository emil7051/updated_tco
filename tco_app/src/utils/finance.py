"""Utility functions for financial calculations used across the TCO application.

This module centralises reusable finance-related maths to avoid code duplication.
All helper functions are intentionally kept free of third-party dependencies
(other than the Python standard library) to ensure they can be imported from
anywhere in the codebase without side-effects.

Functions
---------
npv_constant(annual_cost, discount_rate, years)
    Net present value of a constant annual cash-flow occurring at the end of
    each period.

cumulative_cost_curve(initial_cost, annual_cost, years)
    Simple cumulative cost curve given a one-off up-front expense plus a
    recurring constant annual cost.

price_parity_year(bev_curve, diesel_curve, years=None)
    Year at which two cumulative cost curves intersect (price parity). Uses
    linear interpolation between yearly observations to estimate fractional
    years.

calculate_residual_value(vehicle_data, years, initial_depreciation, annual_depreciation)
    Return the residual value of a vehicle after *years* years.
"""

from __future__ import annotations
from tco_app.src.constants import DataColumns

from math import inf
from typing import Iterable, List, Sequence, Any

__all__ = [
    "npv_constant",
    "cumulative_cost_curve",
    "price_parity_year",
    "calculate_residual_value",
]


def npv_constant(
    annual_cost: float, discount_rate: float, years: int
) -> float:  # noqa: D401
    """Return the net present value of a constant yearly cost.

    The cash-flow is assumed to be paid at the end of each year.

    Parameters
    ----------
    annual_cost
        Constant cash-flow (positive values represent costs).
    discount_rate
        Real discount rate expressed as a decimal (e.g. 0.07 for 7 %).
    years
        Number of years (positive integer).
    """
    if years <= 0:
        return 0.0

    if discount_rate == 0:  # Avoid division by zero; simple multiplication suffices
        return annual_cost * years

    npv = 0.0
    for year in range(1, years + 1):
        npv += annual_cost / ((1 + discount_rate) ** year)
    return npv


def cumulative_cost_curve(
    initial_cost: float,
    annual_cost: float,
    years: int,
) -> List[float]:
    """Return a list with cumulative costs for each year.

    ``years`` entries are returned where element *i* corresponds to the end of
    year *i + 1* when using one-based year notation.
    """
    curve = [initial_cost]
    for _ in range(1, years):
        curve.append(curve[-1] + annual_cost)
    return curve


def price_parity_year(
    bev_curve: Sequence[float],
    diesel_curve: Sequence[float],
    years: Iterable[int] | None = None,
) -> float:
    """Estimate the year at which BEV and diesel cumulative costs are equal.

    Parameters
    ----------
    bev_curve, diesel_curve
        Cumulative cost observations for each year. Both sequences **must** be
        the same length.
    years
        Optional iterable with the associated year numbers (1-indexed). If
        omitted, it defaults to ``range(1, len(bev_curve) + 1)``.

    Returns
    -------
    float
        Fractional year at parity or ``math.inf`` if the curves never
        intersect within the supplied horizon.
    """
    if len(bev_curve) != len(diesel_curve):
        raise ValueError("Cost curves must be the same length to compute parity.")

    if years is None:
        years = range(1, len(bev_curve) + 1)
    else:
        years = list(years)
        if len(years) != len(bev_curve):
            raise ValueError("Length of *years* must match cost curves.")

    parity = inf

    for i in range(len(bev_curve) - 1):
        bev1, bev2 = bev_curve[i], bev_curve[i + 1]
        diesel1, diesel2 = diesel_curve[i], diesel_curve[i + 1]

        # Detect a sign change in the difference between curves → intersection.
        if (bev1 - diesel1) * (bev2 - diesel2) <= 0:
            # Linear interpolation between the two points.
            delta_bev = bev2 - bev1
            delta_diesel = diesel2 - diesel1
            denominator = delta_bev - delta_diesel
            if denominator == 0:  # Parallel over this segment; skip.
                continue
            t = (diesel1 - bev1) / denominator
            parity = years[i] + t  # Fractional year value.
            break

    return parity


def calculate_residual_value(
    vehicle_data: Any,
    years: int,
    initial_depreciation: float,
    annual_depreciation: float,
) -> float:  # noqa: D401
    """Return the residual value of a vehicle after *years* years.

    The formula mirrors the one formerly present in ``calculations.py``.
    """

    if years <= 0:
        return 0.0

    value_after_initial = vehicle_data[DataColumns.MSRP_PRICE] * (
        1 - initial_depreciation
    )
    return value_after_initial * ((1 - annual_depreciation) ** (years - 1))
