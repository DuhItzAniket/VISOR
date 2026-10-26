# Optional learned runtime setup

Updated 2026-10-26. These instructions are for source developers. Standard desktop bundles continue to provide SIFT/ORB and do not expose package installation to end users.

## Supported source pins

| Component | Revision | Integration |
|---|---|---|
| LightGlue | `eb42fee2d71449efb0aa5c10549752b5d75384d8` | Official package; SuperPoint, ALIKED, DISK and SIFT extractors with native LightGlue assignment matching |
| XFeat | `e92685f57f8318b18725c5c8c0bd28c7fe188d9a` | Official source/cache; `modules.xfeat.XFeat.detectAndCompute`, 64-D descriptors and VISOR's mutual L2 nearest-neighbor matching |

The reviewed XFeat source has no installable setup.py and does not expose `xfeat.Extractor`. Installing a package named `xfeat` is not this integration. The pinned upstream Hub entry also fetches weights from a moving main URL; VISOR loads the weights committed at its fixed source revision instead.

## Setup and cache

```powershell
python -m pip install -r requirements/learned.txt
python -m pip install --no-deps -r requirements/learned-adapter.txt
python -m visor.model_setup --xfeat
```

LightGlue's pinned upstream metadata requires the package name opencv-python. VISOR supplies its cv2 API using opencv-contrib-python-headless; the separate --no-deps adapter step avoids overlapping providers after installing the explicitly listed inference dependencies. pip check can still report that upstream package-name requirement as unsatisfied: no metadata shim or false package claim is installed. Real inference checks, not metadata discovery, establish adapter operation. Recreate a contaminated environment rather than uninstalling one overlapping package in place.

The source app offers the same setup under Window → Diagnostics. Git is required for explicit XFeat setup. Existing valid caches are reused. An existing corrupt cache is reported and preserved; setup does not silently replace it.

XFeat is stored under `%LOCALAPPDATA%/VISOR/models` on Windows, `~/Library/Caches/VISOR/models` on macOS, and `$XDG_CACHE_HOME/VISOR/models` or `~/.cache/VISOR/models` on Linux. Set `VISOR_MODEL_HOME` to select another base directory. The runtime directory contains the full revision in its name and a manifest of source/weight SHA-256 hashes. Inference verifies those hashes and never downloads or updates XFeat code.

The adapter initializes the pinned inference model on the requested device and loads a weights-only state dictionary. This avoids upstream constructor behavior that chooses CUDA regardless of the caller's CPU preference. Conflicting packages named `modules` are rejected with an explanation rather than imported accidentally. Upstream source and its license remain in the cache; they are not copied into this repository.

LightGlue may download extractor/matcher weights on first construction using its upstream cache behavior. Dependency availability is not proof that all weights are cached or that an accelerator is usable. Device information in each completed result records the device actually used. Packaged learned support and a complete model notice inventory remain release tasks.

## Evidence and limits

- Local CPU XFeat check with 512 requested features: 512 identity matches; 348 mutual matches/328 inliers on one controlled mild warp; maximum corner error 2.29 px. This is a fixture check, not a real-world accuracy ranking.
- Cache integrity, missing revision, reuse without network, namespace collision and mutual-neighbor contracts have offline regressions.
- Optional CPU inference has a separate manually triggered GitHub workflow. Standard desktop jobs exclude the `optional_model` marker, so core validation does not download model weights.
- CUDA, other devices, model redistribution notices and learned models in native bundles require separate evidence. The pinned source path does not imply those gates are complete.

## Primary sources reviewed

[XFeat inference API at the pin](https://github.com/verlab/accelerated_features/blob/e92685f57f8318b18725c5c8c0bd28c7fe188d9a/modules/xfeat.py), [upstream Hub loading behavior](https://github.com/verlab/accelerated_features/blob/e92685f57f8318b18725c5c8c0bd28c7fe188d9a/hubconf.py), [LightGlue matcher output and threshold](https://github.com/cvg/LightGlue/blob/eb42fee2d71449efb0aa5c10549752b5d75384d8/lightglue/lightglue.py), [PyTorch synchronization](https://docs.pytorch.org/docs/stable/generated/torch.cuda.synchronize.html).
