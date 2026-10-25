"""Optional estimators with shared validation and no silent method fallback."""

from __future__ import annotations

from dataclasses import replace
from math import isfinite
from time import perf_counter
from typing import Literal

import cv2
import numpy as np

from visor.geometry import estimate_geometry
from visor.geometry_validation import failed_geometry, validate_planar_fit
from visor.models import FeatureSet, GeometryProvenance, GeometryResult, MatchSet

RobustMethod = Literal["RANSAC", "MAGSAC", "LMEDS"]


def estimate_with_robust_method(
    reference: FeatureSet,
    target: FeatureSet,
    matches: MatchSet,
    reference_size: tuple[int, int],
    ransac_threshold: float = 4.0,
    target_size: tuple[int, int] | None = None,
    method: RobustMethod = "RANSAC",
) -> tuple[GeometryResult, float]:
    if method not in ("RANSAC", "MAGSAC", "LMEDS"):
        raise ValueError(f"Unsupported robust estimator: {method!r}.")
    if not isfinite(ransac_threshold) or ransac_threshold <= 0:
        raise ValueError("RANSAC threshold must be finite and positive.")
    if method == "RANSAC":
        return estimate_geometry(
            reference, target, matches, reference_size, ransac_threshold, target_size, "Homography",
        )
    start = perf_counter()
    count = len(matches.matches)
    provenance = GeometryProvenance(
        method, None, "Homography", "upper_bound" if method == "MAGSAC" else "not_used",
        ransac_threshold,
    )
    if count < 4:
        result = failed_geometry(f"At least 4 good matches are required for {method} homography.", count)
        return replace(result, provenance=provenance), (perf_counter() - start) * 1000
    source = np.array(
        [(reference.keypoints[m.query_index].x, reference.keypoints[m.query_index].y) for m in matches.matches],
        dtype=np.float32,
    ).reshape(-1, 1, 2)
    target_points = np.array(
        [(target.keypoints[m.train_index].x, target.keypoints[m.train_index].y) for m in matches.matches],
        dtype=np.float32,
    ).reshape(-1, 1, 2)
    flag = cv2.USAC_MAGSAC if method == "MAGSAC" else cv2.LMEDS
    matrix, mask = cv2.findHomography(source, target_points, flag, ransac_threshold)
    result = validate_planar_fit(matrix, mask, source, target_points, reference_size, target_size, method)
    result = replace(result, provenance=replace(
        provenance, executed_method=method,
        effective_threshold_px=ransac_threshold if method == "MAGSAC" else None,
        attempted_thresholds_px=(ransac_threshold,) if method == "MAGSAC" else (),
    ))
    return result, (perf_counter() - start) * 1000
