# Legacy Code Deprecation Plan

## Overview

The TCO application is currently in a transitional state where modern DTOs (Data Transfer Objects) coexist with legacy dictionary-based data structures. This creates unnecessary complexity, performance overhead, and maintenance burden. This document outlines a systematic plan to complete the modernisation and remove legacy compatibility layers.

## Current State Analysis

### ✅ **Modernised Components**
- **Data Loading**: Uses repository pattern with clean interfaces
- **Data Access**: Structured repositories with type safety
- **Core DTOs**: `CalculationParameters`, `CalculationRequest`, `TCOResult`, `ComparisonResult`
- **Service Layer**: `TCOCalculationService` uses DTOs internally

### ⚠️ **Legacy Components Requiring Migration**
- **Domain Functions**: Still expect dictionary formats
- **Conversion Functions**: Bridge between DTOs and legacy code
- **Sensitivity Analysis**: Uses individual parameters instead of DTOs
- **UI Transformation**: Converts DTOs back to dictionaries

## Migration Plan

### **Phase 1: Modernise Domain Functions** 
*Priority: High | Estimated Effort: 2-3 days*

#### 1.1 Update `calculate_comparative_metrics()`
**File**: `tco_app/domain/sensitivity/metrics.py`

**Current Signature**:
```python
def calculate_comparative_metrics(
    bev_results: Dict[str, Any],
    diesel_results: Dict[str, Any], 
    annual_kms: int,
    truck_life_years: int,
) -> Dict[str, Any]:
```

**Target Signature**:
```python
def calculate_comparative_metrics(
    comparison_result: ComparisonResult
) -> Dict[str, Any]:
```

**Steps**:
1. Create new function signature accepting `ComparisonResult`
2. Extract required data from `comparison_result.base_vehicle_result` and `comparison_result.comparison_vehicle_result`
3. Update all call sites in `TCOCalculationService.compare_vehicles()`
4. Remove old function signature
5. Update unit tests

#### 1.2 Update `perform_sensitivity_analysis()`
**File**: `tco_app/domain/sensitivity/single_param.py`

**Current Issues**:
- Takes 18+ individual parameters
- Returns legacy dictionary format
- Duplicates calculation logic

**Target Approach**:
```python
def perform_sensitivity_analysis(
    parameter_name: str,
    parameter_range: List[Any],
    base_request: CalculationRequest,
    comparison_request: CalculationRequest,
    tco_service: TCOCalculationService
) -> List[SensitivityResult]:
```

**Steps**:
1. Create `SensitivityResult` DTO
2. Refactor function to use `CalculationRequest` DTOs
3. Use `TCOCalculationService` for calculations instead of duplicating logic
4. Update tornado chart calculations
5. Update sensitivity page to use new format

### **Phase 2: Remove Conversion Functions**
*Priority: High | Estimated Effort: 1-2 days*

#### 2.1 Remove `convert_tco_result_to_model_runner_dict()`
**File**: `tco_app/services/helpers/__init__.py`

**Steps**:
1. Verify no remaining usage after Phase 1 completion
2. Remove function from `__all__` exports
3. Delete function implementation
4. Remove from imports in `tco_calculation_service.py`

#### 2.2 Remove `_transform_single_tco_result_for_ui()`
**File**: `tco_app/ui/orchestration/calculation_orchestrator.py`

**Steps**:
1. Update UI components to work directly with DTOs
2. Remove transformation function
3. Simplify `_transform_results_for_ui()` method
4. Update UI pages to access DTO properties directly

### **Phase 3: Modernise UI Layer**
*Priority: Medium | Estimated Effort: 2-3 days*

#### 3.1 Update UI Components
**Files**: `tco_app/ui/components/*.py`

**Current Issues**:
- Components expect legacy dictionary format
- Accessing nested dictionary keys like `results["tco"]["npv_total_cost"]`

**Target Approach**:
- Components accept DTOs directly
- Access properties like `result.tco_total_lifetime`

**Steps**:
1. Update `display_summary_metrics()` to accept `TCOResult` objects
2. Update `display_comparison_metrics()` to accept `ComparisonResult`
3. Update all chart/plotter functions to use DTOs
4. Remove dictionary key access patterns

#### 3.2 Update Context Management
**File**: `tco_app/ui/context/context.py`

**Steps**:
1. Return DTOs directly from `get_context()`
2. Update session state caching to store DTOs
3. Remove dictionary transformation in orchestrator

### **Phase 4: Clean Up and Optimisation**
*Priority: Low | Estimated Effort: 1 day*

#### 4.1 Remove Legacy Comments and References
**Files**: Multiple

**Items to Remove**:
- Comments mentioning "model_runner"
- "# Domain module imports - to be reviewed based on model_runner logic"
- "# Used by model_runner"
- References to "historical model_runner dictionary structure"

#### 4.2 Update Import Statements
**Steps**:
1. Remove unused imports from conversion functions
2. Clean up import statements in service files
3. Update `__all__` exports in helper modules

#### 4.3 Optimise Performance
**Steps**:
1. Remove unnecessary data copying between formats
2. Optimise DTO field access patterns
3. Review caching strategy for DTOs

### **Phase 5: Testing and Validation**
*Priority: High | Estimated Effort: 2 days*

#### 5.1 Update Test Suite
**Steps**:
1. Update unit tests to use DTOs instead of dictionaries
2. Update integration tests for new function signatures
3. Add tests for DTO validation and type safety
4. Update end-to-end tests

#### 5.2 Performance Testing
**Steps**:
1. Benchmark calculation performance before/after
2. Verify memory usage improvements
3. Test UI responsiveness with DTO-based rendering

## Implementation Order

### **Week 1: Core Domain Migration**
- [ ] Day 1-2: Update `calculate_comparative_metrics()`
- [ ] Day 3-4: Update `perform_sensitivity_analysis()`
- [ ] Day 5: Testing and validation

### **Week 2: Remove Legacy Layers**
- [ ] Day 1: Remove conversion functions
- [ ] Day 2-3: Update UI components
- [ ] Day 4: Update context management
- [ ] Day 5: Testing and integration

### **Week 3: Polish and Optimisation**
- [ ] Day 1: Clean up comments and imports
- [ ] Day 2: Performance optimisation
- [ ] Day 3-4: Comprehensive testing
- [ ] Day 5: Documentation updates

## Risk Mitigation

### **Backwards Compatibility**
- Keep old functions temporarily with deprecation warnings
- Use feature flags to toggle between old/new implementations
- Maintain comprehensive test coverage during transition

### **Testing Strategy**
- Run parallel implementations during transition
- Compare outputs to ensure consistency
- Gradual rollout with rollback capability

### **Performance Monitoring**
- Benchmark key operations before changes
- Monitor memory usage and calculation speed
- Profile UI rendering performance

## Success Criteria

### **Code Quality**
- [ ] Zero legacy dictionary-based data flows
- [ ] All functions use typed DTOs
- [ ] No conversion functions between formats
- [ ] Clean, consistent import statements

### **Performance**
- [ ] No performance regression in calculations
- [ ] Improved memory usage (no duplicate data structures)
- [ ] Faster UI rendering (direct DTO access)

### **Maintainability**
- [ ] Single source of truth for data structures
- [ ] Type safety throughout the application
- [ ] Simplified debugging and testing
- [ ] Clear, modern code patterns

## Files Affected

### **High Impact Changes**
- `tco_app/domain/sensitivity/metrics.py`
- `tco_app/domain/sensitivity/single_param.py`
- `tco_app/services/helpers/__init__.py`
- `tco_app/ui/orchestration/calculation_orchestrator.py`

### **Medium Impact Changes**
- `tco_app/ui/components/*.py`
- `tco_app/ui/pages/*.py`
- `tco_app/ui/context/context.py`
- `tco_app/services/tco_calculation_service.py`

### **Low Impact Changes**
- `tco_app/plotters/*.py`
- Test files throughout the codebase
- Documentation files

## Post-Migration Benefits

### **Developer Experience**
- **Type Safety**: Full IntelliSense support and compile-time error checking
- **Debugging**: Clear data structures instead of nested dictionaries
- **Testing**: Easier to mock and validate structured data

### **Performance**
- **Memory**: Eliminate duplicate data structures
- **Speed**: Direct property access instead of dictionary lookups
- **Caching**: More efficient caching of structured objects

### **Maintainability**
- **Single Source of Truth**: One data structure per concept
- **Refactoring**: Safe refactoring with type checking
- **Documentation**: Self-documenting code with typed interfaces

## Conclusion

This migration plan will complete the modernisation of the TCO application's data layer, eliminating legacy compatibility code and establishing a clean, type-safe architecture. The phased approach minimises risk while delivering incremental benefits throughout the process.

The end result will be a more maintainable, performant, and developer-friendly codebase that fully leverages modern Python patterns and type safety. 