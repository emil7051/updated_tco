from tco_app.src import st
from tco_app.src.constants import DataColumns, ParameterKeys

from tco_app.ui.context import get_context
from tco_app.domain.sensitivity import perform_sensitivity_analysis
from tco_app.plotters import (
	create_sensitivity_chart,
	create_payload_sensitivity_chart,
)


def render():
	ctx = get_context()
	bev_results = ctx['bev_results']
	diesel_results = ctx['diesel_results']
	bev_vehicle_data = ctx['bev_vehicle_data']
	diesel_vehicle_data = ctx['diesel_vehicle_data']
	bev_fees = ctx['bev_fees']
	diesel_fees = ctx['diesel_fees']
	charging_options = ctx['charging_options']
	infrastructure_options = ctx['infrastructure_options']
	financial_params_with_ui = ctx['financial_params_with_ui']
	battery_params_with_ui = ctx['battery_params_with_ui']
	emission_factors = ctx['emission_factors']
	incentives = ctx['incentives']
	selected_charging = ctx['selected_charging']
	selected_infrastructure = ctx['selected_infrastructure']
	annual_kms = ctx['annual_kms']
	truck_life_years = ctx['truck_life_years']
	discount_rate = ctx['discount_rate']
	fleet_size = ctx['fleet_size']
	charging_mix = ctx['charging_mix']
	apply_incentives = ctx['apply_incentives']
	financial_params_with_ui = ctx['financial_params_with_ui']

	st.subheader('Sensitivity Analysis')
	st.info('Sensitivity Analysis helps understand how changes in key parameters affect the TCO comparison.')

	sensitivity_param = st.selectbox(
		'Select Parameter for Sensitivity Analysis',
		[
			'Annual Distance (km)',
			'Diesel Price ($/L)',
			'Electricity Price ($/kWh)',
			'Vehicle Lifetime (years)',
			'Discount Rate (%)',
			'Annual Distance (km) with Payload Effect',
		],
	)

	num_points = 11
	param_range = None

	if sensitivity_param == 'Annual Distance (km) with Payload Effect':
		min_val = max(1000, annual_kms * 0.5)
		max_val = annual_kms * 1.5
		step = (max_val - min_val) / (num_points - 1)
		distances = [round(min_val + i * step) for i in range(num_points)]

		payload_sensitivity_chart = create_payload_sensitivity_chart(
			bev_results,
			diesel_results,
			financial_params_with_ui,
			distances,
		)
		st.plotly_chart(payload_sensitivity_chart, use_container_width=True, key='payload_sensitivity_chart')

		st.markdown(
			"""
			Values below 1.0 indicate BEV is more cost-effective. The gap between the lines shows the economic impact of payload limitations at higher utilisation.
			"""
		)
	else:
		if sensitivity_param == 'Annual Distance (km)':
			min_val = max(1000, annual_kms * 0.5)
			max_val = annual_kms * 1.5
			step = (max_val - min_val) / (num_points - 1)
			param_range = [round(min_val + i * step) for i in range(num_points)]
			if annual_kms not in param_range:
				param_range.append(annual_kms)
				param_range.sort()
		elif sensitivity_param == 'Diesel Price ($/L)':
			diesel_base = financial_params_with_ui[
				financial_params_with_ui[DataColumns.FINANCE_DESCRIPTION] == ParameterKeys.DIESEL_PRICE
			].iloc[0][DataColumns.FINANCE_DEFAULT_VALUE]
			min_val = max(0.5, diesel_base * 0.7)
			max_val = diesel_base * 1.3
			step = (max_val - min_val) / (num_points - 1)
			param_range = [round(min_val + i * step, 2) for i in range(num_points)]
			if diesel_base not in param_range:
				param_range.append(diesel_base)
				param_range.sort()
		elif sensitivity_param == 'Electricity Price ($/kWh)':
			if 'weighted_electricity_price' in bev_results:
				electricity_base = bev_results['weighted_electricity_price']
			else:
				electricity_base = charging_options[charging_options[DataColumns.CHARGING_ID] == selected_charging].iloc[0][DataColumns.PER_KWH_PRICE]
			min_val = max(0.05, electricity_base * 0.7)
			max_val = electricity_base * 1.3
			step = (max_val - min_val) / (num_points - 1)
			param_range = [round(min_val + i * step, 2) for i in range(num_points)]
			if electricity_base not in param_range:
				param_range.append(electricity_base)
				param_range.sort()
		elif sensitivity_param == 'Vehicle Lifetime (years)':
			min_val = max(1, truck_life_years - 3)
			max_val = truck_life_years + 3
			param_range = list(range(int(min_val), int(max_val + 1)))
			if truck_life_years not in param_range:
				param_range.append(truck_life_years)
				param_range.sort()
		elif sensitivity_param == 'Discount Rate (%)':
			discount_base = discount_rate * 100
			min_val = max(0.5, discount_base - 3)
			max_val = min(15, discount_base + 3)
			step = (max_val - min_val) / (num_points - 1)
			param_range = [round(min_val + i * step, 1) for i in range(num_points)]
			if discount_base not in param_range:
				param_range.append(discount_base)
				param_range.sort()

		with st.spinner(f'Calculating sensitivity for {sensitivity_param}…'):
			sensitivity_results = perform_sensitivity_analysis(
				sensitivity_param,
				param_range,
				bev_vehicle_data,
				diesel_vehicle_data,
				bev_fees,
				diesel_fees,
				charging_options,
				infrastructure_options,
				financial_params_with_ui,
				battery_params_with_ui,
				emission_factors,
				incentives,
				selected_charging,
				selected_infrastructure,
				annual_kms,
				truck_life_years,
				discount_rate,
				fleet_size,
				charging_mix,
				apply_incentives,
			)

			chart = create_sensitivity_chart(
				bev_results,
				diesel_results,
				sensitivity_param,
				param_range,
				sensitivity_results,
			)
			st.plotly_chart(chart, use_container_width=True, key='sensitivity_chart') 