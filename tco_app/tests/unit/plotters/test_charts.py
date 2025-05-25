import plotly.graph_objects as go
from tco_app.src import pd
from tco_app.plotters import (
    create_charging_mix_chart,
    create_tornado_chart,
    create_payload_comparison_chart,
)
from tco_app.src.constants import DataColumns


def test_create_charging_mix_chart_no_data():
    fig = create_charging_mix_chart({})
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 0


def test_create_charging_mix_chart_with_data():
    bev_results = {
        "charging_mix": {"Depot": 1.0},
        "charging_options": pd.DataFrame(
            [
                {
                    DataColumns.CHARGING_ID: "Depot",
                    DataColumns.PER_KWH_PRICE: 0.25,
                    DataColumns.CHARGING_APPROACH: "Depot 50 kW",
                }
            ]
        ),
    }
    fig = create_charging_mix_chart(bev_results)
    assert len(fig.data) == 1
    assert isinstance(fig.data[0], go.Pie)
    assert "Weighted Average: $0.25" in fig.layout.title.text


def test_create_tornado_chart_basic():
    impacts = {
        "A": {"min_impact": -0.2, "max_impact": 0.3},
        "B": {"min_impact": -0.1, "max_impact": 0.1},
    }
    fig = create_tornado_chart(1.0, impacts)
    assert len(fig.data) == 2
    assert all(isinstance(tr, go.Bar) for tr in fig.data)
    assert any(s.type == "line" for s in fig.layout.shapes)


def test_create_payload_comparison_chart_axes_and_traces():
    payload_metrics = {
        "has_penalty": True,
        "additional_operational_cost_lifetime": 1000,
    }
    bev_results = {"tco": {"npv_total_cost": 120000}}
    diesel_results = {"tco": {"npv_total_cost": 110000}}
    fig = create_payload_comparison_chart(payload_metrics, bev_results, diesel_results)
    assert len(fig.data) == 3
    assert fig.layout.xaxis.title.text == "Vehicle Type"
    assert fig.layout.yaxis.title.text == "Lifetime TCO (AUD)"
