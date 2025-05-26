"""UI Components module for reusable Streamlit components."""

import sys
import os

# Ensure proper module resolution
try:
    from .components import render_info_tooltip
    from .metric_cards import display_metric_card, display_comparison_metrics
    from .sensitivity_components import (
        SensitivityContext,
        ParameterRangeCalculator
    )
    from .summary_displays import display_summary_metrics
except ImportError as e:
    # Add debugging information
    print(f"Import error in tco_app.ui.components: {e}")
    print(f"Current file: {__file__}")
    print(f"Python path: {sys.path[:3]}")
    
    # Try absolute imports as fallback
    try:
        from tco_app.ui.components.components import render_info_tooltip
        from tco_app.ui.components.metric_cards import display_metric_card, display_comparison_metrics
        from tco_app.ui.components.sensitivity_components import (
            SensitivityContext,
            ParameterRangeCalculator
        )
        from tco_app.ui.components.summary_displays import display_summary_metrics
    except ImportError:
        raise

__all__ = [
    'render_info_tooltip',
    'display_metric_card',
    'display_comparison_metrics',
    'SensitivityContext',
    'ParameterRangeCalculator',
    'display_summary_metrics'
] 