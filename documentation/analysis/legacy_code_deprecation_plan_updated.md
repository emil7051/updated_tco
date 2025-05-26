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

#### Phase 2.2: Remove UI Transformation Functions
**Status: COMPLETE | Completed: 26/05/2025**

1. **Created DTO accessor utilities** ✅
   - File: `tco_app/ui/utils/dto_accessors.py`
   - Provides safe accessors that work with both DTOs and dictionaries
   - Added infrastructure cost accessors
   - Added charging requirement accessors
   - Fixed vehicle data and drivetrain accessors

2. **Added DTO mode support to orchestrator** ✅
   - Added `_prepare_dto_results()` method
   - Can return DTOs directly when `use_dtos` flag is set
   - Maintains backward compatibility with dictionary mode

3. **Migrated components** ✅:
   - `summary_displays.py` - Migrated to use DTO accessors
   - `key_metrics.py` - Migrated key metrics chart
   - `emissions.py` - Migrated emissions chart
   - `cost_breakdown.py` - Migrated complex cost breakdowns
   - `cost_breakdown.py` (page) - Migrated UI page to use DTO accessors

4. **Added feature flag** ✅:
   - Added "Use DTO mode (experimental)" toggle in sidebar
   - Under "Advanced Settings" expander
   - Allows users to toggle between dictionary and DTO modes

5. **Created test scripts** ✅:
   - File: `utility_scripts/test_dto_mode.py`
   - File: `utility_scripts/test_cost_breakdown_dto.py`
   - Verifies DTO mode works correctly
   - Confirms accessors work with both DTOs and dictionaries

### ⚠️ **Issues Discovered and Resolved**

1. **Battery Parameters Column Mismatch**: ✅ **RESOLVED**
   - The application expected columns named `description` and `default_value`
   - The actual CSV has columns named `battery_description` and `default_value`
   - Fixed by updating the orchestrator to use the correct column name
   - The DataColumns.BATTERY_DESCRIPTION constant already had the correct value

2. **DTO Attribute Issues**: ✅ **RESOLVED**
   - TCOResult doesn't have `drivetrain` attribute
   - Orchestrator dynamically adds `vehicle_data` to DTOs
   - Fixed accessors to use dynamic attributes properly

## Remaining Work - Detailed Plan

### **Phase 3: Complete Migration and Remove Legacy Code**
*Status: READY TO START | Estimated Effort: 3-5 days*

**Current State**:
- All major UI components migrated to use DTO accessors
- Feature flag allows toggling between modes
- Both modes working correctly

**Next Steps**:

1. **Enable DTO mode by default** (Day 1)
   - Change default value of feature flag to True
   - Monitor for any issues in production
   - Keep dictionary mode as fallback

2. **Remove transformation functions** (Day 2-3)
   - Remove `_transform_single_tco_result_for_ui()`
   - Remove `_transform_results_for_ui()`
   - Update orchestrator to only support DTO mode
   - Remove feature flag

3. **Clean up orchestrator** (Day 3-4)
   - Simplify `perform_calculations()` method
   - Remove conditional logic for DTO/dict modes
   - Update tests to only test DTO mode

4. **Update documentation** (Day 4-5)
   - Update API documentation
   - Update developer guides
   - Remove references to dictionary format

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

### Week 1-2: Core Functionality ✅
- [x] Update `calculate_comparative_metrics()` to use DTOs
- [x] Update `ComparisonResult` and `TCOResult` DTOs
- [x] Update `TCOCalculationService.compare_vehicles()`
- [x] Remove `convert_tco_result_to_model_runner_dict`
- [x] Create sensitivity analysis DTOs
- [x] Implement `perform_sensitivity_analysis_with_dtos()`
- [x] Update tornado chart calculations
- [x] Update sensitivity page
- [x] Test sensitivity analysis thoroughly
- [x] Fix battery parameters schema issue

### Week 3: UI Migration ✅
- [x] Create DTO accessor utilities
- [x] Migrate simple display components
- [x] Migrate chart components
- [x] Migrate complex components
- [x] Add feature flag for DTO mode
- [x] Migrate cost breakdown page
- [x] Test all components with both modes

### Week 4: Polish and Cleanup (NEXT)
- [ ] Enable DTO mode by default
- [ ] Remove transformation functions
- [ ] Clean up orchestrator code
- [ ] Update all tests
- [ ] Documentation updates
- [ ] Performance testing
- [ ] Enhance battery replacement calculations

## Testing Strategy

### Unit Tests ✅
- [x] Test new `calculate_comparative_metrics_from_dto()`
- [x] Test new sensitivity analysis functions
- [x] Test DTO accessor utilities
- [ ] Update existing tests to use DTOs only

### Integration Tests ✅
- [x] Test complete calculation flow with DTOs
- [x] Test UI rendering with DTOs
- [x] Test sensitivity analysis end-to-end
- [ ] Test performance improvements

### Manual Testing ✅
- [x] Verify all pages load correctly
- [x] Check all charts render properly
- [x] Validate calculation results match legacy
- [x] Test edge cases and error handling

## Risk Mitigation

### Gradual Migration ✅
- [x] Keep old functions during transition
- [x] Use feature flags
- [x] Test thoroughly at each step
- [x] Maintain backward compatibility

### Data Validation ✅
- [x] Add schema validation for DataFrames
- [x] Log warnings for missing columns
- [x] Provide clear error messages
- [x] Document expected formats

### Performance Monitoring
- [ ] Benchmark before and after changes
- [ ] Monitor memory usage
- [ ] Profile critical paths
- [ ] Optimise as needed

## Success Metrics

### Code Quality
- [x] Modern DTO-based calculate_comparative_metrics
- [x] No dictionary transformations in critical path (with flag)
- [x] Type-safe data access throughout
- [ ] Clean separation of concerns (after cleanup)

### Performance
- [ ] Reduced memory usage (no duplicate structures)
- [ ] Faster calculation times
- [ ] Improved UI responsiveness
- [ ] Efficient data access patterns

### Maintainability
- [x] Single source of truth for data structures
- [x] Clear, documented interfaces
- [ ] Comprehensive test coverage
- [x] Easy to debug and extend

## Next Steps

1. **Immediate**: Monitor DTO mode usage and feedback
2. **This Week**: Enable DTO mode by default
3. **Next Week**: Remove legacy transformation code
4. **Following Week**: Complete cleanup and documentation

## Notes for Implementation

### Performance Benefits of DTO Mode
- Direct attribute access instead of nested dictionary lookups
- No need to create duplicate data structures
- Reduced memory footprint
- Better IDE support and type checking

### Migration Success
- All major UI components now support both modes
- Accessor functions provide seamless compatibility
- Feature flag allows safe rollout
- Test coverage ensures correctness

This plan has been successfully executed through Phase 2.2, with all UI components migrated to support DTO mode. The remaining work focuses on cleanup and optimization once DTO mode is proven stable in production. 