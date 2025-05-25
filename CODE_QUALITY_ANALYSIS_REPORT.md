# Code Quality Analysis Report

**Generated on:** 2025-05-24T17:25:15+10:00  
**Project:** TCO App (Total Cost of Ownership)  
**Tools Used:** Black, Flake8, Vulture, JSCPD, Radon, pytest coverage

## Executive Summary

| Metric | Current Status | Target/Good |
|--------|---------------|-------------|
| **Test Coverage** | 66.31% | 40%+ |
| **Code Formatting** | 13 files need reformatting | 0 |
| **Style Issues** | 553 flake8 violations | <50 |
| **Dead Code** | 69 unused items | 0 |
| **Code Duplication** | 1.31% (10 clones) | <5% |
| **Complex Functions** | 1 high complexity (C-15) | <C-10 |

**Overall Status:** 🟨 **MODERATE** - Good coverage but needs formatting and style improvements

---

## 1. Code Formatting Issues (Black)

### Status: ❌ **13 files need reformatting**

**Files requiring Black formatting:**
- `tco_app/domain/energy.py`
- `tco_app/domain/externalities.py`
- `tco_app/domain/finance.py`
- `tco_app/domain/finance_payload.py`
- `tco_app/domain/sensitivity/metrics.py`
- `tco_app/domain/sensitivity/single_param.py`
- `tco_app/domain/sensitivity/tornado.py`
- `tco_app/tests/unit/domain/test_finance.py`
- `tco_app/tests/unit/domain/sensitivity/test_metrics.py`
- 4 additional files

**Recommended Action:**
```bash
python3 -m black tco_app/ --exclude venv
```

---

## 2. Style Issues (Flake8)

### Status: ❌ **553 total violations**

### Critical Issues (High Priority)

#### 2.1 Import Issues (70 violations)
- **42 F401**: Unused imports - significant cleanup needed
- **10 F811**: Redefinition of unused variables
- **3 E402**: Module-level imports not at top of file

**Key Files with Import Issues:**
- `tco_app/tests/unit/domain/test_finance.py`: Multiple redefinitions
- `tco_app/ui/builders/parameter_builder.py`: Unused UI_CONFIG import
- Various test files: Unused pytest, mock imports

#### 2.2 Indentation Issues (4 violations)
- **2 W191**: Tab characters in `ui/pages/sensitivity.py` (lines 76-77)
- **2 E101**: Mixed spaces and tabs
- **1 E111**: Incorrect indentation multiple

#### 2.3 Line Length Issues (202 violations)
- **202 E501**: Lines exceeding 88 characters
- Primarily in `ui/calculation_orchestrator.py` (24 violations)
- Multiple test files with long assertion lines

### Moderate Issues (Medium Priority)

#### 2.4 Whitespace Issues (94 violations)
- **36 W291**: Trailing whitespace
- **57 W293**: Blank lines with whitespace
- **1 W391**: Blank line at end of file

#### 2.5 Code Quality Issues (8 violations)
- **2 F541**: f-strings missing placeholders
- **1 E741**: Ambiguous variable name 'l'
- **2 F821**: Undefined names

---

## 3. Dead Code Analysis (Vulture)

### Status: ⚠️ **69 unused items detected**

### Critical Dead Code (Remove)

#### 3.1 Configuration Constants (Never Used)
**File:** `tco_app/src/config.py`
- `DEFAULT_DISCOUNT_RATE`, `DEFAULT_TRUCK_LIFE_YEARS`, `DEFAULT_ANNUAL_KMS`
- `MIN_DISCOUNT_RATE`, `MAX_DISCOUNT_RATE`
- `SENSITIVITY_VARIANCE_FACTOR`, `DEFAULT_SENSITIVITY_POINTS`
- `USE_CONTAINER_WIDTH`, `LRU_CACHE_SIZE`
- `CURRENCY_PRECISION`, `PERCENTAGE_PRECISION`, `RATIO_PRECISION`

#### 3.2 Data Column Constants (Never Used)
**File:** `tco_app/src/constants.py`
- Vehicle: `VEHICLE_NAME`, `PAYLOAD_TONNES`, `MAX_ANNUAL_DISTANCE_KM`
- Financial: `TRUCK_LIFE`, `ANNUAL_KMS`, `RESIDUAL_VALUE_PCT`
- Maintenance: `MAINTENANCE_BASE_COST`, `MAINTENANCE_COST_PER_KM`
- Incentives: `INCENTIVE_FLAG`, `INCENTIVE_TYPE`, `INCENTIVE_RATE`
- Externalities: `VEHICLE_CLASS`, `POLLUTANT_TYPE`, `COST_PER_KM`

#### 3.3 Legacy Methods (Remove)
- `tco_app/services/tco_calculation_service.py:382`: `_convert_tco_result_to_model_runner_dict`
- `tco_app/src/utils/data_access.py:44`: `get_all` method
- `tco_app/src/utils/data_access.py:48`: `clear_cache` method

### Test-Related Dead Code (Review)

#### 3.4 Test Variables and Functions
- Multiple `unused variable` issues in test files
- `unused attribute 'side_effect'` in mock configurations
- Test fixture functions that may be reusable

---

## 4. Code Duplication Analysis (JSCPD)

### Status: ✅ **Low duplication (1.31%)**

**Overall Duplication:** 158 lines out of 12,046 (1.31%)

### Identified Clones (10 instances)

#### 4.1 Test Code Duplication (Priority: Low)
**Most Significant:**
- `test_metrics.py`: 4 similar test method structures (17-18 lines each)
- `test_finance_payload.py`: Repeated test setup patterns (13 lines)
- `test_calculation_delegation.py` vs `test_calculations.py`: Similar test fixtures

#### 4.2 Business Logic Duplication (Priority: Medium)
- `domain/finance.py`: Internal method duplication (10 lines)
- `domain/sensitivity/single_param.py` vs `tornado.py`: Parameter processing logic (11 lines)

**Recommendation:** Test duplication is acceptable; focus on business logic refactoring.

---

## 5. Complexity Analysis (Radon)

### Status: ⚠️ **1 high complexity function**

#### 5.1 High Complexity Functions
**File:** `tco_app/domain/sensitivity/metrics.py`
- `calculate_comparative_metrics` - **Complexity: C (15)**
  - **Issue:** Complex nested calculations and multiple conditional paths
  - **Lines:** Multiple price parity calculations, cost comparisons, infrastructure handling

#### 5.2 Complexity Distribution in Application Code
- **A (1-5):** Majority of functions ✅
- **B (6-10):** Several functions ⚠️
- **C (11-20):** 1 function (needs refactoring) ❌
- **D+ (21+):** 0 functions ✅

**Note:** Virtual environment shows many D/E/F complexity functions, but these are external dependencies.

---

## 6. Test Coverage Analysis

### Status: ✅ **Excellent coverage (66.31%)**

**Target:** 40% | **Actual:** 66.31% | **Status:** EXCEEDS TARGET

#### 6.1 High Coverage Modules (>90%)
- `domain/finance.py`: 91.47%
- `domain/finance_payload.py`: 100%
- `services/tco_calculation_service.py`: 97.62%
- `services/data_cache.py`: 96.30%
- `src/exceptions.py`: 92.59%

#### 6.2 Low Coverage Modules (<50%)
- `main.py`: 0% (entry point, acceptable)
- `plotters/*`: 8-26% (UI visualization, lower priority)
- `ui/summary_displays.py`: 12.20%
- `ui/metric_cards.py`: 10.87%

#### 6.3 Missing Test Lines
**Critical missing coverage:**
- Error handling paths in domain modules
- UI component edge cases
- Repository error scenarios

---

## 7. Recommendations & Action Plan

### Phase 1: Critical Fixes (Week 1)
1. **Fix Indentation Issues**
   ```bash
   # Fix mixed tabs/spaces in sensitivity.py
   sed -i 's/\t/    /g' tco_app/ui/pages/sensitivity.py
   ```

2. **Apply Black Formatting**
   ```bash
   python3 -m black tco_app/ --exclude venv
   ```

3. **Remove Critical Dead Code**
   - Delete unused configuration constants
   - Remove legacy method `_convert_tco_result_to_model_runner_dict`

### Phase 2: Quality Improvements (Week 2)
1. **Clean Up Imports**
   - Remove 42 unused imports identified by flake8
   - Fix import order issues

2. **Refactor Complex Function**
   - Break down `calculate_comparative_metrics` into smaller functions
   - Target complexity reduction from C-15 to B-8 or lower

3. **Fix Line Length Issues**
   - Prioritize `ui/calculation_orchestrator.py` (24 violations)
   - Use Black's automatic line breaking where possible

### Phase 3: Polish (Week 3)
1. **Remove Whitespace Issues**
   - Strip trailing whitespace
   - Clean up blank lines

2. **Address Code Duplication**
   - Extract common test setup patterns
   - Refactor business logic duplication in domain/sensitivity

3. **Improve Test Coverage**
   - Focus on error handling paths
   - Add edge case testing for complex calculations

### Automated Quality Gates
```bash
# Set up pre-commit hooks
pip install pre-commit
echo "
repos:
- repo: https://github.com/psf/black
  rev: 23.0.0
  hooks:
  - id: black
- repo: https://github.com/pycqa/flake8
  rev: 6.0.0
  hooks:
  - id: flake8
    args: [--max-line-length=88]
" > .pre-commit-config.yaml

pre-commit install
```

---

## 8. Metrics Summary

| Category | Before | Target | Current Status |
|----------|--------|--------|----------------|
| **Test Coverage** | - | 40% | ✅ 66.31% |
| **Formatting** | - | 100% | ❌ 85.7% (79/92 files) |
| **Style Issues** | - | <50 | ❌ 553 issues |
| **Dead Code** | - | 0 items | ❌ 69 items |
| **Duplication** | - | <5% | ✅ 1.31% |
| **Max Complexity** | - | <C-10 | ⚠️ C-15 |

**Progress Score: 3/6 Targets Met** 🟨

The codebase shows excellent test coverage and low duplication, but requires formatting standardization, style cleanup, and complexity reduction to achieve production-ready quality standards.
