# Changelog

## Unreleased

- Frozen SIFT/ORB regression goldens (`tests/test_classical_frozen.py`) so engine work can't silently shift classical numbers
- Central engine registry with guarded AKAZE/BRISK entries that stay disabled on OpenCV builds without them
- Optional matchers (cross-check, FLANN, symmetric ratio) and robust estimators (MAGSAC, LMEDS) behind frozen defaults
- Planar similarity estimates (rotation/scale/translation) on every analysis result, details dock, and JSON export
- Multi-pair batch runner with `manifest.csv`, batch CSV export, and desktop UI
- Rotation/scale robustness sweeps beside the nine-scenario benchmark, with desktop UI
- DISK+LightGlue and SIFT+LightGlue venv-only engines reusing the installed lightglue package
- Planar reference tracking across video files with per-frame reporting
- Tested camera calibration (synthetic intrinsics/pose recovery, chessboard folders) with a desktop action
- Engine selector lists new engines with missing-dependency reasons; project files restore any engine by name

## v0.1.0 — 2026-09-23

First release of VISOR — Visual Object Registration & Analysis.

### Added

- PySide6 desktop application with dark theme, menu bar, toolbar, dock panels, and status bar
- Reference and target image input with drag-and-drop and native file picker (PNG, JPEG, BMP, TIFF, WebP)
- SIFT engine: configurable `nfeatures`, `nOctaveLayers`, `contrastThreshold`, `edgeThreshold`, `sigma`; 128-D FLOAT32 descriptors; brute-force L2 KNN matching with Lowe ratio filter
- ORB engine: configurable all 9 parameters; 32-byte BINARY descriptors; Hamming / Hamming2 KNN matching with Lowe ratio filter
- RANSAC planar homography with inlier mask, projected corners, center, and mean reprojection error
- Feature Matches view, Localization view, and Warped / Rectified view with zoom, pan, fit, and cursor coordinates
- Keypoint inspection: click Localization view to read nearest target keypoint details
- Visualization toggles: match lines, inliers, outliers, keypoints, localization geometry
- Analysis Details dock with structured SIFT/ORB engine panels, geometry, and performance tabs
- SIFT vs ORB comparison mode
- Benchmark Lab: nine controlled synthetic transformations with ground-truth corner RMSE
- Export: JSON analysis, CSV metrics, comparison CSV, benchmark CSV, PNG/JPEG visualization
- Project save/load as `.visor` JSON session files
- Toolbar with SVG icon actions
- Keyboard shortcuts: F5 Run, Ctrl+1/2 Open images, 0 Fit View, Ctrl+S/O/Q
- Threaded analysis with cancellation support
- PyInstaller one-folder Windows build (`dist\VISOR\VISOR.exe`)
- 16 automated tests covering engines, matching, geometry, pipeline, exports, and benchmark
