"""Tests for safe parameter operations."""

import pytest
from tco_app.src import pd

from tco_app.src.exceptions import DataNotFoundError
from tco_app.src.utils.safe_operations import (
    validate_dataframe_columns,
    safe_get_parameter,
    safe_get_charging_option,
)
from tco_app.src.constants import DataColumns, ParameterKeys


class TestValidateDataFrameColumns:
    """Test validate_dataframe_columns function."""

    @pytest.fixture
    def sample_df(self):
        """Sample DataFrame with known columns."""
        return pd.DataFrame(
            {"col1": [1, 2, 3], "col2": ["a", "b", "c"], "col3": [True, False, True]}
        )

    def test_all_columns_present(self, sample_df):
        """Test when all required columns are present."""
        # Should not raise any exception
        validate_dataframe_columns(sample_df, ["col1", "col2"], "test DataFrame")

    def test_single_missing_column(self, sample_df):
        """Test when one required column is missing."""
        with pytest.raises(ValueError) as exc_info:
            validate_dataframe_columns(
                sample_df, ["col1", "missing_col"], "test DataFrame"
            )

        error_msg = str(exc_info.value)
        assert (
            "test DataFrame is missing required columns: {'missing_col'}" in error_msg
        )
        assert "Available columns: ['col1', 'col2', 'col3']" in error_msg

    def test_multiple_missing_columns(self, sample_df):
        """Test when multiple required columns are missing."""
        with pytest.raises(ValueError) as exc_info:
            validate_dataframe_columns(
                sample_df, ["col1", "missing1", "missing2"], "test DataFrame"
            )

        error_msg = str(exc_info.value)
        assert "missing required columns:" in error_msg
        assert "missing1" in error_msg
        assert "missing2" in error_msg

    def test_empty_required_columns(self, sample_df):
        """Test with empty required columns list."""
        # Should not raise any exception
        validate_dataframe_columns(sample_df, [], "test DataFrame")


class TestSafeGetParameter:
    """Test safe_get_parameter function."""

    @pytest.fixture
    def financial_params_df(self):
        """Sample financial parameters DataFrame."""
        return pd.DataFrame(
            {
                DataColumns.FINANCE_DESCRIPTION: [
                    ParameterKeys.DIESEL_PRICE,
                    ParameterKeys.DISCOUNT_RATE,
                    ParameterKeys.CARBON_PRICE,
                ],
                DataColumns.FINANCE_DEFAULT_VALUE: [2.0, 0.07, 0.0],
            }
        )

    def test_successful_parameter_lookup(self, financial_params_df):
        """Test successful parameter lookup."""
        result = safe_get_parameter(financial_params_df, ParameterKeys.DIESEL_PRICE)
        assert result == 2.0

    def test_parameter_not_found(self, financial_params_df):
        """Test when parameter is not found."""
        with pytest.raises(DataNotFoundError) as exc_info:
            safe_get_parameter(financial_params_df, "NONEXISTENT_PARAM")

        assert "financial parameter 'NONEXISTENT_PARAM'" in str(exc_info.value)

    def test_custom_context(self, financial_params_df):
        """Test with custom context message."""
        with pytest.raises(DataNotFoundError) as exc_info:
            safe_get_parameter(
                financial_params_df, "MISSING", context="custom parameter"
            )

        assert "custom parameter 'MISSING'" in str(exc_info.value)


class TestSafeGetChargingOption:
    """Test safe_get_charging_option function."""

    @pytest.fixture
    def charging_data_df(self):
        """Sample charging data DataFrame."""
        return pd.DataFrame(
            {
                DataColumns.CHARGING_ID: ["CHG001", "CHG002", "CHG003"],
                DataColumns.PER_KWH_PRICE: [0.25, 0.30, 0.35],
            }
        )

    def test_successful_charging_lookup(self, charging_data_df):
        """Test successful charging option lookup."""
        result = safe_get_charging_option(charging_data_df, "CHG002")

        assert result[DataColumns.CHARGING_ID] == "CHG002"
        assert result[DataColumns.PER_KWH_PRICE] == 0.30

    def test_charging_option_not_found(self, charging_data_df):
        """Test when charging option is not found."""
        with pytest.raises(DataNotFoundError) as exc_info:
            safe_get_charging_option(charging_data_df, "NONEXISTENT")

        assert "charging option with ID 'NONEXISTENT'" in str(exc_info.value)
