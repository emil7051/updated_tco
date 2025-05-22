import math

import pandas as pd
import pytest

from tco_app.src.constants import Drivetrain
from tco_app.domain.energy import (
	calculate_energy_costs,
	calculate_emissions,
	calculate_charging_requirements,
)
from tco_app.domain.externalities import (
	calculate_externalities,
	calculate_social_tco,
	prepare_externality_comparison,
	calculate_social_benefit_metrics,
)
from tco_app.domain.finance import (
	calculate_annual_costs,
	calculate_acquisition_cost,
	calculate_tco,
	calculate_infrastructure_costs,
	apply_infrastructure_incentives,
	integrate_infrastructure_with_tco,
)
from tco_app.domain.finance_payload import calculate_payload_penalty_costs

# ---------------------------------------------------------------------------
# Shared dummy fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def bev_vehicle():
	return {
		'vehicle_id': 1,
		'vehicle_type': 'Articulated',
		'vehicle_drivetrain': Drivetrain.BEV,
		'kwh_per100km': 130,  # kWh / 100 km
		'payload_t': 42,
		'msrp_price': 400_000,
	}


@pytest.fixture(scope='module')
def diesel_vehicle():
	return {
		'vehicle_id': 2,
		'vehicle_type': 'Articulated',
		'vehicle_drivetrain': Drivetrain.DIESEL,
		'litres_per100km': 28,  # l / 100 km
		'payload_t': 42,
		'msrp_price': 320_000,
	}


@pytest.fixture(scope='module')
def fees():
	return pd.DataFrame([
		{
			'vehicle_id': 1,
			'maintenance_perkm_price': 0.12,
			'registration_annual_price': 900,
			'insurance_annual_price': 2400,
			'stamp_duty_price': 8000,
		},
		{
			'vehicle_id': 2,
			'maintenance_perkm_price': 0.10,
			'registration_annual_price': 850,
			'insurance_annual_price': 2000,
			'stamp_duty_price': 5000,
		},
	])


@pytest.fixture(scope='module')
def charging_options():
	return pd.DataFrame([
		{'charging_id': 'Depot', 'per_kwh_price': 0.25, 'charging_approach': 'Depot 80 kW'},
		{'charging_id': 'Fast', 'per_kwh_price': 0.60, 'charging_approach': 'Public 150 kW'},
	])


@pytest.fixture(scope='module')
def financial_params():
	return pd.DataFrame([
		{'finance_description': 'diesel_price', 'default_value': 2.0},
		{'finance_description': 'discount_rate_percent', 'default_value': 0.07},
		{'finance_description': 'initial_depreciation_percent', 'default_value': 0.1},
		{'finance_description': 'annual_depreciation_percent', 'default_value': 0.05},
	])


@pytest.fixture(scope='module')
def emission_factors():
	return pd.DataFrame([
		{'fuel_type': 'electricity', 'emission_standard': 'Grid', 'co2_per_unit': 0.2},
		{'fuel_type': 'diesel', 'emission_standard': 'Euro IV+', 'co2_per_unit': 2.68},
	])


@pytest.fixture(scope='module')
def externalities():
	return pd.DataFrame([
		{
			'vehicle_class': 'Articulated',
			'drivetrain': Drivetrain.BEV,
			'pollutant_type': 'externalities_total',
			'cost_per_km': 0.03,
		},
		{
			'vehicle_class': 'Articulated',
			'drivetrain': Drivetrain.DIESEL,
			'pollutant_type': 'externalities_total',
			'cost_per_km': 0.07,
		},
	])


@pytest.fixture(scope='module')
def infrastructure_options():
	return pd.DataFrame([
		{
			'infrastructure_id': 'INFRA1',
			'infrastructure_description': '80 kW depot charger',
			'infrastructure_price': 80000,
			'service_life_years': 8,
			'maintenance_percent': 0.02,
		},
	])


@pytest.fixture(scope='module')
def incentives():
	return pd.DataFrame([
		{
			'incentive_flag': 1,
			'incentive_type': 'charging_infrastructure_subsidy',
			'drivetrain': Drivetrain.BEV,
			'incentive_rate': 0.25,
		},
		{
			'incentive_flag': 1,
			'incentive_type': 'purchase_rebate_aud',
			'drivetrain': Drivetrain.BEV,
			'incentive_rate': 40_000,  # flat dollar rebate
		},
		{
			'incentive_flag': 1,
			'incentive_type': 'stamp_duty_exemption',
			'drivetrain': Drivetrain.BEV,
			'incentive_rate': 1.0,  # 100% exemption
		},
	])

# ---------------------------------------------------------------------------
# Tests – Energy domain
# ---------------------------------------------------------------------------

def test_calculate_energy_costs_bev(bev_vehicle, fees, charging_options, financial_params):
	cost = calculate_energy_costs(
		bev_vehicle,
		fees,
		charging_options,
		financial_params,
		selected_charging='Depot',
	)
	assert math.isclose(cost, 1.30 * 0.25)  # 130 kWh/100km => 1.30 * price


def test_calculate_energy_costs_diesel(diesel_vehicle, fees, charging_options, financial_params):
	cost = calculate_energy_costs(
		diesel_vehicle,
		fees,
		charging_options,
		financial_params,
		selected_charging='Depot',
	)
	assert math.isclose(cost, 0.28 * 2.0)  # 28 L/100km => 0.28 * price


def test_calculate_emissions(bev_vehicle, diesel_vehicle, emission_factors):
	bev = calculate_emissions(bev_vehicle, emission_factors, 100_000, 10)
	diesel = calculate_emissions(diesel_vehicle, emission_factors, 100_000, 10)

	assert bev['co2_per_km'] < diesel['co2_per_km']
	assert bev['lifetime_emissions'] < diesel['lifetime_emissions']


def test_charging_requirements(bev_vehicle, infrastructure_options):
	infra = infrastructure_options.iloc[0]
	req = calculate_charging_requirements(bev_vehicle, 100_000, infra)
	assert req['daily_kwh_required'] > 0
	assert req['charger_power'] == 80.0
	assert req['max_vehicles_per_charger'] > 0

# ---------------------------------------------------------------------------
# Tests – Externalities & social TCO
# ---------------------------------------------------------------------------

def test_externalities_and_social_tco(bev_vehicle, diesel_vehicle, externalities, emission_factors):
	bev_ext = calculate_externalities(bev_vehicle, externalities, 100_000, 10, 0.07)
	diesel_ext = calculate_externalities(diesel_vehicle, externalities, 100_000, 10, 0.07)

	bev_social = calculate_social_tco({'npv_total_cost': 1_000_000, 'annual_kms': 100_000, 'truck_life_years': 10, 'payload_t': 42}, bev_ext)

	assert bev_ext['externality_per_km'] < diesel_ext['externality_per_km']
	assert bev_social['social_tco_lifetime'] > 1_000_000  # Adds externality

# ---------------------------------------------------------------------------
# Tests – Finance helpers
# ---------------------------------------------------------------------------

def test_finance_infrastructure_and_tco(bev_vehicle, fees, financial_params, infrastructure_options, incentives):
	bev_fees = fees[fees['vehicle_id'] == bev_vehicle['vehicle_id']]
	annual = calculate_annual_costs(bev_vehicle, bev_fees, 0.5, 100_000)
	acq = calculate_acquisition_cost(bev_vehicle, bev_fees, incentives, apply_incentives=False)
	residual = 5_000
	tco = calculate_tco(bev_vehicle, bev_fees, annual, acq, residual, 0, 500_000, 100_000, 10)

	infra_opt = infrastructure_options.iloc[0]
	infra = calculate_infrastructure_costs(infra_opt, 10, 0.07, fleet_size=1)
	infra_sub = apply_infrastructure_incentives(infra, incentives)
	combined = integrate_infrastructure_with_tco(tco, infra_sub)

	assert combined['npv_total_cost'] > tco['npv_total_cost']
	assert 'infrastructure_costs' in combined

# ---------------------------------------------------------------------------
# Tests – Payload penalty
# ---------------------------------------------------------------------------

def test_payload_penalty(bev_vehicle, diesel_vehicle, fees, financial_params):
	# craft minimal results dicts
	bev_results = {
		'vehicle_data': bev_vehicle,
		'annual_costs': {'annual_operating_cost': 50_000},
		'tco': {'tco_per_tonne_km': 0.9, 'npv_total_cost': 900_000},
		'annual_kms': 100_000,
		'truck_life_years': 10,
	}
	diesel_results = {
		'vehicle_data': diesel_vehicle,
		'annual_costs': {'annual_operating_cost': 60_000},
		'tco': {'tco_per_tonne_km': 1.1, 'npv_total_cost': 1_000_000},
		'annual_kms': 100_000,
		'truck_life_years': 10,
	}

	penalty = calculate_payload_penalty_costs(bev_results, diesel_results, financial_params)

	assert penalty['has_penalty'] is False  # identical payload in fixture 

# Additional test for acquisition cost with incentives

def test_acquisition_cost_with_incentives(bev_vehicle, fees, incentives):
	bev_fees = fees[fees['vehicle_id'] == bev_vehicle['vehicle_id']]
	cost_without = calculate_acquisition_cost(bev_vehicle, bev_fees, incentives, apply_incentives=False)
	cost_with = calculate_acquisition_cost(bev_vehicle, bev_fees, incentives, apply_incentives=True)
	assert cost_with < cost_without

# Test externality comparison and social benefit metrics

def test_externality_comparison_and_social_benefit(bev_vehicle, diesel_vehicle, externalities, financial_params):
	bev_ext = calculate_externalities(bev_vehicle, externalities, 50_000, 5, 0.05)
	diesel_ext = calculate_externalities(diesel_vehicle, externalities, 50_000, 5, 0.05)
	comparison = prepare_externality_comparison(bev_ext, diesel_ext)
	assert comparison['total_savings'] > 0

	bev_results = {
		'acquisition_cost': 400_000,
		'annual_costs': {'annual_operating_cost': 40_000},
		'externalities': bev_ext,
	}
	diesel_results = {
		'acquisition_cost': 320_000,
		'annual_costs': {'annual_operating_cost': 60_000},
		'externalities': diesel_ext,
	}

	metrics = calculate_social_benefit_metrics(bev_results, diesel_results, 50_000, 5, 0.05)
	assert metrics['social_benefit_cost_ratio'] > 0 