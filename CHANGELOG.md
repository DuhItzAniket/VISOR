# Changelog

## Unreleased

- Established the project plan and modular architecture.
- Added a PySide6 application shell with reference/target image selection and drag-and-drop.
- Added SIFT and ORB feature extraction, descriptor-appropriate ratio-tested matching, RANSAC planar localization, result imagery, and performance details.
- Added SIFT vs ORB comparison mode, benchmark lab with controlled synthetic transformations and ground-truth corner RMSE, JSON/CSV/image exports, and project save/load.
- Added structured `AnalysisDetailsPanel` with engine-specific SIFT and ORB sections (configuration, keypoint statistics, descriptor info, geometry, performance) in tab and tree view modes.
- Added main toolbar with SVG icon actions.
