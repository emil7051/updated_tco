"""Unit tests for model runner service."""

from tco_app.services.model_runner import run_model


class TestModelRunner:
    """Test the model runner service."""

    def test_run_model_basic_execution(
        self,
        articulated_bev_vehicle,
        articulated_diesel_vehicle,
        standard_fees,
        standard_charging_options,
        standard_infrastructure_options,
        standard_financial_params,
        standard_emission_factors,
        standard_incentives,
    ):
        """Test that run_model executes without errors and returns expected structure."""
        # Mock battery params that aren't in our standard fixtures
        battery_params = [
            {"battery_description": "replacement_per_kwh_price", "default_value": 100},
            {
                "battery_description": "degradation_annual_percent",
                "default_value": 0.05,
            },
            {"battery_description": "minimum_capacity_percent", "default_value": 0.7},
        ]

        result = run_model(
            bev_vehicle_data=articulated_bev_vehicle,
            diesel_vehicle_data=articulated_diesel_vehicle,
            bev_fees=standard_fees[
                standard_fees["vehicle_id"] == articulated_bev_vehicle["vehicle_id"]
            ],
            diesel_fees=standard_fees[
                standard_fees["vehicle_id"] == articulated_diesel_vehicle["vehicle_id"]
            ],
            charging_options=standard_charging_options,
            infrastructure_options=standard_infrastructure_options,
            financial_params_with_ui=standard_financial_params,
            battery_params_with_ui=battery_params,
            emission_factors=standard_emission_factors,
            incentives=standard_incentives,
            selected_charging="Depot",
            selected_infrastructure="INFRA1",
            annual_kms=100_000,
            truck_life_years=10,
            discount_rate=0.07,
            fleet_size=1,
            charging_mix=None,
            apply_incentives=False,
            scenario_meta={
                "name": "Test Scenario",
                "description": "Test scenario for unit testing",
            },
        )

        # Check that all expected keys are present
        assert "bev_results" in result
        assert "diesel_results" in result
        assert "comparison_metrics" in result

        # Check BEV results structure
        bev = result["bev_results"]
        required_bev_keys = [
            "vehicle_data",
            "fees",
            "energy_cost_per_km",
            "annual_costs",
            "emissions",
            "acquisition_cost",
            "residual_value",
            "battery_replacement",
            "npv_annual_cost",
            "tco",
            "externalities",
            "social_tco",
            "charging_requirements",
            "infrastructure_costs",
        ]
        for key in required_bev_keys:
            assert key in bev, f"Missing key '{key}' in bev_results"

        # Check diesel results structure
        diesel = result["diesel_results"]
        required_diesel_keys = [
            "vehicle_data",
            "fees",
            "energy_cost_per_km",
            "annual_costs",
            "emissions",
            "acquisition_cost",
            "residual_value",
            "battery_replacement",
            "npv_annual_cost",
            "tco",
            "externalities",
            "social_tco",
        ]
        for key in required_diesel_keys:
            assert key in diesel, f"Missing key '{key}' in diesel_results"

        # Check that BEV has battery replacement but diesel doesn't
        assert bev["battery_replacement"] >= 0
        assert diesel["battery_replacement"] == 0

    def test_run_model_with_charging_mix(
        self,
        articulated_bev_vehicle,
        articulated_diesel_vehicle,
        standard_fees,
        standard_charging_options,
        standard_infrastructure_options,
        standard_financial_params,
        standard_emission_factors,
        standard_incentives,
    ):
        """Test run_model with charging mix specified."""
        battery_params = [
            {"battery_description": "replacement_per_kwh_price", "default_value": 100},
            {
                "battery_description": "degradation_annual_percent",
                "default_value": 0.05,
            },
            {"battery_description": "minimum_capacity_percent", "default_value": 0.7},
        ]

        charging_mix = {"Depot": 0.7, "Fast": 0.3}

        result = run_model(
            bev_vehicle_data=articulated_bev_vehicle,
            diesel_vehicle_data=articulated_diesel_vehicle,
            bev_fees=standard_fees[
                standard_fees["vehicle_id"] == articulated_bev_vehicle["vehicle_id"]
            ],
            diesel_fees=standard_fees[
                standard_fees["vehicle_id"] == articulated_diesel_vehicle["vehicle_id"]
            ],
            charging_options=standard_charging_options,
            infrastructure_options=standard_infrastructure_options,
            financial_params_with_ui=standard_financial_params,
            battery_params_with_ui=battery_params,
            emission_factors=standard_emission_factors,
            incentives=standard_incentives,
            selected_charging="Depot",
            selected_infrastructure="INFRA1",
            annual_kms=100_000,
            truck_life_years=10,
            discount_rate=0.07,
            fleet_size=1,
            charging_mix=charging_mix,
            apply_incentives=False,
            scenario_meta={"name": "Test Scenario"},
        )

        # Should include charging mix information
        bev = result["bev_results"]
        assert "charging_mix" in bev
        assert "weighted_electricity_price" in bev
        assert bev["charging_mix"] == charging_mix

    def test_run_model_with_incentives(
        self,
        articulated_bev_vehicle,
        articulated_diesel_vehicle,
        standard_fees,
        standard_charging_options,
        standard_infrastructure_options,
        standard_financial_params,
        standard_emission_factors,
        standard_incentives,
    ):
        """Test run_model with incentives applied."""
        battery_params = [
            {"battery_description": "replacement_per_kwh_price", "default_value": 100},
            {
                "battery_description": "degradation_annual_percent",
                "default_value": 0.05,
            },
            {"battery_description": "minimum_capacity_percent", "default_value": 0.7},
        ]

        # Run without incentives
        result_no_incentives = run_model(
            bev_vehicle_data=articulated_bev_vehicle,
            diesel_vehicle_data=articulated_diesel_vehicle,
            bev_fees=standard_fees[
                standard_fees["vehicle_id"] == articulated_bev_vehicle["vehicle_id"]
            ],
            diesel_fees=standard_fees[
                standard_fees["vehicle_id"] == articulated_diesel_vehicle["vehicle_id"]
            ],
            charging_options=standard_charging_options,
            infrastructure_options=standard_infrastructure_options,
            financial_params_with_ui=standard_financial_params,
            battery_params_with_ui=battery_params,
            emission_factors=standard_emission_factors,
            incentives=standard_incentives,
            selected_charging="Depot",
            selected_infrastructure="INFRA1",
            annual_kms=100_000,
            truck_life_years=10,
            discount_rate=0.07,
            fleet_size=1,
            charging_mix=None,
            apply_incentives=False,
            scenario_meta={"name": "Test Scenario"},
        )

        # Run with incentives
        result_with_incentives = run_model(
            bev_vehicle_data=articulated_bev_vehicle,
            diesel_vehicle_data=articulated_diesel_vehicle,
            bev_fees=standard_fees[
                standard_fees["vehicle_id"] == articulated_bev_vehicle["vehicle_id"]
            ],
            diesel_fees=standard_fees[
                standard_fees["vehicle_id"] == articulated_diesel_vehicle["vehicle_id"]
            ],
            charging_options=standard_charging_options,
            infrastructure_options=standard_infrastructure_options,
            financial_params_with_ui=standard_financial_params,
            battery_params_with_ui=battery_params,
            emission_factors=standard_emission_factors,
            incentives=standard_incentives,
            selected_charging="Depot",
            selected_infrastructure="INFRA1",
            annual_kms=100_000,
            truck_life_years=10,
            discount_rate=0.07,
            fleet_size=1,
            charging_mix=None,
            apply_incentives=True,
            scenario_meta={"name": "Test Scenario"},
        )

        # With incentives, BEV acquisition cost should be lower
        assert (
            result_with_incentives["bev_results"]["acquisition_cost"]
            <= result_no_incentives["bev_results"]["acquisition_cost"]
        )
