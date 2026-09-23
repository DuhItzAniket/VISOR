# Architecture Decisions

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
