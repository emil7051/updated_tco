"""
TCO Model for Battery Electric vs. Diesel Trucks in Australia
This Streamlit application provides a comprehensive Total Cost of Ownership (TCO)
comparison between battery electric and diesel trucks in the Australian context.

Author: Data Engineering Team
Date: April 2025
"""

import streamlit as st
import pandas as pd
import os
import base64
# Remove the import for streamlit-tailwind since we're not using it
# from streamlit_tailwind import st_tw

# Import modules
from src.data_loading import load_data
from src.calculations import (
    calculate_energy_costs, calculate_annual_costs, calculate_emissions,
    calculate_acquisition_cost, calculate_npv, calculate_residual_value,
    calculate_battery_replacement, calculate_tco, calculate_externalities,
    calculate_social_tco, calculate_comparative_metrics,
    calculate_infrastructure_costs, calculate_charging_requirements,
    apply_infrastructure_incentives, integrate_infrastructure_with_tco,
    perform_sensitivity_analysis, calculate_tornado_data
)
from src.visualization import (
    create_cost_breakdown_chart, create_annual_costs_chart,
    create_emissions_chart,
    create_charging_mix_chart,
    create_sensitivity_chart, create_tornado_chart
)
from src.ui_components import (
    display_metric_card, display_comparison_metrics,
    display_summary_metrics, display_detailed_results_table
)

# Set page configuration
st.set_page_config(
    page_title="Electric vs. Diesel Truck TCO Model",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load and apply CSS
with open(os.path.join(os.path.dirname(__file__), "assets", "styles.css")) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def apply_scenario_parameters(scenario_id, data_tables, vehicle_type, drivetrain):
    """
    Apply all scenario-specific parameters to the appropriate data tables
    
    Args:
        scenario_id: The ID of the selected scenario
        data_tables: Dictionary containing all data tables
        vehicle_type: Selected vehicle type (or 'All')
        drivetrain: Selected drivetrain type (or 'All')
        
    Returns:
        Dictionary of modified data tables with scenario parameters applied
    """
    # Create copies of the tables that might be modified
    modified_tables = {
        'financial_params': data_tables['financial_params'].copy(),
        'battery_params': data_tables['battery_params'].copy(),
        'vehicle_models': data_tables['vehicle_models'].copy(),
        'incentives': data_tables['incentives'].copy()
    }
    
    # Get scenario parameters for the selected scenario
    scenario_params = data_tables['scenario_params']
    selected_params = scenario_params[scenario_params['scenario_id'] == scenario_id]
    
    if selected_params.empty:
        return modified_tables
    
    # Apply each parameter based on table and parameter name
    for _, param in selected_params.iterrows():
        param_table = param['parameter_table']
        param_name = param['parameter_name']
        param_value = param['parameter_value']
        param_vehicle_type = param['vehicle_type']
        param_drivetrain = param['vehicle_drivetrain']
        
        # Skip if parameter doesn't apply to selected vehicle type or drivetrain
        if (param_vehicle_type != 'All' and param_vehicle_type != vehicle_type) or \
           (param_drivetrain != 'All' and param_drivetrain != drivetrain):
            continue
        
        # Apply parameter based on which table it belongs to
        if param_table == 'financial_params':
            # Handle financial parameters
            modified_tables['financial_params'].loc[
                modified_tables['financial_params']['finance_description'] == param_name,
                'default_value'
            ] = param_value
            
            # Special handling for diesel_default_price to map to diesel_price
            if param_name == 'diesel_default_price':
                modified_tables['financial_params'].loc[
                    modified_tables['financial_params']['finance_description'] == 'diesel_price',
                    'default_value'
                ] = param_value
            
        elif param_table == 'battery_params':
            # Handle battery parameters
            modified_tables['battery_params'].loc[
                modified_tables['battery_params']['battery_description'] == param_name,
                'default_value'
            ] = param_value
            
        elif param_table == 'vehicle_models':
            # Handle vehicle model modifiers
            if param_name == 'msrp_price_modifier':
                # Apply price modifier to all relevant vehicles
                mask = (modified_tables['vehicle_models']['vehicle_drivetrain'] == param_drivetrain)
                if param_vehicle_type != 'All':
                    mask &= (modified_tables['vehicle_models']['vehicle_type'] == param_vehicle_type)
                
                for idx, row in modified_tables['vehicle_models'][mask].iterrows():
                    orig_price = row['msrp_price']
                    modified_tables['vehicle_models'].at[idx, 'msrp_price'] = orig_price * param_value
            
            elif param_name == 'kwh_per100km_modifier':
                # Apply energy efficiency modifier
                mask = (modified_tables['vehicle_models']['vehicle_drivetrain'] == param_drivetrain)
                if param_vehicle_type != 'All':
                    mask &= (modified_tables['vehicle_models']['vehicle_type'] == param_vehicle_type)
                
                for idx, row in modified_tables['vehicle_models'][mask].iterrows():
                    orig_efficiency = row['kwh_per100km']
                    modified_tables['vehicle_models'].at[idx, 'kwh_per100km'] = orig_efficiency * param_value
            
            elif param_name == 'range_km_modifier':
                # Apply range modifier
                mask = (modified_tables['vehicle_models']['vehicle_drivetrain'] == param_drivetrain)
                if param_vehicle_type != 'All':
                    mask &= (modified_tables['vehicle_models']['vehicle_type'] == param_vehicle_type)
                
                for idx, row in modified_tables['vehicle_models'][mask].iterrows():
                    orig_range = row['range_km']
                    modified_tables['vehicle_models'].at[idx, 'range_km'] = orig_range * param_value
        
        elif param_table == 'incentives':
            # Handle incentive parameters - parse the param_name which may contain multiple parts
            if '.' in param_name:
                incentive_type, incentive_field = param_name.split('.')
                
                # Find the matching incentive row
                mask = (modified_tables['incentives']['incentive_type'] == incentive_type)
                if param_vehicle_type != 'All':
                    mask &= (modified_tables['incentives']['vehicle_type'] == param_vehicle_type)
                if param_drivetrain != 'All':
                    mask &= (modified_tables['incentives']['drivetrain'] == param_drivetrain)
                
                # Update the incentive
                if not modified_tables['incentives'][mask].empty:
                    for idx in modified_tables['incentives'][mask].index:
                        modified_tables['incentives'].at[idx, incentive_field] = param_value
                else:
                    # If no matching row found, log it for debugging
                    print(f"Warning: No matching incentive found for {incentive_type} with vehicle_type={param_vehicle_type}, drivetrain={param_drivetrain}")
            else:
                print(f"Warning: Invalid incentive parameter format: {param_name}")
    
    return modified_tables

def display_scenario_parameters(scenario_id, scenario_params, scenario_name):
    """
    Display the parameters that are being modified in the current scenario
    
    Args:
        scenario_id: The ID of the selected scenario
        scenario_params: The scenario_params DataFrame
        scenario_name: The name of the scenario for display
    """
    # Filter for parameters in the selected scenario
    selected_params = scenario_params[scenario_params['scenario_id'] == scenario_id]
    
    if selected_params.empty or scenario_id == 'S000':  # Base case has no modifications
        st.caption("Base scenario with default parameters")
        return
    
    # Group parameters by table
    param_groups = {}
    for _, param in selected_params.iterrows():
        table = param['parameter_table']
        if table not in param_groups:
            param_groups[table] = []
        
        # Format the parameter for display
        param_info = {
            'name': param['parameter_name'],
            'value': param['parameter_value'],
            'vehicle_type': param['vehicle_type'],
            'drivetrain': param['vehicle_drivetrain']
        }
        param_groups[table].append(param_info)
    
    # Display the parameters
    with st.expander(f"Scenario Parameters for {scenario_name}"):
        for table, params in param_groups.items():
            st.markdown(f"**{table.replace('_', ' ').title()}**")
            
            for param in params:
                # Format the display based on parameter type
                if '.' in param['name']:
                    # For incentives with dot notation
                    incentive_type, field = param['name'].split('.')
                    if field == 'incentive_flag' and param['value'] == 1.0:
                        st.markdown(f"- Enable {incentive_type} for {param['drivetrain']} {param['vehicle_type']}")
                    elif field == 'incentive_rate':
                        st.markdown(f"- {incentive_type} rate: {param['value']} for {param['drivetrain']} {param['vehicle_type']}")
                elif table == 'financial_params':
                    if param['name'] == 'diesel_default_price':
                        st.markdown(f"- Diesel price: ${param['value']:.2f}/L")
                    elif param['name'] == 'carbon_price':
                        st.markdown(f"- Carbon price: ${param['value']:.0f}/tonne CO₂")
                    else:
                        st.markdown(f"- {param['name']}: {param['value']}")
                elif table == 'vehicle_models':
                    if param['name'] == 'msrp_price_modifier':
                        percent = (param['value'] - 1) * 100
                        direction = "increase" if percent > 0 else "decrease"
                        st.markdown(f"- Vehicle price: {abs(percent):.0f}% {direction} for {param['drivetrain']} {param['vehicle_type']}")
                    elif param['name'] == 'kwh_per100km_modifier':
                        percent = (1 - param['value']) * 100
                        st.markdown(f"- Energy efficiency: {percent:.0f}% improvement for {param['drivetrain']} {param['vehicle_type']}")
                    elif param['name'] == 'range_km_modifier':
                        percent = (param['value'] - 1) * 100
                        st.markdown(f"- Range: {percent:.0f}% increase for {param['drivetrain']} {param['vehicle_type']}")
                elif table == 'battery_params':
                    if param['name'] == 'replacement_per_kwh_price':
                        st.markdown(f"- Battery replacement cost: ${param['value']:.0f}/kWh")
                    elif param['name'] == 'degradation_annual_percent':
                        st.markdown(f"- Battery degradation: {param['value']*100:.1f}% per year")
                else:
                    st.markdown(f"- {param['name']}: {param['value']}")
            
            st.markdown("---")

def main():
    # Load data
    data_tables = load_data()
    
    # Extract tables
    vehicle_models = data_tables['vehicle_models']
    vehicle_fees = data_tables['vehicle_fees']
    charging_options = data_tables['charging_options']
    infrastructure_options = data_tables['infrastructure_options']
    operating_params = data_tables['operating_params']
    financial_params = data_tables['financial_params']
    battery_params = data_tables['battery_params']
    emission_factors = data_tables['emission_factors']
    externalities = data_tables['externalities']
    incentives = data_tables['incentives']
    scenarios = data_tables['scenarios']
    scenario_params = data_tables['scenario_params']
    
    # Application title
    st.title("Total Cost of Ownership: Electric vs. Diesel Trucks")
    st.markdown("Compare the economics of battery electric and diesel trucks in Australia")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        
        # Scenario selection
        st.subheader("Scenario")
        scenario_id = st.selectbox(
            "Select Scenario",
            options=scenarios['scenario_id'].tolist(),
            format_func=lambda x: f"{scenarios[scenarios['scenario_id'] == x].iloc[0]['scenario_name']}",
            index=0
        )
        
        # Display scenario description
        scenario_desc = scenarios[scenarios['scenario_id'] == scenario_id].iloc[0]['scenario_description']
        st.markdown(f"*{scenario_desc}*")
        
        # Display scenario parameters
        scenario_name = scenarios[scenarios['scenario_id'] == scenario_id].iloc[0]['scenario_name']
        display_scenario_parameters(scenario_id, scenario_params, scenario_name)
        
        # Vehicle selection
        st.subheader("Vehicle Selection")
        vehicle_type = st.selectbox(
            "Vehicle Type",
            options=["Light Rigid", "Medium Rigid", "Articulated"],
            index=0
        )
        
        # Filter vehicle models by type
        type_vehicles = vehicle_models[vehicle_models['vehicle_type'] == vehicle_type]
        
        # Get BEV vehicles
        bev_vehicles = type_vehicles[type_vehicles['vehicle_drivetrain'] == 'BEV']
        
        # Vehicle pair selection
        selected_bev_id = st.selectbox(
            "Select BEV Model",
            options=bev_vehicles['vehicle_id'].tolist(),
            format_func=lambda x: f"{vehicle_models[vehicle_models['vehicle_id'] == x].iloc[0]['vehicle_model']}",
            index=0
        )
        
        # Get the comparison diesel vehicle
        selected_bev = vehicle_models[vehicle_models['vehicle_id'] == selected_bev_id].iloc[0]
        comparison_diesel_id = selected_bev['comparison_pair_id']
        
        # Display selected diesel model
        diesel_model = vehicle_models[vehicle_models['vehicle_id'] == comparison_diesel_id].iloc[0]['vehicle_model']
        st.info(f"Comparison Diesel: {diesel_model}")
        
        # Apply scenario parameters to relevant tables
        modified_tables = apply_scenario_parameters(scenario_id, data_tables, vehicle_type, 'All')
        
        # Update the data tables with scenario-specific values
        financial_params = modified_tables['financial_params']
        battery_params = modified_tables['battery_params']
        vehicle_models_updated = modified_tables['vehicle_models']
        incentives = modified_tables['incentives']
        
        # Update vehicle data with scenario-specific modifications
        bev_vehicle_data = vehicle_models_updated[vehicle_models_updated['vehicle_id'] == selected_bev_id].iloc[0]
        diesel_vehicle_data = vehicle_models_updated[vehicle_models_updated['vehicle_id'] == comparison_diesel_id].iloc[0]
        
        # Show vehicle model changes due to scenario if applicable
        bev_original = vehicle_models[vehicle_models['vehicle_id'] == selected_bev_id].iloc[0]
        
        # Check for price changes
        if bev_original['msrp_price'] != bev_vehicle_data['msrp_price']:
            price_diff_pct = ((bev_vehicle_data['msrp_price'] / bev_original['msrp_price']) - 1) * 100
            direction = "increased" if price_diff_pct > 0 else "reduced"
            st.caption(f"BEV price {direction} by {abs(price_diff_pct):.1f}% in this scenario")
        
        # Check for efficiency changes
        if bev_original['kwh_per100km'] != bev_vehicle_data['kwh_per100km']:
            efficiency_diff_pct = ((1 - bev_vehicle_data['kwh_per100km'] / bev_original['kwh_per100km'])) * 100
            st.caption(f"BEV efficiency improved by {efficiency_diff_pct:.1f}% in this scenario")
        
        # Check for range changes
        if bev_original['range_km'] != bev_vehicle_data['range_km']:
            range_diff_pct = ((bev_vehicle_data['range_km'] / bev_original['range_km']) - 1) * 100
            st.caption(f"BEV range increased by {range_diff_pct:.1f}% in this scenario")
        
        # Operating parameters
        st.subheader("Operating Parameters")
        
        # Get default operating parameters for this vehicle type
        default_params = operating_params[operating_params['vehicle_type'] == vehicle_type].iloc[0]
        
        annual_kms = st.number_input(
            "Annual Distance (km)",
            min_value=1000,
            max_value=200000,
            value=int(default_params['annual_kms']),
            step=1000
        )
        
        truck_life_years = st.number_input(
            "Vehicle Lifetime (years)",
            min_value=1,
            max_value=30,
            value=int(default_params['truck_life_years']),
            step=1
        )
        
        # Financial parameters
        st.subheader("Financial Parameters")
        
        # Get default discount rate
        default_discount = financial_params[financial_params['finance_description'] == 'discount_rate_percent'].iloc[0]['default_value']
        
        discount_rate = st.slider(
            "Discount Rate (%)",
            min_value=0.0,
            max_value=15.0,
            value=float(default_discount * 100),
            step=0.5
        ) / 100
        
        # Get default diesel price from financial params (already updated with scenario values)
        default_diesel_price = financial_params[
            financial_params['finance_description'] == 'diesel_price'
        ].iloc[0]['default_value']
        
        diesel_price = st.number_input(
            "Diesel Price (AUD/L)",
            min_value=0.5,
            max_value=10.0,
            value=float(default_diesel_price),
            step=0.05
        )
        
        # Charging options
        st.subheader("Charging Options")
        
        # Add toggle for mixed charging vs single charging option
        charging_approach = st.radio(
            "Charging Approach",
            ["Single Charging Option", "Mixed Charging (Time-of-Use)"],
            index=0,
            help="Choose a single charging option or create a mix of charging options to model time-of-use pricing"
        )
        
        if charging_approach == "Single Charging Option":
            # Single charging option selection
            selected_charging = st.selectbox(
                "Primary Charging Approach",
                options=charging_options['charging_id'].tolist(),
                format_func=lambda x: f"{charging_options[charging_options['charging_id'] == x].iloc[0]['charging_approach']} (${charging_options[charging_options['charging_id'] == x].iloc[0]['per_kwh_price']:.2f}/kWh)",
                index=1  # Default to off-peak charging
            )
            
            # Set charging_mix to None for single option
            use_charging_mix = False
            charging_percentages = None
            
        else:
            # Mixed charging options
            use_charging_mix = True
            charging_percentages = {}
            
            st.markdown("Allocate percentage of charging per option (total must equal 100%):")
            
            # Create columns for a more compact UI
            col_labels = st.columns([3, 1, 1])
            col_labels[0].markdown("**Charging Option**")
            col_labels[1].markdown("**Price/kWh**")
            col_labels[2].markdown("**Percentage**")
            
            # Track total percentage
            total_percentage = 0
            
            # Calculate default even distribution
            default_percentage = 100 / len(charging_options)
            
            # Show options with sliders
            for idx, charging_option in charging_options.iterrows():
                charging_id = charging_option['charging_id']
                charging_name = charging_option['charging_approach']
                charging_price = charging_option['per_kwh_price']
                
                cols = st.columns([3, 1, 2])
                cols[0].text(charging_name)
                cols[1].text(f"${charging_price:.2f}")
                
                percentage = cols[2].slider(
                    f"##",
                    min_value=0,
                    max_value=100,
                    value=int(default_percentage),
                    step=5,
                    key=f"charging_mix_{charging_id}",
                    label_visibility="collapsed"
                )
                
                charging_percentages[charging_id] = percentage / 100
                total_percentage += percentage
            
            # Display weighted average price
            weighted_price = 0
            if total_percentage > 0:  # Prevent division by zero
                for charging_id, percentage in charging_percentages.items():
                    charging_option = charging_options[charging_options['charging_id'] == charging_id].iloc[0]
                    weighted_price += charging_option['per_kwh_price'] * (percentage / total_percentage * 100)
            
            # Display total and validation
            st.metric(
                "Weighted Average Price", 
                f"${weighted_price:.2f}/kWh",
                delta=f"Total: {total_percentage}%"
            )
            
            # Validate total equals 100%
            if total_percentage != 100:
                st.warning(f"Total allocation must equal 100%. Current: {total_percentage}%")
                
            # Set a default selected charging ID for the calculation function when not using it
            selected_charging = charging_options['charging_id'].iloc[0]

        # Infrastructure options
        st.subheader("Infrastructure Options")
        
        selected_infrastructure = st.selectbox(
            "Charging Infrastructure",
            options=infrastructure_options['infrastructure_id'].tolist(),
            format_func=lambda x: f"{infrastructure_options[infrastructure_options['infrastructure_id'] == x].iloc[0]['infrastructure_description']} (${infrastructure_options[infrastructure_options['infrastructure_id'] == x].iloc[0]['infrastructure_price']:,.0f})",
            index=0  # Default to No Infrastructure
        )
        
        # Fleet size for infrastructure cost sharing
        fleet_size = st.number_input(
            "Number of Vehicles Sharing Infrastructure",
            min_value=1,
            max_value=100,
            value=1,
            step=1,
            help="Multiple vehicles can share charging infrastructure, reducing per-vehicle costs"
        )
        
        # Incentives
        st.subheader("Incentives")
        
        # Get all applicable incentives without filtering by incentive_flag
        applicable_incentives = incentives.copy()
        applicable_incentives = applicable_incentives[
            (applicable_incentives['vehicle_type'] == 'All') | (applicable_incentives['vehicle_type'] == vehicle_type)
        ]
        applicable_incentives = applicable_incentives[
            (applicable_incentives['drivetrain'] == 'All') | (applicable_incentives['drivetrain'] == 'BEV')
        ]
        
        # Create a dictionary to store individual incentive toggle states
        incentive_toggles = {}
        
        # Display toggles for all applicable incentives
        if not applicable_incentives.empty:
            # Create a DataFrame to store active incentives for calculations
            applied_incentives = incentives.copy()
            # Initially set all incentive flags to 0
            applied_incentives['incentive_flag'] = 0
            
            # Create toggles for each incentive
            for _, row in applicable_incentives.iterrows():
                incentive_type = row['incentive_type']
                # Format incentive name for display
                display_name = ' '.join(word.capitalize() for word in incentive_type.split('_'))
                
                # Add some specific details based on incentive type
                incentive_details = ""
                if incentive_type == 'purchase_rebate_aud':
                    incentive_details = f" (${row['incentive_rate']:,.0f})"
                elif 'exemption' in incentive_type or 'discount' in incentive_type:
                    incentive_details = f" ({row['incentive_rate']*100:.0f}%)"
                elif incentive_type == 'charging_infrastructure_subsidy':
                    incentive_details = f" ({row['incentive_rate']*100:.0f}%)"
                
                toggle_label = f"{display_name}{incentive_details}"
                
                # Set default state based on incentive_flag in the current scenario
                default_state = row['incentive_flag'] == 1
                
                # Create toggle and store state
                incentive_toggles[incentive_type] = st.checkbox(toggle_label, value=default_state)
                
                # Update the incentives DataFrame based on toggle state
                if incentive_toggles[incentive_type]:
                    applied_incentives.loc[applied_incentives['incentive_type'] == incentive_type, 'incentive_flag'] = 1
            
            # Use the customized incentives DataFrame for calculations
            apply_incentives = True
            # Replace the original incentives with our toggle-controlled version
            incentives = applied_incentives
        else:
            st.info("No applicable incentives available for this vehicle type.")
            apply_incentives = False
        
        # Battery parameters
        st.subheader("Battery Parameters")
        
        default_degradation = battery_params[
            battery_params['battery_description'] == 'degradation_annual_percent'
        ].iloc[0]['default_value']
        
        degradation_rate = st.slider(
            "Annual Battery Degradation (%)",
            min_value=0.0,
            max_value=10.0,
            value=float(default_degradation * 100),
            step=0.1
        ) / 100
        
        default_replacement = battery_params[
            battery_params['battery_description'] == 'replacement_per_kwh_price'
        ].iloc[0]['default_value']
        
        replacement_cost = st.number_input(
            "Battery Replacement Cost ($/kWh)",
            min_value=50,
            max_value=500,
            value=int(default_replacement),
            step=10
        )
        
        # Carbon price
        st.subheader("Carbon Price")
        
        # Get carbon price from financial params (already updated with scenario values)
        default_carbon_price = financial_params[
            financial_params['finance_description'] == 'carbon_price'
        ].iloc[0]['default_value']
        
        carbon_price = st.number_input(
            "Carbon Price ($/tonne CO₂)",
            min_value=0,
            max_value=500,
            value=int(default_carbon_price),
            step=5
        )
    
    # Main content area - Run calculations and display results
    # Get selected vehicle data (updated with scenario modifications)
    bev_vehicle_data = vehicle_models_updated[vehicle_models_updated['vehicle_id'] == selected_bev_id].iloc[0]
    diesel_vehicle_data = vehicle_models_updated[vehicle_models_updated['vehicle_id'] == comparison_diesel_id].iloc[0]
    
    # Get associated fees
    bev_fees = vehicle_fees[vehicle_fees['vehicle_id'] == selected_bev_id]
    diesel_fees = vehicle_fees[vehicle_fees['vehicle_id'] == comparison_diesel_id]
    
    # Battery parameters based on UI inputs (scenario parameters applied first, then UI inputs)
    battery_params_with_ui = battery_params.copy()
    battery_params_with_ui.loc[
        battery_params_with_ui['battery_description'] == 'degradation_annual_percent', 'default_value'
    ] = degradation_rate
    
    battery_params_with_ui.loc[
        battery_params_with_ui['battery_description'] == 'replacement_per_kwh_price', 'default_value'
    ] = replacement_cost
    
    # Financial parameters with UI inputs (scenario parameters applied first, then UI inputs)
    financial_params_with_ui = financial_params.copy()
    financial_params_with_ui.loc[
        financial_params_with_ui['finance_description'] == 'diesel_price', 'default_value'
    ] = diesel_price
    
    financial_params_with_ui.loc[
        financial_params_with_ui['finance_description'] == 'carbon_price', 'default_value'
    ] = carbon_price
    
    # Calculate energy costs
    if use_charging_mix and total_percentage == 100:
        # Only use charging mix if percentages sum to 100%
        charging_mix = charging_percentages
    else:
        charging_mix = None
        
    bev_energy_cost_per_km = calculate_energy_costs(
        bev_vehicle_data,
        bev_fees,
        charging_options,
        financial_params_with_ui,
        selected_charging,
        charging_mix
    )
    
    diesel_energy_cost_per_km = calculate_energy_costs(
        diesel_vehicle_data,
        diesel_fees,
        charging_options,
        financial_params_with_ui,
        selected_charging
    )
    
    # Display charging option information in a smaller info box
    charging_info = f"Using single charging option: {charging_options[charging_options['charging_id'] == selected_charging].iloc[0]['charging_approach']} (${charging_options[charging_options['charging_id'] == selected_charging].iloc[0]['per_kwh_price']:.2f}/kWh)"
    if use_charging_mix and charging_mix is not None:
        # Calculate weighted average electricity price for display
        weighted_price = 0
        for charging_id, percentage in charging_mix.items():
            charging_option = charging_options[charging_options['charging_id'] == charging_id].iloc[0]
            weighted_price += charging_option['per_kwh_price'] * percentage
        
        charging_info = f"Using mixed charging with weighted average price: ${weighted_price:.2f}/kWh"
    
    # Calculate annual costs
    bev_annual_costs = calculate_annual_costs(
        bev_vehicle_data,
        bev_fees,
        bev_energy_cost_per_km,
        annual_kms,
        incentives,
        apply_incentives
    )
    
    diesel_annual_costs = calculate_annual_costs(
        diesel_vehicle_data,
        diesel_fees,
        diesel_energy_cost_per_km,
        annual_kms,
        incentives,
        apply_incentives
    )
    
    # Calculate emissions
    bev_emissions = calculate_emissions(
        bev_vehicle_data,
        emission_factors,
        annual_kms,
        truck_life_years
    )
    
    diesel_emissions = calculate_emissions(
        diesel_vehicle_data,
        emission_factors,
        annual_kms,
        truck_life_years
    )
    
    # Calculate acquisition costs
    bev_acquisition = calculate_acquisition_cost(
        bev_vehicle_data,
        bev_fees,
        incentives,
        apply_incentives
    )
    
    diesel_acquisition = calculate_acquisition_cost(
        diesel_vehicle_data,
        diesel_fees,
        incentives,
        apply_incentives
    )
    
    # Calculate residual values
    initial_depreciation = financial_params[
        financial_params['finance_description'] == 'initial_depreciation_percent'
    ].iloc[0]['default_value']
    
    annual_depreciation = financial_params[
        financial_params['finance_description'] == 'annual_depreciation_percent'
    ].iloc[0]['default_value']
    
    bev_residual = calculate_residual_value(
        bev_vehicle_data,
        truck_life_years,
        initial_depreciation,
        annual_depreciation
    )
    
    diesel_residual = calculate_residual_value(
        diesel_vehicle_data,
        truck_life_years,
        initial_depreciation,
        annual_depreciation
    )
    
    # Calculate battery replacement
    bev_battery_replacement = calculate_battery_replacement(
        bev_vehicle_data,
        battery_params_with_ui,
        truck_life_years,
        discount_rate
    )
    
    # Calculate NPV of annual costs
    bev_npv_annual = calculate_npv(
        bev_annual_costs['annual_operating_cost'],
        discount_rate,
        truck_life_years
    )
    
    diesel_npv_annual = calculate_npv(
        diesel_annual_costs['annual_operating_cost'],
        discount_rate,
        truck_life_years
    )
    
    # Calculate TCO metrics
    bev_tco = calculate_tco(
        bev_vehicle_data,
        bev_fees,
        bev_annual_costs,
        bev_acquisition,
        bev_residual,
        bev_battery_replacement,
        bev_npv_annual,
        annual_kms,
        truck_life_years
    )
    
    diesel_tco = calculate_tco(
        diesel_vehicle_data,
        diesel_fees,
        diesel_annual_costs,
        diesel_acquisition,
        diesel_residual,
        0,  # No battery replacement for diesel
        diesel_npv_annual,
        annual_kms,
        truck_life_years
    )
    
    # Calculate externalities
    bev_externalities = calculate_externalities(
        bev_vehicle_data,
        externalities,
        annual_kms,
        truck_life_years,
        discount_rate
    )
    
    diesel_externalities = calculate_externalities(
        diesel_vehicle_data,
        externalities,
        annual_kms,
        truck_life_years,
        discount_rate
    )
    
    # Calculate social TCO
    bev_social_tco = calculate_social_tco(bev_tco, bev_externalities)
    diesel_social_tco = calculate_social_tco(diesel_tco, diesel_externalities)
    
    # After all other calculations but before comparison metrics, add infrastructure calculations
    # Get selected infrastructure option
    selected_infrastructure_data = infrastructure_options[
        infrastructure_options['infrastructure_id'] == selected_infrastructure
    ].iloc[0]
    
    # Calculate charging requirements
    bev_charging_requirements = calculate_charging_requirements(
        bev_vehicle_data,
        annual_kms,
        selected_infrastructure_data
    )
    
    # Calculate infrastructure costs
    infrastructure_costs = calculate_infrastructure_costs(
        selected_infrastructure_data,
        truck_life_years,
        discount_rate,
        fleet_size
    )
    
    # Apply infrastructure incentives if applicable
    infrastructure_costs_with_incentives = apply_infrastructure_incentives(
        infrastructure_costs,
        incentives,
        apply_incentives
    )
    
    # Update fleet size in the infrastructure costs for reference
    infrastructure_costs_with_incentives['fleet_size'] = fleet_size
    
    # Integrate infrastructure costs into BEV TCO
    bev_tco_with_infrastructure = integrate_infrastructure_with_tco(
        bev_tco,
        infrastructure_costs_with_incentives,
        apply_incentives
    )
    
    # Update the BEV results with infrastructure costs
    bev_results = {
        'vehicle_data': bev_vehicle_data,
        'fees': bev_fees,  # Store the fees in the results
        'energy_cost_per_km': bev_energy_cost_per_km,
        'annual_costs': bev_annual_costs,
        'emissions': bev_emissions,
        'acquisition_cost': bev_acquisition,
        'residual_value': bev_residual,
        'battery_replacement': bev_battery_replacement,
        'npv_annual_cost': bev_npv_annual,
        'tco': bev_tco_with_infrastructure,  # Use the updated TCO with infrastructure
        'externalities': bev_externalities,
        'social_tco': calculate_social_tco(bev_tco_with_infrastructure, bev_externalities),  # Recalculate with updated TCO
        'annual_kms': annual_kms,
        'truck_life_years': truck_life_years,
        'charging_requirements': bev_charging_requirements,  # Add charging requirements
        'infrastructure_costs': infrastructure_costs_with_incentives,  # Add infrastructure costs
        'selected_infrastructure_description': selected_infrastructure_data['infrastructure_description'],
        'charging_options': charging_options,  # Add charging options data
        'discount_rate': discount_rate,  # Store discount rate for sensitivity analysis
        'scenario': {
            'id': scenario_id,
            'name': scenarios[scenarios['scenario_id'] == scenario_id].iloc[0]['scenario_name'],
            'description': scenarios[scenarios['scenario_id'] == scenario_id].iloc[0]['scenario_description']
        }
    }
    
    # Add charging mix information if using mixed charging
    if use_charging_mix and charging_mix is not None:
        bev_results['charging_mix'] = charging_mix
        
        # Calculate and store weighted average electricity price
        weighted_price = 0
        for charging_id, percentage in charging_mix.items():
            charging_option = charging_options[charging_options['charging_id'] == charging_id].iloc[0]
            weighted_price += charging_option['per_kwh_price'] * percentage
            
        bev_results['weighted_electricity_price'] = weighted_price
    
    # Diesel results (without infrastructure costs)
    diesel_results = {
        'vehicle_data': diesel_vehicle_data,
        'fees': diesel_fees,  # Store the fees in the results
        'energy_cost_per_km': diesel_energy_cost_per_km,
        'annual_costs': diesel_annual_costs,
        'emissions': diesel_emissions,
        'acquisition_cost': diesel_acquisition,
        'residual_value': diesel_residual,
        'battery_replacement': 0,
        'npv_annual_cost': diesel_npv_annual,
        'tco': diesel_tco,
        'externalities': diesel_externalities,
        'social_tco': diesel_social_tco,
        'annual_kms': annual_kms,
        'truck_life_years': truck_life_years,
        'discount_rate': discount_rate,  # Store discount rate for sensitivity analysis
        'scenario': {
            'id': scenario_id,
            'name': scenarios[scenarios['scenario_id'] == scenario_id].iloc[0]['scenario_name'],
            'description': scenarios[scenarios['scenario_id'] == scenario_id].iloc[0]['scenario_description']
        }
    }
    
    # Calculate comparative metrics with the updated BEV results
    comparison_metrics = calculate_comparative_metrics(
        bev_results,
        diesel_results,
        annual_kms,
        truck_life_years
    )
    
    # Add comparison metrics to results
    bev_results['comparison'] = comparison_metrics
    
    # Display the scenario and charging approach used
    scenario_name = scenarios[scenarios['scenario_id'] == scenario_id].iloc[0]['scenario_name']
    st.caption(f"Scenario: {scenario_name} | {charging_info}")
    
    # Main dashboard area - create the layout using containers to avoid white spaces
    main_container = st.container()
    with main_container:
        # First display the summary and comparison metrics on the main page
        display_summary_metrics(bev_results, diesel_results)
        
        # Display lifetime payback comparison on the main page
        display_comparison_metrics(comparison_metrics)
        
        # Remaining details in tabs
        tabs = st.tabs([
            "Cost Breakdown", 
            "Emissions", 
            "Detailed Results", 
            "Sensitivity Analysis"
        ])
        
        # Cost Breakdown tab
        with tabs[0]:
            st.subheader("Lifetime Cost Components")
            cost_breakdown_chart = create_cost_breakdown_chart(bev_results, diesel_results)
            st.plotly_chart(cost_breakdown_chart, use_container_width=True)
            
            # Add charging mix chart if mixed charging is used
            if 'charging_mix' in bev_results:
                st.subheader("Charging Mix")
                charging_mix_chart = create_charging_mix_chart(bev_results)
                st.plotly_chart(charging_mix_chart, use_container_width=True)
            
            # Add infrastructure cost information
            if bev_vehicle_data['vehicle_drivetrain'] == 'BEV':
                st.subheader("Infrastructure Costs")
                
                infra_col1, infra_col2 = st.columns(2)
                
                with infra_col1:
                    st.metric(
                        "Infrastructure Capital Cost", 
                        f"${bev_results['infrastructure_costs']['infrastructure_price']:,.0f}"
                    )
                    st.metric(
                        "Annual Maintenance", 
                        f"${bev_results['infrastructure_costs']['annual_maintenance']:,.0f}/year"
                    )
                    st.metric(
                        "Cost Per Vehicle", 
                        f"${bev_results['infrastructure_costs']['npv_per_vehicle']:,.0f}"
                    )
                
                with infra_col2:
                    st.metric(
                        "Service Life", 
                        f"{bev_results['infrastructure_costs']['service_life_years']} years"
                    )
                    st.metric(
                        "Replacement Cycles", 
                        f"{bev_results['infrastructure_costs']['replacement_cycles']}"
                    )
                    
                    # Show subsidy if applied
                    if 'subsidy_rate' in bev_results['infrastructure_costs'] and bev_results['infrastructure_costs']['subsidy_rate'] > 0:
                        st.metric(
                            "Infrastructure Subsidy", 
                            f"${bev_results['infrastructure_costs']['subsidy_amount']:,.0f}",
                            delta=f"{bev_results['infrastructure_costs']['subsidy_rate'] * 100:.0f}%"
                        )
                
                # Charging requirements metrics
                st.subheader("Charging Requirements")
                charging_col1, charging_col2 = st.columns(2)
                
                with charging_col1:
                    st.metric(
                        "Daily Energy Required", 
                        f"{bev_results['charging_requirements']['daily_kwh_required']:.1f} kWh"
                    )
                    st.metric(
                        "Charging Time Per Day", 
                        f"{bev_results['charging_requirements']['charging_time_per_day']:.2f} hours"
                    )
                
                with charging_col2:
                    st.metric(
                        "Charger Power", 
                        f"{bev_results['charging_requirements']['charger_power']:.0f} kW"
                    )
                    st.metric(
                        "Maximum Vehicles Per Charger", 
                        f"{min(100, bev_results['charging_requirements']['max_vehicles_per_charger']):.1f}"
                    )
            
            st.subheader("Costs Over Time")
            annual_costs_chart = create_annual_costs_chart(bev_results, diesel_results, truck_life_years)
            st.plotly_chart(annual_costs_chart, use_container_width=True)
        
        # Emissions tab
        with tabs[1]:
            emissions_chart = create_emissions_chart(bev_results, diesel_results, truck_life_years)
            st.plotly_chart(emissions_chart, use_container_width=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(
                    "Lifetime Emission Savings", 
                    f"{comparison_metrics['emission_savings_lifetime']/1000:.1f} tonnes CO₂",
                    delta=f"{comparison_metrics['emission_savings_lifetime']/diesel_emissions['lifetime_emissions']*100:.1f}%"
                )
            
            with col2:
                st.metric(
                    "Abatement Cost", 
                    f"${comparison_metrics['abatement_cost']:.2f}/tonne CO₂"
                )
            
            st.subheader("Emissions Context")
            st.markdown("""
            The emissions calculations consider:
            - Tailpipe emissions for diesel vehicles
            - Electricity grid emissions for BEVs
            - Australian average grid intensity 
            
            Potential future improvements:
            - Accounting for emissions from vehicle manufacturing
            - Customized electricity emission factors based on location or green power options
            - Lifecycle emissions including battery production
            """)
        
        # Detailed Results tab
        with tabs[2]:
            display_detailed_results_table(bev_results, diesel_results)
        
        # Sensitivity Analysis tab
        with tabs[3]:
            st.subheader("Sensitivity Analysis")
            st.info("Sensitivity Analysis helps understand how changes in key parameters affect the TCO comparison.")
            
            # Select parameter to analyze
            sensitivity_param = st.selectbox(
                "Select Parameter for Sensitivity Analysis",
                options=[
                    "Annual Distance (km)",
                    "Diesel Price ($/L)",
                    "Electricity Price ($/kWh)",
                    "Vehicle Lifetime (years)",
                    "Discount Rate (%)"
                ]
            )
            
            # Create parameter range based on selection
            param_range = None
            num_points = 11  # Number of points to calculate (odd number to include current value)
            
            if sensitivity_param == "Annual Distance (km)":
                min_val = max(1000, annual_kms * 0.5)
                max_val = annual_kms * 1.5
                step = (max_val - min_val) / (num_points - 1)
                param_range = [round(min_val + i * step) for i in range(num_points)]
                # Ensure current value is in the range
                if annual_kms not in param_range:
                    param_range.append(annual_kms)
                    param_range.sort()
            
            elif sensitivity_param == "Diesel Price ($/L)":
                diesel_base = diesel_price
                min_val = max(0.5, diesel_base * 0.7)
                max_val = diesel_base * 1.3
                step = (max_val - min_val) / (num_points - 1)
                param_range = [round(min_val + i * step, 2) for i in range(num_points)]
                # Ensure current value is in the range
                if diesel_base not in param_range:
                    param_range.append(diesel_base)
                    param_range.sort()
            
            elif sensitivity_param == "Electricity Price ($/kWh)":
                # Get base electricity price
                if 'weighted_electricity_price' in bev_results:
                    electricity_base = bev_results['weighted_electricity_price']
                else:
                    electricity_base = charging_options[charging_options['charging_id'] == selected_charging].iloc[0]['per_kwh_price']
                
                min_val = max(0.05, electricity_base * 0.7)
                max_val = electricity_base * 1.3
                step = (max_val - min_val) / (num_points - 1)
                param_range = [round(min_val + i * step, 2) for i in range(num_points)]
                # Ensure current value is in the range
                if electricity_base not in param_range:
                    param_range.append(electricity_base)
                    param_range.sort()
            
            elif sensitivity_param == "Vehicle Lifetime (years)":
                min_val = max(1, truck_life_years - 3)
                max_val = truck_life_years + 3
                param_range = list(range(int(min_val), int(max_val + 1)))
                # Ensure current value is in the range
                if truck_life_years not in param_range:
                    param_range.append(truck_life_years)
                    param_range.sort()
            
            elif sensitivity_param == "Discount Rate (%)":
                discount_base = discount_rate * 100  # Convert to percentage
                min_val = max(0.5, discount_base - 3)
                max_val = min(15, discount_base + 3)
                step = (max_val - min_val) / (num_points - 1)
                param_range = [round(min_val + i * step, 1) for i in range(num_points)]
                # Ensure current value is in the range
                if discount_base not in param_range:
                    param_range.append(discount_base)
                    param_range.sort()
            
            # Run sensitivity analysis
            with st.spinner(f"Calculating sensitivity for {sensitivity_param}..."):
                sensitivity_results = perform_sensitivity_analysis(
                    sensitivity_param,
                    param_range,
                    bev_vehicle_data,
                    diesel_vehicle_data,
                    bev_fees,
                    diesel_fees,
                    charging_options,
                    infrastructure_options,
                    financial_params_with_ui,
                    battery_params_with_ui,
                    emission_factors,
                    incentives,
                    selected_charging,
                    selected_infrastructure,
                    annual_kms,
                    truck_life_years,
                    discount_rate,
                    fleet_size,
                    charging_mix if use_charging_mix else None,
                    apply_incentives
                )
            
            # Create sensitivity chart
            sensitivity_chart = create_sensitivity_chart(
                bev_results,
                diesel_results,
                sensitivity_param,
                param_range,
                sensitivity_results
            )
            
            # Display sensitivity chart
            st.plotly_chart(sensitivity_chart, use_container_width=True)
            
            # Find break-even point
            break_even_value = None
            for i in range(len(sensitivity_results) - 1):
                bev_tco1 = sensitivity_results[i]['bev']['tco_per_km']
                diesel_tco1 = sensitivity_results[i]['diesel']['tco_per_km']
                bev_tco2 = sensitivity_results[i+1]['bev']['tco_per_km']
                diesel_tco2 = sensitivity_results[i+1]['diesel']['tco_per_km']
                
                # Check if the TCO difference changes sign (crosses 0)
                if (bev_tco1 - diesel_tco1) * (bev_tco2 - diesel_tco2) <= 0:
                    # Simple linear interpolation to find the break-even point
                    x1, x2 = param_range[i], param_range[i+1]
                    y1, y2 = bev_tco1 - diesel_tco1, bev_tco2 - diesel_tco2
                    
                    # Avoid division by zero
                    if y1 != y2:
                        break_even_value = x1 - y1 * (x2 - x1) / (y2 - y1)
                        break_even_value = round(break_even_value, 2)
            
            # Display break-even value if found
            st.subheader("Break-even Analysis")
            if break_even_value is not None:
                st.success(f"**Break-even {sensitivity_param}: {break_even_value}**")
                
                # Show contextual information based on parameter
                if sensitivity_param == "Annual Distance (km)":
                    current = annual_kms
                    if break_even_value > current:
                        st.markdown(f"BEV becomes more cost-effective than diesel when annual distance exceeds {break_even_value:,.0f} km (current: {current:,.0f} km).")
                    else:
                        st.markdown(f"BEV is more cost-effective than diesel at the current annual distance of {current:,.0f} km.")
                    
                elif sensitivity_param == "Diesel Price ($/L)":
                    current = diesel_price
                    if break_even_value > current:
                        st.markdown(f"BEV becomes more cost-effective than diesel when diesel price exceeds ${break_even_value:.2f}/L (current: ${current:.2f}/L).")
                    else:
                        st.markdown(f"BEV is more cost-effective than diesel at the current diesel price of ${current:.2f}/L.")
                    
                elif sensitivity_param == "Electricity Price ($/kWh)":
                    if 'weighted_electricity_price' in bev_results:
                        current = bev_results['weighted_electricity_price']
                    else:
                        current = charging_options[charging_options['charging_id'] == selected_charging].iloc[0]['per_kwh_price']
                    
                    if break_even_value < current:
                        st.markdown(f"BEV becomes more cost-effective than diesel when electricity price falls below ${break_even_value:.2f}/kWh (current: ${current:.2f}/kWh).")
                    else:
                        st.markdown(f"BEV is more cost-effective than diesel at the current electricity price of ${current:.2f}/kWh.")
                    
                elif sensitivity_param == "Vehicle Lifetime (years)":
                    current = truck_life_years
                    if break_even_value > current:
                        st.markdown(f"BEV becomes more cost-effective than diesel when vehicle lifetime exceeds {break_even_value:.1f} years (current: {current} years).")
                    else:
                        st.markdown(f"BEV is more cost-effective than diesel at the current vehicle lifetime of {current} years.")
                    
                elif sensitivity_param == "Discount Rate (%)":
                    current = discount_rate * 100
                    if break_even_value < current:
                        st.markdown(f"BEV becomes more cost-effective than diesel when discount rate falls below {break_even_value:.1f}% (current: {current:.1f}%).")
                    else:
                        st.markdown(f"BEV is more cost-effective than diesel at the current discount rate of {current:.1f}%.")
                else:
                    st.info(f"No break-even point found within the analyzed range. BEV is {'more' if bev_results['tco']['tco_per_km'] < diesel_results['tco']['tco_per_km'] else 'less'} cost-effective than diesel across all values tested.")
            
            # What-if scenario analysis
            st.subheader("What-if Break-even Analysis")
            st.markdown("Explore break-even points by adjusting other parameters")
            
            # Create 2 columns for the what-if parameters
            whatif_col1, whatif_col2 = st.columns(2)
            
            with whatif_col1:
                # Parameter 1: Always offer diesel price as it's a common break-even factor
                if sensitivity_param != "Diesel Price ($/L)":
                    whatif_diesel_price = st.slider(
                        "Diesel Price ($/L)",
                        min_value=0.5,
                        max_value=5.0,
                        value=diesel_price,
                        step=0.05
                    )
                else:
                    # If diesel price is the main parameter, offer electricity price instead
                    if 'weighted_electricity_price' in bev_results:
                        electricity_base = bev_results['weighted_electricity_price']
                    else:
                        electricity_base = charging_options[charging_options['charging_id'] == selected_charging].iloc[0]['per_kwh_price']
                    
                    whatif_electricity_price = st.slider(
                        "Electricity Price ($/kWh)",
                        min_value=0.05,
                        max_value=0.50,
                        value=electricity_base,
                        step=0.01
                    )
            
            with whatif_col2:
                # Parameter 2: Annual distance is also a key break-even factor
                if sensitivity_param != "Annual Distance (km)":
                    whatif_annual_kms = st.slider(
                        "Annual Distance (km)",
                        min_value=5000,
                        max_value=100000,
                        value=annual_kms,
                        step=1000
                    )
                else:
                    # If annual distance is the main parameter, offer discount rate instead
                    whatif_discount_rate = st.slider(
                        "Discount Rate (%)",
                        min_value=1.0,
                        max_value=15.0,
                        value=discount_rate * 100,
                        step=0.5
                    ) / 100
            
            # Add button to calculate the break-even for the what-if scenario
            if st.button("Calculate What-if Break-even"):
                with st.spinner("Calculating break-even point..."):
                    whatif_param_range = None
                    
                    # Create modified financial parameters
                    whatif_financial_params = financial_params_with_ui.copy()
                    
                    # Set parameters based on user selections
                    if sensitivity_param != "Diesel Price ($/L)":
                        # Update diesel price in financial params
                        whatif_financial_params.loc[
                            whatif_financial_params['finance_description'] == 'diesel_price', 'default_value'
                        ] = whatif_diesel_price
                    
                    # Define parameter range for the current sensitivity parameter
                    if sensitivity_param == "Annual Distance (km)":
                        min_val = max(1000, whatif_annual_kms * 0.3)
                        max_val = whatif_annual_kms * 2.0
                        step = (max_val - min_val) / (num_points - 1)
                        whatif_param_range = [round(min_val + i * step) for i in range(num_points)]
                        current_value = whatif_annual_kms
                    
                    elif sensitivity_param == "Diesel Price ($/L)":
                        min_val = max(0.5, whatif_diesel_price * 0.5)
                        max_val = whatif_diesel_price * 1.5
                        step = (max_val - min_val) / (num_points - 1)
                        whatif_param_range = [round(min_val + i * step, 2) for i in range(num_points)]
                        current_value = whatif_diesel_price
                    
                    elif sensitivity_param == "Electricity Price ($/kWh)":
                        if 'weighted_electricity_price' in bev_results:
                            electricity_base = bev_results['weighted_electricity_price']
                        else:
                            electricity_base = charging_options[charging_options['charging_id'] == selected_charging].iloc[0]['per_kwh_price']
                        
                        min_val = max(0.05, electricity_base * 0.5)
                        max_val = electricity_base * 1.5
                        step = (max_val - min_val) / (num_points - 1)
                        whatif_param_range = [round(min_val + i * step, 2) for i in range(num_points)]
                        current_value = electricity_base
                    
                    elif sensitivity_param == "Vehicle Lifetime (years)":
                        min_val = max(1, truck_life_years - 3)
                        max_val = truck_life_years + 3
                        step = (max_val - min_val) / (num_points - 1)
                        whatif_param_range = [round(min_val + i * step) for i in range(num_points)]
                        current_value = truck_life_years
                    
                    elif sensitivity_param == "Discount Rate (%)":
                        if 'discount_rate' in bev_results:
                            discount_base = bev_results['discount_rate'] * 100
                        else:
                            discount_base = discount_rate * 100
                        
                        min_val = max(0.5, discount_base - 3)
                        max_val = min(15, discount_base + 3)
                        step = (max_val - min_val) / (num_points - 1)
                        whatif_param_range = [round(min_val + i * step, 1) for i in range(num_points)]
                        current_value = discount_base
                    
                    # Run sensitivity analysis with what-if parameters
                    whatif_annual_distance = whatif_annual_kms if sensitivity_param != "Annual Distance (km)" else annual_kms
                    whatif_discount = whatif_discount_rate if sensitivity_param != "Discount Rate (%)" else discount_rate
                    
                    whatif_sensitivity_results = perform_sensitivity_analysis(
                        sensitivity_param,
                        whatif_param_range,
                        bev_vehicle_data,
                        diesel_vehicle_data,
                        bev_fees,
                        diesel_fees,
                        charging_options,
                        infrastructure_options,
                        whatif_financial_params,
                        battery_params_with_ui,
                        emission_factors,
                        incentives,
                        selected_charging,
                        selected_infrastructure,
                        whatif_annual_distance,
                        truck_life_years,
                        whatif_discount,
                        fleet_size,
                        charging_mix if use_charging_mix else None,
                        apply_incentives
                    )
                    
                    # Create sensitivity chart with what-if results
                    whatif_chart = create_sensitivity_chart(
                        bev_results,
                        diesel_results,
                        sensitivity_param,
                        whatif_param_range,
                        whatif_sensitivity_results
                    )
                    
                    # Display what-if sensitivity chart
                    st.plotly_chart(whatif_chart, use_container_width=True)
                    
                    # Find break-even point with what-if parameters
                    whatif_break_even = None
                    for i in range(len(whatif_sensitivity_results) - 1):
                        bev_tco1 = whatif_sensitivity_results[i]['bev']['tco_per_km']
                        diesel_tco1 = whatif_sensitivity_results[i]['diesel']['tco_per_km']
                        bev_tco2 = whatif_sensitivity_results[i+1]['bev']['tco_per_km']
                        diesel_tco2 = whatif_sensitivity_results[i+1]['diesel']['tco_per_km']
                        
                        # Check if the TCO difference changes sign (crosses 0)
                        if (bev_tco1 - diesel_tco1) * (bev_tco2 - diesel_tco2) <= 0:
                            # Simple linear interpolation to find the break-even point
                            x1, x2 = whatif_param_range[i], whatif_param_range[i+1]
                            y1, y2 = bev_tco1 - diesel_tco1, bev_tco2 - diesel_tco2
                            
                            # Avoid division by zero
                            if y1 != y2:
                                whatif_break_even = x1 - y1 * (x2 - x1) / (y2 - y1)
                                whatif_break_even = round(whatif_break_even, 2)
                    
                    # Display what-if break-even results
                    if whatif_break_even is not None:
                        st.success(f"**What-if Break-even {sensitivity_param}: {whatif_break_even}**")
                        
                        # Show modified parameters
                        whatif_params = []
                        if sensitivity_param != "Diesel Price ($/L)":
                            whatif_params.append(f"Diesel Price: ${whatif_diesel_price:.2f}/L")
                        if sensitivity_param != "Annual Distance (km)" and 'whatif_annual_kms' in locals():
                            whatif_params.append(f"Annual Distance: {whatif_annual_kms:,} km")
                        if sensitivity_param != "Discount Rate (%)" and 'whatif_discount_rate' in locals():
                            whatif_params.append(f"Discount Rate: {whatif_discount_rate*100:.1f}%")
                        if sensitivity_param != "Electricity Price ($/kWh)" and 'whatif_electricity_price' in locals():
                            whatif_params.append(f"Electricity Price: ${whatif_electricity_price:.2f}/kWh")
                        
                        st.markdown(f"Parameters: {', '.join(whatif_params)}")
                    else:
                        st.info(f"No break-even point found with the what-if parameters. BEV is {'more' if whatif_sensitivity_results[0]['bev']['tco_per_km'] < whatif_sensitivity_results[0]['diesel']['tco_per_km'] else 'less'} cost-effective than diesel across all values tested.")
            
            # Multi-parameter sensitivity analysis (Tornado Chart)
            st.subheader("Multi-parameter Sensitivity Analysis")
            
            # Add a button to run the tornado analysis (it's computationally intensive)
            if st.button("Generate Tornado Chart"):
                with st.spinner("Calculating impact of multiple parameters..."):
                    try:
                        # Generate tornado chart
                        tornado_data = calculate_tornado_data(
                            bev_results,
                            diesel_results,
                            financial_params_with_ui,
                            battery_params_with_ui,
                            charging_options,
                            infrastructure_options,
                            emission_factors,
                            incentives,
                            selected_charging,
                            selected_infrastructure,
                            annual_kms,
                            truck_life_years,
                            discount_rate,
                            fleet_size,
                            charging_mix if use_charging_mix else None,
                            apply_incentives
                        )
                        
                        # Create tornado chart
                        tornado_chart = create_tornado_chart(
                            tornado_data["base_tco"],
                            tornado_data["impacts"]
                        )
                        
                        # Display tornado chart
                        st.plotly_chart(tornado_chart, use_container_width=True)
                        
                        # Explanation of tornado chart
                        st.caption("""
                        The tornado chart shows how much each parameter affects the TCO of the BEV when varied from its minimum to maximum value. 
                        Parameters are sorted by their impact, with the most influential at the top.
                        """)
                    except ValueError as ve:
                        if "fees data is required" in str(ve):
                            st.error("Vehicle fees data is missing. This feature requires complete vehicle fee information to function properly.")
                            st.markdown("The tornado chart analysis needs detailed vehicle fee information to calculate accurate sensitivity metrics.")
                        else:
                            st.error(f"Value error: {ve}")
                    except Exception as e:
                        st.error(f"An error occurred while generating the tornado chart: {e}")
                        st.markdown("Try selecting a different scenario or vehicle combination if this error persists.")
            
            # Explain sensitivity analysis 
            with st.expander("About Sensitivity Analysis"):
                st.markdown("""
                ### How to Interpret the Sensitivity Analysis
                
                The sensitivity analysis shows how the Total Cost of Ownership (TCO) changes when a single parameter is varied while keeping all other parameters constant.
                
                - **Lines**: The chart shows the TCO per kilometer for both BEV and diesel trucks as the parameter changes.
                - **Break-even point**: Where the BEV and diesel lines cross - at this point, both vehicles have the same TCO.
                - **Current value**: The currently selected value is marked with a vertical line.
                
                ### Using This for Decision Making
                
                - Identify parameters with the greatest impact on TCO.
                - Understand how sensitive your investment decision is to parameter changes.
                - Evaluate if the break-even point is achievable given your operational constraints.
                - Plan for scenarios where parameters might change (e.g., rising diesel prices).
                """)

# Run the application
if __name__ == "__main__":
    main()
