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

### ⚠️ **Issues Discovered**

1. **Battery Parameters Column Mismatch**:
   - The application expects columns named `description` and `default_value`
   - The actual CSV may have different column names (e.g., `battery_description`, `battery_default_value`)
   - This causes warnings but doesn't break functionality

2. **Extensive Dictionary Usage in UI**:
   - UI components and plotters extensively use dictionary access patterns
   - Over 100+ instances of `bev_results["key"]["subkey"]` patterns
   - Complete migration requires updating all these components

## Remaining Work - Detailed Plan

### **Phase 1.2: Update perform_sensitivity_analysis()**
*Priority: High | Estimated Effort: 3-4 days*

**Current Issues**:
- Takes 18+ individual parameters
- Returns legacy dictionary format
- Duplicates calculation logic
- Used by tornado charts and sensitivity page

**Detailed Steps**:

1. **Create SensitivityRequest DTO**:
```python
@dataclass
class SensitivityRequest:
    parameter_name: str
    parameter_range: List[float]
    base_calculation_request: CalculationRequest
    comparison_calculation_request: CalculationRequest
```

2. **Create SensitivityResult DTO**:
```python
@dataclass
class SensitivityResult:
    parameter_value: float
    base_tco_result: TCOResult
    comparison_tco_result: TCOResult
    tco_difference: float
    percentage_difference: float
```

3. **Create new function alongside existing**:
```python
def perform_sensitivity_analysis_with_dtos(
    sensitivity_request: SensitivityRequest,
    tco_service: TCOCalculationService
) -> List[SensitivityResult]:
    """Modern sensitivity analysis using DTOs and service."""
```

4. **Update tornado chart calculation**:
   - Modify `calculate_tornado_data()` to use new function
   - Create adapter if needed for backward compatibility

5. **Update sensitivity UI page**:
   - Modify `_perform_analysis()` to use new function
   - Update `SensitivityContext` to prepare proper DTOs

### **Phase 2.2: Remove UI Transformation Functions**
*Priority: High | Estimated Effort: 4-5 days*

**Current State**:
- `_transform_single_tco_result_for_ui()` converts DTOs back to dictionaries
- All UI components expect dictionary format

**Detailed Migration Strategy**:

1. **Create DTO accessor utilities**:
```python
# In tco_app/ui/utils/dto_accessors.py
def get_tco_per_km(result: Union[TCOResult, Dict]) -> float:
    """Safe accessor that works with both DTOs and dicts during migration."""
    if isinstance(result, TCOResult):
        return result.tco_per_km
    return result.get("tco", {}).get("tco_per_km", 0.0)
```

2. **Migrate components incrementally**:
   - Start with simple display components
   - Move to complex plotters
   - Update one file at a time with testing

3. **Component migration order**:
   - `summary_displays.py` - Simple metric displays
   - `metric_cards.py` - Card-based displays
   - `key_metrics.py` - Key metrics charts
   - `emissions.py` - Emission charts
   - `cost_breakdown.py` - Complex cost breakdowns
   - `sensitivity.py` - Sensitivity charts
   - `tornado.py` - Tornado charts

4. **Testing strategy**:
   - Create test fixture with both DTO and dict versions
   - Ensure output remains identical
   - Run app after each component update

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
- [ ] Day 5: Create sensitivity analysis DTOs

### Week 2: Sensitivity Analysis
- [ ] Day 1: Implement `perform_sensitivity_analysis_with_dtos()`
- [ ] Day 2: Update tornado chart calculations
- [ ] Day 3: Update sensitivity page
- [ ] Day 4: Test sensitivity analysis thoroughly
- [ ] Day 5: Fix battery parameters schema issue

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