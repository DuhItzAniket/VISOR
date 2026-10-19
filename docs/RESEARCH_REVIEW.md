# VISOR research and engineering review

Review date: 2026-10-19. Audited starting commit: `40e68de` (v0.2.0).

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

## Evidence limits

Local static inspection establishes the above code defects. It does not prove an engine is operational on every machine, nor does this review establish a best-performing engine. Tests and package build outcomes are maintained in `IMPLEMENTATION_STATUS.md`; the execution sequence and acceptance criteria are in `IMPROVEMENT_PLAN.md`.
