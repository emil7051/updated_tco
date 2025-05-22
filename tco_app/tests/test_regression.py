"""Regression tests to ensure outputs remain identical after util refactor."""
import math

import pandas as pd
import pytest

from tco_app.domain.finance import calculate_npv
from tco_app.src.utils import finance as fin
from tco_app.src.utils import energy as en


@pytest.mark.parametrize("annual_cost, discount_rate, years", [(10_000, 0.07, 10), (5_000, 0.0, 5), (0, 0.05, 15)])
def test_npv_constant_matches_original(annual_cost, discount_rate, years):
    """The wrapped `calc.calculate_npv` must equal `fin.npv_constant`."""
    assert math.isclose(
        calculate_npv(annual_cost, discount_rate, years),
        fin.npv_constant(annual_cost, discount_rate, years),
        rel_tol=1e-9,
    )


def test_weighted_electricity_price_basic():
    """Verify weighted price calculation matches manual expectation."""
    data = pd.DataFrame(
        [
            {"charging_id": "A", "per_kwh_price": 0.20},
            {"charging_id": "B", "per_kwh_price": 0.40},
        ]
    )
    mix = {"A": 0.25, "B": 0.75}
    expected = 0.20 * 0.25 + 0.40 * 0.75
    assert math.isclose(
        en.weighted_electricity_price(mix, data), expected, rel_tol=1e-9
    ) 