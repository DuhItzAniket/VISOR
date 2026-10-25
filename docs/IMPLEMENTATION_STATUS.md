# Implementation Status

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
