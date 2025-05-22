from tco_app.plotters import (
    create_cost_breakdown_chart,
    create_emissions_chart,
)
from tco_app.src.constants import Drivetrain
import plotly.graph_objects as go


def _dummy_results(acquisition_cost: float = 100_000, truck_life_years: int = 10):
    """Return a minimal result dict satisfying the visualisation helpers."""
    return {
        "acquisition_cost": acquisition_cost,
        "annual_costs": {
            "annual_energy_cost": 5_000,
            "annual_maintenance_cost": 2_000,
            "insurance_annual": 1_000,
            "registration_annual": 500,
            "annual_operating_cost": 8_500,
        },
        "truck_life_years": truck_life_years,
        "battery_replacement": 0,
        "residual_value": 10_000,
        # Minimal emissions block for emissions-chart helper
        "emissions": {
            "annual_emissions": 50_000,
            "lifetime_emissions": 500_000,
        },
    }


def _collect_unique_x_values(fig: go.Figure):
    """Return the set of unique *x* values across all traces in a Plotly figure."""
    x_values = set()
    for trace in fig.data:
        # Some traces store x in a list; others may embed it in arrays
        if hasattr(trace, "x") and trace.x is not None:
            x_values.update(trace.x)
    return set(map(str, x_values))


def test_cost_breakdown_vehicle_type_labels():
    bev_results = _dummy_results()
    diesel_results = _dummy_results()

    fig = create_cost_breakdown_chart(bev_results, diesel_results)
    x_labels = _collect_unique_x_values(fig)
    assert x_labels == {Drivetrain.BEV.value, Drivetrain.DIESEL.value}


def test_emissions_chart_vehicle_type_labels():
    bev_results = _dummy_results()
    diesel_results = _dummy_results()

    fig = create_emissions_chart(bev_results, diesel_results, truck_life_years=10)
    x_labels = _collect_unique_x_values(fig)
    assert x_labels == {Drivetrain.BEV.value, Drivetrain.DIESEL.value} 