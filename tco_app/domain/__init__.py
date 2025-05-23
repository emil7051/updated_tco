from __future__ import annotations

"""Domain package exposing cohesive business-logic modules.

Each sub-module wraps or hosts the authoritative implementation for its
bounded-context. The API is stable and independent from any legacy monoliths
so that callers can migrate incrementally.
"""

from importlib import import_module as _imp

__all__ = [
    "energy",
    "finance",
    "externalities",
    "sensitivity",
]

for _name in __all__:
    _imp(f"tco_app.domain.{_name}")
