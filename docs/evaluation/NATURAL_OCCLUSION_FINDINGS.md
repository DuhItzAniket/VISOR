# Natural-image occlusion findings

Both SIFT and ORB stayed within 3 px mean corner error on three of eight unmasked HPatches pairs and two of eight with either half masked. The four scenes were unused in VISOR's earlier natural-image studies. The clean evaluator revision was `bc999da`, with OpenCV 4.11.0.86, two CPU threads, OpenCL disabled and no learned model runtime. All 48 attempts completed with zero runtime or annotation errors. [Frozen protocol](NATURAL_OCCLUSION_PROTOCOL.md) · [Raw report](natural-occlusion-20261121.json.gz)

| Engine | Target | Valid fits | Mean corner error ≤3 px | Accepted fits above 5 px |
|---|---|---:|---:|---:|
| SIFT | Unmasked | 7/8 | 3/8 | 2/8 |
| SIFT | Left half masked | 7/8 | 2/8 | 4/8 |
| SIFT | Right half masked | 7/8 | 2/8 | 4/8 |
| ORB | Unmasked | 6/8 | 3/8 | 3/8 |
| ORB | Left half masked | 6/8 | 2/8 | 4/8 |
| ORB | Right half masked | 5/8 | 2/8 | 2/8 |

For each engine and mask, two of the three accurate unmasked pairs stayed within 3 px and one fell outside that threshold. None of the five other pairs crossed into the 3 px band under either mask. An ORB fit on `v_azzola/1-6/left_masked` had five inliers and a 0.56 px mean reprojection residual while missing the annotated image corners by 449.25 px on average. On the unmasked target it already missed by 43.39 px. The low residual describes the fit on those five points. The corner error describes the full-image alignment.

The masks cover half the target pixels, and the whole-image corner metric can measure extrapolation into the masked area. The eight mappings share four scenes. This experiment contains no unrelated-scene negatives and reports no engine ranking, general reliability estimate or deployment threshold. Desktop defaults and solver behavior are unchanged.

To reproduce, obtain the five input files per scene described in the protocol. Verify their SHA-256 values against `manifest.source_files_sha256` in the report. Run the preparation script and call the evaluator with two OpenCV threads, OpenCL disabled, `device="cpu"`, `feature_budget=1500`, `repetitions=1` and `warmup=0`. The report embeds the effective settings, manifest and input hashes.

Raw compressed SHA-256 `b3ada24ab0792d87f901d2d822360e09fecb2c8d6c08e8c88266976dda3cdf92`.
