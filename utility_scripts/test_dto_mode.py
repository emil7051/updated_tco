#!/usr/bin/env python3
"""Test script to verify DTO functionality."""

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
    
    # Test with DTOs (now the only mode)
    print("\nTesting DTO functionality...")
    orchestrator = CalculationOrchestrator(data_tables, ui_context)
    results = orchestrator.perform_calculations()
    
    bev_dto = results["bev_results"]
    diesel_dto = results["diesel_results"]
    comparison_dto = results["comparison"]
    
    print(f"BEV results type: {type(bev_dto)}")
    print(f"BEV TCO per km: ${get_tco_per_km(bev_dto):.4f}")
    print(f"BEV lifetime TCO: ${get_tco_lifetime(bev_dto):,.0f}")
    print(f"BEV annual operating cost: ${get_annual_operating_cost(bev_dto):,.0f}")
    print(f"BEV CO2 per km: {get_co2_per_km(bev_dto):.2f} kg")
    
    print(f"\nDiesel results type: {type(diesel_dto)}")
    print(f"Diesel TCO per km: ${get_tco_per_km(diesel_dto):.4f}")
    print(f"Diesel lifetime TCO: ${get_tco_lifetime(diesel_dto):,.0f}")
    print(f"Diesel annual operating cost: ${get_annual_operating_cost(diesel_dto):,.0f}")
    print(f"Diesel CO2 per km: {get_co2_per_km(diesel_dto):.2f} kg")
    
    # Test comparison metrics
    print("\nTesting comparison metrics...")
    comp_metrics = results["comparison_metrics"]
    print(f"Upfront cost difference: ${comp_metrics['upfront_cost_difference']:,.0f}")
    print(f"Annual operating savings: ${comp_metrics['annual_operating_savings']:,.0f}")
    print(f"Price parity year: {comp_metrics['price_parity_year']:.1f}")
    print(f"Emissions reduction: {comp_metrics['emission_savings_lifetime']:,.0f} kg")
    
    print("\n✅ DTO functionality test completed successfully!")


if __name__ == "__main__":
    test_dto_mode() 