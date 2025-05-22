"""DEPRECATED: Monolithic Streamlit implementation.

The application has been migrated to a modular multi-page architecture.
This stub remains only for backwards-compatibility – importers should switch
to `tco_app.main` instead.  Executing this file at runtime will emit a
deprecation warning and immediately import the new entry-point so that legacy
CLI commands like `streamlit run tco_app/app.py` continue to function.
"""

from importlib import import_module
import warnings
from pathlib import Path
import sys

# Ensure project root directory is on sys.path so that ``tco_app`` can be
# imported when this file is executed directly (e.g. ``streamlit run tco_app/app.py``)
project_root = Path(__file__).resolve().parent.parent
if project_root.as_posix() not in map(str, sys.path):
	# Prepend to give it highest priority whilst avoiding duplicates
	sys.path.insert(0, project_root.as_posix())


def main() -> None:
	"""Redirect to new Streamlit router."""
	warnings.warn('`tco_app.app` is deprecated – use `tco_app.main` instead', DeprecationWarning)
	import_module('tco_app.main')


if __name__ == '__main__':
	main()
