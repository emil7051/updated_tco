"""Tests for the ScenarioApplicationService."""

import pytest
from tco_app.src import pd
from dataclasses import asdict

from tco_app.services.scenario_application_service import (
    ScenarioApplicationService,
    ScenarioModification,
)
from tco_app.src.constants import DataColumns
from tco_app.src.exceptions import ScenarioError


class TestScenarioApplicationService:
    """Test cases for ScenarioApplicationService."""

    @pytest.fixture
    def service(self):
        """Create a ScenarioApplicationService instance."""
        return ScenarioApplicationService()

    @pytest.fixture
    def sample_data_tables(self):
        """Create sample data tables for testing."""
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
                },
                {
                    "battery_description": "degradation_annual_percent",
                    "default_value": 0.05,
                },
            ]
        )

        vehicle_models = pd.DataFrame(
            [
                {
                    "vehicle_id": "BEV1",
                    "vehicle_type": "Articulated",
                    "vehicle_drivetrain": "BEV",
                    "msrp_price": 300000,
                    "kwh_per100km": 100,
                    "range_km": 400,
                },
                {
                    "vehicle_id": "DIESEL1",
                    "vehicle_type": "Articulated",
                    "vehicle_drivetrain": "Diesel",
                    "msrp_price": 200000,
                    "kwh_per100km": 0,
                    "range_km": 800,
                },
            ]
        )

        incentives = pd.DataFrame(
            [
                {
                    "incentive_type": "purchase_rebate_aud",
                    "vehicle_type": "All",
                    "drivetrain": "BEV",
                    "incentive_flag": 1,
                    "incentive_rate": 50000,
                }
            ]
        )

        scenario_params = pd.DataFrame(
            [
                {
                    "scenario_id": "S001",
                    "parameter_table": "financial_params",
                    "parameter_name": "diesel_price",
                    "parameter_value": 2.5,
                    "vehicle_type": "All",
                    "vehicle_drivetrain": "All",
                },
                {
                    "scenario_id": "S001",
                    "parameter_table": "vehicle_models",
                    "parameter_name": "msrp_price_modifier",
                    "parameter_value": 0.9,
                    "vehicle_type": "Articulated",
                    "vehicle_drivetrain": "BEV",
                },
            ]
        )

        return {
            "financial_params": financial_params,
            "battery_params": battery_params,
            "vehicle_models": vehicle_models,
            "incentives": incentives,
            "scenario_params": scenario_params,
        }

    def test_parse_scenario_params(self, service):
        """Test parsing scenario parameters into modification objects."""
        scenario_df = pd.DataFrame(
            [
                {
                    "parameter_table": "financial_params",
                    "parameter_name": "diesel_price",
                    "parameter_value": 2.5,
                    "vehicle_type": "All",
                    "vehicle_drivetrain": "All",
                },
                {
                    "parameter_table": "battery_params",
                    "parameter_name": "replacement_per_kwh_price",
                    "parameter_value": 120.0,
                    "vehicle_type": "Articulated",
                    "vehicle_drivetrain": "BEV",
                },
            ]
        )

        modifications = service.parse_scenario_params(scenario_df)

        assert len(modifications) == 2
        assert all(isinstance(mod, ScenarioModification) for mod in modifications)

        mod1 = modifications[0]
        assert mod1.table_name == "financial_params"
        assert mod1.parameter_name == "diesel_price"
        assert mod1.parameter_value == 2.5
        assert mod1.vehicle_type == "All"
        assert mod1.vehicle_drivetrain == "All"

    def test_apply_financial_param_modification(self, service, sample_data_tables):
        """Test applying financial parameter modifications."""
        modifications = [
            ScenarioModification(
                table_name="financial_params",
                parameter_name="diesel_price",
                parameter_value=3.0,
                vehicle_type="All",
                vehicle_drivetrain="All",
            )
        ]

        modified_tables = service.apply_modifications(sample_data_tables, modifications)

        # Check original table is unchanged
        original_price = sample_data_tables["financial_params"][
            sample_data_tables["financial_params"]["finance_description"]
            == "diesel_price"
        ]["default_value"].iloc[0]
        assert original_price == 2.0

        # Check modified table has new value
        modified_price = modified_tables["financial_params"][
            modified_tables["financial_params"]["finance_description"] == "diesel_price"
        ]["default_value"].iloc[0]
        assert modified_price == 3.0

    def test_apply_vehicle_modifier(self, service, sample_data_tables):
        """Test applying vehicle model modifications."""
        modifications = [
            ScenarioModification(
                table_name="vehicle_models",
                parameter_name="msrp_price_modifier",
                parameter_value=1.1,
                vehicle_type="Articulated",
                vehicle_drivetrain="BEV",
            )
        ]

        modified_tables = service.apply_modifications(sample_data_tables, modifications)

        # Check BEV price was modified
        bev_mask = (
            modified_tables["vehicle_models"]["vehicle_drivetrain"] == "BEV"
        ) & (modified_tables["vehicle_models"]["vehicle_type"] == "Articulated")
        bev_price = modified_tables["vehicle_models"][bev_mask]["msrp_price"].iloc[0]
        assert bev_price == 330000  # 300000 * 1.1

        # Check Diesel price was not modified
        diesel_mask = (
            modified_tables["vehicle_models"]["vehicle_drivetrain"] == "Diesel"
        )
        diesel_price = modified_tables["vehicle_models"][diesel_mask][
            "msrp_price"
        ].iloc[0]
        assert diesel_price == 200000  # Unchanged

    def test_apply_scenario_by_id(self, service, sample_data_tables):
        """Test applying scenario modifications by scenario ID."""
        modified_tables = service.apply_scenario_by_id(
            "S001", sample_data_tables, "Articulated", "BEV"
        )

        # Check diesel price was modified
        diesel_price = modified_tables["financial_params"][
            modified_tables["financial_params"]["finance_description"] == "diesel_price"
        ]["default_value"].iloc[0]
        assert diesel_price == 2.5

        # Check BEV price was modified
        bev_mask = (
            modified_tables["vehicle_models"]["vehicle_drivetrain"] == "BEV"
        ) & (modified_tables["vehicle_models"]["vehicle_type"] == "Articulated")
        bev_price = modified_tables["vehicle_models"][bev_mask]["msrp_price"].iloc[0]
        assert bev_price == 270000  # 300000 * 0.9

    def test_should_apply_modification_filtering(self, service):
        """Test modification filtering logic."""
        mod_all = ScenarioModification(
            table_name="test",
            parameter_name="test",
            parameter_value=1.0,
            vehicle_type="All",
            vehicle_drivetrain="All",
        )

        mod_specific = ScenarioModification(
            table_name="test",
            parameter_name="test",
            parameter_value=1.0,
            vehicle_type="Articulated",
            vehicle_drivetrain="BEV",
        )

        # All modifier should always apply
        assert service._should_apply_modification(mod_all, "Articulated", "BEV")
        assert service._should_apply_modification(mod_all, "Rigid", "Diesel")

        # Specific modifier should only apply to matching vehicles
        assert service._should_apply_modification(mod_specific, "Articulated", "BEV")
        assert not service._should_apply_modification(mod_specific, "Rigid", "BEV")
        assert not service._should_apply_modification(
            mod_specific, "Articulated", "Diesel"
        )

    def test_diesel_default_price_special_case(self, service, sample_data_tables):
        """Test special case handling for diesel_default_price."""
        modifications = [
            ScenarioModification(
                table_name="financial_params",
                parameter_name="diesel_default_price",
                parameter_value=2.8,
            )
        ]

        modified_tables = service.apply_modifications(sample_data_tables, modifications)

        # Should map to diesel_price parameter
        diesel_price = modified_tables["financial_params"][
            modified_tables["financial_params"]["finance_description"] == "diesel_price"
        ]["default_value"].iloc[0]
        assert diesel_price == 2.8

    def test_apply_incentive_modifier(self, service, sample_data_tables):
        """Test applying incentive modifications."""
        modifications = [
            ScenarioModification(
                table_name="incentives",
                parameter_name="purchase_rebate_aud.incentive_rate",
                parameter_value=60000,
                vehicle_type="All",
                vehicle_drivetrain="BEV",
            )
        ]

        modified_tables = service.apply_modifications(sample_data_tables, modifications)

        # Check incentive was modified
        rebate_mask = (
            modified_tables["incentives"]["incentive_type"] == "purchase_rebate_aud"
        )
        incentive_rate = modified_tables["incentives"][rebate_mask][
            "incentive_rate"
        ].iloc[0]
        assert incentive_rate == 60000

    def test_error_handling_missing_table(self, service):
        """Test error handling for missing tables."""
        modifications = [
            ScenarioModification(
                table_name="nonexistent_table",
                parameter_name="test_param",
                parameter_value=1.0,
            )
        ]

        with pytest.raises(ScenarioError) as exc_info:
            service.apply_modifications({}, modifications)

        assert "Table 'nonexistent_table' not found" in str(exc_info.value)

    def test_get_and_clear_applied_modifications(self, service, sample_data_tables):
        """Test tracking of applied modifications."""
        modifications = [
            ScenarioModification(
                table_name="financial_params",
                parameter_name="diesel_price",
                parameter_value=2.5,
            )
        ]

        # Initially no modifications
        assert len(service.get_applied_modifications()) == 0

        # Apply modifications
        service.apply_modifications(sample_data_tables, modifications)

        # Check modifications were tracked
        applied = service.get_applied_modifications()
        assert len(applied) == 1
        assert applied[0].parameter_name == "diesel_price"

        # Clear modifications
        service.clear_applied_modifications()
        assert len(service.get_applied_modifications()) == 0

    def test_scenario_modification_dataclass(self):
        """Test ScenarioModification dataclass functionality."""
        mod = ScenarioModification(
            table_name="test_table", parameter_name="test_param", parameter_value=123.45
        )

        # Test default values
        assert mod.vehicle_type == "All"
        assert mod.vehicle_drivetrain == "All"

        # Test conversion to dict
        mod_dict = asdict(mod)
        assert mod_dict["table_name"] == "test_table"
        assert mod_dict["parameter_value"] == 123.45
