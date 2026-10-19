# Changelog

## Unreleased — improvement review 2026-10-19

- Added source-backed research review and a prioritized improvement plan with acceptance gates and documentation ownership.
- Fixed fresh wheel construction and stale exported version metadata.
- Removed unverified localization fallback; shared validation across robust estimators now checks support, projective horizon, projected polygon and true target overlap.
- Corrected projected center and separated batch reprojection residual from unknown localization accuracy.
- Added standalone Windows installer/ZIP, macOS app/DMG and Linux Debian/portable build paths, with native runner artifacts and bundled workflow checks.
- Fixed Windows DLL discovery contamination and blocked developer package installation inside bundled desktop apps.

## 0.2.0 — existing baseline

- Existing Qt desktop workspace, classical and optional learned adapters, engine status, comparison, benchmark, sweep, batch, tracking, calibration and export workflows.
- Historical implementation details are retained in `docs/IMPLEMENTATION_LOG.md`.
