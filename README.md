# VISOR

**Visual Object Registration & Analysis** is a Windows desktop application for comparing local image features and estimating planar object location from a reference image and a target image.

The project is being built in milestones. The first release focuses on OpenCV SIFT and ORB, feature matching, and homography-based localization. Homography results apply to planar scenes and are estimates, not general 3D pose measurements.

The desktop app supports choosing or dragging and dropping a reference and target image, then running SIFT or ORB analysis. It displays feature correspondences, the target localization overlay, a rectified view when geometry succeeds, and measured extraction/matching/geometry timings.

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

Drag a PNG, JPEG, BMP, TIFF, or WebP file into either image input area, or select it using the corresponding **Choose image…** button. The UI shows the image dimensions and filename after loading. Select SIFT or ORB and choose **Run analysis** (or press F5) once both images are loaded.

Analysis runs outside the UI event thread. Match views, localization and detail values come from the selected OpenCV engine. Homography is a planar mapping estimate; its projected corners do not represent general 3D pose.
