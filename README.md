# VISOR

**Visual Object Registration & Analysis** — a professional Windows desktop application for comparing classical local image features and estimating planar object location from a reference image and a target image.

## Features

- **SIFT and ORB engines** — OpenCV implementations, no model training or weight downloads
- **Drag-and-drop image input** — drop PNG, JPEG, BMP, TIFF, or WebP into either slot, or use the file picker
- **Feature Matches view** — side-by-side match lines with inlier (green) / outlier (red-blue) coloring
- **Localization view** — projected reference polygon and center point drawn on the target image
- **Warped / Rectified view** — target image perspective-corrected back to reference dimensions
- **Analysis Details dock** — structured engine-specific panels for SIFT and ORB (configuration, keypoint statistics, descriptor info, geometry, localization, performance)
- **Keypoint inspection** — click a point in the Localization view to read the nearest target keypoint's coordinates, size, angle, response, and octave
- **SIFT vs ORB comparison** — runs both engines on the same pair and shows a side-by-side metrics table
- **Benchmark Lab** — generates nine controlled transformations (baseline, rotation+scale, perspective, brightness, contrast, blur, noise, crop, resolution reduction) and measures both engines against known synthetic geometry
- **Visualization toggles** — show/hide match lines, inliers, outliers, keypoints, and localization geometry without re-running analysis
- **Export** — JSON analysis, CSV metrics, comparison CSV, benchmark CSV, and PNG/JPEG visualization
- **Project save/load** — stores image paths and all parameters in a `.visor` file
- **Toolbar** — icon actions for Open Reference, Open Target, Run, Compare, Benchmark, Cancel, Export, and Fit View
- **Keyboard shortcuts** — F5 Run, Ctrl+1 Open Reference, Ctrl+2 Open Target, 0 Fit View, Ctrl+S Save, Ctrl+O Open, Ctrl+Q Exit
- **Dark theme** — restrained professional dark UI; no emoji icons, no decorative gradients
- **Threaded analysis** — all OpenCV work runs off the UI thread; the window stays responsive and supports cancellation

## Project status

See [Implementation Status](docs/IMPLEMENTATION_STATUS.md) and [Project Plan](docs/PROJECT_PLAN.md).

## Development setup

Requires Python 3.10 or newer. Install dependencies and launch from the repository root:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m visor
```

Run tests:

```powershell
python -m pytest -q
```

Run linter:

```powershell
python -m ruff check src tests
```

## Image input

Drag a PNG, JPEG, BMP, TIFF, or WebP file into either image input area, or select it using the corresponding **Choose image…** button or the toolbar. The UI shows the image dimensions and filename after loading.

Select SIFT or ORB from the engine selector, adjust parameters under **Analysis Details → Parameters**, then choose **Run analysis** (or press F5). **Compare SIFT / ORB** runs both engines against the same pair and shows a structured comparison in the details dock.

The **Benchmark Lab** generates controlled image transformations from the reference image and measures both engines. Results appear in a table with corner RMSE against known synthetic geometry.

## Analysis Details dock

The right-side dock shows structured results after each analysis:

- **Overview** — input files, resolution, extraction counts, matching summary
- **Engine (SIFT / ORB)** — algorithm configuration, keypoint statistics, descriptor info
- **Geometry** — homography status, inlier/outlier counts, inlier ratio, reprojection error, projected corners, center
- **Performance** — per-stage timing in milliseconds

Click any point in the **Localization** view to inspect the nearest target keypoint. Its details appear in a **Selected Keypoints** tab in the dock.

## Geometry scope

Homography estimates apply to planar scenes. Projected corners, center coordinates, and derived rotation/scale values are image-space estimates under a planar assumption. They do not represent general 3D pose.

## Export

Use **File → Export** to save:

| Format | Contents |
|---|---|
| JSON | Full analysis document with all metrics and homography matrix |
| CSV | Single-row metrics summary |
| Comparison CSV | SIFT vs ORB side-by-side metrics |
| Benchmark CSV | All engine × scenario rows |
| Visualization | Current view as PNG or JPEG |

Use **File → Save Project** to save image paths and current parameters as a `.visor` file. **File → Open Project** restores them.

## Architecture overview

```
PySide6 UI (main_window, image_canvas, image_drop, details_panel)
    │
    ├── AnalysisWorker / ComparisonWorker / BenchmarkWorker  (QThread)
    │       │
    │       └── pipeline.analyze / compare_engines / benchmark.run_benchmark
    │               │
    │               ├── engines.SIFTFeatureEngine / ORBFeatureEngine
    │               ├── matching.match_features
    │               ├── geometry.estimate_homography
    │               └── visualization.render_match_canvas / render_localization
    │
    └── exporting  (JSON, CSV, project save/load)
```

Core vision modules have no Qt dependency. The UI consumes typed `AnalysisResult` / `ComparisonResult` / `BenchmarkReport` records.

See [Architecture](docs/ARCHITECTURE.md) for the full module map.

## Windows standalone build

On Windows with Python installed, run:

```powershell
.\scripts\build_windows.ps1
```

This installs build dependencies, regenerates the application icon, and produces a one-folder PyInstaller distribution at `dist\VISOR\VISOR.exe`. The entire `dist\VISOR\` folder must stay together when distributing. Test on a clean Windows machine before wider release.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| No keypoints detected | Image is blank, very small, or low contrast | Use a textured image with visible features |
| Geometry invalid | Too few good matches | Lower the ratio threshold or use SIFT on a richer image |
| Warped view unavailable | Homography failed | Check the Geometry tab in Analysis Details for the failure reason |
| Icons missing in toolbar | Running from source without install | Run `python -m pip install -e .` from the repo root |
| Build fails on `generate_icon.py` | Pillow not installed | Run `python -m pip install -e ".[build]"` |

## Roadmap

Future milestones (not yet implemented):

- **M10** — Learned feature engines: SuperPoint + LightGlue, XFeat, ALIKED
- **M11** — HTML report export (implemented in the current milestone)
- **M12** — Windows installer (NSIS or Inno Setup)
- **M13** — Camera calibration and PnP for non-planar scenes
