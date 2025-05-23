"""Unit tests for finance domain module."""
import pytest
from tco_app.domain.finance import (
    calculate_annual_costs,
    calculate_acquisition_cost,
    calculate_tco,
    calculate_infrastructure_costs,
    apply_infrastructure_incentives,
    integrate_infrastructure_with_tco,
)
from tco_app.tests.fixtures.vehicles import *


class TestFinanceCalculations:
    """Test finance calculations."""
    
    def test_finance_infrastructure_and_tco(
        self, articulated_bev_vehicle, standard_fees, standard_financial_params, 
        standard_infrastructure_options, standard_incentives
    ):
        """Test finance infrastructure and TCO integration."""
        bev_fees = standard_fees[standard_fees['vehicle_id'] == articulated_bev_vehicle['vehicle_id']]
        annual = calculate_annual_costs(articulated_bev_vehicle, bev_fees, 0.5, 100_000)
        acq = calculate_acquisition_cost(articulated_bev_vehicle, bev_fees, standard_incentives, apply_incentives=False)
        residual = 5_000
        tco = calculate_tco(articulated_bev_vehicle, bev_fees, annual, acq, residual, 0, 500_000, 100_000, 10)

        infra_opt = standard_infrastructure_options.iloc[0]
        infra = calculate_infrastructure_costs(infra_opt, 10, 0.07, fleet_size=1)
        infra_sub = apply_infrastructure_incentives(infra, standard_incentives)
        combined = integrate_infrastructure_with_tco(tco, infra_sub)

        assert combined['npv_total_cost'] > tco['npv_total_cost']
        assert 'infrastructure_costs' in combined
    
    def test_acquisition_cost_with_incentives(
        self, articulated_bev_vehicle, standard_fees, standard_incentives
    ):
        """Test acquisition cost calculation with and without incentives."""
        bev_fees = standard_fees[standard_fees['vehicle_id'] == articulated_bev_vehicle['vehicle_id']]
        cost_without = calculate_acquisition_cost(articulated_bev_vehicle, bev_fees, standard_incentives, apply_incentives=False)
        cost_with = calculate_acquisition_cost(articulated_bev_vehicle, bev_fees, standard_incentives, apply_incentives=True)
        assert cost_with < cost_without 