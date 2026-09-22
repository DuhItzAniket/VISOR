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
- UI execution has not yet been inspected because PySide6 is absent from this environment. Core paths have not yet received an automated test suite.
