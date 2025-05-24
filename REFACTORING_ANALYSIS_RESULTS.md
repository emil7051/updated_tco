# TCO App Static Analysis Results and Refactoring Plan

## Executive Summary

This document presents the results of running static analysis tools (vulture, jscpd, black, flake8, radon) on the TCO app codebase and provides a prioritized refactoring plan to address the identified issues.

## Static Analysis Results

### 1. Vulture - Dead Code Detection (Exit Code: 3)

**Findings:**
- 54 instances of potentially unused code (60% confidence)
- Key unused items include:
  - Multiple unused variables in `services/dtos.py` (npv_infrastructure_cost, emissions fields)
  - Unused method `_convert_tco_result_to_model_runner_dict` in tco_calculation_service.py
  - Unused configuration constants in `src/config.py`
  - ~~Unused functions in `services/data_cache.py` (cached_vehicle_lookup)~~
  - Dead code removed: `cached_vehicle_lookup` has been deleted from `services/data_cache.py`
  - Unused class `EnergyCalculator` in `ui/calculations/energy_calculations.py`

### 2. JSCPD - Code Duplication (1.74% duplication)

**Findings:**
- 10 code clones found across 82 files
- Main duplication areas:
  - Test setup code in model_runner tests (3 clones, ~17-19 lines each)
  - Test fixtures duplicated between unit and integration tests
  - Similar calculation logic in `domain/sensitivity/single_param.py` and `tornado.py`
  - Cost calculation patterns duplicated between `plotters/cost_breakdown.py` and `domain/sensitivity/metrics.py`

### 3. Black - Code Formatting (93 files need reformatting)

**Major Issues:**
- Inconsistent line lengths (many > 79 chars)
- Inconsistent quote usage (mix of single and double)
- Improper line breaks in long function calls
- Inconsistent spacing around operators

### 4. Flake8 - Style and Quality Issues (3,689 total issues)

**Top Issues by Category:**
- **1,841 W191**: Indentation contains tabs (mixed tabs/spaces)
- **665 E501**: Line too long (up to 196 chars, limit 79)
- **622 W293**: Blank line contains whitespace
- **198 W291**: Trailing whitespace
- **93 W292**: No newline at end of file
- **49 F401**: Imported but unused
- **13 F405**: May be undefined (star imports)

**Critical Issues:**
- Mixed tabs and spaces in indentation (particularly in `ui/pages/sensitivity.py`)
- Undefined names due to star imports
- Lambda expressions instead of functions
- Module-level imports not at top of file

### 5. Radon - Complexity Analysis

**Overall Metrics:**
- Total blocks analyzed: 155,887
- Average complexity: A (2.20) - Good overall
- Most complex function: `calculate_comparative_metrics` in `domain/sensitivity/metrics.py` (Complexity: C, score 15)

**High Complexity Areas:**
- `domain/sensitivity/metrics.py`: calculate_comparative_metrics (C - 15)
- `services/scenario_application_service.py`: Multiple methods with B complexity (6-9)
- `domain/finance.py`: Multiple functions with B complexity (7-8)
- `domain/externalities.py`: calculate_externalities (B - 8)

## Prioritized Refactoring Plan

### Phase 1: Critical Issues (Week 1)

#### 1.1 Fix Indentation Issues (Day 1-2)
- **Priority**: CRITICAL
- **Files**: All files with W191 errors, especially `ui/pages/sensitivity.py`
- **Action**: 
  - Configure editor to use spaces only (4 spaces per indent)
  - Run `black` to auto-fix formatting
  - Manually review mixed indentation files

#### 1.2 Apply Black Formatting (Day 2-3)
- **Priority**: HIGH
- **Action**:
  ```bash
  black tco_app/ --exclude venv
  ```
- **Benefits**: Consistent code style, automatic line length fixes

#### 1.3 Fix Import Issues (Day 3-4)
- **Priority**: HIGH
- **Actions**:
  - Remove all star imports (`from .vehicles import *`)
  - Fix undefined names (F405 errors)
  - Remove unused imports (F401 errors)
  - Move module-level imports to top of files

#### 1.4 Remove Dead Code (Day 4-5)
- **Priority**: MEDIUM
- **Actions**:
  - Remove unused variables in DTOs
  - Delete unused `EnergyCalculator` class
  - Remove or implement unused methods
  - Clean up unused configuration constants

### Phase 2: Code Quality (Week 2)

#### 2.1 Reduce Complexity (Day 1-3)
- **Priority**: HIGH
- **Focus**: `calculate_comparative_metrics` function
- **Actions**:
  - Extract calculation logic into smaller functions
  - Create dedicated methods for:
    - TCO difference calculations
    - Operating cost comparisons
    - Emission calculations
    - Abatement cost logic

#### 2.2 Eliminate Code Duplication (Day 3-4)
- **Priority**: MEDIUM
- **Actions**:
  - Create shared test fixtures module
  - Extract common calculation patterns into utility functions
  - Consolidate duplicate sensitivity analysis logic

#### 2.3 Fix Remaining Flake8 Issues (Day 4-5)
- **Priority**: MEDIUM
- **Actions**:
  - Replace lambda expressions with functions
  - Fix variable naming (ambiguous names)
  - Clean up whitespace issues
  - Add missing newlines at end of files

### Phase 3: Testing and Documentation (Week 3)

#### 3.1 Increase Test Coverage (Day 1-3)
- **Priority**: HIGH
- **Current**: 8.79%
- **Target**: 40%+
- **Focus Areas**:
  - Complex calculation functions
  - Service layer methods
  - Error handling paths

#### 3.2 Add Type Hints (Day 3-4)
- **Priority**: MEDIUM
- **Actions**:
  - Add type hints to all public functions
  - Use Python 3.9-compatible syntax
  - Run mypy for type checking

#### 3.3 Documentation Updates (Day 4-5)
- **Priority**: LOW
- **Actions**:
  - Update docstrings for complex functions
  - Document calculation algorithms
  - Create architecture documentation

## Implementation Guidelines

### Setup
1. Create a new branch: `refactoring/static-analysis-fixes`
2. Set up pre-commit hooks:
   ```bash
   pip install pre-commit
   pre-commit install
   ```

### Pre-commit Configuration (.pre-commit-config.yaml)
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        args: [--line-length=88]
        exclude: venv/

  - repo: https://github.com/PyCQA/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203]
        exclude: venv/

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: mixed-line-ending
```

### Testing Strategy
1. Run tests after each major change
2. Use coverage.py to track progress:
   ```bash
   pytest --cov=tco_app --cov-report=html
   ```
3. Focus on high-value test cases first

### Code Review Checklist
- [ ] All tabs converted to spaces
- [ ] No lines > 88 characters
- [ ] No unused imports or variables
- [ ] All functions have type hints
- [ ] Complex functions broken down (complexity <= B)
- [ ] No code duplication > 10 lines
- [ ] Test coverage increased
- [ ] All flake8 issues resolved

## Expected Outcomes

1. **Code Quality**: Move from 3,689 style issues to < 50
2. **Maintainability**: Reduce average complexity from C to B for complex modules
3. **Test Coverage**: Increase from 8.79% to 40%+
4. **Consistency**: 100% Black-formatted code
5. **Type Safety**: Full type hint coverage

## Monitoring Progress

Track progress using:
```bash
# Check remaining issues
flake8 tco_app/ --count --exclude=venv

# Check complexity
radon cc tco_app/ -as --exclude="venv/*" | grep -E "^\s+[C-F]"

# Check formatting
black tco_app/ --check --exclude venv

# Check test coverage
pytest --cov=tco_app --cov-report=term-missing
```

## Next Steps

1. Review and approve this plan
2. Create feature branch
3. Set up pre-commit hooks
4. Begin Phase 1 implementation
5. Daily progress updates
6. Weekly demos of improvements
