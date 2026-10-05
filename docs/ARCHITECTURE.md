# Architecture

## Layers

```
┌─────────────────────────────────────────────────────────┐
│  PySide6 UI                                             │
│  main_window · image_canvas · image_drop · details_panel│
├─────────────────────────────────────────────────────────┤
│  Qt Worker threads                                      │
│  AnalysisWorker · ComparisonWorker · BenchmarkWorker    │
├─────────────────────────────────────────────────────────┤
│  Pipeline                                               │
│  pipeline.analyze · compare_engines                     │
├──────────────┬──────────────┬──────────────┬────────────┤
│  Engines     │  Matching    │  Geometry    │  Viz       │
│  SIFT · ORB  │  BF+ratio    │  RANSAC H    │  overlays  │
├──────────────┴──────────────┴──────────────┴────────────┤
│  Domain models  (models.py)                             │
│  KeypointInfo · FeatureSet · MatchSet · GeometryResult  │
│  AnalysisResult · ComparisonResult · PerformanceMetrics │
├─────────────────────────────────────────────────────────┤
│  Infrastructure                                         │
│  exporting · benchmark · app (logging/startup)          │
└─────────────────────────────────────────────────────────┘
```

## Module responsibilities

| Module | Responsibility |
|---|---|
| `visor.models` | Typed frozen dataclasses shared by all layers. No OpenCV objects escape this boundary except through `KeypointInfo`. |
| `visor.engines` | `SIFTFeatureEngine` and `ORBFeatureEngine` wrap `cv2.SIFT_create` / `cv2.ORB_create`, convert `cv2.KeyPoint` lists to `KeypointInfo` tuples, and return `FeatureSet`. |
| `visor.matching` | `match_features` selects `NORM_L2`, `NORM_HAMMING`, or `NORM_HAMMING2` based on engine name and descriptor distance field, runs KNN matching, applies Lowe ratio filter, and returns `MatchSet`. |
| `visor.geometry` | `estimate_geometry` runs RANSAC homography (or affine variants), validates the result, projects reference corners, computes inlier statistics, and returns `GeometryResult`. |
| `visor.pipeline` | `analyze` and `analyze_images` coordinate image loading, grayscale conversion, extraction, matching, geometry, and visualization into a single `AnalysisResult`. `compare_engines` runs both engines on the same decoded images. |
| `visor.visualization` | `render_match_canvas` and `render_localization` draw overlays onto NumPy arrays using OpenCV drawing primitives. They consume `AnalysisSettings` toggles without rerunning analysis. |
| `visor.benchmark` | `run_benchmark` generates nine deterministic synthetic transformations from a reference image, runs selected engines, and computes corner RMSE against known ground-truth homographies. |
| `visor.exporting` | JSON analysis documents, CSV metrics, comparison/benchmark CSV, PNG/JPEG visualization export, and `.visor` project session save/load. |
| `visor.app` | Application entry point, logging configuration, `QApplication` setup, and window icon. |
| `visor.ui.main_window` | `QMainWindow` with menu bar, toolbar, input/config panel, tabbed result workspace, and Analysis Details dock. Owns all Qt workers and result state. |
| `visor.ui.widgets.image_canvas` | Zoomable `QGraphicsView` with scroll-hand drag, wheel zoom, cursor coordinate signal, and click-to-inspect signal. |
| `visor.ui.widgets.image_drop` | `QFrame` accepting drag-and-drop and native file picker for image files; emits `image_changed(role, path)`. |
| `visor.ui.widgets.details_panel` | `AnalysisDetailsPanel` renders structured engine-specific results in tab or tree view mode. Sections: Overview, Engine (SIFT/ORB), Geometry, Performance, Selected Keypoints. |

## Data flow

```
reference path + target path + engine name + settings
    │
    ▼
pipeline.analyze_images
    ├── SIFTFeatureEngine.extract(gray)  →  FeatureSet
    ├── ORBFeatureEngine.extract(gray)   →  FeatureSet
    ├── match_features(ref, tgt, engine) →  MatchSet
    ├── estimate_homography(...)         →  GeometryResult
    ├── render_match_canvas(...)         →  BGR ndarray
    └── render_localization(...)         →  BGR ndarray
    │
    ▼
AnalysisResult  (frozen dataclass)
    │
    ├── MainWindow._show_result()
    │       ├── ImageCanvas.set_image()  (matches, localization, warped)
    │       └── AnalysisDetailsPanel.populate()
    │
    └── exporting.*  (JSON / CSV / visualization)
```

## Threading model

All OpenCV work runs on a `QThread` subclass (`AnalysisWorker`, `ComparisonWorker`, `BenchmarkWorker`). Results are emitted via Qt signals back to the main thread. A `threading.Event` cancel token is checked at safe pipeline boundaries between stages.

## Geometry scope

Homography is a planar mapping. Projected corners, center, and derived rotation/scale are image-space estimates. The application labels them as estimates and does not claim general 3D pose recovery. The geometry layer is designed to accept future `Essential Matrix` and `PnP` solvers without changing the UI.

## Extension model

New feature engines implement the `FeatureEngine` protocol:

```python
class FeatureEngine(Protocol):
    name: str
    def extract(self, gray: NDArray[np.uint8]) -> FeatureSet: ...
```

New matchers are added to `matching.match_features` behind the engine name dispatch. New geometry solvers are added to `geometry.estimate_geometry` behind the `model` parameter. The UI and pipeline require no changes for new classical engines.

Learned engines (SuperPoint, LightGlue, XFeat, ALIKED) are future additions that follow the same `FeatureEngine` protocol.
