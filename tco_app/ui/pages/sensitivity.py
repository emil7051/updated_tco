"""Sensitivity analysis page module."""
import streamlit as st
from tco_app.ui.context import get_context
from tco_app.domain.sensitivity import perform_sensitivity_analysis, perform_sensitivity_analysis_with_dtos, create_sensitivity_adapter
from tco_app.plotters import create_payload_sensitivity_chart, create_sensitivity_chart
from tco_app.ui.components.sensitivity_components import (
    SensitivityContext,
    ParameterRangeCalculator,
)
from typing import List
from tco_app.services.dtos import SensitivityRequest


def render():
    """Render sensitivity analysis page."""
    # Step 1: Load and validate context
    context = SensitivityContext.from_context(get_context())

    # Step 2: Display header and info
    _display_header()

    # Step 3: Get parameter selection
    sensitivity_param = _get_parameter_selection()

    # Step 4: Initialize components
    range_calculator = ParameterRangeCalculator(num_points=11)

    # Step 5: Perform analysis based on selection
    if sensitivity_param == "Annual Distance (km) with Payload Effect":
        _display_payload_sensitivity(context, range_calculator)
    else:
        _display_parameter_sensitivity(sensitivity_param, context, range_calculator)


def _display_header():
    """Display page header and information."""
    st.subheader("Sensitivity Analysis")
    st.info(
        "Sensitivity Analysis helps understand how changes in key parameters "
        "affect the TCO comparison."
    )


def _get_parameter_selection() -> str:
    """Get user's parameter selection."""
    return st.selectbox(
        "Select Parameter for Sensitivity Analysis",
        [
            "Annual Distance (km)",
            "Diesel Price ($/L)",
            "Electricity Price ($/kWh)",
            "Vehicle Lifetime (years)",
            "Discount Rate (%)",
            "Annual Distance (km) with Payload Effect",
        ],
    )


def _display_payload_sensitivity(
    context: SensitivityContext, range_calculator: ParameterRangeCalculator
):
    """Display payload sensitivity analysis."""
    # Calculate distance range for payload analysis
    distances = range_calculator.calculate_annual_distance_range(context.annual_kms)

    # Create and display chart
    chart = create_payload_sensitivity_chart(
        context.bev_results,
        context.diesel_results,
        context.financial_params_with_ui,
        distances,
    )

    st.plotly_chart(
        chart,
        use_container_width=True,
        key="payload_sensitivity_chart",
    )

    # Display interpretation
    st.markdown(
        "Values below 1.0 indicate BEV is more cost-effective. "
        "The gap between the lines shows the economic impact of "
        "payload limitations at higher utilisation."
    )


def _display_parameter_sensitivity(
    param_type: str,
    context: SensitivityContext,
    range_calculator: ParameterRangeCalculator,
):
    """Display standard parameter sensitivity analysis."""
    # Calculate parameter range based on type
    param_range = _calculate_parameter_range(param_type, context, range_calculator)

    # Perform sensitivity analysis
    with st.spinner(f"Calculating sensitivity for {param_type}…"):
        # Check if we should use the new DTO-based approach
        use_new_approach = st.session_state.get("use_dto_sensitivity", False)
        
        if use_new_approach:
            sensitivity_results = _perform_analysis_with_dtos(param_type, param_range, context)
        else:
            sensitivity_results = _perform_analysis(param_type, param_range, context)

        # Create and display chart
        chart = create_sensitivity_chart(
            context.bev_results,
            context.diesel_results,
            param_type,
            param_range,
            sensitivity_results,
        )

        st.plotly_chart(chart, use_container_width=True, key="sensitivity_chart")


def _calculate_parameter_range(
    param_type: str,
    context: SensitivityContext,
    range_calculator: ParameterRangeCalculator,
) -> List[float]:
    """Calculate range for a given parameter type."""
    range_methods = {
        "Annual Distance (km)": lambda: range_calculator.calculate_annual_distance_range(
            context.annual_kms
        ),
        "Diesel Price ($/L)": lambda: range_calculator.calculate_diesel_price_range(
            context.financial_params_with_ui
        ),
        "Electricity Price ($/kWh)": (
            lambda: range_calculator.calculate_electricity_price_range(
                context.bev_results, context.charging_options, context.selected_charging
            )
        ),
        "Vehicle Lifetime (years)": (
            lambda: range_calculator.calculate_vehicle_lifetime_range(
                context.truck_life_years
            )
        ),
        "Discount Rate (%)": lambda: range_calculator.calculate_discount_rate_range(
            context.discount_rate
        ),
    }

    if param_type not in range_methods:
        raise ValueError(f"Unknown parameter type: {param_type}")

    return range_methods[param_type]()


def _perform_analysis(
    param_type: str, param_range: List[float], context: SensitivityContext
) -> dict:
    """Perform sensitivity analysis for given parameter."""
    return perform_sensitivity_analysis(
        param_type,
        param_range,
        context.bev_vehicle_data,
        context.diesel_vehicle_data,
        context.bev_fees,
        context.diesel_fees,
        context.charging_options,
        context.infrastructure_options,
        context.financial_params_with_ui,
        context.battery_params_with_ui,
        context.emission_factors,
        context.incentives,
        context.selected_charging,
        context.selected_infrastructure,
        context.annual_kms,
        context.truck_life_years,
        context.discount_rate,
        context.fleet_size,
        context.charging_mix,
        context.apply_incentives,
    )


def _perform_analysis_with_dtos(
    param_type: str, param_range: List[float], context: SensitivityContext
) -> dict:
    """Perform sensitivity analysis using new DTO-based approach."""
    # Get externalities data from context - check if it exists
    externalities_data = getattr(context, 'externalities_data', None)
    if externalities_data is None:
        # Try to get from the full context
        full_context = get_context()
        externalities_data = full_context.get('externalities_data', None)
        if externalities_data is None:
            # Create a fallback repository to get externalities
            from tco_app.src.data_loading import load_data
            from tco_app.repositories import ParametersRepository
            data_tables = load_data()
            params_repo = ParametersRepository(data_tables)
            externalities_data = params_repo.get_externalities_data()
    
    # Create calculation requests using adapter
    bev_request, diesel_request = create_sensitivity_adapter(
        context.bev_vehicle_data,
        context.diesel_vehicle_data,
        context.bev_fees,
        context.diesel_fees,
        context.charging_options,
        context.infrastructure_options,
        context.financial_params_with_ui,
        context.battery_params_with_ui,
        context.emission_factors,
        externalities_data,
        context.incentives,
        context.selected_charging,
        context.selected_infrastructure,
        context.annual_kms,
        context.truck_life_years,
        context.discount_rate,
        context.fleet_size,
        context.charging_mix,
        context.apply_incentives,
    )
    
    # Create TCO service
    from tco_app.src.data_loading import load_data
    from tco_app.repositories import VehicleRepository, ParametersRepository
    from tco_app.services.tco_calculation_service import TCOCalculationService
    
    data_tables = load_data()
    vehicle_repo = VehicleRepository(data_tables)
    params_repo = ParametersRepository(data_tables)
    tco_service = TCOCalculationService(vehicle_repo, params_repo)
    
    # Create sensitivity request
    sensitivity_request = SensitivityRequest(
        parameter_name=param_type,
        parameter_range=param_range,
        base_calculation_request=bev_request,
        comparison_calculation_request=diesel_request,
    )
    
    # Perform analysis
    dto_results = perform_sensitivity_analysis_with_dtos(
        sensitivity_request,
        tco_service
    )
    
    # Convert results to legacy format for compatibility with existing charts
    legacy_results = []
    for result in dto_results:
        legacy_results.append({
            "parameter_value": result.parameter_value,
            "bev": {
                "tco_per_km": result.base_tco_result.tco_per_km,
                "tco_lifetime": result.base_tco_result.tco_total_lifetime,
                "annual_operating_cost": result.base_tco_result.annual_operating_cost,
            },
            "diesel": {
                "tco_per_km": result.comparison_tco_result.tco_per_km,
                "tco_lifetime": result.comparison_tco_result.tco_total_lifetime,
                "annual_operating_cost": result.comparison_tco_result.annual_operating_cost,
            },
        })
    
    return legacy_results
