# VISOR research and engineering review

Review date: 2026-10-19. Audited starting commit: `40e68de` (v0.2.0).

## Drag-and-drop action review — 2026-10-25

The input widgets previously accepted the drag source's proposed action. VISOR opens and references the original path; it does not move a file. Qt permits overriding the proposed action with an allowed action using `setDropAction` followed by `accept`. Windows documents that a move effect tells the source to remove its data. Therefore image inputs explicitly choose Copy during enter/move/drop, reject sources that only offer Move, and reject unreadable drops instead of reporting an accepted operation. This is a preventative contract correction, not an observed loss of a source file. [Qt drop actions](https://doc.qt.io/qt-6/qdropevent.html#setDropAction), [Windows drop-effect definitions](https://learn.microsoft.com/en-us/windows/win32/com/dropeffect-constants).

Qt event-dispatch tests cover both roles, Shift-proposed Move overridden by Copy, Unicode/spaced uppercase image paths, preserved source bytes, rejected remote/non-image payloads and unreadable-image recovery. The packaged workflow check also dispatches URL drop events. These are separate from real native Explorer interaction: the Windows automation helper rejects drag endpoints outside its source window, so it cannot currently complete that cross-window review.

## Recommendation

Develop VISOR as a trustworthy registration and evaluation workbench. The immediate return comes from honest geometry, measured runtime, reproducible experiments, and clear failure explanations. Additional engine names and training do not address the current reliability gaps.

This review combines local source inspection, attempted package construction, baseline checks, and upstream documentation/source. Upstream performance figures are not VISOR measurements. A dependency being discoverable does not establish that its model loads or its runtime works.

## Findings in the current source

| Priority | Evidence | Consequence | Proposed response |
|---|---|---|---|
| P0 | `geometry.py` translates the means of the first N keypoints after failed fitting, ignoring match indices; returns all-inlier/zero-error results | A failed registration can look perfect | Remove fabricated fallback; return explicit failure; test adversarial cases |
| P0 | `geometry_robust.py` has separate validation, does not use `target_size`, and silently falls back to adaptive RANSAC | Different estimators can disagree on what constitutes a valid result and conceal method changes | Shared validator, same projection policy, explicit selected-method failure |
| P0 | `pyproject.toml` specifies `setuptools.backends.legacy:build`; wheel attempt raises `Cannot import 'setuptools.backends.legacy'` | Fresh install/build fails despite an existing environment working | Restore documented backend and smoke-build a wheel |
| P1 | Classical RANSAC tries sorted thresholds including 10 px and can use 3 px when the UI says 4 px | User settings do not describe the actual fit | Make threshold policy explicit and record effective estimator/threshold before changing default behavior |
| P1 | Learned engines divide extraction+matching time equally between images; pipeline counts this again as matching time and uses placeholder zero distances | Engine comparisons are not stage-accurate | Separate measured extraction/matching stages; synchronize CUDA measurements; retain model confidence and mark unavailable distances |
| P1 | XFeat code imports `xfeat.Extractor`; upstream documents `modules.xfeat.XFeat` / `detectAndCompute`; local matcher is one-way NN | Install guidance and adapter are not established against upstream behavior | Choose a pinned upstream revision, implement adapter against documented API, use mutual matching and runtime smoke checks |
| P1 | `_analyze_learned` labels XFeat matches LightGlue, ignores selected robust estimator and some configuration fields | Reports can describe an algorithm that did not run | Structured extractor/matcher/estimator metadata shared by all paths |
| P1 | `batch.py` stores fitted inlier residual as `localization_error_px` without ground truth | A fit residual is presented as external accuracy | Separate reprojection residual and known-transform corner error in data/UI/exports |
| P1 | `evaluate_pair_manifest.py` contains a machine-specific repo path; saved sample summaries have no complete provenance | Results cannot be independently reproduced | Portable CLI, input hashes, versions, device, configuration, repetitions and raw results |
| P2 | Registry contains only SIFT/ORB; pipeline still dispatches manually; UI main window is approximately 1,700 lines | New engine additions repeat work and can diverge | Capability registry and job controller, incremental extraction of UI responsibilities |
| P2 | Status, handoff, architecture, and README disagree about environments, available engines, and verification | Maintainers cannot identify the current source of truth | Canonical status and task ledger; clearly label historical documents |

## Research: what to adopt and why

### 1. Robust estimation and localization quality

OpenCV USAC exposes sampling, scoring, degeneracy checking, and local optimization separately. Its documentation describes MAGSAC++ and notes that an approximate threshold still matters for termination; LMEDS has a different assumption about the inlier fraction. Thus simply exposing three method names is insufficient: method, threshold, input quality, and validation must be recorded. [OpenCV USAC](https://docs.opencv.org/4.x/de/d3e/tutorial_usac.html).

Use a shared validation layer for every estimator: finite invertible matrix, a correctly sized inlier mask, sufficient support, finite residuals, no projective horizon crossing inside the reference, a convex nondegenerate projected polygon, and actual polygon overlap with the target. Project the reference center through H; the mean of projected corners is generally different under perspective. Later add inlier coverage and symmetric transfer error as diagnostics, calibrated on evaluation data rather than assigned arbitrary universal pass thresholds.

Keep `valid` scoped to a supported geometric fit. Do not call it a calibrated detection probability. Add negative pairs and repeated-texture cases to measure false localization, not just success on transformed copies.

### 2. Learned features: accurate adapters before more models

LightGlue officially pairs with SuperPoint, DISK, ALIKED and SIFT. It exposes separate feature extraction and matching, match index pairs, and configurable confidence/adaptive computation. Its README also distinguishes licenses for code, models, and extractors. This supports a common result contract but does not justify describing binary ORB matching as LightGlue. [LightGlue](https://github.com/cvg/LightGlue).

XFeat's official README uses `modules.xfeat.XFeat`, `detectAndCompute`, or an explicit Torch Hub path. Its source matcher applies mutual nearest-neighbor selection with a cosine-similarity threshold. VISOR's `xfeat.Extractor` import and one-way NumPy matcher are therefore an adapter mismatch pending an actual pinned integration. Do not resolve this by silently downloading and executing a mutable Hub repository. [XFeat usage](https://github.com/verlab/accelerated_features#inference), [upstream matcher](https://github.com/verlab/accelerated_features/blob/main/modules/xfeat.py).

Record requested versus actual device, model initialization/weight loading separately from warm analysis time, selected model revision, matching confidence, preprocessing resolution, and keypoint budget. Introduce a small measured engine cache only after profiling; bound memory and key it by model/configuration/device. Keep the source-runtime and packaged-runtime support policies explicit; the existing packaged-engine guard is a VISOR policy, not evidence of a universal PyInstaller impossibility.

PyTorch documents asynchronous CUDA execution and synchronization/events for accurate timing. Use synchronized wall-clock measurements for end-to-end stage latency or CUDA events for device execution, label the convention, and warm up separately. A host timer ending immediately after an asynchronous model call does not measure completed inference. [CUDA semantics](https://docs.pytorch.org/docs/main/notes/cuda.html), [CUDA events](https://docs.pytorch.org/docs/stable/generated/torch.cuda.streams.Event.html).

### 3. Evaluation that answers product questions

HPatches is a relevant planar descriptor/registration benchmark. Glue Factory evaluates homography error and matching precision on HPatches, and uses separate datasets and metrics for relative pose. VISOR should not equate a homography fit on four matches with accurate localization on varied real scenes. [HPatches project](https://hpatches.github.io/), [Glue Factory evaluation](https://github.com/cvg/glue-factory#evaluation).

Maintain three evaluation tiers:

1. Deterministic synthetic tests with known H and controlled noise/outliers for mathematical correctness.
2. HPatches image sequences with ground-truth homographies, split by condition, for planar accuracy. Verify actual sequence images and transforms exist; the checked-in HPatches scaffolding is not the dataset.
3. A small user-relevant dataset with annotations, unrelated negative pairs, occlusion, low texture, blur, and resolution changes. Keep tuning scenes separate from reporting scenes.

Report fit rate, false-localization rate, match precision when truth exists, mean corner distance with a documented convention, accuracy at chosen pixel thresholds, and median/p95 latency over repeated warm runs. Synthetic corner RMSE and mean corner distance are distinct metrics; do not reuse names or claim direct equivalence to published scores. Include all failed pairs in denominators. No ground truth means localization error is unavailable, even if reprojection residual is small.

### 4. Desktop architecture and operational reliability

Qt documents cooperative interruption and requires code to act on a cancellation request. Preserve current safe-boundary cancellation, then make engine initialization, multi-pair progress, stale-result rejection, and shutdown explicit in a job controller. Include a generation ID with results so image changes cannot display old results as current. [Qt QThread](https://doc.qt.io/qtforpython-6/PySide6/QtCore/QThread.html#PySide6.QtCore.QThread.requestInterruption).

Setuptools documents `setuptools.build_meta` as the build backend. An installed editable environment cannot substitute for validating a fresh wheel. Add offline core tests, wheel construction/import, and a separate optional learned-runtime validation lane. Preserve supported dependency ranges but record exact versions in validation reports. [Setuptools build backend](https://setuptools.pypa.io/en/latest/build_meta.html).

## Deliberate deferrals

- No model training until adapters, truth-backed evaluation, and reproducible baselines are reliable.
- No dense matcher or ONNX runtime addition in the first improvement phase. Revisit only for a measured accuracy/deployment gap.
- No blanket MAGSAC default change based on upstream benchmarks. Compare it on VISOR's held-out pairs first.
- No installer/release claim based on a process merely staying alive. Validate image loading, analysis, export, and shutdown in the built app.

## Desktop delivery requirement added during review

The user requires standalone Windows/macOS/Linux applications without a Python setup step. Qt remains a suitable desktop UI foundation. PyInstaller explicitly bundles the runtime for end users, and requires builds on each target OS; this is packaging the current implementation, not rewriting it in C++. Add native build jobs and installer formats, then verify each artifact. Platform configuration alone is not platform support. [PyInstaller](https://pyinstaller.org/en/stable/operating-mode.html), [Qt deployment](https://doc.qt.io/qtforpython-6/deployment/index.html). See I13 and `DESKTOP_DISTRIBUTION.md`.

## Evidence limits

### Native dependency follow-up — 2026-10-26

The actual Linux frozen inventory at a6fc4fd contains OpenCV Qt5 libraries in addition to PySide's Qt6. VISOR does not use HighGUI functions. Upstream recommends a headless wheel when another toolkit supplies the interface, and installing exactly one cv2 provider. I16 evaluates opencv-contrib-python-headless at the same 4.11.0.86 desktop pin using retained goldens and native image/video checks. This is a packaging change, not a proposed vision algorithm change or a native-license conclusion. [OpenCV wheel guidance](https://github.com/opencv/opencv-python#installation-and-usage).

The pinned LightGlue metadata requests opencv-python. Source setup therefore supplies its other inference dependencies explicitly and installs the adapter with --no-deps to reuse VISOR's headless contrib cv2. The upstream metadata still reports its package-name requirement; actual inference must be verified separately. [Pinned upstream metadata](https://github.com/cvg/LightGlue/blob/eb42fee2d71449efb0aa5c10549752b5d75384d8/pyproject.toml).

### Follow-up integration review — 2026-10-25

The XFeat pin exposes detectAndCompute with keypoints, scores and 64-D descriptors. Its Hub entry fetches weights through a moving main URL, so VISOR now caches the weights committed at the same fixed source revision instead. The adapter initializes the pinned inference state on the requested device to avoid upstream's unconditional CUDA preference. [Pinned inference source](https://github.com/verlab/accelerated_features/blob/e92685f57f8318b18725c5c8c0bd28c7fe188d9a/modules/xfeat.py), [Hub entry](https://github.com/verlab/accelerated_features/blob/e92685f57f8318b18725c5c8c0bd28c7fe188d9a/hubconf.py).

LightGlue returns assignment scores independently of descriptor distances; VISOR preserves those scores and measures the actual matching stage. Its reviewed default match filter is 0.1, now passed explicitly by the adapter. Completed CUDA stage timing requires synchronization. [Pinned LightGlue source](https://github.com/cvg/LightGlue/blob/eb42fee2d71449efb0aa5c10549752b5d75384d8/lightglue/lightglue.py), [PyTorch synchronization](https://docs.pytorch.org/docs/stable/generated/torch.cuda.synchronize.html). See RESULT_CONTRACT.md and OPTIONAL_ENGINES.md for scope and measured local evidence.

Local static inspection establishes the above code defects. It does not prove an engine is operational on every machine, nor does this review establish a best-performing engine. Tests and package build outcomes are maintained in `IMPLEMENTATION_STATUS.md`; the execution sequence and acceptance criteria are in `IMPROVEMENT_PLAN.md`.

The pinned wheel build 86 explicitly notes that macOS retains Cocoa even in headless mode; its switches disable Qt/GTK/Win32UI. Both native Mac jobs reproduced COCOA. Record the actual backend and permit that exact Darwin/OpenCV 4.11.0 exception, rather than claim universal GUI backend NONE. [Pinned wheel build source](https://github.com/opencv/opencv-python/blob/255564a37c4a23275485e827abbe19031347d458/setup.py).
