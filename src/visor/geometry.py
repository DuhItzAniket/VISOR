"""Robust planar homography and affine transform estimation."""

from __future__ import annotations

from dataclasses import replace
from math import isfinite
from time import perf_counter
from typing import Literal

import cv2
import numpy as np

from visor.geometry_validation import validate_planar_fit
from visor.models import FeatureSet, GeometryProvenance, GeometryResult, MatchSet

GeometryModel = Literal["Homography", "Affine partial", "Affine"]


def estimate_geometry(
    reference: FeatureSet,
    target: FeatureSet,
    matches: MatchSet,
    reference_size: tuple[int, int],
    ransac_threshold: float = 4.0,
    target_size: tuple[int, int] | None = None,
    model: GeometryModel = "Homography",
) -> tuple[GeometryResult, float]:
    start = perf_counter()
    if model not in ("Homography", "Affine partial", "Affine"):
        raise ValueError(f"Unsupported geometry model: {model!r}.")
    if not isfinite(ransac_threshold) or ransac_threshold <= 0:
        raise ValueError("RANSAC threshold must be finite and positive.")
    provenance = GeometryProvenance("RANSAC", None, model, "legacy_adaptive", ransac_threshold)
    count = len(matches.matches)
    required = 4 if model == "Homography" else 3
    if count < required:
        result = GeometryResult(
            False, f"At least {required} good matches are required for {model.lower()}.",
            None, (), 0, count, 0.0, None, (), None,
        )
        return replace(result, provenance=provenance), (perf_counter() - start) * 1000

    src = np.array(
        [(reference.keypoints[m.query_index].x, reference.keypoints[m.query_index].y) for m in matches.matches],
        dtype=np.float32,
    ).reshape(-1, 1, 2)
    dst = np.array(
        [(target.keypoints[m.train_index].x, target.keypoints[m.train_index].y) for m in matches.matches],
        dtype=np.float32,
    ).reshape(-1, 1, 2)

    thresholds = sorted({float(ransac_threshold), max(1.0, float(ransac_threshold) * 0.75), max(2.0, float(ransac_threshold) * 1.5), 10.0})
    attempted: list[float] = []
    for threshold in thresholds:
        attempted.append(threshold)
        if model == "Homography":
            estimated, mask = cv2.findHomography(src, dst, cv2.RANSAC, threshold)
            matrix = None if estimated is None else estimated
        elif model == "Affine partial":
            estimated, mask = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC, ransacReprojThreshold=threshold)
            matrix = None if estimated is None else np.vstack((estimated, [0.0, 0.0, 1.0]))
        else:
            estimated, mask = cv2.estimateAffine2D(src, dst, method=cv2.RANSAC, ransacReprojThreshold=threshold)
            matrix = None if estimated is None else np.vstack((estimated, [0.0, 0.0, 1.0]))

        result = validate_planar_fit(
            matrix, mask, src, dst, reference_size, target_size,
            f"{model} with adaptive RANSAC", required,
        )
        result = replace(result, provenance=replace(
            provenance, executed_method="RANSAC", effective_threshold_px=threshold,
            attempted_thresholds_px=tuple(attempted),
        ))
        if result.valid or "outside the target" in result.message:
            return result, (perf_counter() - start) * 1000

    # Failure must stay failure. Averaging unrelated keypoints cannot verify a
    # translation, inlier mask, or zero residual.
    return result, (perf_counter() - start) * 1000


def estimate_homography(
    reference: FeatureSet,
    target: FeatureSet,
    matches: MatchSet,
    reference_size: tuple[int, int],
    ransac_threshold: float = 4.0,
    target_size: tuple[int, int] | None = None,
) -> tuple[GeometryResult, float]:
    """Backward-compatible convenience wrapper for homography estimation."""
    return estimate_geometry(reference, target, matches, reference_size, ransac_threshold, target_size, "Homography")

