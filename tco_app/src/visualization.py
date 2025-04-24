import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_cost_breakdown_chart(bev_results, diesel_results):
    """
    Create a stacked bar chart showing cost breakdown
    """
    # Prepare data for BEV
    bev_costs = {
        'Acquisition': bev_results['acquisition_cost'],
        'Energy': bev_results['annual_costs']['annual_energy_cost'] * bev_results['truck_life_years'],
        'Maintenance': bev_results['annual_costs']['annual_maintenance_cost'] * bev_results['truck_life_years'],
        'Insurance': bev_results['annual_costs']['insurance_annual'] * bev_results['truck_life_years'],
        'Registration': bev_results['annual_costs']['registration_annual'] * bev_results['truck_life_years'],
        'Battery Replacement': bev_results['battery_replacement'],
        'Residual Value': -bev_results['residual_value']
    }
    
    # Add infrastructure costs if available
    if 'infrastructure_costs' in bev_results:
        # Use the incentive-adjusted value if available
        if 'npv_per_vehicle_with_incentives' in bev_results['infrastructure_costs']:
            bev_costs['Infrastructure'] = bev_results['infrastructure_costs']['npv_per_vehicle_with_incentives']
        else:
            bev_costs['Infrastructure'] = bev_results['infrastructure_costs']['npv_per_vehicle']
    
    # Prepare data for Diesel
    diesel_costs = {
        'Acquisition': diesel_results['acquisition_cost'],
        'Energy': diesel_results['annual_costs']['annual_energy_cost'] * diesel_results['truck_life_years'],
        'Maintenance': diesel_results['annual_costs']['annual_maintenance_cost'] * diesel_results['truck_life_years'],
        'Insurance': diesel_results['annual_costs']['insurance_annual'] * diesel_results['truck_life_years'],
        'Registration': diesel_results['annual_costs']['registration_annual'] * diesel_results['truck_life_years'],
        'Battery Replacement': 0,
        'Residual Value': -diesel_results['residual_value'],
        'Infrastructure': 0  # No infrastructure costs for diesel
    }
    
    # Create DataFrame for plotting
    categories = list(bev_costs.keys())
    bev_values = list(bev_costs.values())
    diesel_values = [diesel_costs.get(cat, 0) for cat in categories]  # Use get to handle missing keys
    
    df = pd.DataFrame({
        'Category': categories + categories,
        'Cost': bev_values + diesel_values,
        'Vehicle Type': ['BEV'] * len(categories) + ['Diesel'] * len(categories)
    })
    
    # Create stacked bar chart
    fig = px.bar(
        df, 
        x='Vehicle Type', 
        y='Cost', 
        color='Category',
        title='Lifetime Cost Breakdown',
        labels={'Cost': 'Cost (AUD)', 'Vehicle Type': 'Vehicle Type'},
        color_discrete_sequence=px.colors.qualitative.Safe,
        height=500
    )
    
    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def create_annual_costs_chart(bev_results, diesel_results, truck_life_years):
    """
    Create a line chart showing annual costs over time
    """
    # Create year range
    years = list(range(1, truck_life_years + 1))
    
    # Calculate cumulative costs for each year
    bev_cumulative = [bev_results['acquisition_cost']]
    diesel_cumulative = [diesel_results['acquisition_cost']]
    
    # Add initial infrastructure cost for BEV if available
    if 'infrastructure_costs' in bev_results:
        # Use the incentive-adjusted initial cost if available
        if 'infrastructure_price_with_incentives' in bev_results['infrastructure_costs']:
            bev_cumulative[0] += bev_results['infrastructure_costs']['infrastructure_price_with_incentives'] / bev_results['infrastructure_costs'].get('fleet_size', 1)
        else:
            bev_cumulative[0] += bev_results['infrastructure_costs']['infrastructure_price'] / bev_results['infrastructure_costs'].get('fleet_size', 1)
    
    for year in range(1, truck_life_years):
        # Add annual operating costs (simplified - in a real implementation would include discount rate)
        bev_annual = bev_results['annual_costs']['annual_operating_cost']
        diesel_annual = diesel_results['annual_costs']['annual_operating_cost']
        
        # Add battery replacement in the appropriate year if applicable
        if bev_results.get('battery_replacement_year') == year:
            bev_annual += bev_results.get('battery_replacement_cost', 0)
        
        # Add infrastructure maintenance costs for BEV
        if 'infrastructure_costs' in bev_results:
            infrastructure_maintenance = bev_results['infrastructure_costs']['annual_maintenance'] / bev_results['infrastructure_costs'].get('fleet_size', 1)
            bev_annual += infrastructure_maintenance
            
            # Add infrastructure replacement costs if needed
            service_life = bev_results['infrastructure_costs']['service_life_years']
            if year % service_life == 0 and year < truck_life_years:
                if 'infrastructure_price_with_incentives' in bev_results['infrastructure_costs']:
                    bev_annual += bev_results['infrastructure_costs']['infrastructure_price_with_incentives'] / bev_results['infrastructure_costs'].get('fleet_size', 1)
                else:
                    bev_annual += bev_results['infrastructure_costs']['infrastructure_price'] / bev_results['infrastructure_costs'].get('fleet_size', 1)
        
        # Update cumulative costs
        bev_cumulative.append(bev_cumulative[-1] + bev_annual)
        diesel_cumulative.append(diesel_cumulative[-1] + diesel_annual)
    
    # Adjust for residual value in final year
    bev_cumulative[-1] -= bev_results['residual_value']
    diesel_cumulative[-1] -= diesel_results['residual_value']
    
    # Create DataFrame for plotting
    df = pd.DataFrame({
        'Year': years + years,
        'Cumulative Cost': bev_cumulative + diesel_cumulative,
        'Vehicle Type': ['BEV'] * len(years) + ['Diesel'] * len(years)
    })
    
    # Create line chart
    fig = px.line(
        df, 
        x='Year', 
        y='Cumulative Cost', 
        color='Vehicle Type',
        title='Cumulative Costs Over Time',
        labels={'Cumulative Cost': 'Cumulative Cost (AUD)', 'Year': 'Year'},
        color_discrete_map={'BEV': '#1f77b4', 'Diesel': '#ff7f0e'},
        height=400
    )
    
    # Add price parity point if applicable
    if bev_results['comparison']['price_parity_year'] < truck_life_years:
        parity_year = bev_results['comparison']['price_parity_year']
        parity_cost = np.interp(parity_year, years, diesel_cumulative)
        
        fig.add_trace(go.Scatter(
            x=[parity_year],
            y=[parity_cost],
            mode='markers',
            marker=dict(size=12, color='green', symbol='star'),
            name='Price Parity Point',
            hoverinfo='text',
            text=f'Price Parity at {parity_year:.1f} years'
        ))
    
    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def create_emissions_chart(bev_results, diesel_results, truck_life_years):
    """
    Create a bar chart comparing emissions
    """
    # Create data for plotting
    data = pd.DataFrame({
        'Vehicle Type': ['BEV', 'Diesel'],
        'Annual Emissions (kg CO₂)': [
            bev_results['emissions']['annual_emissions'],
            diesel_results['emissions']['annual_emissions']
        ],
        'Lifetime Emissions (tonnes CO₂)': [
            bev_results['emissions']['lifetime_emissions'] / 1000,
            diesel_results['emissions']['lifetime_emissions'] / 1000
        ]
    })
    
    # Create subplots
    fig = make_subplots(rows=1, cols=2, subplot_titles=('Annual Emissions', 'Lifetime Emissions'))
    
    # Add annual emissions bar chart
    fig.add_trace(
        go.Bar(
            x=data['Vehicle Type'],
            y=data['Annual Emissions (kg CO₂)'],
            marker_color=['#1f77b4', '#ff7f0e'],
            showlegend=False
        ),
        row=1, col=1
    )
    
    # Add lifetime emissions bar chart
    fig.add_trace(
        go.Bar(
            x=data['Vehicle Type'],
            y=data['Lifetime Emissions (tonnes CO₂)'],
            marker_color=['#1f77b4', '#ff7f0e'],
            showlegend=False
        ),
        row=1, col=2
    )
    
    # Update layout
    fig.update_layout(
        title_text='Emissions Comparison',
        height=400
    )
    
    fig.update_yaxes(title_text='kg CO₂ per year', row=1, col=1)
    fig.update_yaxes(title_text='tonnes CO₂ lifetime', row=1, col=2)
    
    return fig

def create_key_metrics_chart(bev_results, diesel_results):
    """
    Create a radar chart comparing key performance metrics
    """
    # Calculate infrastructure cost per km for BEV
    infrastructure_cost_per_km = 0
    if 'infrastructure_costs' in bev_results and 'annual_kms' in bev_results and 'truck_life_years' in bev_results:
        if 'npv_per_vehicle_with_incentives' in bev_results['infrastructure_costs']:
            infrastructure_npv = bev_results['infrastructure_costs']['npv_per_vehicle_with_incentives']
        else:
            infrastructure_npv = bev_results['infrastructure_costs']['npv_per_vehicle']
        
        total_kms = bev_results['annual_kms'] * bev_results['truck_life_years']
        infrastructure_cost_per_km = infrastructure_npv / total_kms if total_kms > 0 else 0
    
    # Normalize metrics for radar chart
    metrics = {
        'TCO per km': [
            bev_results['tco']['tco_per_km'],
            diesel_results['tco']['tco_per_km']
        ],
        'Energy cost per km': [
            bev_results['energy_cost_per_km'],
            diesel_results['energy_cost_per_km']
        ],
        'Maintenance per km': [
            bev_results['annual_costs']['annual_maintenance_cost'] / bev_results['annual_kms'],
            diesel_results['annual_costs']['annual_maintenance_cost'] / diesel_results['annual_kms']
        ],
        'CO₂ per km': [
            bev_results['emissions']['co2_per_km'],
            diesel_results['emissions']['co2_per_km']
        ],
        'Externality cost': [
            bev_results['externalities']['externality_per_km'],
            diesel_results['externalities']['externality_per_km']
        ],
        'Infrastructure per km': [
            infrastructure_cost_per_km,
            0  # No infrastructure costs for diesel
        ]
    }
    
    # Calculate ratios compared to the maximum value for each metric
    normalized_metrics = {}
    for key, values in metrics.items():
        max_value = max(values)
        normalized_metrics[key] = [value / max_value for value in values]
    
    # Prepare data for radar chart
    categories = list(normalized_metrics.keys())
    bev_values = [normalized_metrics[cat][0] for cat in categories]
    diesel_values = [normalized_metrics[cat][1] for cat in categories]
    
    # Create radar chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=bev_values,
        theta=categories,
        fill='toself',
        name='BEV',
        line_color='#1f77b4'
    ))
    
    fig.add_trace(go.Scatterpolar(
        r=diesel_values,
        theta=categories,
        fill='toself',
        name='Diesel',
        line_color='#ff7f0e'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )
        ),
        title='Comparative Performance (Lower is Better)',
        height=500
    )
    
    return fig

def create_charging_mix_chart(bev_results):
    """
    Create a pie chart showing the charging mix distribution
    """
    if 'charging_mix' not in bev_results:
        # If no charging mix available, return an empty figure
        fig = go.Figure()
        fig.update_layout(
            title="No Charging Mix Data Available",
            height=300
        )
        return fig
    
    # Prepare data for pie chart
    labels = []
    values = []
    prices = []
    
    for charging_id, percentage in bev_results['charging_mix'].items():
        # Only include options with non-zero percentage
        if percentage > 0:
            # Get charging option details
            for idx, option in bev_results['charging_options'].iterrows():
                if option['charging_id'] == charging_id:
                    labels.append(option['charging_approach'])
                    values.append(percentage * 100)  # Convert to percentage
                    prices.append(option['per_kwh_price'])
                    break
    
    # Create hover text with prices
    hover_text = [f"{label}: {value:.1f}%<br>Price: ${price:.2f}/kWh" for label, value, price in zip(labels, values, prices)]
    
    # Create pie chart
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hovertext=hover_text,
        hoverinfo='text',
        textinfo='percent',
        marker=dict(
            colors=px.colors.qualitative.Safe[:len(labels)]
        )
    )])
    
    # Calculate weighted average price
    if sum(values) > 0:
        weighted_price = sum([price * (value / 100) for price, value in zip(prices, values)])
        subtitle = f"Weighted Average: ${weighted_price:.2f}/kWh"
    else:
        subtitle = "No charging mix data"
    
    fig.update_layout(
        title={
            'text': f"Charging Mix Distribution<br><sup>{subtitle}</sup>",
            'x': 0.5,
            'y': 0.95,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        height=400
    )
    
    return fig

def create_sensitivity_chart(bev_results, diesel_results, parameter, param_range, recalculated_tcos):
    """
    Create a sensitivity analysis chart showing how TCO changes with parameter values
    
    Args:
        bev_results: Dictionary of BEV results
        diesel_results: Dictionary of diesel results
        parameter: The parameter being analyzed (string)
        param_range: Array of parameter values tested
        recalculated_tcos: Dictionary with recalculated TCO values for each parameter value
            
    Returns:
        Plotly figure object
    """
    import plotly.graph_objects as go
    
    # Set up the figure
    fig = go.Figure()
    
    # Add BEV TCO line
    fig.add_trace(go.Scatter(
        x=param_range,
        y=[tco['bev']['tco_per_km'] for tco in recalculated_tcos],
        mode='lines+markers',
        name='BEV TCO',
        line=dict(color='#2E86C1', width=3),
        marker=dict(size=8)
    ))
    
    # Add Diesel TCO line
    fig.add_trace(go.Scatter(
        x=param_range,
        y=[tco['diesel']['tco_per_km'] for tco in recalculated_tcos],
        mode='lines+markers',
        name='Diesel TCO',
        line=dict(color='#E67E22', width=3),
        marker=dict(size=8)
    ))
    
    # Add TCO difference line
    fig.add_trace(go.Scatter(
        x=param_range,
        y=[tco['bev']['tco_per_km'] - tco['diesel']['tco_per_km'] for tco in recalculated_tcos],
        mode='lines+markers',
        name='TCO Difference (BEV - Diesel)',
        line=dict(color='#8E44AD', width=2, dash='dash'),
        marker=dict(size=6)
    ))
    
    # Mark the current parameter value
    current_value = None
    if parameter == "Annual Distance (km)":
        current_value = bev_results['annual_kms']
    elif parameter == "Diesel Price ($/L)":
        current_value = diesel_results['vehicle_data']['diesel_price'] if 'diesel_price' in diesel_results['vehicle_data'] else None
    elif parameter == "Vehicle Lifetime (years)":
        current_value = bev_results['truck_life_years']
    elif parameter == "Discount Rate (%)":
        current_value = bev_results.get('discount_rate', None)
    elif parameter == "Electricity Price ($/kWh)":
        if 'weighted_electricity_price' in bev_results:
            current_value = bev_results['weighted_electricity_price']
        
    # Add a vertical line at the current parameter value if available
    if current_value is not None and current_value in param_range:
        fig.add_vline(
            x=current_value,
            line_width=2,
            line_dash="solid",
            line_color="green",
            annotation_text="Current Value",
            annotation_position="top right"
        )
    
    # Find break-even point (where BEV TCO = Diesel TCO)
    break_even_index = None
    break_even_value = None
    
    for i in range(len(param_range) - 1):
        bev_tco1 = recalculated_tcos[i]['bev']['tco_per_km']
        diesel_tco1 = recalculated_tcos[i]['diesel']['tco_per_km']
        bev_tco2 = recalculated_tcos[i+1]['bev']['tco_per_km']
        diesel_tco2 = recalculated_tcos[i+1]['diesel']['tco_per_km']
        
        # Check if the TCO difference changes sign (crosses 0)
        if (bev_tco1 - diesel_tco1) * (bev_tco2 - diesel_tco2) <= 0:
            # Simple linear interpolation to find the break-even point
            x1, x2 = param_range[i], param_range[i+1]
            y1, y2 = bev_tco1 - diesel_tco1, bev_tco2 - diesel_tco2
            
            # Avoid division by zero
            if y1 != y2:
                break_even_value = x1 - y1 * (x2 - x1) / (y2 - y1)
                break_even_index = i
    
    # Mark the break-even point if found
    if break_even_value is not None:
        # Find the interpolated TCO at break-even
        if break_even_index is not None:
            # Linear interpolation for BEV TCO at break-even
            x1, x2 = param_range[break_even_index], param_range[break_even_index+1]
            y1 = recalculated_tcos[break_even_index]['bev']['tco_per_km']
            y2 = recalculated_tcos[break_even_index+1]['bev']['tco_per_km']
            
            bev_tco_at_breakeven = y1 + (break_even_value - x1) * (y2 - y1) / (x2 - x1)
            
            fig.add_trace(go.Scatter(
                x=[break_even_value],
                y=[bev_tco_at_breakeven],
                mode='markers',
                marker=dict(
                    color='red',
                    size=12,
                    symbol='star',
                    line=dict(color='black', width=2)
                ),
                name=f'Break-even at {break_even_value:.2f}',
                hoverinfo='text',
                hovertext=f'Break-even: {break_even_value:.2f}'
            ))
    
    # Set up the layout
    param_unit = ""
    if parameter == "Annual Distance (km)":
        param_unit = "km"
    elif parameter == "Diesel Price ($/L)":
        param_unit = "$/L"
    elif parameter == "Vehicle Lifetime (years)":
        param_unit = "years"
    elif parameter == "Discount Rate (%)":
        param_unit = "%"
    elif parameter == "Electricity Price ($/kWh)":
        param_unit = "$/kWh"
    
    fig.update_layout(
        title=f'TCO Sensitivity to {parameter}',
        xaxis_title=f'{parameter} {param_unit}',
        yaxis_title='TCO per km (AUD)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        hovermode='x unified',
        margin=dict(l=20, r=20, t=60, b=20),
        height=500
    )
    
    return fig

def create_tornado_chart(base_tco, sensitivity_results):
    """
    Create a tornado chart showing the impact of varying different parameters on TCO
    
    Args:
        base_tco: Base TCO value
        sensitivity_results: Dictionary with parameter impacts
            
    Returns:
        Plotly figure object
    """
    import plotly.graph_objects as go
    
    # Prepare data for tornado chart
    parameters = []
    lower_impacts = []
    upper_impacts = []
    
    # Sort parameters by maximum absolute impact
    sorted_params = sorted(
        sensitivity_results.items(),
        key=lambda x: max(abs(x[1]['min_impact']), abs(x[1]['max_impact'])),
        reverse=True
    )
    
    for param, impacts in sorted_params:
        parameters.append(param)
        lower_impacts.append(impacts['min_impact'])
        upper_impacts.append(impacts['max_impact'])
    
    # Create the tornado chart
    fig = go.Figure()
    
    # Add bars for lower impact
    fig.add_trace(go.Bar(
        y=parameters,
        x=lower_impacts,
        orientation='h',
        name='Lower Value Impact',
        marker=dict(color='blue'),
        base=base_tco,
        hoverinfo='text',
        hovertext=[f"{p}: {i:.4f} AUD/km" for p, i in zip(parameters, lower_impacts)]
    ))
    
    # Add bars for upper impact
    fig.add_trace(go.Bar(
        y=parameters,
        x=upper_impacts,
        orientation='h',
        name='Upper Value Impact',
        marker=dict(color='red'),
        base=base_tco,
        hoverinfo='text',
        hovertext=[f"{p}: {i:.4f} AUD/km" for p, i in zip(parameters, upper_impacts)]
    ))
    
    # Update layout
    fig.update_layout(
        title='Tornado Chart: Impact of Parameters on BEV TCO',
        xaxis_title='TCO per km (AUD)',
        yaxis=dict(
            title='Parameter',
            categoryorder='array',
            categoryarray=parameters
        ),
        barmode='overlay',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        height=400,
        margin=dict(l=20, r=20, t=60, b=20)
    )
    
    # Add a vertical line for the base TCO
    fig.add_vline(
        x=base_tco,
        line_width=2,
        line_dash="dash",
        line_color="green",
        annotation_text=f"Base TCO: {base_tco:.4f}",
        annotation_position="top right"
    )
    
    return fig
