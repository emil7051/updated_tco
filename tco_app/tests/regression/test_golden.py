"""Golden regression tests ensuring key utilities remain stable across refactors."""

import math
from typing import List

import pytest

from tco_app.src import pd
from tco_app.src.utils.energy import weighted_electricity_price
from tco_app.src.utils.finance import (
    calculate_residual_value,
    cumulative_cost_curve,
    npv_constant,
    price_parity_year,
)

# ---------------------------------------------------------------------------
# Net-present-value (constant annuity) ‑ 6 representative scenarios
# ---------------------------------------------------------------------------

NPV_CASES = [
    (10_000, 0.07, 10),
    (5_000, 0.0, 5),  # zero discount edge-case
    (12_345, 0.10, 8),
    (7_500, 0.03, 15),
    (0, 0.05, 10),  # zero cash-flow edge-case
    (1_000, 0.05, 0),  # zero years edge-case
]


def _pv_formula(annual: float, rate: float, years: int) -> float:
    """Reference implementation independent of `npv_constant`."""
    if years <= 0:
        return 0.0
    if rate == 0:
        return annual * years
    factor = (1 - (1 + rate) ** (-years)) / rate
    return annual * factor


@pytest.mark.parametrize("annual,rate,years", NPV_CASES)
def test_npv_constant_golden(annual: float, rate: float, years: int):
    """`npv_constant` must equal closed-form PV formula."""
    expected = _pv_formula(annual, rate, years)
    assert math.isclose(npv_constant(annual, rate, years), expected, rel_tol=1e-9)


# ---------------------------------------------------------------------------
# Weighted electricity price – 3 scenarios
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "mix,prices,expected",
    [
        (
            {"A": 0.25, "B": 0.75},
            pd.DataFrame(
                [
                    {"charging_id": "A", "per_kwh_price": 0.20},
                    {"charging_id": "B", "per_kwh_price": 0.40},
                ]
            ),
            0.20 * 0.25 + 0.40 * 0.75,
        ),
        (
            {"Fast": 0.5, "Depot": 0.5},
            pd.DataFrame(
                [
                    {"charging_id": "Fast", "per_kwh_price": 0.60},
                    {"charging_id": "Depot", "per_kwh_price": 0.28},
                ]
            ),
            (0.60 + 0.28) / 2,
        ),
        (
            {"X": 1.0},
            pd.DataFrame([{"charging_id": "X", "per_kwh_price": 0.35}]),
            0.35,
        ),
    ],
)
def test_weighted_electricity_price_golden(mix, prices, expected):
    assert math.isclose(
        weighted_electricity_price(mix, prices), expected, rel_tol=1e-12
    )


# ---------------------------------------------------------------------------
# Price parity year – synthetic curves (2 cases)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bev_curve,diesel_curve,expected",
    [
        ([100, 200, 300], [300, 200, 100], 2.0),  # equal at year 2
        ([100, 300, 500], [450, 250, 50], 1.875),  # fractional crossing within year 2
    ],
)
def test_price_parity_year_golden(
    bev_curve: List[float], diesel_curve: List[float], expected: float
):
    assert math.isclose(
        price_parity_year(bev_curve, diesel_curve), expected, rel_tol=1e-9
    )


# ---------------------------------------------------------------------------
# Cumulative cost curve & residual value – smoke coverage
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "initial,annual,years",
    [(50_000, 10_000, 5), (0, 7_500, 3), (123_456, 0, 4)],
)
def test_cumulative_cost_curve_length(initial: float, annual: float, years: int):
    curve = cumulative_cost_curve(initial, annual, years)
    assert len(curve) == years
    # Check first and last values intuitively
    expected_last = initial + annual * (years - 1)
    assert math.isclose(curve[-1], expected_last, rel_tol=1e-9)


def test_calculate_residual_value_basic():
    vehicle = {"msrp_price": 100_000}
    res = calculate_residual_value(
        vehicle, years=5, initial_depreciation=0.1, annual_depreciation=0.05
    )
    expected_after_initial = 100_000 * (1 - 0.1)
    expected = expected_after_initial * ((1 - 0.05) ** 4)
    assert math.isclose(res, expected, rel_tol=1e-9)
