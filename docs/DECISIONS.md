# Architecture Decisions

## Use built-in OpenCV SIFT and ORB

SIFT and ORB are classical feature algorithms with stable OpenCV implementations. They require no training or downloaded weights and provide a suitable local baseline.

## Match descriptor types with their appropriate distances

SIFT uses floating point descriptors and L2 distance. ORB uses binary descriptors and Hamming distance, or Hamming2 for `WTA_K` 3 or 4. The engines remain separate while sharing a structured result interface.

## Treat homography output as planar image-space estimation

RANSAC homography is useful for projecting a planar reference into a target image. VISOR describes it as an estimate and does not present it as general 3D pose recovery.

## Run analysis outside the Qt event thread

Image decoding, extraction, matching, and geometry run on a `QThread` worker so the desktop event loop can continue responding during analysis.

