"""Service for applying scenario modifications to data."""

from typing import Dict, Any, List
from tco_app.src import logging
from tco_app.src import pd
from dataclasses import dataclass

from tco_app.src.constants import DataColumns
from tco_app.src.exceptions import ScenarioError

logger = logging.getLogger(__name__)


@dataclass
class ScenarioModification:
    """Represents a single parameter modification."""

    table_name: str
    parameter_name: str
    parameter_value: Any
    vehicle_type: str = "All"
    vehicle_drivetrain: str = "All"


class ScenarioApplicationService:
    """Service for applying scenario modifications to data tables."""

    def __init__(self):
        """Initialise scenario application service."""
        self.applied_modifications = []

    def parse_scenario_params(
        self, scenario_params: pd.DataFrame
    ) -> List[ScenarioModification]:
        """Parse scenario parameters into modification objects.

        Args:
            scenario_params: DataFrame with scenario modifications

        Returns:
            List of modification objects
        """
        modifications = []

        for _, row in scenario_params.iterrows():
            mod = ScenarioModification(
                table_name=row["parameter_table"],
                parameter_name=row["parameter_name"],
                parameter_value=row["parameter_value"],
                vehicle_type=row.get("vehicle_type", "All"),
                vehicle_drivetrain=row.get("vehicle_drivetrain", "All"),
            )
            modifications.append(mod)

        return modifications

    def apply_modifications(
        self,
        data_tables: Dict[str, pd.DataFrame],
        modifications: List[ScenarioModification],
        target_vehicle_type: str = None,
        target_drivetrain: str = None,
    ) -> Dict[str, pd.DataFrame]:
        """Apply scenario modifications to data tables.

        Args:
            data_tables: Original data tables
            modifications: List of modifications to apply
            target_vehicle_type: Filter modifications by vehicle type
            target_drivetrain: Filter modifications by drivetrain

        Returns:
            Modified data tables (copies)
        """
        # Create deep copies
        modified_tables = {name: df.copy() for name, df in data_tables.items()}

        for mod in modifications:
            # Check if modification applies
            if not self._should_apply_modification(
                mod, target_vehicle_type, target_drivetrain
            ):
                continue

            # Apply modification
            try:
                self._apply_single_modification(modified_tables, mod)
                self.applied_modifications.append(mod)
            except Exception as e:
                logger.error(f"Failed to apply modification {mod}: {e}")
                raise ScenarioError(
                    f"Failed to apply scenario modification: {str(e)}"
                ) from e

        return modified_tables

    def apply_scenario_by_id(
        self,
        scenario_id: str,
        data_tables: Dict[str, pd.DataFrame],
        target_vehicle_type: str = None,
        target_drivetrain: str = None,
    ) -> Dict[str, pd.DataFrame]:
        """Apply scenario modifications by scenario ID.

        Args:
            scenario_id: Scenario ID to apply
            data_tables: Original data tables
            target_vehicle_type: Filter modifications by vehicle type
            target_drivetrain: Filter modifications by drivetrain

        Returns:
            Modified data tables (copies)
        """
        scenario_params = data_tables.get("scenario_params")
        if scenario_params is None:
            logger.warning("No scenario_params table found")
            return {name: df.copy() for name, df in data_tables.items()}

        # Filter scenario parameters by ID
        selected_params = scenario_params[scenario_params["scenario_id"] == scenario_id]

        if selected_params.empty:
            logger.info(f"No parameters found for scenario {scenario_id}")
            return {name: df.copy() for name, df in data_tables.items()}

        # Parse and apply modifications
        modifications = self.parse_scenario_params(selected_params)
        return self.apply_modifications(
            data_tables, modifications, target_vehicle_type, target_drivetrain
        )

    def _should_apply_modification(
        self,
        mod: ScenarioModification,
        target_vehicle_type: str,
        target_drivetrain: str,
    ) -> bool:
        """Check if modification should be applied."""
        # Vehicle type check
        if (
            mod.vehicle_type != "All"
            and target_vehicle_type
            and mod.vehicle_type != target_vehicle_type
        ):
            return False

        # Drivetrain check
        if (
            mod.vehicle_drivetrain != "All"
            and target_drivetrain
            and mod.vehicle_drivetrain != target_drivetrain
        ):
            return False

        return True

    def _apply_single_modification(
        self, tables: Dict[str, pd.DataFrame], mod: ScenarioModification
    ) -> None:
        """Apply a single modification to tables."""
        if mod.table_name not in tables:
            raise ScenarioError(f"Table '{mod.table_name}' not found in data tables")

        table = tables[mod.table_name]

        # Route to appropriate handler
        if mod.table_name == "financial_params":
            self._apply_financial_param(table, mod)
        elif mod.table_name == "battery_params":
            self._apply_battery_param(table, mod)
        elif mod.table_name == "vehicle_models":
            self._apply_vehicle_modifier(table, mod)
        elif mod.table_name == "incentives":
            self._apply_incentive_modifier(table, mod)
        else:
            logger.warning(f"No handler for table '{mod.table_name}'")

    def _apply_financial_param(
        self, table: pd.DataFrame, mod: ScenarioModification
    ) -> None:
        """Apply modification to financial parameters."""
        mask = table[DataColumns.FINANCE_DESCRIPTION] == mod.parameter_name
        if mask.any():
            table.loc[mask, DataColumns.FINANCE_DEFAULT_VALUE] = mod.parameter_value
            logger.debug(
                f"Applied financial parameter: {mod.parameter_name} = {mod.parameter_value}"
            )
        else:
            # Handle special case for diesel_default_price -> diesel_price mapping
            if mod.parameter_name == "diesel_default_price":
                mask = table[DataColumns.FINANCE_DESCRIPTION] == "diesel_price"
                if mask.any():
                    table.loc[mask, DataColumns.FINANCE_DEFAULT_VALUE] = (
                        mod.parameter_value
                    )
                    logger.debug(
                        f"Applied diesel_default_price to diesel_price: {mod.parameter_value}"
                    )
                else:
                    logger.warning(
                        "Financial parameter 'diesel_price' not found for diesel_default_price"
                    )
            else:
                logger.warning(f"Financial parameter '{mod.parameter_name}' not found")

    def _apply_battery_param(
        self, table: pd.DataFrame, mod: ScenarioModification
    ) -> None:
        """Apply modification to battery parameters."""
        mask = table[DataColumns.BATTERY_DESCRIPTION] == mod.parameter_name
        if mask.any():
            table.loc[mask, DataColumns.BATTERY_DEFAULT_VALUE] = mod.parameter_value
            logger.debug(
                f"Applied battery parameter: {mod.parameter_name} = {mod.parameter_value}"
            )
        else:
            logger.warning(f"Battery parameter '{mod.parameter_name}' not found")

    def _apply_vehicle_modifier(
        self, table: pd.DataFrame, mod: ScenarioModification
    ) -> None:
        """Apply modification to vehicle models."""
        # Build mask for target vehicles
        mask = table[DataColumns.VEHICLE_DRIVETRAIN] == mod.vehicle_drivetrain
        if mod.vehicle_type != "All":
            mask &= table[DataColumns.VEHICLE_TYPE] == mod.vehicle_type

        if not mask.any():
            logger.warning(
                f"No vehicles found for type '{mod.vehicle_type}' and drivetrain '{mod.vehicle_drivetrain}'"
            )
            return

        # Apply modifier based on parameter name
        if mod.parameter_name == "msrp_price_modifier":
            for idx in table[mask].index:
                original_value = table.at[idx, DataColumns.MSRP_PRICE]
                table.at[idx, DataColumns.MSRP_PRICE] = (
                    original_value * mod.parameter_value
                )

        elif mod.parameter_name == "kwh_per100km_modifier":
            for idx in table[mask].index:
                original_value = table.at[idx, DataColumns.KWH_PER100KM]
                table.at[idx, DataColumns.KWH_PER100KM] = (
                    original_value * mod.parameter_value
                )

        elif mod.parameter_name == "range_km_modifier":
            for idx in table[mask].index:
                original_value = table.at[idx, DataColumns.RANGE_KM]
                table.at[idx, DataColumns.RANGE_KM] = (
                    original_value * mod.parameter_value
                )

        else:
            logger.warning(f"Unknown vehicle modifier: {mod.parameter_name}")
            return

        logger.debug(
            f"Applied vehicle modifier {mod.parameter_name} = {mod.parameter_value} "
            f"to {mask.sum()} vehicles"
        )

    def _apply_incentive_modifier(
        self, table: pd.DataFrame, mod: ScenarioModification
    ) -> None:
        """Apply modification to incentives."""
        if "." not in mod.parameter_name:
            logger.warning(f"Invalid incentive parameter format: {mod.parameter_name}")
            return

        incentive_type, incentive_field = mod.parameter_name.split(".", 1)

        # Build mask for target incentives
        mask = table["incentive_type"] == incentive_type
        if mod.vehicle_type != "All":
            mask &= table["vehicle_type"] == mod.vehicle_type
        if mod.vehicle_drivetrain != "All":
            mask &= table["drivetrain"] == mod.vehicle_drivetrain

        if mask.any():
            for idx in table[mask].index:
                table.at[idx, incentive_field] = mod.parameter_value
            logger.debug(
                f"Applied incentive {incentive_type}.{incentive_field} = {mod.parameter_value} "
                f"to {mask.sum()} incentive entries"
            )
        else:
            logger.warning(
                f"No matching incentive for {incentive_type} "
                f"VT={mod.vehicle_type} DR={mod.vehicle_drivetrain}"
            )

    def get_applied_modifications(self) -> List[ScenarioModification]:
        """Get list of modifications that were applied."""
        return self.applied_modifications.copy()

    def clear_applied_modifications(self) -> None:
        """Clear the list of applied modifications."""
        self.applied_modifications.clear()
