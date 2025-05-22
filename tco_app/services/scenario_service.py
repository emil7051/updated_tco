"""Scenario parameter application & display utilities.

Extracted verbatim from the legacy monolith so that the same behaviour is
available to all callers (UI pages, notebooks, CLI, etc.) via a single import.
"""

from __future__ import annotations

from typing import Dict

import warnings
import pandas as pd
import streamlit as st

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

	This is *exactly* the logic that lived in `tco_app.ui.context` (and before
	that in the monolithic `app.py`).  It makes defensive copies of the four
	tables that may be edited in-place and mutates them according to the rows in
	`scenario_params` for the selected scenario / vehicle / drivetrain.
	"""
	modified_tables = {
		'financial_params': data_tables['financial_params'].copy(),
		'battery_params': data_tables['battery_params'].copy(),
		'vehicle_models': data_tables['vehicle_models'].copy(),
		'incentives': data_tables['incentives'].copy(),
	}

	scenario_params = data_tables['scenario_params']
	selected_params = scenario_params[scenario_params['scenario_id'] == scenario_id]
	if selected_params.empty:
		return modified_tables

	for _, param in selected_params.iterrows():
		param_table = param['parameter_table']
		param_name = param['parameter_name']
		param_value = param['parameter_value']
		param_vehicle_type = param['vehicle_type']
		param_drivetrain = param['vehicle_drivetrain']

		if (
			(param_vehicle_type != 'All' and param_vehicle_type != vehicle_type)
			or (param_drivetrain != 'All' and param_drivetrain != drivetrain)
		):
			continue

		if param_table == 'financial_params':
			mask = modified_tables['financial_params']['finance_description'] == param_name
			modified_tables['financial_params'].loc[mask, 'default_value'] = param_value

			if param_name == 'diesel_default_price':
				mask = modified_tables['financial_params']['finance_description'] == 'diesel_price'
				modified_tables['financial_params'].loc[mask, 'default_value'] = param_value

		elif param_table == 'battery_params':
			mask = modified_tables['battery_params']['battery_description'] == param_name
			modified_tables['battery_params'].loc[mask, 'default_value'] = param_value

		elif param_table == 'vehicle_models':
			mask = modified_tables['vehicle_models']['vehicle_drivetrain'] == param_drivetrain
			if param_vehicle_type != 'All':
				mask &= modified_tables['vehicle_models']['vehicle_type'] == param_vehicle_type

			if param_name == 'msrp_price_modifier':
				for idx, row in modified_tables['vehicle_models'][mask].iterrows():
					modified_tables['vehicle_models'].at[idx, 'msrp_price'] = row['msrp_price'] * param_value
			elif param_name == 'kwh_per100km_modifier':
				for idx, row in modified_tables['vehicle_models'][mask].iterrows():
					modified_tables['vehicle_models'].at[idx, 'kwh_per100km'] = row['kwh_per100km'] * param_value
			elif param_name == 'range_km_modifier':
				for idx, row in modified_tables['vehicle_models'][mask].iterrows():
					modified_tables['vehicle_models'].at[idx, 'range_km'] = row['range_km'] * param_value

		elif param_table == 'incentives':
			if '.' not in param_name:
				warnings.warn(f'Invalid incentive parameter format: {param_name}')
				continue
			incentive_type, incentive_field = param_name.split('.')
			mask = modified_tables['incentives']['incentive_type'] == incentive_type
			if param_vehicle_type != 'All':
				mask &= modified_tables['incentives']['vehicle_type'] == param_vehicle_type
			if param_drivetrain != 'All':
				mask &= modified_tables['incentives']['drivetrain'] == param_drivetrain
			if mask.any():
				for idx in modified_tables['incentives'][mask].index:
					modified_tables['incentives'].at[idx, incentive_field] = param_value
			else:
				warnings.warn(
					f'No matching incentive for {incentive_type} VT={param_vehicle_type} DR={param_drivetrain}'
				)

	return modified_tables


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