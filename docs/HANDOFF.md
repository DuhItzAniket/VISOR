# VISOR continuation guide

## Purpose

VISOR is a Windows desktop app for visual object registration and planar localization. The application compares reference and target images using classical local feature pipelines and, when optional dependencies are installed, learned matchers such as SuperPoint+LightGlue, XFeat, and ALIKED+LightGlue.

## Current verified baseline

- Python workspace: project venv under the repo root
- Test command: `python -m pytest -q`
- Last verified result: 33 passed in 22.43s
- UI regression fix: the pair-history list and stale-result refresh path are implemented without the earlier `QListWidget` and stale widget reference errors.

## Core architecture

- `src/visor/ui/main_window.py` — main Qt window, worker orchestration, image state, list/history panel, settings, and result rendering
- `src/visor/ui/widgets/image_drop.py` — file picker and drag-and-drop input widgets
- `src/visor/ui/widgets/image_canvas.py` — zoom/pan result canvas
- `src/visor/ui/widgets/details_panel.py` — structured results dock
- `src/visor/pipeline.py` — end-to-end analysis pipeline and learned-engine dispatch
- `src/visor/engines.py` — SIFT/ORB descriptor extraction wrappers
- `src/visor/matching.py` — candidate matching and ratio filtering
- `src/visor/geometry.py` — homography estimation and planar geometry validation
- `src/visor/visualization.py` — match and localization overlays
- `src/visor/learned_engines.py` — optional learned backends with guarded import checks
- `src/visor/exporting.py` — JSON/CSV/project export and session loading

## Important project rules

- Keep computer-vision logic separate from Qt widgets.
- Use OpenCV built-in SIFT and ORB implementations; do not train custom models in this repo.
- Keep heavy processing on background threads.
- Label homography and projected geometry as estimates under a planar-scene assumption.
- Do not commit secrets, environment files, or generated build artifacts.

## Current user-facing workflow

1. Load a reference image and target image.
2. Select the engine from the selector.
3. Adjust matching and geometry parameters if needed.
4. Run analysis or compare SIFT/ORB.
5. Inspect match, localization, and warped views.
6. Save/export results or project session when needed.

## Regression and validation commands

```powershell
cd <repo-root>
.venv\Scripts\Activate.ps1
python -m pytest -q
```

## Git workflow

- Work on `main` unless explicitly told otherwise.
- Keep commits focused and conventional.
- Avoid committing local environments, caches, or generated `dist/` / `build/` output
- Push verified work after validation.

## Immediate next tasks

- Continue the multi-pair inspection workflow for saved reference/target pairs.
- Expand the sample dataset strategy for GPU-based evaluation on the RTX 4050.
- Track any additional learned-engine tuning and parameter calibration under the same repo structure.
- Keep documentation aligned with the actual code and runtime behavior.
