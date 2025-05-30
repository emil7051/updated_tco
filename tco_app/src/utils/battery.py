"""Battery-related helper functions shared across the codebase.

This module centralises all battery-specific economic calculations so that the
implementation is never duplicated between the Streamlit UI, the core model
and any future notebooks.
"""

from __future__ import annotations

import math
from typing import List, Union

from tco_app.src import pd
from tco_app.src.constants import DataColumns, Drivetrain, ParameterKeys

__all__ = [
    "calculate_battery_replacement",
]


def calculate_battery_replacement(
    vehicle_data: Union[pd.Series, dict],
    battery_params: Union[pd.DataFrame, List[dict]],
    truck_life_years: int,
    discount_rate: float,
) -> float:  # noqa: D401
    """Return the **net present value** of any battery replacement.

    The function follows the same assumptions that were previously implemented
    inside *calculations.py* but moves the logic to a single, shared location.

    Parameters
    ----------
    vehicle_data
        Row/record with at least ``vehicle_drivetrain`` (matching
        :class:`~tco_app.src.constants.Drivetrain` values),
        ``battery_capacity_kwh`` and other descriptive columns.
    battery_params
        Table containing *replacement_per_kwh_price*,
        *degradation_annual_percent* and *minimum_capacity_percent* rows.
    truck_life_years
        Economic life of the truck.
    discount_rate
        Real discount rate as a decimal (e.g. 0.07 for 7 %).
    """

    # Battery replacements only apply to BEVs.
    if vehicle_data[DataColumns.VEHICLE_DRIVETRAIN.value] != Drivetrain.BEV:
        return 0.0

    # ------------------------------------------------------------------
    # Normalise `battery_params` to a DataFrame.
    # ------------------------------------------------------------------

    if isinstance(battery_params, list):
        # A list of dictionaries was supplied (as used in certain legacy unit
        # tests). Convert it on-the-fly.
        battery_params = pd.DataFrame(battery_params)

    if not isinstance(battery_params, pd.DataFrame):
        raise TypeError(
            "battery_params must be a pandas DataFrame or a list of dictionaries"
        )

    # Extract required parameters from the table – these rows should always be
    # present; if not, a KeyError will be raised which is **expected** and
    # should be caught upstream.
    replacement_cost_per_kwh = battery_params[
        battery_params[DataColumns.BATTERY_DESCRIPTION.value]
        == ParameterKeys.REPLACEMENT_COST.value
    ].iloc[0][DataColumns.BATTERY_DEFAULT_VALUE.value]

    degradation_rate = battery_params[
        battery_params[DataColumns.BATTERY_DESCRIPTION.value]
        == ParameterKeys.DEGRADATION_RATE.value
    ].iloc[0][DataColumns.BATTERY_DEFAULT_VALUE.value]

    min_capacity = battery_params[
        battery_params[DataColumns.BATTERY_DESCRIPTION.value]
        == ParameterKeys.MINIMUM_CAPACITY.value
    ].iloc[0][DataColumns.BATTERY_DEFAULT_VALUE.value]

    # Determine when the battery will reach the minimum acceptable capacity.
    # The formula rearranges: capacity = (1-d)^t  →  t = ln(capacity) / ln(1-d)
    years_until_replacement = math.log(min_capacity) / math.log(1 - degradation_rate)

    # If the degradation horizon is beyond the truck life, no replacement
    # occurs within the project horizon.
    if years_until_replacement > truck_life_years:
        return 0.0

    # Up-front replacement cost.
    replacement_cost = (
        vehicle_data[DataColumns.BATTERY_CAPACITY_KWH.value] * replacement_cost_per_kwh
    )

    # Discount the future replacement back to present value.
    npv_replacement = replacement_cost / (
        (1 + discount_rate) ** years_until_replacement
    )

    return npv_replacement
