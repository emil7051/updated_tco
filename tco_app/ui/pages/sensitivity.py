"""Sensitivity analysis page module."""
import streamlit as st
from typing import List
import traceback
import sys
import os
import importlib.util

# Add debugging info for deployment environments
if st.session_state.get("debug_mode", False):
    st.sidebar.write("Debug Info:")
    st.sidebar.write(f"Python version: {sys.version}")
    st.sidebar.write(f"Python path: {sys.path[:3]}")
    st.sidebar.write(f"Current working directory: {os.getcwd()}")

try:
    # Add the project root to the Python path if needed
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    from tco_app.ui.context import get_context
    from tco_app.domain.sensitivity import (
        perform_sensitivity_analysis_with_dtos, 
        create_sensitivity_adapter
    )
    from tco_app.plotters import create_payload_sensitivity_chart, create_sensitivity_chart
    
    # Import sensitivity components using the method that works in Streamlit Cloud
    # Based on debug output, method 3 (path manipulation) works reliably
    components_dir = os.path.join(project_root, 'tco_app', 'ui', 'components')
    if components_dir not in sys.path:
        sys.path.insert(0, components_dir)
    
    try:
        # Try direct import first (Method 3 from debug)
        import sensitivity_components
        SensitivityContext = sensitivity_components.SensitivityContext
        ParameterRangeCalculator = sensitivity_components.ParameterRangeCalculator
    except ImportError:
        # Fallback to importlib (Method 4 from debug)
        sensitivity_file = os.path.join(components_dir, 'sensitivity_components.py')
        spec = importlib.util.spec_from_file_location("sensitivity_components", sensitivity_file)
        sensitivity_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sensitivity_module)
        SensitivityContext = sensitivity_module.SensitivityContext
        ParameterRangeCalculator = sensitivity_module.ParameterRangeCalculator
    
    from tco_app.services.dtos import SensitivityRequest
except ImportError as e:
    st.error(f"Import Error: {str(e)}")
    st.error("Full traceback:")
    st.code(traceback.format_exc())
    st.stop()


def render():
    """Render sensitivity analysis page."""
    try:
        # Step 1: Load full context once at the beginning
        full_context = get_context()
        
        # Step 2: Extract externalities data for later use
        externalities_data = full_context.get('externalities_data', None)
        
        # Step 3: Create SensitivityContext from the full context
        context = SensitivityContext.from_context(full_context)

        # Step 4: Display header and info
        _display_header()

        # Step 5: Get parameter selection
        sensitivity_param = _get_parameter_selection()

        # Step 6: Initialize components
        range_calculator = ParameterRangeCalculator(num_points=11)

        # Step 7: Perform analysis based on selection
        if sensitivity_param == "Annual Distance (km) with Payload Effect":
            _display_payload_sensitivity(context, range_calculator)
        else:
            _display_parameter_sensitivity(sensitivity_param, context, range_calculator, externalities_data)
            
    except Exception as e:
        st.error(f"Error rendering sensitivity page: {str(e)}")
        st.error("Full traceback:")
        st.code(traceback.format_exc())


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
        key="sensitivity_parameter_selector",
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
    externalities_data: dict,
):
    """Display standard parameter sensitivity analysis."""
    # Calculate parameter range based on type
    param_range = _calculate_parameter_range(param_type, context, range_calculator)

    # Perform sensitivity analysis
    with st.spinner(f"Calculating sensitivity for {param_type}…"):
        # Always use the DTO-based approach
        sensitivity_results = _perform_analysis_with_dtos(param_type, param_range, context, externalities_data)

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


def _perform_analysis_with_dtos(
    param_type: str, param_range: List[float], context: SensitivityContext, externalities_data: dict
) -> dict:
    """Perform sensitivity analysis using new DTO-based approach."""
    # If externalities_data is None, load it as a fallback
    if externalities_data is None:
        # Import here to avoid circular imports and containerisation issues
        import tco_app.repositories as repos
        from tco_app.src.data_loading import load_data
        
        data_tables = load_data()
        params_repo = repos.ParametersRepository(data_tables)
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
    # Import here to avoid circular imports and containerisation issues
    import tco_app.repositories as repos
    from tco_app.src.data_loading import load_data
    from tco_app.services.tco_calculation_service import TCOCalculationService
    
    data_tables = load_data()
    vehicle_repo = repos.VehicleRepository(data_tables)
    params_repo = repos.ParametersRepository(data_tables)
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
