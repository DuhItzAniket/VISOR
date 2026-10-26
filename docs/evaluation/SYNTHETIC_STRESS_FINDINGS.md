# Synthetic stress findings — 2026-10-26

Protocol and generator were pushed at `c79b950` before engine measurement. The evaluator report records that exact clean source revision, CPU execution, no installed Torch/LightGlue and all requested settings. [Frozen protocol](SYNTHETIC_STRESS_PROTOCOL.md), [complete raw report](synthetic-stress-20261026.json.gz). The compressed report SHA256 is `6ab5f37ef99a2b10d4f67b523c47a9ae01d46e04de8334983db97efbff8c3a1e`.

The three fixed seeds generate 21 development pairs. SIFT/ORB use budget 1500, ratio 0.75, legacy adaptive RANSAC base 4 px and seed 0. All 126 measured attempts and 42 warmups are retained. There were no runtime or annotation errors. Every completed analysis records actual CPU device. Timings are raw execution evidence while other work was running, not a controlled speed comparison.

| Engine | Truth-backed attempts | Valid positive fits | Mean corner error ≤1 px | ≤3 px | ≤5 px | Valid positives >5 px | Labeled negatives accepted |
|---|---:|---:|---:|---:|---:|---:|---:|
| SIFT | 36 | 18 | 18 | 18 | 18 | 0 | 3/27 |
| ORB | 36 | 18 | 12 | 18 | 18 | 0 | 0/27 |

Accuracy denominators include all 36 truth-backed attempts per engine, including failed fits. The three accepted SIFT negative attempts are repetitions of **one pair**, not three independent scenes. Repetitions reuse pixels and all seeds share construction rules; these counts do not establish an engine ranking or a general false-acceptance rate.

| Condition | SIFT valid fits | ORB valid fits | Accuracy/negative interpretation |
|---|---:|---:|---|
| Textured positive | 9/9 | 9/9 | All within 3 px mean corner error |
| Half-occluded positive | 9/9 | 9/9 | All within 3 px mean corner error |
| Repeated-tile positive | 0/9 | 0/9 | No fit; all nine remain in accuracy denominators |
| Smooth low-texture positive | 0/9 | 0/9 | No fit; all nine remain in accuracy denominators |
| Independent seeded scene | 3/9 | 0/9 | Labeled-negative acceptance, not truth-backed localization accuracy |
| Independent pixel noise | 0/9 | 0/9 | No negative fit in this constructed sample |
| Uniform image | 0/9 | 0/9 | No negative fit in this constructed sample |

SIFT accepted `1302/independent-scene` on every measured repetition with nine solver inliers, mean inlier residual about **0.327 px**, p95 residual **0.849 px**, and reference support hull fraction **0.273**. There is no supplied ground-truth transform for that negative, so corner accuracy remains unavailable. Small fit residual and a broad support hull do not prove the complete reference scene is present.

The repeated-tile and smooth cases are deliberately difficult constructions. Their failed fits must remain failures; generating a transform from unverified correspondences would conceal this result. Repeated appearance may allow ambiguous visual alignments, and this experiment does not establish unique physical pose. The half-occlusion success covers only one fixed synthetic masking rule and cannot establish natural-occlusion robustness.

**Decision:** preserve all results and keep desktop policies/goldens unchanged. No threshold is selected from this probe. The earlier [I15 reporting findings](RELIABILITY_FINDINGS.md) remain unchanged, including their failed policy-generalization result. Next reliability work needs independently annotated natural object/background negatives and diverse occlusion/repeated-texture scenes with source/annotation provenance, followed by a separately frozen reporting plan. More fitted transforms alone are not a useful acceptance target.

To inspect or reproduce the evidence, follow [EVALUATION.md](../EVALUATION.md). Generated images remain under ignored build storage; their hashes, complete manifest, construction truth and generator/protocol hashes are embedded in the raw report. The report can be read with standard gzip/JSON tools and contains per-condition summaries plus every correspondence-level analysis, warmup and failure row.
