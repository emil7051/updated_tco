from __future__ import annotations
from tco_app.src.constants import DataColumns

from tco_app.src.utils.safe_operations import safe_division

"""Comparative BEV-vs-Diesel KPI helper, extracted to its own file."""

from typing import Any, Dict, List
from tco_app.src.utils.pandas_helpers import to_scalar

import math


def calculate_comparative_metrics(
    bev_results: Dict[str, Any],
    diesel_results: Dict[str, Any],
    annual_kms: int,
    truck_life_years: int,
) -> Dict[str, Any]:
    """Return parity & abatement KPIs for BEV vs diesel (unchanged logic)."""

    upfront_diff = bev_results["acquisition_cost"] - diesel_results["acquisition_cost"]
    annual_savings = (
        diesel_results["annual_costs"]["annual_operating_cost"]
        - bev_results["annual_costs"]["annual_operating_cost"]
    )

    years = list(range(1, truck_life_years + 1))
    bev_cum: List[float] = [bev_results["acquisition_cost"]]
    diesel_cum: List[float] = [diesel_results["acquisition_cost"]]

    if "infrastructure_costs" in bev_results:
        infra_price = (
            bev_results["infrastructure_costs"].get(
                "infrastructure_price_with_incentives"
            )
            or bev_results["infrastructure_costs"][DataColumns.INFRASTRUCTURE_PRICE]
        )

        fleet_size = bev_results["infrastructure_costs"].get("fleet_size", 1) or 1

        # Allocate infrastructure CAPEX on a per-vehicle basis and add to the
        # upfront cash-flow for the BEV.
        bev_cum[0] += infra_price / float(fleet_size)

    for year in range(1, truck_life_years):
        bev_annual = bev_results["annual_costs"]["annual_operating_cost"]
        diesel_annual = diesel_results["annual_costs"]["annual_operating_cost"]

        if bev_results.get("battery_replacement_year") == year:
            bev_annual += bev_results.get("battery_replacement_cost", 0)

        if "infrastructure_costs" in bev_results:
            infra_maint = bev_results["infrastructure_costs"][
                "annual_maintenance"
            ] / bev_results["infrastructure_costs"].get("fleet_size", 1)
            bev_annual += infra_maint
            service_life = bev_results["infrastructure_costs"]["service_life_years"]
            if year % service_life == 0 and year < truck_life_years:
                infra_rep = (
                    bev_results["infrastructure_costs"].get(
                        "infrastructure_price_with_incentives"
                    )
                    or bev_results["infrastructure_costs"][
                        DataColumns.INFRASTRUCTURE_PRICE
                    ]
                ) / bev_results["infrastructure_costs"].get("fleet_size", 1)
                bev_annual += infra_rep

        bev_cum.append(bev_cum[-1] + bev_annual)
        diesel_cum.append(diesel_cum[-1] + diesel_annual)

    bev_cum[-1] -= to_scalar(bev_results["residual_value"])
    diesel_cum[-1] -= to_scalar(diesel_results["residual_value"])

    price_parity_year = math.inf
    for i in range(len(years) - 1):
        if (bev_cum[i] - diesel_cum[i]) * (bev_cum[i + 1] - diesel_cum[i + 1]) <= 0:
            delta_bev = bev_cum[i + 1] - bev_cum[i]
            delta_diesel = diesel_cum[i + 1] - diesel_cum[i]
            if delta_bev != delta_diesel:
                t = (diesel_cum[i] - bev_cum[i]) / (delta_bev - delta_diesel)
                price_parity_year = years[i] + t
                break

    emission_savings = to_scalar(
        diesel_results["emissions"]["lifetime_emissions"]
    ) - to_scalar(bev_results["emissions"]["lifetime_emissions"])
    bev_npv = to_scalar(bev_results["tco"]["npv_total_cost"])
    diesel_npv = to_scalar(diesel_results["tco"]["npv_total_cost"])
    abatement_cost = (
        ((bev_npv - diesel_npv) / (emission_savings / 1000))
        if emission_savings > 0
        else float("inf")
    )

    bev_to_diesel_ratio = (
        safe_division(bev_npv, diesel_npv, context="bev_npv/diesel_npv calculation")
        if diesel_npv
        else float("inf")
    )

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
