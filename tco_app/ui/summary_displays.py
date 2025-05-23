from tco_app.src import st
from tco_app.src.constants import Drivetrain, DataColumns
from tco_app.src.utils.pandas_helpers import to_scalar
from tco_app.src.utils.safe_operations import safe_division
def display_summary_metrics(bev_results, diesel_results):
    """
    Display summary metrics for both vehicles
    """
    st.subheader("TCO Summary")
    
    col1, col2 = st.columns(2)
    
    with col1:
        bev_npv = to_scalar(bev_results['tco']['npv_total_cost'])
        bev_tco_km = to_scalar(bev_results['tco']['tco_per_km'])
        bev_tco_tkm = to_scalar(bev_results['tco']['tco_per_tonne_km'])
        bev_annual = to_scalar(bev_results['annual_costs']['annual_operating_cost'])
        bev_html = f"""
        <div class="vehicle-summary-card bev" style="margin-bottom: 0;">
            <h5 style="color: #0B3954; font-weight: 600; margin-bottom: 1rem;">Battery Electric Vehicle</h5>
            <div style="background-color: rgba(8, 126, 139, 0.1); padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem;">
                <span style="color: #333333; font-weight: 600;">Model:</span> <span style="color: #333333;">{bev_results['vehicle_data'][DataColumns.VEHICLE_MODEL]}</span>
            </div>
            <div style="background-color: rgba(8, 126, 139, 0.1); padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem;">
                <span style="color: #333333; font-weight: 600;">Payload:</span> <span style="color: #333333;">{bev_results['vehicle_data'][DataColumns.PAYLOAD_T]} tonnes</span>
            </div>
            <div style="background-color: rgba(8, 126, 139, 0.1); padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem;">
                <span style="color: #333333; font-weight: 600;">Range:</span> <span style="color: #333333;">{bev_results['vehicle_data'].get(DataColumns.RANGE_KM, 'N/A')} km</span>
            </div>
            <div style="background-color: rgba(8, 126, 139, 0.1); padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem;">
                <span style="color: #333333; font-weight: 600;">Lifetime TCO:</span> <span style="color: #333333;">${bev_npv:,.2f}</span>
            </div>
            <div style="background-color: rgba(8, 126, 139, 0.1); padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem;">
                <span style="color: #333333; font-weight: 600;">TCO per km:</span> <span style="color: #333333;">${bev_tco_km:,.2f}</span>
            </div>
            <div style="background-color: rgba(8, 126, 139, 0.1); padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem;">
                <span style="color: #333333; font-weight: 600;">TCO per tonne-km:</span> <span style="color: #333333;">${bev_tco_tkm:,.2f}</span>
            </div>
            <div style="background-color: rgba(8, 126, 139, 0.1); padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem;">
                <span style="color: #333333; font-weight: 600;">Annual Operating Cost:</span> <span style="color: #333333;">${bev_annual:,.2f}</span>
            </div>
        </div>
        """
        st.markdown(bev_html, unsafe_allow_html=True)
    
    with col2:
        diesel_npv = to_scalar(diesel_results['tco']['npv_total_cost'])
        diesel_tco_km = to_scalar(diesel_results['tco']['tco_per_km'])
        diesel_tco_tkm = to_scalar(diesel_results['tco']['tco_per_tonne_km'])
        diesel_annual = to_scalar(diesel_results['annual_costs']['annual_operating_cost'])
        diesel_html = f"""
        <div class="vehicle-summary-card diesel" style="margin-bottom: 0;">
            <h5 style="color: #0B3954; font-weight: 600; margin-bottom: 1rem;">Diesel Vehicle</h5>
            <div style="background-color: rgba(255, 193, 7, 0.1); padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem;">
                <span style="color: #333333; font-weight: 600;">Model:</span> <span style="color: #333333;">{diesel_results['vehicle_data'][DataColumns.VEHICLE_MODEL]}</span>
            </div>
            <div style="background-color: rgba(255, 193, 7, 0.1); padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem;">
                <span style="color: #333333; font-weight: 600;">Payload:</span> <span style="color: #333333;">{diesel_results['vehicle_data'][DataColumns.PAYLOAD_T]} tonnes</span>
            </div>
            <div style="background-color: rgba(255, 193, 7, 0.1); padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem;">
                <span style="color: #333333; font-weight: 600;">Range:</span> <span style="color: #333333;">{diesel_results['vehicle_data'].get(DataColumns.RANGE_KM, 'N/A')} km</span>
            </div>
            <div style="background-color: rgba(255, 193, 7, 0.1); padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem;">
                <span style="color: #333333; font-weight: 600;">Lifetime TCO:</span> <span style="color: #333333;">${diesel_npv:,.2f}</span>
            </div>
            <div style="background-color: rgba(255, 193, 7, 0.1); padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem;">
                <span style="color: #333333; font-weight: 600;">TCO per km:</span> <span style="color: #333333;">${diesel_tco_km:,.2f}</span>
            </div>
            <div style="background-color: rgba(255, 193, 7, 0.1); padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem;">
                <span style="color: #333333; font-weight: 600;">TCO per tonne-km:</span> <span style="color: #333333;">${diesel_tco_tkm:,.2f}</span>
            </div>
            <div style="background-color: rgba(255, 193, 7, 0.1); padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem;">
                <span style="color: #333333; font-weight: 600;">Annual Operating Cost:</span> <span style="color: #333333;">${diesel_annual:,.2f}</span>
            </div>
        </div>
        """
        st.markdown(diesel_html, unsafe_allow_html=True) 