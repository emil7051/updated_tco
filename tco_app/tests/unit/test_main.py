import importlib
from types import SimpleNamespace
from unittest.mock import MagicMock, patch


def test_main_import_triggers_render():
    page_key = "Home"
    fake_module = SimpleNamespace(render=MagicMock())
    real_import_module = importlib.import_module

    with patch("tco_app.src.st.set_page_config"), patch(
        "tco_app.src.st.sidebar.title"
    ), patch("tco_app.src.st.sidebar.radio", return_value=page_key), patch(
        "importlib.import_module"
    ) as import_module_mock, patch(
        "tco_app.main.st.sidebar.radio", return_value=page_key
    ):

        def side_effect(name, package=None):
            if name == "tco_app.ui.pages.home":
                return fake_module
            return real_import_module(name, package)

        import_module_mock.side_effect = side_effect

        importlib.import_module("tco_app.main")

    fake_module.render.assert_called_once()
