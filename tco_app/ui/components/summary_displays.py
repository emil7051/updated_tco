from tco_app.src import st
from tco_app.src.constants import DataColumns
from tco_app.ui.utils.dto_accessors import (
    get_tco_lifetime,
    get_tco_per_km,
    get_tco_per_tonne_km,
    get_vehicle_name,
    get_annual_operating_cost,
)


def display_summary_metrics(bev_results, diesel_results):
    """
    Display summary metrics for both vehicles with improved visual hierarchy
    """
    st.markdown(
        "<h1 style='text-align: center; margin-bottom: 2rem;'>Total Cost of Ownership Analysis</h1>",
        unsafe_allow_html=True,
    )

    # Key insight section first
    bev_npv = get_tco_lifetime(bev_results)
    diesel_npv = get_tco_lifetime(diesel_results)
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
            # Handle both DTO and dict cases for vehicle data access
            if hasattr(bev_results, 'vehicle_id'):
                # DTO case
                vehicle_data = bev_results.vehicle_data if hasattr(bev_results, 'vehicle_data') else {}
                # Get vehicle model name from vehicle_data
                if hasattr(vehicle_data, 'get'):
                    vehicle_name = vehicle_data.get(DataColumns.VEHICLE_MODEL, bev_results.vehicle_id)
                else:
                    vehicle_name = bev_results.vehicle_id
            else:
                # Dict case
                vehicle_data = bev_results.get('vehicle_data', {})
                vehicle_name = vehicle_data.get(DataColumns.VEHICLE_MODEL, 'Unknown')
            
            st.markdown(f"### {vehicle_name}")

            # Vehicle details
            st.markdown("**Vehicle Type:** Battery Electric")
            
            # Safe access to vehicle data fields
            payload = vehicle_data.get(DataColumns.PAYLOAD_T, 0) if hasattr(vehicle_data, 'get') else 0
            range_km = vehicle_data.get(DataColumns.RANGE_KM, 'N/A') if hasattr(vehicle_data, 'get') else 'N/A'
            
            st.markdown(f"**Payload Capacity:** {payload:.1f} tonnes")
            st.markdown(f"**Range:** {range_km if range_km == 'N/A' else f'{range_km:,.0f}'} km")

            # TCO metrics
            st.markdown(f"**Lifetime TCO:** ${bev_npv:,.0f}")
            bev_tco_km = get_tco_per_km(bev_results)
            st.markdown(f"**Cost per km:** ${bev_tco_km:.2f}")
            bev_tco_tkm = get_tco_per_tonne_km(bev_results)
            st.markdown(f"**Cost per tonne-km:** ${bev_tco_tkm:.3f}")
            bev_annual = get_annual_operating_cost(bev_results)
            st.markdown(f"**Annual Operating Cost:** ${bev_annual:,.0f}")

    with col2:
        with st.container():
            # Handle both DTO and dict cases for vehicle data access
            if hasattr(diesel_results, 'vehicle_id'):
                # DTO case
                vehicle_data = diesel_results.vehicle_data if hasattr(diesel_results, 'vehicle_data') else {}
                # Get vehicle model name from vehicle_data
                if hasattr(vehicle_data, 'get'):
                    vehicle_name = vehicle_data.get(DataColumns.VEHICLE_MODEL, diesel_results.vehicle_id)
                else:
                    vehicle_name = diesel_results.vehicle_id
            else:
                # Dict case
                vehicle_data = diesel_results.get('vehicle_data', {})
                vehicle_name = vehicle_data.get(DataColumns.VEHICLE_MODEL, 'Unknown')
            
            st.markdown(f"### {vehicle_name}")

            # Vehicle details
            st.markdown("**Vehicle Type:** Diesel")
            
            # Safe access to vehicle data fields
            payload = vehicle_data.get(DataColumns.PAYLOAD_T, 0) if hasattr(vehicle_data, 'get') else 0
            range_km = vehicle_data.get(DataColumns.RANGE_KM, 'N/A') if hasattr(vehicle_data, 'get') else 'N/A'
            
            st.markdown(f"**Payload Capacity:** {payload:.1f} tonnes")
            st.markdown(f"**Range:** {range_km if range_km == 'N/A' else f'{range_km:,.0f}'} km")

            # TCO metrics
            st.markdown(f"**Lifetime TCO:** ${diesel_npv:,.0f}")
            diesel_tco_km = get_tco_per_km(diesel_results)
            st.markdown(f"**Cost per km:** ${diesel_tco_km:.2f}")
            diesel_tco_tkm = get_tco_per_tonne_km(diesel_results)
            st.markdown(f"**Cost per tonne-km:** ${diesel_tco_tkm:.3f}")
            diesel_annual = get_annual_operating_cost(diesel_results)
            st.markdown(f"**Annual Operating Cost:** ${diesel_annual:,.0f}")
