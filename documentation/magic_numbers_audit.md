# Magic Numbers Audit Report

## Overview
This report identifies all magic numbers found in the TCO application codebase and provides recommendations for whether they should be:
1. Drawn from CSV files (operational data)
2. Defined as constants in config.py (application behaviour)
3. Left as-is (calculation logic)

## Magic Numbers Found

### 1. Domain Layer

#### finance_payload.py
- **Line 56-59**: Hardcoded default values for operational parameters:
  ```python
  freight_value_per_tonne = get_param("freight_value_per_tonne", 120)
  driver_cost_hourly = get_param("driver_cost_hourly", 35)
  avg_trip_distance = get_param("avg_trip_distance", 100)
  avg_loadunload_time = get_param("avg_loadunload_time", 1)
  ```
  **Status**: ✅ Already in CSV (financial_params.csv)
  **Action**: None needed - these are fallback values matching CSV data

- **Line 70**: `avg_speed_kmh = 60`
  **Status**: ❌ Not in CSV
  **Recommendation**: Add to financial_params.csv as operational parameter
  **Action**: Add new row to financial_params.csv

#### energy.py
- **Line 60**: `electric_range = vehicle_data.get(DataColumns.RANGE_KM, 50)`
  **Status**: ❌ Hardcoded default for PHEV electric range
  **Recommendation**: Add to config.py as `DEFAULT_PHEV_ELECTRIC_RANGE_KM`
  
- **Line 63**: `electric_range / 100` (assumes 100km daily driving)
  **Status**: ❌ Hardcoded assumption
  **Recommendation**: Add to config.py as `TYPICAL_DAILY_DISTANCE_KM`

- **Line 165**: `24` hours in charging calculation
  **Status**: ✅ Mathematical constant
  **Action**: Replace with `CALC_DEFAULTS.HOURS_PER_DAY` (add to config.py)

### 2. Data Access Layer

#### data_access.py
- **Lines 57, 62, 67, 81, 86, 91**: Default values for parameters
  ```python
  diesel_price: 2.03
  discount_rate: 0.05
  carbon_price: 0.0
  replacement_cost: 150.0
  degradation_rate: 0.025
  minimum_capacity: 0.7
  ```
  **Status**: ✅ Already match CSV values
  **Action**: None needed - these are appropriate fallbacks

### 3. UI Layer

#### sensitivity_components.py
- **Line 58**: `min_val = max(1000, base_value * 0.5)`
  **Status**: ✅ Already using VALIDATION_LIMITS where appropriate
  **Recommendation**: Replace hardcoded factors with config constants:
    - `0.5` → `VALIDATION_LIMITS.SENSITIVITY_MIN_FACTOR_STRICT`
    - `1.5` → `VALIDATION_LIMITS.SENSITIVITY_MAX_FACTOR`
    - `0.7` → `VALIDATION_LIMITS.SENSITIVITY_MIN_FACTOR`
    - `1.3` → `VALIDATION_LIMITS.SENSITIVITY_MAX_FACTOR`

- **Lines 86-87, 97**: Range adjustments `± 3`
  **Status**: ❌ Hardcoded adjustment values
  **Recommendation**: Add to config.py as `SENSITIVITY_LIFETIME_ADJUSTMENT` and `SENSITIVITY_DISCOUNT_ADJUSTMENT`

#### metric_cards.py
- **Line 74**: `if comparative_metrics["price_parity_year"] < 100:`
  **Status**: ❌ Arbitrary threshold
  **Recommendation**: Add to config.py as `MAX_REASONABLE_PARITY_YEARS`

- **Line 121-122**: Abatement cost thresholds `50` and `100`
  **Status**: ❌ Business logic thresholds
  **Recommendation**: Add to config.py as `ABATEMENT_COST_LOW_THRESHOLD` and `ABATEMENT_COST_HIGH_THRESHOLD`

### 4. Calculation Optimisations

#### calculation_optimisations.py
- **Lines 46, 53**: Array size thresholds `100` and `1000`
  **Status**: ✅ Performance optimisation thresholds
  **Action**: None needed - these are internal optimisation details

## New CSV Data Required

### 1. Add to financial_params.csv:
```csv
FP015,avg_speed_kmh,60.0
```

### 2. Consider adding operational_params.csv:
```csv
param_id,param_description,default_value
OP001,typical_daily_distance_km,100.0
OP002,default_phev_electric_range_km,50.0
```

## New Constants for config.py

### 1. Add to CalculationDefaults:
```python
HOURS_PER_DAY: int = 24
DEFAULT_PHEV_ELECTRIC_RANGE_KM: float = 50.0
TYPICAL_DAILY_DISTANCE_KM: float = 100.0
```

### 2. Add to ValidationLimits:
```python
# Sensitivity adjustments
SENSITIVITY_LIFETIME_ADJUSTMENT: int = 3
SENSITIVITY_DISCOUNT_ADJUSTMENT: float = 3.0

# Business logic thresholds
MAX_REASONABLE_PARITY_YEARS: int = 100
ABATEMENT_COST_LOW_THRESHOLD: float = 50.0
ABATEMENT_COST_HIGH_THRESHOLD: float = 100.0
```

## Summary

Most magic numbers in the codebase are either:
1. Already backed by CSV data (with appropriate fallbacks)
2. Mathematical constants or calculation logic
3. Performance optimisation thresholds

The main gaps identified are:
- `avg_speed_kmh` should be added to CSV files
- Several UI thresholds should be moved to config.py
- PHEV-specific assumptions need proper constants

The application correctly follows the pattern of using CSV files for operational data and config.py for application behaviour constants. 