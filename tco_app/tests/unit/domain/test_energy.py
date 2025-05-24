"""Unit tests for energy domain module."""

import math
import pytest
from unittest.mock import Mock, patch
import pandas as pd
from tco_app.domain.energy import (
    calculate_energy_costs,
    calculate_emissions,
    calculate_charging_requirements,
)
from tco_app.src.constants import DataColumns, Drivetrain, ParameterKeys
from tco_app.tests.fixtures.vehicles import (
    bev_vehicle_data,
    diesel_vehicle_data,
    standard_charging_options,
    articulated_bev_vehicle,
    articulated_diesel_vehicle,
    standard_fees,
    standard_financial_params,
    standard_emission_factors,
    standard_infrastructure_options,
)


class TestEnergyCalculations:
    """Test energy cost calculations."""

    def test_calculate_energy_costs_bev(
        self,
        articulated_bev_vehicle,
        standard_fees,
        standard_charging_options,
        standard_financial_params,
    ):
        """Test BEV energy cost calculation."""
        cost = calculate_energy_costs(
            articulated_bev_vehicle,
            standard_fees,
            standard_charging_options,
            standard_financial_params,
            selected_charging="Depot",
        )
        assert math.isclose(cost, 1.30 * 0.25)  # 130 kWh/100km => 1.30 * price

    def test_calculate_energy_costs_diesel(
        self,
        articulated_diesel_vehicle,
        standard_fees,
        standard_charging_options,
        standard_financial_params,
    ):
        """Test diesel energy cost calculation."""
        cost = calculate_energy_costs(
            articulated_diesel_vehicle,
            standard_fees,
            standard_charging_options,
            standard_financial_params,
            selected_charging="Depot",
        )
        assert math.isclose(cost, 0.28 * 2.0)  # 28 L/100km => 0.28 * price

    def test_energy_costs_with_missing_charging_option(
        self,
        articulated_bev_vehicle,
        standard_fees,
        standard_financial_params,
    ):
        """Test BEV energy cost with missing charging option."""
        empty_charging = pd.DataFrame(
            columns=[DataColumns.CHARGING_ID, DataColumns.PER_KWH_PRICE]
        )

        with pytest.raises(Exception):  # Should raise when charging option not found
            calculate_energy_costs(
                articulated_bev_vehicle,
                standard_fees,
                empty_charging,
                standard_financial_params,
                selected_charging="NonExistent",
            )

    def test_energy_costs_phev_vehicle(self):
        """Test PHEV energy cost calculation (hybrid mode)."""
        phev_vehicle = pd.Series(
            {
                DataColumns.VEHICLE_ID: "phev_truck",
                DataColumns.VEHICLE_DRIVETRAIN: Drivetrain.PHEV,
                DataColumns.LITRES_PER100KM: 20.0,  # L/100km
                DataColumns.KWH_PER100KM: 15.0,  # kWh/100km for electric mode
                DataColumns.BATTERY_CAPACITY_KWH: 30.0,
                DataColumns.RANGE_KM: 50.0,  # 50km electric range
            }
        )

        fees = pd.Series(
            {
                DataColumns.REGISTRATION_ANNUAL_PRICE: 1000,
            }
        )

        charging = pd.DataFrame(
            {
                DataColumns.CHARGING_ID: ["Depot"],
                DataColumns.PER_KWH_PRICE: [0.25],
            }
        )

        financial = pd.DataFrame(
            {
                DataColumns.FINANCE_DESCRIPTION: [ParameterKeys.DIESEL_PRICE],
                DataColumns.FINANCE_DEFAULT_VALUE: [2.0],
            }
        )

        # PHEV should use combination of electric and diesel
        cost = calculate_energy_costs(
            phev_vehicle,
            fees,
            charging,
            financial,
            selected_charging="Depot",
        )

        # Cost should be between pure electric and pure diesel
        assert cost > 0
        assert cost < (0.20 * 2.0)  # Less than pure diesel

    def test_energy_costs_with_battery_inefficiency(self):
        """Test energy cost calculation with battery efficiency."""
        bev_with_efficiency = pd.Series(
            {
                DataColumns.VEHICLE_ID: "bev_eff",
                DataColumns.VEHICLE_DRIVETRAIN: Drivetrain.BEV,
                DataColumns.BATTERY_CAPACITY_KWH: 540.0,
                DataColumns.RANGE_KM: 300.0,
                DataColumns.BATTERY_EFFICIENCY: 0.85,  # 85% efficiency
            }
        )

        fees = pd.Series({DataColumns.REGISTRATION_ANNUAL_PRICE: 0})

        charging = pd.DataFrame(
            {
                DataColumns.CHARGING_ID: ["Depot"],
                DataColumns.PER_KWH_PRICE: [0.25],
            }
        )

        financial = pd.DataFrame(
            {
                DataColumns.FINANCE_DESCRIPTION: [ParameterKeys.DIESEL_PRICE],
                DataColumns.FINANCE_DEFAULT_VALUE: [2.0],
            }
        )

        cost = calculate_energy_costs(
            bev_with_efficiency,
            fees,
            charging,
            financial,
            selected_charging="Depot",
        )

        # Cost should account for efficiency loss
        # 540kWh / 300km = 180 kWh/100km, with 85% efficiency = 211.76 kWh/100km from grid
        expected = (180 / 0.85 / 100) * 0.25
        assert math.isclose(cost, expected, rel_tol=0.01)


class TestEmissionsCalculations:
    """Test emissions calculations."""

    def test_calculate_emissions_comparison(
        self,
        articulated_bev_vehicle,
        articulated_diesel_vehicle,
        standard_emission_factors,
    ):
        """Test emissions calculation comparison between BEV and diesel."""
        bev = calculate_emissions(
            articulated_bev_vehicle, standard_emission_factors, 100_000, 10
        )
        diesel = calculate_emissions(
            articulated_diesel_vehicle, standard_emission_factors, 100_000, 10
        )

        assert bev["co2_per_km"] < diesel["co2_per_km"]
        assert bev["lifetime_emissions"] < diesel["lifetime_emissions"]

    def test_emissions_with_zero_grid_factor(self):
        """Test BEV emissions with zero grid emission factor (100% renewable)."""
        bev_vehicle = pd.Series(
            {
                DataColumns.VEHICLE_ID: "bev_clean",
                DataColumns.VEHICLE_DRIVETRAIN: Drivetrain.BEV,
                DataColumns.BATTERY_CAPACITY_KWH: 540.0,
                DataColumns.RANGE_KM: 300.0,
            }
        )

        zero_emission_factors = pd.Series(
            {
                DataColumns.GRID_EMISSION_FACTOR: 0.0,  # 100% renewable
                DataColumns.DIESEL_EMISSION_FACTOR: 2.7,
            }
        )

        emissions = calculate_emissions(bev_vehicle, zero_emission_factors, 100_000, 10)

        # With zero grid factor, BEV should have zero emissions
        assert emissions["co2_per_km"] == 0.0
        assert emissions["lifetime_emissions"] == 0.0
        assert emissions["annual_emissions"] == 0.0

    def test_emissions_with_high_grid_factor(self):
        """Test BEV emissions with very high grid emission factor."""
        bev_vehicle = pd.Series(
            {
                DataColumns.VEHICLE_ID: "bev_dirty",
                DataColumns.VEHICLE_DRIVETRAIN: Drivetrain.BEV,
                DataColumns.BATTERY_CAPACITY_KWH: 540.0,
                DataColumns.RANGE_KM: 300.0,
            }
        )

        high_emission_factors = pd.Series(
            {
                DataColumns.GRID_EMISSION_FACTOR: 1.0,  # Very dirty grid (1kg CO2/kWh)
                DataColumns.DIESEL_EMISSION_FACTOR: 2.7,
            }
        )

        emissions = calculate_emissions(bev_vehicle, high_emission_factors, 100_000, 10)

        # Even with dirty grid, calculations should work
        assert emissions["co2_per_km"] > 0
        assert emissions["lifetime_emissions"] > 0
        # 180 kWh/100km * 1 kg/kWh = 1.8 kg/km
        assert math.isclose(emissions["co2_per_km"], 1.8, rel_tol=0.1)

    def test_emissions_phev_vehicle(self):
        """Test PHEV emissions calculation."""
        phev_vehicle = pd.Series(
            {
                DataColumns.VEHICLE_ID: "phev",
                DataColumns.VEHICLE_DRIVETRAIN: Drivetrain.PHEV,
                DataColumns.LITRES_PER100KM: 20.0,
                DataColumns.BATTERY_CAPACITY_KWH: 30.0,
                DataColumns.RANGE_KM: 50.0,  # 50km electric range
            }
        )

        emission_factors = pd.Series(
            {
                DataColumns.GRID_EMISSION_FACTOR: 0.5,
                DataColumns.DIESEL_EMISSION_FACTOR: 2.7,
            }
        )

        emissions = calculate_emissions(phev_vehicle, emission_factors, 100_000, 10)

        # PHEV emissions should be between BEV and diesel
        assert emissions["co2_per_km"] > 0
        assert emissions["co2_per_km"] < (0.20 * 2.7)  # Less than pure diesel

    def test_emissions_with_negative_values(self):
        """Test emissions calculation with invalid negative values."""
        vehicle = pd.Series(
            {
                DataColumns.VEHICLE_ID: "invalid",
                DataColumns.VEHICLE_DRIVETRAIN: Drivetrain.BEV,
                DataColumns.BATTERY_CAPACITY_KWH: -100.0,  # Invalid negative
                DataColumns.RANGE_KM: 300.0,
            }
        )

        emission_factors = pd.Series(
            {
                DataColumns.GRID_EMISSION_FACTOR: 0.5,
                DataColumns.DIESEL_EMISSION_FACTOR: 2.7,
            }
        )

        # Should handle gracefully or raise appropriate error
        with pytest.raises(Exception):
            calculate_emissions(vehicle, emission_factors, 100_000, 10)


class TestChargingRequirements:
    """Test charging requirement calculations."""

    def test_charging_requirements(
        self, articulated_bev_vehicle, standard_infrastructure_options
    ):
        """Test charging requirements calculation."""
        infra = standard_infrastructure_options.iloc[0]
        req = calculate_charging_requirements(articulated_bev_vehicle, 100_000, infra)

        assert req["daily_kwh_required"] > 0
        assert req["charger_power"] == 80.0
        assert req["max_vehicles_per_charger"] > 0

    def test_charging_requirements_high_utilization(self):
        """Test charging requirements with high daily utilization."""
        high_util_vehicle = pd.Series(
            {
                DataColumns.VEHICLE_ID: "high_util",
                DataColumns.VEHICLE_DRIVETRAIN: Drivetrain.BEV,
                DataColumns.BATTERY_CAPACITY_KWH: 540.0,
                DataColumns.RANGE_KM: 300.0,
                DataColumns.BATTERY_EFFICIENCY: 0.9,
            }
        )

        infra = pd.Series(
            {
                DataColumns.INFRASTRUCTURE_ID: "fast_charge",
                DataColumns.CHARGER_POWER: 350.0,  # Fast charger
                DataColumns.CHARGER_EFFICIENCY: 0.95,
                DataColumns.UTILIZATION_HOURS: 22,  # High utilization
            }
        )

        # Very high annual km (500km/day average)
        req = calculate_charging_requirements(high_util_vehicle, 182_500, infra)

        assert req["daily_kwh_required"] > 900  # ~180kWh/100km * 500km
        assert req["charging_hours_per_day"] > 2.5
        assert req["max_vehicles_per_charger"] < 10  # Limited by utilization

    def test_charging_requirements_slow_charger(self):
        """Test charging requirements with slow charger."""
        vehicle = pd.Series(
            {
                DataColumns.VEHICLE_ID: "bev",
                DataColumns.VEHICLE_DRIVETRAIN: Drivetrain.BEV,
                DataColumns.BATTERY_CAPACITY_KWH: 200.0,
                DataColumns.RANGE_KM: 200.0,
            }
        )

        slow_infra = pd.Series(
            {
                DataColumns.INFRASTRUCTURE_ID: "slow",
                DataColumns.CHARGER_POWER: 11.0,  # Slow AC charger
                DataColumns.CHARGER_EFFICIENCY: 0.90,
                DataColumns.UTILIZATION_HOURS: 12,
            }
        )

        req = calculate_charging_requirements(vehicle, 50_000, slow_infra)

        # With slow charger, fewer vehicles can be served
        assert req["max_vehicles_per_charger"] <= 2
        assert req["charging_hours_per_day"] > 10

    def test_charging_requirements_zero_utilization(self):
        """Test charging requirements with zero utilization hours."""
        vehicle = pd.Series(
            {
                DataColumns.VEHICLE_ID: "bev",
                DataColumns.VEHICLE_DRIVETRAIN: Drivetrain.BEV,
                DataColumns.BATTERY_CAPACITY_KWH: 200.0,
                DataColumns.RANGE_KM: 200.0,
            }
        )

        zero_util_infra = pd.Series(
            {
                DataColumns.INFRASTRUCTURE_ID: "zero",
                DataColumns.CHARGER_POWER: 50.0,
                DataColumns.CHARGER_EFFICIENCY: 0.95,
                DataColumns.UTILIZATION_HOURS: 0,  # No utilization
            }
        )

        req = calculate_charging_requirements(vehicle, 50_000, zero_util_infra)

        # With zero utilization, should return 0 or handle gracefully
        assert req["max_vehicles_per_charger"] == 0

    def test_charging_requirements_diesel_vehicle(self):
        """Test charging requirements for diesel vehicle (should return zeros)."""
        diesel_vehicle = pd.Series(
            {
                DataColumns.VEHICLE_ID: "diesel",
                DataColumns.VEHICLE_DRIVETRAIN: Drivetrain.DIESEL,
                DataColumns.LITRES_PER100KM: 30.0,
            }
        )

        infra = pd.Series(
            {
                DataColumns.INFRASTRUCTURE_ID: "depot",
                DataColumns.CHARGER_POWER: 80.0,
                DataColumns.CHARGER_EFFICIENCY: 0.95,
                DataColumns.UTILIZATION_HOURS: 8,
            }
        )

        req = calculate_charging_requirements(diesel_vehicle, 100_000, infra)

        # Diesel vehicles don't need charging
        assert req["daily_kwh_required"] == 0
        assert req["charging_hours_per_day"] == 0
        assert req["max_vehicles_per_charger"] == float("inf")


class TestEnergyConsumption:
    """Test energy consumption calculations."""

    def test_calculate_energy_consumption_bev(self):
        """Test BEV energy consumption calculation."""
        bev_vehicle = pd.Series(
            {
                DataColumns.VEHICLE_ID: "bev",
                DataColumns.VEHICLE_DRIVETRAIN: Drivetrain.BEV,
                DataColumns.BATTERY_CAPACITY_KWH: 540.0,
                DataColumns.RANGE_KM: 300.0,
            }
        )

        consumption = calculate_energy_consumption(bev_vehicle)

        # 540 kWh / 300 km = 180 kWh/100km
        assert math.isclose(consumption, 180.0, rel_tol=0.01)

    def test_calculate_energy_consumption_diesel(self):
        """Test diesel energy consumption calculation."""
        diesel_vehicle = pd.Series(
            {
                DataColumns.VEHICLE_ID: "diesel",
                DataColumns.VEHICLE_DRIVETRAIN: Drivetrain.DIESEL,
                DataColumns.LITRES_PER100KM: 35.0,  # L/100km
            }
        )

        consumption = calculate_energy_consumption(diesel_vehicle)

        # Should return diesel consumption directly
        assert consumption == 35.0

    def test_calculate_energy_consumption_phev(self):
        """Test PHEV energy consumption calculation."""
        phev_vehicle = pd.Series(
            {
                DataColumns.VEHICLE_ID: "phev",
                DataColumns.VEHICLE_DRIVETRAIN: Drivetrain.PHEV,
                DataColumns.LITRES_PER100KM: 25.0,
                DataColumns.BATTERY_CAPACITY_KWH: 30.0,
                DataColumns.RANGE_KM: 50.0,  # Electric range
            }
        )

        consumption = calculate_energy_consumption(phev_vehicle)

        # PHEV should return combined consumption
        assert consumption > 0

    def test_energy_consumption_edge_cases(self):
        """Test energy consumption with edge cases."""
        # Zero range
        zero_range_vehicle = pd.Series(
            {
                DataColumns.VEHICLE_ID: "zero",
                DataColumns.VEHICLE_DRIVETRAIN: Drivetrain.BEV,
                DataColumns.BATTERY_CAPACITY_KWH: 100.0,
                DataColumns.RANGE_KM: 0.0,
            }
        )

        with pytest.raises(Exception):  # Division by zero
            calculate_energy_consumption(zero_range_vehicle)

        # Missing battery capacity
        missing_battery = pd.Series(
            {
                DataColumns.VEHICLE_ID: "missing",
                DataColumns.VEHICLE_DRIVETRAIN: Drivetrain.BEV,
                DataColumns.RANGE_KM: 300.0,
            }
        )

        with pytest.raises(Exception):  # Missing required field
            calculate_energy_consumption(missing_battery)
