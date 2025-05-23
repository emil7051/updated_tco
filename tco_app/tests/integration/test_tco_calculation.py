"""Integration tests for TCO calculation"""

from tco_app.services.model_runner import run_model


class TestTCOCalculationIntegration:
    """Integration test for the complete TCO calculation process."""

    def test_complete_tco_calculation_integration(
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
        """Test the complete TCO calculation process integrating all modules."""
        # Battery parameters
        battery_params = pd.DataFrame(
            [
                {
                    "battery_description": "replacement_per_kwh_price",
                    "default_value": 100,
                },
                {
                    "battery_description": "degradation_annual_percent",
                    "default_value": 0.05,
                },
                {
                    "battery_description": "minimum_capacity_percent",
                    "default_value": 0.7,
                },
            ]
        )

        # Run the complete model
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
            apply_incentives=True,
            scenario_meta={
                "name": "Integration Test",
                "description": "Full pipeline test",
            },
        )

        # Validate the complete calculation pipeline
        bev_results = result["bev_results"]
        diesel_results = result["diesel_results"]
        comparison = result["comparison_metrics"]

        # Test logical relationships
        assert bev_results["energy_cost_per_km"] != diesel_results["energy_cost_per_km"]
        assert (
            bev_results["emissions"]["co2_per_km"]
            < diesel_results["emissions"]["co2_per_km"]
        )
        assert bev_results["battery_replacement"] > 0
        assert diesel_results["battery_replacement"] == 0

        # Test that social TCO includes externalities
        assert (
            bev_results["social_tco"]["social_tco_lifetime"]
            > bev_results["tco"]["npv_total_cost"]
        )
        assert (
            diesel_results["social_tco"]["social_tco_lifetime"]
            > diesel_results["tco"]["npv_total_cost"]
        )

        # Test comparison metrics exist
        assert "upfront_cost_difference" in comparison
        assert "annual_operating_savings" in comparison
        assert "emission_savings_lifetime" in comparison

        # Test infrastructure costs are included for BEV
        assert "infrastructure_costs" in bev_results
        assert bev_results["infrastructure_costs"]["npv_per_vehicle"] > 0

    def test_tco_comparison_makes_sense(
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
        """Test that TCO comparison results make logical sense."""
        battery_params = pd.DataFrame(
            [
                {
                    "battery_description": "replacement_per_kwh_price",
                    "default_value": 100,
                },
                {
                    "battery_description": "degradation_annual_percent",
                    "default_value": 0.05,
                },
                {
                    "battery_description": "minimum_capacity_percent",
                    "default_value": 0.7,
                },
            ]
        )

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
            scenario_meta={"name": "Comparison Test"},
        )

        bev = result["bev_results"]
        diesel = result["diesel_results"]

        # BEV should have higher acquisition cost in this scenario
        assert bev["acquisition_cost"] > diesel["acquisition_cost"]

        # BEV should have lower emissions
        assert (
            bev["emissions"]["lifetime_emissions"]
            < diesel["emissions"]["lifetime_emissions"]
        )

        # Both should have positive TCO values
        assert bev["tco"]["npv_total_cost"] > 0
        assert diesel["tco"]["npv_total_cost"] > 0

        # Both should have reasonable cost per km
        assert 0 < bev["tco"]["tco_per_km"] < 10  # Reasonable range
        assert 0 < diesel["tco"]["tco_per_km"] < 10  # Reasonable range
