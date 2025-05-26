from __future__ import annotations

"""Sensitivity analysis package – splits the former monolithic module into
smaller, responsibility-focused helpers for maintainability.
"""

from .externality import perform_externality_sensitivity
from .metrics import calculate_comparative_metrics, calculate_comparative_metrics_from_dto
from .single_param import perform_sensitivity_analysis, perform_sensitivity_analysis_with_dtos, create_sensitivity_adapter
from .tornado import calculate_tornado_data, calculate_tornado_data_with_dtos

__all__ = [
    "calculate_comparative_metrics",
    "calculate_comparative_metrics_from_dto",
    "perform_sensitivity_analysis",
    "perform_sensitivity_analysis_with_dtos",
    "create_sensitivity_adapter",
    "calculate_tornado_data",
    "calculate_tornado_data_with_dtos",
    "perform_externality_sensitivity",
]
