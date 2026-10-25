# Implementation Status

## Native file-dialog defaults — 2026-10-25

- Review-driven source fix starts image/project/export/video dialogs in Qt's platform Pictures/Documents/Movies locations, shares the last image directory, remembers successful project/export choices and reuses the current project filename. Cancelled/failed exports do not overwrite successful destination preferences. README now leads with the standalone desktop workflow and separates source-developer instructions.
- Eighteen focused dialog/input/project/overlay checks passed. Full local suite: **201 passed, 2 skipped in 32.28s**; Ruff, focused image-widget Mypy and whitespace checks passed. Native rebuild/picker review follows; current download links still identify verified 7bf73d6 application code.

## I15 independent reporting result — 2026-10-25

- Completed the preregistered [initial reliability experiment](evaluation/RELIABILITY_FINDINGS.md): 192 development and 72 reporting attempts, with choices published before reporting. Reserved-source f85c7e0 recorded a clean tree; evaluator/analysis algorithms match development dec9b33.
- The frozen gates retain all baseline ≤3 px positives but reject no additional reporting fits. SIFT's v_artisans/1-4 remains accepted at 9.88 px mean corner error with 343 inliers and 0.359 reference coverage. **Neither gate is promoted into desktop defaults**; no retuning on the reporting scenes.
- Reporting has no runtime failures. One truth transform crosses the full reference rectangle's horizon (v_artisans/1-5); six repeated rows are retained as annotation errors and excluded from corner-accuracy denominators. Each engine has 27 evaluable positive and six negative attempts, from nine/two distinct pairs. No pair was replaced after inspection.
- Published raw reports, hashes, the full development grid and per-attempt reporting decisions; consistency regressions recompute these results. Broader user-relevant data and stability/overlap investigation remain necessary before general reliability claims.

## I15 development measurements and frozen choices — 2026-10-25

- Published [independent development evidence](evaluation/RELIABILITY_FINDINGS.md): 192 measured attempts on 20 truth-backed pairs and 12 distinct negatives from four scenes, with three repetitions and two engines. Evaluator dec9b33 recorded a clean source tree; no runtime/annotation errors.
- The preregistered rule selects SIFT minimum 20 inliers and ORB minimum 40, each requiring reference hull fraction ≥0.01 and no additional residual cap. In development, both preserve all baseline positives within 3 px and reject the observed >5 px accepted fits; SIFT also rejects one distinct negative pair accepted by baseline. ORB loses one distinct positive pair that had been within 5 px.
- Published every candidate and the exact selection before inspecting the reserved i_books/v_artisans performance. This is development evidence under selection bias, not a default desktop behavior change or production accuracy claim. Reserved reporting follows without retuning.

## Current desktop builds and offline study tool — 2026-10-25

- Copy-only-drop desktop [run 40219803747](https://github.com/DuhItzAniket/VISOR/actions/runs/40219803747) passed all four native targets at **7bf73d6**. Windows: **165 passed/2 skipped/17 deselected**; macOS ARM64/Intel and Linux: **163 passed/4 skipped/17 deselected**. Lint, packaging and every bundled workflow step passed, including Qt URL-drop copy semantics. [Download links](DESKTOP_DISTRIBUTION.md) identify this revision. Local Windows rebuild and the expanded bundled check passed too.
- Added a separate offline `visor.reliability_study` tool for the preregistered diagnostic grid. It refuses reporting data during selection, freezes per-engine choices, keeps failure denominators and checks reporting input/setting separation. It does not change desktop fitting or acceptance defaults.
- Twenty-two focused evaluation/study checks passed; full local suite **193 passed, 2 skipped in 32.02s**. Ruff and study-module Mypy passed. Development images were downloaded with bounded ranges (~29.6 MB); their first images show distinct scenes (mountain station, city, Creation of Adam reproduction, apprentice illustration), supporting all twelve planned directed negatives. New performance measurement follows from a clean committed evaluator.

## Reliability study preregistration — 2026-10-25

- I15 now has a [frozen scene-selection and analysis protocol](RELIABILITY_STUDY.md): four disjoint development scenes, two reserved reporting scenes, fixed classical execution settings, a defined diagnostic-gate grid and selection/retention criteria. Selection used archive metadata only; no new scene performance has been inspected. Original reporting scenes remain excluded from policy development.
- No acceptance threshold or estimator behavior changes in the application. Download preparation, negative-pair inspection, development measurements and frozen-policy reporting follow the recorded protocol.

## Drag-and-drop contract follow-up — 2026-10-25

- Overlay-fix desktop [run 40219098560](https://github.com/DuhItzAniket/VISOR/actions/runs/40219098560) passed all four targets at d2370af: Windows 158 passed/2 skipped/17 deselected, macOS ARM64/Intel and Linux each 156 passed/4 skipped/17 deselected. Lint, packaging and bundled workflows passed. These are the current downloadable validation artifacts; the subsequent copy-only drop fix has the source evidence below.
- Real Explorer dragging remains pending: the Windows helper rejects cross-window drag endpoints. The attempted operation did not complete and is not counted as native validation. See [review limits](WINDOWS_REVIEW.md).
- Source input handlers now explicitly accept Copy, including when Shift proposes Move, and reject move-only sources. URL drop tests cover both image roles, Unicode/spaced uppercase filenames, unchanged source bytes, rejected remote/non-image data and unreadable-file recovery. The bundled workflow check now includes Qt URL drop events, explicitly separate from shell integration.
- Fourteen focused drop/overlay/session checks passed, including 12 px project replay. Full local suite: **182 passed, 2 skipped in 33.26s**. Ruff, focused image-widget Mypy and the source bundled-workflow check passed. A broad follow-import type traversal through the smoke entry point was stopped without a result; no whole-UI type-check pass is claimed. Fresh packaging follows this source commit.

## Four native targets and resumed Windows review — 2026-10-25

- Desktop [run 40217772265](https://github.com/DuhItzAniket/VISOR/actions/runs/40217772265) passed Windows x64, macOS ARM64 and Linux x64 at c67936c. Separate [Intel Mac run 40217899781](https://github.com/DuhItzAniket/VISOR/actions/runs/40217899781) passed at 33ab883; that commit only extends the workflow and documentation, with identical application code. All targets passed lint, packaging and bundled workflow checks.
- Windows core suite: **155 passed, 2 skipped, 17 optional tests deselected**. Each macOS/Linux target: **153 passed, 4 skipped, 17 deselected**. Separate CPU [model run 40217775833](https://github.com/DuhItzAniket/VISOR/actions/runs/40217775833) passed **17 tests, 157 deselected** at c67936c. GPU execution and packaged learned models remain unverified.
- Resumed actual Windows review confirmed automatic Localization display, explicit fit status, estimator-change invalidation and native project replay in a fresh process. Symmetric ratio/MAGSAC, both input paths, rainbow colors and 3 px overlays restored correctly; the replayed run returned 348 matches/339 inliers. See [Windows review](WINDOWS_REVIEW.md).
- Review found mismatched overlay editors. Follow-up source synchronizes both width sliders before rendering, shares their 1–12 px range, and synchronizes the rainbow menu/button in both directions. Fourteen focused UI/session/job checks passed; full local suite **175 passed, 2 skipped in 35.77s** and Ruff passed. Local Windows rebuild succeeded; native review confirmed both editing directions (12 px then 2 px) and the blank-target no-fit workflow. The artifact links above identify the preceding verified application revision.
- Remaining release gates include clean-desktop installation/uninstallation, full screen-reader/scaling and macOS/Linux interaction, complete artifact notices, owner-selected project license, signing/notarization, packaged learned support, and the I15 reliability investigation. Four successful builds do not close those gates.

## Intel Mac validation extension — 2026-10-25

- Added a separate macOS Intel runner target alongside Apple Silicon. The manual desktop workflow can run all four targets or Intel alone. Intel is pending until its native job actually passes; no universal binary is claimed.
- Final replay/video desktop and optional CPU model runs are in progress at c67936c. Adding the Intel job changes the workflow only; application code is unchanged by this extension.

## Video resource handling follow-up — 2026-10-25

- File-based tracking decodes frames lazily into the per-frame tracker instead of retaining the entire decoded clip. Capture release is guaranteed on normal completion and tracking/cancellation failure. Total time includes reference/video decoding.
- Video APIs explicitly support SIFT/ORB and reject other engine names before work; they cannot silently label ORB as another engine. Result UI says valid planar fits rather than measured localization accuracy.
- Twenty focused video/job regressions passed; video focused Mypy and Ruff passed. The broader/core suite and final native refresh follow this commit.

## Current source verification — 2026-10-25

- Full local suite after project format 2 and native-review fixes: **169 passed, 2 skipped in 32.63s**. Ruff and focused exporting/matcher Mypy passed. The subsequent test fixture isolates Qt window preferences so regression runs do not overwrite the developer's real layout.
- Native artifacts below remain the verified fe5ec16 desktop baseline until the final replay/UI refresh completes. Published evaluation measurements remain unchanged and identify their clean b2c7f0b evaluator source.

## Windows interaction and session replay follow-up — 2026-10-25

- Actual local Windows executable review covered native pickers/shortcuts, SIFT/ORB completion, match rendering, PNG export, engine-change invalidation and clean Ctrl+Q close. UI Automation exposed the intended control names. See WINDOWS_REVIEW.md; this is not complete screen-reader/scaling/install validation.
- Follow-up source changes automatically reveal the first image result, distinguish accepted/no-fit states, widen engine choices, wrap/plain-text details and clear primary results before repeated analysis.
- Project format 2 now restores matching/estimator/overlay choices and uses relative image references when possible; version 1 remains readable. Unavailable project engines cannot silently substitute a classical engine.
- Corrected symmetric matching's nested timing double count, made cross-check threshold unavailable rather than zero and rejected ambiguous strategy flags. Focused replay/UI/matching regression set passed; final complete/native refresh follows.
- Pre-follow-up full local suite including published raw evidence: 161 passed, 2 skipped in 51.41s. The published data reports remain tied to unchanged evaluator b2c7f0b.

## Latest native validation and published evaluation — 2026-10-25

- Native desktop [run 40213846401](https://github.com/DuhItzAniket/VISOR/actions/runs/40213846401) passed all three targets at fe5ec16: Windows x64 131 passed/2 skipped/17 model tests deselected; macOS ARM64 and Linux x64 each 129 passed/4 skipped/17 deselected. Lint, native packaging and bundled workflow checks passed on each runner. This includes the new workspace, job guards, registry, result contract and diagnostics. Artifacts are unsigned validation builds; see DESKTOP_DISTRIBUTION.md.
- Developer evaluator b2c7f0b has 11 additional focused regressions. Latest local core suite: 142 passed, 2 skipped, 17 deselected in 12.66s. The prior full installed-model suite at ac28f47 passed 144 tests/2 skips; source developer evaluation modules were added after the native artifact revision.
- Published [raw evaluation evidence](evaluation/README.md): 18 synthetic development attempts and 72 attempts on a small full-image HPatches reporting sample, with clean source revision, settings, hashes, effective results and all failures. Reporting sample: ten positive pairs/two distinct cross-scene negatives, three repetitions, CPU budget 1500; no runtime/annotation errors.
- On that sample, mean corner error ≤3 px occurred in 9/30 positive SIFT attempts and 12/30 ORB attempts; valid-fit counts were 21/30 and 30/30. Each engine rejected all six repeated negative attempts. This small sample does not establish general false-positive rates or an engine ranking. Wrong but valid fits motivate I15, using separate development scenes rather than tuning to the reporting sample.
- Added a source/package notice [inventory](THIRD_PARTY_INVENTORY.md). Complete per-artifact notices, project license choice, model redistribution review, signing/notarization and native manual/accessibility/scaling review remain open release gates.

## Reproducible evaluation runner — 2026-10-25

- I07 implemented as `python -m visor.evaluate`: portable manifests, hashed input/truth files, actual matrices/settings/runtime versions, source revision/dirty state and raw warmup/repetition/failure rows. Accuracy against truth, fit residual and negative false acceptance have separate definitions.
- I08 now has synthetic development positives/unrelated/blank negatives and a full-image HPatches loader that records missing pairs, enforces split separation and reports condition-specific summaries. No actual HPatches sequence directory was present at implementation time; do not treat scaffolding as evaluated data.
- Eleven focused evaluation tests passed; targeted evaluator/data Mypy passed. The first development run produced 18 measured attempts with no runtime errors; public raw evidence should identify a committed evaluator revision before conclusions. See EVALUATION.md.

## Fit diagnostics and current source checks — 2026-10-25

- I11 adds measured spatial-support hull fractions, inlier residual median/p95/maximum and projected area ratios to valid fits, UI details and exports. Keypoint inspection identifies accepted correspondences and solver membership with actual descriptor distances or assignment scores.
- These diagnostics are explicitly not calibrated confidence or ground-truth accuracy. Missing size/invalid fit does not create fabricated values. See RESULT_CONTRACT.md for definitions.
- Source baseline ac28f47 passed the full local suite: 144 passed, 2 skipped in 66.04s, plus Ruff and focused registry/pipeline Mypy. Diagnostic follow-up: 20 focused tests passed and validator Mypy/Ruff passed.
- Added explicit packaging discovery for factory-loaded classical/learned wrapper modules. Fresh three-platform builds will verify the current desktop code; existing artifact links remain tied to their recorded revisions.

## Shared engine capabilities — 2026-10-25

- I09 now routes pipeline construction through one registry for all nine built-in engines. Capability records drive the selector/status dialog, list configuration fields and distinguish dependency presence from weight/device validation at use.
- Fixed available AKAZE/BRISK choices being rejected by the main pipeline; both now execute their own factories and descriptor norms. Missing engines never silently use ORB. Learned dependency probing does not import Torch or fetch weights.
- Focused registry/reporting/classical checks: 27 passed, then 25 follow-up capability/reporting/UI checks passed. Focused Mypy on registry/pipeline passed. Fresh broader/native verification follows; prior native artifact links still identify the older code baseline.

## Job ownership and asynchronous shutdown — 2026-10-25

- I10 worker lifecycle implemented: input/algorithm changes cancel and invalidate the active revision; late results and errors are discarded. Main-thread relays deliver at most one terminal event and clean up finished worker objects.
- Close requests leave the event loop responsive and defer destruction until workers finish. Analysis cancellation is cooperative at stage boundaries; calibration now checks between images and around calibration. Source dependency installation owns its worker lifetime; close waits for installation to finish without blocking the UI or killing pip halfway through setup.
- Controlled Qt regressions cover current/stale delivery, image/config changes, cancellation, deferred close and install lifetime. Focused job/UI/calibration checks passed; broader source and native verification follows.
- Independent optional CPU workflow [40212401735](https://github.com/DuhItzAniket/VISOR/actions/runs/40212401735) passed all 17 model-marked tests at source 7214553, including real XFeat/LightGlue inference. This does not verify GPU execution or packaged learned support.

## XFeat source runtime repair — 2026-10-25

- I05 implemented against fixed upstream revision e92685f57f8318b18725c5c8c0bd28c7fe188d9a, using detectAndCompute and its 64-D descriptors. Setup explicitly caches source/weights and hashes; inference validates the cache and performs no network access. CPU preference is honored during initialization.
- Replaced invalid xfeat.Extractor / pip-package instructions in the adapter, source installer and status dialog. LightGlue setup is also pinned; source startup probes dependencies without eagerly importing Torch.
- Local CPU fixture: 512 self-matches; controlled warp 348 mutual matches, 328 inliers, maximum corner error 2.29 px. This is one fixture, not evidence of general accuracy. Full local suite: 128 passed, 2 skipped in 54.20s. Focused runtime tests and Ruff passed; new runtime/setup modules passed focused Mypy.
- Optional model tests are marked separately and have a manual CPU workflow. Core desktop jobs exclude them. Workflow execution and native rebuilds follow; packaged learned engines, CUDA verification and complete notice inventory remain pending.
- Setup and limitations: [OPTIONAL_ENGINES.md](OPTIONAL_ENGINES.md).

## Engine reporting and estimator provenance — 2026-10-25

- I04/I06 implemented in source: typed learned pair results, independently measured completed extraction/matching stages, separate initialization/preprocessing/rendering, actual device and assignment scores; no fabricated learned descriptor distances or candidate counts.
- Learned and classical paths honor the selected robust estimator. Every attempted geometry fit records method and threshold provenance; the existing adaptive RANSAC sequence is preserved and explicitly labeled.
- JSON analysis schema 2 and expanded CSV/HTML/UI details describe these semantics. See [RESULT_CONTRACT.md](RESULT_CONTRACT.md). Optional model keypoint fields absent from extractor output are displayed as unavailable.
- Verification: 52 focused tests passed; full local suite 120 passed, 2 skipped in 52.34s, including installed optional model tests. Ruff passed; focused Mypy passed for models and the measured pair adapter. Dedicated device profiling and fresh native bundles remain pending.
- XFeat's upstream API repair is next (I05); its old import path is not claimed operational. The source matching contract now correctly identifies its mutual L2 matcher.

## Product quality follow-up — 2026-10-20

- Established [PRODUCT_QUALITY_STANDARD.md](PRODUCT_QUALITY_STANDARD.md) and I14 as an ongoing acceptance requirement.
- Refined the source desktop workspace: stacked, scrollable inputs; larger result area; compact engine selection; separate Diagnostics dock; visible recent-pair disclosure; consistent control/focus styles and role-specific accessible names.
- Diagnostics opens for logged errors and source dependency installation. Parameter forms scroll and classical forms are hidden for other engines. Overview filenames are escaped as text.
- Local offscreen renders reviewed at 1280×820 and 1040×680, plus loaded inputs/history and parameters at 1280×820. Ruff and diff whitespace checks passed. No automated tests or new native bundles were run for this UI follow-up; the verified package baseline below predates it.
- Native monitor scaling, keyboard/screen-reader review, complete success/failure/busy workflows and clean-desktop installation remain open release gates. I04–I14 remain tracked; this is not a completed production release.

## Current verified baseline — 2026-10-19

Source commit: `ba7e05d`. [Native verification run 39301662952](https://github.com/DuhItzAniket/VISOR/actions/runs/39301662952) completed successfully on all targets.

| Target | Core suite | Lint | Native packages | Bundled workflow check |
|---|---|---|---|---|
| Windows x64 (Windows Server 2022 runner) | 91 passed, 17 skipped | Passed | Setup EXE + portable ZIP | Passed |
| macOS ARM64 (macOS 14 runner) | 89 passed, 19 skipped | Passed | App bundle + DMG | Passed |
| Linux x64 (Ubuntu 22.04 runner) | 89 passed, 19 skipped | Passed | Debian package + portable tar | Passed |

The core environment excludes optional model dependencies. Skips include optional engine tests; macOS/Linux also skip the exact Windows/OpenCV snapshot checks. Every target runs independent known-transform accuracy checks. Bundled checks load image inputs in Qt, run SIFT/ORB localization, render results, export JSON/CSV, save/load a project and close the window.

End users launch a standalone application without a separate Python installation. The implementation retains Python/Qt internally. These artifacts are unsigned validation builds, not a signed public release or proof of interactive install/uninstall on all desktops.

## Improvement work delivered

- I01: corrected package backend; wheel construction verified, with application assets and launcher metadata. Exported version follows the application version.
- I02: common geometric validation across RANSAC/MAGSAC/LMEDS; removed unverified centroid fallback and silent estimator substitution. Checks include support, projective horizon and actual polygon overlap. Center is projected through H.
- I03: batch reprojection residual has its own field; localization error remains unavailable without external ground truth.
- I13 build foundation: shared host builder, Windows setup recipe, macOS app/DMG, Linux Debian/portable artifacts, build provenance and native runner workflow.
- I12/I08 progress: core checks require no models; preserve exact Windows snapshots on their recorded platform and test geometry against known transforms on all targets.
- Documentation: dated research review, task ledger, deployment guide, restored development rules and changelog. Historical handoff documents point here.

## Verification and evidence

- Original pre-change baseline: 90 passed, 2 skipped.
- Latest local full suite before the final test-only portability change: 104 passed, 2 skipped in 36.41s. Follow-up portable/default-contract tests: 8 passed in 4.23s.
- Focused new-module Mypy: passed for validator, bundle builder and smoke checker (3 files; imported modules excluded).
- Fresh wheel build and Windows source/bundled checks passed.
- First native bundle run `39300439636` passed. Adding full native core tests then exposed Windows-only snapshot assumptions in `39301243754`; original golden values were retained, their scope corrected, and final run `39301662952` passed.
- Windows build discovery was isolated after detecting an incompatible Poppler ICU DLL on developer PATH.

## Next work and limits

Follow [IMPROVEMENT_PLAN.md](IMPROVEMENT_PLAN.md), supported by [RESEARCH_REVIEW.md](RESEARCH_REVIEW.md).

1. I07–I08: portable provenance-rich evaluation with held-out annotated/negative pairs. Existing saved sample summaries predate the geometry corrections and must be rerun before drawing conclusions.
2. I09–I11: capability registry, job lifecycle/stale-result protection and calibrated quality diagnostics.
3. I12/I13/I14 release gates: dependency/model notices, optional learned runtime in desktop bundles, signing/notarization, native accessibility/scaling, user-driven desktop and install/uninstall checks. Standard bundles currently include SIFT/ORB; learned support is not advertised as packaged-ready.

## Historical Phase 1 snapshot (superseded)


The project is in a stable, verified Windows desktop-analysis state after the Phase 1 fix pass.

- SIFT/ORB behavior is pinned by frozen regression goldens (updated for opencv-contrib-python 4.11).
- The codebase supports the classical SIFT/ORB path, guarded AKAZE/BRISK entries, optional matching/robust-estimator variants, and the venv-only learned path for SuperPoint+LightGlue, XFeat, ALIKED+LightGlue, DISK+LightGlue, and SIFT+LightGlue when their dependencies are available.
- The system Python environment has `lightglue` installed and all learned engines are active.
- XFeat is the only remaining optional engine not yet installed (requires `accelerated-features` from verlab).

## Completed

### Original milestones (M0–M8)
- Initialized and continued the repo on `main` with the configured GitHub remote.
- Delivered the PySide6 desktop app with drag-and-drop inputs, previews, image metadata, toolbar actions, and dark themed analysis workspace.
- Implemented SIFT and ORB feature extraction, matching, RANSAC homography, localization, rectification, and structured results output.
- Added comparison, benchmark, JSON/CSV/export, and project save/load features.
- Wired the details dock and the overlay controls for match thickness and rainbow option.
- Added the optional learned-engine support path for SuperPoint+LightGlue, XFeat, and ALIKED+LightGlue.
- Added the UI regression fix for the dropped pair-history controls and stale result handling after image changes.
- Added the sample dataset scaffolding under `Sample/Reference` and `Sample/Target`.

### Phase 1 — Install flow fix + repo restoration (v0.2.0)
- Restored missing `pyproject.toml` (was deleted from disk, only egg-info remained).
- Restored missing `README.md` with accurate install instructions.
- Added `.gitignore` and initialized the Git repository.
- Fixed `_install_learned_engines()` — the old implementation had three critical bugs:
  1. It tried to create a new `.venv` even when one already existed (would overwrite torch).
  2. It used `xfeat` as the pip package name — the real package is `accelerated-features` from verlab.
  3. It had no progress feedback — the UI appeared frozen during install.
- Added `InstallWorker` QThread that runs pip in a background thread with live line-by-line output to the engine console.
- Fixed install to target `sys.executable` (the running interpreter) instead of creating a new venv.
- Added `_refresh_engine_selector()` — dynamically re-evaluates engine availability after install and updates the selector without requiring a restart.
- Added soft `importlib.reload()` of learned engine modules after install so engines activate in the same session when possible.
- Fixed `XFeatEngine.extract_and_match()` — removed `sklearn.NearestNeighbors` dependency (sklearn not installed); replaced with pure-numpy L2 nearest-neighbour using matrix operations.
- Updated engine selector hint text to be actionable ("click 'Install learned engines'").
- Updated golden regression baseline for `opencv-contrib-python 4.11` (ORB inlier count changed from 760 → 731 due to RANSAC implementation changes in the new opencv version).

## Verification

Fresh project verification ran successfully on the active workspace:

- Python environment: system Python 3.11.9 (`C:\Users\Luikz\AppData\Local\Python\pythoncore-3.11-64`)
- Command: `python -m pytest -q`
- Result: **90 passed, 2 skipped in 26.01s**
- Exit code: 0

## Current focus (Phase 2 — next)

1. Engine Status Dialog — a dedicated dialog showing each engine's availability, version, and install button per engine.
2. Per-engine config panels in the UI for SuperPoint/ALIKED/XFeat (max_keypoints, detection_threshold, use_cuda).
3. Improve details panel for learned engines (currently shows minimal info).
4. Extend benchmark to include learned engines when available.
5. XFeat install — verify `accelerated-features` package installs and works correctly.

## Known limitations

- XFeat is not yet installed (`accelerated-features` package from verlab not yet in the environment).
- Learned engines are disabled in the packaged EXE (PyInstaller + TorchScript incompatibility is a known architectural constraint).
- AKAZE and BRISK stay disabled because the pinned opencv-contrib-python wheel does not ship them.
- The project remains a planar-scene registration tool; it does not claim general 3D pose recovery.
