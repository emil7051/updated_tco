"""Financial calculations for TCO analysis."""

from __future__ import annotations

import math
from typing import Union

from tco_app.domain.finance_payload import calculate_payload_penalty_costs as _impl
from tco_app.src import PERFORMANCE_CONFIG, Any, Dict, Optional, np, pd
from tco_app.src.constants import DataColumns, Drivetrain
from tco_app.src.utils.finance import calculate_residual_value, cumulative_cost_curve
from tco_app.src.utils.finance import npv_constant as calculate_npv
from tco_app.src.utils.finance import price_parity_year
from tco_app.src.utils.safe_operations import safe_division, safe_iloc_zero

__all__ = [
    "calculate_npv",
    "calculate_npv_optimised",
    "cumulative_cost_curve",
    "price_parity_year",
    "calculate_residual_value",
    "calculate_annual_costs",
    "calculate_acquisition_cost",
    "calculate_tco",
    "compute_infrastructure_npv",
    "calculate_infrastructure_costs",
    "apply_infrastructure_incentives",
    "integrate_infrastructure_with_tco",
    "calculate_payload_penalty_costs",
]


def calculate_npv_optimised(
    annual_cost: float, discount_rate: float, years: int
) -> float:
    """Optimised NPV calculation that uses fast computation for large arrays.

    Args:
            annual_cost: Constant annual cash flow
            discount_rate: Discount rate as decimal
            years: Number of years

    Returns:
            Net present value
    """
    # For small calculations, use the original function
    if years <= PERFORMANCE_CONFIG.NPV_OPTIMIZATION_THRESHOLD:
        return calculate_npv(annual_cost, discount_rate, years)

    # For larger calculations, use optimised version
    try:
        from tco_app.src.utils.calculation_optimisations import fast_npv

        cash_flows = np.full(years, annual_cost)
        return fast_npv(cash_flows, discount_rate)
    except ImportError:
        # Fallback to original if numba not available
        return calculate_npv(annual_cost, discount_rate, years)


# --------------------------------------------------------------------------------------
# Annual & acquisition cost helpers
# --------------------------------------------------------------------------------------


def calculate_annual_costs(
    vehicle_data: Union[pd.Series, dict],
    fees_data: Union[pd.Series, pd.DataFrame],
    energy_cost_per_km: float,
    annual_kms: int,
    incentives_data: Optional[pd.DataFrame] = None,
    apply_incentives: bool = False,
) -> Dict[str, float]:
    # If fees_data is a Series (single row), use it directly
    if isinstance(fees_data, pd.Series):
        maintenance_data = fees_data
    else:
        # If it's a DataFrame, filter by vehicle ID
        maintenance_condition = (
            fees_data[DataColumns.VEHICLE_ID] == vehicle_data[DataColumns.VEHICLE_ID]
        )
        maintenance_data = safe_iloc_zero(
            fees_data, maintenance_condition, context="maintenance data"
        )

    maintenance_per_km = maintenance_data["maintenance_perkm_price"]

    annual_maintenance_cost = maintenance_per_km * annual_kms
    annual_energy_cost = energy_cost_per_km * annual_kms

    registration_annual = maintenance_data["registration_annual_price"]
    insurance_annual = maintenance_data["insurance_annual_price"]

    if (
        apply_incentives
        and incentives_data is not None
        and vehicle_data[DataColumns.VEHICLE_DRIVETRAIN] == Drivetrain.BEV
    ):
        active = incentives_data[
            (incentives_data["incentive_flag"] == 1)
            & (
                (incentives_data["drivetrain"] == Drivetrain.BEV)
                | (incentives_data["drivetrain"] == Drivetrain.ALL)
            )
        ]

        registration_exemption = active[
            active["incentive_type"] == "registration_exemption"
        ]
        if not registration_exemption.empty:
            reg_exemption_condition = pd.Series(
                [True] * len(registration_exemption), index=registration_exemption.index
            )
            reg_exemption_data = safe_iloc_zero(
                registration_exemption,
                reg_exemption_condition,
                context="registration exemption incentive",
            )
            registration_annual *= 1 - reg_exemption_data["incentive_rate"]

        insurance_discount = active[active["incentive_type"] == "insurance_discount"]
        if not insurance_discount.empty:
            insurance_condition = pd.Series(
                [True] * len(insurance_discount), index=insurance_discount.index
            )
            insurance_data = safe_iloc_zero(
                insurance_discount,
                insurance_condition,
                context="insurance discount incentive",
            )
            insurance_annual *= 1 - insurance_data["incentive_rate"]

        electricity_discount = active[
            active["incentive_type"] == "electricity_rate_discount"
        ]
        if not electricity_discount.empty:
            electricity_condition = pd.Series(
                [True] * len(electricity_discount), index=electricity_discount.index
            )
            electricity_data = safe_iloc_zero(
                electricity_discount,
                electricity_condition,
                context="electricity discount incentive",
            )
            annual_energy_cost *= 1 - electricity_data["incentive_rate"]

    annual_operating_cost = (
        annual_energy_cost
        + annual_maintenance_cost
        + registration_annual
        + insurance_annual
    )

    return {
        "annual_energy_cost": annual_energy_cost,
        "annual_maintenance_cost": annual_maintenance_cost,
        "registration_annual": registration_annual,
        "insurance_annual": insurance_annual,
        "annual_operating_cost": annual_operating_cost,
    }


def calculate_acquisition_cost(
    vehicle_data: Union[pd.Series, dict],
    fees_data: Union[pd.Series, pd.DataFrame],
    incentives_data: pd.DataFrame,
    apply_incentives: bool = True,
) -> float:
    msrp = vehicle_data[DataColumns.MSRP_PRICE]

    # Handle fees_data as either Series (already filtered) or DataFrame
    if isinstance(fees_data, pd.Series):
        # If it's already a Series, use it directly
        fees = fees_data
        stamp_duty = fees.get("stamp_duty_price", 0) if not fees.empty else 0
    else:
        # If it's a DataFrame, filter it
        fees_condition = (
            fees_data[DataColumns.VEHICLE_ID] == vehicle_data[DataColumns.VEHICLE_ID]
        )
        fees = safe_iloc_zero(fees_data, fees_condition, context="vehicle fees")
        stamp_duty = fees["stamp_duty_price"]

    acquisition_cost = msrp + stamp_duty

    if (
        apply_incentives
        and vehicle_data[DataColumns.VEHICLE_DRIVETRAIN] == Drivetrain.BEV
    ):
        active = incentives_data[
            (incentives_data["incentive_flag"] == 1)
            & (
                (incentives_data["drivetrain"] == Drivetrain.BEV)
                | (incentives_data["drivetrain"] == Drivetrain.ALL)
            )
        ]

        purchase_rebate = active[active["incentive_type"] == "purchase_rebate_aud"]
        if not purchase_rebate.empty:
            rebate_condition = pd.Series(
                [True] * len(purchase_rebate), index=purchase_rebate.index
            )
            rebate_data = safe_iloc_zero(
                purchase_rebate, rebate_condition, context="purchase rebate incentive"
            )
            acquisition_cost -= rebate_data["incentive_rate"]

        stamp_duty_exemption = active[
            active["incentive_type"] == "stamp_duty_exemption"
        ]
        if not stamp_duty_exemption.empty:
            duty_condition = pd.Series(
                [True] * len(stamp_duty_exemption), index=stamp_duty_exemption.index
            )
            duty_exemption_data = safe_iloc_zero(
                stamp_duty_exemption,
                duty_condition,
                context="stamp duty exemption incentive",
            )
            acquisition_cost -= stamp_duty * duty_exemption_data["incentive_rate"]

    return acquisition_cost


# --------------------------------------------------------------------------------------
# TCO & infrastructure helpers
# --------------------------------------------------------------------------------------


def calculate_tco(
    vehicle_data: Union[pd.Series, dict],
    fees_data: pd.DataFrame,
    annual_costs: Dict[str, float],
    acquisition_cost: float,
    residual_value: float,
    battery_replacement: float,
    npv_annual_cost: float,
    annual_kms: int,
    truck_life_years: int,
) -> Dict[str, float]:
    npv_total_cost = (
        acquisition_cost + npv_annual_cost - residual_value + battery_replacement
    )
    tco_per_km = npv_total_cost / (annual_kms * truck_life_years)
    tco_per_tonne_km = safe_division(
        tco_per_km,
        vehicle_data[DataColumns.PAYLOAD_T],
        context="tco_per_km/payload calculation",
    )

    return {
        "npv_total_cost": npv_total_cost,
        "tco_per_km": tco_per_km,
        "tco_per_tonne_km": tco_per_tonne_km,
        "tco_lifetime": npv_total_cost,
        "tco_annual": safe_division(
            npv_total_cost,
            truck_life_years,
            context="npv_total_cost/truck_life_years calculation",
        ),
    }


def compute_infrastructure_npv(
    price: float,
    service_life: int,
    discount_rate: float,
    truck_life_years: int,
    annual_maintenance: float,
) -> float:
    """Calculate infrastructure NPV over the truck lifetime.

    Args:
        price: Upfront infrastructure cost.
        service_life: Expected service life of the infrastructure in years.
        discount_rate: Discount rate as a decimal.
        truck_life_years: Lifetime of the truck in years.
        annual_maintenance: Annual maintenance cost of the infrastructure.

    Returns:
        Net present value of the infrastructure costs over the truck lifetime.
    """

    replacement_cycles = max(
        1,
        math.ceil(
            safe_division(
                truck_life_years,
                service_life,
                context="truck_life_years/service_life calculation",
            )
        ),
    )

    npv_infra = 0.0
    for cycle in range(replacement_cycles):
        start_year = cycle * service_life
        if start_year >= truck_life_years:
            break

        npv_infra += (
            price if cycle == 0 else price / ((1 + discount_rate) ** start_year)
        )

        years_in_cycle = min(service_life, truck_life_years - start_year)
        for year in range(years_in_cycle):
            current_year = start_year + year + 1
            npv_infra += annual_maintenance / ((1 + discount_rate) ** current_year)

    return npv_infra


def calculate_infrastructure_costs(
    infrastructure_option: Union[pd.Series, dict],
    truck_life_years: int,
    discount_rate: float,
    fleet_size: int = 1,
) -> Dict[str, Any]:
    price = infrastructure_option[DataColumns.INFRASTRUCTURE_PRICE]
    service_life = infrastructure_option["service_life_years"]
    maint_pct = infrastructure_option["maintenance_percent"]

    annual_maintenance = price * maint_pct
    annual_capital = safe_division(
        price, service_life, context="price/service_life calculation"
    )
    total_annual_cost = annual_capital + annual_maintenance
    per_vehicle_annual = safe_division(
        total_annual_cost,
        fleet_size,
        context="total_annual_cost/fleet_size calculation",
    )

    replacement_cycles = max(
        1,
        math.ceil(
            safe_division(
                truck_life_years,
                service_life,
                context="truck_life_years/service_life calculation",
            )
        ),
    )

    npv_infra = compute_infrastructure_npv(
        price,
        service_life,
        discount_rate,
        truck_life_years,
        annual_maintenance,
    )

    npv_per_vehicle = safe_division(
        npv_infra, fleet_size, context="npv_infra/fleet_size calculation"
    )

    return {
        DataColumns.INFRASTRUCTURE_PRICE: price,
        "service_life_years": service_life,
        "annual_maintenance": annual_maintenance,
        "annual_capital_cost": annual_capital,
        "total_annual_cost": total_annual_cost,
        "per_vehicle_annual_cost": per_vehicle_annual,
        "replacement_cycles": replacement_cycles,
        "npv_infrastructure": npv_infra,
        "npv_per_vehicle": npv_per_vehicle,
        "fleet_size": fleet_size,
    }


def apply_infrastructure_incentives(
    infrastructure_costs: Dict[str, Any],
    incentives_data: pd.DataFrame,
    apply_incentives: bool = True,
) -> Dict[str, Any]:
    if not apply_incentives:
        return infrastructure_costs

    costs = infrastructure_costs.copy()
    active = incentives_data[
        (incentives_data["incentive_flag"] == 1)
        & (incentives_data["incentive_type"] == "charging_infrastructure_subsidy")
    ]

    if not active.empty:
        incentive_condition = pd.Series([True] * len(active), index=active.index)
        incentive_data = safe_iloc_zero(
            active,
            incentive_condition,
            context="charging infrastructure subsidy incentive",
        )
        rate = incentive_data["incentive_rate"]
        costs["infrastructure_price_with_incentives"] = costs[
            DataColumns.INFRASTRUCTURE_PRICE
        ] * (1 - rate)
        costs["npv_infrastructure_with_incentives"] = costs["npv_infrastructure"] * (
            1 - rate
        )
        costs["npv_per_vehicle_with_incentives"] = costs["npv_per_vehicle"] * (1 - rate)
        costs["subsidy_rate"] = rate
    else:
        costs["infrastructure_price_with_incentives"] = costs[
            DataColumns.INFRASTRUCTURE_PRICE
        ]
        costs["npv_infrastructure_with_incentives"] = costs["npv_infrastructure"]
        costs["npv_per_vehicle_with_incentives"] = costs["npv_per_vehicle"]
        costs["subsidy_rate"] = 0

    return costs


def integrate_infrastructure_with_tco(
    tco_data: Dict[str, Any],
    infrastructure_costs: Dict[str, Any],
    apply_incentives: bool = True,
) -> Dict[str, Any]:
    updated = tco_data.copy()
    infra_npv = (
        infrastructure_costs["npv_per_vehicle_with_incentives"]
        if apply_incentives
        else infrastructure_costs["npv_per_vehicle"]
    )
    updated["npv_total_cost"] += infra_npv

    annual_kms = updated.get("annual_kms", 0)
    truck_life_years = updated.get("truck_life_years", 0)
    payload_t = updated.get(DataColumns.PAYLOAD_T, 0)

    if annual_kms and truck_life_years:
        total_kms = annual_kms * truck_life_years
        updated["tco_per_km"] = updated["npv_total_cost"] / total_kms
        if payload_t:
            updated["tco_per_tonne_km"] = updated["tco_per_km"] / payload_t

    updated["infrastructure_costs"] = infrastructure_costs
    return updated


# --------------------------------------------------------------------------------------
# Payload penalty – delegate to legacy impl for now (low usage outside plotters)
# --------------------------------------------------------------------------------------


def calculate_payload_penalty_costs(
    bev_results: Dict[str, Any],
    diesel_results: Dict[str, Any],
    financial_params: pd.DataFrame,
) -> Dict[str, Any]:
    """Proxy to :pyfunc:`tco_app.domain.finance_payload.calculate_payload_penalty_costs`."""
    return _impl(bev_results, diesel_results, financial_params)
