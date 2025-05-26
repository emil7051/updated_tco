import plotly.graph_objects as go

from tco_app.src.utils.safe_operations import safe_division
from tco_app.ui.utils.dto_accessors import (
    get_tco_per_km,
    get_energy_cost_per_km,
    get_annual_maintenance_cost,
    get_co2_per_km,
    get_infrastructure_npv_per_vehicle,
)


def create_key_metrics_chart(bev_results, diesel_results):
    """Create a radar chart comparing key performance metrics."""
    infrastructure_cost_per_km = 0
    
    # Handle infrastructure costs for BEV
    infra_npv = get_infrastructure_npv_per_vehicle(bev_results)
    if infra_npv:
        # Get annual_kms and truck_life_years from either DTO or dict
        if hasattr(bev_results, 'annual_kms'):
            annual_kms = bev_results.annual_kms
            truck_life_years = bev_results.truck_life_years
        else:
            annual_kms = bev_results.get("annual_kms", 0)
            truck_life_years = bev_results.get("truck_life_years", 0)
        
        total_kms = annual_kms * truck_life_years
        infrastructure_cost_per_km = (
            safe_division(
                infra_npv, total_kms, context="infra_npv/total_kms calculation"
            )
            if total_kms > 0
            else 0
        )

    # Get annual_kms for maintenance calculation
    if hasattr(bev_results, 'annual_kms'):
        bev_annual_kms = bev_results.annual_kms
        diesel_annual_kms = diesel_results.annual_kms
    else:
        bev_annual_kms = bev_results.get("annual_kms", 1)  # Avoid division by zero
        diesel_annual_kms = diesel_results.get("annual_kms", 1)

    # Get maintenance per km
    bev_maintenance_per_km = get_annual_maintenance_cost(bev_results) / bev_annual_kms if bev_annual_kms > 0 else 0
    diesel_maintenance_per_km = get_annual_maintenance_cost(diesel_results) / diesel_annual_kms if diesel_annual_kms > 0 else 0

    # Get externality per km
    if hasattr(bev_results, 'externalities_breakdown'):
        bev_externality_per_km = bev_results.externalities_breakdown.get("externality_per_km", 0)
    else:
        bev_externality_per_km = bev_results.get("externalities", {}).get("externality_per_km", 0)
    
    if hasattr(diesel_results, 'externalities_breakdown'):
        diesel_externality_per_km = diesel_results.externalities_breakdown.get("externality_per_km", 0)
    else:
        diesel_externality_per_km = diesel_results.get("externalities", {}).get("externality_per_km", 0)

    metrics = {
        "TCO per km": [
            get_tco_per_km(bev_results),
            get_tco_per_km(diesel_results),
        ],
        "Energy cost per km": [
            get_energy_cost_per_km(bev_results),
            get_energy_cost_per_km(diesel_results),
        ],
        "Maintenance per km": [
            bev_maintenance_per_km,
            diesel_maintenance_per_km,
        ],
        "CO₂ per km": [
            get_co2_per_km(bev_results),
            get_co2_per_km(diesel_results),
        ],
        "Externality cost": [
            bev_externality_per_km,
            diesel_externality_per_km,
        ],
        "Infrastructure per km": [infrastructure_cost_per_km, 0],
    }

    categories = list(metrics.keys())
    bev_values = [metrics[c][0] for c in categories]
    diesel_values = [metrics[c][1] for c in categories]
    
    # Normalise each metric to its maximum
    normalised = {}
    for i, c in enumerate(categories):
        max_val = max(bev_values[i], diesel_values[i])
        if max_val > 0:
            normalised[c] = [
                safe_division(bev_values[i], max_val, context=f"{c} BEV normalisation"),
                safe_division(diesel_values[i], max_val, context=f"{c} Diesel normalisation"),
            ]
        else:
            normalised[c] = [0, 0]
    
    bev_norm = [normalised[c][0] for c in categories]
    diesel_norm = [normalised[c][1] for c in categories]

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=bev_norm,
            theta=categories,
            fill="toself",
            name="BEV",
            line_color="#1f77b4",
        )
    )
    fig.add_trace(
        go.Scatterpolar(
            r=diesel_norm,
            theta=categories,
            fill="toself",
            name="Diesel",
            line_color="#ff7f0e",
        )
    )

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        title="Comparative Performance (Lower is Better)",
        height=500,
    )
    return fig
