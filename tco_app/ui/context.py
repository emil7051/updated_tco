"""Shared context & data-preparation utilities for Streamlit pages.

This module centralises the heavy-lifting previously performed in the monolithic
`tco_app.app` entry-point. It is intentionally *UI-aware*: the sidebar widgets
are rendered here so that all pages share the same interactive controls.

Down-stream pages call `get_context()` and receive a dictionary with
pre-computed results in the same structure used historically. The helper is
idempotent and cached in `st.session_state` under the key `'ctx_cache'` so the
expensive calculations run at most once per page refresh.

This module has been refactored to use the Builder pattern for better
maintainability and testability.
"""

from __future__ import annotations
from typing import Dict, Any

import streamlit as st

from tco_app.src.data_loading import load_data
from tco_app.ui.context_builder import ContextDirector
from tco_app.ui.calculation_orchestrator import CalculationOrchestrator

def get_context() -> Dict[str, Any]:
    """Return cached modelling context using builder pattern."""
    print("Attempting to get context...")
    
    # Basic cache – recompute when the user presses the Streamlit *rerun* button.
    if 'ctx_cache' in st.session_state:
        print("Returning cached context.")
        return st.session_state['ctx_cache']
    
    print("No cached context found, computing new context...")
    
    # Load data
    print("Loading data...")
    data_tables = load_data()
    print("Data loaded successfully.")
    
    # Build UI context using builder pattern
    print("Building UI context...")
    context_director = ContextDirector(data_tables)
    ui_context = context_director.build_ui_context()
    print("UI context built successfully.")
    
    # Perform calculations
    print("Starting calculations...")
    calculation_orchestrator = CalculationOrchestrator(data_tables, ui_context)
    complete_context = calculation_orchestrator.perform_calculations()
    
    # Show caption for active scenario
    st.caption(f'Scenario: {ui_context["scenario_meta"]["name"]}')
    
    # Cache and return
    st.session_state['ctx_cache'] = complete_context
    print("Context computed and cached.")
    return complete_context 