from __future__ import annotations

"""Carbon-price / externality cost sensitivity helper extracted from monolith."""

from typing import Any, Dict, List

from tco_app.domain.externalities import calculate_externalities, calculate_social_tco
from tco_app.src import pd

__all__ = ["perform_externality_sensitivity"]


def perform_externality_sensitivity(
    bev_results: Dict[str, Any],
    diesel_results: Dict[str, Any],
    externalities_data: pd.DataFrame,
    annual_kms: int,
    truck_life_years: int,
    discount_rate: float,
    sensitivity_range: List[int] | None = None,
) -> List[Dict[str, Any]]:
    if sensitivity_range is None:
        sensitivity_range = [-50, 0, 50, 100]

    results: List[Dict[str, Any]] = []
    bev_vehicle_data = bev_results["vehicle_data"]
    diesel_vehicle_data = diesel_results["vehicle_data"]
    original_bev_tco = bev_results["tco"]["tco_per_km"]
    original_diesel_tco = diesel_results["tco"]["tco_per_km"]

    for pct in sensitivity_range:
        modified_ext = externalities_data.copy()
        modified_ext["cost_per_km"] = externalities_data["cost_per_km"] * (
            1 + pct / 100
        )

        bev_ext = calculate_externalities(
            bev_vehicle_data,
            modified_ext,
            annual_kms,
            truck_life_years,
            discount_rate,
        )
        diesel_ext = calculate_externalities(
            diesel_vehicle_data,
            modified_ext,
            annual_kms,
            truck_life_years,
            discount_rate,
        )

        bev_social = calculate_social_tco(bev_results["tco"], bev_ext)
        diesel_social = calculate_social_tco(diesel_results["tco"], diesel_ext)

        emission_savings = (
            diesel_results["emissions"]["lifetime_emissions"]
            - bev_results["emissions"]["lifetime_emissions"]
        )
        abatement_cost = (
            (
                (
                    bev_social["social_tco_lifetime"]
                    - diesel_social["social_tco_lifetime"]
                )
                / (emission_savings / 1000)
            )
            if emission_savings > 0
            else float("inf")
        )

        results.append(
            {
                "percent_change": pct,
                "bev_externality_per_km": bev_ext["externality_per_km"],
                "diesel_externality_per_km": diesel_ext["externality_per_km"],
                "bev_tco_per_km": original_bev_tco,
                "diesel_tco_per_km": original_diesel_tco,
                "bev_social_tco_per_km": bev_social["social_tco_per_km"],
                "diesel_social_tco_per_km": diesel_social["social_tco_per_km"],
                "social_abatement_cost": abatement_cost,
            }
        )

    return results
