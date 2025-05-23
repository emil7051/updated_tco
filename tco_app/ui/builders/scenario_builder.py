"""Scenario selection builder for UI context."""

from tco_app.src import Dict, Any
from tco_app.src import pd
from tco_app.src import st

from tco_app.services.scenario_service import display_scenario_parameters


class ScenarioBuilder:
    """Builds scenario-related context."""

    def __init__(self, data_tables: Dict[str, pd.DataFrame]):
        self.data_tables = data_tables
        self.scenario_id = None
        self.scenario_params = None
        self.scenario_meta = None

    def select_scenario(self) -> "ScenarioBuilder":
        """Handle scenario selection UI."""
        scenarios = self.data_tables["scenarios"]
        scenario_params = self.data_tables["scenario_params"]

        self.scenario_id = st.selectbox(
            "Select Scenario",
            scenarios["scenario_id"].tolist(),
            format_func=lambda x: scenarios[scenarios["scenario_id"] == x].iloc[0][
                "scenario_name"
            ],
        )

        # Get scenario details
        scenario_row = scenarios[scenarios["scenario_id"] == self.scenario_id].iloc[0]

        st.markdown(f'*{scenario_row["scenario_description"]}*')

        # Store scenario metadata
        self.scenario_meta = {
            "id": self.scenario_id,
            "name": scenario_row["scenario_name"],
            "description": scenario_row["scenario_description"],
        }

        # Show scenario parameter overrides
        display_scenario_parameters(
            self.scenario_id, scenario_params, self.scenario_meta["name"]
        )

        return self

    def build(self) -> Dict[str, Any]:
        """Return scenario context."""
        if not self.scenario_id:
            raise ValueError("Scenario must be selected before building context")

        return {"scenario_id": self.scenario_id, "scenario_meta": self.scenario_meta}
