"""Sidebar renderer for collecting user inputs.

This module handles the rendering of sidebar inputs independently from context building,
ensuring they remain visible when switching between pages.
"""

from __future__ import annotations

from tco_app.services.scenario_service import apply_scenario_parameters
from tco_app.src import Any, Dict, pd, st
from tco_app.src.constants import DataColumns, Drivetrain
from tco_app.ui.builders import (
    ChargingConfigurationBuilder,
    InfrastructureBuilder,
    ParameterInputBuilder,
    ScenarioBuilder,
    VehicleSelectionBuilder,
)


class SidebarRenderer:
    """Handles rendering of sidebar inputs and returns collected values."""

    def __init__(self, data_tables: Dict[str, pd.DataFrame]):
        self.data_tables = data_tables

    def render_and_collect_inputs(self) -> Dict[str, Any]:
        """Render sidebar inputs and return collected values."""
        inputs = {}

        with st.sidebar:
            st.header("Configuration")

            # Step 1: Scenario selection
            scenario_builder = ScenarioBuilder(self.data_tables)
            scenario_ctx = scenario_builder.select_scenario().build()
            inputs.update(scenario_ctx)

            # Step 2: Vehicle selection
            vehicle_builder = VehicleSelectionBuilder(self.data_tables)
            vehicle_ctx = vehicle_builder.select_vehicles().build()
            inputs.update(vehicle_ctx)

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
            inputs.update(param_ctx)

            # Step 4: Charging configuration
            charging_builder = ChargingConfigurationBuilder(self.data_tables)
            charging_ctx = charging_builder.configure_charging().build()
            inputs.update(charging_ctx)

            # Step 5: Infrastructure configuration
            infra_builder = InfrastructureBuilder(self.data_tables)
            infra_ctx = infra_builder.configure_infrastructure().build()
            inputs.update(infra_ctx)
            
            # Step 6: Advanced settings
            with st.expander("Advanced Settings", expanded=False):
                st.write("**Performance Options**")
                use_dtos = st.checkbox(
                    "Use DTO mode (experimental)",
                    value=False,
                    help="Enable direct DTO usage for improved performance. This is an experimental feature.",
                    key="use_dto_mode"
                )
                inputs["use_dtos"] = use_dtos

        # Store modified tables for calculations
        inputs["modified_tables"] = modified_tables

        return inputs 