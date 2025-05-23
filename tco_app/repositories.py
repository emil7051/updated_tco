"""
Data Repositories for the TCO application.

These repositories will provide an abstraction layer for accessing data,
initially from in-memory DataFrames, but could be adapted for other sources.
"""

from tco_app.src import logging
from tco_app.src import pd, Dict, Any
from tco_app.src.exceptions import (
    VehicleNotFoundError,
)  # Assuming this exception exists


class VehicleRepository:
    def __init__(self, data_tables: Dict[str, pd.DataFrame]):
        self.vehicle_models_df = data_tables.get("vehicle_models", pd.DataFrame())
        self.vehicle_fees_df = data_tables.get("vehicle_fees", pd.DataFrame())

    def get_vehicle_by_id(self, vehicle_id: str) -> pd.Series:
        """Retrieve a vehicle's specification data by its ID."""
        if (
            self.vehicle_models_df.empty
            or "vehicle_id" not in self.vehicle_models_df.columns
        ):
            raise VehicleNotFoundError(
                f"Vehicle models data is empty or 'vehicle_id' column is missing."
            )

        vehicle_data = self.vehicle_models_df[
            self.vehicle_models_df["vehicle_id"] == vehicle_id
        ]
        if vehicle_data.empty:
            raise VehicleNotFoundError(
                f"Vehicle with ID '{vehicle_id}' not found in vehicle_models."
            )
        return vehicle_data.iloc[0]

    def get_fees_by_vehicle_id(self, vehicle_id: str) -> pd.Series:
        """Retrieve a vehicle's fee data by its ID."""
        if (
            self.vehicle_fees_df.empty
            or "vehicle_id" not in self.vehicle_fees_df.columns
        ):
            # Allow returning empty series if fees are optional or not always present for a vehicle
            return pd.Series(dtype=object)

        fees_data = self.vehicle_fees_df[
            self.vehicle_fees_df["vehicle_id"] == vehicle_id
        ]
        if fees_data.empty:
            # Return empty series if no fees found for this specific vehicle
            return pd.Series(dtype=object)
        return fees_data.iloc[0]


class ParametersRepository:
    def __init__(self, data_tables: Dict[str, pd.DataFrame]):
        self.data_tables = data_tables

    def get_charging_options(self) -> pd.DataFrame:
        return self.data_tables.get("charging_options", pd.DataFrame()).copy()

    def get_infrastructure_options(self) -> pd.DataFrame:
        return self.data_tables.get("infrastructure_options", pd.DataFrame()).copy()

    def get_financial_params(self) -> pd.DataFrame:
        # Assuming 'modified_tables' is handled by the caller before repo instantiation if needed,
        # or scenario application happens before data hits the repo.
        # For now, this repo provides base parameters.
        return self.data_tables.get("financial_params", pd.DataFrame()).copy()

    def get_battery_params(self) -> pd.DataFrame:
        return self.data_tables.get("battery_params", pd.DataFrame()).copy()

    def get_emission_factors(self) -> pd.DataFrame:
        return self.data_tables.get("emission_factors", pd.DataFrame()).copy()

    def get_externalities_data(self) -> pd.DataFrame:
        return self.data_tables.get(
            "externalities", pd.DataFrame()
        ).copy()  # Changed from 'externalities_data' to 'externalities' to match orchestrator

    def get_incentives(self) -> pd.DataFrame:
        return self.data_tables.get("incentives", pd.DataFrame()).copy()

    # Add methods to get specific parameters if needed, e.g.:
    # def get_diesel_price(self) -> float:
    #     financial_params = self.get_financial_params()
    #     # Logic to extract diesel price
    #     pass
