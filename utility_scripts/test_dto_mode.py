#!/usr/bin/env python3
"""Test script to verify DTO mode functionality."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tco_app.src.data_loading import load_data
from tco_app.ui.context.context_builder import ContextDirector
from tco_app.ui.orchestration import CalculationOrchestrator
from tco_app.ui.utils.dto_accessors import (
    get_tco_per_km,
    get_tco_lifetime,
    get_annual_operating_cost,
    get_co2_per_km,
)


def test_dto_mode():
    """Test that DTO mode returns DTOs and accessors work correctly."""
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
        "selected_infrastructure": "I000",
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
    diesel_dict = dict_results["diesel_results"]
    
    print(f"BEV results type: {type(bev_dict)}")
    print(f"BEV TCO per km (dict): ${get_tco_per_km(bev_dict):.4f}")
    print(f"BEV lifetime TCO (dict): ${get_tco_lifetime(bev_dict):,.0f}")
    print(f"BEV annual operating cost (dict): ${get_annual_operating_cost(bev_dict):,.0f}")
    print(f"BEV CO2 per km (dict): {get_co2_per_km(bev_dict):.2f} kg")
    
    # Test with DTOs enabled
    print("\nTesting with DTOs enabled...")
    ui_context["use_dtos"] = True
    orchestrator_dto = CalculationOrchestrator(data_tables, ui_context)
    dto_results = orchestrator_dto.perform_calculations()
    
    bev_dto = dto_results["bev_results"]
    diesel_dto = dto_results["diesel_results"]
    comparison_dto = dto_results["comparison"]
    
    print(f"BEV results type: {type(bev_dto)}")
    print(f"BEV TCO per km (DTO): ${get_tco_per_km(bev_dto):.4f}")
    print(f"BEV lifetime TCO (DTO): ${get_tco_lifetime(bev_dto):,.0f}")
    print(f"BEV annual operating cost (DTO): ${get_annual_operating_cost(bev_dto):,.0f}")
    print(f"BEV CO2 per km (DTO): {get_co2_per_km(bev_dto):.2f} kg")
    
    # Verify accessors work correctly with both types
    print("\nVerifying accessor compatibility...")
    dict_tco_km = get_tco_per_km(bev_dict)
    dto_tco_km = get_tco_per_km(bev_dto)
    
    if abs(dict_tco_km - dto_tco_km) < 0.0001:
        print("✅ TCO per km matches between dict and DTO modes")
    else:
        print(f"❌ TCO per km mismatch: dict={dict_tco_km}, dto={dto_tco_km}")
    
    dict_lifetime = get_tco_lifetime(bev_dict)
    dto_lifetime = get_tco_lifetime(bev_dto)
    
    if abs(dict_lifetime - dto_lifetime) < 1:
        print("✅ Lifetime TCO matches between dict and DTO modes")
    else:
        print(f"❌ Lifetime TCO mismatch: dict={dict_lifetime}, dto={dto_lifetime}")
    
    # Test comparison metrics
    print("\nTesting comparison metrics...")
    comp_metrics = dto_results["comparison_metrics"]
    print(f"Upfront cost difference: ${comp_metrics['upfront_cost_difference']:,.0f}")
    print(f"Annual operating savings: ${comp_metrics['annual_operating_savings']:,.0f}")
    print(f"Price parity year: {comp_metrics['price_parity_year']:.1f}")
    print(f"Emissions reduction: {comp_metrics['emission_savings_lifetime']:,.0f} kg")
    
    print("\n✅ DTO mode test completed successfully!")


if __name__ == "__main__":
    test_dto_mode() 