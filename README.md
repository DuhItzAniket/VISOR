# VISOR

**Visual Object Registration & Analysis** is a Windows desktop application for comparing local image features and estimating planar object location from a reference image and a target image.

The project is being built in milestones. The first release focuses on OpenCV SIFT and ORB, feature matching, and homography-based localization. Homography results apply to planar scenes and are estimates, not general 3D pose measurements.

The desktop app supports choosing or dragging and dropping a reference and target image, then running SIFT or ORB analysis. It displays inliers and outliers, the target localization overlay, a rectified view when geometry succeeds, and measured stage timings. The image canvases support fit, zoom, pan, coordinate readout, and nearby target-keypoint inspection.

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

## Scope

The initial implementation uses OpenCV's existing SIFT and ORB algorithms. It does not train models or download pretrained weights. Learned engines, benchmark tooling, export formats, and packaged Windows installers are later roadmap items.

## Image input

Drag a PNG, JPEG, BMP, TIFF, or WebP file into either image input area, or select it using the corresponding **Choose image…** button. The UI shows the image dimensions and filename after loading. Select SIFT or ORB, adjust parameters under **Analysis Details → Parameters**, then choose **Run analysis** (or press F5). **Compare SIFT / ORB** runs both engines against the same pair. The Benchmark Lab generates controlled rotation/scale, perspective, brightness, contrast, blur, noise, crop, and resolution changes with known image-space transforms.

Analysis runs outside the UI event thread. Match views, localization and detail values come from the selected OpenCV engine. Homography is a planar mapping estimate; its projected corners do not represent general 3D pose.

Use **File → Save Project** to save image paths and current parameters, and **File → Export** for JSON analysis, CSV metrics, comparison/benchmark CSV, or the active visualization. Project files reference images by path and do not embed image data.

## Windows standalone build

On Windows with Python installed, run:

```powershell
.
scripts\build_windows.ps1
```

The first build creates a one-folder PyInstaller distribution at `dist\VISOR\VISOR.exe`. The folder must stay together when distributing. Test the folder on a clean Windows machine before wider release.
