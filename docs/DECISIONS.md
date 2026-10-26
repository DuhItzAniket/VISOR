# Architecture Decisions

## 2026-10-26: Keep overlay requests bounded and results atomic

Overlay controls request background presentation work rather than drawing synchronously. Keep one active worker and one replaceable pending style; cooperate with cancellation between drawing batches and reject obsolete ticket delivery. Install images and their effective settings together, retain the old result on failure/cancel, and wait before exporting a pending style. Preserve the inspected viewport and avoid re-uploading unchanged rectified images. Own QImage bytes in BGR order; QPixmap creation stays on the GUI thread. Rendering does not rerun or change fitting, measured algorithm stages or independent accuracy claims.

## 2026-10-26: One OpenCV provider with Qt as the desktop interface

Actual Linux artifact inventory showed OpenCV's Qt5 runtime alongside PySide's Qt6. Use the same OpenCV 4.11.0.86 contrib APIs through the headless wheel, following upstream guidance for apps whose interface is supplied by another toolkit. No application HighGUI calls exist. Reject overlapping cv2 distributions during packaging and require compiled GUI backend (NONE, with the upstream 4.11 Mac Cocoa exception). Retain the classical golden fixtures and test actual image/video functionality in isolated source and native frozen builds. This minimizes unnecessary GUI dependencies; it does not remove all native codec dependencies or certify their licensing.

## 2026-10-26: Audit actual artifacts without inventing ownership

Collect exact installed dependency/interpreter notices offline and a hash-pinned Qt source corpus; version-matched Qt source fallback is explicit when wheels omit standalone texts. Hash the actual frozen filesystem outside the app, preserving ambiguous origins and opaque native/embedded contents. Unique relocated filename mapping is labeled; links/signature metadata are not library ownership. These records support review rather than certify transitive/source-offer compliance. Exclude unused Qt PDF-image/Virtual Keyboard plugins while protecting advertised image codecs through actual frozen decoding checks.

## 2026-10-26: Apache-2.0 for original VISOR source

The owner selected Apache-2.0. Root LICENSE/NOTICE, SPDX package metadata and source-wheel/desktop notice inclusion implement that choice. Dependencies, model weights and datasets retain their terms. Project licensing does not close the separate per-artifact third-party notice review.

## 2026-10-26: Preserve study outcomes rather than promote unconfirmed gates

The preregistered I15 inlier/support gates improved development counts but rejected no additional reserved reporting fits; a 343-inlier SIFT fit still had 9.88 px mean corner error. Do not promote the gates into desktop defaults or retune them on reporting scenes. Publish all choices, attempts and unsupported-truth rows; retain the original estimator/goldens. See evaluation/RELIABILITY_FINDINGS.md.

## 2026-10-26: Separate JSON content identity from original input bytes

Keep the original file-byte hash for provenance and add a canonical parsed-JSON hash for portable content verification. Git's CRLF/LF conversion must not look like a changed gate. New study JSON uses LF; compressed raw evidence retains exact bytes. The cross-platform regression that found this distinction remains recorded in the implementation log.

## 2026-10-26: Build versions identify frozen source

Read the literal source version without importing/executing the application. Installed developer-wheel metadata can be stale and must not relabel the executable, installer/archive or build-info. Missing/nonliteral source versions fail before packaging.

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
