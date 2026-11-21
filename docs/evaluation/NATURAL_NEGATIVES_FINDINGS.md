# Cross-scene negative results

SIFT and ORB each rejected all 12 directed pairs across four visually distinct HPatches scenes. There were no runtime errors. The two directions between the architectural scenes were rejected by both engines. The test used a model-free CPU environment from clean source `e321fba`. [Frozen protocol](NATURAL_NEGATIVES_PROTOCOL.md) · [All 24 raw rows](natural-negatives-20261121.json.gz)

These are six unordered comparisons that reuse four scenes. The result records zero false accepts in this sample. It supplies no general false-acceptance rate and does not cover near-duplicate objects, confusing repeated patterns or other visually similar subjects. There is no ground-truth transform for an unrelated pair, so the report leaves corner error unavailable. The earlier [occlusion study](NATURAL_OCCLUSION_FINDINGS.md) still contains accepted inaccurate fits on true pairs. App settings were not changed.

To reproduce, verify the four original image hashes in the raw manifest, preserve the directed ordering and use the parameters in the protocol. Compressed report SHA-256 `b4f377a1b0f872505e70aa2f40b55f3caaab327bf0ec5fc3ff8445bc99eced3f`.
