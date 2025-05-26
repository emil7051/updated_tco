# Legacy Code Deprecation Plan - Updated

## Overview

The TCO application is currently in a transitional state where modern DTOs (Data Transfer Objects) coexist with legacy dictionary-based data structures. This creates unnecessary complexity, performance overhead, and maintenance burden. This document outlines the progress made and remaining work to complete the modernisation and remove legacy compatibility layers.

## Progress Summary

### ✅ **Completed Work**

#### Phase 1.1: Modernise Domain Functions - calculate_comparative_metrics()
**Status: COMPLETE**

1. **Created new DTO-based function**: `calculate_comparative_metrics_from_dto()`
   - File: `tco_app/domain/sensitivity/metrics.py`
   - Accepts `ComparisonResult` DTO instead of dictionaries
   - Calculates all comparative metrics including price parity year

2. **Updated ComparisonResult DTO**:
   - Added `annual_kms` and `truck_life_years` fields
   - These parameters are needed for price parity calculations

3. **Updated TCOResult DTO**:
   - Added `battery_replacement_year` and `battery_replacement_cost` fields
   - These will be needed for accurate price parity calculations (not yet populated)

4. **Modified TCOCalculationService**:
   - `compare_vehicles()` now uses `calculate_comparative_metrics_from_dto()`
   - Removed dependency on `convert_tco_result_to_model_runner_dict`
   - Properly populates all comparison metrics

5. **Removed conversion function**:
   - Deleted `convert_tco_result_to_model_runner_dict` from helpers module
   - No longer imported anywhere in the codebase

#### Phase 1.2: Update perform_sensitivity_analysis()
**Status: COMPLETE**

1. **Created new DTOs**:
   - `SensitivityRequest` - Request parameters for sensitivity analysis
   - `SensitivityResult` - Result structure for each parameter value

2. **Created new DTO-based function**: `perform_sensitivity_analysis_with_dtos()`
   - File: `tco_app/domain/sensitivity/single_param.py`
   - Accepts `SensitivityRequest` DTO instead of 18+ individual parameters
   - Returns list of `SensitivityResult` DTOs
   - Uses TCOCalculationService for consistent calculations

3. **Created adapter function**: `create_sensitivity_adapter()`
   - Converts legacy parameters to CalculationRequest DTOs
   - Enables gradual migration of UI components

4. **Updated tornado chart calculation**:
   - Created `calculate_tornado_data_with_dtos()` function
   - Uses new DTO-based sensitivity analysis
   - Maintains backward compatibility

5. **Updated sensitivity page**:
   - Added `_perform_analysis_with_dtos()` function
   - Can switch between old and new implementation via session state
   - Converts DTO results to legacy format for chart compatibility

6. **Tested implementation**:
   - Created and ran test script verifying functionality
   - All sensitivity calculations produce correct results

### ⚠️ **Issues Discovered**

1. **Battery Parameters Column Mismatch**: ✅ **RESOLVED**
   - The application expected columns named `description` and `default_value`
   - The actual CSV has columns named `battery_description` and `default_value`
   - Fixed by updating the orchestrator to use the correct column name
   - The DataColumns.BATTERY_DESCRIPTION constant already had the correct value

2. **Extensive Dictionary Usage in UI**:
   - UI components and plotters extensively use dictionary access patterns
   - Over 100+ instances of `bev_results["key"]["subkey"]` patterns
   - Complete migration requires updating all these components

## Remaining Work - Detailed Plan

### **Phase 1.2: Update perform_sensitivity_analysis()** ✅
*Status: COMPLETE | Completed: 26/05/2025*

The sensitivity analysis has been successfully modernised with:
- New DTOs for type-safe parameter passing
- Modern function using TCOCalculationService
- Adapter for backward compatibility
- Updated tornado chart calculations
- Gradual migration path for UI

### **Phase 2.2: Remove UI Transformation Functions**
*Status: IN PROGRESS | Started: 26/05/2025*

**Current State**:
- `_transform_single_tco_result_for_ui()` converts DTOs back to dictionaries
- All UI components expect dictionary format

**Progress So Far**:

1. **Created DTO accessor utilities** ✅
   - File: `tco_app/ui/utils/dto_accessors.py`
   - Provides safe accessors that work with both DTOs and dictionaries
   - Enables gradual migration of UI components

2. **Added DTO mode support to orchestrator** ✅
   - Added `_prepare_dto_results()` method
   - Can return DTOs directly when `use_dtos` flag is set
   - Maintains backward compatibility with dictionary mode

3. **Migrated components** ✅:
   - `summary_displays.py` - Migrated to use DTO accessors
   - `key_metrics.py` - Migrated key metrics chart
   - `emissions.py` - Migrated emissions chart
   - `cost_breakdown.py` - Migrated complex cost breakdowns

4. **Created test script** ✅
   - File: `utility_scripts/test_dto_mode.py`
   - Verifies DTO mode works correctly
   - Confirms accessors work with both DTOs and dictionaries

**Remaining Components to Migrate**:
- `metric_cards.py` - Works with comparison_metrics dict (no changes needed)
- `sensitivity.py` - Works with sensitivity results (no changes needed)
- `tornado.py` - Works with tornado results (no changes needed)
- UI pages that directly access results dictionaries

**Next Steps**:
1. Identify and migrate any remaining UI components that directly access result dictionaries
2. Update main pages to optionally use DTO mode
3. Add feature flag in UI to toggle between modes
4. Once all components support DTOs, remove transformation functions

### **Phase 3: Fix Data Schema Issues**
*Priority: Medium | Estimated Effort: 1 day*

1. **Investigate battery_params column names**:
```bash
# Check actual CSV columns
head -1 tco_app/data/dictionary/battery_params.csv
```

2. **Update column mappings**:
   - Either update CSV headers
   - Or update `DataColumns` constants
   - Ensure consistency across codebase

3. **Add validation**:
```python
def validate_dataframe_schema(df: pd.DataFrame, expected_columns: List[str]):
    """Validate DataFrame has expected columns."""
    missing = set(expected_columns) - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")
```

### **Phase 4: Battery Replacement Enhancement**
*Priority: Low | Estimated Effort: 2 days*

1. **Enhance battery calculation to return more details**:
```python
@dataclass
class BatteryReplacementResult:
    npv_cost: float
    replacement_year: Optional[int]
    undiscounted_cost: Optional[float]
```

2. **Update `calculate_battery_replacement()` function**
3. **Populate TCOResult battery fields properly**
4. **Use in price parity calculations**

## Implementation Checklist

### Week 1: Core Functionality
- [x] Day 1: Update `calculate_comparative_metrics()` to use DTOs
- [x] Day 2: Update `ComparisonResult` and `TCOResult` DTOs
- [x] Day 3: Update `TCOCalculationService.compare_vehicles()`
- [x] Day 4: Remove `convert_tco_result_to_model_runner_dict`
- [x] Day 5: Create sensitivity analysis DTOs

### Week 2: Sensitivity Analysis
- [x] Day 1: Implement `perform_sensitivity_analysis_with_dtos()`
- [x] Day 2: Update tornado chart calculations
- [x] Day 3: Update sensitivity page
- [x] Day 4: Test sensitivity analysis thoroughly
- [x] Day 5: Fix battery parameters schema issue

### Week 3: UI Migration
- [ ] Day 1: Create DTO accessor utilities
- [ ] Day 2: Migrate simple display components
- [ ] Day 3: Migrate chart components
- [ ] Day 4: Migrate complex components
- [ ] Day 5: Remove transformation functions

### Week 4: Polish and Testing
- [ ] Day 1: Enhance battery replacement calculations
- [ ] Day 2: Performance testing and optimisation
- [ ] Day 3: Update all tests
- [ ] Day 4: Documentation updates
- [ ] Day 5: Final testing and deployment prep

## Testing Strategy

### Unit Tests
- [x] Test new `calculate_comparative_metrics_from_dto()`
- [ ] Test new sensitivity analysis functions
- [ ] Test DTO accessor utilities
- [ ] Update existing tests to use DTOs

### Integration Tests
- [ ] Test complete calculation flow with DTOs
- [ ] Test UI rendering with DTOs
- [ ] Test sensitivity analysis end-to-end
- [ ] Test performance improvements

### Manual Testing
- [ ] Verify all pages load correctly
- [ ] Check all charts render properly
- [ ] Validate calculation results match legacy
- [ ] Test edge cases and error handling

## Risk Mitigation

### Gradual Migration
- Keep old functions during transition
- Use feature flags if needed
- Test thoroughly at each step
- Maintain backward compatibility temporarily

### Data Validation
- Add schema validation for DataFrames
- Log warnings for missing columns
- Provide clear error messages
- Document expected formats

### Performance Monitoring
- Benchmark before and after changes
- Monitor memory usage
- Profile critical paths
- Optimise as needed

## Success Metrics

### Code Quality
- [x] Modern DTO-based calculate_comparative_metrics
- [ ] No dictionary transformations in service layer
- [ ] Type-safe data access throughout
- [ ] Clean separation of concerns

### Performance
- [ ] Reduced memory usage (no duplicate structures)
- [ ] Faster calculation times
- [ ] Improved UI responsiveness
- [ ] Efficient data access patterns

### Maintainability
- [ ] Single source of truth for data structures
- [ ] Clear, documented interfaces
- [ ] Comprehensive test coverage
- [ ] Easy to debug and extend

## Next Steps

1. **Immediate**: Fix battery parameters column issue to eliminate warnings
2. **This Week**: Start sensitivity analysis modernisation
3. **Next Week**: Begin UI component migration
4. **Following Week**: Complete migration and testing

## Notes for Implementation

### When Migrating UI Components
1. Always check for None/missing values
2. Use safe accessor methods during transition
3. Test with both BEV and Diesel vehicles
4. Verify infrastructure cost handling for BEV
5. Check charging mix calculations

### Common Patterns to Replace
```python
# Old pattern
bev_tco = bev_results["tco"]["tco_per_km"]

# New pattern
bev_tco = bev_result.tco_per_km

# Old pattern with safety
bev_tco = bev_results.get("tco", {}).get("tco_per_km", 0)

# New pattern with safety
bev_tco = getattr(bev_result, "tco_per_km", 0)
```

### Infrastructure Cost Access
```python
# Old pattern
if "infrastructure_costs" in bev_results:
    cost = bev_results["infrastructure_costs"]["npv_per_vehicle"]

# New pattern
if bev_result.infrastructure_costs_breakdown:
    cost = bev_result.infrastructure_costs_breakdown.get("npv_per_vehicle", 0)
```

This plan provides a clear path forward with detailed steps to complete the modernisation while maintaining system stability throughout the transition. 