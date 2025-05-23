"""Pytest configuration ensuring project root is importable as a package.

This allows test modules to import `tco_app` without requiring an editable
install or manual PYTHONPATH exports."""

from __future__ import annotations

import sys
from pathlib import Path

# Calculate repository root (two directories up from this file: tests/ -> tco_app/ -> repo root)
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
