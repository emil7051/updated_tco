import plotly.graph_objects as go

from tco_app.src.constants import ParameterKeys


def create_sensitivity_chart(
    bev_results, diesel_results, parameter, param_range, recalculated_tcos
):
    """Create a sensitivity analysis chart showing how TCO changes with parameter values."""
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=param_range,
            y=[t["bev"]["tco_lifetime"] for t in recalculated_tcos],
            mode="lines+markers",
            name="BEV TCO",
            line=dict(color="#2E86C1", width=3),
            marker=dict(size=8),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=param_range,
            y=[t["diesel"]["tco_lifetime"] for t in recalculated_tcos],
            mode="lines+markers",
            name="Diesel TCO",
            line=dict(color="#E67E22", width=3),
            marker=dict(size=8),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=param_range,
            y=[
                t["bev"]["tco_lifetime"] - t["diesel"]["tco_lifetime"]
                for t in recalculated_tcos
            ],
            mode="lines+markers",
            name="TCO Difference (BEV - Diesel)",
            line=dict(color="#8E44AD", width=2, dash="dash"),
            marker=dict(size=6),
        )
    )

    current_value = None
    if parameter == "Annual Distance (km)":
        current_value = bev_results["annual_kms"]
    elif parameter == "Diesel Price ($/L)":
        current_value = (
            diesel_results["vehicle_data"].get(ParameterKeys.DIESEL_PRICE)
            if "vehicle_data" in diesel_results
            else None
        )
    elif parameter == "Vehicle Lifetime (years)":
        current_value = bev_results["truck_life_years"]
    elif parameter == "Discount Rate (%)":
        current_value = bev_results.get("discount_rate")
    elif parameter == "Electricity Price ($/kWh)":
        current_value = bev_results.get("weighted_electricity_price")

    if current_value is not None and current_value in param_range:
        fig.add_vline(
            x=current_value,
            line_width=2,
            line_dash="solid",
            line_color="green",
            annotation_text="Current Value",
            annotation_position="top right",
        )

    break_even_value = None
    for i in range(len(param_range) - 1):
        bev1, diesel1 = (
            recalculated_tcos[i]["bev"]["tco_lifetime"],
            recalculated_tcos[i]["diesel"]["tco_lifetime"],
        )
        bev2, diesel2 = (
            recalculated_tcos[i + 1]["bev"]["tco_lifetime"],
            recalculated_tcos[i + 1]["diesel"]["tco_lifetime"],
        )
        if (bev1 - diesel1) * (bev2 - diesel2) <= 0:
            x1, x2 = param_range[i], param_range[i + 1]
            y1, y2 = bev1 - diesel1, bev2 - diesel2
            if y1 != y2:
                break_even_value = x1 - y1 * (x2 - x1) / (y2 - y1)
                break

    if break_even_value is not None:
        bev_at_be = next(
            (
                b["bev"]["tco_lifetime"]
                for b in recalculated_tcos
                if b["bev"]["tco_lifetime"] - b["diesel"]["tco_lifetime"] == 0
            ),
            None,
        )
        fig.add_trace(
            go.Scatter(
                x=[break_even_value],
                y=[bev_at_be] if bev_at_be else [],
                mode="markers",
                marker=dict(
                    color="red",
                    size=12,
                    symbol="star",
                    line=dict(color="black", width=2),
                ),
                name=f"Break-even at {break_even_value:.2f}",
            )
        )

    unit = {
        "Annual Distance (km)": "km",
        "Diesel Price ($/L)": "$/L",
        "Vehicle Lifetime (years)": "years",
        "Discount Rate (%)": "%",
        "Electricity Price ($/kWh)": "$/kWh",
    }.get(parameter, "")

    fig.update_layout(
        title=f"TCO Sensitivity to {parameter}",
        xaxis_title=f"{parameter} {unit}",
        yaxis_title="Lifetime TCO (AUD)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        hovermode="x unified",
        margin=dict(l=20, r=20, t=60, b=20),
        height=500,
    )
    return fig
