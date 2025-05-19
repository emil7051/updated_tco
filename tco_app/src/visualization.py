import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .constants import Drivetrain  # Centralised drivetrain strings
from .utils.energy import weighted_electricity_price

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
    
    df = pd.DataFrame(
        {
            "Category": categories + categories,
            "Cost": bev_values + diesel_values,
            "Vehicle Type": [Drivetrain.BEV.value] * len(categories)
            + [Drivetrain.DIESEL.value] * len(categories),
        }
    )
    
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
    df = pd.DataFrame(
        {
            "Year": years + years,
            "Cumulative Cost": bev_cumulative + diesel_cumulative,
            "Vehicle Type": [Drivetrain.BEV.value] * len(years)
            + [Drivetrain.DIESEL.value] * len(years),
        }
    )
    
    # Create line chart
    fig = px.line(
        df, 
        x='Year', 
        y='Cumulative Cost', 
        color='Vehicle Type',
        title='Cumulative Costs Over Time',
        labels={'Cumulative Cost': 'Cumulative Cost (AUD)', 'Year': 'Year'},
        color_discrete_map={Drivetrain.BEV.value: "#1f77b4", Drivetrain.DIESEL.value: "#ff7f0e"},
        height=400
    )
    
    # Find intersection point (price parity) where BEV and Diesel costs are equal
    intersection_year = None
    intersection_cost = None
    
    # Check for intersection between consecutive years
    for i in range(len(years) - 1):
        bev_cost1, bev_cost2 = bev_cumulative[i], bev_cumulative[i+1]
        diesel_cost1, diesel_cost2 = diesel_cumulative[i], diesel_cumulative[i+1]
        
        # Check if the cost difference changes sign (intersection)
        if (bev_cost1 - diesel_cost1) * (bev_cost2 - diesel_cost2) <= 0:
            # Lines intersect between year i and i+1
            # Use linear interpolation to find the exact point
            year1, year2 = years[i], years[i+1]
            
            # Calculate the intersection point using line equation
            if bev_cost2 - bev_cost1 != diesel_cost2 - diesel_cost1:  # Avoid division by zero
                # Solve for t where: bev_cost1 + t*(bev_cost2-bev_cost1) = diesel_cost1 + t*(diesel_cost2-diesel_cost1)
                t = (diesel_cost1 - bev_cost1) / ((bev_cost2 - bev_cost1) - (diesel_cost2 - diesel_cost1))
                intersection_year = year1 + t
                intersection_cost = bev_cost1 + t * (bev_cost2 - bev_cost1)
                break
    
    # Add the calculated price parity point if found
    if intersection_year is not None and intersection_cost is not None:
        fig.add_trace(go.Scatter(
            x=[intersection_year],
            y=[intersection_cost],
            mode='markers',
            marker=dict(size=12, color='green', symbol='star'),
            name='Price Parity Point',
            hoverinfo='text',
            text=f'Price Parity at {intersection_year:.1f} years'
        ))
    # If no intersection found but we have a price parity year, use the old method as fallback
    elif 'comparison' in bev_results and 'price_parity_year' in bev_results['comparison'] and bev_results['comparison']['price_parity_year'] < truck_life_years:
        parity_year = bev_results['comparison']['price_parity_year']
        # Interpolate costs for both lines to find the exact costs at parity_year
        parity_bev_cost = np.interp(parity_year, years, bev_cumulative)
        parity_diesel_cost = np.interp(parity_year, years, diesel_cumulative)
        # Use the average of both costs to better approximate the intersection
        parity_cost = (parity_bev_cost + parity_diesel_cost) / 2
        
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
        'Vehicle Type': [Drivetrain.BEV.value, Drivetrain.DIESEL.value],
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
    
    # Calculate weighted average price using utility (values are already percentages)
    if sum(values) > 0:
        # Reconstruct mix dict for the utility
        charging_mix = {
            cid: bev_results['charging_mix'][cid]
            for cid in bev_results['charging_mix']
            if bev_results['charging_mix'][cid] > 0
        }
        weighted_price = weighted_electricity_price(charging_mix, bev_results['charging_options'])
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
    
    # Add BEV TCO line - use lifetime TCO instead of per km
    fig.add_trace(go.Scatter(
        x=param_range,
        y=[tco['bev']['tco_lifetime'] for tco in recalculated_tcos],
        mode='lines+markers',
        name='BEV TCO',
        line=dict(color='#2E86C1', width=3),
        marker=dict(size=8)
    ))
    
    # Add Diesel TCO line - use lifetime TCO instead of per km
    fig.add_trace(go.Scatter(
        x=param_range,
        y=[tco['diesel']['tco_lifetime'] for tco in recalculated_tcos],
        mode='lines+markers',
        name='Diesel TCO',
        line=dict(color='#E67E22', width=3),
        marker=dict(size=8)
    ))
    
    # Add TCO difference line - use lifetime TCO difference
    fig.add_trace(go.Scatter(
        x=param_range,
        y=[tco['bev']['tco_lifetime'] - tco['diesel']['tco_lifetime'] for tco in recalculated_tcos],
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
        bev_tco1 = recalculated_tcos[i]['bev']['tco_lifetime']
        diesel_tco1 = recalculated_tcos[i]['diesel']['tco_lifetime']
        bev_tco2 = recalculated_tcos[i+1]['bev']['tco_lifetime']
        diesel_tco2 = recalculated_tcos[i+1]['diesel']['tco_lifetime']
        
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
            y1 = recalculated_tcos[break_even_index]['bev']['tco_lifetime']
            y2 = recalculated_tcos[break_even_index+1]['bev']['tco_lifetime']
            
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
        yaxis_title='Lifetime TCO (AUD)',
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

def create_payload_comparison_chart(payload_metrics, bev_results, diesel_results):
    """
    Create a stacked bar chart showing the impact of payload penalty on TCO
    
    Args:
        payload_metrics: Dictionary with payload analysis metrics
        bev_results: Dictionary with BEV results
        diesel_results: Dictionary with diesel results
        
    Returns:
        Plotly figure object
    """
    # Create data for a stacked bar chart showing both original and additional costs
    fig = go.Figure()
    
    # Diesel bar (reference)
    fig.add_trace(go.Bar(
        x=['Diesel'],
        y=[diesel_results['tco']['npv_total_cost']],
        name='Total TCO',
        marker_color='#ff7f0e'
    ))
    
    # BEV bars (standard and with payload adjustment)
    fig.add_trace(go.Bar(
        x=['BEV (Standard)', 'BEV (Payload-Adjusted)'],
        y=[
            bev_results['tco']['npv_total_cost'], 
            bev_results['tco']['npv_total_cost']
        ],
        name='Base TCO',
        marker_color='#1f77b4'
    ))
    
    # Add payload adjustment costs as a separate bar segment
    if payload_metrics['has_penalty']:
        fig.add_trace(go.Bar(
            x=['BEV (Standard)', 'BEV (Payload-Adjusted)'],
            y=[
                0,  # No adjustment for standard
                payload_metrics['additional_operational_cost_lifetime']
            ],
            name='Payload Penalty Costs',
            marker_color='#d62728'
        ))
    
    fig.update_layout(
        barmode='stack',
        title='Lifetime TCO Comparison with Payload Adjustment',
        xaxis_title='Vehicle Type',
        yaxis_title='Lifetime TCO (AUD)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=500
    )
    
    return fig

def create_payload_sensitivity_chart(bev_results, diesel_results, financial_params, distances):
    """
    Create a chart showing how payload penalty affects TCO ratio at different annual distances
    
    Args:
        bev_results: Dictionary with BEV results
        diesel_results: Dictionary with diesel results
        financial_params: Financial parameters
        distances: List of annual distances to analyze
        
    Returns:
        Plotly figure object
    """
    import copy
    from .calculations import calculate_payload_penalty_costs
    
    # Calculate TCO for each distance
    results = []
    
    for distance in distances:
        # Make deep copies to avoid modifying the original results
        bev_temp = copy.deepcopy(bev_results)
        diesel_temp = copy.deepcopy(diesel_results)
        
        # Update annual distance
        bev_temp['annual_kms'] = distance
        diesel_temp['annual_kms'] = distance
        
        # Recalculate energy costs - simplified approach
        bev_annual_energy = bev_results['energy_cost_per_km'] * distance
        diesel_annual_energy = diesel_results['energy_cost_per_km'] * distance
        
        # Update annual costs
        bev_temp['annual_costs']['annual_energy_cost'] = bev_annual_energy
        diesel_temp['annual_costs']['annual_energy_cost'] = diesel_annual_energy
        
        # Update total annual operating costs
        bev_temp['annual_costs']['annual_operating_cost'] = (
            bev_annual_energy + 
            bev_temp['annual_costs']['annual_maintenance_cost'] + 
            bev_temp['annual_costs']['insurance_annual'] + 
            bev_temp['annual_costs']['registration_annual']
        )
        
        diesel_temp['annual_costs']['annual_operating_cost'] = (
            diesel_annual_energy + 
            diesel_temp['annual_costs']['annual_maintenance_cost'] + 
            diesel_temp['annual_costs']['insurance_annual'] + 
            diesel_temp['annual_costs']['registration_annual']
        )
        
        # Calculate payload penalty
        payload_metrics = calculate_payload_penalty_costs(bev_temp, diesel_temp, financial_params)
        
        # Store results
        results.append({
            'distance': distance,
            'standard_tco_ratio': bev_temp['tco']['npv_total_cost'] / diesel_temp['tco']['npv_total_cost'],
            'adjusted_tco_ratio': payload_metrics['bev_adjusted_lifetime_tco'] / diesel_temp['tco']['npv_total_cost'] if payload_metrics['has_penalty'] else bev_temp['tco']['npv_total_cost'] / diesel_temp['tco']['npv_total_cost']
        })
    
    # Create DataFrame for plotting
    results_df = pd.DataFrame(results)
    
    # Create line chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=results_df['distance'],
        y=results_df['standard_tco_ratio'],
        mode='lines+markers',
        name='Standard TCO Ratio (BEV/Diesel)',
        line=dict(color='#1f77b4')
    ))
    
    fig.add_trace(go.Scatter(
        x=results_df['distance'],
        y=results_df['adjusted_tco_ratio'],
        mode='lines+markers',
        name='Payload-Adjusted TCO Ratio',
        line=dict(color='#d62728')
    ))
    
    # Add horizontal line at ratio = 1 (break-even)
    fig.add_shape(
        type="line",
        x0=min(distances),
        y0=1,
        x1=max(distances),
        y1=1,
        line=dict(
            color="green",
            width=2,
            dash="dash",
        )
    )
    
    fig.add_annotation(
        x=min(distances) + (max(distances) - min(distances))*0.05,
        y=1.02,
        text="Break-even point (BEV = Diesel)",
        showarrow=False,
        font=dict(color="green")
    )
    
    fig.update_layout(
        title='Impact of Annual Distance on TCO Ratio with Payload Adjustment',
        xaxis_title='Annual Distance (km)',
        yaxis_title='TCO Ratio (BEV/Diesel)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=500
    )
    
    return fig
