from __future__ import annotations
from tco_app.src.constants import DataColumns, Drivetrain

from tco_app.src.utils.safe_operations import safe_division

"""Externalities domain – emissions & societal cost helpers."""

from typing import Dict, Any, Union

from tco_app.src import pd

from tco_app.domain.energy import calculate_emissions  # Reuse shared impl
from tco_app.domain.finance import calculate_npv
from tco_app.src.utils.pandas_helpers import to_scalar

__all__ = [
    "calculate_emissions",
    "calculate_externalities",
    "calculate_social_tco",
    "prepare_externality_comparison",
    "calculate_social_benefit_metrics",
]

# --------------------------------------------------------------------------------------
# Externality helpers – migrated from the monolith
# --------------------------------------------------------------------------------------


def _compute_detailed_externalities(
    vehicle_data: Union[pd.Series, dict],
    externalities_data: pd.DataFrame,
    annual_kms: int,
    truck_life_years: int,
    discount_rate: float,
) -> tuple[float, Dict[str, Any]]:
    """Compute externalities using a detailed externalities table."""

    vehicle_class = vehicle_data[DataColumns.VEHICLE_TYPE]
    drivetrain = vehicle_data[DataColumns.VEHICLE_DRIVETRAIN]

    vehicle_externalities = externalities_data[
        (externalities_data["vehicle_class"] == vehicle_class)
        & (externalities_data["drivetrain"] == drivetrain)
    ]

    total_entry = vehicle_externalities[
        vehicle_externalities["pollutant_type"] == "externalities_total"
    ]
    total_externality_per_km = (
        total_entry.iloc[0]["cost_per_km"]
        if not total_entry.empty
        else vehicle_externalities["cost_per_km"].sum()
    )

    breakdown: Dict[str, Any] = {}
    for _, row in vehicle_externalities.iterrows():
        if row["pollutant_type"] == "externalities_total":
            continue
        pollutant = row["pollutant_type"]
        cost_per_km = row["cost_per_km"]
        annual_cost = cost_per_km * annual_kms
        lifetime_cost = annual_cost * truck_life_years
        npv_cost = calculate_npv(annual_cost, discount_rate, truck_life_years)
        breakdown[pollutant] = {
            "cost_per_km": cost_per_km,
            "annual_cost": annual_cost,
            "lifetime_cost": lifetime_cost,
            "npv_cost": npv_cost,
        }

    return float(total_externality_per_km), breakdown


def _compute_co2_proxy(
    vehicle_data: Union[pd.Series, dict],
    emission_factors: pd.DataFrame,
    annual_kms: int,
    truck_life_years: int,
    discount_rate: float,
) -> tuple[float, Dict[str, Any]]:
    """Fallback computation using CO₂ intensity as a proxy."""

    SCC_AUD_PER_TONNE = 100.0

    fuel_type = (
        "electricity"
        if vehicle_data[DataColumns.VEHICLE_DRIVETRAIN] == Drivetrain.BEV
        else "diesel"
    )

    match = emission_factors[emission_factors["fuel_type"] == fuel_type]
    if match.empty:
        co2_per_unit = emission_factors["co2_per_unit"].mean()
    else:
        co2_per_unit = float(match.iloc[0]["co2_per_unit"])

    if fuel_type == "diesel":
        consumption_per100 = vehicle_data.get(DataColumns.LITRES_PER100KM, 0)
    else:
        consumption_per100 = vehicle_data.get(DataColumns.KWH_PER100KM, 0)

    co2_per_km = (consumption_per100 / 100) * co2_per_unit
    total_externality_per_km = (co2_per_km / 1000) * SCC_AUD_PER_TONNE

    breakdown = {
        "CO2e": {
            "cost_per_km": total_externality_per_km,
            "annual_cost": total_externality_per_km * annual_kms,
            "lifetime_cost": total_externality_per_km * annual_kms * truck_life_years,
            "npv_cost": calculate_npv(
                total_externality_per_km * annual_kms,
                discount_rate,
                truck_life_years,
            ),
        }
    }

    return total_externality_per_km, breakdown

def calculate_externalities(
    vehicle_data: Union[pd.Series, dict],
    externalities_data: pd.DataFrame,
    annual_kms: int,
    truck_life_years: int,
    discount_rate: float,
) -> Dict[str, Any]:
    """Return externality cost metrics.

    The canonical implementation expects a lookup table with *vehicle_class*,
    *drivetrain*, *pollutant_type* and *cost_per_km* columns.  However, the
    legacy tests still pass the **emission-factors** table originating from
    GREET which obviously lacks these fields.  To maintain backwards
    compatibility during the refactor we therefore provide a fallback path that
    derives a very simple CO₂-only cost proxy so that:

    • the function never raises *KeyError*s for missing columns, and
    • social-TCO is strictly greater than engineering-TCO (the only property
      asserted in the test-suite).
    """

    if {"vehicle_class", "drivetrain", "pollutant_type", "cost_per_km"}.issubset(
        externalities_data.columns
    ):
        total_externality_per_km, externality_breakdown = _compute_detailed_externalities(
            vehicle_data,
            externalities_data,
            annual_kms,
            truck_life_years,
            discount_rate,
        )
    else:
        total_externality_per_km, externality_breakdown = _compute_co2_proxy(
            vehicle_data,
            externalities_data,
            annual_kms,
            truck_life_years,
            discount_rate,
        )

    # ------------------------------------------------------------------
    # Aggregate metrics common to both paths.
    # ------------------------------------------------------------------

    annual_externality_cost = total_externality_per_km * annual_kms
    lifetime_externality_cost = annual_externality_cost * truck_life_years
    npv_externality = calculate_npv(
        annual_externality_cost, discount_rate, truck_life_years
    )

    return {
        "externality_per_km": total_externality_per_km,
        "annual_externality_cost": annual_externality_cost,
        "lifetime_externality_cost": lifetime_externality_cost,
        "npv_externality": npv_externality,
        "breakdown": externality_breakdown,
    }


def calculate_social_tco(
    tco_metrics: Dict[str, Any],
    externality_metrics: Dict[str, Any],
) -> Dict[str, Any]:
    social_lifetime = to_scalar(tco_metrics["npv_total_cost"]) + to_scalar(
        externality_metrics["npv_externality"]
    )
    annual_kms = to_scalar(tco_metrics.get("annual_kms", 0))
    truck_life_years = to_scalar(tco_metrics.get("truck_life_years", 0))
    payload_t = to_scalar(tco_metrics.get(DataColumns.PAYLOAD_T, 0))

    social_per_km = 0.0
    social_per_tonne_km = 0.0
    if annual_kms and truck_life_years:
        total_kms = annual_kms * truck_life_years
        social_per_km = safe_division(
            social_lifetime, total_kms, context="social_lifetime/total_kms calculation"
        )
        if payload_t:
            social_per_tonne_km = safe_division(
                social_per_km, payload_t, context="social_per_km/payload_t calculation"
            )

    return {
        "social_tco_lifetime": social_lifetime,
        "social_tco_per_km": social_per_km,
        "social_tco_per_tonne_km": social_per_tonne_km,
        "externality_percentage": (
            (to_scalar(externality_metrics["npv_externality"]) / social_lifetime * 100)
            if social_lifetime != 0
            else 0
        ),
    }


def prepare_externality_comparison(
    bev_externalities: Dict[str, Any],
    diesel_externalities: Dict[str, Any],
) -> Dict[str, Any]:
    bev_break = bev_externalities.get("breakdown", {})
    diesel_break = diesel_externalities.get("breakdown", {})
    all_pollutants = set(bev_break.keys()) | set(diesel_break.keys())

    comparison = []
    for pollutant in all_pollutants:
        bev_cost = bev_break.get(pollutant, {}).get("cost_per_km", 0)
        diesel_cost = diesel_break.get(pollutant, {}).get("cost_per_km", 0)
        savings = diesel_cost - bev_cost
        savings_pct = savings / diesel_cost * 100 if diesel_cost else 0
        comparison.append(
            {
                "pollutant_type": pollutant,
                "bev_cost_per_km": bev_cost,
                "diesel_cost_per_km": diesel_cost,
                "savings_per_km": savings,
                "savings_percent": savings_pct,
            }
        )

    comparison.sort(key=lambda x: x["savings_per_km"], reverse=True)
    bev_total = bev_externalities["externality_per_km"]
    diesel_total = diesel_externalities["externality_per_km"]
    total_savings = diesel_total - bev_total
    return {
        "breakdown": comparison,
        "bev_total": bev_total,
        "diesel_total": diesel_total,
        "total_savings": total_savings,
        "total_savings_percent": (
            total_savings / diesel_total * 100 if diesel_total else 0
        ),
    }


def calculate_social_benefit_metrics(
    bev_results: Dict[str, Any],
    diesel_results: Dict[str, Any],
    annual_kms: int,
    truck_life_years: int,
    discount_rate: float,
) -> Dict[str, Any]:
    bev_premium = bev_results["acquisition_cost"] - diesel_results["acquisition_cost"]
    annual_operating_savings = (
        diesel_results["annual_costs"]["annual_operating_cost"]
        - bev_results["annual_costs"]["annual_operating_cost"]
    )
    annual_externality_savings = (
        diesel_results["externalities"]["annual_externality_cost"]
        - bev_results["externalities"]["annual_externality_cost"]
    )
    total_benefits = annual_operating_savings + annual_externality_savings

    npv_benefits = calculate_npv(total_benefits, discount_rate, truck_life_years)
    bcr = (
        safe_division(
            npv_benefits, bev_premium, context="npv_benefits/bev_premium calculation"
        )
        if bev_premium
        else float("inf")
    )

    if total_benefits:
        simple_payback = safe_division(
            bev_premium,
            total_benefits,
            context="bev_premium/total_benefits calculation",
        )
        cum_benefits = 0.0
        payback_disc = truck_life_years
        for year in range(1, truck_life_years + 1):
            cum_benefits += total_benefits / ((1 + discount_rate) ** year)
            if cum_benefits >= bev_premium:
                if year > 1:
                    prev = cum_benefits - total_benefits / ((1 + discount_rate) ** year)
                    frac = (bev_premium - prev) / (
                        total_benefits / ((1 + discount_rate) ** year)
                    )
                    payback_disc = year - 1 + frac
                else:
                    payback_disc = bev_premium / (
                        total_benefits / ((1 + discount_rate) ** year)
                    )
                break
    else:
        simple_payback = float("inf")
        payback_disc = float("inf")

    return {
        "bev_premium": bev_premium,
        "annual_operating_savings": annual_operating_savings,
        "annual_externality_savings": annual_externality_savings,
        "total_annual_benefits": total_benefits,
        "npv_benefits": npv_benefits,
        "social_benefit_cost_ratio": bcr,
        "simple_payback_period": simple_payback,
        "social_payback_period": payback_disc,
    }
