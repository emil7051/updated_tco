"""Tests for the scenario_service module."""

from unittest.mock import MagicMock, patch

from tco_app.services import scenario_service
from tco_app.src import pd


class _StubExpander:
    def __enter__(self):
        return None

    def __exit__(self, *exc):
        return False


class TestApplyScenarioParameters:
    """Tests for apply_scenario_parameters function."""

    def _build_tables(self):
        financial_params = pd.DataFrame(
            [
                {"finance_description": "diesel_price", "default_value": 2.0},
                {"finance_description": "discount_rate_percent", "default_value": 0.07},
            ]
        )

        battery_params = pd.DataFrame(
            [
                {
                    "battery_description": "replacement_per_kwh_price",
                    "default_value": 100.0,
                }
            ]
        )

        vehicle_models = pd.DataFrame(
            [
                {
                    "vehicle_id": "V1",
                    "vehicle_type": "Truck",
                    "vehicle_drivetrain": "BEV",
                    "msrp_price": 300000,
                },
                {
                    "vehicle_id": "V2",
                    "vehicle_type": "Truck",
                    "vehicle_drivetrain": "Diesel",
                    "msrp_price": 200000,
                },
            ]
        )

        scenario_params = pd.DataFrame(
            [
                {
                    "scenario_id": "S1",
                    "parameter_table": "financial_params",
                    "parameter_name": "diesel_price",
                    "parameter_value": 2.5,
                    "vehicle_type": "All",
                    "vehicle_drivetrain": "All",
                },
                {
                    "scenario_id": "S1",
                    "parameter_table": "vehicle_models",
                    "parameter_name": "msrp_price_modifier",
                    "parameter_value": 0.8,
                    "vehicle_type": "Truck",
                    "vehicle_drivetrain": "BEV",
                },
                {
                    "scenario_id": "S2",
                    "parameter_table": "battery_params",
                    "parameter_name": "replacement_per_kwh_price",
                    "parameter_value": 80.0,
                    "vehicle_type": "All",
                    "vehicle_drivetrain": "All",
                },
            ]
        )

        return {
            "financial_params": financial_params,
            "battery_params": battery_params,
            "vehicle_models": vehicle_models,
            "scenario_params": scenario_params,
        }

    def test_apply_known_scenario(self):
        data_tables = self._build_tables()
        modified = scenario_service.apply_scenario_parameters(
            "S1", data_tables, "Truck", "BEV"
        )

        # financial param changed
        diesel_price = modified["financial_params"][
            modified["financial_params"]["finance_description"] == "diesel_price"
        ]["default_value"].iloc[0]
        assert diesel_price == 2.5

        # vehicle price modified for BEV truck
        bev_mask = (modified["vehicle_models"]["vehicle_drivetrain"] == "BEV") & (
            modified["vehicle_models"]["vehicle_type"] == "Truck"
        )
        bev_price = modified["vehicle_models"][bev_mask]["msrp_price"].iloc[0]
        assert bev_price == 240000  # 300000 * 0.8

        # ensure originals untouched
        original_price = data_tables["vehicle_models"][bev_mask]["msrp_price"].iloc[0]
        assert original_price == 300000

    def test_apply_unknown_scenario(self):
        data_tables = self._build_tables()
        modified = scenario_service.apply_scenario_parameters(
            "UNKNOWN", data_tables, "Truck", "BEV"
        )

        pd.testing.assert_frame_equal(
            modified["financial_params"], data_tables["financial_params"]
        )  # noqa: E501
        pd.testing.assert_frame_equal(
            modified["vehicle_models"], data_tables["vehicle_models"]
        )  # noqa: E501
        pd.testing.assert_frame_equal(
            modified["battery_params"], data_tables["battery_params"]
        )  # noqa: E501


class TestDisplayScenarioParameters:
    """Tests for display_scenario_parameters function."""

    def _stub_streamlit(self):
        stub = MagicMock()
        stub.expander.return_value = _StubExpander()
        return stub

    def test_display_with_params(self):
        scenario_params = pd.DataFrame(
            [
                {
                    "scenario_id": "S1",
                    "parameter_table": "financial_params",
                    "parameter_name": "diesel_price",
                    "parameter_value": 2.5,
                }
            ]
        )
        stub = self._stub_streamlit()
        with patch("tco_app.services.scenario_service.st", stub):
            scenario_service.display_scenario_parameters("S1", scenario_params, "Name")
        stub.expander.assert_called_once()
        stub.markdown.assert_called_once()
        stub.caption.assert_not_called()

    def test_display_base_scenario(self):
        scenario_params = pd.DataFrame(
            [
                {
                    "scenario_id": "S1",
                    "parameter_table": "financial_params",
                    "parameter_name": "diesel_price",
                    "parameter_value": 2.5,
                }
            ]
        )
        stub = self._stub_streamlit()
        with patch("tco_app.services.scenario_service.st", stub):
            scenario_service.display_scenario_parameters(
                "S000", scenario_params, "Base"
            )
        stub.caption.assert_called_once()
        stub.markdown.assert_not_called()
