from __future__ import annotations

from tco_app.src.constants import DataColumns, ParameterKeys
from tco_app.src.utils.safe_operations import safe_division

"""Single-parameter sensitivity analysis helpers (extracted from the former
`tco_app.domain.sensitivity` monolith to satisfy the 300-line file limit).

The implementation is a verbatim copy of the original logic so regression
behaviour is unchanged.  Only import paths were updated where the monolith
previously referenced legacy modules.
"""

from typing import Any, Dict, List, Union

from tco_app.domain.energy import calculate_energy_costs
from tco_app.domain.finance import (
    apply_infrastructure_incentives,
    calculate_acquisition_cost,
    calculate_annual_costs,
    calculate_infrastructure_costs,
    calculate_npv,
    calculate_residual_value,
    calculate_tco,
    integrate_infrastructure_with_tco,
)
from tco_app.src import pd
from tco_app.src.utils.battery import calculate_battery_replacement

__all__ = ["perform_sensitivity_analysis"]

# --------------------------------------------------------------------------------------
# perform_sensitivity_analysis (verbatim copy)
# --------------------------------------------------------------------------------------


def perform_sensitivity_analysis(
    parameter_name: str,
    parameter_range: List[Any],
    bev_vehicle_data: Union[pd.Series, dict],
    diesel_vehicle_data: Union[pd.Series, dict],
    bev_fees: pd.DataFrame,
    diesel_fees: pd.DataFrame,
    charging_options: pd.DataFrame,
    infrastructure_options: pd.DataFrame,
    financial_params: pd.DataFrame,
    battery_params: pd.DataFrame,
    emission_factors: pd.DataFrame,
    incentives: pd.DataFrame,
    selected_charging: Any,
    selected_infrastructure: Any,
    annual_kms: int,
    truck_life_years: int,
    discount_rate: float,
    fleet_size: int,
    charging_mix: Dict[int, float] | None = None,
    apply_incentives: bool = True,
) -> List[Dict[str, Any]]:
    """Return result rows for each *parameter_value* in *parameter_range*.

    This is the same algorithm used previously; refactor only affects file
    organisation, not behaviour.
    """
    results: List[Dict[str, Any]] = []

    for param_value in parameter_range:
        financial_params_copy = financial_params.copy()
        battery_params_copy = battery_params.copy()
        current_annual_kms = annual_kms
        current_discount_rate = discount_rate
        current_truck_life_years = truck_life_years
        current_charging_mix = charging_mix
        modified_charging_options = charging_options

        if parameter_name == "Annual Distance (km)":
            current_annual_kms = param_value
        elif parameter_name == "Diesel Price ($/L)":
            financial_params_copy.loc[
                financial_params_copy[DataColumns.FINANCE_DESCRIPTION]
                == ParameterKeys.DIESEL_PRICE,
                DataColumns.FINANCE_DEFAULT_VALUE,
            ] = param_value
        elif parameter_name == "Vehicle Lifetime (years)":
            current_truck_life_years = param_value
        elif parameter_name == "Discount Rate (%)":
            current_discount_rate = param_value / 100
        elif parameter_name == "Electricity Price ($/kWh)":
            base_price = charging_options[
                charging_options[DataColumns.CHARGING_ID] == selected_charging
            ].iloc[0][DataColumns.PER_KWH_PRICE]
            modified_charging_options = charging_options.copy()
            for idx in modified_charging_options.index:
                orig = charging_options.loc[idx, DataColumns.PER_KWH_PRICE]
                modified_charging_options.loc[idx, DataColumns.PER_KWH_PRICE] = (
                    param_value
                    * (
                        safe_division(
                            orig, base_price, context="orig/base_price calculation"
                        )
                    )
                )
        else:
            # Unsupported parameter name – skip
            continue

        # --------------- Energy costs ---------------
        bev_energy_cost_per_km = calculate_energy_costs(
            bev_vehicle_data,
            bev_fees,
            modified_charging_options,
            financial_params_copy,
            selected_charging,
            current_charging_mix,
        )
        diesel_energy_cost_per_km = calculate_energy_costs(
            diesel_vehicle_data,
            diesel_fees,
            charging_options,
            financial_params_copy,
            selected_charging,
        )

        # --------------- Annual costs ---------------
        bev_annual_costs = calculate_annual_costs(
            bev_vehicle_data,
            bev_fees,
            bev_energy_cost_per_km,
            current_annual_kms,
            incentives,
            apply_incentives,
        )
        diesel_annual_costs = calculate_annual_costs(
            diesel_vehicle_data,
            diesel_fees,
            diesel_energy_cost_per_km,
            current_annual_kms,
            incentives,
            apply_incentives,
        )

        # --------------- Acquisition & residual ---------------
        bev_acquisition = calculate_acquisition_cost(
            bev_vehicle_data,
            bev_fees,
            incentives,
            apply_incentives,
        )
        diesel_acquisition = calculate_acquisition_cost(
            diesel_vehicle_data,
            diesel_fees,
            incentives,
            apply_incentives,
        )

        initial_dep = financial_params_copy[
            financial_params_copy[DataColumns.FINANCE_DESCRIPTION]
            == ParameterKeys.INITIAL_DEPRECIATION
        ].iloc[0][DataColumns.FINANCE_DEFAULT_VALUE]
        annual_dep = financial_params_copy[
            financial_params_copy[DataColumns.FINANCE_DESCRIPTION]
            == ParameterKeys.ANNUAL_DEPRECIATION
        ].iloc[0][DataColumns.FINANCE_DEFAULT_VALUE]

        bev_residual = calculate_residual_value(
            bev_vehicle_data,
            current_truck_life_years,
            initial_dep,
            annual_dep,
        )
        diesel_residual = calculate_residual_value(
            diesel_vehicle_data,
            current_truck_life_years,
            initial_dep,
            annual_dep,
        )

        # --------------- Battery replacement ---------------
        bev_battery_replacement = calculate_battery_replacement(
            bev_vehicle_data,
            battery_params_copy,
            current_truck_life_years,
            current_discount_rate,
        )

        # --------------- NPV of annuals ---------------
        bev_npv_annual = calculate_npv(
            bev_annual_costs["annual_operating_cost"],
            current_discount_rate,
            current_truck_life_years,
        )
        diesel_npv_annual = calculate_npv(
            diesel_annual_costs["annual_operating_cost"],
            current_discount_rate,
            current_truck_life_years,
        )

        # --------------- TCO ---------------
        bev_tco = calculate_tco(
            bev_vehicle_data,
            bev_fees,
            bev_annual_costs,
            bev_acquisition,
            bev_residual,
            bev_battery_replacement,
            bev_npv_annual,
            current_annual_kms,
            current_truck_life_years,
        )
        diesel_tco = calculate_tco(
            diesel_vehicle_data,
            diesel_fees,
            diesel_annual_costs,
            diesel_acquisition,
            diesel_residual,
            0,
            diesel_npv_annual,
            current_annual_kms,
            current_truck_life_years,
        )

        # --------------- Infrastructure ---------------
        infra_data = infrastructure_options[
            infrastructure_options[DataColumns.INFRASTRUCTURE_ID]
            == selected_infrastructure
        ].iloc[0]
        infra_costs = calculate_infrastructure_costs(
            infra_data,
            current_truck_life_years,
            current_discount_rate,
            fleet_size,
        )
        infra_with_incentives = apply_infrastructure_incentives(
            infra_costs,
            incentives,
            apply_incentives,
        )
        bev_tco_with_infra = integrate_infrastructure_with_tco(
            bev_tco,
            infra_with_incentives,
            apply_incentives,
        )

        # --------------- Output ---------------
        results.append(
            {
                "parameter_value": param_value,
                "bev": {
                    "tco_per_km": bev_tco_with_infra["tco_per_km"],
                    "tco_lifetime": bev_tco_with_infra["tco_lifetime"],
                    "annual_operating_cost": bev_annual_costs["annual_operating_cost"],
                },
                "diesel": {
                    "tco_per_km": diesel_tco["tco_per_km"],
                    "tco_lifetime": diesel_tco["tco_lifetime"],
                    "annual_operating_cost": diesel_annual_costs[
                        "annual_operating_cost"
                    ],
                },
            }
        )

    return results
