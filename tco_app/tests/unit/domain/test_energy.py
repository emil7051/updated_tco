"""Unit tests for energy domain module."""
import math
import pytest
from tco_app.domain.energy import (
    calculate_energy_costs,
    calculate_emissions,
    calculate_charging_requirements
)
from tco_app.tests.fixtures.vehicles import *


class TestEnergyCalculations:
    """Test energy cost calculations."""
    
    def test_calculate_energy_costs_bev(
        self, articulated_bev_vehicle, standard_fees, standard_charging_options, standard_financial_params
    ):
        """Test BEV energy cost calculation."""
        cost = calculate_energy_costs(
            articulated_bev_vehicle,
            standard_fees,
            standard_charging_options,
            standard_financial_params,
            selected_charging='Depot',
        )
        assert math.isclose(cost, 1.30 * 0.25)  # 130 kWh/100km => 1.30 * price
    
    def test_calculate_energy_costs_diesel(
        self, articulated_diesel_vehicle, standard_fees, standard_charging_options, standard_financial_params
    ):
        """Test diesel energy cost calculation."""
        cost = calculate_energy_costs(
            articulated_diesel_vehicle,
            standard_fees,
            standard_charging_options,
            standard_financial_params,
            selected_charging='Depot',
        )
        assert math.isclose(cost, 0.28 * 2.0)  # 28 L/100km => 0.28 * price


class TestEmissionsCalculations:
    """Test emissions calculations."""
    
    def test_calculate_emissions_comparison(
        self, articulated_bev_vehicle, articulated_diesel_vehicle, standard_emission_factors
    ):
        """Test emissions calculation comparison between BEV and diesel."""
        bev = calculate_emissions(articulated_bev_vehicle, standard_emission_factors, 100_000, 10)
        diesel = calculate_emissions(articulated_diesel_vehicle, standard_emission_factors, 100_000, 10)

        assert bev['co2_per_km'] < diesel['co2_per_km']
        assert bev['lifetime_emissions'] < diesel['lifetime_emissions']


class TestChargingRequirements:
    """Test charging requirement calculations."""
    
    def test_charging_requirements(
        self, articulated_bev_vehicle, standard_infrastructure_options
    ):
        """Test charging requirements calculation."""
        infra = standard_infrastructure_options.iloc[0]
        req = calculate_charging_requirements(articulated_bev_vehicle, 100_000, infra)
        
        assert req['daily_kwh_required'] > 0
        assert req['charger_power'] == 80.0
        assert req['max_vehicles_per_charger'] > 0 