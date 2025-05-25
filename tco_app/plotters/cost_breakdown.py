"""Cost breakdown plotting functions."""

from tco_app.src import pd
from tco_app.src.constants import DataColumns, Drivetrain
import plotly.express as px
import plotly.graph_objects as go


def create_cost_breakdown_chart(bev_results, diesel_results):
    """Create a stacked bar chart showing cost breakdown"""
    # Prepare data for BEV
    bev_costs = {
        "Acquisition": bev_results["acquisition_cost"],
        "Energy": bev_results["annual_costs"]["annual_energy_cost"]
        * bev_results["truck_life_years"],
        "Maintenance": bev_results["annual_costs"]["annual_maintenance_cost"]
        * bev_results["truck_life_years"],
        "Insurance": bev_results["annual_costs"]["insurance_annual"]
        * bev_results["truck_life_years"],
        "Registration": bev_results["annual_costs"]["registration_annual"]
        * bev_results["truck_life_years"],
        "Battery Replacement": bev_results["battery_replacement"],
        "Residual Value": -bev_results["residual_value"],
    }

    # Add infrastructure costs if available
    if "infrastructure_costs" in bev_results:
        if "npv_per_vehicle_with_incentives" in bev_results["infrastructure_costs"]:
            bev_costs["Infrastructure"] = bev_results["infrastructure_costs"][
                "npv_per_vehicle_with_incentives"
            ]
        else:
            bev_costs["Infrastructure"] = bev_results["infrastructure_costs"][
                "npv_per_vehicle"
            ]

    # Prepare data for Diesel
    diesel_costs = {
        "Acquisition": diesel_results["acquisition_cost"],
        "Energy": diesel_results["annual_costs"]["annual_energy_cost"]
        * diesel_results["truck_life_years"],
        "Maintenance": diesel_results["annual_costs"]["annual_maintenance_cost"]
        * diesel_results["truck_life_years"],
        "Insurance": diesel_results["annual_costs"]["insurance_annual"]
        * diesel_results["truck_life_years"],
        "Registration": diesel_results["annual_costs"]["registration_annual"]
        * diesel_results["truck_life_years"],
        "Battery Replacement": 0,
        "Residual Value": -diesel_results["residual_value"],
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
    bev_cumulative = [bev_results["acquisition_cost"]]
    diesel_cumulative = [diesel_results["acquisition_cost"]]

    if "infrastructure_costs" in bev_results:
        if (
            "infrastructure_price_with_incentives"
            in bev_results["infrastructure_costs"]
        ):
            bev_cumulative[0] += bev_results["infrastructure_costs"][
                "infrastructure_price_with_incentives"
            ] / bev_results["infrastructure_costs"].get("fleet_size", 1)
        else:
            bev_cumulative[0] += bev_results["infrastructure_costs"][
                DataColumns.INFRASTRUCTURE_PRICE
            ] / bev_results["infrastructure_costs"].get("fleet_size", 1)

    for year in range(1, truck_life_years):
        bev_annual = bev_results["annual_costs"]["annual_operating_cost"]
        diesel_annual = diesel_results["annual_costs"]["annual_operating_cost"]

        if bev_results.get("battery_replacement_year") == year:
            bev_annual += bev_results.get("battery_replacement_cost", 0)

        if "infrastructure_costs" in bev_results:
            infra_maintenance = bev_results["infrastructure_costs"][
                "annual_maintenance"
            ] / bev_results["infrastructure_costs"].get("fleet_size", 1)
            bev_annual += infra_maintenance

            service_life = bev_results["infrastructure_costs"]["service_life_years"]
            if year % service_life == 0 and year < truck_life_years:
                if (
                    "infrastructure_price_with_incentives"
                    in bev_results["infrastructure_costs"]
                ):
                    bev_annual += bev_results["infrastructure_costs"][
                        "infrastructure_price_with_incentives"
                    ] / bev_results["infrastructure_costs"].get("fleet_size", 1)
                else:
                    bev_annual += bev_results["infrastructure_costs"][
                        DataColumns.INFRASTRUCTURE_PRICE
                    ] / bev_results["infrastructure_costs"].get("fleet_size", 1)

        bev_cumulative.append(bev_cumulative[-1] + bev_annual)
        diesel_cumulative.append(diesel_cumulative[-1] + diesel_annual)

    bev_cumulative[-1] -= bev_results["residual_value"]
    diesel_cumulative[-1] -= diesel_results["residual_value"]

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
