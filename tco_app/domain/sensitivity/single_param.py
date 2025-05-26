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

__all__ = ["perform_sensitivity_analysis", "perform_sensitivity_analysis_with_dtos"]

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


# --------------------------------------------------------------------------------------
# New DTO-based sensitivity analysis
# --------------------------------------------------------------------------------------

from copy import deepcopy
from tco_app.services.dtos import (
    SensitivityRequest,
    SensitivityResult,
    CalculationRequest,
    CalculationParameters,
)
from tco_app.src.utils.safe_operations import safe_division


def perform_sensitivity_analysis_with_dtos(
    sensitivity_request: SensitivityRequest,
    tco_service: Any,  # Using Any to avoid circular import
) -> List[SensitivityResult]:
    """
    Perform sensitivity analysis using modern DTOs and service architecture.
    
    This function varies a single parameter across the provided range and
    calculates TCO for both base (typically BEV) and comparison (typically Diesel)
    vehicles at each parameter value.
    
    Args:
        sensitivity_request: The sensitivity analysis request containing parameter
                           details and base calculation requests
        tco_service: The TCO calculation service to use for calculations
        
    Returns:
        List of SensitivityResult objects, one for each parameter value
    """
    results: List[SensitivityResult] = []
    
    for param_value in sensitivity_request.parameter_range:
        # Create deep copies of the calculation requests to avoid modifying originals
        base_request = _create_modified_request(
            sensitivity_request.base_calculation_request,
            sensitivity_request.parameter_name,
            param_value,
        )
        
        comparison_request = _create_modified_request(
            sensitivity_request.comparison_calculation_request,
            sensitivity_request.parameter_name,
            param_value,
        )
        
        # Calculate TCO for both vehicles at this parameter value
        base_result = tco_service.calculate_single_vehicle_tco(base_request)
        comparison_result = tco_service.calculate_single_vehicle_tco(comparison_request)
        
        # Calculate differences
        tco_difference = base_result.tco_per_km - comparison_result.tco_per_km
        percentage_difference = safe_division(
            tco_difference,
            comparison_result.tco_per_km,
            context="sensitivity percentage calculation"
        ) * 100
        
        # Create result
        sensitivity_result = SensitivityResult(
            parameter_value=param_value,
            base_tco_result=base_result,
            comparison_tco_result=comparison_result,
            tco_difference=tco_difference,
            percentage_difference=percentage_difference,
            base_tco_per_km=base_result.tco_per_km,
            comparison_tco_per_km=comparison_result.tco_per_km,
            base_annual_operating_cost=base_result.annual_operating_cost,
            comparison_annual_operating_cost=comparison_result.annual_operating_cost,
        )
        
        results.append(sensitivity_result)
    
    return results


def _create_modified_request(
    original_request: CalculationRequest,
    parameter_name: str,
    parameter_value: float,
) -> CalculationRequest:
    """
    Create a modified calculation request with the specified parameter changed.
    
    This function creates a deep copy of the original request and modifies
    the relevant parameter based on the parameter name.
    """
    # Deep copy all dataframes and parameters
    modified_request = CalculationRequest(
        vehicle_data=original_request.vehicle_data.copy(),
        fees_data=original_request.fees_data.copy(),
        parameters=deepcopy(original_request.parameters),
        charging_options=original_request.charging_options.copy(),
        infrastructure_options=original_request.infrastructure_options.copy(),
        financial_params=original_request.financial_params.copy(),
        battery_params=original_request.battery_params.copy(),
        emission_factors=original_request.emission_factors.copy(),
        externalities_data=original_request.externalities_data.copy(),
        incentives=original_request.incentives.copy(),
    )
    
    # Modify the appropriate parameter based on parameter_name
    if parameter_name == "Annual Distance (km)":
        modified_request.parameters.annual_kms = int(parameter_value)
        
    elif parameter_name == "Diesel Price ($/L)":
        # Update diesel price in financial params
        modified_request.financial_params.loc[
            modified_request.financial_params[DataColumns.FINANCE_DESCRIPTION]
            == ParameterKeys.DIESEL_PRICE,
            DataColumns.FINANCE_DEFAULT_VALUE,
        ] = parameter_value
        
    elif parameter_name == "Vehicle Lifetime (years)":
        modified_request.parameters.truck_life_years = int(parameter_value)
        
    elif parameter_name == "Discount Rate (%)":
        modified_request.parameters.discount_rate = parameter_value / 100
        
    elif parameter_name == "Electricity Price ($/kWh)":
        # Get the base price for the selected charging option
        selected_charging_id = original_request.parameters.selected_charging_profile_id
        base_price = original_request.charging_options[
            original_request.charging_options[DataColumns.CHARGING_ID] == selected_charging_id
        ].iloc[0][DataColumns.PER_KWH_PRICE]
        
        # Update all charging options proportionally
        for idx in modified_request.charging_options.index:
            orig_price = original_request.charging_options.loc[idx, DataColumns.PER_KWH_PRICE]
            price_ratio = safe_division(orig_price, base_price, context="electricity price ratio")
            modified_request.charging_options.loc[idx, DataColumns.PER_KWH_PRICE] = (
                parameter_value * price_ratio
            )
    
    return modified_request


def create_sensitivity_adapter(
    bev_vehicle_data: Union[pd.Series, dict],
    diesel_vehicle_data: Union[pd.Series, dict],
    bev_fees: pd.DataFrame,
    diesel_fees: pd.DataFrame,
    charging_options: pd.DataFrame,
    infrastructure_options: pd.DataFrame,
    financial_params: pd.DataFrame,
    battery_params: pd.DataFrame,
    emission_factors: pd.DataFrame,
    externalities_data: pd.DataFrame,
    incentives: pd.DataFrame,
    selected_charging: Any,
    selected_infrastructure: Any,
    annual_kms: int,
    truck_life_years: int,
    discount_rate: float,
    fleet_size: int,
    charging_mix: Dict[int, float] | None = None,
    apply_incentives: bool = True,
) -> tuple[CalculationRequest, CalculationRequest]:
    """
    Create CalculationRequest objects for BEV and Diesel from legacy parameters.
    
    This adapter function helps transition from the old dictionary-based approach
    to the new DTO-based approach.
    """
    # Convert vehicle data to pandas Series if needed
    if isinstance(bev_vehicle_data, dict):
        bev_vehicle_series = pd.Series(bev_vehicle_data)
    else:
        bev_vehicle_series = bev_vehicle_data
        
    if isinstance(diesel_vehicle_data, dict):
        diesel_vehicle_series = pd.Series(diesel_vehicle_data)
    else:
        diesel_vehicle_series = diesel_vehicle_data
    
    # Get fees data - assuming bev_fees and diesel_fees are DataFrames with one row
    bev_fees_series = bev_fees.iloc[0] if not bev_fees.empty else pd.Series()
    diesel_fees_series = diesel_fees.iloc[0] if not diesel_fees.empty else pd.Series()
    
    # Create shared parameters
    parameters = CalculationParameters(
        annual_kms=annual_kms,
        truck_life_years=truck_life_years,
        discount_rate=discount_rate,
        selected_charging_profile_id=selected_charging,
        selected_infrastructure_id=selected_infrastructure,
        fleet_size=fleet_size,
        apply_incentives=apply_incentives,
        charging_mix=charging_mix,
        scenario_name="Sensitivity Analysis",
    )
    
    # Create BEV calculation request
    bev_request = CalculationRequest(
        vehicle_data=bev_vehicle_series,
        fees_data=bev_fees_series,
        parameters=parameters,
        charging_options=charging_options,
        infrastructure_options=infrastructure_options,
        financial_params=financial_params,
        battery_params=battery_params,
        emission_factors=emission_factors,
        externalities_data=externalities_data,
        incentives=incentives,
    )
    
    # Create Diesel calculation request
    diesel_request = CalculationRequest(
        vehicle_data=diesel_vehicle_series,
        fees_data=diesel_fees_series,
        parameters=parameters,
        charging_options=charging_options,
        infrastructure_options=infrastructure_options,
        financial_params=financial_params,
        battery_params=battery_params,
        emission_factors=emission_factors,
        externalities_data=externalities_data,
        incentives=incentives,
    )
    
    return bev_request, diesel_request
