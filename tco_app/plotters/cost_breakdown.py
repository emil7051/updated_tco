"""Cost breakdown plotting functions."""

import plotly.express as px
import plotly.graph_objects as go

from tco_app.src import pd
from tco_app.src.constants import DataColumns, Drivetrain
from tco_app.ui.utils.dto_accessors import (
    get_acquisition_cost,
    get_annual_energy_cost,
    get_annual_maintenance_cost,
    get_battery_replacement_cost,
    get_residual_value,
    get_annual_operating_cost,
    get_infrastructure_npv_per_vehicle,
)


def create_cost_breakdown_chart(bev_results, diesel_results):
    """Create a stacked bar chart showing cost breakdown"""
    # Get truck_life_years from either DTO or dict
    if hasattr(bev_results, 'truck_life_years'):
        bev_truck_life_years = bev_results.truck_life_years
        diesel_truck_life_years = diesel_results.truck_life_years
    else:
        bev_truck_life_years = bev_results.get("truck_life_years", 0)
        diesel_truck_life_years = diesel_results.get("truck_life_years", 0)
    
    # Get annual costs safely
    if hasattr(bev_results, 'annual_costs_breakdown'):
        bev_insurance_annual = bev_results.annual_costs_breakdown.get("insurance_annual", 0)
        bev_registration_annual = bev_results.annual_costs_breakdown.get("registration_annual", 0)
    else:
        bev_insurance_annual = bev_results.get("annual_costs", {}).get("insurance_annual", 0)
        bev_registration_annual = bev_results.get("annual_costs", {}).get("registration_annual", 0)
    
    if hasattr(diesel_results, 'annual_costs_breakdown'):
        diesel_insurance_annual = diesel_results.annual_costs_breakdown.get("insurance_annual", 0)
        diesel_registration_annual = diesel_results.annual_costs_breakdown.get("registration_annual", 0)
    else:
        diesel_insurance_annual = diesel_results.get("annual_costs", {}).get("insurance_annual", 0)
        diesel_registration_annual = diesel_results.get("annual_costs", {}).get("registration_annual", 0)
    
    # Prepare data for BEV
    bev_costs = {
        "Acquisition": get_acquisition_cost(bev_results),
        "Energy": get_annual_energy_cost(bev_results) * bev_truck_life_years,
        "Maintenance": get_annual_maintenance_cost(bev_results) * bev_truck_life_years,
        "Insurance": bev_insurance_annual * bev_truck_life_years,
        "Registration": bev_registration_annual * bev_truck_life_years,
        "Battery Replacement": get_battery_replacement_cost(bev_results),
        "Residual Value": -get_residual_value(bev_results),
    }

    # Add infrastructure costs if available
    infra_npv = get_infrastructure_npv_per_vehicle(bev_results)
    if infra_npv:
        bev_costs["Infrastructure"] = infra_npv

    # Prepare data for Diesel
    diesel_costs = {
        "Acquisition": get_acquisition_cost(diesel_results),
        "Energy": get_annual_energy_cost(diesel_results) * diesel_truck_life_years,
        "Maintenance": get_annual_maintenance_cost(diesel_results) * diesel_truck_life_years,
        "Insurance": diesel_insurance_annual * diesel_truck_life_years,
        "Registration": diesel_registration_annual * diesel_truck_life_years,
        "Battery Replacement": 0,
        "Residual Value": -get_residual_value(diesel_results),
        "Infrastructure": 0,  # No infrastructure costs for diesel
    }

    categories = list(bev_costs.keys())
    bev_values = list(bev_costs.values())
    diesel_values = [diesel_costs.get(cat, 0) for cat in categories]

    df = pd.DataFrame(
        {
            "Category": categories + categories,
            "Cost": bev_values + diesel_values,
            "Vehicle Type": [Drivetrain.BEV.value] * len(categories)
            + [Drivetrain.DIESEL.value] * len(categories),
        }
    )

    fig = px.bar(
        df,
        x="Vehicle Type",
        y="Cost",
        color="Category",
        title="Lifetime Cost Breakdown",
        labels={"Cost": "Cost (AUD)", "Vehicle Type": "Vehicle Type"},
        color_discrete_sequence=px.colors.qualitative.Safe,
        height=500,
    )

    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig


def create_annual_costs_chart(bev_results, diesel_results, truck_life_years):
    """Create a line chart showing annual costs over time"""
    years = list(range(1, truck_life_years + 1))

    # Initial cumulative costs include acquisition (and infrastructure for BEV)
    bev_cumulative = [get_acquisition_cost(bev_results)]
    diesel_cumulative = [get_acquisition_cost(diesel_results)]

    # Handle infrastructure costs for BEV
    if hasattr(bev_results, 'infrastructure_costs_breakdown'):
        infra_breakdown = bev_results.infrastructure_costs_breakdown
    else:
        infra_breakdown = bev_results.get("infrastructure_costs", {})
    
    if infra_breakdown:
        fleet_size = infra_breakdown.get("fleet_size", 1)
        if "infrastructure_price_with_incentives" in infra_breakdown:
            bev_cumulative[0] += infra_breakdown["infrastructure_price_with_incentives"] / fleet_size
        elif DataColumns.INFRASTRUCTURE_PRICE in infra_breakdown:
            bev_cumulative[0] += infra_breakdown[DataColumns.INFRASTRUCTURE_PRICE] / fleet_size

    for year in range(1, truck_life_years):
        bev_annual = get_annual_operating_cost(bev_results)
        diesel_annual = get_annual_operating_cost(diesel_results)

        # Check for battery replacement
        if hasattr(bev_results, 'battery_replacement_year'):
            if bev_results.battery_replacement_year == year:
                bev_annual += bev_results.battery_replacement_cost or 0
        elif bev_results.get("battery_replacement_year") == year:
            bev_annual += bev_results.get("battery_replacement_cost", 0)

        # Handle infrastructure maintenance and replacement
        if infra_breakdown:
            fleet_size = infra_breakdown.get("fleet_size", 1)
            infra_maintenance = infra_breakdown.get("annual_maintenance", 0) / fleet_size
            bev_annual += infra_maintenance

            service_life = infra_breakdown.get("service_life_years", float('inf'))
            if service_life > 0 and year % service_life == 0 and year < truck_life_years:
                if "infrastructure_price_with_incentives" in infra_breakdown:
                    bev_annual += infra_breakdown["infrastructure_price_with_incentives"] / fleet_size
                elif DataColumns.INFRASTRUCTURE_PRICE in infra_breakdown:
                    bev_annual += infra_breakdown[DataColumns.INFRASTRUCTURE_PRICE] / fleet_size

        bev_cumulative.append(bev_cumulative[-1] + bev_annual)
        diesel_cumulative.append(diesel_cumulative[-1] + diesel_annual)

    # Subtract residual value at the end
    bev_cumulative[-1] -= get_residual_value(bev_results)
    diesel_cumulative[-1] -= get_residual_value(diesel_results)

    df = pd.DataFrame(
        {
            "Year": years + years,
            "Cumulative Cost": bev_cumulative + diesel_cumulative,
            "Vehicle Type": [Drivetrain.BEV.value] * len(years)
            + [Drivetrain.DIESEL.value] * len(years),
        }
    )

    fig = px.line(
        df,
        x="Year",
        y="Cumulative Cost",
        color="Vehicle Type",
        title="Cumulative Costs Over Time",
        labels={"Cumulative Cost": "Cumulative Cost (AUD)", "Year": "Year"},
        color_discrete_map={
            Drivetrain.BEV.value: "#1f77b4",
            Drivetrain.DIESEL.value: "#ff7f0e",
        },
        height=400,
    )

    # Find intersection point (price parity)
    intersection_year = None
    intersection_cost = None

    for i in range(len(years) - 1):
        bev_cost1, bev_cost2 = bev_cumulative[i], bev_cumulative[i + 1]
        diesel_cost1, diesel_cost2 = diesel_cumulative[i], diesel_cumulative[i + 1]
        if (bev_cost1 - diesel_cost1) * (bev_cost2 - diesel_cost2) <= 0:
            year1 = years[i]
            if bev_cost2 - bev_cost1 != diesel_cost2 - diesel_cost1:
                t = (diesel_cost1 - bev_cost1) / (
                    (bev_cost2 - bev_cost1) - (diesel_cost2 - diesel_cost1)
                )
                intersection_year = year1 + t
                intersection_cost = bev_cost1 + t * (bev_cost2 - bev_cost1)
                break

    if intersection_year is not None and intersection_cost is not None:
        fig.add_trace(
            go.Scatter(
                x=[intersection_year],
                y=[intersection_cost],
                mode="markers",
                marker=dict(size=12, color="green", symbol="star"),
                name="Price Parity Point",
                hoverinfo="text",
                text=f"Price Parity at {intersection_year:.1f} years",
            )
        )

    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig
