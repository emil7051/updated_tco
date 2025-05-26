"""UI components for Streamlit pages.

Exports all UI components for use across the application.
"""

import streamlit as st

def render_info_tooltip(text: str, tooltip: str) -> None:
    """Render text with an info tooltip."""
    col1, col2 = st.columns([20, 1])
    with col1:
        st.markdown(text)
    with col2:
        st.info("ℹ️", help=tooltip)

# Define what gets exported when someone does "from tco_app.ui.components import *"
__all__ = [
    "display_metric_card",
    "display_comparison_metrics",
    "display_summary_metrics",
    "CalculationOrchestrator",
    "ContextDirector",
]
