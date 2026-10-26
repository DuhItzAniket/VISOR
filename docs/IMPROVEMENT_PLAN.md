# VISOR improvement plan and task ledger

Created 2026-10-19 from audit of `40e68de`. Research: [RESEARCH_REVIEW.md](RESEARCH_REVIEW.md).

## Objective and order

Make registration outcomes trustworthy, comparisons reproducible, and desktop workflows maintainable. Complete correctness and measurement work before adding engines or training models.

User requirement added 2026-10-19: distribute standalone desktop applications for Windows, macOS, and Linux. End users must not need Python, pip, a virtual environment, or a terminal. Keep Qt as the desktop foundation, bundle the runtime, and validate builds on their target OS/architecture. Current source language remains Python; a native-language rewrite is not required for this delivery approach and has not been performed.

User requirement added 2026-10-20: professional product quality. Apply [PRODUCT_QUALITY_STANDARD.md](PRODUCT_QUALITY_STANDARD.md) throughout the work, including visual hierarchy, keyboard access, error recovery and evidence-backed results. This is an acceptance standard for every batch.

| ID | Priority | Task and expected files | Acceptance / verification | State |
|---|---|---|---|---|
| I01 | P0 | Fix package backend (`pyproject.toml`) | Wheel builds without changing the current environment; version/assets are present | Implemented; wheel verified locally |
| I02 | P0 | Share geometry validation, remove invented fallback (`geometry.py`, `geometry_robust.py`, new validation module, tests) | Failed/degenerate fits stay failures; mask counts/residuals agree; all estimators reject horizon crossing and outside-target polygons; positive classical regressions remain | Implemented; 34 focused tests passed, including frozen classical positives |
| I03 | P1 | Clarify batch residual vs truth error (`batch.py`, export/UI, tests) | No ground truth => localization error unavailable; residual reported with its own name; output contract migration documented | Implemented; batch regressions passed |
| I04 | P1 | Typed pair matching and honest timing (`models.py`, learned engines, pipeline, details, exports) | Separate measured stages; actual matcher/device/confidence; no fabricated zero distances or split joint timers; mock unit tests plus optional real-model CPU/CUDA checks | Implemented: typed pair result, synchronized stage timing, assignment scores, nullable unavailable fields and schema-2 reporting; offline contracts and installed-model suite passed. Dedicated device profiling remains part of evaluation |
| I05 | P1 | Repair and pin XFeat integration (adapter, status, installer, dependency docs) | Pinned documented API; mutual matching; missing weights/dependencies actionable; real pair smoke run required before claiming supported | Implemented and checked on local CPU: fixed source/weight pin and integrity manifest, detectAndCompute API, explicit setup/offline inference, mutual L2 matching; identity and known-warp checks passed. CUDA and packaged learned support remain unverified |
| I06 | P1 | Record estimator provenance and effective threshold (settings/results, geometry, exports/UI) | Every result describes selected and executed method; adaptive policy explicit; learned/classical paths honor same geometry choice | Implemented: requested/executed methods, effective and attempted thresholds, explicit adaptive policy and LMEDS semantics; learned pipeline honors all three estimators; classical goldens retained |
| I07 | P1 | Reproducible evaluation runner (scripts, benchmark/batch, manifests, docs) | Relative paths, input hashes, versions/config/device, warmup/repetitions, failure rows; known-H error and residual separate; portable CLI | Implemented: developer CLI, manifest snapshot/hashes, versions/revision/dirty state, effective settings and device, separate warmup rows, failure denominators, corner mean/RMSE/max and negative false acceptance; 11 focused tests passed |
| I08 | P1 | Held-out evaluation dataset and metrics (evaluation module/tests/docs) | Synthetic negatives/outliers plus HPatches loader; absent data skipped explicitly; failure denominators and localization conventions documented; publish raw results before conclusions | Initial evidence delivered: adversarial/synthetic cases, full-sequence loader and frozen two-scene HPatches sample with raw 18 development/72 reporting attempts published. Broader user-relevant scenes, additional independent negatives and reliability tradeoffs remain under I15 |
| I09 | P2 | Runtime capability registry (registry/pipeline/status/UI) | One source for extractor/matcher config, dependency/weights/device readiness; unavailable engine never silently routes to ORB | Implemented: all nine built-in factories, typed config/pair protocols, shared capability/config metadata and selector/status discovery; dependency presence vs verified runtime is explicit. Available AKAZE/BRISK resolve their actual factories; absent/frozen learned choices remain disabled |
| I10 | P2 | Job lifecycle and responsive desktop (new UI jobs/controller, main window) | Input/config changes invalidate old jobs; cancellation/shutdown responsive; install worker lifecycle covered; incremental refactor under UI regressions | Implemented for worker delivery/lifetime: revision tickets, main-thread signal relays, single terminal event, stale result/error rejection, cooperative cancellation and deferred nonblocking close. Controlled-worker and install-lifetime regressions passed; native interactive review remains |
| I11 | P2 | Explainable quality diagnostics (geometry diagnostics/details/export) | Coverage/residual distribution/transform plausibility shown without uncalibrated confidence claims; click-through inlier inspection | Implemented: support hull/image fractions, median/p95/max inlier residuals, projected area/target ratio in UI/exports and solver membership on keypoint inspection. No confidence score or accuracy inferred; 20 focused diagnostic/geometry/golden checks passed |
| I12 | P2 | Release and CI discipline (workflows/build docs/scripts) | Offline core lane, separate optional learned lane, wheel/install smoke, packaged full workflow verification, dependency/model licenses inventoried | Notice collection, pinned 203-file Qt corpus and frozen filesystem inventories verified in all four targets at a6fc4fd/40227340916; hashes and smoke reports independently inspected. Full local 227 passed/5 skipped; focused 25 passed/3 host-symlink skips, Ruff/focused Mypy passed. Native/transitive/source-offer review remains; I16 addresses unnecessary OpenCV GUI dependencies |
| I13 | P1 | Standalone desktop distribution (platform builder, installer scripts, CI matrix, deployment guide) | Windows setup executable; macOS app/DMG; Linux executable/package; bundled runtime and launcher; artifact workflow smoke check; platform support limited to verified runners/architectures | Four native targets passed at a6fc4fd (40227340916): Windows x64, macOS ARM64/Intel and Linux x64; version 0.2.0, project/dependency notices and five image formats checked. Signing, complete transitive/source-offer review, packaged learned support and clean-desktop install gates remain |
| I14 | P1 | Professional desktop workflow and accessibility (UI widgets, product quality standard) | Canvas-first layout, compact engine choices, discoverable history/diagnostics, consistent focus/disabled states; native keyboard, scaling, screen-reader and success/failure review on each target | Windows picker/keyboard/analysis/render/export/close, no-fit, invalidation, session replay, paired width editing and platform Pictures/Documents defaults reviewed. Latest full local 227 passed/5 skipped and four-target bundle checks passed; this batch changes packaging, not visual/native interaction review. Physical drop, full screen-reader/scaling, native macOS/Linux and clean-install gates remain |
| I15 | P1 | Conservative registration reliability policy using separate development/reporting scenes | Investigate wrong but valid low-support fits; compare matching/support/plausibility measures on development scenes, freeze the policy, then report raw accuracy/rejection/negative tradeoffs on additional held-out scenes without tuning to them | Initial preregistered study complete: 192 development/72 reporting attempts and frozen choices published. Reporting adds no gate benefit; SIFT's 343-inlier fit still has 9.88 px error. Gates not promoted; defaults/goldens unchanged. Six annotation-error rows retained. Broader scenes and stability/overlap investigation remain before production reliability claims |
| I16 | P1 | Minimize and trace the OpenCV native dependency profile | Isolated headless-contrib profile at the same OpenCV version; one cv2 provider per environment; classical goldens, image/video workflows and four-target frozen checks; inspect native inventories before replacing downloads | Implemented headless profile/overlap and compiled-GUI guards, native Qt5 exclusion, actual provider provenance, frozen MJPEG check and separate no-deps LightGlue setup. Isolated core 226 passed/5 skipped/17 deselected; full developer suite 243 passed/5 skipped; 28 focused tests, Ruff/focused Mypy passed. Native/optional refresh and actual inventories pending; no native licensing conclusion |

## Execution batches

1. **Trust baseline:** I01–I03. Build and focused geometry/batch regressions; run the available suite. Commit verified changes with source evidence. Historical positive goldens must not be rewritten just to hide failures.
2. **Honest engine contracts:** I04–I06. Preserve the classical path; move learned metrics to a structured pair result. Fix installed/importable/weights-ready distinctions. Record warm and cold timing separately.
3. **Evaluation:** I07–I08. Evaluate existing engines with consistent budgets and truth-backed accuracy. Keep tuning and reporting sets separate. Investigate negative-pair false positives before setting a detection-quality policy.
4. **Product and release:** I09–I12. Incremental registry/job refactor, richer diagnostics, package verification. Only consider new engines after prior gates are satisfied.

I13 is promoted into the current implementation batch in response to the desktop-distribution requirement. Build a shared host-platform builder and a manually triggered native runner matrix. Signing/notarization and target-system validation remain explicit release gates, not implied by configuration files.

Each task updates this ledger, `IMPLEMENTATION_STATUS.md`, and `IMPLEMENTATION_LOG.md`, records checks and limitations, and gets a focused commit. A task can be implemented while some platform validation is pending; it must not be labeled fully verified without evidence.

## Documentation ownership

- `README.md`: installation, features and links to current status; avoid machine-specific or universal availability claims.
- `PROJECT_PLAN.md`: original product mission and milestones, with this plan as current improvement sequence.
- `RESEARCH_REVIEW.md`: dated evidence and primary-source rationale; append/review when upstream integration changes.
- `IMPROVEMENT_PLAN.md`: task ledger and acceptance gates.
- `PRODUCT_QUALITY_STANDARD.md`: product/design requirements, interface audit and native release review gates.
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
