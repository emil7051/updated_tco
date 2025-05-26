"""Context director for orchestrating UI context building."""

from tco_app.src import Any, Dict, pd


class ContextDirector:
    """Orchestrates context building using the builder pattern."""

    def __init__(self, data_tables: Dict[str, pd.DataFrame]):
        self.data_tables = data_tables

    def build_ui_context(self, sidebar_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Build complete UI context from pre-collected sidebar inputs.
        
        Args:
            sidebar_inputs: Pre-collected inputs from SidebarRenderer
            
        Returns:
            Complete UI context with sidebar inputs
        """
        # Simply return the sidebar inputs as they already contain everything needed
        return sidebar_inputs
