# Dataset and model-training plan

## Goal

Prepare a professional image-pair dataset flow for the VISOR matching stack and keep the project aligned with the actual runtime environment.

## Verified runtime facts

- CUDA-enabled torch is installed in the active project venv.
- The learned-engine path is available when `lightglue` is importable.
- `XFeat` is not currently available because the package installation fails in this environment; the UI lists it as disabled until the dependency is fixed.
- The app already exposes the learned-engine selectors in the runtime UI. `SuperPoint+LightGlue` and `ALIKED+LightGlue` are active when `lightglue` is present.

## Recommended public datasets

1. MegaDepth — large-scale multi-view image pairs for geometric matching and localization.
2. HPatches — compact but useful benchmark for validation and tuning.
3. A local project-specific capture set in `Sample/Reference` and `Sample/Target` for domain-specific testing.

## Folder layout

```text
Sample/
  Dataset/
    MegaDepth/
    HPatches/
  Reference/
  Target/
```

## Download commands

```bash
cd /d c:\Users\Luikz\Downloads\VISOR
bash scripts/download_matching_dataset.sh
```

The script is a pragmatic dataset bootstrap for the project. It attempts a large public matching dataset in `Sample/Dataset` and adds the HPatches benchmark as a validation set.

## Model-training guidance

This repository is not a full deep-learning training project. It is a classical/OpenCV + optional learned-matching desktop app. For real end-to-end model training, the correct workflow is:

1. build a dataset of matched image pairs
2. generate positive and negative pairs with valid homographies
3. train a dedicated matching or feature model in a separate GPU project
4. then integrate the trained model into a VISOR engine wrapper once the weights are proven

## What to avoid

- Do not attempt a huge from-scratch model training pass inside this desktop app without a separate training pipeline.
- Do not treat the current repo as a generic foundation-model training workspace.
- Do not commit heavy downloaded datasets to Git.

## Best practical path

- use the current repo for the app + geometry validation
- keep `Sample/` as the local test and tuning area
- keep the large training dataset on local disk and not under version control
- use HPatches for fast validation and MegaDepth-style pairs for larger tuning

## Next steps

- Add a real pair-list and metadata CSV for local matching evaluations.
- Add a stable `Dataset/manifest.csv` with `reference,target,scene` entries.
- Validate the learned engines on the downloaded pairs before increasing model complexity.
- Only then decide whether a separate deep-learning training project is justified.
