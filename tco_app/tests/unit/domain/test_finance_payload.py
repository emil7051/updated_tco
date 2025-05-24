"""Unit tests for finance payload module."""

import pytest
import pandas as pd
from tco_app.domain.finance_payload import calculate_payload_penalty_costs


class TestPayloadPenalty:
    """Test payload penalty calculations."""

    def test_payload_penalty_identical_payload(
        self,
    ):
        """Test payload penalty calculation when vehicles have identical payload."""
        # craft minimal results dicts
        bev_results = {
            "vehicle_data": {
                "vehicle_id": 1,
                "vehicle_type": "Articulated",
                "vehicle_drivetrain": "BEV",
                "kwh_per100km": 130,
                "payload_t": 40,
                "msrp_price": 400_000,
            },
            "annual_costs": {"annual_operating_cost": 50_000},
            "tco": {"tco_per_tonne_km": 0.9, "npv_total_cost": 900_000},
            "annual_kms": 100_000,
            "truck_life_years": 10,
        }
        diesel_results = {
            "vehicle_data": {
                "vehicle_id": 2,
                "vehicle_type": "Articulated",
                "vehicle_drivetrain": "Diesel",
                "litres_per100km": 28,
                "payload_t": 40,
                "msrp_price": 320_000,
            },
            "annual_costs": {"annual_operating_cost": 60_000},
            "tco": {"tco_per_tonne_km": 1.1, "npv_total_cost": 1_000_000},
            "annual_kms": 100_000,
            "truck_life_years": 10,
        }

        # Create basic financial params DataFrame
        standard_financial_params = pd.DataFrame([
            {"finance_description": "diesel_price", "default_value": 2.0},
            {"finance_description": "discount_rate_percent", "default_value": 0.07},
            {"finance_description": "freight_value_per_tonne", "default_value": 120},
            {"finance_description": "driver_cost_hourly", "default_value": 35},
            {"finance_description": "avg_trip_distance", "default_value": 100},
            {"finance_description": "avg_loadunload_time", "default_value": 1},
        ])

        penalty = calculate_payload_penalty_costs(
            bev_results, diesel_results, standard_financial_params
        )

        assert penalty["has_penalty"] is False  # identical payload in fixture

    def test_payload_penalty_different_payload(self):
        """Test payload penalty calculation when vehicles have different payload."""
        bev_vehicle_lower_payload = {
            "vehicle_id": 1,
            "vehicle_type": "Articulated",
            "vehicle_drivetrain": "BEV",
            "kwh_per100km": 130,
            "payload_t": 40,  # Lower payload
            "msrp_price": 400_000,
        }

        diesel_vehicle_higher_payload = {
            "vehicle_id": 2,
            "vehicle_type": "Articulated",
            "vehicle_drivetrain": "Diesel",
            "litres_per100km": 28,
            "payload_t": 42,  # Higher payload
            "msrp_price": 320_000,
        }

        bev_results = {
            "vehicle_data": bev_vehicle_lower_payload,
            "annual_costs": {"annual_operating_cost": 50_000},
            "tco": {"tco_per_tonne_km": 0.9, "npv_total_cost": 900_000},
            "annual_kms": 100_000,
            "truck_life_years": 10,
        }
        diesel_results = {
            "vehicle_data": diesel_vehicle_higher_payload,
            "annual_costs": {"annual_operating_cost": 60_000},
            "tco": {"tco_per_tonne_km": 1.1, "npv_total_cost": 1_000_000},
            "annual_kms": 100_000,
            "truck_life_years": 10,
        }

        # Create basic financial params DataFrame with payload penalty parameters
        standard_financial_params = pd.DataFrame([
            {"finance_description": "diesel_price", "default_value": 2.0},
            {"finance_description": "discount_rate_percent", "default_value": 0.07},
            {"finance_description": "freight_value_per_tonne", "default_value": 120},
            {"finance_description": "driver_cost_hourly", "default_value": 35},
            {"finance_description": "avg_trip_distance", "default_value": 100},
            {"finance_description": "avg_loadunload_time", "default_value": 1},
        ])

        penalty = calculate_payload_penalty_costs(
            bev_results, diesel_results, standard_financial_params
        )

        assert penalty["has_penalty"] is True  # BEV has lower payload
