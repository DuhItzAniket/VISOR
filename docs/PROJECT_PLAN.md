# VISOR Project Plan

## Vision

Build a maintainable Windows desktop tool that compares classical feature-based methods for locating a planar reference object in a target image. The app should make its inputs, configuration, geometry assumptions, and measured outputs visible.

## Architecture

- `visor.models`: typed domain/result contracts.
- `visor.engines`: feature extraction adapters for OpenCV SIFT and ORB.
- `visor.matching`: descriptor-appropriate matching and filtering.
- `visor.geometry`: homography estimation and planar localization.
- `visor.pipeline`: coordinates the core stages and timing.
- `visor.ui`: PySide6 shell, image input, visualization, and details.

The UI consumes structured pipeline results. OpenCV objects stay inside the vision layer except for deliberately exposed keypoint detail records. Worker execution keeps processing off the UI thread.

## Technology

Python 3.11+, OpenCV, NumPy, PySide6, pytest, and Ruff. Use OpenCV's built-in SIFT/ORB implementations without model training or weight downloads.

## Milestones and acceptance criteria

1. **M0 Repository and plan** — isolated `main` repository, development rules, architecture and implementation plan committed.
2. **M1 Foundation and image-input UI** — installable package, logging/configuration baseline, professional Qt shell, reference/target selection including drag-and-drop, and clear validation/error feedback.
3. **M2 Domain contracts and engine interface** — typed image, feature, match, geometry, timing and analysis records.
4. **M3 SIFT and ORB extraction** — configurable engines and engine-specific metadata.
5. **M4 Matching and filtering** — L2 for SIFT, Hamming/Hamming2 for ORB, ratio filtering and measured timings.
6. **M5 Planar geometry/localization** — RANSAC homography, inlier accounting, projected corners and failure handling.
7. **M6 Visualization and analysis details** — reference/target/matches/localization views, algorithm-specific details and interaction.
8. **M7 Comparison, benchmark and export** — comparable SIFT/ORB results, controlled transformations and JSON/CSV/image export.
9. **M8 Packaging and release docs** — Windows build, usage/developer docs and release hardening.

## Ordered first implementation tasks

- M1.1 Create `pyproject.toml`, package entry point, and runtime dependencies.
- M1.2 Add a Qt main window with reference and target drop zones, browse buttons, image preview/metadata, and useful empty/error states.
- M1.3 Add logging setup and document install/run instructions.
- M2.1 Define typed domain records and engine protocol.
- M3-M5.1 Implement SIFT/ORB pipeline and planar geometry in separate modules.
- M6.1 Render analysis views and expose actual pipeline metrics.

## Testing strategy

Add focused unit tests for image validation, engine output contracts, matching distance norms, geometry success/failure, and deterministic synthetic image-pair integration. Keep GUI tests limited to key input and state behavior. Use small generated fixtures rather than large datasets.

## Packaging strategy

First stabilize a normal Python install and launch. Then build a Windows standalone distribution with PyInstaller or Nuitka and validate the packaged app on a clean environment before considering a one-file installer.

## Documentation strategy

Keep README, architecture, implementation status/log, decisions, and changelog updated as milestones land. Document planar assumptions and estimate wording wherever geometry is presented.

## Extension points

Future feature engines and matchers may include SuperPoint, ALIKED, XFeat, and LightGlue. They remain optional and out of the classical first release.

