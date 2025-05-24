import importlib
import sys
from types import ModuleType
from unittest.mock import MagicMock
from tco_app.src.constants import Drivetrain
import tco_app.domain.sensitivity as _sens
import tco_app.domain.finance as _fin


class _StreamlitStub(ModuleType):
    def __getattr__(self, name):
        # Provide simple fallbacks for common widget functions so page code runs.
        if name in {"selectbox", "radio"}:
            return lambda label, options=None, **kwargs: options[0] if options else ""
        elif name in {"number_input", "slider"}:
            return lambda *a, **k: k.get("value", 1)
        elif name in {"columns"}:
            return lambda *a, **k: [MagicMock() for _ in range(a[0] if a else 1)]
        elif name == "spinner":

            class _CM:
                def __enter__(self):
                    return None

                def __exit__(self, *exc):
                    return False

            return lambda *a, **k: _CM()
        elif name in {"expander"}:

            class _CM2:
                def __enter__(self):
                    return None

                def __exit__(self, *exc):
                    return False

            return lambda *a, **k: _CM2()
        elif name in {
            "metric",
            "plotly_chart",
            "markdown",
            "subheader",
            "info",
            "warning",
            "caption",
            "title",
            "header",
            "text",
            "download_button",
            "dataframe",
            "success",
            "experimental_set_query_params",
        }:
            return lambda *a, **k: None
        return MagicMock()


# Inject stub before any Streamlit import occurs
sys.modules["streamlit"] = _StreamlitStub("streamlit")


def _smoke_render(module_path: str) -> None:
    # Inject lightweight context stub so rendering code can run without heavy
    # pandas/plotly dependencies when executed in the mocked Streamlit env.
    import tco_app.ui.context as _ctx

    _ctx.get_context = lambda: {
        "bev_results": {
            "vehicle_data": {"vehicle_drivetrain": Drivetrain.BEV},
            "infrastructure_costs": {
                "infrastructure_price": 0,
                "annual_maintenance": 0,
                "npv_per_vehicle": 0,
                "service_life_years": 0,
                "replacement_cycles": 0,
            },
            "charging_requirements": {
                "daily_kwh_required": 0,
                "charging_time_per_day": 0,
                "charger_power": 0,
                "max_vehicles_per_charger": 1,
            },
            "tco": {},
            "annual_costs": {},
        },
        "diesel_results": {"vehicle_data": {}, "tco": {}, "annual_costs": {}},
        "comparison_metrics": {},
        "truck_life_years": 10,
        "bev_vehicle_data": {},
        "diesel_vehicle_data": {},
        "bev_fees": {},
        "diesel_fees": {},
        "charging_options": {},
        "infrastructure_options": {},
        "financial_params_with_ui": [],
        "battery_params_with_ui": [],
        "emission_factors": {},
        "incentives": [],
        "selected_charging": 0,
        "selected_infrastructure": 0,
        "annual_kms": 10000,
        "discount_rate": 0.07,
        "fleet_size": 1,
        "charging_mix": None,
        "apply_incentives": False,
    }
    # Stub heavy plotting helpers to no-op
    import tco_app.plotters as _plotters_pkg

    for _name in dir(_plotters_pkg):
        if _name.startswith("create_"):
            setattr(_plotters_pkg, _name, lambda *a, **kw: None)
    # Stub UI metric helpers
    import tco_app.ui.components as _ui_comp

    _ui_comp.display_summary_metrics = lambda *a, **k: None
    _ui_comp.display_comparison_metrics = lambda *a, **k: None
    # Stub heavy calculations used in sensitivity page
    _sens.perform_sensitivity_analysis = lambda *a, **k: []
    _fin.calculate_payload_penalty_costs = lambda *a, **k: {
        "has_penalty": False,
        "payload_difference": 0,
        "payload_difference_percentage": 0,
    }
    # Mock the re-exported streamlit from tco_app.src
    import tco_app.src.imports as _imports
    import tco_app.src as _src
    
    # Replace the imported streamlit with our stub
    _imports.st = sys.modules["streamlit"]
    _src.st = sys.modules["streamlit"]
    
    import importlib
    module = importlib.import_module(module_path)
    assert hasattr(module, "render")
    module.render()


def test_home_page_smoke():
    _smoke_render("tco_app.ui.pages.home")


def test_cost_breakdown_page_smoke():
    _smoke_render("tco_app.ui.pages.cost_breakdown")


def test_sensitivity_page_smoke():
    _smoke_render("tco_app.ui.pages.sensitivity")
