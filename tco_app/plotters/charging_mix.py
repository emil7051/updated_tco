"""Charging mix plotting functions."""

import plotly.express as px
import plotly.graph_objects as go

from tco_app.src.constants import DataColumns
from tco_app.src.utils.energy import weighted_electricity_price


def create_charging_mix_chart(bev_results):
    """Create a pie chart visualising the charging mix distribution."""
    if "charging_mix" not in bev_results:
        fig = go.Figure()
        fig.update_layout(title="No Charging Mix Data Available", height=300)
        return fig

    labels, values, prices = [], [], []
    for charging_id, pct in bev_results["charging_mix"].items():
        if pct > 0:
            option = (
                bev_results["charging_options"]
                .loc[
                    bev_results["charging_options"][DataColumns.CHARGING_ID]
                    == charging_id
                ]
                .iloc[0]
            )
            labels.append(option[DataColumns.CHARGING_APPROACH])
            values.append(pct * 100)
            prices.append(option[DataColumns.PER_KWH_PRICE])

    hover_text = [
        f"{label}: {v:.1f}%<br>Price: ${p:.2f}/kWh"
        for label, v, p in zip(labels, values, prices)
    ]

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hovertext=hover_text,
            hoverinfo="text",
            textinfo="percent",
            marker=dict(colors=px.colors.qualitative.Safe[: len(labels)]),
        )
    )

    charging_mix = {
        cid: bev_results["charging_mix"][cid]
        for cid in bev_results["charging_mix"]
        if bev_results["charging_mix"][cid] > 0
    }
    weighted_price = (
        weighted_electricity_price(charging_mix, bev_results["charging_options"])
        if sum(values)
        else None
    )
    subtitle = (
        f"Weighted Average: ${weighted_price:.2f}/kWh"
        if weighted_price
        else "No charging mix data"
    )

    fig.update_layout(
        title={
            "text": f"Charging Mix Distribution<br><sup>{subtitle}</sup>",
            "x": 0.5,
            "y": 0.95,
            "xanchor": "center",
            "yanchor": "top",
        },
        height=400,
    )
    return fig
