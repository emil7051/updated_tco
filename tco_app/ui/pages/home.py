import streamlit as st

# Legacy app contains full interactive UI.
# We invoke its `main()` function to preserve behaviour while we gradually
# decompose the monolith (see modularisation step 5.2).

from tco_app.ui.context import get_context
from tco_app.ui.components import (
	display_summary_metrics,
	display_comparison_metrics,
)


def render():
	"""Render dashboard landing page – summary + key comparison metrics."""
	ctx = get_context()
	bev_results = ctx['bev_results']
	diesel_results = ctx['diesel_results']
	comparison_metrics = ctx['comparison_metrics']

	display_summary_metrics(bev_results, diesel_results)
	display_comparison_metrics(comparison_metrics)

	st.experimental_set_query_params(page='home') 