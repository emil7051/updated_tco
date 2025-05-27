from tco_app.src import st, UNIT_CONVERSIONS, VALIDATION_LIMITS
from tco_app.src.utils.pandas_helpers import to_scalar


def display_metric_card(title, value, unit, tooltip=None, metric_type=None):
    """
    Display a metric in a formatted card with improved styling
    """
    val = to_scalar(value)

    # Format the value based on unit type
    if unit == "years":
        formatted_val = f"{val:.1f}"
    elif unit == "%" or unit == "":
        formatted_val = f"{val:.2f}"
    elif "CO₂" in unit:
        formatted_val = f"{val:.1f}"
    else:
        formatted_val = f"{val:,.0f}"

    # Display the metric using Streamlit's metric component
    delta_color = "normal"
    if metric_type == "positive" and val > 0:
        delta_color = "normal"
    elif metric_type == "negative" and val < 0:
        delta_color = "inverse"

    st.metric(
        label=title,
        value=f"{formatted_val} {unit}",
        delta=None,
        delta_color=delta_color,
        help=tooltip,
    )


def display_comparison_metrics(comparative_metrics):
    """
    Display the comparative metrics with improved visual hierarchy
    """
    st.markdown("## Key Performance Indicators")

    # Financial metrics section
    st.markdown("### 💰 Financial Comparison")

    col1, col2, col3 = st.columns(3)

    with col1:
        display_metric_card(
            "Upfront Cost Difference",
            comparative_metrics["upfront_cost_difference"],
            "AUD",
            "Additional initial investment for electric vehicle",
            metric_type="negative",
        )

    with col2:
        display_metric_card(
            "Annual Operating Savings",
            comparative_metrics["annual_operating_savings"],
            "AUD/year",
            "Yearly savings in fuel and maintenance costs",
            metric_type="positive",
        )

    with col3:
        if comparative_metrics["price_parity_year"] < VALIDATION_LIMITS.MAX_REASONABLE_PARITY_YEARS:
            display_metric_card(
                "Price Parity Year",
                comparative_metrics["price_parity_year"],
                "years",
                "First year when BEV lifetime cost equals diesel",
            )

    # Payback period insight
    if comparative_metrics["price_parity_year"] < 100:
        payback_years = comparative_metrics["price_parity_year"]
        upfront_diff = comparative_metrics["upfront_cost_difference"]
        annual_savings = comparative_metrics["annual_operating_savings"]

        # Use multiple info boxes to avoid the rendering bug with multiple formatted values
        st.markdown("**Investment Recovery Timeline**")
        st.info(f"💵 Upfront BEV Premium: ${upfront_diff:,.0f}")
        st.info(f"💰 Annual Operating Savings: ${annual_savings:,.0f}")
        st.info(f"📅 Payback Period: {payback_years:.1f} years")

    # Environmental and efficiency metrics
    st.markdown("### 🌱 Environmental Impact")

    col1, col2, col3 = st.columns(3)

    with col1:
        display_metric_card(
            "Lifetime CO₂ Reduction",
            comparative_metrics["emission_savings_lifetime"] / UNIT_CONVERSIONS.KG_TO_TONNES,
            "tonnes CO₂",
            "Total emissions avoided over vehicle lifetime",
            metric_type="positive",
        )

    with col2:
        tco_ratio = comparative_metrics["bev_to_diesel_tco_ratio"]
        percentage_savings = (1 - tco_ratio) * 100 if tco_ratio < 1 else 0

        display_metric_card(
            "Total Cost Savings",
            percentage_savings,
            "%",
            "Percentage reduction in total cost of ownership",
            metric_type="positive" if percentage_savings > 0 else None,
        )

    with col3:
        abatement_cost = comparative_metrics["abatement_cost"]

        display_metric_card(
            "Carbon Abatement Cost",
            abatement_cost,
            "$/tonne CO₂",
            "Cost effectiveness of emissions reduction",
            metric_type=(
                "positive"
                if abatement_cost < VALIDATION_LIMITS.ABATEMENT_COST_LOW_THRESHOLD
                else "negative" if abatement_cost > VALIDATION_LIMITS.ABATEMENT_COST_HIGH_THRESHOLD else None
            ),
        )

    # Summary insight
    if percentage_savings > 0:
        st.success(
            f"**Investment Summary:** {percentage_savings:.1f}% lower total cost of ownership "
            f"while reducing {comparative_metrics['emission_savings_lifetime'] / UNIT_CONVERSIONS.KG_TO_TONNES:.1f} tonnes of CO₂"
        )
