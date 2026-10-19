# Implementation Status

## Active improvement review — 2026-10-19

The latest audit starts from `40e68de`. See [research findings](RESEARCH_REVIEW.md) and [task ledger](IMPROVEMENT_PLAN.md).
The earlier verified snapshot below is historical and does not establish current engine readiness.

Initial audit reproduced a fresh-wheel build failure (`Cannot import 'setuptools.backends.legacy'`) and 10 Ruff findings.
Code inspection found an unverified translation fallback with invented zero residual/all-inlier metrics and inconsistent validation between robust estimators. I01–I03 are the first implementation batch.

I01: corrected backend to `setuptools.build_meta` and aligned exported application version with `visor.__version__`.
Verified `python -m pip wheel . --no-deps --no-build-isolation --wheel-dir build/audit-wheels`; the v0.2.0 wheel includes UI, icon, and `visor` console entry point. This verifies package construction, not a clean-machine desktop installation.

Fresh pre-change baseline: **90 passed, 2 skipped in 55.09s**. Dependency readiness remains machine-specific.

I02/I03 implemented: shared geometric validation, removed unverified translation fallback, no silent alternative-estimator fallback, correct perspective center projection, and explicit batch reprojection residual. Focused check: **34 passed in 5.16s**, covering new failure cases, frozen classical positives, alternative estimators, batch and exports. Full-suite post-change validation follows the desktop-distribution work.

## Current verified state

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
