# Reproducible registration evaluation

Updated 2026-10-25. This is a developer evaluation tool; desktop users use the normal image workflow.

## Local controlled fixtures

```powershell
python -m visor.evaluate make-synthetic tests/data/golden_reference.png build/evaluation-example
python -m visor.evaluate run build/evaluation-example/manifest.json build/evaluation-example/report.json --engines SIFT ORB --repetitions 3 --warmup 1 --device cpu
```

Preparation requires a new output directory and preserves existing files. It creates one mild known warp, an unrelated noise image and a blank negative. These are development fixtures, not a real-world reporting dataset. Generator seed and homography are embedded in the manifest.

## Manifest version 1

Paths are relative to the manifest. Ground truth is optional and can be a finite invertible inline 3×3 matrix or a path to a whitespace-delimited matrix file.

```json
{
  "version": 1,
  "pairs": [
    {
      "id": "scene-a/1-2",
      "reference": "images/reference.png",
      "target": "images/target.png",
      "homography": "H_reference_target.txt",
      "expected_match": true,
      "split": "heldout",
      "condition": "viewpoint"
    },
    {
      "id": "unrelated-scenes",
      "reference": "images/reference.png",
      "target": "images/another-scene.png",
      "expected_match": false,
      "split": "heldout",
      "condition": "negative"
    }
  ]
}
```

Pair ids must be unique. A negative cannot also carry a ground-truth mapping. Missing image files generate failure rows rather than disappearing from the run. Invalid annotations are reported explicitly. Development and held-out splits cannot be mixed in one aggregate run; a split label does not prove a pretrained model never saw the source data.

## HPatches full images

```powershell
python -m visor.evaluate make-hpatches Sample/Dataset/HPatches/sequences build/hpatches-manifest.json
python -m visor.evaluate run build/hpatches-manifest.json build/hpatches-report.json --engines SIFT ORB --repetitions 3 --warmup 1
```

Provide the **full-image sequences**, not stacked descriptor patches. The loader expects sequence folders prefixed `i_`/`v_`, `1.ppm` through `6.ppm`, and `H_1_2` through `H_1_6`. It records absent pairs and reports when no usable dataset is present. It does not download data. Reports separate illumination/viewpoint conditions. Dataset source and citation: [official HPatches repository](https://github.com/hpatches/hpatches-dataset#full-image-sequences). VISOR's corner-error summaries are not the published descriptor benchmark protocol.

## What is recorded

- Manifest snapshot and hash; hashes of input images/external truth files; the actual matrices used.
- Application/source revision, dirty state, evaluator code hash, platform/architecture and dependency versions.
- Exact requested settings, estimator, RNG seed, device policy, repetitions/warmup and optional feature budget. Every completed result also contains effective engine/matcher/threshold/device information.
- Every measured attempt, including failed fits and runtime errors, plus separately marked warmup attempts. Unknown metrics stay null.
- Per-engine and per-condition summaries. Failed fits/runtime errors remain in denominators. Invalid annotations are counted separately and excluded from accuracy denominators.

Each call creates a fresh engine and includes image decoding, initialization, extraction, matching, geometry and rendering. Warmup warms caches; it does **not** reuse a model object or establish steady-state inference latency. Timing summaries cover all attempts, including cheap failures/negatives; inspect raw rows or conditions before comparing speed.

`--feature-budget` applies to SIFT/ORB and learned extractors. Defaults retain each engine's native budget; this is not an equal-budget experiment unless the flag is supplied. AKAZE/BRISK use native configurations and reject that flag. Device policy defaults to CPU; `--device auto` permits CUDA when supported and the result records the device used. Optional setup is described in OPTIONAL_ENGINES.md.

## Accuracy and negative-pair conventions

Forward-project the four reference pixel-coordinate corners `(0,0)`, `(w-1,0)`, `(w-1,h-1)`, `(0,h-1)` through fitted and ground-truth transforms. Report mean, RMSE and maximum Euclidean corner distance in target pixels. A ground-truth horizon crossing the reference is an annotation error. Accuracy at 1/3/5 px uses the **mean** corner distance and all evaluable truth-backed attempts as the denominator.

Inlier reprojection residual remains separate from corner accuracy. Without a supplied truth mapping, corner accuracy is unavailable. A geometrically valid fit on a pair explicitly marked `expected_match: false` counts as a false acceptance. Unlabeled pairs do not enter negative denominators; no negative pairs means the false-acceptance rate is unavailable, not zero.

The CLI completing successfully means a report was produced. It does not mean every attempted engine succeeded or a release-quality threshold was met. Review error rows, failure denominators, dataset membership and raw outputs before drawing conclusions.

## Independent diagnostic-gate study

The preregistered [reliability protocol](RELIABILITY_STUDY.md) fixes development/reporting scenes, the grid and its selection rule. The separate offline tool consumes existing raw evaluator reports:

```text
python -m visor.reliability_study select development.json.gz frozen-selection.json
python -m visor.reliability_study report heldout.json.gz frozen-selection.json reporting-analysis.json
```

Selection accepts only development rows; reporting accepts only held-out rows, identical execution settings and disjoint pair ids/image hashes. Outputs are created exclusively and cannot overwrite existing inputs/reports. The selection records every candidate and the chosen gate; reporting records each attempt's decision and keeps all truth-backed failures in denominators. Input/code hashes make the derived analysis reviewable. This module never changes fitted transforms, solver masks or desktop defaults. Publish the selection before inspecting reporting performance.

Reporting records both the original selection-file byte hash and a canonical parsed-JSON content hash (sorted keys, compact separators, UTF-8). Git can normalize CRLF/LF across platforms without changing a choice; verify content with the canonical hash. New study JSON outputs and tracked evidence JSON use LF. Compressed raw reports retain their exact bytes. Provenance repairs must preserve the original input-byte hash and explicitly record that choices/results did not change.

## Frozen synthetic stress cases

The [2026-10-26 protocol](evaluation/SYNTHETIC_STRESS_PROTOCOL.md) fixes 21 development pairs before measurement: known textured/repeated/low-texture/occluded mappings and independent-scene/noise/blank negatives. It makes no real-world reliability or speed claim and never retunes I15's reserved reporting gates. Preparation invokes no engine/model/UI and refuses existing output:

```powershell
$env:CUDA_VISIBLE_DEVICES='-1'
python scripts/create_stress_manifest.py build/evaluation-stress-20261026
python -m visor.evaluate run build/evaluation-stress-20261026/manifest.json build/evaluation-stress-20261026/report.json --engines SIFT ORB --repetitions 3 --warmup 1 --device cpu --feature-budget 1500 --seed 0
```

Use new output paths and keep raw failures, warmups, source/input/truth hashes and per-condition counts. The generator hash and frozen protocol hash are embedded in the manifest. Three seeds/repetitions share construction rules and are not new independent natural scenes.
