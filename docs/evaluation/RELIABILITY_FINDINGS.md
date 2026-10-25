# Independent reliability study — 2026-10-25

Protocol frozen at `689522d`: [selection and analysis plan](../RELIABILITY_STUDY.md). Evaluator and study tool source: `dec9b33`. The development report recorded a clean checkout. This is a small diagnostic-gate experiment, not a revised registration algorithm or production reliability claim.

## Development evidence and frozen choices

Scenes: i_autannes, i_bologna, v_adam and v_apprentices. First-image previews were inspected before evaluation: mountain station, city panorama, Creation of Adam reproduction and apprentice illustration. No shared scene/object was identified; all twelve directed cross-scene negatives were retained. Twenty truth-backed positive pairs plus twelve negatives, two engines, three measured repetitions and one warmup produce **192 measured attempts** plus 64 warmups. There were no runtime or annotation errors.

- [Raw development report](reliability-development-20261025.json.gz), 822,896 bytes; SHA256 `74ea64de955b670ef70759c49e54c3178071ffe62995d448abf152f2bd3971a1`.
- [Frozen selection and all 27 candidates per engine](reliability-selection-20261025.json); SHA256 `8eaf60eafcef5ce889a9d0bacc20434f7fe4fad6d31a818687d74e6dcd00215e`.

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

i_books and v_artisans remain reserved. The selected definitions above are published before their performance is inspected. Run baseline registration with identical settings, then apply only the frozen choices. Do not retune on these scenes or the original published reporting sample. This section will record adverse as well as favorable results.

## Reproduction

The raw report embeds relative manifest paths, complete truth matrices, selected data/URL/hash provenance, settings, all measured/warmup rows and actual fit diagnostics. Images are excluded from Git. Obtain matching full sequences through the official dataset link and verify hashes. Recompute the selection:

```text
python -m visor.reliability_study select docs/evaluation/reliability-development-20261025.json.gz new-selection.json
```

Bounded development retrieval transferred ~29.6 MB of archive ranges and checked each member's ZIP CRC and SHA256. This engineering study does not reproduce the published HPatches descriptor benchmark protocol. No speed ranking or general false-positive rate is inferred.
