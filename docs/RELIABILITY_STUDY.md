# Registration reliability study protocol

Frozen selection and analysis plan, 2026-10-25. This advances I15 without changing the classical estimator or rewriting its golden fixtures. A valid fitted transform remains distinct from an accurate localization. The original published i_ajuntament/v_abstract reporting results remain unchanged and are excluded from policy development.

## Selection before measurement

Inspect only the HPatches full-image ZIP directory. For each i_/v_ condition, sort complete sequences alphabetically, exclude i_ajuntament/v_abstract, and retain sequences with at most 64 MiB uncompressed across images 1–6 and matrices H_1_2..6. The first two eligible sequences per condition are development; the next is reserved reporting. This selects:

| Split | Illumination | Viewpoint |
|---|---|---|
| Development | i_autannes, i_bologna | v_adam, v_apprentices |
| Reserved reporting | i_books | v_artisans |

No extraction, matching, fit diagnostics or truth-error results were inspected to select these scenes. Obtain images through the [official dataset's full-image archive link](https://github.com/hpatches/hpatches-dataset#full-image-sequences). Preserve URL, file hashes and selected names; do not commit dataset images.

Each sequence contributes all five 1→2..6 truth-backed positives. Development uses all directed cross-scene combinations of first images as candidate negatives (12 pairs); reporting uses its two cross-scene directions (2 pairs). Inspect first-image previews before labeling negatives. If two sequences show a shared scene/object, exclude that negative explicitly with a recorded reason before running, without replacing it based on engine behavior.

## Baseline execution

Use SIFT and ORB, CPU, feature budget 1500, ratio 0.75, legacy adaptive RANSAC with base 4 px, seed 0, three measured repetitions and one warmup. Use the existing evaluator and retain every raw result/failure, input/truth hash, configuration and clean source revision. Do not interpret repetitions as new independent scenes. Report development and reporting separately.

## Candidate diagnostic gates

Apply gates to the existing fits after execution; do not refit, fabricate a fit or modify reported correspondence membership. A candidate retains an attempt only when the baseline fit is valid and all its required diagnostics exist and meet:

- Minimum solver inliers: 10, 20 or 40.
- Minimum reference support hull / reference pixel-extent area: 0.01, 0.05 or 0.10.
- Maximum inlier residual p95 in target pixels: 3, 5 or no additional cap.

These 27 candidates are hypotheses, not established universal thresholds. The target-image hull fraction is deliberately not a gate because a small object can occupy a small part of its target. Missing diagnostics cannot pass a required gate. No gate is a calibrated confidence score.

For each engine separately, eligible candidates must retain at least 75% of baseline accepted positive attempts whose mean corner error is ≤3 px. Among eligible candidates choose lexicographically: fewest accepted labeled negatives; then fewest accepted truth-backed positives with mean corner error >5 px; then most accepted positives within 3 px; then most accepted positives within 5 px. Exact ties use the least restrictive tuple (minimum inliers, minimum support, residual cap with no cap least restrictive). If no baseline positive is accurate within 3 px, do not choose a policy from that engine's sample.

Publish every development candidate's counts and the chosen definitions before inspecting reporting diagnostics/errors. Then apply only the selected policy and baseline to the reserved reporting scenes. Do not retune after reporting. Separately count baseline failed fits, policy rejections, accepted inaccurate fits, labeled-negative acceptance and runtime/annotation errors. Use all evaluable truth-backed attempts for accuracy denominators; a rejected fit is not a successful localization.

## Decision and limits

This small six-scene experiment may support further research or an explicitly experimental gate; it cannot establish general detection reliability. A reporting result that fails to retain 75% of the baseline's accurate positives, or adds no useful rejection of inaccurate fits, is evidence against promoting that candidate. Preserve adverse results. Do not ship an automatic default rejection policy from development counts alone. Broader unrelated, repeated-texture, occluded, low-texture and user-relevant object scenes remain necessary before a production claim.
