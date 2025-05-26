from __future__ import annotations

from tco_app.src.constants import DataColumns
from tco_app.src.utils.safe_operations import safe_division
from tco_app.src.config import UNIT_CONVERSIONS

"""Comparative BEV-vs-Diesel KPI helper, extracted to its own file."""

import math
from typing import Any, Dict, List

from tco_app.services.dtos import ComparisonResult


def compute_price_parity(
    bev_cumulative: List[float], diesel_cumulative: List[float], years: List[int]
) -> float:
    """Return the interpolated price parity year."""

    price_parity_year = math.inf
    for i in range(len(years) - 1):
        if (bev_cumulative[i] - diesel_cumulative[i]) * (
            bev_cumulative[i + 1] - diesel_cumulative[i + 1]
        ) <= 0:
            delta_bev = bev_cumulative[i + 1] - bev_cumulative[i]
            delta_diesel = diesel_cumulative[i + 1] - diesel_cumulative[i]
            if delta_bev != delta_diesel:
                t = (diesel_cumulative[i] - bev_cumulative[i]) / (
                    delta_bev - delta_diesel
                )
                price_parity_year = years[i] + t
                break

    return price_parity_year


def calculate_comparative_metrics_from_dto(
    comparison_result: ComparisonResult
) -> Dict[str, Any]:
    """Return parity & abatement KPIs for BEV vs diesel using DTOs.
    
    This is the modernised version that works directly with DTOs.
    """
    # Extract base (BEV) and comparison (Diesel) results
    bev_result = comparison_result.base_vehicle_result
    diesel_result = comparison_result.comparison_vehicle_result
    
    # Get annual_kms and truck_life_years from ComparisonResult
    annual_kms = comparison_result.annual_kms or 100000  # Default fallback
    truck_life_years = comparison_result.truck_life_years or 10  # Default fallback
    
    # Calculate annual savings
    annual_savings = diesel_result.annual_operating_cost - bev_result.annual_operating_cost
    
    # Calculate upfront cost difference
    bev_initial_cost = bev_result.acquisition_cost
    diesel_initial_cost = diesel_result.acquisition_cost
    
    # Add infrastructure cost per vehicle if present
    if bev_result.infrastructure_costs_breakdown:
        infra_price = (
            bev_result.infrastructure_costs_breakdown.get(
                "infrastructure_price_with_incentives"
            )
            or bev_result.infrastructure_costs_breakdown.get("initial_capital_with_incentives")
            or bev_result.infrastructure_costs_breakdown.get("initial_capital", 0)
        )
        fleet_size = bev_result.infrastructure_costs_breakdown.get("fleet_size", 1) or 1
        bev_initial_cost += infra_price / float(fleet_size)
    
    upfront_diff = bev_initial_cost - diesel_initial_cost
    
    # Calculate emission savings
    emission_savings = diesel_result.lifetime_emissions_co2e - bev_result.lifetime_emissions_co2e
    
    # Calculate abatement cost
    bev_npv = bev_result.tco_total_lifetime
    diesel_npv = diesel_result.tco_total_lifetime
    abatement_cost = (
        ((bev_npv - diesel_npv) / (emission_savings / UNIT_CONVERSIONS.KG_TO_TONNES))
        if emission_savings > 0
        else float("inf")
    )
    
    # Calculate BEV to diesel ratio
    bev_to_diesel_ratio = (
        safe_division(bev_npv, diesel_npv, context="bev_npv/diesel_npv calculation")
        if diesel_npv
        else float("inf")
    )
    
    # Build cumulative cost arrays for price parity calculation
    years = list(range(1, truck_life_years + 1))
    
    # Initialize cumulative costs with upfront costs
    bev_cum: List[float] = [bev_initial_cost]
    diesel_cum: List[float] = [diesel_initial_cost]
    
    # Add annual operating costs year by year
    for year in range(1, truck_life_years):
        bev_annual = bev_result.annual_operating_cost
        diesel_annual = diesel_result.annual_operating_cost
        
        # Add battery replacement cost if applicable (not available in current DTOs)
        # This would need to be stored in the DTO for full accuracy
        
        # Add infrastructure maintenance if present
        if bev_result.infrastructure_costs_breakdown:
            infra = bev_result.infrastructure_costs_breakdown
            infra_maint = infra.get("annual_maintenance", 0) / infra.get("fleet_size", 1)
            bev_annual += infra_maint
            
            # Check for infrastructure replacement
            service_life = infra.get("service_life_years", 15)
            if year % service_life == 0 and year < truck_life_years:
                infra_rep = (
                    infra.get("infrastructure_price_with_incentives")
                    or infra.get("initial_capital_with_incentives")
                    or infra.get("initial_capital", 0)
                ) / infra.get("fleet_size", 1)
                bev_annual += infra_rep
        
        bev_cum.append(bev_cum[-1] + bev_annual)
        diesel_cum.append(diesel_cum[-1] + diesel_annual)
    
    # Subtract residual values from final year
    bev_cum[-1] -= bev_result.residual_value
    diesel_cum[-1] -= diesel_result.residual_value
    
    # Calculate price parity year
    price_parity_year = compute_price_parity(bev_cum, diesel_cum, years)
    
    # Compose response
    response = {
        "upfront_cost_difference": upfront_diff,
        "annual_operating_savings": annual_savings,
        "price_parity_year": price_parity_year,
        "emission_savings_lifetime": emission_savings,
        "abatement_cost": abatement_cost,
        "bev_to_diesel_tco_ratio": bev_to_diesel_ratio,
    }
    
    return response
