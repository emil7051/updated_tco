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

### 5. ✅ Constants Standardisation - RESOLVED
- **Previous Issues**:
  - Emission constants duplicated between `EmissionConstants` class and `EmissionStandard` enum
  - Hardcoded column names instead of using `DataColumns` enum
  - Hardcoded fuel types and emission standards
  - `SCC_AUD_PER_TONNE` hardcoded in externalities.py
- **Resolution**:
  - Removed duplicate emission constants from config
  - Updated all domain code to use appropriate enums
  - Created `UnitConversions` and `ExternalityConstants` classes
  - Moved all hardcoded constants to centralised configuration
- **Status**: Complete - All production code now uses centralised constants

## Remaining Minor Issues

### 1. Magic Numbers in Code
- Some numeric constants still hardcoded (e.g., 0.05, 365)
- **Priority**: Low - These are mostly in test files or less critical paths
- **Recommendation**: Gradual replacement as code is modified

### 2. Test File Constants
- Test files still use hardcoded values
- **Priority**: Very Low
- **Recommendation**: Consider test independence vs DRY principles case by case

## Architectural Patterns (Not Issues)

### 1. Proxy Pattern (Acceptable)
- `calculate_payload_penalty_costs` - finance.py proxies to finance_payload.py
- This is intentional for providing a unified API
- No action required

### 2. Re-export Pattern (Acceptable)
- Functions defined in utils and re-exported from domain
- This provides a clean API while maintaining implementation separation
- Example: `weighted_electricity_price`

### 3. Late Import Pattern (Acceptable)
- Some modules use late imports to avoid circular dependencies
- This is a valid pattern when necessary
- Document these cases for clarity

## Conclusion

All major code duplication and constant standardisation issues have been resolved. The codebase now has:
- Clear separation between domain logic and utilities
- Consolidated safe operation functions with flexible error handling
- Consistent repository naming conventions
- Centralised constants with type-safe enum usage
- Reduced redundancy while maintaining backward compatibility

The remaining items are minor and can be addressed opportunistically. The code quality has significantly improved with better maintainability and reduced risk of bugs from duplicated or inconsistent code. 