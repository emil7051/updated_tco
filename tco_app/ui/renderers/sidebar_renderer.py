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
    IncentivesBuilder,
)


class SidebarRenderer:
    """Handles rendering of sidebar inputs and returns collected values."""

    def __init__(self, data_tables: Dict[str, pd.DataFrame]):
        self.data_tables = data_tables

    def render_and_collect_inputs(self) -> Dict[str, Any]:
        """Render sidebar inputs and return collected values."""
        inputs = {}

        with st.sidebar:
            st.header("⚙️ Configuration")
            st.markdown("---")

            # Step 1: Scenario selection - Always visible as it's the primary selector
            with st.container():
                st.subheader("📋 Scenario")
                scenario_builder = ScenarioBuilder(self.data_tables)
                scenario_ctx = scenario_builder.select_scenario().build()
                inputs.update(scenario_ctx)
                st.markdown("---")

            # Step 2: Vehicle selection - In expander
            with st.expander("🚛 Vehicle Selection", expanded=True):
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

            # Step 3: Parameter inputs - Grouped into logical sections
            with st.expander("📊 Operating & Financial Parameters", expanded=False):
                param_builder = ParameterInputBuilder(
                    self.data_tables, vehicle_ctx[DataColumns.VEHICLE_TYPE]
                )
                
                # Operating parameters
                st.markdown("**Operating Parameters**")
                param_builder.collect_operating_parameters()
                
                st.markdown("---")
                
                # Financial parameters
                st.markdown("**Financial Parameters**")
                param_builder.collect_financial_parameters(modified_tables["financial_params"])
                
                st.markdown("---")
                
                # Battery parameters
                st.markdown("**Battery Parameters**")
                param_builder.collect_battery_parameters(modified_tables["battery_params"])
                
                param_ctx = param_builder.build()
                inputs.update(param_ctx)

            # Step 4: Charging configuration
            with st.expander("⚡ Charging Configuration", expanded=False):
                charging_builder = ChargingConfigurationBuilder(self.data_tables)
                charging_ctx = charging_builder.configure_charging().build()
                inputs.update(charging_ctx)

            # Step 5: Infrastructure configuration
            with st.expander("🏗️ Infrastructure", expanded=False):
                infra_builder = InfrastructureBuilder(self.data_tables)
                infra_ctx = infra_builder.configure_infrastructure().build()
                inputs.update(infra_ctx)

            # Step 6: Policies & Incentives configuration
            with st.expander("💰 Policies & Incentives", expanded=False):
                # Pass modified_tables to get scenario-adjusted incentives
                incentives_builder = IncentivesBuilder(modified_tables)
                incentives_ctx = incentives_builder.configure_incentives().build()
                inputs.update(incentives_ctx)
                
                # Update the modified incentives table
                if "modified_incentives" in incentives_ctx:
                    modified_tables["incentives"] = incentives_ctx["modified_incentives"]

            # Add a help section at the bottom
            with st.expander("❓ Help", expanded=False):
                st.markdown("""
                **Quick Guide:**
                - **Scenario**: Select pre-configured analysis scenarios
                - **Vehicle**: Choose BEV model and see comparison diesel
                - **Parameters**: Adjust operating, financial, and battery settings
                - **Charging**: Configure charging approach and mix
                - **Infrastructure**: Set up charging infrastructure options
                - **Policies & Incentives**: Select applicable government support programs
                
                💡 *Tip: Scenarios automatically adjust relevant parameters*
                """)

        # Store modified tables for calculations
        inputs["modified_tables"] = modified_tables

        return inputs 