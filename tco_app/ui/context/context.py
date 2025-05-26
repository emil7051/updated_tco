"""Context module for managing UI state and dependencies.

This module provides a way to manage context throughout the UI components
and pages, ensuring consistent data access and calculations.
"""

from __future__ import annotations

from tco_app.src import Any, Dict, logging, st
from tco_app.src.data_loading import load_data
from tco_app.ui.orchestration import CalculationOrchestrator
from tco_app.ui.context.context_builder import ContextDirector
from tco_app.ui.renderers import SidebarRenderer
from tco_app.ui.context.input_hash import generate_input_hash

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
