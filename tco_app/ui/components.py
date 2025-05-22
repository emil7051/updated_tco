"""UI components for Streamlit pages (temporary proxy).

Re-exports everything from the legacy `tco_app.src.ui_components` module so
new code can import `tco_app.ui.components` while existing call-sites keep
working. This file will eventually become the canonical implementation once
all imports are migrated and the old module is removed.
"""

from importlib import import_module as _import_module

_legacy = _import_module('tco_app.src.ui_components')

__all__ = [name for name in dir(_legacy) if not name.startswith('_')]

globals().update({name: getattr(_legacy, name) for name in __all__}) 