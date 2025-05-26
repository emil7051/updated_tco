from __future__ import annotations

from tco_app.src.constants import DataColumns, ParameterKeys
from tco_app.src.utils.safe_operations import safe_get_parameter

"""Multi-parameter tornado-chart helper extracted from the original monolith.
Keeps implementation identical while reducing per-file line-count.
"""

from typing import Any, Dict

from tco_app.src import pd

from .single_param import perform_sensitivity_analysis

__all__ = ["calculate_tornado_data", "calculate_tornado_data_with_dtos"]

# --------------------------------------------------------------------------------------
# calculate_tornado_data – verbatim (save import path updates only)
# --------------------------------------------------------------------------------------


def calculate_tornado_data(
    bev_results: Dict[str, Any],
    diesel_results: Dict[str, Any],
    financial_params: pd.DataFrame,
    battery_params: pd.DataFrame,
    charging_options: pd.DataFrame,
    infrastructure_options: pd.DataFrame,
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
) -> Dict[str, Any]:
    bev_vehicle_data = bev_results["vehicle_data"]
    diesel_vehicle_data = diesel_results["vehicle_data"]
    bev_fees = bev_results.get("fees")
    diesel_fees = diesel_results.get("fees")

    base_tco = bev_results["tco"]["tco_per_km"]

    sensitivity_data: Dict[str, Dict[str, Any]] = {
        "Annual Distance (km)": {
            "range": [annual_kms * 0.5, annual_kms * 1.5],
            "variation": 0.5,
        },
        "Diesel Price ($/L)": {
            "range": [
                safe_get_parameter(financial_params, ParameterKeys.DIESEL_PRICE) * 0.8,
                safe_get_parameter(financial_params, ParameterKeys.DIESEL_PRICE) * 1.2,
            ],
            "variation": 0.2,
        },
        "Vehicle Lifetime (years)": {
            "range": [max(1, truck_life_years - 3), truck_life_years + 3],
            "variation": 3,
        },
        "Discount Rate (%)": {
            "range": [max(0.5, discount_rate * 100 - 3), discount_rate * 100 + 3],
            "variation": 3,
        },
    }

    base_electricity_price = charging_options[
        charging_options[DataColumns.CHARGING_ID] == selected_charging
    ].iloc[0][DataColumns.PER_KWH_PRICE]
    if "weighted_electricity_price" in bev_results:
        base_electricity_price = bev_results["weighted_electricity_price"]

    sensitivity_data["Electricity Price ($/kWh)"] = {
        "range": [base_electricity_price * 0.8, base_electricity_price * 1.2],
        "variation": 0.2,
    }

    impacts: Dict[str, Any] = {}

    if bev_fees is None or diesel_fees is None:
        raise ValueError("Vehicle fees data is required for tornado chart analysis")

    for param_name, param_info in sensitivity_data.items():
        param_range = param_info["range"]
        results = perform_sensitivity_analysis(
            param_name,
            param_range,
            bev_vehicle_data,
            diesel_vehicle_data,
            bev_fees,
            diesel_fees,
            charging_options,
            infrastructure_options,
            financial_params,
            battery_params,
            emission_factors,
            incentives,
            selected_charging,
            selected_infrastructure,
            annual_kms,
            truck_life_years,
            discount_rate,
            fleet_size,
            charging_mix,
            apply_incentives,
        )
        min_impact = results[0]["bev"]["tco_per_km"] - base_tco
        max_impact = results[1]["bev"]["tco_per_km"] - base_tco
        impacts[param_name] = {"min_impact": min_impact, "max_impact": max_impact}

    return {"base_tco": base_tco, "impacts": impacts}


# --------------------------------------------------------------------------------------
# New DTO-based tornado chart calculation
# --------------------------------------------------------------------------------------

from tco_app.services.dtos import SensitivityRequest, CalculationRequest
from .single_param import perform_sensitivity_analysis_with_dtos


def calculate_tornado_data_with_dtos(
    base_request: CalculationRequest,
    comparison_request: CalculationRequest,
    tco_service: Any,  # Using Any to avoid circular import
) -> Dict[str, Any]:
    """
    Calculate tornado chart data using modern DTO-based approach.
    
    This function calculates sensitivity impacts for multiple parameters
    to create a tornado chart visualization.
    
    Args:
        base_request: Calculation request for base vehicle (typically BEV)
        comparison_request: Calculation request for comparison vehicle (typically Diesel)
        tco_service: TCO calculation service instance
        
    Returns:
        Dictionary with base TCO and impact ranges for each parameter
    """
    # Calculate base TCO for reference
    base_result = tco_service.calculate_single_vehicle_tco(base_request)
    base_tco = base_result.tco_per_km
    
    # Define sensitivity parameters with their ranges
    sensitivity_params = {
        "Annual Distance (km)": {
            "range": [
                base_request.parameters.annual_kms * 0.5,
                base_request.parameters.annual_kms * 1.5
            ],
            "variation": 0.5,
        },
        "Diesel Price ($/L)": {
            "range": [
                safe_get_parameter(base_request.financial_params, ParameterKeys.DIESEL_PRICE) * 0.8,
                safe_get_parameter(base_request.financial_params, ParameterKeys.DIESEL_PRICE) * 1.2,
            ],
            "variation": 0.2,
        },
        "Vehicle Lifetime (years)": {
            "range": [
                max(1, base_request.parameters.truck_life_years - 3),
                base_request.parameters.truck_life_years + 3
            ],
            "variation": 3,
        },
        "Discount Rate (%)": {
            "range": [
                max(0.5, base_request.parameters.discount_rate * 100 - 3),
                base_request.parameters.discount_rate * 100 + 3
            ],
            "variation": 3,
        },
    }
    
    # Add electricity price if base vehicle is BEV
    if base_request.drivetrain == "BEV":
        # Get base electricity price
        selected_charging_id = base_request.parameters.selected_charging_profile_id
        base_electricity_price = base_request.charging_options[
            base_request.charging_options[DataColumns.CHARGING_ID] == selected_charging_id
        ].iloc[0][DataColumns.PER_KWH_PRICE]
        
        # If weighted price is available in the result, use it
        if hasattr(base_result, 'weighted_electricity_price') and base_result.weighted_electricity_price:
            base_electricity_price = base_result.weighted_electricity_price
            
        sensitivity_params["Electricity Price ($/kWh)"] = {
            "range": [base_electricity_price * 0.8, base_electricity_price * 1.2],
            "variation": 0.2,
        }
    
    # Calculate impacts for each parameter
    impacts: Dict[str, Any] = {}
    
    for param_name, param_info in sensitivity_params.items():
        # Create sensitivity request
        sensitivity_request = SensitivityRequest(
            parameter_name=param_name,
            parameter_range=param_info["range"],
            base_calculation_request=base_request,
            comparison_calculation_request=comparison_request,
        )
        
        # Perform sensitivity analysis
        results = perform_sensitivity_analysis_with_dtos(
            sensitivity_request,
            tco_service
        )
        
        # Calculate impact on base vehicle TCO
        if len(results) >= 2:
            min_impact = results[0].base_tco_result.tco_per_km - base_tco
            max_impact = results[1].base_tco_result.tco_per_km - base_tco
            impacts[param_name] = {
                "min_impact": min_impact,
                "max_impact": max_impact
            }
    
    return {"base_tco": base_tco, "impacts": impacts}
