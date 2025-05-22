# Modularisation PRD – Monolith Decomposition (Steps 1.1 – 1.3)

## 1. Purpose

The purpose of this refactor is to break the `tco_app` monoliths (`app.py`, `calculations.py`, `visualization.py`) into cohesive, domain-focused packages without changing external behaviour.  This will:

* Cut the average change-set blast radius, reducing merge conflicts.
* Enable selective re-runs in Streamlit, boosting interactivity speed.
* Eradicate duplicated business logic by enforcing single sources of truth.

## 2. Scope

Included:

* 1.1 Streamlit UI extraction (`app.py` → `ui/` pages & `main.py`).
* 1.2 Domain split of `calculations.py` into dedicated packages under `tco_app/domain/*`.
* 1.3 Plot build logic relocation from `visualization.py` into `tco_app/plotters/*`.

Excluded:

* New feature development (handled by other backlog items).
* Major algorithmic rewrites – formulas remain bit-for-bit identical.

## 3. Guiding Principles

1. Pure refactor – zero functional drift; golden tests must stay green.
2. Ensembles over fragments – a package per bounded context, not one file per function.
3. "Leave campground cleaner" – deduplicate on contact; never copy-paste.
4. Incremental PRs (< 400 LOC each) to ease review and git blame.

## 4. Target Folder Map

```text
# pre-refactor (simplified)
 tco_app/
 ├── app.py                         # 1 445 LOC Streamlit + orchestration + maths
 ├── src/
 │   ├── calculations.py           # 1 455 LOC domain logic
 │   ├── visualization.py          # 853 LOC figure assembly
 │   └── ui_components.py          # widgets (used by app.py)
 ...

# post-refactor (proposed)
 tco_app/
 ├── main.py                        # ≤50 LOC – entry point only
 ├── ui/
 │   ├── pages/
 │   │   ├── home.py               # Streamlit pages (formerly chunks of app.py)
 │   │   ├── cost_breakdown.py
 │   │   └── sensitivity.py
 │   └── components.py             # widgets (moved from src/ui_components.py)
 │
 ├── domain/
 │   ├── energy.py                 # kWh↔MJ, efficiency, charging mix
 │   ├── finance.py                # NPV, financing, carbon price, incentives
 │   ├── battery.py                # degradation, replacement, residual
 │   ├── externalities.py          # emissions, carbon price multipliers
 │   ├── sensitivity.py            # what-if runners
 │   └── __init__.py
 │
 ├── plotters/
 │   ├── cost_breakdown.py         # Figure factories (was visualization.py)
 │   ├── tornado.py
 │   └── __init__.py
 │
 ├── services/
 │   ├── scenario_service.py       # orchestration glue
 │   └── incentive_service.py      # (extracted earlier)
 └── ...
```

## 5. Implementation Plan

### 5.1 Automated Safety Net

1. Create golden-output fixture for 10 representative vehicles:
	* `pytest -q tests/regression/test_golden.py` must pass before & after.
2. Turn on `coverage –fail-under=80` in CI.
3. Add temporary pre-commit hook that blocks commits touching `calculations.py` unless tests pass.

### 5.2 Step 1.1 — UI Extraction

| Order | Action | Risk Mitigation |
| --- | --- | --- |
| 1 | Scaffold `main.py` with only `st.set_page_config()` + router. | No business logic moved yet. |
| 2 | Copy visual sections of `app.py` into individual files under `ui/pages/`. Use Streamlit's multi-page feature. | Keep imports pointing back to old functions until step 1.2 completes. |
| 3 | Move `ui_components` → `ui/components.py`, update import paths. | Search-replace with `rope` to avoid typos. |
| 4 | Delete redundant sections from `app.py`; leave thin orchestration shim that calls new pages (to keep legacy single-file entry working until decommission). | CI ensures nothing breaks. |
| 5 | After all pages validated, flip Streamlit entry point from `app.py` to `main.py`; deprecate `app.py` with warning banner. | Provide migration note in README. |

### 5.3 Step 1.2 — Domain Decomposition

1. Establish `tco_app/domain/` package with empty `__init__.py`.
2. For each logical area (energy, finance, battery, externalities, sensitivity):
	1. `git mv` the corresponding code slice from `calculations.py` into new module **without changing lines**.
	2. Replace original with `from tco_app.domain.energy import ...` re-export stub to preserve import contract.
	3. Run tests; ensure identical results.
3. Extract shared helpers into `tco_app/utils/` **only when duplication >1**; otherwise keep local.
4. After all slices moved, delete empty stubs in `calculations.py`, leaving a façade that only re-exports domain functions (temporary; marked `# Deprecated – will be removed in release v2.0`).
5. Update callers (`ui/*`, `services/*`, tests) to import from domain modules instead of façade.
6. Remove façade after downstream merges land.

### 5.4 Step 1.3 — Plotter Relocation

1. Create `tco_app/plotters/` and move each figure-builder out of `visualization.py` verbatim.
2. Keep public signature identical; export via `plotters.__init__` for DX.
3. Update `ui/pages/*.py` to call `plotters.cost_breakdown.build(fig_data)` style helpers.
4. Delete obsolete `visualization.py` after migration.

## 6. Duplication / Redundancy Control

* Use the **Strangler Fig Pattern** – old functions wrap new ones until parity proven.
* Run `ruff –select PLR0915` after each PR; fail build if duplicate-code detected.
* Disallow "copy-then-tweak" in reviews; encourage `git mv` so history tracks origin.

## 7. Roll-out Strategy

1. Merge Feature Flags (`ENABLE_NEW_UI`, `ENABLE_DOMAIN_V1`) defaulting to *False*.
2. Dog-food internally for one release cycle.
3. Flip flags to *True* once metrics stable (<0.5 % diff on key KPIs).
4. Remove flags & dead code in subsequent sprint.

## 8. Acceptance Criteria (Definition of Done)

* No file >300 LOC (validate with `radon raw`).
* All golden regression tests pass.
* `ruff`, `black`, `mypy --strict` clean.
* Streamlit hot reload <300 ms on slider change (baseline 1 200 ms).
* 90 %+ of domain functions covered by tests (was 55 %).
* `grep -R "def calculate_npv"` returns single implementation.

## 9. Timeline & Effort

| Week | Milestone | Owner |
| --- | --- | --- |
| 1 | Safety net + scaffolding | EM |
| 2–3 | UI extraction & smoke tests | EM + AB |
| 4–5 | Domain split (energy, battery, finance) | AB |
| 6 | Plotter move & UI hookup | CD |
| 7 | Clean-up, facade removal, docs | EM |

*Total* ≈ **10 dev-days** spread across three team-members.

## 10. Open Questions

1. Keep `app.py` as legacy entry for backward compatibility or remove entirely in v1.1?
2. Naming: `plotters` vs `figures` – pick one and document.
3. Do we expose public API for 3rd-party notebooks now or post-refactor?

---

*Authored*: 2025-05-22  *Owner*: Edward Miller 