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
from tco_app.src import Dict, Any

from tco_app.src import st, logging

from tco_app.src.data_loading import load_data
from tco_app.ui.context_builder import ContextDirector
from tco_app.ui.calculation_orchestrator import CalculationOrchestrator

logger = logging.getLogger(__name__)


def get_context() -> Dict[str, Any]:
    """Return cached modelling context using builder pattern."""
    logger.info("Attempting to get context...")

    # Basic cache – recompute when the user presses the Streamlit *rerun* button.
    if "ctx_cache" in st.session_state:
        logger.info("Returning cached context.")
        return st.session_state["ctx_cache"]

    logger.info("No cached context found, computing new context...")

    # Load data
    logger.debug("Loading data...")
    data_tables = load_data()
    logger.debug("Data loaded successfully.")

    # Build UI context using builder pattern
    logger.info("Building UI context...")
    context_director = ContextDirector(data_tables)
    ui_context = context_director.build_ui_context()
    logger.debug("UI context built successfully.")

    # Perform calculations
    logger.info("Starting calculations...")
    calculation_orchestrator = CalculationOrchestrator(data_tables, ui_context)
    complete_context = calculation_orchestrator.perform_calculations()

    # Show caption for active scenario
    st.caption(f'Scenario: {ui_context["scenario_meta"]["name"]}')

    # Cache and return
    st.session_state["ctx_cache"] = complete_context
    logger.info("Context computed and cached.")
    return complete_context
