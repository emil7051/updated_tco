#!/usr/bin/env python3
"""Test script to verify cost breakdown page works with DTO mode."""

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
    get_infrastructure_subsidy_amount,
    get_daily_kwh_required,
    get_charging_time_per_day,
    get_charger_power,
    get_max_vehicles_per_charger,
    is_bev,
)


def test_cost_breakdown_accessors():
    """Test that cost breakdown accessors work correctly with both modes."""
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
        "selected_infrastructure": "I002",  # Non-zero infrastructure
        "charging_mix": {"C002": 1.0},
        "apply_incentives": True,
        "annual_kms": 20000,
        "truck_life_years": 10,
        "discount_rate": 0.05,
        "fleet_size": 1,
        "scenario_meta": {"name": "Default", "description": "Default scenario"},
    }
    
    ui_context = context_director.build_ui_context(sidebar_inputs)
    
    # Test with DTOs disabled (default)
    print("\nTesting with DTOs disabled (dictionary mode)...")
    orchestrator = CalculationOrchestrator(data_tables, ui_context)
    dict_results = orchestrator.perform_calculations()
    
    bev_dict = dict_results["bev_results"]
    
    print(f"BEV is BEV check: {is_bev(bev_dict)}")
    print(f"Infrastructure price: ${get_infrastructure_price(bev_dict):,.0f}")
    print(f"Infrastructure annual maintenance: ${get_infrastructure_annual_maintenance(bev_dict):,.0f}")
    print(f"Infrastructure NPV per vehicle: ${get_infrastructure_npv_per_vehicle(bev_dict) or 0:,.0f}")
    print(f"Infrastructure service life: {get_infrastructure_service_life(bev_dict)} years")
    print(f"Infrastructure replacement cycles: {get_infrastructure_replacement_cycles(bev_dict)}")
    
    subsidy_rate = get_infrastructure_subsidy_rate(bev_dict)
    print(f"Infrastructure subsidy rate: {subsidy_rate * 100:.0f}%")
    if subsidy_rate > 0:
        print(f"Infrastructure subsidy amount: ${get_infrastructure_subsidy_amount(bev_dict):,.0f}")
    
    print(f"\nCharging requirements:")
    print(f"Daily kWh required: {get_daily_kwh_required(bev_dict):.1f} kWh")
    print(f"Charging time per day: {get_charging_time_per_day(bev_dict):.2f} hours")
    print(f"Charger power: {get_charger_power(bev_dict):.0f} kW")
    print(f"Max vehicles per charger: {get_max_vehicles_per_charger(bev_dict):.1f}")
    
    # Test with DTOs enabled
    print("\n\nTesting with DTOs enabled...")
    ui_context["use_dtos"] = True
    orchestrator_dto = CalculationOrchestrator(data_tables, ui_context)
    dto_results = orchestrator_dto.perform_calculations()
    
    bev_dto = dto_results["bev_results"]
    
    print(f"BEV is BEV check: {is_bev(bev_dto)}")
    print(f"Infrastructure price: ${get_infrastructure_price(bev_dto):,.0f}")
    print(f"Infrastructure annual maintenance: ${get_infrastructure_annual_maintenance(bev_dto):,.0f}")
    print(f"Infrastructure NPV per vehicle: ${get_infrastructure_npv_per_vehicle(bev_dto) or 0:,.0f}")
    print(f"Infrastructure service life: {get_infrastructure_service_life(bev_dto)} years")
    print(f"Infrastructure replacement cycles: {get_infrastructure_replacement_cycles(bev_dto)}")
    
    subsidy_rate = get_infrastructure_subsidy_rate(bev_dto)
    print(f"Infrastructure subsidy rate: {subsidy_rate * 100:.0f}%")
    if subsidy_rate > 0:
        print(f"Infrastructure subsidy amount: ${get_infrastructure_subsidy_amount(bev_dto):,.0f}")
    
    print(f"\nCharging requirements:")
    print(f"Daily kWh required: {get_daily_kwh_required(bev_dto):.1f} kWh")
    print(f"Charging time per day: {get_charging_time_per_day(bev_dto):.2f} hours")
    print(f"Charger power: {get_charger_power(bev_dto):.0f} kW")
    print(f"Max vehicles per charger: {get_max_vehicles_per_charger(bev_dto):.1f}")
    
    # Verify values match
    print("\n\nVerifying accessor compatibility...")
    dict_price = get_infrastructure_price(bev_dict)
    dto_price = get_infrastructure_price(bev_dto)
    
    if abs(dict_price - dto_price) < 1:
        print("✅ Infrastructure price matches between dict and DTO modes")
    else:
        print(f"❌ Infrastructure price mismatch: dict={dict_price}, dto={dto_price}")
    
    dict_daily_kwh = get_daily_kwh_required(bev_dict)
    dto_daily_kwh = get_daily_kwh_required(bev_dto)
    
    if abs(dict_daily_kwh - dto_daily_kwh) < 0.1:
        print("✅ Daily kWh required matches between dict and DTO modes")
    else:
        print(f"❌ Daily kWh mismatch: dict={dict_daily_kwh}, dto={dto_daily_kwh}")
    
    print("\n✅ Cost breakdown accessor test completed successfully!")


if __name__ == "__main__":
    test_cost_breakdown_accessors()