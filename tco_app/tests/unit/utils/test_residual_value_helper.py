from tco_app.src import pd
import pytest

from tco_app.services.helpers import get_residual_value_parameters
from tco_app.src.constants import ParameterKeys, DataColumns


def _build_financial_params_df(initial: float = 0.2, annual: float = 0.1):
    """Utility to build a minimal financial_params DataFrame for tests."""
    return pd.DataFrame({
        DataColumns.FINANCE_DESCRIPTION: [
            ParameterKeys.INITIAL_DEPRECIATION,
            ParameterKeys.ANNUAL_DEPRECIATION,
        ],
        DataColumns.FINANCE_DEFAULT_VALUE: [initial, annual],
    })


def test_get_residual_value_parameters_success():
    df = _build_financial_params_df(0.25, 0.12)
    init_dep, annual_dep = get_residual_value_parameters(df)
    assert init_dep == pytest.approx(0.25)
    assert annual_dep == pytest.approx(0.12)


def test_get_residual_value_parameters_missing_key_defaults():
    # Remove annual depreciation row to trigger fallback to 0.0
    df = _build_financial_params_df().loc[lambda x: x[DataColumns.FINANCE_DESCRIPTION] != ParameterKeys.ANNUAL_DEPRECIATION]
    init_dep, annual_dep = get_residual_value_parameters(df)
    assert init_dep == pytest.approx(0.2)
    assert annual_dep == pytest.approx(0.0) 