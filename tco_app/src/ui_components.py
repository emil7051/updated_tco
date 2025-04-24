import streamlit as st
import pandas as pd

def display_metric_card(title, value, unit, tooltip=None):
    """
    Display a metric in a formatted card
    """
    metric_html = f"""
    <div class="metric-card">
        <div style="font-size: 0.8rem; color: #505A64;">{title}</div>
        <div class="metric-value">{value:,.2f} {unit}</div>
    </div>
    """
    
    st.markdown(metric_html, unsafe_allow_html=True)
    if tooltip:
        st.caption(tooltip)

def display_comparison_metrics(comparative_metrics):
    """
    Display the comparative metrics in a formatted way
    """
    st.markdown('<div class="comparison-card">', unsafe_allow_html=True)
    st.subheader("Comparison Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        display_metric_card(
            "Upfront Cost Difference",
            comparative_metrics['upfront_cost_difference'],
            "AUD",
            "Additional upfront cost of BEV compared to diesel"
        )
    
    with col2:
        display_metric_card(
            "Annual Operating Savings",
            comparative_metrics['annual_operating_savings'],
            "AUD/year",
            "Annual operating cost savings with BEV"
        )
    
    with col3:
        display_metric_card(
            "Price Parity Point",
            comparative_metrics['price_parity_year'],
            "years",
            "Time until BEV and diesel costs become equal"
        )
    
    # Payback highlight section
    if comparative_metrics['price_parity_year'] < 100:  # Show if there is a reasonable payback period
        payback_html = f"""
        <div class="payback-highlight">
            <strong style="color: #17a2b8;">Price Parity Analysis:</strong> <span style="color: #333333;">The electric vehicle's higher initial cost 
            (${comparative_metrics['upfront_cost_difference']:,.2f}) is balanced by lower operating costs after {comparative_metrics['price_parity_year']:,.1f} years
            through annual savings of ${comparative_metrics['annual_operating_savings']:,.2f}.</span>
        </div>
        """
        st.markdown(payback_html, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        display_metric_card(
            "Lifetime Emission Savings",
            comparative_metrics['emission_savings_lifetime'] / 1000,
            "tonnes CO₂",
            "Total emissions avoided over vehicle lifetime"
        )
    
    with col2:
        display_metric_card(
            "BEV to Diesel TCO Ratio",
            comparative_metrics['bev_to_diesel_tco_ratio'],
            "",
            "Ratio of BEV TCO to diesel TCO (values < 1 favor BEV)"
        )
    
    with col3:
        display_metric_card(
            "Abatement Cost",
            comparative_metrics['abatement_cost'],
            "$/tonne CO₂",
            "Cost per tonne of CO₂ emissions avoided"
        )
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_summary_metrics(bev_results, diesel_results):
    """
    Display summary metrics for both vehicles
    """
    st.subheader("TCO Summary")
    
    col1, col2 = st.columns(2)
    
    with col1:
        bev_html = f"""
        <div class="vehicle-summary-card bev" style="margin-bottom: 0;">
            <h5 style="color: #0B3954; font-weight: 600; margin-bottom: 1rem;">Battery Electric Vehicle</h5>
            <div style="background-color: rgba(8, 126, 139, 0.1); padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem;">
                <span style="color: #333333; font-weight: 600;">Model:</span> <span style="color: #333333;">{bev_results['vehicle_data']['vehicle_model']}</span>
            </div>
            <div style="background-color: rgba(8, 126, 139, 0.1); padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem;">
                <span style="color: #333333; font-weight: 600;">Payload:</span> <span style="color: #333333;">{bev_results['vehicle_data']['payload_t']} tonnes</span>
            </div>
            <div style="background-color: rgba(8, 126, 139, 0.1); padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem;">
                <span style="color: #333333; font-weight: 600;">Range:</span> <span style="color: #333333;">{bev_results['vehicle_data'].get('range_km', 'N/A')} km</span>
            </div>
            <div style="background-color: rgba(8, 126, 139, 0.1); padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem;">
                <span style="color: #333333; font-weight: 600;">Lifetime TCO:</span> <span style="color: #333333;">${bev_results['tco']['npv_total_cost']:,.2f}</span>
            </div>
            <div style="background-color: rgba(8, 126, 139, 0.1); padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem;">
                <span style="color: #333333; font-weight: 600;">TCO per km:</span> <span style="color: #333333;">${bev_results['tco']['tco_per_km']:,.2f}</span>
            </div>
            <div style="background-color: rgba(8, 126, 139, 0.1); padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem;">
                <span style="color: #333333; font-weight: 600;">TCO per tonne-km:</span> <span style="color: #333333;">${bev_results['tco']['tco_per_tonne_km']:,.2f}</span>
            </div>
            <div style="background-color: rgba(8, 126, 139, 0.1); padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem;">
                <span style="color: #333333; font-weight: 600;">Annual Operating Cost:</span> <span style="color: #333333;">${bev_results['annual_costs']['annual_operating_cost']:,.2f}</span>
            </div>
        </div>
        """
        st.markdown(bev_html, unsafe_allow_html=True)
    
    with col2:
        diesel_html = f"""
        <div class="vehicle-summary-card diesel" style="margin-bottom: 0;">
            <h5 style="color: #0B3954; font-weight: 600; margin-bottom: 1rem;">Diesel Vehicle</h5>
            <div style="background-color: rgba(255, 193, 7, 0.1); padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem;">
                <span style="color: #333333; font-weight: 600;">Model:</span> <span style="color: #333333;">{diesel_results['vehicle_data']['vehicle_model']}</span>
            </div>
            <div style="background-color: rgba(255, 193, 7, 0.1); padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem;">
                <span style="color: #333333; font-weight: 600;">Payload:</span> <span style="color: #333333;">{diesel_results['vehicle_data']['payload_t']} tonnes</span>
            </div>
            <div style="background-color: rgba(255, 193, 7, 0.1); padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem;">
                <span style="color: #333333; font-weight: 600;">Range:</span> <span style="color: #333333;">{diesel_results['vehicle_data'].get('range_km', 'N/A')} km</span>
            </div>
            <div style="background-color: rgba(255, 193, 7, 0.1); padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem;">
                <span style="color: #333333; font-weight: 600;">Lifetime TCO:</span> <span style="color: #333333;">${diesel_results['tco']['npv_total_cost']:,.2f}</span>
            </div>
            <div style="background-color: rgba(255, 193, 7, 0.1); padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem;">
                <span style="color: #333333; font-weight: 600;">TCO per km:</span> <span style="color: #333333;">${diesel_results['tco']['tco_per_km']:,.2f}</span>
            </div>
            <div style="background-color: rgba(255, 193, 7, 0.1); padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem;">
                <span style="color: #333333; font-weight: 600;">TCO per tonne-km:</span> <span style="color: #333333;">${diesel_results['tco']['tco_per_tonne_km']:,.2f}</span>
            </div>
            <div style="background-color: rgba(255, 193, 7, 0.1); padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem;">
                <span style="color: #333333; font-weight: 600;">Annual Operating Cost:</span> <span style="color: #333333;">${diesel_results['annual_costs']['annual_operating_cost']:,.2f}</span>
            </div>
        </div>
        """
        st.markdown(diesel_html, unsafe_allow_html=True)

def display_detailed_results_table(bev_results, diesel_results):
    """
    Display a detailed results table with all metrics
    """
    # Create DataFrame for results with properly formatted strings
    results_data = {
        'Metric': [
            'Vehicle Model',
            'Vehicle Type',
            'Payload (tonnes)',
            'Acquisition Cost ($)',
            'Annual Energy Cost ($)',
            'Annual Maintenance Cost ($)',
            'Annual Operating Cost ($)',
            'Energy Consumption per 100km',
            'CO₂ per km (kg)',
            'Annual Emissions (tonnes CO₂)',
            'Lifetime Emissions (tonnes CO₂)',
            'TCO per km ($)',
            'TCO per tonne-km ($)',
            'Lifetime TCO ($)',
            'Externality Cost per km ($)',
            'Social TCO ($)'
        ],
        'BEV': [
            str(bev_results['vehicle_data']['vehicle_model']),
            str(bev_results['vehicle_data']['vehicle_type']),
            str(bev_results['vehicle_data']['payload_t']),
            f"${bev_results['acquisition_cost']:,.2f}",
            f"${bev_results['annual_costs']['annual_energy_cost']:,.2f}",
            f"${bev_results['annual_costs']['annual_maintenance_cost']:,.2f}",
            f"${bev_results['annual_costs']['annual_operating_cost']:,.2f}",
            f"{bev_results['vehicle_data']['kwh_per100km']} kWh",
            f"{bev_results['emissions']['co2_per_km']:.4f}",
            f"{bev_results['emissions']['annual_emissions'] / 1000:.2f}",
            f"{bev_results['emissions']['lifetime_emissions'] / 1000:.2f}",
            f"${bev_results['tco']['tco_per_km']:.2f}",
            f"${bev_results['tco']['tco_per_tonne_km']:.2f}",
            f"${bev_results['tco']['npv_total_cost']:,.2f}",
            f"${bev_results['externalities']['externality_per_km']:.4f}",
            f"${bev_results['social_tco']:,.2f}"
        ],
        'Diesel': [
            str(diesel_results['vehicle_data']['vehicle_model']),
            str(diesel_results['vehicle_data']['vehicle_type']),
            str(diesel_results['vehicle_data']['payload_t']),
            f"${diesel_results['acquisition_cost']:,.2f}",
            f"${diesel_results['annual_costs']['annual_energy_cost']:,.2f}",
            f"${diesel_results['annual_costs']['annual_maintenance_cost']:,.2f}",
            f"${diesel_results['annual_costs']['annual_operating_cost']:,.2f}",
            f"{diesel_results['vehicle_data']['litres_per100km']} L",
            f"{diesel_results['emissions']['co2_per_km']:.4f}",
            f"{diesel_results['emissions']['annual_emissions'] / 1000:.2f}",
            f"{diesel_results['emissions']['lifetime_emissions'] / 1000:.2f}",
            f"${diesel_results['tco']['tco_per_km']:.2f}",
            f"${diesel_results['tco']['tco_per_tonne_km']:.2f}",
            f"${diesel_results['tco']['npv_total_cost']:,.2f}",
            f"${diesel_results['externalities']['externality_per_km']:.4f}",
            f"${diesel_results['social_tco']:,.2f}"
        ],
        'Difference': [
            "",
            "",
            f"{bev_results['vehicle_data']['payload_t'] - diesel_results['vehicle_data']['payload_t']}",
            f"${bev_results['acquisition_cost'] - diesel_results['acquisition_cost']:,.2f}",
            f"${bev_results['annual_costs']['annual_energy_cost'] - diesel_results['annual_costs']['annual_energy_cost']:,.2f}",
            f"${bev_results['annual_costs']['annual_maintenance_cost'] - diesel_results['annual_costs']['annual_maintenance_cost']:,.2f}",
            f"${bev_results['annual_costs']['annual_operating_cost'] - diesel_results['annual_costs']['annual_operating_cost']:,.2f}",
            "",
            f"{bev_results['emissions']['co2_per_km'] - diesel_results['emissions']['co2_per_km']:.4f}",
            f"{(bev_results['emissions']['annual_emissions'] - diesel_results['emissions']['annual_emissions']) / 1000:.2f}",
            f"{(bev_results['emissions']['lifetime_emissions'] - diesel_results['emissions']['lifetime_emissions']) / 1000:.2f}",
            f"${bev_results['tco']['tco_per_km'] - diesel_results['tco']['tco_per_km']:.2f}",
            f"${bev_results['tco']['tco_per_tonne_km'] - diesel_results['tco']['tco_per_tonne_km']:.2f}",
            f"${bev_results['tco']['npv_total_cost'] - diesel_results['tco']['npv_total_cost']:,.2f}",
            f"${bev_results['externalities']['externality_per_km'] - diesel_results['externalities']['externality_per_km']:.4f}",
            f"${bev_results['social_tco'] - diesel_results['social_tco']:,.2f}"
        ]
    }
    
    results_df = pd.DataFrame(results_data)
    
    # Group all detailed results into a single container to prevent white spaces
    with st.container():
        # Display the main results table
        st.subheader("Detailed Comparison")
        st.dataframe(
            results_df,
            hide_index=True,
            column_config={
                'Metric': st.column_config.TextColumn('Metric'),
                'BEV': st.column_config.TextColumn('BEV'),
                'Diesel': st.column_config.TextColumn('Diesel'),
                'Difference': st.column_config.TextColumn('Difference (BEV - Diesel)')
            }
        )
        
        # Add charging mix information if available
        if 'charging_mix' in bev_results:
            st.subheader("Charging Mix Details")
            
            # Create DataFrame for charging mix
            charging_mix_data = {'Charging Option': [], 'Price ($/kWh)': [], 'Percentage': []}
            
            for charging_id, percentage in bev_results['charging_mix'].items():
                # Get charging option details
                charging_option = None
                for idx, option in bev_results['charging_options'].iterrows():
                    if option['charging_id'] == charging_id:
                        charging_option = option
                        break
                
                if charging_option is not None:
                    charging_mix_data['Charging Option'].append(str(charging_option['charging_approach']))
                    charging_mix_data['Price ($/kWh)'].append(f"${charging_option['per_kwh_price']:.2f}")
                    charging_mix_data['Percentage'].append(f"{percentage * 100:.0f}%")
            
            charging_mix_df = pd.DataFrame(charging_mix_data)
            
            # Calculate weighted average price
            weighted_price = sum(
                [option['per_kwh_price'] * bev_results['charging_mix'][option['charging_id']] 
                 for idx, option in bev_results['charging_options'].iterrows() 
                 if option['charging_id'] in bev_results['charging_mix']]
            )
            
            # Display charging mix table
            st.dataframe(
                charging_mix_df,
                hide_index=True,
                column_config={
                    'Charging Option': st.column_config.TextColumn('Charging Option'),
                    'Price ($/kWh)': st.column_config.TextColumn('Price ($/kWh)'),
                    'Percentage': st.column_config.TextColumn('Percentage')
                }
            )
            
            st.info(f"Weighted Average Electricity Price: ${weighted_price:.2f}/kWh")
        
        # Add infrastructure details if available
        if 'infrastructure_costs' in bev_results:
            st.subheader("Infrastructure Details")
            
            infrastructure = bev_results['infrastructure_costs']
            
            infrastructure_data = {
                'Metric': [
                    'Infrastructure Type',
                    'Capital Cost ($)',
                    'Service Life (years)',
                    'Annual Maintenance Cost ($)',
                    'Fleet Size (vehicles)',
                    'Cost Per Vehicle ($)',
                    'Replacement Cycles',
                    'Infrastructure Subsidy ($)',
                    'Subsidy Rate (%)'
                ],
                'Value': [
                    str(bev_results.get('selected_infrastructure_description', 'N/A')),
                    f"${infrastructure['infrastructure_price']:,.0f}",
                    str(infrastructure['service_life_years']),
                    f"${infrastructure['annual_maintenance']:,.0f}",
                    str(infrastructure.get('fleet_size', 1)),
                    f"${infrastructure['npv_per_vehicle']:,.0f}",
                    str(infrastructure['replacement_cycles']),
                    f"${infrastructure.get('subsidy_amount', 0):,.0f}",
                    f"{infrastructure.get('subsidy_rate', 0) * 100:.0f}%"
                ]
            }
            
            infrastructure_df = pd.DataFrame(infrastructure_data)
            
            st.dataframe(
                infrastructure_df,
                hide_index=True,
                column_config={
                    'Metric': st.column_config.TextColumn('Metric'),
                    'Value': st.column_config.TextColumn('Value')
                }
            )
        
        # Add export button
        # We'll create a serializable version of the results dataframe for export
        export_data = results_df.copy()
        
        # Clean up any non-serializable data before export
        csv = export_data.to_csv(index=False)
        st.download_button(
            label="Download Results as CSV",
            data=csv,
            file_name="tco_comparison_results.csv",
            mime="text/csv"
        )
