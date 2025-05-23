from tco_app.src import st
from tco_app.src.utils.pandas_helpers import to_scalar
from tco_app.src.utils.safe_operations import safe_division


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
        display_metric_card(
            "Payback Period",
            comparative_metrics["price_parity_year"],
            "years",
            "Time to recover additional upfront investment",
        )

    # Payback period insight
    if comparative_metrics["price_parity_year"] < 100:
        payback_years = comparative_metrics["price_parity_year"]
        upfront_diff = comparative_metrics["upfront_cost_difference"]
        annual_savings = comparative_metrics["annual_operating_savings"]

        st.info(
            f"**Investment Recovery Timeline:** "
            f"The electric vehicle's higher upfront cost of **${upfront_diff:,.0f}** will be recovered in "
            f"**{payback_years:.1f} years** through annual operating savings of **${annual_savings:,.0f}**."
        )

    # Environmental and efficiency metrics
    st.markdown("### 🌱 Environmental Impact")

    col1, col2, col3 = st.columns(3)

    with col1:
        display_metric_card(
            "Lifetime CO₂ Reduction",
            comparative_metrics["emission_savings_lifetime"] / 1000,
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
                if abatement_cost < 50
                else "negative" if abatement_cost > 100 else None
            ),
        )

    # Summary insight
    if percentage_savings > 0:
        st.success(
            f"**Investment Summary:** {percentage_savings:.1f}% lower total cost of ownership "
            f"while reducing {comparative_metrics['emission_savings_lifetime'] / 1000:.1f} tonnes of CO₂"
        )
