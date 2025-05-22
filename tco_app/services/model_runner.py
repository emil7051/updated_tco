"""Model-runner service.

Takes the fully-specified UI / scenario inputs and returns:
    bev_results, diesel_results, comparison_metrics
in the exact structure previously built inside `ui.context`.

This lets UI code depend on a single helper instead of re-implementing the
maths – and it means we can unit-test the modelling pipeline in isolation from
Streamlit widgets.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from tco_app.domain.energy import (
    calculate_energy_costs,
    calculate_emissions,
    calculate_charging_requirements,
)
from tco_app.domain.finance import (
    calculate_annual_costs,
    calculate_acquisition_cost,
    calculate_npv,
    calculate_residual_value,
    calculate_tco,
    calculate_infrastructure_costs,
    apply_infrastructure_incentives,
    integrate_infrastructure_with_tco,
)
from tco_app.domain.externalities import (
    calculate_externalities,
    calculate_social_tco,
)
from tco_app.domain.sensitivity import calculate_comparative_metrics
from tco_app.src.utils.battery import calculate_battery_replacement
from tco_app.src.utils.energy import weighted_electricity_price
from tco_app.src.constants import Drivetrain

# --------------------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------------------

def run_model(
    # vehicle specs & fees
    bev_vehicle_data: Any,
    diesel_vehicle_data: Any,
    bev_fees: Any,
    diesel_fees: Any,
    # parameter tables
    charging_options,
    infrastructure_options,
    financial_params_with_ui,
    battery_params_with_ui,
    emission_factors,
    incentives,
    # scenario selections / scalars
    selected_charging: int,
    selected_infrastructure: int,
    annual_kms: int,
    truck_life_years: int,
    discount_rate: float,
    fleet_size: int,
    charging_mix: Optional[Dict[int, float]],
    apply_incentives: bool,
    scenario_meta: Dict[str, str],
) -> Dict[str, Any]:
    """Compute TCO results for the selected BEV & diesel pair.

    Parameters are intentionally verbose – the UI layer already has all of
    them and passing everything in keeps this function pure & testable.
    """

    # ------------------------------------------------------------------
    # Energy + annual costs
    # ------------------------------------------------------------------
    bev_energy_cost_per_km = calculate_energy_costs(
        bev_vehicle_data,
        bev_fees,
        charging_options,
        financial_params_with_ui,
        selected_charging,
        charging_mix,
    )
    diesel_energy_cost_per_km = calculate_energy_costs(
        diesel_vehicle_data,
        diesel_fees,
        charging_options,
        financial_params_with_ui,
        selected_charging,
    )

    bev_annual_costs = calculate_annual_costs(
        bev_vehicle_data,
        bev_fees,
        bev_energy_cost_per_km,
        annual_kms,
        incentives,
        apply_incentives,
    )
    diesel_annual_costs = calculate_annual_costs(
        diesel_vehicle_data,
        diesel_fees,
        diesel_energy_cost_per_km,
        annual_kms,
        incentives,
        apply_incentives,
    )

    # ------------------------------------------------------------------
    # Emissions
    # ------------------------------------------------------------------
    bev_emissions = calculate_emissions(
        bev_vehicle_data, emission_factors, annual_kms, truck_life_years
    )
    diesel_emissions = calculate_emissions(
        diesel_vehicle_data, emission_factors, annual_kms, truck_life_years
    )

    # ------------------------------------------------------------------
    # Acquisition + depreciation
    # ------------------------------------------------------------------
    bev_acquisition = calculate_acquisition_cost(
        bev_vehicle_data, bev_fees, incentives, apply_incentives
    )
    diesel_acquisition = calculate_acquisition_cost(
        diesel_vehicle_data, diesel_fees, incentives, apply_incentives
    )

    init_dep = 0  # already baked into residual calc inside finance domain
    annual_dep = 0

    bev_residual = calculate_residual_value(
        bev_vehicle_data, truck_life_years, init_dep, annual_dep
    )
    diesel_residual = calculate_residual_value(
        diesel_vehicle_data, truck_life_years, init_dep, annual_dep
    )

    # ------------------------------------------------------------------
    # Battery & NPV
    # ------------------------------------------------------------------
    bev_battery_replacement = calculate_battery_replacement(
        bev_vehicle_data, battery_params_with_ui, truck_life_years, discount_rate
    )
    bev_npv_annual = calculate_npv(
        bev_annual_costs['annual_operating_cost'], discount_rate, truck_life_years
    )
    diesel_npv_annual = calculate_npv(
        diesel_annual_costs['annual_operating_cost'], discount_rate, truck_life_years
    )

    # ------------------------------------------------------------------
    # Raw TCO
    # ------------------------------------------------------------------
    bev_tco = calculate_tco(
        bev_vehicle_data,
        bev_fees,
        bev_annual_costs,
        bev_acquisition,
        bev_residual,
        bev_battery_replacement,
        bev_npv_annual,
        annual_kms,
        truck_life_years,
    )
    diesel_tco = calculate_tco(
        diesel_vehicle_data,
        diesel_fees,
        diesel_annual_costs,
        diesel_acquisition,
        diesel_residual,
        0,
        diesel_npv_annual,
        annual_kms,
        truck_life_years,
    )

    # ------------------------------------------------------------------
    # Externalities
    # ------------------------------------------------------------------
    bev_externalities = calculate_externalities(
        bev_vehicle_data,
        emission_factors,
        annual_kms,
        truck_life_years,
        discount_rate,
    )
    diesel_externalities = calculate_externalities(
        diesel_vehicle_data,
        emission_factors,
        annual_kms,
        truck_life_years,
        discount_rate,
    )

    # ------------------------------------------------------------------
    # Infrastructure integration (BEV only)
    # ------------------------------------------------------------------
    selected_infra_data = infrastructure_options[
        infrastructure_options['infrastructure_id'] == selected_infrastructure
    ].iloc[0]

    bev_charging_requirements = calculate_charging_requirements(
        bev_vehicle_data, annual_kms, selected_infra_data
    )
    infrastructure_costs = calculate_infrastructure_costs(
        selected_infra_data, truck_life_years, discount_rate, fleet_size
    )
    infra_costs_with_incentives = apply_infrastructure_incentives(
        infrastructure_costs, incentives, apply_incentives
    )
    infra_costs_with_incentives['fleet_size'] = fleet_size

    bev_tco_with_infra = integrate_infrastructure_with_tco(
        bev_tco, infra_costs_with_incentives, apply_incentives
    )

    # ------------------------------------------------------------------
    # Assemble results dicts (identical to legacy structure)
    # ------------------------------------------------------------------
    bev_results = {
        'vehicle_data': bev_vehicle_data,
        'fees': bev_fees,
        'energy_cost_per_km': bev_energy_cost_per_km,
        'annual_costs': bev_annual_costs,
        'emissions': bev_emissions,
        'acquisition_cost': bev_acquisition,
        'residual_value': bev_residual,
        'battery_replacement': bev_battery_replacement,
        'npv_annual_cost': bev_npv_annual,
        'tco': bev_tco_with_infra,
        'externalities': bev_externalities,
        'social_tco': calculate_social_tco(bev_tco_with_infra, bev_externalities),
        'annual_kms': annual_kms,
        'truck_life_years': truck_life_years,
        'charging_requirements': bev_charging_requirements,
        'infrastructure_costs': infra_costs_with_incentives,
        'selected_infrastructure_description': selected_infra_data['infrastructure_description'],
        'charging_options': charging_options,
        'discount_rate': discount_rate,
        'scenario': scenario_meta,
    }
    if charging_mix:
        bev_results['charging_mix'] = charging_mix
        bev_results['weighted_electricity_price'] = weighted_electricity_price(charging_mix, charging_options)

    diesel_results = {
        'vehicle_data': diesel_vehicle_data,
        'fees': diesel_fees,
        'energy_cost_per_km': diesel_energy_cost_per_km,
        'annual_costs': diesel_annual_costs,
        'emissions': diesel_emissions,
        'acquisition_cost': diesel_acquisition,
        'residual_value': diesel_residual,
        'battery_replacement': 0,
        'npv_annual_cost': diesel_npv_annual,
        'tco': diesel_tco,
        'externalities': diesel_externalities,
        'social_tco': calculate_social_tco(diesel_tco, diesel_externalities),
        'annual_kms': annual_kms,
        'truck_life_years': truck_life_years,
        'discount_rate': discount_rate,
        'scenario': scenario_meta,
    }

    comparison_metrics = calculate_comparative_metrics(
        bev_results, diesel_results, annual_kms, truck_life_years
    )
    bev_results['comparison'] = comparison_metrics

    return {
        'bev_results': bev_results,
        'diesel_results': diesel_results,
        'comparison_metrics': comparison_metrics,
    } 