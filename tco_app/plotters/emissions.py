from tco_app.src import pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from tco_app.src.constants import Drivetrain


def create_emissions_chart(bev_results, diesel_results, truck_life_years):
	"""Create a bar chart comparing annual & lifetime emissions"""
	data = pd.DataFrame({
		'Vehicle Type': [Drivetrain.BEV.value, Drivetrain.DIESEL.value],
		'Annual Emissions (kg CO₂)': [
			bev_results['emissions']['annual_emissions'],
			diesel_results['emissions']['annual_emissions'],
		],
		'Lifetime Emissions (tonnes CO₂)': [
			bev_results['emissions']['lifetime_emissions'] / 1_000,
			diesel_results['emissions']['lifetime_emissions'] / 1_000,
		],
	})

	fig = make_subplots(rows=1, cols=2, subplot_titles=('Annual Emissions', 'Lifetime Emissions'))

	fig.add_trace(
		go.Bar(
			x=data['Vehicle Type'],
			y=data['Annual Emissions (kg CO₂)'],
			marker_color=['#1f77b4', '#ff7f0e'],
			showlegend=False,
		),
		row=1,
		col=1,
	)

	fig.add_trace(
		go.Bar(
			x=data['Vehicle Type'],
			y=data['Lifetime Emissions (tonnes CO₂)'],
			marker_color=['#1f77b4', '#ff7f0e'],
			showlegend=False,
		),
		row=1,
		col=2,
	)

	fig.update_layout(title_text='Emissions Comparison', height=400)
	fig.update_yaxes(title_text='kg CO₂ per year', row=1, col=1)
	fig.update_yaxes(title_text='tonnes CO₂ lifetime', row=1, col=2)
	return fig 