import copy

import plotly.graph_objects as go

from tco_app.domain.finance import calculate_payload_penalty_costs
from tco_app.src import pd
from tco_app.src.config import UI_CONFIG


def create_payload_comparison_chart(payload_metrics, bev_results, diesel_results):
    """Stacked bar chart showing the impact of payload penalty on TCO."""
    fig = go.Figure()
    
    # Get TCO values from DTOs
    diesel_tco = getattr(diesel_results, "tco_total_lifetime", 0)
    bev_tco = getattr(bev_results, "tco_total_lifetime", 0)
    
    fig.add_trace(
        go.Bar(
            x=["Diesel"],
            y=[diesel_tco],
            name="Total TCO",
            marker_color="#ff7f0e",
        )
    )
    fig.add_trace(
        go.Bar(
            x=["BEV (Standard)", "BEV (Payload-Adjusted)"],
            y=[bev_tco, bev_tco],
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
        # Create temporary dictionaries to work with the existing payload calculation
        # Since calculate_payload_penalty_costs expects dictionaries, we'll create them
        bev_temp = {
            "annual_kms": distance,
            "energy_cost_per_km": getattr(bev_results, "energy_cost_per_km", 0),
            "annual_costs": getattr(bev_results, "annual_costs_breakdown", {}).copy(),
            "tco": {
                "npv_total_cost": getattr(bev_results, "tco_total_lifetime", 0),
            },
            "vehicle_data": getattr(bev_results, "vehicle_data", {}),
        }
        
        diesel_temp = {
            "annual_kms": distance,
            "energy_cost_per_km": getattr(diesel_results, "energy_cost_per_km", 0),
            "annual_costs": getattr(diesel_results, "annual_costs_breakdown", {}).copy(),
            "tco": {
                "npv_total_cost": getattr(diesel_results, "tco_total_lifetime", 0),
            },
            "vehicle_data": getattr(diesel_results, "vehicle_data", {}),
        }

        # Calculate annual energy costs
        bev_annual_energy = bev_temp["energy_cost_per_km"] * distance
        diesel_annual_energy = diesel_temp["energy_cost_per_km"] * distance
        bev_temp["annual_costs"]["annual_energy_cost"] = bev_annual_energy
        diesel_temp["annual_costs"]["annual_energy_cost"] = diesel_annual_energy

        # Update annual operating costs
        bev_temp["annual_costs"]["annual_operating_cost"] = (
            bev_annual_energy
            + bev_temp["annual_costs"].get("annual_maintenance_cost", 0)
            + bev_temp["annual_costs"].get("insurance_annual", 0)
            + bev_temp["annual_costs"].get("registration_annual", 0)
        )

        diesel_temp["annual_costs"]["annual_operating_cost"] = (
            diesel_annual_energy
            + diesel_temp["annual_costs"].get("annual_maintenance_cost", 0)
            + diesel_temp["annual_costs"].get("insurance_annual", 0)
            + diesel_temp["annual_costs"].get("registration_annual", 0)
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
        x=min(distances) + (max(distances) - min(distances)) * UI_CONFIG.PLOT_TEXT_OFFSET_FACTOR,
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
