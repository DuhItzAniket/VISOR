"""Typed records shared by feature engines, matching, geometry, and the UI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np
from numpy.typing import NDArray

EngineName = Literal["SIFT", "ORB"]
FloatArray = NDArray[np.float32]
ByteArray = NDArray[np.uint8]
MatrixArray = NDArray[np.float64]


@dataclass(frozen=True)
class KeypointInfo:
    x: float
    y: float
    size: float
    angle: float
    response: float
    octave: int
    class_id: int


@dataclass(frozen=True)
class DescriptorInfo:
    count: int
    dimensions: int
    dtype: str
    bytes_used: int
    distance: str


@dataclass(frozen=True)
class FeatureSet:
    keypoints: tuple[KeypointInfo, ...]
    descriptors: NDArray[np.generic] | None
    descriptor_info: DescriptorInfo
    extraction_ms: float


@dataclass(frozen=True)
class MatchInfo:
    query_index: int
    train_index: int
    distance: float
    ratio: float | None


@dataclass(frozen=True)
class MatchSet:
    matches: tuple[MatchInfo, ...]
    candidate_count: int
    good_count: int
    matcher: str
    filter_name: str
    threshold: float
    duration_ms: float


@dataclass(frozen=True)
class GeometryResult:
    valid: bool
    message: str
    homography: MatrixArray | None
    inlier_mask: tuple[bool, ...]
    inlier_count: int
    outlier_count: int
    inlier_ratio: float
    reprojection_error_px: float | None
    projected_corners: tuple[tuple[float, float], ...]
    center: tuple[float, float] | None


@dataclass(frozen=True)
class PerformanceMetrics:
    extraction_reference_ms: float
    extraction_target_ms: float
    matching_ms: float
    geometry_ms: float
    total_ms: float


@dataclass(frozen=True)
class AnalysisResult:
    engine: EngineName
    reference_path: Path
    target_path: Path
    reference_size: tuple[int, int]
    target_size: tuple[int, int]
    reference_features: FeatureSet
    target_features: FeatureSet
    match_set: MatchSet
    geometry: GeometryResult
    performance: PerformanceMetrics
    matches_image: NDArray[np.uint8]
    localization_image: NDArray[np.uint8]
    warped_image: NDArray[np.uint8] | None

