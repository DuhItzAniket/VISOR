# VISOR improvement plan and task ledger

Created 2026-10-19 from audit of `40e68de`. Research: [RESEARCH_REVIEW.md](RESEARCH_REVIEW.md).

## Objective and order

Make registration outcomes trustworthy, comparisons reproducible, and desktop workflows maintainable. Complete correctness and measurement work before adding engines or training models.

| ID | Priority | Task and expected files | Acceptance / verification | State |
|---|---|---|---|---|
| I01 | P0 | Fix package backend (`pyproject.toml`) | Wheel builds without changing the current environment; version/assets are present | Planned |
| I02 | P0 | Share geometry validation, remove invented fallback (`geometry.py`, `geometry_robust.py`, new validation module, tests) | Failed/degenerate fits stay failures; mask counts/residuals agree; all estimators reject horizon crossing and outside-target polygons; positive classical regressions remain | Planned |
| I03 | P1 | Clarify batch residual vs truth error (`batch.py`, export/UI, tests) | No ground truth => localization error unavailable; residual reported with its own name; output contract migration documented | Planned |
| I04 | P1 | Typed pair matching and honest timing (`models.py`, learned engines, pipeline, details, exports) | Separate measured stages; actual matcher/device/confidence; no fabricated zero distances or split joint timers; mock unit tests plus optional real-model CPU/CUDA checks | Planned |
| I05 | P1 | Repair and pin XFeat integration (adapter, status, installer, dependency docs) | Pinned documented API; mutual matching; missing weights/dependencies actionable; real pair smoke run required before claiming supported | Planned |
| I06 | P1 | Record estimator provenance and effective threshold (settings/results, geometry, exports/UI) | Every result describes selected and executed method; adaptive policy explicit; learned/classical paths honor same geometry choice | Planned |
| I07 | P1 | Reproducible evaluation runner (scripts, benchmark/batch, manifests, docs) | Relative paths, input hashes, versions/config/device, warmup/repetitions, failure rows; known-H error and residual separate; portable CLI | Planned |
| I08 | P1 | Held-out evaluation dataset and metrics (evaluation module/tests/docs) | Synthetic negatives/outliers plus HPatches loader; absent data skipped explicitly; failure denominators and localization conventions documented; publish raw results before conclusions | Planned |
| I09 | P2 | Runtime capability registry (registry/pipeline/status/UI) | One source for extractor/matcher config, dependency/weights/device readiness; unavailable engine never silently routes to ORB | Planned |
| I10 | P2 | Job lifecycle and responsive desktop (new UI jobs/controller, main window) | Input/config changes invalidate old jobs; cancellation/shutdown responsive; install worker lifecycle covered; incremental refactor under UI regressions | Planned |
| I11 | P2 | Explainable quality diagnostics (geometry diagnostics/details/export) | Coverage/residual distribution/transform plausibility shown without uncalibrated confidence claims; click-through inlier inspection | Planned |
| I12 | P2 | Release and CI discipline (workflows/build docs/scripts) | Offline core lane, separate optional learned lane, wheel/install smoke, packaged full workflow verification, dependency/model licenses inventoried | Planned |

## Execution batches

1. **Trust baseline:** I01–I03. Build and focused geometry/batch regressions; run the available suite. Commit verified changes with source evidence. Historical positive goldens must not be rewritten just to hide failures.
2. **Honest engine contracts:** I04–I06. Preserve the classical path; move learned metrics to a structured pair result. Fix installed/importable/weights-ready distinctions. Record warm and cold timing separately.
3. **Evaluation:** I07–I08. Evaluate existing engines with consistent budgets and truth-backed accuracy. Keep tuning and reporting sets separate. Investigate negative-pair false positives before setting a detection-quality policy.
4. **Product and release:** I09–I12. Incremental registry/job refactor, richer diagnostics, package verification. Only consider new engines after prior gates are satisfied.

Each task updates this ledger, `IMPLEMENTATION_STATUS.md`, and `IMPLEMENTATION_LOG.md`, records checks and limitations, and gets a focused commit. A task can be implemented while some platform validation is pending; it must not be labeled fully verified without evidence.

## Documentation ownership

- `README.md`: installation, features and links to current status; avoid machine-specific or universal availability claims.
- `PROJECT_PLAN.md`: original product mission and milestones, with this plan as current improvement sequence.
- `RESEARCH_REVIEW.md`: dated evidence and primary-source rationale; append/review when upstream integration changes.
- `IMPROVEMENT_PLAN.md`: task ledger and acceptance gates.
- `IMPLEMENTATION_STATUS.md`: latest verified facts and outstanding limitations; canonical current status.
- `IMPLEMENTATION_LOG.md`: append-only implementation/check history.
- `DECISIONS.md` and `ARCHITECTURE.md`: accepted design changes when implementation lands.
- `HANDOFF.md` and `LAST_DOCUMENTATION.md`: historical references; direct readers to canonical current status.

## Success measures

- A failed solver cannot produce an all-inlier zero-error success.
- Every displayed stage time was measured for that stage or is explicitly unavailable.
- Every experiment can be rerun from its recorded inputs, configuration and runtime versions.
- Ground-truth accuracy is never inferred from training/fit residual alone.
- The normal install/build path works from package metadata, and optional engines cannot break core use.
