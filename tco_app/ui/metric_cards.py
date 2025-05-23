from tco_app.src import st
from tco_app.src.utils.pandas_helpers import to_scalar

from tco_app.src.utils.safe_operations import safe_division
def display_metric_card(title, value, unit, tooltip=None):
    """
    Display a metric in a formatted card
    """
    val = to_scalar(value)
    metric_html = f"""
    <div class="metric-card">
        <div style="font-size: 0.8rem; color: #505A64;">{title}</div>
        <div class="metric-value">{val:,.2f} {unit}</div>
    </div>
    """
    
    st.markdown(metric_html, unsafe_allow_html=True)
    if tooltip:
        st.caption(tooltip)

def display_comparison_metrics(comparative_metrics):
    """
    Display the comparative metrics in a formatted way
    """
    st.markdown('<div class="comparison-card">', unsafe_allow_html=True)
    st.subheader("Comparison Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        display_metric_card(
            "Upfront Cost Difference",
            comparative_metrics['upfront_cost_difference'],
            "AUD",
            "Additional upfront cost of BEV compared to diesel"
        )
    
    with col2:
        display_metric_card(
            "Annual Operating Savings",
            comparative_metrics['annual_operating_savings'],
            "AUD/year",
            "Annual operating cost savings with BEV"
        )
    
    with col3:
        display_metric_card(
            "Price Parity Point",
            comparative_metrics['price_parity_year'],
            "years",
            "Time until BEV and diesel costs become equal"
        )
    
    # Payback highlight section
    if comparative_metrics['price_parity_year'] < 100:  # Show if there is a reasonable payback period
        payback_html = f"""
        <div class="payback-highlight">
            <strong style="color: #17a2b8;">Price Parity Analysis:</strong> <span style="color: #333333;">The electric vehicle's higher initial cost 
            (${comparative_metrics['upfront_cost_difference']:,.2f}) is balanced by lower operating costs after {comparative_metrics['price_parity_year']:,.1f} years
            through annual savings of ${comparative_metrics['annual_operating_savings']:,.2f}.</span>
        </div>
        """
        st.markdown(payback_html, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        display_metric_card(
            "Lifetime Emission Savings",
            comparative_metrics['emission_savings_lifetime'] / 1000,
            "tonnes CO₂",
            "Total emissions avoided over vehicle lifetime"
        )
    
    with col2:
        display_metric_card(
            "BEV to Diesel TCO Ratio",
            comparative_metrics['bev_to_diesel_tco_ratio'],
            "",
            "Ratio of BEV TCO to diesel TCO (values < 1 favor BEV)"
        )
    
    with col3:
        display_metric_card(
            "Abatement Cost",
            comparative_metrics['abatement_cost'],
            "$/tonne CO₂",
            "Cost per tonne of CO₂ emissions avoided"
        )
    
    st.markdown('</div>', unsafe_allow_html=True) 