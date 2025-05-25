from tco_app.src import st
from tco_app.src.constants import DataColumns
from tco_app.src.utils.pandas_helpers import to_scalar


def display_summary_metrics(bev_results, diesel_results):
    """
    Display summary metrics for both vehicles with improved visual hierarchy
    """
    st.markdown(
        "<h1 style='text-align: center; margin-bottom: 2rem;'>Total Cost of Ownership Analysis</h1>",
        unsafe_allow_html=True,
    )

    # Key insight section first
    bev_npv = to_scalar(bev_results["tco"]["npv_total_cost"])
    diesel_npv = to_scalar(diesel_results["tco"]["npv_total_cost"])
    savings = diesel_npv - bev_npv

    if savings > 0:
        st.success(" **Electric Vehicle Delivers Lower Total Cost**")
        st.info(
            f"**${savings:,.0f}** total savings over vehicle lifetime compared to diesel"
        )
    else:
        st.warning(" **Diesel Vehicle Has Lower Total Cost**")
        st.info(
            f"Electric vehicle costs **${abs(savings):,.0f}** more over vehicle lifetime"
        )

    # Vehicle comparison cards
    col1, col2 = st.columns(2)

    with col1:
        with st.container():
            st.markdown(
                f"### {bev_results['vehicle_data'][DataColumns.VEHICLE_MODEL]}"
            )

            # Vehicle details
            st.markdown("**Vehicle Type:** Battery Electric")
            st.markdown(
                f"**Payload Capacity:** {bev_results['vehicle_data'][DataColumns.PAYLOAD_T]:.1f} tonnes"
            )
            st.markdown(
                f"**Range:** {bev_results['vehicle_data'].get(DataColumns.RANGE_KM, 'N/A'):,.0f} km"
            )

            # TCO metrics
            st.markdown(f"**Lifetime TCO:** ${bev_npv:,.0f}")
            bev_tco_km = to_scalar(bev_results["tco"]["tco_per_km"])
            st.markdown(f"**Cost per km:** ${bev_tco_km:.2f}")
            bev_tco_tkm = to_scalar(bev_results["tco"]["tco_per_tonne_km"])
            st.markdown(f"**Cost per tonne-km:** ${bev_tco_tkm:.3f}")
            bev_annual = to_scalar(bev_results["annual_costs"]["annual_operating_cost"])
            st.markdown(f"**Annual Operating Cost:** ${bev_annual:,.0f}")

    with col2:
        with st.container():
            st.markdown(
                f"### {diesel_results['vehicle_data'][DataColumns.VEHICLE_MODEL]}"
            )

            # Vehicle details
            st.markdown("**Vehicle Type:** Diesel")
            st.markdown(
                f"**Payload Capacity:** {diesel_results['vehicle_data'][DataColumns.PAYLOAD_T]:.1f} tonnes"
            )
            st.markdown(
                f"**Range:** {diesel_results['vehicle_data'].get(DataColumns.RANGE_KM, 'N/A'):,.0f} km"
            )

            # TCO metrics
            st.markdown(f"**Lifetime TCO:** ${diesel_npv:,.0f}")
            diesel_tco_km = to_scalar(diesel_results["tco"]["tco_per_km"])
            st.markdown(f"**Cost per km:** ${diesel_tco_km:.2f}")
            diesel_tco_tkm = to_scalar(diesel_results["tco"]["tco_per_tonne_km"])
            st.markdown(f"**Cost per tonne-km:** ${diesel_tco_tkm:.3f}")
            diesel_annual = to_scalar(
                diesel_results["annual_costs"]["annual_operating_cost"]
            )
            st.markdown(f"**Annual Operating Cost:** ${diesel_annual:,.0f}")
