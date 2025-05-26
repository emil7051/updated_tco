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

from tco_app.src import Any, Dict, logging, st
from tco_app.src.data_loading import load_data
from tco_app.ui.calculation_orchestrator import CalculationOrchestrator
from tco_app.ui.context_builder import ContextDirector
from tco_app.ui.sidebar_renderer import SidebarRenderer
from tco_app.ui.input_hash import generate_input_hash

logger = logging.getLogger(__name__)


def get_context() -> Dict[str, Any]:
    """Return cached modelling context using builder pattern."""
    logger.info("Attempting to get context...")

    # Load data
    logger.debug("Loading data...")
    data_tables = load_data()
    logger.debug("Data loaded successfully.")

    # Always render sidebar to collect inputs
    logger.info("Rendering sidebar and collecting inputs...")
    sidebar_renderer = SidebarRenderer(data_tables)
    sidebar_inputs = sidebar_renderer.render_and_collect_inputs()
    
    # Generate hash of current inputs
    current_input_hash = generate_input_hash(sidebar_inputs)
    
    # Check if we have a cached context and if inputs haven't changed
    if (
        "ctx_cache" in st.session_state
        and "ctx_input_hash" in st.session_state
        and st.session_state["ctx_input_hash"] == current_input_hash
    ):
        logger.info("Returning cached context (inputs unchanged).")
        # Show caption for active scenario
        st.caption(f'Scenario: {sidebar_inputs["scenario_meta"]["name"]}')
        return st.session_state["ctx_cache"]

    logger.info("Inputs changed or no cache found, computing new context...")

    # Build UI context using builder pattern
    logger.info("Building UI context...")
    context_director = ContextDirector(data_tables)
    ui_context = context_director.build_ui_context(sidebar_inputs)
    logger.debug("UI context built successfully.")

    # Perform calculations
    logger.info("Starting calculations...")
    calculation_orchestrator = CalculationOrchestrator(data_tables, ui_context)
    complete_context = calculation_orchestrator.perform_calculations()

    # Show caption for active scenario
    st.caption(f'Scenario: {ui_context["scenario_meta"]["name"]}')

    # Cache context and input hash
    st.session_state["ctx_cache"] = complete_context
    st.session_state["ctx_input_hash"] = current_input_hash
    logger.info("Context computed and cached with input hash.")
    
    return complete_context
