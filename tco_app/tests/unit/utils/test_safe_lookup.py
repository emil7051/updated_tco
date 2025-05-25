"""Tests for safe lookup operations."""

import pytest

from tco_app.src import pd
from tco_app.src.constants import DataColumns
from tco_app.src.exceptions import DataNotFoundError
from tco_app.src.utils.safe_operations import safe_iloc_zero, safe_lookup_vehicle


class TestSafeIlocZero:
    """Test safe_iloc_zero function."""

    @pytest.fixture
    def sample_df(self):
        """Sample DataFrame for testing."""
        return pd.DataFrame(
            {"id": ["A", "B", "C"], "value": [1, 2, 3], "category": ["X", "Y", "X"]}
        )

    def test_successful_lookup(self, sample_df):
        """Test successful row lookup."""
        condition = sample_df["id"] == "B"
        result = safe_iloc_zero(sample_df, condition, "test row")

        assert result["id"] == "B"
        assert result["value"] == 2
        assert result["category"] == "Y"

    def test_no_matching_rows(self, sample_df):
        """Test when no rows match the condition."""
        condition = sample_df["id"] == "NONEXISTENT"

        with pytest.raises(DataNotFoundError) as exc_info:
            safe_iloc_zero(sample_df, condition, "nonexistent row")

        assert "No nonexistent row found matching the condition" in str(exc_info.value)
        assert "DataFrame has 3 rows, 0 match condition" in str(exc_info.value)
        assert exc_info.value.dataframe_name == "nonexistent row"

    def test_multiple_matching_rows(self, sample_df):
        """Test when multiple rows match the condition."""
        condition = sample_df["category"] == "X"
        result = safe_iloc_zero(sample_df, condition, "X category")

        # Should return the first matching row
        assert result["id"] == "A"
        assert result["value"] == 1

    def test_empty_dataframe(self):
        """Test with empty DataFrame."""
        empty_df = pd.DataFrame(columns=["id", "value"])
        condition = pd.Series([], dtype=bool)

        with pytest.raises(DataNotFoundError):
            safe_iloc_zero(empty_df, condition, "empty data")


class TestSafeLookupVehicle:
    """Test safe_lookup_vehicle function."""

    @pytest.fixture
    def vehicle_df(self):
        """Sample vehicle DataFrame."""
        return pd.DataFrame(
            {
                DataColumns.VEHICLE_ID: ["VEH001", "VEH002", "VEH003"],
                DataColumns.VEHICLE_MODEL: ["Model A", "Model B", "Model C"],
                DataColumns.PAYLOAD_T: [2.0, 5.0, 8.0],
            }
        )

    def test_successful_vehicle_lookup(self, vehicle_df):
        """Test successful vehicle lookup."""
        result = safe_lookup_vehicle(vehicle_df, "VEH002")

        assert result[DataColumns.VEHICLE_ID] == "VEH002"
        assert result[DataColumns.VEHICLE_MODEL] == "Model B"
        assert result[DataColumns.PAYLOAD_T] == 5.0

    def test_vehicle_not_found(self, vehicle_df):
        """Test when vehicle is not found."""
        with pytest.raises(DataNotFoundError) as exc_info:
            safe_lookup_vehicle(vehicle_df, "NONEXISTENT")

        error_msg = str(exc_info.value)
        assert "vehicle with ID 'NONEXISTENT'" in error_msg
        assert "Available IDs:" in error_msg
        assert "VEH001" in error_msg

    def test_empty_vehicle_dataframe(self):
        """Test with empty vehicle DataFrame."""
        empty_df = pd.DataFrame(
            columns=[DataColumns.VEHICLE_ID, DataColumns.VEHICLE_MODEL]
        )

        with pytest.raises(DataNotFoundError):
            safe_lookup_vehicle(empty_df, "ANY_ID")
