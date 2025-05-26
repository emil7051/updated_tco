# Constants Consolidation Report

## Overview
This report documents all constant duplication and redundant definitions found in the TCO application codebase, along with recommendations for consolidation.

## Completed Work

### 1. ✅ Emission Standards Consolidation - COMPLETED
**Previous Issue**: 
- Emission standards were defined in two places with identical values
- `EmissionConstants` class had `DEFAULT_ELECTRICITY_STANDARD` and `DEFAULT_DIESEL_STANDARD`
- `EmissionStandard` enum had `GRID` and `EURO_IV_PLUS`

**Resolution**:
- Removed duplicate constants from `EmissionConstants` class
- Updated `domain/energy.py` to use `EmissionStandard` enum values
- Now using `EmissionStandard.GRID` and `EmissionStandard.EURO_IV_PLUS` throughout
- All tests passing

### 2. ✅ Configuration Restructuring - COMPLETED
**Changes Made**:
- Removed `EmissionConstants` class and moved its unit conversion constants to new `UnitConversions` class
- Created `ExternalityConstants` class for externality-specific constants
- Moved `SCC_AUD_PER_TONNE` from hardcoded value in `domain/externalities.py` to `ExternalityConstants`
- Updated all imports and usages

### 3. ✅ DataFrame Column Names - COMPLETED
**Previous Issue**: 
- Column names were hardcoded as strings instead of using `DataColumns` enum

**Resolution**:
- Updated `domain/energy.py` to use `DataColumns` enum for all column references
- Updated `domain/externalities.py` to use `DataColumns` enum
- Updated `services/scenario_application_service.py` to use `DataColumns` enum
- Fixed test files to use correct column names matching the enum values
- Maintained backward compatibility where needed (e.g., in externalities fallback)

### 4. ✅ Fuel Type Constants - COMPLETED
**Resolution**:
- Updated code to use `FuelType.ELECTRICITY` and `FuelType.DIESEL` enum values
- Removed hardcoded "electricity" and "diesel" strings from domain code

### 5. ✅ Magic Numbers for Unit Conversions - COMPLETED
**Previous Issue**:
- `1000` for kg to tonnes conversion
- `100` for percentage conversions (per100km to per km)
- `0.05` for plot text offset

**Resolution**:
- Created `UnitConversions` class with `KG_TO_TONNES` and `PERCENTAGE_TO_DECIMAL` constants
- Updated all domain code to use these constants:
  - `domain/energy.py` - Now uses `UNIT_CONVERSIONS.PERCENTAGE_TO_DECIMAL`
  - `domain/externalities.py` - Now uses `UNIT_CONVERSIONS.KG_TO_TONNES`
  - `domain/sensitivity/externality.py` - Now uses `UNIT_CONVERSIONS.KG_TO_TONNES`
  - `domain/sensitivity/metrics.py` - Now uses `UNIT_CONVERSIONS.KG_TO_TONNES`
  - `ui/components/metric_cards.py` - Now uses `UNIT_CONVERSIONS.KG_TO_TONNES`
  - `plotters/payload.py` - Now uses `UI_CONFIG.PLOT_TEXT_OFFSET_FACTOR`

## Important Design Decision: CSV Files as Source of Truth

### Approach Taken
- **Maintained CSV files as the single source of truth** for all operational data
- Configuration file (`config.py`) contains only:
  - UI/validation constants (not data)
  - Unit conversion constants (mathematical, not operational)
  - Performance thresholds
  - Application behaviour settings
- Data access layer (`data_access.py`) uses hardcoded fallbacks that match CSV values only when data is missing
- All data flows through the `data_loading.py` service which reads from CSV files

### Why This Matters
- Changes to operational parameters only require updating CSV files
- No need to modify code when business parameters change
- Clear separation between application logic and business data
- Supports future migration to database or API without code changes

## Remaining Minor Issues

### 1. Sensitivity Analysis Magic Numbers
**Current State**: 
- Values like 0.5, 0.7 used for sensitivity range calculations
- Located in `ui/components/sensitivity_components.py`

**Recommendation**: 
- Keep as is - these are calculation logic, not data parameters
- They define how sensitivity analysis behaves, not what values to analyse

### 2. Performance Thresholds
**Current State**:
- Some thresholds like 100, 1000 in `calculation_optimisations.py`

**Recommendation**:
- Already moved to `PerformanceConfig` where appropriate
- These are optimization thresholds, not business data

## Files Updated

### Production Code
- ✅ `tco_app/domain/energy.py` - Uses constants for unit conversions
- ✅ `tco_app/domain/externalities.py` - Uses constants for unit conversions
- ✅ `tco_app/domain/sensitivity/externality.py` - Uses constants for unit conversions
- ✅ `tco_app/domain/sensitivity/metrics.py` - Uses constants for unit conversions
- ✅ `tco_app/ui/components/metric_cards.py` - Uses constants for unit conversions
- ✅ `tco_app/plotters/payload.py` - Uses UI config for plot formatting
- ✅ `tco_app/src/config.py` - Contains only non-data constants
- ✅ `tco_app/src/utils/data_access.py` - Reverted to use hardcoded fallbacks matching CSV data

## Next Steps

### 1. Data Completeness Audit (High Priority)
- Review if any operational parameters are still hardcoded in the application
- Identify any missing data that should be added to CSV files
- Consider adding new CSV files for:
  - Sensitivity analysis configuration (if needed)
  - Regional variations in parameters

### 2. Documentation (Medium Priority)
- Document which CSV file contains which type of data
- Create data dictionary for all CSV columns
- Document the fallback values and when they're used

### 3. Data Validation (Low Priority)
- Add validation to ensure CSV data is within expected ranges
- Consider adding data quality checks on startup
- Log warnings when fallback values are used

## Conclusion

The codebase now properly separates:
- **Data constants** (from CSV files) - business/operational parameters that may change
- **Code constants** (in config.py) - application behaviour, UI settings, mathematical constants
- **Magic numbers** - eliminated where they represent data or conversions

The CSV files remain the single source of truth for all operational data, ensuring the application can adapt to changing business requirements without code modifications. 