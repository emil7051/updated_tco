"""Utility helpers for energy-related calculations.

These helpers are shared between UI layers (Streamlit) and deeper model
functions to guarantee a single, authoritative implementation for weighted
charging-mix calculations.
"""
from __future__ import annotations

from typing import Dict, Mapping

import pandas as pd

__all__ = [
    "weighted_electricity_price",
]


# _EPS is used as a guard against division-by-zero errors.
_EPS = 1e-12


def weighted_electricity_price(
    charging_mix: Mapping[int | str, float],
    charging_options: pd.DataFrame,
    *,
    id_column: str = "charging_id",
    price_column: str = "per_kwh_price",
) -> float:  # noqa: D401
    """Return the weighted average electricity price for a charging mix.

    Parameters
    ----------
    charging_mix
        Mapping of ``charging_id`` → proportion. Proportions can either be in
        decimal form (0-1) or percentage form (0-100). The function will
        automatically normalise the values, so they do **not** need to sum to
        unity/100.
    charging_options
        DataFrame that contains at least ``id_column`` & ``price_column``.
    id_column, price_column
        Column names for the identifier and price respectively.
    """
    if not charging_mix:
        return 0.0

    # Determine whether the mix is expressed in percentages (>1) or fractions.
    total = sum(charging_mix.values())
    if total < _EPS:
        return 0.0

    # Normalise to 1.0 regardless of original scale.
    normalised_mix: Dict[int | str, float] = {k: v / total for k, v in charging_mix.items()}

    # Map each id to its price.
    prices = charging_options.set_index(id_column)[price_column]

    weighted_price = 0.0
    for cid, weight in normalised_mix.items():
        try:
            price = float(prices.loc[cid])
        except KeyError as exc:
            raise KeyError(
                f"Charging option with ID {cid!r} not found in charging_options table."
            ) from exc
        weighted_price += price * weight

    return weighted_price 