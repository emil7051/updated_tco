from tco_app.src import st
from tco_app.ui.components import display_comparison_metrics, display_summary_metrics
from tco_app.ui.context import get_context

# Legacy app contains full interactive UI.
# We invoke its `main()` function to preserve behaviour while we gradually
# decompose the monolith (see modularisation step 5.2).


def render():
    """Render dashboard landing page – summary + key comparison metrics."""
    ctx = get_context()
    bev_results = ctx["bev_results"]
    diesel_results = ctx["diesel_results"]
    comparison_metrics = ctx["comparison_metrics"]

    display_summary_metrics(bev_results, diesel_results)
    display_comparison_metrics(comparison_metrics)
    
    # Display payload penalty warning if applicable
    if "comparison" in ctx and hasattr(ctx["comparison"], "payload_penalties"):
        payload_penalties = ctx["comparison"].payload_penalties
        if payload_penalties and payload_penalties.get("has_penalty", False):
            st.warning(
                f"⚠️ **Payload Consideration**: The BEV has {payload_penalties['payload_difference_percentage']:.1f}% "
                f"less payload capacity than the diesel vehicle. This analysis includes an additional "
                f"${payload_penalties['additional_operational_cost_lifetime']:,.0f} in lifetime costs to account for "
                f"the {payload_penalties['additional_trips_percentage']:.1f}% more trips required to transport the same freight volume."
            )

    st.query_params["page"] = "home"
