"""End-to-end classical image registration pipeline."""

from __future__ import annotations

from pathlib import Path
from time import perf_counter

import cv2
import numpy as np

from visor.engines import ORBFeatureEngine, SIFTFeatureEngine
from visor.geometry import estimate_homography
from visor.matching import match_features
from visor.models import AnalysisResult, EngineName, PerformanceMetrics


def _read_image(path: Path) -> np.ndarray:
    try:
        encoded = np.fromfile(path, dtype=np.uint8)
    except OSError as exc:
        raise ValueError(f"Could not read image: {path.name}") from exc
    image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    if image is None or image.size == 0:
        raise ValueError(f"Could not decode image: {path.name}")
    return image


def analyze(reference_path: Path, target_path: Path, engine_name: EngineName) -> AnalysisResult:
    total_start = perf_counter()
    reference_image = _read_image(reference_path)
    target_image = _read_image(target_path)
    reference_gray = cv2.cvtColor(reference_image, cv2.COLOR_BGR2GRAY)
    target_gray = cv2.cvtColor(target_image, cv2.COLOR_BGR2GRAY)
    engine = SIFTFeatureEngine() if engine_name == "SIFT" else ORBFeatureEngine()
    reference_features = engine.extract(reference_gray)
    target_features = engine.extract(target_gray)
    match_set = match_features(reference_features, target_features, engine_name)
    geometry, geometry_ms = estimate_homography(
        reference_features, target_features, match_set,
        (reference_image.shape[1], reference_image.shape[0]),
    )
    draw_matches = [
        cv2.DMatch(m.query_index, m.train_index, m.distance) for m in match_set.matches
    ]
    matches_image = cv2.drawMatches(
        reference_image, [cv2.KeyPoint(k.x, k.y, k.size, k.angle, k.response, k.octave, k.class_id) for k in reference_features.keypoints],
        target_image, [cv2.KeyPoint(k.x, k.y, k.size, k.angle, k.response, k.octave, k.class_id) for k in target_features.keypoints],
        draw_matches, None, matchColor=(75, 190, 130), singlePointColor=(130, 145, 160),
        flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS,
    )
    localization_image = target_image.copy()
    warped_image = None
    if geometry.valid and geometry.projected_corners:
        polygon = np.round(np.asarray(geometry.projected_corners)).astype(np.int32).reshape(-1, 1, 2)
        cv2.polylines(localization_image, [polygon], True, (64, 210, 146), 3, cv2.LINE_AA)
        if geometry.center:
            cv2.circle(localization_image, tuple(round(v) for v in geometry.center), 6, (50, 180, 255), -1, cv2.LINE_AA)
        # H maps reference coordinates into target coordinates; invert it to rectify target into reference dimensions.
        warped_image = cv2.warpPerspective(
            target_image, np.linalg.inv(geometry.homography),
            (reference_image.shape[1], reference_image.shape[0]),
        )
    total_ms = (perf_counter() - total_start) * 1000
    performance = PerformanceMetrics(
        reference_features.extraction_ms, target_features.extraction_ms,
        match_set.duration_ms, geometry_ms, total_ms,
    )
    return AnalysisResult(
        engine_name, reference_path, target_path,
        (reference_image.shape[1], reference_image.shape[0]),
        (target_image.shape[1], target_image.shape[0]), reference_features, target_features,
        match_set, geometry, performance, matches_image, localization_image, warped_image,
    )

