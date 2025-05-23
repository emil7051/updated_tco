"""Scenario parameter application & display utilities.

Extracted verbatim from the legacy monolith so that the same behaviour is
available to all callers (UI pages, notebooks, CLI, etc.) via a single import.
"""

from __future__ import annotations

from typing import Dict

import warnings
from tco_app.src import pd
from tco_app.src import st

from tco_app.services.scenario_application_service import ScenarioApplicationService, ScenarioModification

__all__ = [
	'apply_scenario_parameters',
	'display_scenario_parameters',
]

def apply_scenario_parameters(
	scenario_id: str,
	data_tables: Dict[str, pd.DataFrame],
	vehicle_type: str,
	drivetrain: str,
) -> Dict[str, pd.DataFrame]:
	"""Return copies of parameter tables with scenario overrides applied.

	Uses ScenarioApplicationService to apply modifications.
	"""
	scenario_params_df = data_tables.get('scenario_params')
	if scenario_params_df is None:
		warnings.warn("No scenario_params table found in data_tables.")
		# Return copies of potentially modifiable tables to maintain original behaviour
		return {
			name: df.copy() for name, df in data_tables.items() 
			if name in ['financial_params', 'battery_params', 'vehicle_models', 'incentives']
		}

	selected_params_df = scenario_params_df[scenario_params_df['scenario_id'] == scenario_id]

	if selected_params_df.empty:
		# Return copies of potentially modifiable tables
		return {
			name: df.copy() for name, df in data_tables.items() 
			if name in ['financial_params', 'battery_params', 'vehicle_models', 'incentives']
		}

	app_service = ScenarioApplicationService()
	modifications = app_service.parse_scenario_params(selected_params_df)
	
	# Create copies of the tables that can be modified by scenarios
	# to avoid altering the original data_tables dict passed in.
	tables_to_modify = {
		'financial_params': data_tables.get('financial_params', pd.DataFrame()).copy(),
		'battery_params': data_tables.get('battery_params', pd.DataFrame()).copy(),
		'vehicle_models': data_tables.get('vehicle_models', pd.DataFrame()).copy(),
		'incentives': data_tables.get('incentives', pd.DataFrame()).copy(),
	}

	# Include other tables from data_tables, without copying if they are not modified
	# This ensures the returned dictionary has all original tables.
	# However, ScenarioApplicationService only modifies the above 4.
	# We will pass only these 4 to apply_modifications and then merge back.
	
	modified_subset = app_service.apply_modifications(
		data_tables=tables_to_modify, # Pass only the subset of tables that can be modified
		modifications=modifications,
		target_vehicle_type=vehicle_type,
		target_drivetrain=drivetrain
	)
	
	# Start with copies of all original tables
	final_modified_tables = {name: df.copy() for name, df in data_tables.items()}
	# Update with the (potentially) modified tables
	final_modified_tables.update(modified_subset)

	return final_modified_tables


def display_scenario_parameters(
	scenario_id: str,
	scenario_params: pd.DataFrame,
	scenario_name: str,
) -> None:
	"""Render human-friendly list of scenario overrides inside an expander."""
	selected_params = scenario_params[scenario_params['scenario_id'] == scenario_id]
	if selected_params.empty or scenario_id == 'S000':
		st.caption('Base scenario with default parameters')
		return

	with st.expander(f'Scenario Parameters for {scenario_name}'):
		for _, param in selected_params.iterrows():
			st.markdown(
				f"- **{param['parameter_table']}** → {param['parameter_name']}: {param['parameter_value']}"
			) 