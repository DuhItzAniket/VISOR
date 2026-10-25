# VISOR

**Visual Object Registration & Analysis** — a desktop workspace for comparing local image features and inspecting planar registration between a reference and target image.

The distribution target is a standalone desktop app for Windows, macOS, and Linux, with bundled dependencies so end users do not need Python. See [desktop distribution](docs/DESKTOP_DISTRIBUTION.md) for build artifacts, platform validation and current limitations. Source setup commands below are for developers.

Current work: [research review](docs/RESEARCH_REVIEW.md), [improvement plan](docs/IMPROVEMENT_PLAN.md), and [verified implementation status](docs/IMPLEMENTATION_STATUS.md).

VISOR's original source is licensed under [Apache 2.0](LICENSE), with the project [NOTICE](NOTICE). Dependencies, models and datasets retain their [own terms](docs/THIRD_PARTY_INVENTORY.md).

## Features

- **SIFT and ORB engines** — OpenCV implementations, no model training or weight downloads
- **Source-only learned engines** — optional SuperPoint+LightGlue, XFeat, ALIKED+LightGlue, DISK+LightGlue and SIFT+LightGlue; excluded from standard desktop bundles
- **Developer dependency installation** — source builds can install optional runtime packages with live output and a pinned XFeat source/weights cache
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
- **Video tracking** — SIFT/ORB frame-by-frame planar fits with streaming decoding; fit validity is not independent accuracy
- **Camera calibration** — chessboard-based intrinsic calibration
- **Export** — JSON analysis, CSV metrics, comparison CSV, benchmark CSV, HTML report, PNG/JPEG visualization
- **Project save/load** — portable image references, selected engine, matching/estimator choices and core SIFT/ORB/display parameters; older projects remain readable
- **Dark theme** — restrained professional dark UI
- **Threaded analysis** — analysis and long-running jobs use workers with cooperative cancellation and stale-result protection

## Use the desktop app

1. Get the [validation build for your OS and architecture](docs/DESKTOP_DISTRIBUTION.md): Windows x64, macOS Apple Silicon/Intel, or Linux x64. These are unsigned validation artifacts with documented remaining release gates.
2. Launch the installed app or portable bundle. Keep a portable bundle's files together; no Python environment or terminal is needed.
3. Choose or drop a reference and target image, select SIFT or ORB, and press **F5**. Inspect Localization, Feature Matches and the measured details, then save a `.visor` project or export.

An accepted planar fit does not establish correct localization. Ground-truth accuracy requires independent truth; see the [result contract](docs/RESULT_CONTRACT.md) and [measured reliability study](docs/evaluation/RELIABILITY_FINDINGS.md).

## Developer source setup

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

## Optional engines for source developers

The app ships with SIFT and ORB ready to use. Learned engines (SuperPoint+LightGlue, ALIKED+LightGlue, DISK+LightGlue, SIFT+LightGlue, XFeat) require additional packages.

**Option A — one-click from the app:**
Open **Window → Diagnostics**, then click **Install learned engines**. The source app installs dependencies into its active interpreter, prepares the pinned XFeat source/weights cache, and shows live progress. Restart the source app if imports cannot refresh immediately. This developer control is hidden in ordinary desktop bundles.

**Option B — manual install:**
```powershell
python -m pip install -r requirements/learned.txt
python -m visor.model_setup --xfeat
```

> **Developer note:** Learned engines require compatible `torch` and `torchvision`; installing the extra does not guarantee CUDA support. Standard desktop bundles currently include the classical engines. Packaged learned-engine support is a separate tracked improvement.

See [optional runtime setup](docs/OPTIONAL_ENGINES.md) for pins, cache behavior and verification limits, and [result contract](docs/RESULT_CONTRACT.md) for measured timing and estimator semantics.

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
| Learned engines greyed out | Dependencies or pinned XFeat cache absent | Source app: open **Window → Diagnostics** for setup; standard bundles currently include classical engines |
| Install button installs but engines still greyed out | Restart required | Restart the app after installation |
| Icons missing in toolbar | Running from source without install | Run `python -m pip install -e .` |
| Build fails on `generate_icon.py` | Pillow not installed | Run `python -m pip install -e ".[build]"` |

## Project status

See [Implementation Status](docs/IMPLEMENTATION_STATUS.md) and [Project Plan](docs/PROJECT_PLAN.md).
