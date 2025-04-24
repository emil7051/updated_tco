import math
import numpy as np

def calculate_energy_costs(vehicle_data, fees_data, charging_data, financial_params, selected_charging, charging_mix=None):
    """
    Calculate energy costs per km based on vehicle drivetrain
    
    Args:
        vehicle_data: Vehicle specifications
        fees_data: Associated fees for the vehicle
        charging_data: Charging options data
        financial_params: Financial parameters
        selected_charging: ID of selected charging option
        charging_mix: Optional dictionary of charging_id -> percentage (as decimal) for mixed charging
    """
    if vehicle_data['vehicle_drivetrain'] == 'BEV':
        if charging_mix is not None and len(charging_mix) > 0:
            # Calculate weighted average electricity price
            weighted_price = 0
            for charging_id, percentage in charging_mix.items():
                charging_option = charging_data[charging_data['charging_id'] == charging_id].iloc[0]
                weighted_price += charging_option['per_kwh_price'] * percentage
            
            electricity_price = weighted_price
        else:
            # Get electricity price from selected charging option
            charging_option = charging_data[charging_data['charging_id'] == selected_charging].iloc[0]
            electricity_price = charging_option['per_kwh_price']
        
        # Calculate energy cost per km for BEV
        energy_cost_per_km = vehicle_data['kwh_per100km'] / 100 * electricity_price
    else:
        # Get diesel price from financial parameters
        diesel_price = financial_params[financial_params['finance_description'] == 'diesel_price'].iloc[0]['default_value']
        
        # Calculate energy cost per km for diesel
        energy_cost_per_km = vehicle_data['litres_per100km'] / 100 * diesel_price
    
    return energy_cost_per_km

def calculate_annual_costs(vehicle_data, fees_data, energy_cost_per_km, annual_kms, incentives_data=None, apply_incentives=False):
    """
    Calculate annual operating costs with optional incentives
    """
    # Get maintenance cost per km
    maintenance_data = fees_data[fees_data['vehicle_id'] == vehicle_data['vehicle_id']].iloc[0]
    maintenance_per_km = maintenance_data['maintenance_perkm_price']
    
    # Calculate annual maintenance cost
    annual_maintenance_cost = maintenance_per_km * annual_kms
    
    # Calculate annual energy cost
    annual_energy_cost = energy_cost_per_km * annual_kms
    
    # Get registration and insurance costs
    registration_annual = maintenance_data['registration_annual_price']
    insurance_annual = maintenance_data['insurance_annual_price']
    
    # Apply incentives if specified and provided
    if apply_incentives and incentives_data is not None and vehicle_data['vehicle_drivetrain'] == 'BEV':
        # Filter active incentives
        active_incentives = incentives_data[
            (incentives_data['incentive_flag'] == 1) &
            ((incentives_data['drivetrain'] == 'BEV') | (incentives_data['drivetrain'] == 'All'))
        ]
        
        # Apply registration exemption if available
        registration_exemption = active_incentives[active_incentives['incentive_type'] == 'registration_exemption']
        if not registration_exemption.empty:
            registration_annual *= (1 - registration_exemption.iloc[0]['incentive_rate'])
        
        # Apply insurance discount if available
        insurance_discount = active_incentives[active_incentives['incentive_type'] == 'insurance_discount']
        if not insurance_discount.empty:
            insurance_annual *= (1 - insurance_discount.iloc[0]['incentive_rate'])
        
        # Apply electricity rate discount if available
        electricity_discount = active_incentives[active_incentives['incentive_type'] == 'electricity_rate_discount']
        if not electricity_discount.empty and vehicle_data['vehicle_drivetrain'] == 'BEV':
            annual_energy_cost *= (1 - electricity_discount.iloc[0]['incentive_rate'])
    
    # Calculate total annual operating cost
    annual_operating_cost = annual_energy_cost + annual_maintenance_cost + registration_annual + insurance_annual
    
    return {
        'annual_energy_cost': annual_energy_cost,
        'annual_maintenance_cost': annual_maintenance_cost,
        'registration_annual': registration_annual,
        'insurance_annual': insurance_annual,
        'annual_operating_cost': annual_operating_cost
    }

def calculate_emissions(vehicle_data, emission_factors, annual_kms, truck_life_years):
    """
    Calculate emissions metrics
    """
    if vehicle_data['vehicle_drivetrain'] == 'BEV':
        # Get electricity emission factor from the emission_factors table
        electricity_ef = emission_factors[
            (emission_factors['fuel_type'] == 'electricity') & 
            (emission_factors['emission_standard'] == 'Grid')
        ].iloc[0]['co2_per_unit']
        
        # Calculate CO2 per km for BEV
        co2_per_km = vehicle_data['kwh_per100km'] / 100 * electricity_ef
    else:
        # Get diesel emission factor
        diesel_ef = emission_factors[
            (emission_factors['fuel_type'] == 'diesel') & 
            (emission_factors['emission_standard'] == 'Euro IV+')
        ].iloc[0]['co2_per_unit']
        
        # Calculate CO2 per km for diesel
        co2_per_km = vehicle_data['litres_per100km'] / 100 * diesel_ef
    
    # Calculate annual and lifetime emissions
    annual_emissions = co2_per_km * annual_kms
    lifetime_emissions = annual_emissions * truck_life_years
    
    return {
        'co2_per_km': co2_per_km,
        'annual_emissions': annual_emissions,
        'lifetime_emissions': lifetime_emissions
    }

def calculate_acquisition_cost(vehicle_data, fees_data, incentives_data, apply_incentives=True):
    """
    Calculate vehicle acquisition cost with optional incentives
    """
    # Base vehicle price
    msrp = vehicle_data['msrp_price']
    
    # Get associated fees
    fees = fees_data[fees_data['vehicle_id'] == vehicle_data['vehicle_id']].iloc[0]
    stamp_duty = fees['stamp_duty_price']
    
    # Calculate base acquisition cost
    acquisition_cost = msrp + stamp_duty
    
    # Apply incentives if specified and for BEVs
    if apply_incentives and vehicle_data['vehicle_drivetrain'] == 'BEV':
        # Filter active incentives
        active_incentives = incentives_data[
            (incentives_data['incentive_flag'] == 1) &
            ((incentives_data['drivetrain'] == 'BEV') | (incentives_data['drivetrain'] == 'All'))
        ]
        
        # Apply purchase rebate if available
        purchase_rebate = active_incentives[active_incentives['incentive_type'] == 'purchase_rebate_aud']
        if not purchase_rebate.empty:
            acquisition_cost -= purchase_rebate.iloc[0]['incentive_rate']
        
        # Apply stamp duty exemption if available
        stamp_duty_exemption = active_incentives[active_incentives['incentive_type'] == 'stamp_duty_exemption']
        if not stamp_duty_exemption.empty:
            acquisition_cost -= stamp_duty * stamp_duty_exemption.iloc[0]['incentive_rate']
    
    return acquisition_cost

def calculate_npv(annual_cost, discount_rate, years):
    """
    Calculate Net Present Value of a constant annual cost
    """
    npv = 0
    for year in range(1, years + 1):
        npv += annual_cost / ((1 + discount_rate) ** year)
    return npv

def calculate_residual_value(vehicle_data, years, initial_depreciation, annual_depreciation):
    """
    Calculate residual value of the vehicle after specified years
    """
    # Initial value after first-year depreciation
    value_after_initial = vehicle_data['msrp_price'] * (1 - initial_depreciation)
    
    # Apply annual depreciation for remaining years
    residual_value = value_after_initial * ((1 - annual_depreciation) ** (years - 1))
    
    return residual_value

def calculate_battery_replacement(vehicle_data, battery_params, truck_life_years, discount_rate):
    """
    Calculate battery replacement costs if needed
    """
    if vehicle_data['vehicle_drivetrain'] != 'BEV':
        return 0
    
    # Get battery parameters
    replacement_cost_per_kwh = battery_params[
        battery_params['battery_description'] == 'replacement_per_kwh_price'
    ].iloc[0]['default_value']
    
    degradation_rate = battery_params[
        battery_params['battery_description'] == 'degradation_annual_percent'
    ].iloc[0]['default_value']
    
    min_capacity = battery_params[
        battery_params['battery_description'] == 'minimum_capacity_percent'
    ].iloc[0]['default_value']
    
    # Calculate years until replacement needed
    years_until_replacement = math.log(min_capacity) / math.log(1 - degradation_rate)
    
    # Check if replacement happens within lifetime
    if years_until_replacement > truck_life_years:
        return 0
    
    # Calculate replacement cost
    replacement_cost = vehicle_data['battery_capacity_kwh'] * replacement_cost_per_kwh
    
    # Use the provided discount rate from financial parameters
    npv_replacement = replacement_cost / ((1 + discount_rate) ** years_until_replacement)
    
    return npv_replacement

def calculate_tco(vehicle_data, fees_data, annual_costs, acquisition_cost, 
                  residual_value, battery_replacement, npv_annual_cost, 
                  annual_kms, truck_life_years):
    """
    Calculate Total Cost of Ownership metrics
    """
    # Calculate NPV of total costs
    npv_total_cost = acquisition_cost + npv_annual_cost - residual_value + battery_replacement
    
    # Calculate TCO per km
    tco_per_km = npv_total_cost / (annual_kms * truck_life_years)
    
    # Calculate TCO per tonne-km
    tco_per_tonne_km = tco_per_km / vehicle_data['payload_t']
    
    return {
        'npv_total_cost': npv_total_cost,
        'tco_per_km': tco_per_km,
        'tco_per_tonne_km': tco_per_tonne_km,
        'tco_lifetime': npv_total_cost,
        'tco_annual': npv_total_cost / truck_life_years
    }

def calculate_externalities(vehicle_data, externalities_data, annual_kms, truck_life_years, discount_rate):
    """
    Calculate externality costs
    """
    vehicle_class = vehicle_data['vehicle_type']
    drivetrain = vehicle_data['vehicle_drivetrain']
    
    # Filter externalities for this vehicle type and drivetrain
    vehicle_externalities = externalities_data[
        (externalities_data['vehicle_class'] == vehicle_class) & 
        (externalities_data['drivetrain'] == drivetrain)
    ]
    
    # Calculate total externality cost per km
    total_externality_per_km = vehicle_externalities['cost_per_km'].sum()
    
    # Calculate annual and lifetime costs
    annual_externality_cost = total_externality_per_km * annual_kms
    lifetime_externality_cost = annual_externality_cost * truck_life_years
    
    # Calculate NPV of externality costs
    npv_externality = calculate_npv(annual_externality_cost, discount_rate, truck_life_years)
    
    return {
        'externality_per_km': total_externality_per_km,
        'annual_externality_cost': annual_externality_cost,
        'lifetime_externality_cost': lifetime_externality_cost,
        'npv_externality': npv_externality
    }

def calculate_social_tco(tco_metrics, externality_metrics):
    """
    Calculate social TCO including externalities
    """
    social_tco = tco_metrics['npv_total_cost'] + externality_metrics['npv_externality']
    
    return social_tco

def calculate_comparative_metrics(bev_results, diesel_results, annual_kms, truck_life_years):
    """
    Calculate comparative metrics between BEV and diesel
    """
    # Upfront cost difference
    upfront_diff = bev_results['acquisition_cost'] - diesel_results['acquisition_cost']
    
    # Annual operating cost savings
    annual_savings = diesel_results['annual_costs']['annual_operating_cost'] - bev_results['annual_costs']['annual_operating_cost']
    
    # Calculate price parity year (intersection of price curves)
    # Price parity occurs when: BEV_initial + BEV_annual*years = Diesel_initial + Diesel_annual*years
    # Solving for years: (BEV_initial - Diesel_initial) / (Diesel_annual - BEV_annual)
    bev_initial = bev_results['acquisition_cost']
    diesel_initial = diesel_results['acquisition_cost']
    bev_annual = bev_results['annual_costs']['annual_operating_cost']
    diesel_annual = diesel_results['annual_costs']['annual_operating_cost']
    
    if diesel_annual > bev_annual:
        price_parity_year = (bev_initial - diesel_initial) / (diesel_annual - bev_annual)
    else:
        price_parity_year = float('inf')
    
    # Emission savings
    emission_savings = diesel_results['emissions']['lifetime_emissions'] - bev_results['emissions']['lifetime_emissions']
    
    # TCO ratio (BEV to diesel)
    tco_ratio = bev_results['tco']['npv_total_cost'] / diesel_results['tco']['npv_total_cost']
    
    # Abatement cost ($ per tonne CO2)
    if emission_savings > 0:
        abatement_cost = (bev_results['tco']['npv_total_cost'] - diesel_results['tco']['npv_total_cost']) / (emission_savings / 1000)
    else:
        abatement_cost = float('inf')
    
    return {
        'upfront_cost_difference': upfront_diff,
        'annual_operating_savings': annual_savings,
        'price_parity_year': price_parity_year,
        'emission_savings_lifetime': emission_savings,
        'bev_to_diesel_tco_ratio': tco_ratio,
        'abatement_cost': abatement_cost
    }

def calculate_infrastructure_costs(infrastructure_option, truck_life_years, discount_rate, fleet_size=1):
    """
    Calculate charging infrastructure costs amortized over the vehicle lifetime
    
    Args:
        infrastructure_option: Selected infrastructure option data
        truck_life_years: Vehicle service life in years
        discount_rate: Discount rate for NPV calculations
        fleet_size: Number of vehicles sharing the infrastructure
    
    Returns:
        Dictionary containing infrastructure cost metrics
    """
    # Extract infrastructure data
    infrastructure_price = infrastructure_option['infrastructure_price']
    service_life_years = infrastructure_option['service_life_years']
    maintenance_percent = infrastructure_option['maintenance_percent']
    
    # Calculate annual maintenance cost
    annual_maintenance = infrastructure_price * maintenance_percent
    
    # Amortized capital cost (straight-line depreciation)
    annual_capital_cost = infrastructure_price / service_life_years
    
    # Total annual infrastructure cost
    total_annual_cost = annual_capital_cost + annual_maintenance
    
    # Per-vehicle annual cost
    per_vehicle_annual_cost = total_annual_cost / fleet_size
    
    # Calculate NPV of infrastructure costs over truck lifetime
    replacement_cycles = max(1, math.ceil(truck_life_years / service_life_years))
    
    npv_infrastructure = 0
    for cycle in range(replacement_cycles):
        # Initial capital for this cycle
        cycle_start_year = cycle * service_life_years
        
        # Only count if within truck lifetime
        if cycle_start_year < truck_life_years:
            # Capital cost at the start of this cycle
            if cycle == 0:
                # First infrastructure installation
                npv_infrastructure += infrastructure_price
            else:
                # Replacement cost (discounted to present value)
                npv_infrastructure += infrastructure_price / ((1 + discount_rate) ** cycle_start_year)
            
            # Maintenance costs for this cycle
            years_in_cycle = min(service_life_years, truck_life_years - cycle_start_year)
            for year in range(years_in_cycle):
                current_year = cycle_start_year + year + 1  # +1 because maintenance starts after year 0
                npv_maintenance = annual_maintenance / ((1 + discount_rate) ** current_year)
                npv_infrastructure += npv_maintenance
    
    # Infrastructure cost per vehicle
    npv_per_vehicle = npv_infrastructure / fleet_size
    
    return {
        'infrastructure_price': infrastructure_price,
        'service_life_years': service_life_years,
        'annual_maintenance': annual_maintenance,
        'annual_capital_cost': annual_capital_cost,
        'total_annual_cost': total_annual_cost,
        'per_vehicle_annual_cost': per_vehicle_annual_cost,
        'replacement_cycles': replacement_cycles,
        'npv_infrastructure': npv_infrastructure,
        'npv_per_vehicle': npv_per_vehicle
    }

def calculate_charging_requirements(vehicle_data, annual_kms, infrastructure_option=None):
    """
    Calculate charging requirements based on vehicle data and usage pattern
    
    Args:
        vehicle_data: Vehicle specifications
        annual_kms: Annual distance traveled
        infrastructure_option: Optional infrastructure data
    
    Returns:
        Dictionary containing charging requirement metrics
    """
    # Only applicable for BEVs
    if vehicle_data['vehicle_drivetrain'] != 'BEV':
        return {
            'daily_distance': 0,
            'daily_kwh_required': 0,
            'charging_time_per_day': 0,
            'max_vehicles_per_charger': 0
        }
    
    # Calculate daily distance and energy requirements
    daily_distance = annual_kms / 365
    daily_kwh_required = daily_distance * vehicle_data['kwh_per100km'] / 100
    
    # Default charger power if infrastructure option not provided
    charger_power = 80  # kW
    
    # Extract charger power from infrastructure option if available
    if infrastructure_option is not None:
        # Extract power from description (e.g. "DC Fast Charger 80 kW" -> 80)
        description = infrastructure_option['infrastructure_description']
        if "kW" in description:
            try:
                charger_power = float(description.split("kW")[0].strip().split(" ")[-1])
            except (ValueError, IndexError):
                # If extraction fails, keep default value
                pass
    
    # Calculate charging time needed per day (hours)
    charging_time_per_day = daily_kwh_required / charger_power if charger_power > 0 else 0
    
    # Calculate maximum vehicles that can share one charger
    # Assuming charger is available 24 hours per day
    max_vehicles_per_charger = 24 / charging_time_per_day if charging_time_per_day > 0 else 0
    
    return {
        'daily_distance': daily_distance,
        'daily_kwh_required': daily_kwh_required,
        'charger_power': charger_power,
        'charging_time_per_day': charging_time_per_day,
        'max_vehicles_per_charger': max_vehicles_per_charger
    }

def apply_infrastructure_incentives(infrastructure_costs, incentives_data, apply_incentives=True):
    """
    Apply infrastructure-related incentives to costs
    
    Args:
        infrastructure_costs: Infrastructure cost data
        incentives_data: Available incentives data
        apply_incentives: Whether to apply incentives
    
    Returns:
        Updated infrastructure costs with incentives applied
    """
    if not apply_incentives:
        return infrastructure_costs
    
    # Copy the input costs to avoid modifying the original
    updated_costs = infrastructure_costs.copy()
    
    # Filter for active infrastructure incentives
    active_incentives = incentives_data[
        (incentives_data['incentive_flag'] == 1) &
        (incentives_data['incentive_type'] == 'charging_infrastructure_subsidy')
    ]
    
    if not active_incentives.empty:
        # Apply infrastructure subsidy
        subsidy_rate = active_incentives.iloc[0]['incentive_rate']
        
        # Apply to upfront infrastructure price
        subsidy_amount = updated_costs['infrastructure_price'] * subsidy_rate
        updated_costs['infrastructure_price_with_incentives'] = updated_costs['infrastructure_price'] - subsidy_amount
        
        # Recalculate NPV with incentives
        discount = subsidy_rate * updated_costs['npv_infrastructure']
        updated_costs['npv_infrastructure_with_incentives'] = updated_costs['npv_infrastructure'] - discount
        updated_costs['npv_per_vehicle_with_incentives'] = updated_costs['npv_per_vehicle'] - (discount / updated_costs.get('fleet_size', 1))
        
        # Store subsidy information
        updated_costs['subsidy_rate'] = subsidy_rate
        updated_costs['subsidy_amount'] = subsidy_amount
    else:
        # No incentives applied
        updated_costs['infrastructure_price_with_incentives'] = updated_costs['infrastructure_price']
        updated_costs['npv_infrastructure_with_incentives'] = updated_costs['npv_infrastructure']
        updated_costs['npv_per_vehicle_with_incentives'] = updated_costs['npv_per_vehicle']
        updated_costs['subsidy_rate'] = 0
        updated_costs['subsidy_amount'] = 0
    
    return updated_costs

def integrate_infrastructure_with_tco(tco_data, infrastructure_costs, apply_incentives=True):
    """
    Integrate infrastructure costs into TCO calculations
    
    Args:
        tco_data: Existing TCO calculation results
        infrastructure_costs: Infrastructure cost data
        apply_incentives: Whether incentives are applied
    
    Returns:
        Updated TCO data with infrastructure costs included
    """
    # Create a copy to avoid modifying the original
    updated_tco = tco_data.copy()
    
    # Use incentive-adjusted values if available and incentives are applied
    if apply_incentives and 'npv_per_vehicle_with_incentives' in infrastructure_costs:
        infrastructure_npv = infrastructure_costs['npv_per_vehicle_with_incentives']
    else:
        infrastructure_npv = infrastructure_costs['npv_per_vehicle']
    
    # Add infrastructure costs to total cost
    updated_tco['npv_total_cost'] += infrastructure_npv
    
    # Update per-km and per-tonne-km metrics
    annual_kms = tco_data.get('annual_kms', 0)
    truck_life_years = tco_data.get('truck_life_years', 0)
    payload_t = tco_data.get('payload_t', 0)
    
    # Recalculate per-km metrics if we have the necessary data
    if annual_kms > 0 and truck_life_years > 0:
        total_lifetime_kms = annual_kms * truck_life_years
        updated_tco['tco_per_km'] = updated_tco['npv_total_cost'] / total_lifetime_kms
        
        if payload_t > 0:
            updated_tco['tco_per_tonne_km'] = updated_tco['tco_per_km'] / payload_t
    
    # Add infrastructure costs as separate item
    updated_tco['infrastructure_costs'] = infrastructure_costs
    
    return updated_tco
