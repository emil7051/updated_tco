import copy

import plotly.graph_objects as go

from tco_app.domain.finance import calculate_payload_penalty_costs
from tco_app.src import pd


def create_payload_comparison_chart(payload_metrics, bev_results, diesel_results):
    """Stacked bar chart showing the impact of payload penalty on TCO."""
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=["Diesel"],
            y=[diesel_results["tco"]["npv_total_cost"]],
            name="Total TCO",
            marker_color="#ff7f0e",
        )
    )
    fig.add_trace(
        go.Bar(
            x=["BEV (Standard)", "BEV (Payload-Adjusted)"],
            y=[
                bev_results["tco"]["npv_total_cost"],
                bev_results["tco"]["npv_total_cost"],
            ],
            name="Base TCO",
            marker_color="#1f77b4",
        )
    )

    if payload_metrics["has_penalty"]:
        fig.add_trace(
            go.Bar(
                x=["BEV (Standard)", "BEV (Payload-Adjusted)"],
                y=[0, payload_metrics["additional_operational_cost_lifetime"]],
                name="Payload Penalty Costs",
                marker_color="#d62728",
            )
        )

    fig.update_layout(
        barmode="stack",
        title="Lifetime TCO Comparison with Payload Adjustment",
        xaxis_title="Vehicle Type",
        yaxis_title="Lifetime TCO (AUD)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=500,
    )
    return fig


def create_payload_sensitivity_chart(
    bev_results, diesel_results, financial_params, distances
):
    """Show how payload penalty affects TCO ratio at different annual distances."""
    results = []
    for distance in distances:
        bev_temp, diesel_temp = copy.deepcopy(bev_results), copy.deepcopy(
            diesel_results
        )
        bev_temp["annual_kms"] = distance
        diesel_temp["annual_kms"] = distance

        bev_annual_energy = bev_results["energy_cost_per_km"] * distance
        diesel_annual_energy = diesel_results["energy_cost_per_km"] * distance
        bev_temp["annual_costs"]["annual_energy_cost"] = bev_annual_energy
        diesel_temp["annual_costs"]["annual_energy_cost"] = diesel_annual_energy

        bev_temp["annual_costs"]["annual_operating_cost"] = (
            bev_annual_energy
            + bev_temp["annual_costs"]["annual_maintenance_cost"]
            + bev_temp["annual_costs"]["insurance_annual"]
            + bev_temp["annual_costs"]["registration_annual"]
        )

        diesel_temp["annual_costs"]["annual_operating_cost"] = (
            diesel_annual_energy
            + diesel_temp["annual_costs"]["annual_maintenance_cost"]
            + diesel_temp["annual_costs"]["insurance_annual"]
            + diesel_temp["annual_costs"]["registration_annual"]
        )

        payload_metrics = calculate_payload_penalty_costs(
            bev_temp, diesel_temp, financial_params
        )

        results.append(
            {
                "distance": distance,
                "standard_tco_ratio": bev_temp["tco"]["npv_total_cost"]
                / diesel_temp["tco"]["npv_total_cost"],
                "adjusted_tco_ratio": (
                    payload_metrics["bev_adjusted_lifetime_tco"]
                    / diesel_temp["tco"]["npv_total_cost"]
                    if payload_metrics["has_penalty"]
                    else bev_temp["tco"]["npv_total_cost"]
                    / diesel_temp["tco"]["npv_total_cost"]
                ),
            }
        )

    results_df = pd.DataFrame(results)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=results_df["distance"],
            y=results_df["standard_tco_ratio"],
            mode="lines+markers",
            name="Standard TCO Ratio (BEV/Diesel)",
            line=dict(color="#1f77b4"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=results_df["distance"],
            y=results_df["adjusted_tco_ratio"],
            mode="lines+markers",
            name="Payload-Adjusted TCO Ratio",
            line=dict(color="#d62728"),
        )
    )

    fig.add_shape(
        type="line",
        x0=min(distances),
        y0=1,
        x1=max(distances),
        y1=1,
        line=dict(color="green", width=2, dash="dash"),
    )
    fig.add_annotation(
        x=min(distances) + (max(distances) - min(distances)) * 0.05,
        y=1.02,
        text="Break-even point (BEV = Diesel)",
        showarrow=False,
        font=dict(color="green"),
    )

    fig.update_layout(
        title="Impact of Annual Distance on TCO Ratio with Payload Adjustment",
        xaxis_title="Annual Distance (km)",
        yaxis_title="TCO Ratio (BEV/Diesel)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=500,
    )
    return fig
