### ❏ Codebase Improvement Backlog

Below is a curated backlog of refactoring, debugging and technical	debt tasks that will simplify ongoing implementation. Each item is phrased so it can be lifted straight into a ticketing system.

---
#DONE:

#### 0. High-Priority – Deduplicate Reusable Logic  
*Rationale*: Significant code duplication (price-parity & cumulative cost curves, weighted electricity price logic, charging-mix computation) exists across `calculations.py`, `visualization.py`, `app.py`, and `ui_components.py`. Divergent copies risk silent defects and inflate maintenance costs.  
*Tasks*  
- Extract shared formulas into `tco_app/src/utils/finance.py` (NPV, cumulative-cost, price-parity interpolation) and `tco_app/src/utils/energy.py` (weighted electricity price, charging-mix weighting).  
- Refactor duplicated blocks in all modules to call these utilities.  
- Add regression tests ensuring identical outputs pre-/post-refactor.  
*Effort*: **High**.

**Context snapshot**  
• `tco_app/src/calculations.py` – lines 11-438 house NPV, cumulative-cost and price-parity algorithms.  
• `tco_app/app.py` duplicates these formulas (notably lines 450-478 & 842-920).  
• `tco_app/src/visualization.py` and `tco_app/src/ui_components.py` each redo weighted-electricity-price maths.

**Enhancements / sub-tasks**  
- Create `tco_app/src/utils/finance.py` exporting `npv_constant()`, `cumulative_cost_curve()`, `price_parity_year()`.  
- Create `tco_app/src/utils/energy.py` exporting `weighted_electricity_price()` and `apply_charging_mix()`.  
- Refactor all call-sites in `calculations.py`, `app.py`, `visualization.py`, `ui_components.py` to import these helpers.  
- Delete obsolete duplicated code blocks in callers.

**Definition of done**  
- `ruff --select PLR0915` returns zero duplicate-code warnings.  
- Unit regression `tests/test_regression.py` validating pre- vs post-refactor outputs is green.  
- CI pipeline passes (lint, type-check, tests).

#### 0.1 Medium-Priority – Harmonise Naming Conventions  
*Rationale*: Mixed naming styles (e.g., `msrp_price` vs `battery_capacity_kwh`, inconsistent casing in UI strings) impede searchability and comprehension.  
*Tasks*  
- Establish project-wide naming guidelines (PEP-8 `snake_case` for variables/functions, `PascalCase` for classes, `ALL_CAPS` for constants).  
- Run automated renaming (`ruff`, IDE refactor, or `rope`) for straightforward cases; follow with manual clean-up.  
- Update documentation and comments to reflect standardised names.  
*Effort*: **Medium**.

**Context snapshot**  
• Mixed snake/camel and inconsistent UI labels (e.g. `price_parity_year` v `Payback Period`).  
• Constants such as `'vehicle_drivetrain'`, `'BEV'`, `'Diesel'` repeated across >50 call-sites.  
• Data dictionary field names diverge from code attributes (see Task 0.2).

**Progress (2025-05-19)**  
✅ Created `tco_app/src/constants.py` with `Drivetrain`, `FuelType` enums and shared column-name constants.  
✅ Replaced magic strings `'BEV'`, `'Diesel'`, `'All'` with `Drivetrain` enum in `app.py` & `calculations.py`.  
✅ Added `documentation/naming_map.csv` capturing current→next naming map.  

**Enhancements / sub-tasks – remaining**  
- Add `documentation/naming_map.csv` with columns `current_name,next_name,notes`.  
- Automate renaming using `rope`/`libcst` driven from the map; fallback to manual patches for dynamic attributes.  
- Insert temporary failing test: `assert hasattr(calculations, 'msrp_price') is False` – removed after migration.  
- Update docstrings & markdown examples to new names via search-replace.

**Definition of done**  
- `grep -R "msrpPrice\|BatteryReplacementYear" tco_app | wc -l` → `0`.  
- All unit tests reference new names only.  
- `mypy` strict mode passes.

#TO DO:

#### 0.2 High-Priority – Align Implementation with `calculations.csv`  
*Rationale*: Several metrics defined in the data dictionary are either partially implemented or absent in `calculations.py`, creating analytical gaps and confusing stakeholders when exported tables do not match spec.  
*Observed Divergences*  
- **Missing**: `energy_mj_per_km`, `vehicle_efficiency`, `battery_residual`, `max_range_with_degradation`, `battery_replacement_year`, `monthly_finance_payment`, `total_financing_cost`, `levelised_cost_of_driving`, `tco_with_carbon_price`.  
- **Different naming / semantics**: `price_parity_year` ~= `payback_period`; `tco['tco_per_km']` vs `levelised_cost_of_driving`.  
- **Partial**: NPV calculations include residual value but exclude `npv_externality_cost` for *tco_with_carbon_price*.  
*Tasks*  
- Implement outstanding formulae in dedicated modules, re-using utility functions from Task 0.  
- Map dictionary field names → function outputs; expose via `results` dict for UI and CSV export.  
- Add unit tests comparing computed values with hand-calculated fixtures for at least 10 representative vehicles.  
*Effort*: **High**.

**Context snapshot**  
`calculations.py` currently lacks 9 metrics enumerated in the table below; result dictionaries surfaced to UI omit them, causing CSV exports to diverge from spec.

**Enhancements / sub-tasks**  
- Implement missing formulas in new domain modules (`energy.py`, `finance.py`, `battery.py`, etc.) using utilities from Task 0.  
- Extend `calculate_tco()` return dict to include every dictionary field.  
- Raise `MetricMissingError` whenever a downstream consumer requests an absent metric.  
- Provide conversion helper `kwh_to_mj()` inside `energy.py` for `energy_mj_per_km`.

**Definition of done**  
- `results.keys()` exactly matches `calculations.csv` header.  
- Unit fixtures for 10 vehicles (CSV in `tests/fixtures/`) pass bit-for-bit comparison.  
- Docs: each new function has a one-line formula citation from the dictionary.

| Metric (dictionary field) | Present in data dictionary | Present in code | Variance / Notes | Authoritative source | Reconciliation action |
|---|:---:|:---:|---|---|---|
| `energy_mj_per_km` | ✓ | ✗ | Not calculated anywhere. | Dictionary | Implement helper converting kWh→MJ and litres→MJ; expose in results. |
| `vehicle_efficiency` | ✓ | ✗ | Depends on `energy_mj_per_km`; therefore also missing. | Dictionary | Derive after adding above; return in results/export. |
| `battery_residual` | ✓ | ✗ | Code does not calculate recycling value of battery at end-of-life. | Dictionary | Implement per formula using `recycling_value_percent`. |
| `max_range_with_degradation` | ✓ | ✗ | Degradation model exists but range projection over time is absent. | Dictionary | Add to battery utilities; useful for range-sizing dashboards. |
| `battery_replacement_year` | ✓ | ◐ | Code computes `years_until_replacement` (good) but does not surface value in results. | Code (logic), Dictionary (naming) | Expose computed year as `battery_replacement_year`. |
| `monthly_finance_payment` | ✓ | ✗ | Financing module not implemented at all. | Dictionary | Add finance module; param sources already in `financial_params.csv`. |
| `total_financing_cost` | ✓ | ✗ | Depends on above; likewise missing. | Dictionary | Implement after monthly payment logic. |
| `levelised_cost_of_driving` | ✓ | ✓ (as `tco_per_km`) | Same formula but different name; spec prefers `levelised_cost_of_driving`. | Code (implementation), Dictionary (name) | Alias `tco_per_km` to dictionary name or rename UI label. |
| `tco_with_carbon_price` | ✓ | ✗ | Carbon price captured as input but not added to TCO. | Dictionary | Extend TCO function to include carbon component when price >0. |
| `payback_period` | ✓ | ✓ (as `price_parity_year`) | Code uses cumulative-cost intersection; dictionary formula uses algebraic difference. | Code (richer), Dictionary | Keep code's robust interpolation but rename to `payback_period` for consistency. |
| `diesel_price_breakeven` / `electricity_price_breakeven` / `annual_distance_breakeven` | ✓ | ✗ | Sensitivity engine exists but breakeven solvers not exposed individually. | Dictionary | Add target-search wrappers that call sensitivity until equality achieved. |

*Legend*: ✓ = fully implemented, ◐ = partially, ✗ = absent.

> **Direction**: The data dictionary represents the agreed modelling contract; code should conform to its field names so downstream tools (e.g., BI exports, scenario notebooks) remain stable. Where code already has a superior algorithm (`price_parity_year`), keep the algorithm but adopt dictionary naming to eliminate confusion.

#### 1. Modularise Monoliths  
*Rationale*: `app.py` (≈1&nbsp;450 loc) and `calculations.py` (≈1 440 loc) violate SRP, are brittle to test and hinder re-use.  
*Tasks*  
1.1 Split Streamlit UI concerns into `pages/` or `ui/` modules; keep `main.py` as a thin event orchestrator.  
1.2 Decompose `calculations.py` into domain-oriented packages (`energy.py`, `finance.py`, `battery.py`, `externalities.py`, `sensitivity.py`, etc.).  
1.3 Move plot construction from `visualization.py` into sub-modules that mirror the new calculation structure.  
*Effort*: High (but unlocks most other clean-ups).

**Context snapshot**  
`app.py` → UI + data loading + scenario logic + charts in one file (≈1 450 LOC).  
`calculations.py` lumps unrelated domains (energy, finance, externalities).  
Plot rendering functions in `visualization.py` know too much about calculation internals.

**Enhancements / sub-tasks**  
1. Create `tco_app/main.py` orchestrator (≤50 LOC).  
2. Move Streamlit pages to `tco_app/ui/` (widget code only).  
3. Extract domain packages under `tco_app/domain/` mirroring backlog 0 modules.  
4. Swap imports in `visualization.py` to call new plotting services (e.g. `plotters.cost_breakdown(fig_data)`).

**Definition of done**  
- No Python file >300 LOC.  
- Each module has single responsibility; cyclomatic complexity per function ≤10 (`radon cc -a`).  
- Existing Streamlit routes unchanged for end-users.

#### 2. Introduce Typing & Data Models  
*Rationale*: Heavy pandas look-ups with string keys (`iloc[0]`) are error-prone. Typed models give IDE support and safer refactors.  
*Tasks*  
2.1 Create `dataclasses`/`pydantic` models for `Vehicle`, `Fees`, `Scenario`, `Infrastructure`, etc.  
2.2 Add `typing` annotations throughout; turn `mypy` on in CI.  
*Effort*: Medium.

**Context snapshot**  
Direct pandas row dicts are passed to every calculation; column typos surface at runtime.  
No type-checking; IDE autocomplete is hindered.

**Enhancements / sub-tasks**  
- Introduce `@dataclass` models (`Vehicle`, `Fees`, `Scenario`, `Infrastructure`).  
- Add `from_row(df_row)` constructor for easy dataframe migration.  
- Enable `mypy --strict` in CI; configure `pandas-stubs`.  
- Refactor top-level APIs (`calculate_tco`, etc.) to accept the models.

**Definition of done**  
- `mypy` passes with zero errors.  
- Auto-generated HTML docs via `pdoc` list all models and fields.  
- Example notebook in `documentation/typing_demo.ipynb` shows IDE autocomplete working.

#### 3. Centralised Configuration & Constants  
*Rationale*: Magic strings (e.g. `'diesel_price'`, `'infrastructure_id'`) are scattered across modules.  
*Tasks*  
3.1 Extract constants into `config/constants.py`.  
3.2 Replace string literals and inline numeric defaults with constants or config-file values.  
*Effort*: Low.

**Context snapshot**  
Hard-coded strings like `'diesel_price'` appear ≥20×; maintenance pain and rename risk.

**Enhancements / sub-tasks**  
- Add `config/constants.py` containing `Enum` classes `FinanceKey`, `IncentiveType`, etc.  
- Replace literals with enum usage across codebase using regex replace.  
- Provide helper `get_finance_param(df, FinanceKey.DIESEL_PRICE)` to encapsulate pandas lookup.

**Definition of done**  
- `grep -R "'diesel_price'" tco_app/src | wc -l` returns 0.  
- Static analysis (`flake8-eradicate`) shows no magic strings.  
- Documentation updated with constants reference table.

#### 4. Caching & Performance Optimisation  
*Rationale*: Recalculation occurs on every widget change; some functions scale O(years²).  
*Tasks*  
4.1 Profile hot paths with `@st.cache_data` / memoisation; store expensive NPV & tornado outputs.  
4.2 Vectorise loops over `range(years)` in NPV and cumulative cost methods using NumPy for ~40 × speed-up.  
4.3 Replace `.iterrows()` in efficiency modifiers with boolean masks + assignment.  
*Effort*: Medium.

**Context snapshot**  
`calculate_npv` loops over `range(years)` causing O(N) cost; called inside nested loops for tornado analysis.  
Streamlit re-runs whole pipeline on every widget change.

**Enhancements / sub-tasks**  
- Replace looped NPV with `numpy_financial.npv` or vectorised formula.  
- Memoise pure functions with `@functools.cache` or `st.cache_data`.  
- Benchmark with `pytest-benchmark` before/after.

**Definition of done**  
- `pytest --benchmark-only` shows ≥20× speed-up on NPV hotspot.  
- Streamlit slider interaction latency <300 ms measured via built-in profiler.

#### 5. Robust Error Handling  
*Rationale*: Indexing via `.iloc[0]` without checks crashes when tables change.  
*Tasks*  
5.1 Implement helper `safe_lookup(df, expr, default=...)` raising `LookupError` with informative message.  
5.2 Replace bare `print` warnings with Python `logging` + Streamlit status messages.  
*Effort*: Low–Medium.

**Context snapshot**  
Frequent `df[df[col]==val].iloc[0]` patterns crash with `IndexError` when upstream filters change.  
User currently sees blank white Streamlit screen.

**Enhancements / sub-tasks**  
- Implement `safe_lookup(df, expr, default=...)` raising `LookupError` with informative message.  
- Replace all raw `.iloc[0]` hot-points.  
- Integrate `logging` configured via `logging.config.dictConfig` for server logs and `st.error` for UI.

**Definition of done**  
- Simulated missing row returns graceful error banner, no stack trace.  
- 100 % coverage for `safe_lookup` branch conditions.

#### 6. Unit & Regression Test Suite  
*Rationale*: No automated tests; high regression risk as formulas evolve.  
*Tasks*  
6.1 Scaffold `tests/` with `pytest`, `pytest-cov`, `pytest-benchmark`, `pytest-snapshot`.  
6.2 Golden-value tests for each calculation function using fixture CSVs.  
6.3 Snapshot tests for NPV, price-parity interpolation, externality aggregation.  
*Effort*: Medium.

**Context snapshot**  
No `tests/` directory exists; manual testing only.

**Enhancements / sub-tasks**  
- Scaffold `tests/` with `pytest`, `pytest-cov`, `pytest-benchmark`, `pytest-snapshot`.  
- Add golden-value CSV fixtures under `tests/fixtures/` captured from current `app.py` run.  
- Introduce CI matrix job `tox -e py,lint,mypy,tests`.

**Definition of done**  
- `pytest -q` green; coverage ≥80 %.  
- Snapshot of Plotly figure JSON passes ensuring visual outputs remain stable.

#### 7. Linting & Formatting  
*Rationale*: Inconsistent style, long lines and trailing whitespace.  
*Tasks*  
7.1 Add `ruff`/`flake8` and `black` pre-commit hooks.  
7.2 Resolve style infractions & unused imports.  
*Effort*: Low.

**Context snapshot**  
Mix of tabs/spaces and trailing whitespace; Ruff reports >300 issues (`ruff check`).

**Enhancements / sub-tasks**  
- Add `.pre-commit-config.yaml` with `black`, `ruff`, `isort`, `nbstripout`.  
- Run `black . && ruff --fix` once to normalise code.  
- Configure CI to fail if formatting differs (`ruff format --check`).

**Definition of done**  
- `ruff check` returns zero infractions.  
- Pre-commit hook runs in <3s on staged files.

#### 8. Data-Layer Abstraction  
*Rationale*: `data_loading.load_data()` hard-codes local relative path `./data/tables` and mixes IO with business logic.  
*Tasks*  
8.1 Parameterise data directory via `env` or CLI arg.  
8.2 Use a thin repository pattern (`TableRepository`) to decouple pandas from business logic.  
*Effort*: Low.

**Context snapshot**  
`data_loading.load_data()` hard-codes local relative path `./data/tables` and mixes IO with business logic.

**Enhancements / sub-tasks**  
- Create `TableRepository` protocol with `get(table_name)` and `list_tables()` signatures.  
- Implement `CSVRepository` and `ParquetRepository`.  
- Inject repository into calculation functions (dependency inversion).  
- Parameterise data directory via `TCO_DATA_DIR` env var.

**Definition of done**  
- Changing `--data-dir` CLI flag or env var reloads alternative dataset without code change.  
- Unit test mocks repo via `pytest-mock`.

#### 9. Scenario & Sensitivity Engine Refactor  
*Rationale*: Scenario mutations currently copy entire DataFrames and iterate row-wise; difficult to extend.  
*Tasks*  
9.1 Refactor `apply_scenario_parameters()` into declarative mapping engine based on YAML/JSON manifests.  
9.2 Generalise sensitivity analysis to accept arbitrary lambda and return structured results suitable for plotting.  
*Effort*: High.

**Context snapshot**  
Scenario parameters currently applied imperatively inside `app.apply_scenario_parameters` causing DataFrame copies and row-wise loops.

**Enhancements / sub-tasks**  
- Define YAML schema `scenarios/*.yml` listing parameter overrides.  
- Implement declarative engine reading schema → transformations pipeline.  
- Ensure idempotent: re-applying same scenario twice yields identical table (hash check).  
- Provide `SensitivityRunner` class supporting arbitrary lambda calc.

**Definition of done**  
- Editing YAML and reloading Streamlit reflects changes immediately.  
- Sensitivity API returns pandas DataFrame with columns `parameter,value,bev_tco,diesel_tco,diff`.  
- Benchmarked execution time ≤ 1.5× current performance despite flexibility.

#### 10. Infrastructure & Incentive Logic Consolidation  
*Rationale*: Incentive application duplicated across acquisition, annual cost and infrastructure functions.  
*Tasks*  
10.1 Create `IncentiveService` that exposes `apply(vehicle, category)` and returns discounted figures.  
10.2 Remove duplicated checks (`if incentive_type == 'purchase_rebate_aud'` etc.) from each calculation.  
*Effort*: Medium.

**Context snapshot**  
`purchase_rebate_aud`, `registration_exemption`, `electricity_rate_discount` conditional blocks duplicated in 3+ modules.

**Enhancements / sub-tasks**  
- Create `IncentiveType(Enum)` with mapping to calculation strategy.  
- Implement `IncentiveService.apply(vehicle, fee_category)` returning discounted values.  
- Replace conditional chains with polymorphic dispatch.  
- Unit test each incentive type using parametrised fixtures.

**Definition of done**  
- New code path reduces 100+ LOC duplication.  
- Adding a new incentive requires only updating enum and strategy, no caller changes.

#### 11. Improved State Management in Streamlit  
*Rationale*: Re-computing unchanged results wastes CPU; state duplication across tabs causes inconsistent displays.  
*Tasks*  
11.1 Store heavy results (`bev_results`, `diesel_results`) in `st.session_state`.  
11.2 Use callbacks to update only affected sub-trees when inputs change.  
*Effort*: Low-Medium.

#### 12. Accessibility & UX Polish  
*Rationale*: Hard-coded font sizes/colours in HTML strings hinder theming and screen-reader friendliness.  
*Tasks*  
12.1 Replace raw HTML metric cards with Streamlit `st.metric` or `st.columns` for semantic markup.  
12.2 Add alt-text to all Plotly figures; ensure tab order logical.  
*Effort*: Low.

#### 13. Environment & Dependency Harmonisation  
*Rationale*: Two `venv/` directories inflate repo & risk package drift.  
*Tasks*  
13.1 Delete committed virtual-envs; add them to `.gitignore`.  
13.2 Promote single `pyproject.toml` or `requirements.lock` at repo root; pin package versions.  
*Effort*: Low.

#### 14. Continuous Integration & Deployment  
*Rationale*: No pipeline yet; manual deploys are fragile.  
*Tasks*  
14.1 Add GitHub Actions workflow: lint → type-check → tests → Streamlit deployment.  
14.2 Publish Dockerfile for reproducible prod image (mounts `/data` at runtime).  
*Effort*: Medium.

#### 15. Documentation Alignment & API Docs  
*Rationale*: PRD describes future features (Monte-Carlo, account system) not yet reflected in code.  
*Tasks*  
15.1 Update `documentation/README.md` with current feature flags & endpoints.  
15.2 Auto-generate API docs via `mkdocs` or `pdoc`, linking to calculation formulas.  
*Effort*: Low.

---

### ⬇️ Ticket boiler-plate (copy into issue description)
```
**Context**
<one-sentence on current implementation>

**Required change**
<concise description of new behaviour / refactor>

**Definition of done**
- [ ] Lint passes (ruff, black)
- [ ] Typing passes (mypy --strict)
- [ ] Unit tests & golden fixtures green
- [ ] Benchmarks/regressions unchanged or improved
```

---

**Legend**  
• _Low_ = <½ day • _Medium_ = ½–2 days • _High_ = >2 days  

This backlog should clear the path for feature work while keeping the codebase maintainable and testable. 