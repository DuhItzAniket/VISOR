# VISOR

**Visual Object Registration & Analysis** — a professional Windows desktop application for comparing classical local image features and estimating planar object location from a reference image and a target image.

## Features

- **SIFT and ORB engines** — OpenCV implementations, no model training or weight downloads
- **Learned engine support** — optional SuperPoint+LightGlue, XFeat, ALIKED+LightGlue, DISK+LightGlue, SIFT+LightGlue when dependencies are installed
- **One-click install** — click **Install learned engines** in the toolbar; the app installs the correct packages into the running Python environment with live console output
- **Drag-and-drop image input** — drop PNG, JPEG, BMP, TIFF, or WebP into either slot, or use the file picker
- **Feature Matches view** — side-by-side match lines with inlier (green) / outlier (red-blue) coloring
- **Localization view** — projected reference polygon and center point drawn on the target image
- **Warped / Rectified view** — target image perspective-corrected back to reference dimensions
- **Analysis Details dock** — structured engine-specific panels (configuration, keypoint statistics, descriptor info, geometry, performance)
- **Keypoint inspection** — click a point in the Localization view to read the nearest target keypoint record
- **SIFT vs ORB comparison** — runs both engines on the same pair and shows a side-by-side metrics table
- **Benchmark Lab** — nine controlled transformations with corner RMSE against known synthetic geometry
- **Robustness Sweep** — rotation and scale sweep across engines
- **Batch processing** — run a CSV manifest of image pairs across engines
- **Video tracking** — track a reference object through a video file frame by frame
- **Camera calibration** — chessboard-based intrinsic calibration
- **Export** — JSON analysis, CSV metrics, comparison CSV, benchmark CSV, HTML report, PNG/JPEG visualization
- **Project save/load** — stores image paths and all parameters in a `.visor` file
- **Dark theme** — restrained professional dark UI
- **Threaded analysis** — all OpenCV work runs off the UI thread with cancellation support

## Quick start

```powershell
# 1. Create environment (skip if .venv already exists)
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip setuptools wheel

# 2. Install the app
python -m pip install -e .

# 3. Run
python -m visor
```

## Installing learned engines

The app ships with SIFT and ORB ready to use. Learned engines (SuperPoint+LightGlue, ALIKED+LightGlue, DISK+LightGlue, SIFT+LightGlue, XFeat) require additional packages.

**Option A — one-click from the app:**
Click **Install learned engines** in the toolbar. The app installs the correct packages into the running Python environment and shows live progress in the engine console. Restart the app after installation.

**Option B — manual install:**
```powershell
# LightGlue (covers SuperPoint, ALIKED, DISK, SIFT+LG)
pip install git+https://github.com/cvg/LightGlue.git

# XFeat
pip install git+https://github.com/verlab/accelerated_features.git#subdirectory=.
```

> **Note:** Learned engines require `torch` and `torchvision`. The venv already includes CUDA-enabled torch if you installed the `[learned]` extra. They are disabled in the packaged EXE — run from source for learned engine support.

## Development

```powershell
python -m pip install -e ".[dev]"
python -m pytest -q
python -m ruff check src tests
```

## Windows standalone build

```powershell
.\scripts\build_windows.ps1
```

Produces `dist\VISOR\VISOR.exe`. The entire `dist\VISOR\` folder must stay together. Learned engines are not available in the packaged EXE.

## Architecture

```
PySide6 UI (main_window, image_canvas, image_drop, details_panel)
    │
    ├── Workers (QThread): Analysis / Comparison / Benchmark / Install
    │       │
    │       └── pipeline.analyze / compare_engines / benchmark.run_benchmark
    │               │
    │               ├── engines.SIFTFeatureEngine / ORBFeatureEngine
    │               ├── learned_engines.SuperPointLightGlueEngine / ALIKEDLightGlueEngine / XFeatEngine
    │               ├── learned_extra.DISKLightGlueEngine / SIFTLightGlueEngine
    │               ├── matching.match_features
    │               ├── geometry.estimate_homography
    │               └── visualization.render_match_canvas / render_localization
    │
    └── exporting (JSON, CSV, HTML, project save/load)
```

See [Architecture](docs/ARCHITECTURE.md) for the full module map and data flow.

## Geometry scope

Homography estimates apply to planar scenes. Projected corners, center coordinates, and derived rotation/scale values are image-space estimates under a planar assumption. They do not represent general 3D pose.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| No keypoints detected | Image is blank or low contrast | Use a textured image with visible features |
| Geometry invalid | Too few good matches | Lower the ratio threshold or switch to SIFT |
| Learned engines greyed out | Dependencies not installed | Click **Install learned engines** in the toolbar |
| Install button installs but engines still greyed out | Restart required | Restart the app after installation |
| Icons missing in toolbar | Running from source without install | Run `python -m pip install -e .` |
| Build fails on `generate_icon.py` | Pillow not installed | Run `python -m pip install -e ".[build]"` |

## Project status

See [Implementation Status](docs/IMPLEMENTATION_STATUS.md) and [Project Plan](docs/PROJECT_PLAN.md).
