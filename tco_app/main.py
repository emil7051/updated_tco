"""Lightweight Streamlit entry point.

Provides a router for multi-page UI as part of modularisation step 5.2.
"""

import importlib
from typing import Dict

import streamlit as st

# ------- Page registry ----------------------------------------------------

PAGES: Dict[str, str] = {
	'Home': 'tco_app.ui.pages.home',
	'Cost Breakdown': 'tco_app.ui.pages.cost_breakdown',
	'Sensitivity': 'tco_app.ui.pages.sensitivity',
}

# ------- Page config ------------------------------------------------------

st.set_page_config(
	title='Electric vs. Diesel Truck TCO Model',
	page_icon='🚚',
	layout='wide',
	initial_sidebar_state='expanded',
)

# ------- Navigation -------------------------------------------------------

st.sidebar.title('Navigation')
selection = st.sidebar.radio('Go to', list(PAGES.keys()))

module_path = PAGES[selection]
page_module = importlib.import_module(module_path)

# Each page exposes a `render()` callable.
page_module.render() 