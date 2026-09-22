"""OpenCV-backed SIFT and ORB feature extraction."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Protocol

import cv2
import numpy as np
from numpy.typing import NDArray

from visor.models import DescriptorInfo, FeatureSet, KeypointInfo


@dataclass(frozen=True)
class SIFTConfiguration:
    max_features: int = 0
    octave_layers: int = 3
    contrast_threshold: float = 0.04
    edge_threshold: float = 10.0
    sigma: float = 1.6


@dataclass(frozen=True)
class ORBConfiguration:
    max_features: int = 1500
    scale_factor: float = 1.2
    levels: int = 8
    edge_threshold: int = 31
    first_level: int = 0
    wta_k: int = 2
    patch_size: int = 31
    fast_threshold: int = 20


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
        detector = cv2.SIFT_create(
            nfeatures=cfg.max_features,
            nOctaveLayers=cfg.octave_layers,
            contrastThreshold=cfg.contrast_threshold,
            edgeThreshold=cfg.edge_threshold,
            sigma=cfg.sigma,
        )
        start = perf_counter()
        points, descriptors = detector.detectAndCompute(gray, None)
        elapsed = (perf_counter() - start) * 1000
        count = 0 if descriptors is None else int(descriptors.shape[0])
        dims = 128 if descriptors is None else int(descriptors.shape[1])
        info = DescriptorInfo(count, dims, "FLOAT32", 0 if descriptors is None else descriptors.nbytes, "L2")
        return FeatureSet(_convert_keypoints(points), descriptors, info, elapsed)


class ORBFeatureEngine:
    name = "ORB"

    def __init__(self, config: ORBConfiguration | None = None) -> None:
        self.config = config or ORBConfiguration()

    def extract(self, gray: NDArray[np.uint8]) -> FeatureSet:
        cfg = self.config
        if cfg.wta_k not in (2, 3, 4):
            raise ValueError("ORB WTA_K must be 2, 3, or 4.")
        detector = cv2.ORB_create(
            nfeatures=cfg.max_features,
            scaleFactor=cfg.scale_factor,
            nlevels=cfg.levels,
            edgeThreshold=cfg.edge_threshold,
            firstLevel=cfg.first_level,
            WTA_K=cfg.wta_k,
            scoreType=cv2.ORB_HARRIS_SCORE,
            patchSize=cfg.patch_size,
            fastThreshold=cfg.fast_threshold,
        )
        start = perf_counter()
        points, descriptors = detector.detectAndCompute(gray, None)
        elapsed = (perf_counter() - start) * 1000
        count = 0 if descriptors is None else int(descriptors.shape[0])
        dims = 32 if descriptors is None else int(descriptors.shape[1])
        distance = "HAMMING2" if cfg.wta_k in (3, 4) else "HAMMING"
        info = DescriptorInfo(count, dims, "UINT8 / BINARY", 0 if descriptors is None else descriptors.nbytes, distance)
        return FeatureSet(_convert_keypoints(points), descriptors, info, elapsed)

