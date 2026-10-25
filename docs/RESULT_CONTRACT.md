# Analysis result contract, schema 2

Updated 2026-10-25. Applies to newly generated analyses; existing saved reports are not rewritten.

## Matching

`PairMatchResult` carries the two extracted feature sets, an actual `MatchSet`, and the executed device. The pipeline consumes this typed result. The older `extract_and_match` tuple API remains a compatibility wrapper returning index pairs.

- Classical matches retain descriptor distance and their applicable ratio/filter semantics.
- LightGlue matches carry assignment scores in `confidence`; descriptor `distance` and Lowe `ratio` are null because they were not measured. Assignment scores are not calibrated probabilities of correct localization.
- LightGlue does not expose the number of candidate queries through this adapter; `candidate_pairs` is null. Accepted correspondence count is reported separately.
- XFeat uses mutual nearest-neighbor matching of its float descriptors and reports actual L2 distances, without a fabricated confidence score.
- Match ordering for drawing prefers descriptor distance when present, otherwise assignment score. Existing classical ordering is preserved.
- Unavailable keypoint size, orientation, response, octave or class information is identified by `FeatureSet.keypoint_metadata`. Placeholder storage values must not be displayed as measured statistics.

## Timing

All pipeline timings are wall-clock milliseconds. Each run constructs a fresh engine; `runtime.engine_reused` is false. Initialization includes construction, model loading and completed device transfer. Cache/download state can change initialization cost; this is not a steady-state latency benchmark.

Extraction for each learned image includes tensor preparation, device transfer, inference, and conversion into CPU domain records. Matching includes completed matching and conversion into CPU correspondence records. CUDA work is synchronized around measured stages. The two extraction times and matching time are measured separately; no joint timer is divided or counted twice.

`performance_ms` also reports image decoding, grayscale preprocessing, geometry, visualization/rectification, and total elapsed work. Total includes orchestration overhead, so it need not equal the sum of named stages exactly. Reading/comparing an image pair once can share image-loading cost between individual comparison results; do not add the two comparison totals as a batch timer.

## Geometry provenance

`geometry.provenance` records requested/executed method, model, threshold policy, requested base, effective threshold and ordered attempted thresholds. If insufficient matches prevent a solver call, executed method and effective threshold remain null.

- RANSAC retains the legacy adaptive sequence to preserve classical regression behavior: sorted distinct values of `base`, `max(1, 0.75*base)`, `max(2, 1.5*base)` and `10` px. For a base of 4 px, attempts start at 3 px, then 4, 6 and 10 as needed. The first accepted fit or outside-target result stops the sequence. This policy is explicit; the base must not be described as a strict maximum.
- MAGSAC records the supplied value as its upper-bound policy.
- LMEDS does not use a supplied pixel threshold; effective threshold is null and policy is `not_used`.
- Learned and classical runs honor the same selected robust method. Unsupported classical matching strategies on learned engines raise an actionable error; they are not silently ignored.

A valid fit and its inlier residual are evidence of internal geometric consistency. They do not establish accuracy without independent ground truth.

### Fit diagnostics

Valid fits report convex-hull area of the solver's inlier support divided by each image's pixel-coordinate area, inlier residual median/p95/maximum, projected polygon area and its ratio to target area. Pixel-coordinate area uses `(width-1)*(height-1)`, consistent with projected image corners. Percentiles use NumPy's default linear interpolation. Outliers are excluded from the inlier residual distribution. Metrics requiring an unknown target size remain null; rejected fits do not fabricate diagnostics.

Projected area can exceed 100% of target area for a partially visible reference. These geometric ratios are not confidence percentages and are not clamped into a quality score. Sparse spatial support can leave the rest of the reference weakly constrained even when fit residual is small. Inspecting a target keypoint lists its accepted correspondence(s), solver inlier/outlier membership and real descriptor distance or assignment score when available.

## Export migration

Analysis JSON schema is now 2. Existing fields remain, with nullable learned candidate counts/thresholds, added correspondence distance/score records, runtime/timing metadata, and geometry provenance. CSV adds measured stage/device/matcher/estimator fields. Consumers must handle null/empty values as unavailable, not zero.

The `.visor` project format is now 2 and preserves matching strategy and robust estimator in addition to core/display settings. Image paths are saved relative to the project when possible, allowing the project and its image directory to move together; images are not embedded. Paths across Windows drives remain absolute. Version 1 is still readable and defaults to the original ratio matcher/RANSAC semantics. Unavailable project engines are reported rather than silently replaced. Loading restores overlay settings as well as matching/geometry controls.

Nondefault symmetric-ratio matching now measures its complete forward/reverse operation once; nested stage durations must not be added again. Cross-check has no numeric filter threshold, so it reports null. Conflicting matching-strategy flags are rejected instead of being resolved by hidden precedence.
