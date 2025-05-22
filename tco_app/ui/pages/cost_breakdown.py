import streamlit as st

from tco_app.ui.context import get_context
from tco_app.plotters import (
	create_cost_breakdown_chart,
	create_charging_mix_chart,
	create_annual_costs_chart,
)
from tco_app.src.constants import Drivetrain


def render():
	ctx = get_context()
	bev_results = ctx['bev_results']
	diesel_results = ctx['diesel_results']
	truck_life_years = ctx['truck_life_years']

	st.subheader('Lifetime Cost Components')
	chart = create_cost_breakdown_chart(bev_results, diesel_results)
	st.plotly_chart(chart, use_container_width=True)

	# Charging mix visual
	if 'charging_mix' in bev_results:
		st.subheader('Charging Mix')
		cm_chart = create_charging_mix_chart(bev_results)
		st.plotly_chart(cm_chart, use_container_width=True)

	# Infrastructure + charging requirements
	bev_vehicle_data = bev_results['vehicle_data']
	if bev_vehicle_data['vehicle_drivetrain'] == Drivetrain.BEV:
		st.subheader('Infrastructure Costs')
		infra_col1, infra_col2 = st.columns(2)
		with infra_col1:
			st.metric('Infrastructure Capital Cost', f"${bev_results['infrastructure_costs']['infrastructure_price']:,.0f}")
			st.metric('Annual Maintenance', f"${bev_results['infrastructure_costs']['annual_maintenance']:,.0f}/year")
			st.metric('Cost Per Vehicle', f"${bev_results['infrastructure_costs']['npv_per_vehicle']:,.0f}")
		with infra_col2:
			st.metric('Service Life', f"{bev_results['infrastructure_costs']['service_life_years']} years")
			st.metric('Replacement Cycles', f"{bev_results['infrastructure_costs']['replacement_cycles']}")
			if bev_results['infrastructure_costs'].get('subsidy_rate', 0) > 0:
				st.metric(
					'Infrastructure Subsidy',
					f"${bev_results['infrastructure_costs']['subsidy_amount']:,.0f}",
					delta=f"{bev_results['infrastructure_costs']['subsidy_rate'] * 100:.0f}%",
				)

		st.subheader('Charging Requirements')
		cc1, cc2 = st.columns(2)
		with cc1:
			st.metric('Daily Energy Required', f"{bev_results['charging_requirements']['daily_kwh_required']:.1f} kWh")
			st.metric('Charging Time Per Day', f"{bev_results['charging_requirements']['charging_time_per_day']:.2f} hours")
		with cc2:
			st.metric('Charger Power', f"{bev_results['charging_requirements']['charger_power']:.0f} kW")
			st.metric('Maximum Vehicles Per Charger', f"{min(100, bev_results['charging_requirements']['max_vehicles_per_charger']):.1f}")

	st.subheader('Costs Over Time')
	annual_chart = create_annual_costs_chart(bev_results, diesel_results, truck_life_years)
	st.plotly_chart(annual_chart, use_container_width=True, key='annual_costs_chart') 