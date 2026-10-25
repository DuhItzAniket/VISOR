# Independent reliability study — 2026-10-25

Protocol frozen at `689522d`: [selection and analysis plan](../RELIABILITY_STUDY.md). Development source: `dec9b33`; reporting source: `f85c7e0`, which publishes the choices and changes only documentation/data consistency checks. Both raw reports recorded clean checkouts. The evaluator/study algorithms are identical across those revisions. This is a small diagnostic-gate experiment, not a revised registration algorithm or production reliability claim.

## Development evidence and frozen choices

Scenes: i_autannes, i_bologna, v_adam and v_apprentices. First-image previews were inspected before evaluation: mountain station, city panorama, Creation of Adam reproduction and apprentice illustration. No shared scene/object was identified; all twelve directed cross-scene negatives were retained. Twenty truth-backed positive pairs plus twelve negatives, two engines, three measured repetitions and one warmup produce **192 measured attempts** plus 64 warmups. There were no runtime or annotation errors.

- [Raw development report](reliability-development-20261025.json.gz), 822,896 bytes; SHA256 `74ea64de955b670ef70759c49e54c3178071ffe62995d448abf152f2bd3971a1`.
- [Frozen selection and all 27 candidates per engine](reliability-selection-20261025.json); Git/LF file SHA256 `2549e43e82cb71cf7fc641ff4867cfdd133c3a66c17067f5b6acbe926f13f172`. Original Windows/CRLF input SHA256 was `8eaf60eafcef5ce889a9d0bacc20434f7fe4fad6d31a818687d74e6dcd00215e`. Canonical parsed-JSON SHA256 is `d95702007c6d8c76db3d71d9d0b04fc774ab22e7df9e9242eec1d896833145b2`, independent of whitespace/line endings.

Counts below are measured attempts, not independent scenes. Each engine has 60 truth-backed positive attempts and 36 negative attempts from 20 and 12 distinct pairs respectively.

| Engine / decision | Accepted positives within 3 px | Accepted positives within 5 px | Accepted positives above 5 px | Accepted labeled negatives |
|---|---|---|---|---|
| SIFT baseline | 45/60 | 54/60 | 6/60 | 3/36 |
| SIFT frozen gate | 45/60 | 54/60 | 0/60 | 0/36 |
| ORB baseline | 15/60 | 48/60 | 12/60 | 0/36 |
| ORB frozen gate | 15/60 | 45/60 | 0/60 | 0/36 |

The fixed selection rule chooses **SIFT ≥20 inliers / reference hull fraction ≥0.01**, and **ORB ≥40 inliers / reference hull fraction ≥0.01**. Neither selected gate adds a residual-p95 cap. This is a result of the preregistered least-restrictive tie rule, not evidence that residuals are generally irrelevant.

SIFT's three accepted negative attempts repeat one distinct negative pair. ORB's gate also rejects three positive attempts that were within 5 px (one distinct pair). Policy rejection is not successful localization; denominators remain unchanged. These development improvements are subject to selection bias and require the reserved reporting step.

## Reserved reporting

i_books and v_artisans were evaluated only after the selected definitions were pushed at f85c7e0. First-image previews show books versus a mosaic mural; both directed negatives were retained. Ten positive pairs/two negatives, two engines and three repetitions produce 72 measured rows plus 24 warmups. Bounded retrieval transferred ~17.5 MB; hashes and provenance are embedded in the raw report.

- [Raw reserved reporting report](reliability-reporting-20261025.json.gz), 753,670 bytes; SHA256 `f4f0f8000b774079f8b6aca84996723af18544497498c266ef4ec63eaa1890bc`.
- [Frozen-gate reporting analysis and all attempt decisions](reliability-reporting-analysis-20261025.json); Git/LF SHA256 `468c6b4419c7ce664626089cb9568193340e19bdfbff2a8a2e7b781b215fa128`. A 2026-10-26 provenance repair adds the canonical selection hash while preserving the original input-byte hash, every choice, count and decision. The earlier analysis file's Windows-byte SHA256 was `b85d4b5d362937d0eae1b9cec65c53b9d6d8b356a29000c8338ecc10c84aa9cc`; only provenance fields/line endings changed.

There were **no runtime failures**. The truth transform for v_artisans/1-5 crosses the reference rectangle's horizon under the evaluator's whole-image corner convention. Its three repetitions per engine are retained as annotation-error rows and excluded from truth-accuracy denominators. This is a limitation of this metric/annotation combination, not a claim that every use of that dataset transform is invalid. No replacement pair was selected. Nine distinct positive pairs remain evaluable, giving 27 truth-backed attempts per engine; two distinct negatives give six attempts.

| Engine / decision | Accepted positives within 3 px | Accepted positives within 5 px | Accepted positives above 5 px | Accepted labeled negatives |
|---|---|---|---|---|
| SIFT baseline | 24/27 | 24/27 | 3/27 | 0/6 |
| SIFT frozen gate | 24/27 | 24/27 | 3/27 | 0/6 |
| ORB baseline | 24/27 | 27/27 | 0/27 | 0/6 |
| ORB frozen gate | 24/27 | 27/27 | 0/27 | 0/6 |

Both policies retain all baseline ≤3 px positives, but **reject no additional reporting fits**. SIFT v_artisans/1-4 remains accepted with mean corner error 9.88 px, 343 inliers and reference hull fraction 0.359. Inlier count and reference coverage alone do not establish corner accuracy. Repeated runs of that pair are not three independent failures.

**Decision:** do not promote either gate into the desktop default. The development gain did not demonstrate independent reporting benefit, and the predeclared decision rule treats that as evidence against promotion. Do not retune these gates on the reporting scenes. Future work needs additional independent scenes, user-relevant object/background negatives and investigation of spatial/extrapolation stability and overlap-aware ground-truth conventions. The original published sample and classical golden fixtures remain unchanged.

## Reproduction

The raw report embeds relative manifest paths, complete truth matrices, selected data/URL/hash provenance, settings, all measured/warmup rows and actual fit diagnostics. Images are excluded from Git. Obtain matching full sequences through the official dataset link and verify hashes. Recompute the selection:

```text
python -m visor.reliability_study select docs/evaluation/reliability-development-20261025.json.gz new-selection.json
```

Bounded development retrieval transferred ~29.6 MB of archive ranges and checked each member's ZIP CRC and SHA256. This engineering study does not reproduce the published HPatches descriptor benchmark protocol. No speed ranking or general false-positive rate is inferred.
