"""OpenCV-backed SIFT and ORB feature extraction."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from time import perf_counter
from typing import Any, Protocol, cast

import cv2
import numpy as np
from numpy.typing import NDArray

from visor.models import DescriptorArray, DescriptorInfo, FeatureSet, KeypointInfo


@dataclass(frozen=True)
class SIFTConfiguration:
    max_features: int = 0
    octave_layers: int = 3
    contrast_threshold: float = 0.04
    edge_threshold: float = 10.0
    sigma: float = 1.6

    def __post_init__(self) -> None:
        if self.max_features < 0 or self.octave_layers < 1:
            raise ValueError("SIFT max features must be non-negative and octave layers must be positive.")
        if not all(isfinite(value) and value > 0 for value in (self.contrast_threshold, self.edge_threshold, self.sigma)):
            raise ValueError("SIFT thresholds and sigma must be finite positive values.")


@dataclass(frozen=True)
class ORBConfiguration:
    max_features: int = 1500
    scale_factor: float = 1.2
    levels: int = 8
    edge_threshold: int = 31
    first_level: int = 0
    wta_k: int = 2
    score_type: str = "HARRIS"
    patch_size: int = 31
    fast_threshold: int = 20

    def __post_init__(self) -> None:
        if self.max_features < 1 or self.levels < 1 or self.first_level < 0 or self.first_level >= self.levels:
            raise ValueError("ORB feature count and levels must be positive; first level must be within the pyramid.")
        if not isfinite(self.scale_factor) or self.scale_factor <= 1:
            raise ValueError("ORB scale factor must be finite and greater than one.")
        if self.wta_k not in (2, 3, 4) or self.score_type not in ("HARRIS", "FAST"):
            raise ValueError("ORB WTA_K must be 2, 3, or 4 and score type must be HARRIS or FAST.")
        if self.edge_threshold < 0 or self.patch_size < 2 or not 0 <= self.fast_threshold <= 255:
            raise ValueError("ORB edge, patch, and FAST threshold values are outside supported ranges.")


class FeatureEngine(Protocol):
    name: str

    def extract(self, gray: NDArray[np.uint8]) -> FeatureSet: ...


def _convert_keypoints(points: list[cv2.KeyPoint]) -> tuple[KeypointInfo, ...]:
    return tuple(
        KeypointInfo(p.pt[0], p.pt[1], p.size, p.angle, p.response, p.octave, p.class_id)
        for p in points
    )


class SIFTFeatureEngine:
    name = "SIFT"

    def __init__(self, config: SIFTConfiguration | None = None) -> None:
        self.config = config or SIFTConfiguration()

    def extract(self, gray: NDArray[np.uint8]) -> FeatureSet:
        cfg = self.config
        detector = cast(Any, cv2).SIFT_create(
            nfeatures=cfg.max_features,
            nOctaveLayers=cfg.octave_layers,
            contrastThreshold=cfg.contrast_threshold,
            edgeThreshold=cfg.edge_threshold,
            sigma=cfg.sigma,
        )
        start = perf_counter()
        points, descriptors = detector.detectAndCompute(gray, None)
        elapsed = (perf_counter() - start) * 1000
        descriptor_array = cast(DescriptorArray | None, descriptors)
        count = 0 if descriptor_array is None else int(descriptor_array.shape[0])
        dims = 128 if descriptor_array is None else int(descriptor_array.shape[1])
        info = DescriptorInfo(count, dims, "FLOAT32", 0 if descriptor_array is None else descriptor_array.nbytes, "L2")
        return FeatureSet(_convert_keypoints(points), descriptor_array, info, elapsed)


class ORBFeatureEngine:
    name = "ORB"

    def __init__(self, config: ORBConfiguration | None = None) -> None:
        self.config = config or ORBConfiguration()

    def extract(self, gray: NDArray[np.uint8]) -> FeatureSet:
        cfg = self.config
        detector = cast(Any, cv2).ORB_create(
            nfeatures=cfg.max_features,
            scaleFactor=cfg.scale_factor,
            nlevels=cfg.levels,
            edgeThreshold=cfg.edge_threshold,
            firstLevel=cfg.first_level,
            WTA_K=cfg.wta_k,
            scoreType=cv2.ORB_HARRIS_SCORE if cfg.score_type == "HARRIS" else cv2.ORB_FAST_SCORE,
            patchSize=cfg.patch_size,
            fastThreshold=cfg.fast_threshold,
        )
        start = perf_counter()
        points, descriptors = detector.detectAndCompute(gray, None)
        elapsed = (perf_counter() - start) * 1000
        descriptor_array = cast(DescriptorArray | None, descriptors)
        count = 0 if descriptor_array is None else int(descriptor_array.shape[0])
        dims = 32 if descriptor_array is None else int(descriptor_array.shape[1])
        distance = "HAMMING2" if cfg.wta_k in (3, 4) else "HAMMING"
        info = DescriptorInfo(count, dims, "UINT8 / BINARY", 0 if descriptor_array is None else descriptor_array.nbytes, distance)
        return FeatureSet(_convert_keypoints(points), descriptor_array, info, elapsed)
