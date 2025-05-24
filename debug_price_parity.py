#!/usr/bin/env python3

# Debug script to verify price parity calculation
import sys
sys.path.append('.')

from tco_app.domain.sensitivity.metrics import calculate_comparative_metrics

# Test data from the failing test
bev_results = {
    'acquisition_cost': 200000,
    'residual_value': 40000,
    'annual_costs': {'annual_operating_cost': 20000},
    'emissions': {'lifetime_emissions': 500000},
    'tco': {'npv_total_cost': 350000},
}

diesel_results = {
    'acquisition_cost': 100000,
    'residual_value': 20000,
    'annual_costs': {'annual_operating_cost': 30000},
    'emissions': {'lifetime_emissions': 800000},
    'tco': {'npv_total_cost': 380000},
}

metrics = calculate_comparative_metrics(
    bev_results=bev_results,
    diesel_results=diesel_results,
    annual_kms=100000,
    truck_life_years=10
)

print(f"Price parity year: {metrics['price_parity_year']}")
print(f"Upfront cost difference: {metrics['upfront_cost_difference']}")
print(f"Annual operating savings: {metrics['annual_operating_savings']}")

# Manual calculation to understand the logic
years = list(range(1, 11))
bev_cum = [200000]  # Start with acquisition cost
diesel_cum = [100000]

# Add annual costs for years 1-9
for year in range(1, 10):
    bev_cum.append(bev_cum[-1] + 20000)
    diesel_cum.append(diesel_cum[-1] + 30000)

# Final year includes residual value reduction
bev_cum[-1] -= 40000  # Subtract residual value
diesel_cum[-1] -= 20000

print("\nYear-by-year cumulative costs:")
for i, year in enumerate(years):
    print(f"Year {year}: BEV={bev_cum[i]:,}, Diesel={diesel_cum[i]:,}, Diff={bev_cum[i]-diesel_cum[i]:,}")

# Find crossover point
for i in range(len(years) - 1):
    if (bev_cum[i] - diesel_cum[i]) * (bev_cum[i + 1] - diesel_cum[i + 1]) <= 0:
        delta_bev = bev_cum[i + 1] - bev_cum[i]
        delta_diesel = diesel_cum[i + 1] - diesel_cum[i]
        if delta_bev != delta_diesel:
            t = (diesel_cum[i] - bev_cum[i]) / (delta_bev - delta_diesel)
            crossover_year = years[i] + t
            print(f"\nCrossover detected between year {years[i]} and {years[i+1]}")
            print(f"Delta BEV: {delta_bev}, Delta Diesel: {delta_diesel}")
            print(f"t = ({diesel_cum[i]} - {bev_cum[i]}) / ({delta_bev} - {delta_diesel}) = {t}")
            print(f"Crossover year: {years[i]} + {t} = {crossover_year}")
            break
