import plotly.graph_objects as go
from tco_app.src.constants import Drivetrain


def create_key_metrics_chart(bev_results, diesel_results):
	"""Create a radar chart comparing key performance metrics."""
	infrastructure_cost_per_km = 0
	if 'infrastructure_costs' in bev_results and 'annual_kms' in bev_results and 'truck_life_years' in bev_results:
		if 'npv_per_vehicle_with_incentives' in bev_results['infrastructure_costs']:
			infra_npv = bev_results['infrastructure_costs']['npv_per_vehicle_with_incentives']
		else:
			infra_npv = bev_results['infrastructure_costs']['npv_per_vehicle']
		total_kms = bev_results['annual_kms'] * bev_results['truck_life_years']
		infrastructure_cost_per_km = infra_npv / total_kms if total_kms > 0 else 0

	metrics = {
		'TCO per km': [bev_results['tco']['tco_per_km'], diesel_results['tco']['tco_per_km']],
		'Energy cost per km': [bev_results['energy_cost_per_km'], diesel_results['energy_cost_per_km']],
		'Maintenance per km': [
			bev_results['annual_costs']['annual_maintenance_cost'] / bev_results['annual_kms'],
			diesel_results['annual_costs']['annual_maintenance_cost'] / diesel_results['annual_kms'],
		],
		'CO₂ per km': [bev_results['emissions']['co2_per_km'], diesel_results['emissions']['co2_per_km']],
		'Externality cost': [bev_results['externalities']['externality_per_km'], diesel_results['externalities']['externality_per_km']],
		'Infrastructure per km': [infrastructure_cost_per_km, 0],
	}

	categories = list(metrics.keys())
	bev_values = [metrics[c][0] for c in categories]
	diesel_values = [metrics[c][1] for c in categories]
	# Normalise each metric to its maximum
	normalised = {
		c: [v / max(bev_values[i], diesel_values[i]) for v in metrics[c]]
		for i, c in enumerate(categories)
	}
	bev_norm = [normalised[c][0] for c in categories]
	diesel_norm = [normalised[c][1] for c in categories]

	fig = go.Figure()
	fig.add_trace(go.Scatterpolar(r=bev_norm, theta=categories, fill='toself', name='BEV', line_color='#1f77b4'))
	fig.add_trace(go.Scatterpolar(r=diesel_norm, theta=categories, fill='toself', name='Diesel', line_color='#ff7f0e'))

	fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), title='Comparative Performance (Lower is Better)', height=500)
	return fig 