"""Shared context & data-preparation utilities for Streamlit pages.

This module centralises the heavy-lifting previously performed in the monolithic
`tco_app.app` entry-point.  It is intentionally *UI-aware*: the sidebar widgets
are rendered here so that all pages share the same interactive controls.

Down-stream pages call `get_context()` and receive a dictionary with
pre-computed results in the same structure used historically.  The helper is
idempotent and cached in `st.session_state` under the key `'ctx_cache'` so the
expensive calculations run at most once per page refresh.

NB: This file deliberately violates the 350-line soft-limit – it mainly hosts
legacy code that will be refactored further in upcoming modularisation steps.
"""

from __future__ import annotations

import streamlit as st

# --------------------------------------------------------------------------------------
# Domain imports (unchanged)
# --------------------------------------------------------------------------------------
from tco_app.src.data_loading import load_data
from tco_app.src.constants import Drivetrain
from tco_app.domain.energy import (
	calculate_energy_costs,
	calculate_emissions,
	calculate_charging_requirements,
)
from tco_app.domain.finance import (
	calculate_annual_costs,
	calculate_acquisition_cost,
	calculate_npv,
	calculate_residual_value,
	calculate_tco,
	calculate_infrastructure_costs,
	apply_infrastructure_incentives,
	integrate_infrastructure_with_tco,
)
from tco_app.domain.externalities import (
	calculate_externalities,
	calculate_social_tco,
)
from tco_app.domain.sensitivity import calculate_comparative_metrics
from tco_app.src.utils.battery import calculate_battery_replacement
from tco_app.src.utils.energy import weighted_electricity_price

# --------------------------------------------------------------------------------------
# Scenario helpers (migrated verbatim from the legacy monolith) 
# --------------------------------------------------------------------------------------

from tco_app.services.scenario_service import apply_scenario_parameters as _svc_apply, display_scenario_parameters as _svc_display

# --------------------------------------------------------------------------------------
# Context builder
# --------------------------------------------------------------------------------------

def get_context() -> Dict[str, Any]:
	"""Return cached modelling context (data + computed results)."""
	print("Attempting to get context...")

	# Basic cache – recompute when the user presses the Streamlit *rerun* button.
	if 'ctx_cache' in st.session_state:
		print("Returning cached context.")
		return st.session_state['ctx_cache']
	
	print("No cached context found, computing new context...")

	# ----------------------------------------------------------------------------------
	# 1. Data loading
	# ----------------------------------------------------------------------------------
	print("Loading data...")
	data_tables = load_data()
	print("Data loaded successfully.")

	vehicle_models = data_tables['vehicle_models']
	vehicle_fees = data_tables['vehicle_fees']
	charging_options = data_tables['charging_options']
	infrastructure_options = data_tables['infrastructure_options']
	operating_params = data_tables['operating_params']
	financial_params = data_tables['financial_params']
	battery_params = data_tables['battery_params']
	emission_factors = data_tables['emission_factors']
	externalities = data_tables['externalities']
	incentives = data_tables['incentives']
	scenarios = data_tables['scenarios']
	scenario_params = data_tables['scenario_params']

	# ----------------------------------------------------------------------------------
	# 2. Sidebar inputs
	# ----------------------------------------------------------------------------------
	with st.sidebar:
		st.header('Configuration')
		print("Setting up sidebar inputs...")

		# Scenario selection
		scenario_id = st.selectbox(
			'Select Scenario',
			scenarios['scenario_id'].tolist(),
			format_func=lambda x: scenarios[scenarios['scenario_id'] == x].iloc[0]['scenario_name'],
		)
		scenario_desc = scenarios[scenarios['scenario_id'] == scenario_id].iloc[0]['scenario_description']
		st.markdown(f'*{scenario_desc}*')

		# Show scenario parameter overrides
		scenario_name = scenarios[scenarios['scenario_id'] == scenario_id].iloc[0]['scenario_name']
		_svc_display(scenario_id, scenario_params, scenario_name)
		print("Sidebar inputs setup complete.")

		# Vehicle selection
		vehicle_type = st.selectbox(
			'Vehicle Type', ['Light Rigid', 'Medium Rigid', 'Articulated']
		)
		type_vehicles = vehicle_models[vehicle_models['vehicle_type'] == vehicle_type]
		bev_vehicles = type_vehicles[type_vehicles['vehicle_drivetrain'] == Drivetrain.BEV]
		selected_bev_id = st.selectbox(
			'Select BEV Model',
			bev_vehicles['vehicle_id'].tolist(),
			format_func=lambda x: vehicle_models[vehicle_models['vehicle_id'] == x].iloc[0]['vehicle_model'],
		)

		selected_bev = vehicle_models[vehicle_models['vehicle_id'] == selected_bev_id].iloc[0]
		comparison_diesel_id = selected_bev['comparison_pair_id']
		diesel_model = vehicle_models[vehicle_models['vehicle_id'] == comparison_diesel_id].iloc[0]['vehicle_model']
		st.info(f'Comparison Diesel: {diesel_model}')

		# Apply scenario parameters
		modified_tables = _svc_apply(
			scenario_id,
			data_tables,
			vehicle_type,
			Drivetrain.ALL,
		)

		financial_params = modified_tables['financial_params']
		battery_params = modified_tables['battery_params']
		vehicle_models_updated = modified_tables['vehicle_models']
		incentives = modified_tables['incentives']

		bev_vehicle_data = (
			vehicle_models_updated[vehicle_models_updated['vehicle_id'] == selected_bev_id]
			.iloc[0]
		)
		diesel_vehicle_data = (
			vehicle_models_updated[vehicle_models_updated['vehicle_id'] == comparison_diesel_id]
			.iloc[0]
		)

		# Operating parameters
		default_params = operating_params[operating_params['vehicle_type'] == vehicle_type].iloc[0]
		annual_kms = st.number_input(
			'Annual Distance (km)', 1000, 200000, int(default_params['annual_kms']), 1000
		)
		truck_life_years = st.number_input(
			'Vehicle Lifetime (years)', 1, 30, int(default_params['truck_life_years']), 1
		)

		# Financial parameters
		default_discount = financial_params[
			financial_params['finance_description'] == 'discount_rate_percent'
		].iloc[0]['default_value']
		discount_rate = st.slider(
			'Discount Rate (%)', 0.0, 15.0, float(default_discount * 100), 0.5
		) / 100

		default_diesel_price = financial_params[
			financial_params['finance_description'] == 'diesel_price'
		].iloc[0]['default_value']
		diesel_price = st.number_input(
			'Diesel Price (AUD/L)', 0.5, 10.0, float(default_diesel_price), 0.05
		)

		# Charging options
		charging_approach = st.radio(
			'Charging Approach',
			['Single Charging Option', 'Mixed Charging (Time-of-Use)'],
			index=0,
		)

		use_charging_mix = charging_approach == 'Mixed Charging (Time-of-Use)'
		charging_mix: Dict[int, float] | None = None
		selected_charging = charging_options['charging_id'].iloc[0]

		if use_charging_mix:
			st.markdown('Allocate percentage of charging per option (must sum to 100%)')
			charging_percentages: Dict[int, float] = {}
			total_percentage = 0
			default_pct = 100 // len(charging_options)

			for idx, option in charging_options.iterrows():
				pct = st.slider(
					option['charging_approach'], 0, 100, default_pct, 5, key=f'cm_{idx}'
				)
				charging_percentages[option['charging_id']] = pct / 100
				total_percentage += pct

			if total_percentage != 100:
				st.warning(f'Total allocation must equal 100% (current {total_percentage}%)')
			else:
				charging_mix = charging_percentages
				selected_charging = charging_options['charging_id'].iloc[0]
		else:
			selected_charging = st.selectbox(
				'Primary Charging Approach',
				charging_options['charging_id'].tolist(),
				format_func=lambda x: charging_options[charging_options['charging_id'] == x]
				.loc[:, ['charging_approach', 'per_kwh_price']]
				.apply(lambda r: f"{r.iloc[0]} (${r.iloc[1]:.2f}/kWh)", axis=1)
				.iloc[0],
			)

		# Infrastructure option & fleet size
		selected_infrastructure = st.selectbox(
			'Charging Infrastructure',
			infrastructure_options['infrastructure_id'].tolist(),
			format_func=lambda x: infrastructure_options[
				infrastructure_options['infrastructure_id'] == x
			].iloc[0]['infrastructure_description'],
		)
		fleet_size = st.number_input(
			'Number of Vehicles Sharing Infrastructure', 1, 1000, 1, 1
		)

		# Incentives toggle
		apply_incentives = st.checkbox('Apply Incentives', value=True)

		# Battery parameters UI customisation
		default_deg = battery_params[
			battery_params['battery_description'] == 'degradation_annual_percent'
		].iloc[0]['default_value']
		degradation_rate = st.slider(
			'Annual Battery Degradation (%)', 0.0, 10.0, float(default_deg * 100), 0.1
		) / 100

		default_rep = battery_params[
			battery_params['battery_description'] == 'replacement_per_kwh_price'
		].iloc[0]['default_value']
		replacement_cost = st.number_input(
			'Battery Replacement Cost ($/kWh)', 50, 500, int(default_rep), 10
		)

		# Carbon price
		default_cp = financial_params[
			financial_params['finance_description'] == 'carbon_price'
		].iloc[0]['default_value']
		carbon_price = st.number_input(
			'Carbon Price ($/tonne CO₂)', 0, 500, int(default_cp), 5
		)

	# ----------------------------------------------------------------------------------
	# 3. Derived parameter tables (UI overrides applied)
	# ----------------------------------------------------------------------------------
	battery_params_with_ui = battery_params.copy()
	print("Preparing derived parameter tables...")
	mask = battery_params_with_ui['battery_description'] == 'degradation_annual_percent'
	battery_params_with_ui.loc[mask, 'default_value'] = degradation_rate
	mask = battery_params_with_ui['battery_description'] == 'replacement_per_kwh_price'
	battery_params_with_ui.loc[mask, 'default_value'] = replacement_cost

	financial_params_with_ui = financial_params.copy()
	mask = financial_params_with_ui['finance_description'] == 'diesel_price'
	financial_params_with_ui.loc[mask, 'default_value'] = diesel_price
	mask = financial_params_with_ui['finance_description'] == 'carbon_price'
	financial_params_with_ui.loc[mask, 'default_value'] = carbon_price

	# ----------------------------------------------------------------------------------
	# 4. Core calculations (identical to legacy implementation)
	# ----------------------------------------------------------------------------------
	bev_fees = vehicle_fees[vehicle_fees['vehicle_id'] == selected_bev_id]
	print("Starting core TCO calculations...")
	diesel_fees = vehicle_fees[vehicle_fees['vehicle_id'] == comparison_diesel_id]

	bev_energy_cost_per_km = calculate_energy_costs(
		bev_vehicle_data,
		bev_fees,
		charging_options,
		financial_params_with_ui,
		selected_charging,
		charging_mix,
	)
	diesel_energy_cost_per_km = calculate_energy_costs(
		diesel_vehicle_data,
		diesel_fees,
		charging_options,
		financial_params_with_ui,
		selected_charging,
	)

	bev_annual_costs = calculate_annual_costs(
		bev_vehicle_data,
		bev_fees,
		bev_energy_cost_per_km,
		annual_kms,
		incentives,
		apply_incentives,
	)
	diesel_annual_costs = calculate_annual_costs(
		diesel_vehicle_data,
		diesel_fees,
		diesel_energy_cost_per_km,
		annual_kms,
		incentives,
		apply_incentives,
	)

	bev_emissions = calculate_emissions(
		bev_vehicle_data, emission_factors, annual_kms, truck_life_years
	)
	diesel_emissions = calculate_emissions(
		diesel_vehicle_data, emission_factors, annual_kms, truck_life_years
	)

	bev_acquisition = calculate_acquisition_cost(
		bev_vehicle_data, bev_fees, incentives, apply_incentives
	)
	diesel_acquisition = calculate_acquisition_cost(
		diesel_vehicle_data, diesel_fees, incentives, apply_incentives
	)

	init_dep = financial_params[
		financial_params['finance_description'] == 'initial_deprecation_percent'
	].get('default_value', 0)
	annual_dep = financial_params[
		financial_params['finance_description'] == 'annual_depreciation_percent'
	].iloc[0]['default_value']

	bev_residual = calculate_residual_value(
		bev_vehicle_data, truck_life_years, init_dep, annual_dep
	)
	diesel_residual = calculate_residual_value(
		diesel_vehicle_data, truck_life_years, init_dep, annual_dep
	)

	bev_battery_replacement = calculate_battery_replacement(
		bev_vehicle_data,
		battery_params_with_ui,
		truck_life_years,
		discount_rate,
	)

	bev_npv_annual = calculate_npv(
		bev_annual_costs['annual_operating_cost'], discount_rate, truck_life_years
	)
	diesel_npv_annual = calculate_npv(
		diesel_annual_costs['annual_operating_cost'], discount_rate, truck_life_years
	)

	bev_tco = calculate_tco(
		bev_vehicle_data,
		bev_fees,
		bev_annual_costs,
		bev_acquisition,
		bev_residual,
		bev_battery_replacement,
		bev_npv_annual,
		annual_kms,
		truck_life_years,
	)
	diesel_tco = calculate_tco(
		diesel_vehicle_data,
		diesel_fees,
		diesel_annual_costs,
		diesel_acquisition,
		diesel_residual,
		0,
		diesel_npv_annual,
		annual_kms,
		truck_life_years,
	)

	bev_externalities = calculate_externalities(
		bev_vehicle_data,
		externalities,
		annual_kms,
		truck_life_years,
		discount_rate,
	)
	diesel_externalities = calculate_externalities(
		diesel_vehicle_data,
		externalities,
		annual_kms,
		truck_life_years,
		discount_rate,
	)

	# Infrastructure costs
	selected_infra_data = infrastructure_options[
		infrastructure_options['infrastructure_id'] == selected_infrastructure
	].iloc[0]

	bev_charging_requirements = calculate_charging_requirements(
		bev_vehicle_data, annual_kms, selected_infra_data
	)
	infrastructure_costs = calculate_infrastructure_costs(
		selected_infra_data, truck_life_years, discount_rate, fleet_size
	)
	infra_costs_with_incentives = apply_infrastructure_incentives(
		infrastructure_costs, incentives, apply_incentives
	)
	infra_costs_with_incentives['fleet_size'] = fleet_size

	bev_tco_with_infra = integrate_infrastructure_with_tco(
		bev_tco, infra_costs_with_incentives, apply_incentives
	)

	bev_results = {
		'vehicle_data': bev_vehicle_data,
		'fees': bev_fees,
		'energy_cost_per_km': bev_energy_cost_per_km,
		'annual_costs': bev_annual_costs,
		'emissions': bev_emissions,
		'acquisition_cost': bev_acquisition,
		'residual_value': bev_residual,
		'battery_replacement': bev_battery_replacement,
		'npv_annual_cost': bev_npv_annual,
		'tco': bev_tco_with_infra,
		'externalities': bev_externalities,
		'social_tco': calculate_social_tco(bev_tco_with_infra, bev_externalities),
		'annual_kms': annual_kms,
		'truck_life_years': truck_life_years,
		'charging_requirements': bev_charging_requirements,
		'infrastructure_costs': infra_costs_with_incentives,
		'selected_infrastructure_description': selected_infra_data['infrastructure_description'],
		'charging_options': charging_options,
		'discount_rate': discount_rate,
		'scenario': {
			'id': scenario_id,
			'name': scenario_name,
			'description': scenario_desc,
		},
	}
	if charging_mix:
		bev_results['charging_mix'] = charging_mix
		bev_results['weighted_electricity_price'] = weighted_electricity_price(
			charging_mix, charging_options
		)

	diesel_results = {
		'vehicle_data': diesel_vehicle_data,
		'fees': diesel_fees,
		'energy_cost_per_km': diesel_energy_cost_per_km,
		'annual_costs': diesel_annual_costs,
		'emissions': diesel_emissions,
		'acquisition_cost': diesel_acquisition,
		'residual_value': diesel_residual,
		'battery_replacement': 0,
		'npv_annual_cost': diesel_npv_annual,
		'tco': diesel_tco,
		'externalities': diesel_externalities,
		'social_tco': calculate_social_tco(diesel_tco, diesel_externalities),
		'annual_kms': annual_kms,
		'truck_life_years': truck_life_years,
		'discount_rate': discount_rate,
		'scenario': {
			'id': scenario_id,
			'name': scenario_name,
			'description': scenario_desc,
		},
	}

	comparison_metrics = calculate_comparative_metrics(
		bev_results, diesel_results, annual_kms, truck_life_years
	)
	bev_results['comparison'] = comparison_metrics

	# Show caption for active scenario
	st.caption(f'Scenario: {scenario_name}')
	print("Core TCO calculations complete.")

	ctx: Dict[str, Any] = {
		'bev_results': bev_results,
		'diesel_results': diesel_results,
		'comparison_metrics': comparison_metrics,
		'bev_vehicle_data': bev_vehicle_data,
		'diesel_vehicle_data': diesel_vehicle_data,
		'bev_fees': bev_fees,
		'diesel_fees': diesel_fees,
		'charging_options': charging_options,
		'infrastructure_options': infrastructure_options,
		'financial_params_with_ui': financial_params_with_ui,
		'battery_params_with_ui': battery_params_with_ui,
		'emission_factors': emission_factors,
		'incentives': incentives,
		'selected_charging': selected_charging,
		'selected_infrastructure': selected_infrastructure,
		'annual_kms': annual_kms,
		'truck_life_years': truck_life_years,
		'discount_rate': discount_rate,
		'fleet_size': fleet_size,
		'charging_mix': charging_mix,
		'apply_incentives': apply_incentives,
	}

	st.session_state['ctx_cache'] = ctx
	print("Context computed and cached.")
	return ctx 