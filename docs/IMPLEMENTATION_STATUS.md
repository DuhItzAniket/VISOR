# Implementation Status

## Current milestone

M10 complete — SuperPoint+LightGlue learned engine added.

## Completed

- Confirmed the working folder was empty and isolated it from an unrelated Git repository at the user home directory.
- Initialized a repository on `main` and configured the requested GitHub URL as `origin`.
- Recorded project vision, architecture, milestone sequence, and drag-and-drop image input requirement.
- Added an installable Python package and PySide6 desktop shell with reference/target file pickers, drag-and-drop input, previews, image dimensions, and invalid-image feedback.
- Added startup logging and a visible planar-geometry limitation statement.
- Added typed records for features, descriptors, matches, geometry, analysis, and performance.
- Implemented configurable SIFT and ORB extraction, L2/Hamming/Hamming2 KNN matching with Lowe ratio filtering, and RANSAC homography localization.
- Connected the pipeline to a Qt worker thread and added feature-match, localization, rectification, and analysis-details views.
- Added SIFT/ORB-specific parameter controls, geometry/match visualization toggles, zoom/pan/fit canvases, cursor coordinates, and nearby keypoint inspection.
- Added a comparison workflow, deterministic synthetic transformation benchmark with ground-truth corner error, cancellation at safe stage boundaries, and analysis/benchmark exports.
- Added JSON project sessions, JSON/CSV/image exports, PyInstaller Windows build script, and a multi-resolution application icon.
- Added core integration, geometry, matching, export, benchmark, and offscreen UI coverage.
- Wired the structured `AnalysisDetailsPanel` (tab/tree view with engine-specific SIFT and ORB sections) into the main window dock, replacing the plain-text details area.
- Added a main toolbar with SVG icon actions for Open Reference, Open Target, Run, Compare, Benchmark, Cancel, Export, and Fit View.
- Included `assets/icons/` in package data and PyInstaller bundle; fixed `_MEIPASS` icon resolution for the standalone build.
- Built and verified `dist/VISOR/VISOR.exe` one-folder Windows distribution with all assets bundled.

- Added `visor.learned_engines` module with `SuperPointLightGlueEngine` implementing the `FeatureEngine` protocol via SuperPoint extraction and LightGlue joint matching.
- Added graceful unavailability guard: engine raises `LearnedEngineUnavailable` when `torch`/`lightglue` are absent; UI disables the selector item with an install hint.
- Added `SuperPoint+LightGlue` to `EngineName` literal and pipeline dispatch (`_analyze_learned` branch).
- Added `[learned]` optional dependency group in `pyproject.toml`.
- Added 5 new tests for the learned engine (extract, match, pipeline integration, config validation, unavailability).
- Total: 21 tests passing.

## Verification

- Python 3.11.9, PyTorch 2.2.2+cu118, LightGlue 0.0, OpenCV 4.11, PySide6 6.11.
- `python -m pytest -q`: 21 passed.
- `python -m ruff check src tests`: passed.

## Next

Add ALIKED+LightGlue as a second learned engine (M10 continuation), then M11 HTML/PDF report export.

## Known limitations

Caching remains deferred until repeated analysis demonstrates a measurable benefit. Installer signing and clean-machine distribution validation require a separate target system.
