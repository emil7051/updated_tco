"""Context director for orchestrating UI context building."""

from tco_app.src import Dict, Any
from tco_app.src import pd
from tco_app.src import st

from tco_app.src.constants import Drivetrain, DataColumns
from tco_app.services.scenario_service import apply_scenario_parameters
from tco_app.ui.builders import (
    ScenarioBuilder,
    VehicleSelectionBuilder,
    ParameterInputBuilder,
    ChargingConfigurationBuilder,
    InfrastructureBuilder,
)


class ContextDirector:
    """Orchestrates context building using the builder pattern."""

    def __init__(self, data_tables: Dict[str, pd.DataFrame]):
        self.data_tables = data_tables
        self.builders = []

    def build_ui_context(self) -> Dict[str, Any]:
        """Build complete UI context using all builders."""
        context = {}

        with st.sidebar:
            st.header("Configuration")

            # Step 1: Scenario selection
            scenario_builder = ScenarioBuilder(self.data_tables)
            scenario_ctx = scenario_builder.select_scenario().build()
            context.update(scenario_ctx)

            # Step 2: Vehicle selection
            vehicle_builder = VehicleSelectionBuilder(self.data_tables)
            vehicle_ctx = vehicle_builder.select_vehicles().build()
            context.update(vehicle_ctx)

            # Apply scenario parameters now that we have vehicle type
            modified_tables = apply_scenario_parameters(
                scenario_ctx["scenario_id"],
                self.data_tables,
                vehicle_ctx[DataColumns.VEHICLE_TYPE],
                Drivetrain.ALL,
            )

            # Step 3: Parameter inputs
            param_builder = ParameterInputBuilder(
                self.data_tables, vehicle_ctx[DataColumns.VEHICLE_TYPE]
            )
            param_ctx = (
                param_builder.collect_operating_parameters()
                .collect_financial_parameters(modified_tables["financial_params"])
                .collect_battery_parameters(modified_tables["battery_params"])
                .build()
            )
            context.update(param_ctx)

            # Step 4: Charging configuration
            charging_builder = ChargingConfigurationBuilder(self.data_tables)
            charging_ctx = charging_builder.configure_charging().build()
            context.update(charging_ctx)

            # Step 5: Infrastructure configuration
            infra_builder = InfrastructureBuilder(self.data_tables)
            infra_ctx = infra_builder.configure_infrastructure().build()
            context.update(infra_ctx)

        # Store modified tables for calculations
        context["modified_tables"] = modified_tables

        return context
