#!/usr/bin/env python3
"""Test script to verify cost breakdown DTO accessor functionality."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tco_app.src.data_loading import load_data
from tco_app.ui.context.context_builder import ContextDirector
from tco_app.ui.orchestration import CalculationOrchestrator
from tco_app.ui.utils.dto_accessors import (
    get_infrastructure_price,
    get_infrastructure_annual_maintenance,
    get_infrastructure_npv_per_vehicle,
    get_infrastructure_service_life,
    get_infrastructure_replacement_cycles,
    get_infrastructure_subsidy_rate,
    get_daily_kwh_required,
    get_charging_time_per_day,
    get_charger_power,
    get_max_vehicles_per_charger,
    is_bev,
)


def test_cost_breakdown_accessors():
    """Test that cost breakdown DTO accessors work correctly."""
    print("Loading data...")
    data_tables = load_data()
    
    # Build a minimal UI context
    print("Building UI context...")
    context_director = ContextDirector(data_tables)
    
    # Create minimal inputs
    sidebar_inputs = {
        "selected_bev_id": "BEV001",
        "comparison_diesel_id": "DSL001",
        "selected_charging": "C002",
        "selected_infrastructure": "I001",  # Select non-zero infrastructure
        "charging_mix": {"C002": 1.0},
        "apply_incentives": True,
        "annual_kms": 20000,
        "truck_life_years": 10,
        "discount_rate": 0.05,
        "fleet_size": 1,
        "scenario_meta": {"name": "Default", "description": "Default scenario"},
    }
    
    ui_context = context_director.build_ui_context(sidebar_inputs)
    
    # Test with DTOs (now the only mode)
    print("\nTesting DTO accessor functionality...")
    orchestrator = CalculationOrchestrator(data_tables, ui_context)
    results = orchestrator.perform_calculations()
    
    bev_dto = results["bev_results"]
    
    print(f"BEV is BEV check: {is_bev(bev_dto)}")
    
    # Test infrastructure accessors
    infra_price = get_infrastructure_price(bev_dto)
    infra_maint = get_infrastructure_annual_maintenance(bev_dto)
    infra_npv = get_infrastructure_npv_per_vehicle(bev_dto)
    infra_life = get_infrastructure_service_life(bev_dto)
    infra_cycles = get_infrastructure_replacement_cycles(bev_dto)
    infra_subsidy = get_infrastructure_subsidy_rate(bev_dto)
    
    print(f"Infrastructure price: ${infra_price:,.0f}")
    print(f"Infrastructure annual maintenance: ${infra_maint:,.0f}")
    print(f"Infrastructure NPV per vehicle: ${infra_npv:,.0f}")
    print(f"Infrastructure service life: {infra_life} years")
    print(f"Infrastructure replacement cycles: {infra_cycles}")
    print(f"Infrastructure subsidy rate: {infra_subsidy:.0%}")
    
    # Test charging requirement accessors
    print("\nCharging requirements:")
    daily_kwh = get_daily_kwh_required(bev_dto)
    charge_time = get_charging_time_per_day(bev_dto)
    charger_power = get_charger_power(bev_dto)
    max_vehicles = get_max_vehicles_per_charger(bev_dto)
    
    print(f"Daily kWh required: {daily_kwh:.1f} kWh")
    print(f"Charging time per day: {charge_time:.2f} hours")
    print(f"Charger power: {charger_power} kW")
    print(f"Max vehicles per charger: {max_vehicles:.1f}")
    
    print("\n✅ Cost breakdown accessor test completed successfully!")


if __name__ == "__main__":
    test_cost_breakdown_accessors()