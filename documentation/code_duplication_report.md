# Code Duplication and Naming Issues Report

## Summary
This report documents duplications and naming issues found in the TCO application codebase as of the latest review.

## Completed Fixes (As of Latest Update)

### 1. ✅ `calculate_energy_costs` - RESOLVED
- **Previous Issue**: Duplicated in both `tco_app/domain/energy.py` and `tco_app/src/utils/energy.py`
- **Resolution**: Removed duplicate from `src/utils/energy.py`. All code now uses domain version.
- **Status**: Complete

### 2. ✅ `calculate_emissions` - RESOLVED  
- **Previous Issue**: Duplicated in both `tco_app/domain/energy.py` and `tco_app/src/utils/energy.py`
- **Resolution**: Removed duplicate from `src/utils/energy.py`. All code now uses domain version.
- **Status**: Complete

### 3. ✅ Repository Naming Consistency - RESOLVED
- **Previous Issue**: `ParameterRepository` (singular) vs `ParametersRepository` (plural)
- **Resolution**: Renamed `ParameterRepository` to `ParametersRepository` in `src/utils/data_access.py`
- **Status**: Complete

### 4. ✅ Safe Operations Consolidation - RESOLVED
- **Previous Issues**:
  - `safe_iloc_zero` and `safe_get_first` had overlapping functionality
  - `safe_get_parameter` and `get_parameter_value` had similar purposes
- **Resolution**:
  - Enhanced `safe_get_first` to support both default-return and error-throwing modes
  - Enhanced `get_parameter_value` with `raise_on_missing` parameter
  - `safe_iloc_zero` now uses enhanced `safe_get_first` internally
  - `safe_get_parameter` now uses enhanced `get_parameter_value` internally
- **Status**: Complete - All tests passing

## Remaining Issues

### Import Structure Issues

#### 1. Circular Import Prevention
- Late imports in some modules to avoid circularity
- Indicates potential architectural issues
- **Recommendation**: Review module dependencies

#### 2. Re-exports (Acceptable Pattern)
- `weighted_electricity_price` is defined in `src/utils/energy.py`
- Re-exported from `domain/energy.py`
- **Status**: This pattern is acceptable for API consistency

### Constants Standardisation Issues

#### 1. Emission Constants
- Some modules use `EMISSION_CONSTANTS.DEFAULT_ELECTRICITY_STANDARD`
- Others use `EmissionStandard.GRID.value`
- **Recommendation**: Standardise on enum usage throughout

## Next Steps (Priority Order)

### 1. Constants Standardisation (High Priority)
- Audit all uses of emission constants
- Standardise on `EmissionStandard` enum usage
- Remove redundant constant definitions
- Update any remaining hardcoded values

### 2. Architecture Review (Medium Priority)
- Review module dependencies to identify circular import risks
- Consider restructuring if necessary
- Document any intentional late imports

### 3. Documentation Updates (Low Priority)
- Update docstrings for consolidated functions
- Document the enhanced parameter handling in pandas_helpers
- Update any developer guides that reference the old patterns

## Testing Requirements After Each Change
- Run full test suite
- Pay special attention to:
  - Parameter access functions
  - Safe operations on DataFrames
  - Any code using consolidated functions

## Notes on Acceptable Patterns

### Proxy Pattern (Not Duplication)
- `calculate_payload_penalty_costs` - finance.py proxies to finance_payload.py
- This is intentional for providing a unified API
- No action required

### Re-export Pattern
- Functions defined in utils and re-exported from domain
- This provides a clean API while maintaining implementation separation
- Example: `weighted_electricity_price`

## Conclusion
Major code duplication issues have been resolved. The codebase now has:
- Clear separation between domain logic and utilities
- Consolidated safe operation functions with flexible error handling
- Consistent repository naming conventions
- Reduced redundancy while maintaining backward compatibility

The remaining work focuses on standardising constants usage and reviewing architecture for potential improvements. 