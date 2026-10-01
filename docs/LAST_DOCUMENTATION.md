# VISOR — Final Deep Handoff Documentation

## 1. Project identity

VISOR is a Windows desktop image registration and localization tool built in Python with PySide6, OpenCV, NumPy, and optional learned feature matching support.

The app is designed to:
- load a reference image and a target image,
- detect and match local features,
- estimate planar geometry with homography,
- visualize matches and localization,
- compare classical algorithms (SIFT and ORB),
- run a benchmark suite across synthetic challenge conditions,
- export analysis data for downstream evaluation.

The project is not a generic deep-learning training repo. It is a desktop analysis application with classical vision as the stable foundation and optional learned matchers layered on top when dependencies are available.

---

## 2. Core purpose

The product goal is to provide a practical inspection and evaluation workflow for:
- image registration,
- planar localization,
- feature matching quality analysis,
- benchmark comparisons between classical methods,
- later extension toward learned feature methods if the environment supports them.

This is best understood as a tool for validating whether two images are aligned under a planar assumption and whether the chosen feature engine is good enough for that task.

---

## 3. Verified runtime environment

The working project environment is the repo-local `.venv` at:

- `c:\Users\Luikz\Downloads\VISOR\.venv`

The project has been verified with the active workspace Python interpreter and the app has passed pytest validation.

Verified facts from runtime checks:
- pytest passed: `33 passed in 20.33s`
- main branch in Git is active
- remote is configured to GitHub repo: `https://github.com/DuhItzAniket/VISOR.git`
- PyInstaller successfully built the Windows app in the dist folder

The most important runtime rule is this:

- do not expect a frozen PyInstaller EXE to host heavy TorchScript-based learned engines reliably,
- use the repo-local virtual environment for learned matchers,
- keep the EXE as a packaged launch/distribution artifact, not as the full runtime environment for LightGlue/XFeat/ALIKED.

---

## 4. Project structure

Repository layout (important only to understand where the logic lives):

- `src/visor/__main__.py` — application entry point
- `src/visor/app.py` — app bootstrap / app-level initialization
- `src/visor/benchmark.py` — benchmark generation and reporting
- `src/visor/engines.py` — classical SIFT / ORB engine wrappers
- `src/visor/geometry.py` — homography, geometry, projective calculations
- `src/visor/learned_engines.py` — optional learned feature engines and availability guards
- `src/visor/matching.py` — feature matching logic
- `src/visor/models.py` — typed records and enums for analysis results
- `src/visor/pipeline.py` — orchestration of analysis, comparison, benchmark runs
- `src/visor/visualization.py` — rendered match/localization images
- `src/visor/exporting.py` — JSON / CSV / project serialization
- `src/visor/ui/main_window.py` — main Qt window and workflow controller
- `src/visor/ui/widgets/image_drop.py` — drag/drop image panel
- `src/visor/ui/widgets/image_canvas.py` — image display panel
- `src/visor/ui/widgets/details_panel.py` — result details dock
- `tests/` — regression and behavior tests
- `scripts/` — build and dataset utilities
- `docs/` — planning, implementation status, and handoff docs
- `Sample/` — local area for reference/target inputs and dataset experimentation

---

## 5. Application architecture

The architecture follows a clean layered pattern:

1. UI layer
   - PySide6 window
   - image panels
   - toolbar controls
   - result tabs
   - details dock
   - engine console

2. Task layer
   - `AnalysisWorker`
   - `ComparisonWorker`
   - `BenchmarkWorker`
   - all expensive CV work is kept off the UI thread

3. Processing layer
   - `pipeline.analyze()`
   - `pipeline.compare_engines()`
   - `benchmark.run_benchmark()`

4. Core vision layer
   - engines
   - matching
   - geometry
   - visualization
   - exporting

5. Data model layer
   - `AnalysisResult`, `ComparisonResult`, `BenchmarkReport`
   - typed config objects for SIFT / ORB and optional learned engines

The design rule from the repo is important:

- CV logic is kept independent from Qt widgets
- typed Python data objects are preferred over ad hoc UI globals
- heavy image processing stays out of the UI thread
- planar assumptions are labeled as estimates and not generic 3D pose claims

---

## 6. Classical engine implementation

### SIFT
- OpenCV implementation via `engines.py`
- stable and reliable baseline
- good when texture is present and feature distribution is rich

### ORB
- OpenCV implementation via `engines.py`
- fast feature extraction and matching
- often competitive for binary descriptor scenes

The project works strongly around the idea of comparing both classical engines on the same image pair and summarizing the result in a structured details view.

---

## 7. Learned engine design and constraints

The repo includes support for:
- `SuperPoint+LightGlue`
- `XFeat`
- `ALIKED+LightGlue`

These are treated as optional engines.

### Why they are optional
They depend on packages such as:
- `torch`
- `lightglue`
- optionally `xfeat`

The direct PyInstaller packaging path is unstable for TorchScript-backed modules because the frozen app cannot reliably load the necessary runtime modules in a safe packaged environment.

### Current working strategy
The app now exposes an explicit UI flow:
- if learned engine dependencies are missing, the toolbar shows an install button,
- the app can create or reuse the repo-local `.venv`,
- it installs the required dependencies there,
- the user restarts the app in that environment.

This is the correct professional solution for this project.

### Important rule for later models
Do not attempt to force `lightglue` or `xfeat` into the PyInstaller EXE as a hidden dependency package path. That is the root architectural issue that caused the packaging problems.

---

## 8. Main application behavior

### Workflow
1. Load reference image
2. Load target image
3. Select engine
4. Tune matching/geometry parameters
5. Run analysis or compare engines
6. Inspect results in tabs: matches, localization, warped output
7. Export or save the project

### UI features
- drag-and-drop image input
- compact side-by-side image panels
- recent pairs panel
- engine console for backend status events
- overlay controls for rainbow feature color and line thickness
- screenshot-quality visual results for matches and localization

### Result interpretation
The app is a planar-scene geometry estimator. It can show:
- homography matrix quality,
- inlier/outlier ratio,
- center projection,
- projected polygon corners,
- visual matching quality.

This is not a full 3D pose system and should not be described as one.

---

## 9. Geometry and localization assumptions

The geometry layer estimates a homography from feature correspondences. That is only valid for planar scenes or scenes that are locally planar under the image-view assumption.

Translation to user-facing language should always say:
- planar assumption,
- image-space estimate,
- estimated homography,
- projected localization under planarity,
- not a true world-coordinate 3D pose.

This distinction is important for credibility and correctness.

---

## 10. Benchmarking system

The benchmark lab generates controlled synthetic transformations from a reference image. It measures both classical engines against known conditions such as:
- baseline
- rotation + scale
- perspective transform
- brightness variation
- contrast change
- blur
- noise
- crop
- resolution reduction

It produces a report with rows per engine and scenario. The report includes metrics like:
- good matches,
- inlier count,
- inlier ratio,
- valid geometry flag,
- corner RMSE,
- runtime in milliseconds.

This is the main internal validation utility for comparing engine robustness.

---

## 11. Exporting and project persistence

The repo supports:
- JSON export of analysis results,
- CSV export of metrics,
- comparison CSV for SIFT vs ORB,
- benchmark CSV,
- visualization export,
- project save/load in `.visor` format.

The application stores image paths and parameters so that a user can reopen a previous analysis session.

---

## 12. Build and packaging notes

### Source app launch
Use the repo-local venv:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip setuptools wheel
python -m pip install -e .
python -m visor
```

### Windows build script
The repo contains:
- `scripts/build_windows.ps1`
- `rebuild_visior_app.bat`

The build command is the authoritative Windows packaging flow for the source app.

### Important build decision
The build was corrected to avoid stale `VISOR.spec` corruption and unnecessary Torch-heavy packaging. The packaging config deliberately does not force the whole `torch` / `lightglue` stack into the frozen EXE because that breaks the intended architecture.

The correct distribution model is:
- source app + base dependencies in repo venv
- optional learned-engine dependencies installed there
- packaged EXE for distribution of the UI and core classical processing

---

## 13. Known issues and constraints

### 1. PyInstaller + TorchScript compatibility
This remains the biggest packaging constraint.
- a frozen app will complain about TorchScript-backed modules,
- `PyInstaller` is not the right place to force a full learned-feature runtime,
- installer flow must use repo-local venv for those dependencies.

### 2. XFeat availability
This package is not guaranteed to be available in the current environment and may require its own install path. The app marks it as unavailable until the dependency is installed.

### 3. Learned-engine quality is environment-dependent
The quality of learned engines depends on:
- GPU presence,
- driver support,
- installed package versions,
- dataset quality.

The app does not claim perfect model performance; it provides a practical validation environment.

### 4. Dataset training remains outside the app
The repo is not a full deep-learning training project. It is a desktop app for image registration and matching. Any serious large-scale training should live in a separate GPU-focused project with a proper dataset pipeline.

---

## 14. Testing status

The project has an active test suite under `tests/`.

Verified test command:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Verified result:

- `33 passed in 20.33s`

This is the most important evidence for the current app state. Any future model working on the repo should run these tests before claiming compatibility.

---

## 15. Git workflow and branch status

The repo is being kept on `main`, not a separate feature branch, as requested.

The project has a remote configured to GitHub:

- `origin https://github.com/DuhItzAniket/VISOR.git`

The final verified push succeeded on main. The workflow should remain:
- continue work on main,
- validate with pytest,
- rebuild when packaging changes are made,
- commit and push verified work only.

This keeps the project handoff clean and avoids branch drift.

---

## 16. What was fixed in the final working state

The final project state includes the following important work:

- fixed stale or corrupted build config issues in the packaged app path,
- removed bad packaging assumptions that attempted to bundle the full learned-engine stack into the frozen EXE,
- added an install button flow for missing learned engines in the GUI,
- implemented repo-local venv bootstrap logic,
- kept the workflow compact and professional,
- added documentation for install/build workflow and dataset strategy,
- preserved the classical engine pipeline as the stable baseline,
- preserved the app’s “main branch” Git flow and push discipline.

---

## 17. What to do next if a new model takes over

The next model should follow this order:

1. open the repo,
2. activate `.venv`,
3. run pytest,
4. inspect main app logic in `src/visor/ui/main_window.py`,
5. understand the pipeline in `src/visor/pipeline.py`,
6. understand the optional learned-engine guard in `src/visor/learned_engines.py`,
7. build only after confirming source code is stable,
8. never assume the EXE is a full learned-engine runtime,
9. keep all large data and training artifacts out of Git,
10. prefer repo-local environment workflows for GPU / learned-engine experimentation.

---

## 18. Final summary

VISOR is a mature desktop image registration and localization tool built around classical vision, with optional learned-engine capability handled in a disciplined repo-local environment. The working architecture is sound, validation is green, and the packaging strategy is now aligned with the actual runtime constraints.

The project is not trying to be a general-purpose AI model training platform. It is a compact and professional desktop tool for visual matching, geometry estimation, and benchmarking with a clean installation and handoff story.

This is the state you should carry forward.
