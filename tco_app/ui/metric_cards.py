from tco_app.src import st
from tco_app.src.utils.pandas_helpers import to_scalar
from tco_app.src.utils.safe_operations import safe_division

def display_metric_card(title, value, unit, tooltip=None, metric_type=None):
    """
    Display a metric in a formatted card with improved styling
    """
    val = to_scalar(value)
    
    # Determine card class based on metric type
    card_class = "metric-card"
    if metric_type == "positive" and val > 0:
        card_class += " positive"
    elif metric_type == "negative" and val < 0:
        card_class += " negative"
    
    # Format the value based on unit type
    if unit == "years":
        formatted_val = f"{val:.1f}"
    elif unit == "%" or unit == "":
        formatted_val = f"{val:.2f}"
    elif "CO₂" in unit:
        formatted_val = f"{val:.1f}"
    else:
        formatted_val = f"{val:,.0f}"
    
    metric_html = f"""
    <div class="{card_class}">
        <div class="metric-label">{title}</div>
        <div class="metric-value">{formatted_val}</div>
        <div class="metric-unit">{unit}</div>
    </div>
    """
    
    st.markdown(metric_html, unsafe_allow_html=True)
    if tooltip:
        st.caption(f"ℹ️ {tooltip}")

def display_comparison_metrics(comparative_metrics):
    """
    Display the comparative metrics with improved visual hierarchy
    """
    st.markdown("<h2 style='margin-top: 3rem; margin-bottom: 2rem;'>Key Performance Indicators</h2>", unsafe_allow_html=True)
    
    # Financial metrics section
    st.markdown("<h3 style='color: #0066CC; margin-bottom: 1rem;'>💰 Financial Comparison</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        display_metric_card(
            "Upfront Cost Difference",
            comparative_metrics['upfront_cost_difference'],
            "AUD",
            "Additional initial investment for electric vehicle",
            metric_type="negative"
        )
    
    with col2:
        display_metric_card(
            "Annual Operating Savings",
            comparative_metrics['annual_operating_savings'],
            "AUD/year",
            "Yearly savings in fuel and maintenance costs",
            metric_type="positive"
        )
    
    with col3:
        display_metric_card(
            "Payback Period",
            comparative_metrics['price_parity_year'],
            "years",
            "Time to recover additional upfront investment"
        )
    
    # Payback period insight
    if comparative_metrics['price_parity_year'] < 100:
        payback_years = comparative_metrics['price_parity_year']
        upfront_diff = comparative_metrics['upfront_cost_difference']
        annual_savings = comparative_metrics['annual_operating_savings']
        
        payback_html = f"""
        <div class="payback-highlight">
            <div class="payback-content">
                <strong>Investment Recovery Timeline</strong>
                <p style="margin-top: 0.5rem; margin-bottom: 0;">
                    The electric vehicle's higher upfront cost of <strong>${upfront_diff:,.0f}</strong> will be recovered in 
                    <strong>{payback_years:.1f} years</strong> through annual operating savings of <strong>${annual_savings:,.0f}</strong>.
                </p>
            </div>
        </div>
        """
        st.markdown(payback_html, unsafe_allow_html=True)
    
    # Environmental and efficiency metrics
    st.markdown("<h3 style='color: #00A86B; margin-top: 2rem; margin-bottom: 1rem;'>🌱 Environmental Impact</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        display_metric_card(
            "Lifetime CO₂ Reduction",
            comparative_metrics['emission_savings_lifetime'] / 1000,
            "tonnes CO₂",
            "Total emissions avoided over vehicle lifetime",
            metric_type="positive"
        )
    
    with col2:
        tco_ratio = comparative_metrics['bev_to_diesel_tco_ratio']
        percentage_savings = (1 - tco_ratio) * 100 if tco_ratio < 1 else 0
        
        display_metric_card(
            "Total Cost Savings",
            percentage_savings,
            "%",
            "Percentage reduction in total cost of ownership",
            metric_type="positive" if percentage_savings > 0 else None
        )
    
    with col3:
        abatement_cost = comparative_metrics['abatement_cost']
        
        display_metric_card(
            "Carbon Abatement Cost",
            abatement_cost,
            "$/tonne CO₂",
            "Cost effectiveness of emissions reduction",
            metric_type="positive" if abatement_cost < 50 else "negative" if abatement_cost > 100 else None
        )
    
    # Summary insight
    if percentage_savings > 0:
        summary_html = f"""
        <div class="comparison-summary">
            <h3>Investment Summary</h3>
            <div class="savings-amount">{percentage_savings:.1f}%</div>
            <div class="savings-description">
                Lower total cost of ownership while reducing {comparative_metrics['emission_savings_lifetime'] / 1000:.1f} tonnes of CO₂
            </div>
        </div>
        """
        st.markdown(summary_html, unsafe_allow_html=True)