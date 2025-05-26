from __future__ import annotations

"""Utility helpers for energy-related calculations.

These helpers are shared between UI layers (Streamlit) and deeper model
functions to guarantee a single, authoritative implementation for weighted
charging-mix calculations.
"""

import logging
from typing import Dict, Mapping

from tco_app.src import pd
from tco_app.src.constants import DataColumns
from tco_app.src.utils.safe_operations import safe_division

logger = logging.getLogger(__name__)

__all__ = [
    "weighted_electricity_price",
]


# _EPS is used as a guard against division-by-zero errors.
_EPS = 1e-12


def weighted_electricity_price(
    charging_mix: Mapping[int | str, float],
    charging_options: pd.DataFrame,
    *,
    id_column: str = DataColumns.CHARGING_ID,
    price_column: str = DataColumns.PER_KWH_PRICE,
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
    logger.debug(f"weighted_electricity_price called with charging_mix: {charging_mix}")
    logger.debug(
        f"charging_mix type: {type(charging_mix)}, keys: {list(charging_mix.keys()) if charging_mix else 'None'}"
    )

    if not charging_mix:
        return 0.0

    # Determine whether the mix is expressed in percentages (>1) or fractions.
    total = sum(charging_mix.values())
    if total < _EPS:
        return 0.0

    # Normalise to 1.0 regardless of original scale.
    normalised_mix: Dict[int | str, float] = {
        k: safe_division(v, total, context="v/total calculation")
        for k, v in charging_mix.items()
    }

    # Map each id to its price.
    prices = charging_options.set_index(id_column)[price_column]
    logger.debug(f"Prices index: {prices.index.tolist()}")

    weighted_price = 0.0
    for cid, weight in normalised_mix.items():
        logger.debug(f"Looking up charging ID: {cid} (type: {type(cid)})")
        try:
            price = float(prices.loc[cid])
        except KeyError as exc:
            logger.error(
                f"Failed to find charging ID {cid} in prices. Available IDs: {prices.index.tolist()}"
            )
            raise KeyError(
                f"Charging option with ID {cid!r} not found in charging_options table."
            ) from exc
        weighted_price += price * weight

    return weighted_price
