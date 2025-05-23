from tco_app.src import st
from tco_app.src.constants import Drivetrain, DataColumns
from tco_app.src.utils.pandas_helpers import to_scalar
from tco_app.src.utils.safe_operations import safe_division

def display_summary_metrics(bev_results, diesel_results):
    """
    Display summary metrics for both vehicles with improved visual hierarchy
    """
    st.markdown("<h1 style='text-align: center; margin-bottom: 2rem;'>Total Cost of Ownership Analysis</h1>", unsafe_allow_html=True)
    
    # Key insight section first
    bev_npv = to_scalar(bev_results['tco']['npv_total_cost'])
    diesel_npv = to_scalar(diesel_results['tco']['npv_total_cost'])
    savings = diesel_npv - bev_npv
    
    if savings > 0:
        insight_html = f"""
        <div class="insight-card">
            <h3 style="margin-top: 0;"> Electric Vehicle Delivers Lower Total Cost</h3>
            <div class="savings-amount">${savings:,.0f}</div>
            <div class="savings-description">
                Total savings over vehicle lifetime compared to diesel
            </div>
        </div>
        """
        st.markdown(insight_html, unsafe_allow_html=True)
    
    # Vehicle comparison cards
    col1, col2 = st.columns(2)
    
    with col1:
        bev_tco_km = to_scalar(bev_results['tco']['tco_per_km'])
        bev_tco_tkm = to_scalar(bev_results['tco']['tco_per_tonne_km'])
        bev_annual = to_scalar(bev_results['annual_costs']['annual_operating_cost'])
        
        bev_html = f"""
        <div class="vehicle-card electric">
            <h5><span class="vehicle-icon">E</span> {bev_results['vehicle_data'][DataColumns.VEHICLE_MODEL]}</h5>
            
            <div class="data-row">
                <span class="data-label">Vehicle Type</span>
                <span class="data-value">Battery Electric</span>
            </div>
            
            <div class="data-row">
                <span class="data-label">Payload Capacity</span>
                <span class="data-value">{bev_results['vehicle_data'][DataColumns.PAYLOAD_T]} tonnes</span>
            </div>
            
            <div class="data-row">
                <span class="data-label">Range</span>
                <span class="data-value">{bev_results['vehicle_data'].get(DataColumns.RANGE_KM, 'N/A')} km</span>
            </div>
            
            <div class="data-row highlight">
                <span class="data-label">Lifetime TCO</span>
                <span class="data-value">${bev_npv:,.0f}</span>
            </div>
            
            <div class="data-row">
                <span class="data-label">Cost per km</span>
                <span class="data-value">${bev_tco_km:.2f}</span>
            </div>
            
            <div class="data-row">
                <span class="data-label">Cost per tonne-km</span>
                <span class="data-value">${bev_tco_tkm:.3f}</span>
            </div>
            
            <div class="data-row">
                <span class="data-label">Annual Operating Cost</span>
                <span class="data-value">${bev_annual:,.0f}</span>
            </div>
        </div>
        """
        st.markdown(bev_html, unsafe_allow_html=True)
    
    with col2:
        diesel_tco_km = to_scalar(diesel_results['tco']['tco_per_km'])
        diesel_tco_tkm = to_scalar(diesel_results['tco']['tco_per_tonne_km'])
        diesel_annual = to_scalar(diesel_results['annual_costs']['annual_operating_cost'])
        
        diesel_html = f"""
        <div class="vehicle-card diesel">
            <h5><span class="vehicle-icon">D</span> {diesel_results['vehicle_data'][DataColumns.VEHICLE_MODEL]}</h5>
            
            <div class="data-row">
                <span class="data-label">Vehicle Type</span>
                <span class="data-value">Diesel</span>
            </div>
            
            <div class="data-row">
                <span class="data-label">Payload Capacity</span>
                <span class="data-value">{diesel_results['vehicle_data'][DataColumns.PAYLOAD_T]} tonnes</span>
            </div>
            
            <div class="data-row">
                <span class="data-label">Range</span>
                <span class="data-value">{diesel_results['vehicle_data'].get(DataColumns.RANGE_KM, 'N/A')} km</span>
            </div>
            
            <div class="data-row highlight">
                <span class="data-label">Lifetime TCO</span>
                <span class="data-value">${diesel_npv:,.0f}</span>
            </div>
            
            <div class="data-row">
                <span class="data-label">Cost per km</span>
                <span class="data-value">${diesel_tco_km:.2f}</span>
            </div>
            
            <div class="data-row">
                <span class="data-label">Cost per tonne-km</span>
                <span class="data-value">${diesel_tco_tkm:.3f}</span>
            </div>
            
            <div class="data-row">
                <span class="data-label">Annual Operating Cost</span>
                <span class="data-value">${diesel_annual:,.0f}</span>
            </div>
        </div>
        """
        st.markdown(diesel_html, unsafe_allow_html=True)