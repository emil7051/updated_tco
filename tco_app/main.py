"""Lightweight Streamlit entry point.

Provides a router for multi-page UI as part of modularisation step 5.2.
"""

import importlib
import sys
from pathlib import Path

# Ensure project root directory is on sys.path so that ``tco_app`` can be
# imported when this file is executed directly (e.g. ``streamlit run tco_app/main.py``)
# This allows imports like `from tco_app.ui.pages import ...`
_project_root = Path(__file__).resolve().parent.parent

# Handle both local and containerised environments
# In containerised environments, the path might be /mount/src/updated_tco
# So we need to ensure both the actual root and potential mount points are in path
if _project_root.as_posix() not in sys.path:
    sys.path.insert(0, _project_root.as_posix())

# Also check if we're in a container environment and add appropriate paths
current_file = Path(__file__).resolve()
if '/mount/src/' in str(current_file):
    # We're in a container, add the mount source directory
    mount_root = Path('/mount/src/updated_tco')
    if mount_root.exists() and mount_root.as_posix() not in sys.path:
        sys.path.insert(0, mount_root.as_posix())

# Now import tco_app modules after path is properly set
from tco_app.src import UI_CONFIG, Dict, st

# ------- Page registry ----------------------------------------------------

PAGES: Dict[str, str] = {
    "Home": "tco_app.ui.pages.home",
    "Cost Breakdown": "tco_app.ui.pages.cost_breakdown",
    "Sensitivity": "tco_app.ui.pages.sensitivity",
}

# ------- Page config ------------------------------------------------------

st.set_page_config(
    page_title=UI_CONFIG.PAGE_TITLE,
    page_icon=UI_CONFIG.PAGE_ICON,
    layout=UI_CONFIG.PAGE_LAYOUT,
    initial_sidebar_state=UI_CONFIG.SIDEBAR_STATE,
)

# ------- Navigation -------------------------------------------------------

st.sidebar.title("Navigation")
selection = st.sidebar.radio("Go to", list(PAGES.keys()))

module_path = PAGES[selection]
page_module = importlib.import_module(module_path)

# Each page exposes a `render()` callable.
page_module.render()
