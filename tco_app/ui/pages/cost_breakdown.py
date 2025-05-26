from tco_app.plotters import (
    create_annual_costs_chart,
    create_charging_mix_chart,
    create_cost_breakdown_chart,
)
from tco_app.src import st
from tco_app.src.constants import DataColumns, Drivetrain
from tco_app.ui.context import get_context
from tco_app.ui.utils.dto_accessors import (
    get_vehicle_name,
    get_drivetrain,
    has_charging_mix,
    is_bev,
    get_infrastructure_price,
    get_infrastructure_annual_maintenance,
    get_infrastructure_npv_per_vehicle,
    get_infrastructure_service_life,
    get_infrastructure_replacement_cycles,
    get_infrastructure_subsidy_rate,
    get_infrastructure_subsidy_amount,
    get_daily_kwh_required,
    get_charging_time_per_day,
    get_charger_power,
    get_max_vehicles_per_charger,
)


def render():
    ctx = get_context()
    bev_results = ctx["bev_results"]
    diesel_results = ctx["diesel_results"]
    truck_life_years = ctx["truck_life_years"]

    st.subheader("Lifetime Cost Components")
    chart = create_cost_breakdown_chart(bev_results, diesel_results)
    st.plotly_chart(chart, use_container_width=True)

    # Charging mix visual
    if has_charging_mix(bev_results):
        st.subheader("Charging Mix")
        cm_chart = create_charging_mix_chart(bev_results)
        st.plotly_chart(cm_chart, use_container_width=True)

    # Infrastructure + charging requirements
    if is_bev(bev_results):
        st.subheader("Infrastructure Costs")
        infra_col1, infra_col2 = st.columns(2)
        with infra_col1:
            st.metric(
                "Infrastructure Capital Cost",
                f"${get_infrastructure_price(bev_results):,.0f}",
            )
            st.metric(
                "Annual Maintenance",
                f"${get_infrastructure_annual_maintenance(bev_results):,.0f}/year",
            )
            st.metric(
                "Cost Per Vehicle",
                f"${get_infrastructure_npv_per_vehicle(bev_results) or 0:,.0f}",
            )
        with infra_col2:
            st.metric(
                "Service Life",
                f"{get_infrastructure_service_life(bev_results)} years",
            )
            st.metric(
                "Replacement Cycles",
                f"{get_infrastructure_replacement_cycles(bev_results)}",
            )
            subsidy_rate = get_infrastructure_subsidy_rate(bev_results)
            if subsidy_rate > 0:
                st.metric(
                    "Infrastructure Subsidy",
                    f"${get_infrastructure_subsidy_amount(bev_results):,.0f}",
                    delta=f"{subsidy_rate * 100:.0f}%",
                )

        st.subheader("Charging Requirements")
        cc1, cc2 = st.columns(2)
        with cc1:
            st.metric(
                "Daily Energy Required",
                f"{get_daily_kwh_required(bev_results):.1f} kWh",
            )
            st.metric(
                "Charging Time Per Day",
                f"{get_charging_time_per_day(bev_results):.2f} hours",
            )
        with cc2:
            st.metric(
                "Charger Power",
                f"{get_charger_power(bev_results):.0f} kW",
            )
            st.metric(
                "Maximum Vehicles Per Charger",
                f"{min(100, get_max_vehicles_per_charger(bev_results)):.1f}",
            )

    st.subheader("Costs Over Time")
    annual_chart = create_annual_costs_chart(
        bev_results, diesel_results, truck_life_years
    )
    st.plotly_chart(annual_chart, use_container_width=True, key="annual_costs_chart")
