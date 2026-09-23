"""Typed records shared by feature engines, matching, geometry, and the UI."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from typing import Literal

import numpy as np
from numpy.typing import NDArray

EngineName = Literal["SIFT", "ORB", "SuperPoint+LightGlue"]
FloatArray = NDArray[np.float32]
ByteArray = NDArray[np.uint8]
DescriptorArray = NDArray[np.float32] | NDArray[np.uint8]
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
    descriptors: DescriptorArray | None
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
    image_loading_ms: float
    extraction_reference_ms: float
    extraction_target_ms: float
    matching_ms: float
    geometry_ms: float
    total_ms: float


@dataclass(frozen=True)
class AnalysisSettings:
    ratio_threshold: float = 0.75
    ransac_threshold: float = 4.0
    show_match_lines: bool = True
    show_inliers: bool = True
    show_outliers: bool = True
    show_keypoints: bool = False
    show_geometry: bool = True

    def __post_init__(self) -> None:
        if not isfinite(self.ratio_threshold) or not 0 < self.ratio_threshold < 1:
            raise ValueError("Ratio threshold must be finite and between zero and one.")
        if not isfinite(self.ransac_threshold) or self.ransac_threshold <= 0:
            raise ValueError("RANSAC threshold must be finite and positive.")


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
    settings: AnalysisSettings
    engine_configuration: dict[str, object]
    reference_image: NDArray[np.uint8]
    target_image: NDArray[np.uint8]


@dataclass(frozen=True)
class ComparisonResult:
    sift: AnalysisResult
    orb: AnalysisResult
