# Architecture Decisions

## 2026-10-19: Scope exact snapshots to the recorded platform

Native CI reproduced different OpenCV feature/RANSAC counts on Windows x64, Linux x64, and macOS ARM despite using the same OpenCV package version. Preserve original Windows/OpenCV 4.11 goldens on that platform; require independent known-transform corner accuracy on every platform. Default-option forwarding is checked against explicit defaults on the current platform. Do not rewrite golden counts to conceal algorithm drift or treat cross-platform count equality as accuracy.

## 2026-10-19: Fit failure is not a translation estimate

Remove the keypoint-centroid fallback that reported all matches as inliers with zero error after fitting failed. All estimators use `geometry_validation.validate_planar_fit`; MAGSAC/LMEDS no longer silently run a different estimator on failure. The validator checks support, projection, projective horizon and actual target polygon overlap. Object center is the projected reference center. Positive classical goldens remain unchanged; invalid historical results may intentionally become failures. Adaptive threshold selection remains a separately tracked policy issue (I06).

## 2026-10-19: Batch residual and localization accuracy are distinct

Pair-only manifests have no external transform truth. `BatchRow.localization_error_px` is retained for compatibility but is now `None`; new `reprojection_error_px` contains the measured inlier residual. Batch CSV gains this column and the UI's existing Reproj px column reads it. Consumers must not use fitted residual as ground-truth localization error.

## Use built-in OpenCV SIFT and ORB

SIFT and ORB are classical feature algorithms with stable OpenCV implementations. They require no training or downloaded weights and provide a suitable local baseline.

## Match descriptor types with their appropriate distances

SIFT uses floating point descriptors and L2 distance. ORB uses binary descriptors and Hamming distance, or Hamming2 for `WTA_K` 3 or 4. The engines remain separate while sharing a structured result interface.

## Treat homography output as planar image-space estimation

RANSAC homography is useful for projecting a planar reference into a target image. VISOR describes it as an estimate and does not present it as general 3D pose recovery.

## Run analysis outside the Qt event thread

Image decoding, extraction, matching, and geometry run on a `QThread` worker so the desktop event loop can continue responding during analysis.

## Use a structured details panel instead of a plain text area

The `AnalysisDetailsPanel` renders engine-specific sections (SIFT configuration vs ORB configuration, keypoint statistics, descriptor info, geometry, performance) in a structured tab/tree layout. This makes algorithm-specific information discoverable and avoids mixing SIFT and ORB fields in a single text dump.

## Use SVG icons in the toolbar

SVG icons scale cleanly at any DPI. They are stored in `assets/icons/` and loaded via `QIcon`. The `_icon()` helper resolves the path both in a normal Python install and in a PyInstaller `_MEIPASS` bundle.

## One-folder PyInstaller distribution

A one-folder distribution (`dist/VISOR/`) is easier to inspect and debug than a single-file bundle. The folder must be distributed as a unit. Single-file packaging is a future option once the one-folder build is validated on a clean machine.

## Defer caching

Feature extraction caching would require a content-hash key, invalidation logic, and disk management. The benefit is only measurable when the same image is analyzed repeatedly with the same configuration. This is deferred until profiling shows it is worthwhile.

## Measure learned stages and preserve estimator provenance (2026-10-25)

Learned engines return typed pair results with separately measured extraction/matching stages, actual device and matcher scores. Assignment scores are not descriptor distances or localization probabilities. Analysis JSON moves to schema 2 with nullable unavailable fields and measured runtime/geometry provenance; see RESULT_CONTRACT.md. Preserve the legacy adaptive RANSAC sequence for regression compatibility while exposing its actual attempted thresholds. Learned paths use the same selected robust estimator as classical paths.
