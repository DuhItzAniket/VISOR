# Evaluation evidence — 2026-10-25

Evaluator source: `b2c7f0b`; both reports recorded a clean source checkout. JSON is gzip-compressed to keep full correspondence-level evidence manageable. No model weights or dataset images are committed here.

## Raw reports

- [Synthetic development report](synthetic-20261025.json.gz): one known warp and two negatives, two classical engines, three measured repetitions after one warmup per pair/engine; 18 measured attempts.
- [HPatches sample report](hpatches-sample-20261025.json.gz): 10 positive full-image pairs plus two cross-scene negatives, two engines, three measured repetitions after one warmup; 72 measured attempts.

Each report embeds its manifest, input hashes, actual ground-truth matrices, source/environment/settings, every warmup/measured row and effective analysis details. Read it with standard gzip tools or Python:

```powershell
python -c "import gzip,json; r=json.load(gzip.open('docs/evaluation/hpatches-sample-20261025.json.gz','rt')); print(json.dumps(r['summary'],indent=2))"
```

## Dataset selection and reproducibility

The HPatches archive is linked by the [official dataset repository](https://github.com/hpatches/hpatches-dataset#full-image-sequences). The sample selected the alphabetically first complete illumination and viewpoint sequence with no more than 64 MiB of uncompressed image/transform files per sequence: `i_ajuntament` and `v_abstract`. Selection did not use engine performance. Bounded archive-range retrieval downloaded about 17.7 MB, rather than the entire 1.28 GB ZIP. The report's `sample_source` records source URL, selection rule and file hashes.

The five 1→2..6 mappings per sequence provide ten positive pairs. Cross-scene pairs use each sequence's first image against the other sequence's first image in both directions; reference previews were inspected and show different scenes (town hall versus artwork). These provide only two distinct negatives. Repeated executions are repeated measurements, not additional independent scenes.

Images remain local under ignored `build/evaluation-data/hpatches/sequences`. To reproduce elsewhere, obtain matching full-image sequences, verify the report's file hashes, and recreate its embedded manifest relative to the images. The local selection helper is a research-download aid, not part of the application. See [EVALUATION.md](../EVALUATION.md) for the loader and metric definitions.

## Baseline observations

HPatches sample: CPU, feature budget 1500, default ratio 0.75, legacy adaptive RANSAC with base 4 px, fixed seed 0. Each engine has 30 positive measured attempts and six negative attempts, from ten and two distinct pairs respectively.

| Engine | Valid positive fits | Mean corner error ≤3 px | Mean corner error ≤5 px | Accepted negative fits |
|---|---|---|---|---|
| SIFT | 21/30 | 9/30 | 12/30 | 0/6 |
| ORB | 30/30 | 12/30 | 15/30 | 0/6 |

All attempts completed without runtime or annotation errors. A high positive fit rate does not imply accurate localization: for example ORB accepted `i_ajuntament/1-4` with seven solver inliers and mean corner error around 305 px. That observation warrants reliability work; it is not a reason to rewrite the measured result or tune thresholds on this reporting sample.

Synthetic positives were accurate within 1 px mean corner distance and neither development negative was accepted in these runs. Those easy controlled fixtures do not predict generalization to the real-image sample.

This small sample does **not** establish an engine ranking, published HPatches benchmark equivalence, a general false-positive rate or production reliability. Timing rows include fresh construction, decoding and rendering and vary across pair difficulty; aggregate speed claims are deliberately omitted.

## Next experiment

Keep this reporting sample unchanged. Select separate development scenes to investigate low-support but apparently valid fits; compare matching policies and support/plausibility diagnostics there. Then freeze any policy before testing additional held-out scenes and user-relevant unrelated/occluded/low-texture pairs. Track this work as I15 in the improvement ledger.
