"""UI Components module for reusable Streamlit components."""

import sys
import os

# Initialize exports list
__all__ = []

# Import with graceful fallbacks
try:
    from .components import render_info_tooltip
    __all__.append('render_info_tooltip')
except ImportError:
    pass

try:
    from .metric_cards import display_metric_card, display_comparison_metrics
    __all__.extend(['display_metric_card', 'display_comparison_metrics'])
except ImportError:
    pass

try:
    from .sensitivity_components import SensitivityContext, ParameterRangeCalculator
    __all__.extend(['SensitivityContext', 'ParameterRangeCalculator'])
except ImportError:
    # Try importing the module directly
    try:
        import tco_app.ui.components.sensitivity_components as sc
        SensitivityContext = sc.SensitivityContext
        ParameterRangeCalculator = sc.ParameterRangeCalculator
        __all__.extend(['SensitivityContext', 'ParameterRangeCalculator'])
    except ImportError:
        # Last resort: try direct file import
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            sensitivity_file = os.path.join(current_dir, 'sensitivity_components.py')
            if os.path.exists(sensitivity_file):
                import importlib.util
                spec = importlib.util.spec_from_file_location("sensitivity_components", sensitivity_file)
                sensitivity_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(sensitivity_module)
                SensitivityContext = sensitivity_module.SensitivityContext
                ParameterRangeCalculator = sensitivity_module.ParameterRangeCalculator
                __all__.extend(['SensitivityContext', 'ParameterRangeCalculator'])
        except Exception:
            pass

try:
    from .summary_displays import display_summary_metrics
    __all__.append('display_summary_metrics')
except ImportError:
    pass 