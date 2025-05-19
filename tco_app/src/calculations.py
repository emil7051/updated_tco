import math
import numpy as np
from .utils.finance import npv_constant as _npv_constant
from .utils.energy import weighted_electricity_price
from .constants import Drivetrain

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
    if vehicle_data['vehicle_drivetrain'] == Drivetrain.BEV:
        if charging_mix is not None and len(charging_mix) > 0:
            # Use shared utility to derive weighted average electricity price
            electricity_price = weighted_electricity_price(charging_mix, charging_data)
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
    if apply_incentives and incentives_data is not None and vehicle_data['vehicle_drivetrain'] == Drivetrain.BEV:
        # Filter active incentives
        active_incentives = incentives_data[
            (incentives_data['incentive_flag'] == 1) &
            ((incentives_data['drivetrain'] == Drivetrain.BEV) | (incentives_data['drivetrain'] == Drivetrain.ALL))
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
        if not electricity_discount.empty and vehicle_data['vehicle_drivetrain'] == Drivetrain.BEV:
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
    if vehicle_data['vehicle_drivetrain'] == Drivetrain.BEV:
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
    if apply_incentives and vehicle_data['vehicle_drivetrain'] == Drivetrain.BEV:
        # Filter active incentives
        active_incentives = incentives_data[
            (incentives_data['incentive_flag'] == 1) &
            ((incentives_data['drivetrain'] == Drivetrain.BEV) | (incentives_data['drivetrain'] == Drivetrain.ALL))
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
    """Delegate to utils.finance.npv_constant for the calculation."""
    return _npv_constant(annual_cost, discount_rate, years)

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
    if vehicle_data['vehicle_drivetrain'] != Drivetrain.BEV:
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
    
    # Calculate total externality cost per km (using the externalities_total if available)
    total_entry = vehicle_externalities[vehicle_externalities['pollutant_type'] == 'externalities_total']
    if not total_entry.empty:
        total_externality_per_km = total_entry.iloc[0]['cost_per_km']
    else:
        # Sum individual externality costs if total not available
        total_externality_per_km = vehicle_externalities['cost_per_km'].sum()
    
    # Calculate annual and lifetime costs
    annual_externality_cost = total_externality_per_km * annual_kms
    lifetime_externality_cost = annual_externality_cost * truck_life_years
    
    # Calculate NPV of externality costs
    npv_externality = calculate_npv(annual_externality_cost, discount_rate, truck_life_years)
    
    # Create breakdown by externality type
    externality_breakdown = {}
    for _, row in vehicle_externalities.iterrows():
        if row['pollutant_type'] != 'externalities_total':
            pollutant_type = row['pollutant_type']
            cost_per_km = row['cost_per_km']
            annual_cost = cost_per_km * annual_kms
            lifetime_cost = annual_cost * truck_life_years
            npv_cost = calculate_npv(annual_cost, discount_rate, truck_life_years)
            
            externality_breakdown[pollutant_type] = {
                'cost_per_km': cost_per_km,
                'annual_cost': annual_cost,
                'lifetime_cost': lifetime_cost,
                'npv_cost': npv_cost
            }
    
    return {
        'externality_per_km': total_externality_per_km,
        'annual_externality_cost': annual_externality_cost,
        'lifetime_externality_cost': lifetime_externality_cost,
        'npv_externality': npv_externality,
        'breakdown': externality_breakdown
    }

def calculate_social_tco(tco_metrics, externality_metrics):
    """
    Calculate social TCO including externalities
    """
    # Calculate social TCO metrics
    social_tco_lifetime = tco_metrics['npv_total_cost'] + externality_metrics['npv_externality']
    
    # Calculate other social TCO metrics
    annual_kms = tco_metrics.get('annual_kms', 0)
    truck_life_years = tco_metrics.get('truck_life_years', 0)
    payload_t = tco_metrics.get('payload_t', 0)
    
    # Calculate per-km metrics if we have the necessary data
    social_tco_per_km = 0
    social_tco_per_tonne_km = 0
    if annual_kms > 0 and truck_life_years > 0:
        total_lifetime_kms = annual_kms * truck_life_years
        social_tco_per_km = social_tco_lifetime / total_lifetime_kms
        
        if payload_t > 0:
            social_tco_per_tonne_km = social_tco_per_km / payload_t
    
    return {
        'social_tco_lifetime': social_tco_lifetime,
        'social_tco_per_km': social_tco_per_km,
        'social_tco_per_tonne_km': social_tco_per_tonne_km,
        'externality_percentage': (externality_metrics['npv_externality'] / social_tco_lifetime) * 100 if social_tco_lifetime > 0 else 0
    }

def calculate_comparative_metrics(bev_results, diesel_results, annual_kms, truck_life_years):
    """
    Calculate comparative metrics between BEV and diesel
    """
    # Upfront cost difference
    upfront_diff = bev_results['acquisition_cost'] - diesel_results['acquisition_cost']
    
    # Annual operating cost savings
    annual_savings = diesel_results['annual_costs']['annual_operating_cost'] - bev_results['annual_costs']['annual_operating_cost']
    
    # Calculate price parity year (intersection of cumulative cost curves)
    # Create arrays to track cumulative costs over time
    years = list(range(1, truck_life_years + 1))
    
    # Initialize cumulative costs with acquisition costs
    bev_cumulative = [bev_results['acquisition_cost']]
    diesel_cumulative = [diesel_results['acquisition_cost']]
    
    # Add initial infrastructure cost for BEV if available
    if 'infrastructure_costs' in bev_results:
        if 'infrastructure_price_with_incentives' in bev_results['infrastructure_costs']:
            bev_cumulative[0] += bev_results['infrastructure_costs']['infrastructure_price_with_incentives'] / bev_results['infrastructure_costs'].get('fleet_size', 1)
        else:
            bev_cumulative[0] += bev_results['infrastructure_costs']['infrastructure_price'] / bev_results['infrastructure_costs'].get('fleet_size', 1)
    
    # Calculate cumulative costs for each year
    for year in range(1, truck_life_years):
        # Add annual operating costs
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
    
    # Find intersection point (price parity) where BEV and Diesel costs are equal
    price_parity_year = float('inf')  # Default if no intersection
    
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
                price_parity_year = year1 + t
                break
    
    # Fallback to the algebraic calculation if no intersection found
    if price_parity_year == float('inf'):
        bev_initial = bev_results['acquisition_cost']
        diesel_initial = diesel_results['acquisition_cost']
        bev_annual = bev_results['annual_costs']['annual_operating_cost']
        diesel_annual = diesel_results['annual_costs']['annual_operating_cost']
        
        if diesel_annual > bev_annual:
            price_parity_year = (bev_initial - diesel_initial) / (diesel_annual - bev_annual)
    
    # Emission savings
    emission_savings = diesel_results['emissions']['lifetime_emissions'] - bev_results['emissions']['lifetime_emissions']
    
    # TCO ratio (BEV to diesel)
    tco_ratio = bev_results['tco']['npv_total_cost'] / diesel_results['tco']['npv_total_cost']
    
    # Abatement cost ($ per tonne CO2)
    if emission_savings > 0:
        abatement_cost = (bev_results['tco']['npv_total_cost'] - diesel_results['tco']['npv_total_cost']) / (emission_savings / 1000)
    else:
        abatement_cost = float('inf')
    
    # Social TCO comparison metrics
    social_tco_ratio = 0
    social_abatement_cost = float('inf')
    
    if ('social_tco' in bev_results and 'social_tco' in diesel_results):
        # Social TCO ratio
        social_tco_ratio = bev_results['social_tco']['social_tco_lifetime'] / diesel_results['social_tco']['social_tco_lifetime']
        
        # Social abatement cost
        if emission_savings > 0:
            social_abatement_cost = (bev_results['social_tco']['social_tco_lifetime'] - diesel_results['social_tco']['social_tco_lifetime']) / (emission_savings / 1000)
    
    # Externality savings
    externality_savings = 0
    if ('externalities' in bev_results and 'externalities' in diesel_results):
        externality_savings = diesel_results['externalities']['lifetime_externality_cost'] - bev_results['externalities']['lifetime_externality_cost']
    
    return {
        'upfront_cost_difference': upfront_diff,
        'annual_operating_savings': annual_savings,
        'price_parity_year': price_parity_year,
        'emission_savings_lifetime': emission_savings,
        'bev_to_diesel_tco_ratio': tco_ratio,
        'abatement_cost': abatement_cost,
        'social_tco_ratio': social_tco_ratio,
        'social_abatement_cost': social_abatement_cost,
        'externality_savings_lifetime': externality_savings
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
    if vehicle_data['vehicle_drivetrain'] != Drivetrain.BEV:
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

def perform_sensitivity_analysis(
    parameter_name,
    parameter_range,
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
    charging_mix=None,
    apply_incentives=True
):
    """
    Perform sensitivity analysis by recalculating TCO metrics for different parameter values
    
    Args:
        parameter_name: Name of the parameter to analyze
        parameter_range: Range of values to test for the parameter
        bev_vehicle_data: BEV vehicle data
        diesel_vehicle_data: Diesel vehicle data
        (other parameters): All other parameters needed for TCO calculations
        
    Returns:
        A list of dictionaries containing TCO metrics for each parameter value
    """
    results = []
    
    # Make copies of original parameters that might be modified
    financial_params_copy = financial_params.copy()
    battery_params_copy = battery_params.copy()
    
    # Cycle through each value in the parameter range
    for param_value in parameter_range:
        # Update parameters based on which parameter is being analyzed
        if parameter_name == "Annual Distance (km)":
            current_annual_kms = param_value
            current_diesel_price = financial_params[
                financial_params['finance_description'] == 'diesel_price'
            ].iloc[0]['default_value']
            current_discount_rate = discount_rate
            current_truck_life_years = truck_life_years
            current_charging_mix = charging_mix
            
        elif parameter_name == "Diesel Price ($/L)":
            current_annual_kms = annual_kms
            current_diesel_price = param_value
            current_discount_rate = discount_rate
            current_truck_life_years = truck_life_years
            current_charging_mix = charging_mix
            
            # Update diesel price in financial params copy
            financial_params_copy.loc[
                financial_params_copy['finance_description'] == 'diesel_price', 'default_value'
            ] = param_value
            
        elif parameter_name == "Vehicle Lifetime (years)":
            current_annual_kms = annual_kms
            current_diesel_price = financial_params[
                financial_params['finance_description'] == 'diesel_price'
            ].iloc[0]['default_value']
            current_discount_rate = discount_rate
            current_truck_life_years = param_value
            current_charging_mix = charging_mix
            
        elif parameter_name == "Discount Rate (%)":
            current_annual_kms = annual_kms
            current_diesel_price = financial_params[
                financial_params['finance_description'] == 'diesel_price'
            ].iloc[0]['default_value']
            current_discount_rate = param_value / 100  # Convert percentage to decimal
            current_truck_life_years = truck_life_years
            current_charging_mix = charging_mix
            
        elif parameter_name == "Electricity Price ($/kWh)":
            current_annual_kms = annual_kms
            current_diesel_price = financial_params[
                financial_params['finance_description'] == 'diesel_price'
            ].iloc[0]['default_value']
            current_discount_rate = discount_rate
            current_truck_life_years = truck_life_years
            
            # For electricity price, we'll need to create a modified charging options table with adjusted prices
            modified_charging_options = charging_options.copy()
            # Apply the same percentage change to all charging options
            base_price = charging_options[charging_options['charging_id'] == selected_charging].iloc[0]['per_kwh_price']
            for idx in modified_charging_options.index:
                original_price = charging_options.loc[idx, 'per_kwh_price']
                modified_charging_options.loc[idx, 'per_kwh_price'] = param_value * (original_price / base_price)
            
            # Use the original charging mix but with modified prices
            current_charging_mix = charging_mix
            
        else:
            # Unsupported parameter
            continue
        
        # Calculate energy costs for BEV and diesel
        if parameter_name == "Electricity Price ($/kWh)":
            # Use modified charging options
            bev_energy_cost_per_km = calculate_energy_costs(
                bev_vehicle_data,
                bev_fees,
                modified_charging_options,  # Use modified prices
                financial_params_copy,
                selected_charging,
                current_charging_mix
            )
        else:
            # Use original charging options
            bev_energy_cost_per_km = calculate_energy_costs(
                bev_vehicle_data,
                bev_fees,
                charging_options,
                financial_params_copy,
                selected_charging,
                current_charging_mix
            )
        
        diesel_energy_cost_per_km = calculate_energy_costs(
            diesel_vehicle_data,
            diesel_fees,
            charging_options,
            financial_params_copy,
            selected_charging
        )
        
        # Calculate annual costs
        bev_annual_costs = calculate_annual_costs(
            bev_vehicle_data,
            bev_fees,
            bev_energy_cost_per_km,
            current_annual_kms,
            incentives,
            apply_incentives
        )
        
        diesel_annual_costs = calculate_annual_costs(
            diesel_vehicle_data,
            diesel_fees,
            diesel_energy_cost_per_km,
            current_annual_kms,
            incentives,
            apply_incentives
        )
        
        # Calculate emissions
        bev_emissions = calculate_emissions(
            bev_vehicle_data,
            emission_factors,
            current_annual_kms,
            current_truck_life_years
        )
        
        diesel_emissions = calculate_emissions(
            diesel_vehicle_data,
            emission_factors,
            current_annual_kms,
            current_truck_life_years
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
        
        # Extract financial parameters for residual value calculation
        initial_depreciation = financial_params[
            financial_params['finance_description'] == 'initial_depreciation_percent'
        ].iloc[0]['default_value']
        
        annual_depreciation = financial_params[
            financial_params['finance_description'] == 'annual_depreciation_percent'
        ].iloc[0]['default_value']
        
        # Calculate residual values
        bev_residual = calculate_residual_value(
            bev_vehicle_data,
            current_truck_life_years,
            initial_depreciation,
            annual_depreciation
        )
        
        diesel_residual = calculate_residual_value(
            diesel_vehicle_data,
            current_truck_life_years,
            initial_depreciation,
            annual_depreciation
        )
        
        # Calculate battery replacement
        bev_battery_replacement = calculate_battery_replacement(
            bev_vehicle_data,
            battery_params_copy,
            current_truck_life_years,
            current_discount_rate
        )
        
        # Calculate NPV of annual costs
        bev_npv_annual = calculate_npv(
            bev_annual_costs['annual_operating_cost'],
            current_discount_rate,
            current_truck_life_years
        )
        
        diesel_npv_annual = calculate_npv(
            diesel_annual_costs['annual_operating_cost'],
            current_discount_rate,
            current_truck_life_years
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
            current_annual_kms,
            current_truck_life_years
        )
        
        diesel_tco = calculate_tco(
            diesel_vehicle_data,
            diesel_fees,
            diesel_annual_costs,
            diesel_acquisition,
            diesel_residual,
            0,  # No battery replacement for diesel
            diesel_npv_annual,
            current_annual_kms,
            current_truck_life_years
        )
        
        # Get selected infrastructure option
        selected_infrastructure_data = infrastructure_options[
            infrastructure_options['infrastructure_id'] == selected_infrastructure
        ].iloc[0]
        
        # Calculate charging requirements
        bev_charging_requirements = calculate_charging_requirements(
            bev_vehicle_data,
            current_annual_kms,
            selected_infrastructure_data
        )
        
        # Calculate infrastructure costs
        infrastructure_costs = calculate_infrastructure_costs(
            selected_infrastructure_data,
            current_truck_life_years,
            current_discount_rate,
            fleet_size
        )
        
        # Apply infrastructure incentives
        infrastructure_costs_with_incentives = apply_infrastructure_incentives(
            infrastructure_costs,
            incentives,
            apply_incentives
        )
        
        # Integrate infrastructure costs with BEV TCO
        bev_tco_with_infrastructure = integrate_infrastructure_with_tco(
            bev_tco,
            infrastructure_costs_with_incentives,
            apply_incentives
        )
        
        # Store results for this parameter value
        result = {
            'parameter_value': param_value,
            'bev': {
                'tco_per_km': bev_tco_with_infrastructure['tco_per_km'],
                'tco_lifetime': bev_tco_with_infrastructure['tco_lifetime'],
                'annual_operating_cost': bev_annual_costs['annual_operating_cost'],
            },
            'diesel': {
                'tco_per_km': diesel_tco['tco_per_km'],
                'tco_lifetime': diesel_tco['tco_lifetime'],
                'annual_operating_cost': diesel_annual_costs['annual_operating_cost'],
            }
        }
        
        results.append(result)
    
    return results

def calculate_tornado_data(
    bev_results,
    diesel_results,
    financial_params,
    battery_params,
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
    charging_mix=None,
    apply_incentives=True
):
    """
    Calculate sensitivity data for multiple parameters to create a tornado chart
    
    Args:
        bev_results: Base BEV results
        diesel_results: Base Diesel results
        (other parameters): All parameters needed for sensitivity calculations
        
    Returns:
        Dictionary containing base TCO and impact of each parameter
    """
    # Extract vehicle data
    bev_vehicle_data = bev_results['vehicle_data']
    diesel_vehicle_data = diesel_results['vehicle_data']
    
    # Extract fees - get them from the results instead of setting to None
    bev_fees = bev_results.get('fees', None)
    diesel_fees = diesel_results.get('fees', None)
    
    # Base TCO per km
    base_tco = bev_results['tco']['tco_per_km']
    
    # Define parameter variations (typically ±20% or meaningful ranges)
    sensitivity_data = {
        "Annual Distance (km)": {
            "range": [annual_kms * 0.5, annual_kms * 1.5],
            "variation": 0.5  # ±50%
        },
        "Diesel Price ($/L)": {
            "range": [
                financial_params[financial_params['finance_description'] == 'diesel_price'].iloc[0]['default_value'] * 0.8,
                financial_params[financial_params['finance_description'] == 'diesel_price'].iloc[0]['default_value'] * 1.2
            ],
            "variation": 0.2  # ±20%
        },
        "Vehicle Lifetime (years)": {
            "range": [max(1, truck_life_years - 3), truck_life_years + 3],
            "variation": 3  # ±3 years
        },
        "Discount Rate (%)": {
            "range": [max(0.5, discount_rate * 100 - 3), discount_rate * 100 + 3],
            "variation": 3  # ±3 percentage points
        }
    }
    
    # For electricity price, we need to handle it differently
    base_electricity_price = charging_options[charging_options['charging_id'] == selected_charging].iloc[0]['per_kwh_price']
    if 'weighted_electricity_price' in bev_results:
        base_electricity_price = bev_results['weighted_electricity_price']
        
    sensitivity_data["Electricity Price ($/kWh)"] = {
        "range": [base_electricity_price * 0.8, base_electricity_price * 1.2],
        "variation": 0.2  # ±20%
    }
    
    # Calculate impacts for each parameter
    impacts = {}
    
    # If fees are not available, we can't run the tornado analysis
    if bev_fees is None or diesel_fees is None:
        raise ValueError("Vehicle fees data is required for tornado chart analysis")
    
    for param_name, param_info in sensitivity_data.items():
        param_range = param_info["range"]
        
        # Calculate TCO for min and max values
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
            apply_incentives
        )
        
        # Calculate impact on TCO
        min_impact = results[0]['bev']['tco_per_km'] - base_tco
        max_impact = results[1]['bev']['tco_per_km'] - base_tco
        
        impacts[param_name] = {
            "min_impact": min_impact,
            "max_impact": max_impact,
        }
    
    return {
        "base_tco": base_tco,
        "impacts": impacts
    }

def prepare_externality_comparison(bev_externalities, diesel_externalities):
    """
    Prepare externality data for visualization comparison between BEV and diesel
    
    Args:
        bev_externalities: Externality metrics for BEV
        diesel_externalities: Externality metrics for diesel
        
    Returns:
        Dictionary with processed data for visualization
    """
    # Extract breakdowns
    bev_breakdown = bev_externalities.get('breakdown', {})
    diesel_breakdown = diesel_externalities.get('breakdown', {})
    
    # Combine all pollutant types
    all_pollutants = set(bev_breakdown.keys()) | set(diesel_breakdown.keys())
    
    # Prepare comparison data
    comparison_data = []
    for pollutant in all_pollutants:
        bev_cost = bev_breakdown.get(pollutant, {}).get('cost_per_km', 0)
        diesel_cost = diesel_breakdown.get(pollutant, {}).get('cost_per_km', 0)
        savings = diesel_cost - bev_cost
        savings_percent = (savings / diesel_cost * 100) if diesel_cost > 0 else 0
        
        comparison_data.append({
            'pollutant_type': pollutant,
            'bev_cost_per_km': bev_cost,
            'diesel_cost_per_km': diesel_cost,
            'savings_per_km': savings,
            'savings_percent': savings_percent
        })
    
    # Sort by savings amount (highest first)
    comparison_data.sort(key=lambda x: x['savings_per_km'], reverse=True)
    
    # Calculate totals
    bev_total = bev_externalities.get('externality_per_km', 0)
    diesel_total = diesel_externalities.get('externality_per_km', 0)
    total_savings = diesel_total - bev_total
    total_savings_percent = (total_savings / diesel_total * 100) if diesel_total > 0 else 0
    
    return {
        'breakdown': comparison_data,
        'bev_total': bev_total,
        'diesel_total': diesel_total,
        'total_savings': total_savings,
        'total_savings_percent': total_savings_percent
    }

def calculate_social_benefit_metrics(bev_results, diesel_results, annual_kms, truck_life_years, discount_rate):
    """
    Calculate social benefit-cost ratio and payback period for BEV
    
    Args:
        bev_results: Results dictionary for BEV
        diesel_results: Results dictionary for diesel
        annual_kms: Annual distance traveled
        truck_life_years: Vehicle service life in years
        discount_rate: Discount rate for NPV calculations
        
    Returns:
        Dictionary with social benefit metrics
    """
    # Calculate the upfront cost difference (BEV premium)
    bev_premium = bev_results['acquisition_cost'] - diesel_results['acquisition_cost']
    
    # Get annual operating cost savings (diesel minus BEV)
    annual_operating_savings = diesel_results['annual_costs']['annual_operating_cost'] - bev_results['annual_costs']['annual_operating_cost']
    
    # Get annual externality savings
    annual_externality_savings = 0
    if 'externalities' in bev_results and 'externalities' in diesel_results:
        annual_externality_savings = diesel_results['externalities']['annual_externality_cost'] - bev_results['externalities']['annual_externality_cost']
    
    # Total annual benefits (operating + externality savings)
    total_annual_benefits = annual_operating_savings + annual_externality_savings
    
    # Calculate NPV of benefits
    npv_benefits = calculate_npv(total_annual_benefits, discount_rate, truck_life_years)
    
    # Calculate social benefit-cost ratio
    # BCR = NPV of benefits / upfront premium
    if bev_premium > 0:
        social_benefit_cost_ratio = npv_benefits / bev_premium
    else:
        # If BEV costs less upfront than diesel, the BCR is infinite (or very large)
        social_benefit_cost_ratio = float('inf')
    
    # Calculate social payback period (in years)
    # This is when cumulative discounted benefits exceed the upfront premium
    if total_annual_benefits > 0:
        # Simple payback period (not considering discount rate)
        simple_payback_period = bev_premium / total_annual_benefits
        
        # Discounted payback period calculation
        cumulative_benefits = 0
        social_payback_period = truck_life_years  # Default to max lifetime
        
        for year in range(1, truck_life_years + 1):
            annual_benefit_discounted = total_annual_benefits / ((1 + discount_rate) ** year)
            cumulative_benefits += annual_benefit_discounted
            
            if cumulative_benefits >= bev_premium:
                # Linear interpolation for more precise payback period
                if year > 1:
                    prev_year_benefits = cumulative_benefits - annual_benefit_discounted
                    fraction = (bev_premium - prev_year_benefits) / annual_benefit_discounted
                    social_payback_period = year - 1 + fraction
                else:
                    social_payback_period = bev_premium / annual_benefit_discounted
                break
    else:
        simple_payback_period = float('inf')
        social_payback_period = float('inf')
    
    return {
        'bev_premium': bev_premium,
        'annual_operating_savings': annual_operating_savings,
        'annual_externality_savings': annual_externality_savings,
        'total_annual_benefits': total_annual_benefits,
        'npv_benefits': npv_benefits,
        'social_benefit_cost_ratio': social_benefit_cost_ratio,
        'simple_payback_period': simple_payback_period,
        'social_payback_period': social_payback_period
    }

def calculate_payload_penalty_costs(bev_results, diesel_results, financial_params):
    """
    Calculate the economic impact of reduced payload capacity in BEV trucks
    
    Args:
        bev_results: Results dictionary for the BEV vehicle
        diesel_results: Results dictionary for the diesel vehicle
        financial_params: Financial parameters dataframe
        
    Returns:
        Dictionary containing various payload penalty metrics
    """
    # Extract payload capacities
    bev_payload = bev_results['vehicle_data']['payload_t']
    diesel_payload = diesel_results['vehicle_data']['payload_t']
    
    # Calculate payload difference
    payload_difference = diesel_payload - bev_payload
    payload_difference_percentage = (payload_difference / diesel_payload) * 100 if diesel_payload > 0 else 0
    
    # Only proceed if BEV has lower payload
    if payload_difference <= 0:
        return {
            'has_penalty': False,
            'payload_difference': payload_difference,
            'payload_difference_percentage': payload_difference_percentage
        }
    
    # Get annual distance and years
    annual_kms = bev_results.get('annual_kms', 0)
    truck_life_years = bev_results.get('truck_life_years', 0)
    
    # Calculate additional trips required
    trips_multiplier = diesel_payload / bev_payload if bev_payload > 0 else 1
    additional_trips_percentage = (trips_multiplier - 1) * 100
    
    # Get financial parameters
    freight_value_per_tonne = financial_params[
        financial_params['finance_description'] == 'freight_value_per_tonne'
    ].iloc[0]['default_value'] if 'freight_value_per_tonne' in financial_params['finance_description'].values else 120
    
    driver_cost_hourly = financial_params[
        financial_params['finance_description'] == 'driver_cost_hourly'
    ].iloc[0]['default_value'] if 'driver_cost_hourly' in financial_params['finance_description'].values else 35
    
    avg_trip_distance = financial_params[
        financial_params['finance_description'] == 'avg_trip_distance'
    ].iloc[0]['default_value'] if 'avg_trip_distance' in financial_params['finance_description'].values else 100
    
    avg_loadunload_time = financial_params[
        financial_params['finance_description'] == 'avg_loadunload_time'
    ].iloc[0]['default_value'] if 'avg_loadunload_time' in financial_params['finance_description'].values else 1
    
    # Calculate economic impacts
    
    # 1. Fleet expansion approach - how many more BEVs needed for same total capacity
    fleet_ratio = diesel_payload / bev_payload if bev_payload > 0 else 1
    additional_bevs_needed_per_diesel = fleet_ratio - 1
    
    # 2. Additional operating costs due to more trips
    # Assume linear relationship between trips and costs, excluding acquisition
    additional_operational_cost_annual = (trips_multiplier - 1) * bev_results['annual_costs']['annual_operating_cost']
    additional_operational_cost_lifetime = additional_operational_cost_annual * truck_life_years
    
    # 3. Additional driver hours (assuming average speed and load/unload time)
    avg_speed_kmh = 60  # Assume 60 km/h average speed
    
    baseline_driving_hours = annual_kms / avg_speed_kmh
    baseline_trips = annual_kms / avg_trip_distance
    baseline_loadunload_hours = baseline_trips * avg_loadunload_time
    
    # Total baseline hours
    baseline_total_hours = baseline_driving_hours + baseline_loadunload_hours
    
    # Additional hours due to more trips
    additional_hours_annual = baseline_total_hours * (trips_multiplier - 1)
    additional_labour_cost_annual = additional_hours_annual * driver_cost_hourly
    additional_labour_cost_lifetime = additional_labour_cost_annual * truck_life_years
    
    # 4. Opportunity cost (revenue potential lost)
    lost_carrying_capacity_annual = payload_difference * baseline_trips
    opportunity_cost_annual = lost_carrying_capacity_annual * freight_value_per_tonne
    opportunity_cost_lifetime = opportunity_cost_annual * truck_life_years
    
    # 5. Adjusted TCO metrics
    # TCO per effective tonne-km
    effective_payload_ratio = bev_payload / diesel_payload
    bev_tco_per_effective_tonnekm = bev_results['tco']['tco_per_tonne_km'] / effective_payload_ratio
    
    # Total adjusted lifetime TCO
    bev_adjusted_lifetime_tco = bev_results['tco']['npv_total_cost'] + additional_operational_cost_lifetime
    
    # Return all calculated metrics
    return {
        'has_penalty': True,
        'payload_difference': payload_difference,
        'payload_difference_percentage': payload_difference_percentage,
        'trips_multiplier': trips_multiplier,
        'additional_trips_percentage': additional_trips_percentage,
        'fleet_ratio': fleet_ratio,
        'additional_bevs_needed_per_diesel': additional_bevs_needed_per_diesel,
        'additional_operational_cost_annual': additional_operational_cost_annual,
        'additional_operational_cost_lifetime': additional_operational_cost_lifetime,
        'additional_hours_annual': additional_hours_annual,
        'additional_labour_cost_annual': additional_labour_cost_annual,
        'additional_labour_cost_lifetime': additional_labour_cost_lifetime,
        'lost_carrying_capacity_annual': lost_carrying_capacity_annual,
        'opportunity_cost_annual': opportunity_cost_annual,
        'opportunity_cost_lifetime': opportunity_cost_lifetime,
        'bev_tco_per_effective_tonnekm': bev_tco_per_effective_tonnekm,
        'bev_adjusted_lifetime_tco': bev_adjusted_lifetime_tco
    }

def perform_externality_sensitivity(
    bev_results, 
    diesel_results, 
    externalities_data, 
    annual_kms, 
    truck_life_years, 
    discount_rate, 
    sensitivity_range=[-50, 0, 50, 100]
):
    """
    Perform sensitivity analysis by adjusting externality costs
    
    Args:
        bev_results: Results dictionary for BEV
        diesel_results: Results dictionary for diesel
        externalities_data: Externality data
        annual_kms: Annual distance traveled
        truck_life_years: Vehicle service life in years
        discount_rate: Discount rate for NPV calculations
        sensitivity_range: List of percentage changes to apply to externality costs
        
    Returns:
        Dictionary with sensitivity analysis results
    """
    results = []
    
    # Get original externality data
    bev_vehicle_data = bev_results['vehicle_data']
    diesel_vehicle_data = diesel_results['vehicle_data']
    
    # Get original TCO values
    original_bev_tco = bev_results['tco']['tco_per_km']
    original_diesel_tco = diesel_results['tco']['tco_per_km']
    
    # Get original social TCO values
    if 'social_tco' in bev_results and 'social_tco' in diesel_results:
        original_bev_social_tco = bev_results['social_tco']['social_tco_per_km']
        original_diesel_social_tco = diesel_results['social_tco']['social_tco_per_km']
    else:
        original_bev_social_tco = original_bev_tco
        original_diesel_social_tco = original_diesel_tco
    
    for percent_change in sensitivity_range:
        # Create modified externality data with the percentage change
        modified_externalities_data = externalities_data.copy()
        modified_externalities_data['cost_per_km'] = externalities_data['cost_per_km'] * (1 + percent_change / 100)
        
        # Recalculate externalities
        bev_externalities = calculate_externalities(
            bev_vehicle_data, 
            modified_externalities_data, 
            annual_kms, 
            truck_life_years, 
            discount_rate
        )
        
        diesel_externalities = calculate_externalities(
            diesel_vehicle_data, 
            modified_externalities_data, 
            annual_kms, 
            truck_life_years, 
            discount_rate
        )
        
        # Recalculate social TCO
        bev_social_tco = calculate_social_tco(
            bev_results['tco'], 
            bev_externalities
        )
        
        diesel_social_tco = calculate_social_tco(
            diesel_results['tco'], 
            diesel_externalities
        )
        
        # Calculate comparative metrics
        abatement_cost = 0
        emission_savings = diesel_results['emissions']['lifetime_emissions'] - bev_results['emissions']['lifetime_emissions']
        if emission_savings > 0:
            abatement_cost = (bev_social_tco['social_tco_lifetime'] - diesel_social_tco['social_tco_lifetime']) / (emission_savings / 1000)
        
        # Calculate social benefit metrics
        social_benefit_metrics = calculate_social_benefit_metrics(
            {**bev_results, 'externalities': bev_externalities, 'social_tco': bev_social_tco},
            {**diesel_results, 'externalities': diesel_externalities, 'social_tco': diesel_social_tco},
            annual_kms,
            truck_life_years,
            discount_rate
        )
        
        # Store results
        results.append({
            'percent_change': percent_change,
            'bev_externality_per_km': bev_externalities['externality_per_km'],
            'diesel_externality_per_km': diesel_externalities['externality_per_km'],
            'bev_tco_per_km': original_bev_tco,  # This doesn't change
            'diesel_tco_per_km': original_diesel_tco,  # This doesn't change
            'bev_social_tco_per_km': bev_social_tco['social_tco_per_km'],
            'diesel_social_tco_per_km': diesel_social_tco['social_tco_per_km'],
            'social_abatement_cost': abatement_cost,
            'social_benefit_cost_ratio': social_benefit_metrics['social_benefit_cost_ratio'],
            'social_payback_period': social_benefit_metrics['social_payback_period']
        })
    
    return results
