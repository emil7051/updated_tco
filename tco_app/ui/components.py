"""UI components for Streamlit pages.

Exports all UI components for use across the application.
"""

# Import all UI components from their modules
from tco_app.ui.metric_cards import (
    display_metric_card,
    display_comparison_metrics
)

from tco_app.ui.summary_displays import (
    display_summary_metrics
)

from tco_app.ui.calculation_orchestrator import (
    CalculationOrchestrator
)

from tco_app.ui.context_builder import (
    ContextDirector
)

# Define what gets exported when someone does "from tco_app.ui.components import *"
__all__ = [
    'display_metric_card',
    'display_comparison_metrics',
    'display_summary_metrics',
    'CalculationOrchestrator',
    'ContextDirector'
] 