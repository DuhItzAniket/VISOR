# Implementation Log

## M0 — Repository foundation

- Added project plan, architecture, status, development rules, and ignore patterns.
- Initialized an isolated Git repository on `main`; configured and pushed `origin`.
- Verified the remote had no existing branch refs before the first push.

## M1 — Desktop shell and image input

- Added setuptools packaging metadata and `python -m visor` entry point.
- Added a restrained dark PySide6 main window and image input widgets.
- Each input supports a native file picker and drag-and-drop of PNG, JPEG, BMP, TIFF, and WebP.
- Image previews show filename and pixel dimensions; unreadable files produce visible feedback and a log entry.
- Analysis actions are not exposed until the underlying analysis pipeline exists.

## M2–M5 — Classical registration pipeline

- Added typed result records and separate SIFT, ORB, matching, geometry, and pipeline modules.
- SIFT descriptors use brute-force L2 matching; ORB descriptors use Hamming or Hamming2 according to `WTA_K`. Both paths use KNN candidates and ratio filtering.
- RANSAC estimates a planar homography, inlier mask, projected reference corners, center, and mean inlier reprojection error. Numerically degenerate transforms and insufficient matches are reported as failures.
- Added worker-thread analysis, match visualization, localized target polygon, optional rectification, and measured timing/engine details in the UI.

## M6 — Comparison, benchmark, and exports

- Added `compare_engines` pipeline function that decodes images once and runs both engines.
- Added `ComparisonWorker` and comparison display in the main window.
- Added `benchmark.run_benchmark` with nine deterministic synthetic transformations (baseline, rotation+scale, perspective, brightness, contrast, blur, noise, crop, resolution reduction) and ground-truth corner RMSE.
- Added `BenchmarkWorker` and a results dialog with a sortable table.
- Added cancellation via `threading.Event` checked at safe pipeline boundaries.
- Added `exporting` module: JSON analysis documents, CSV metrics, comparison CSV, benchmark CSV, PNG/JPEG visualization, and `.visor` project session save/load.
- Added PyInstaller `build_windows.ps1` script and multi-resolution `.ico` generator.
- Added 16 automated tests covering engines, matching, geometry edge cases, pipeline integration, exports, and benchmark.

## M7 — Algorithm-specific details panel

- Added `AnalysisDetailsPanel` widget with tab and tree view modes.
- SIFT tab shows: configuration (max features, octave layers, contrast threshold, edge threshold, sigma), keypoint statistics (count, mean size, mean response, mean angle, octave distribution), descriptor info (128-D FLOAT32, L2, memory).
- ORB tab shows: configuration (all 9 parameters), keypoint statistics, descriptor info (32-byte BINARY, Hamming/Hamming2, memory).
- Geometry tab shows: homography status, inlier/outlier counts, inlier ratio, mean reprojection error, projected corners, center.
- Performance tab shows per-stage timing.
- Keypoint inspection: clicking the Localization view appends the nearest target keypoint's full record to a Selected Keypoints tab.
- Comparison mode calls `populate_comparison` to show both engines' structured results.

## M8 — Toolbar, packaging, and release

- Added `QToolBar` with SVG icon actions: Open Reference, Open Target, Run, Compare, Benchmark, Cancel, Export, Fit View.
- Added `assets/icons/` to `pyproject.toml` package data and PyInstaller `--add-data`.
- Fixed `_icon()` to resolve `visor/assets/icons/` correctly under PyInstaller `_MEIPASS`.
- Built and verified `dist/VISOR/VISOR.exe` one-folder distribution; all 9 SVG icons confirmed present in `_internal/visor/assets/icons/`.
- Updated README with full feature list, keyboard shortcuts, architecture overview, export table, and troubleshooting guide.
- Updated ARCHITECTURE.md with full module map, data flow diagram, threading model, and extension model.
- Tagged v0.1.0.
