"""Optional robust estimators around the frozen adaptive-RANSAC default.

:func:`estimate_with_robust_method` with ``method="RANSAC"`` delegates to the
exact ``estimate_geometry`` path the pipeline uses today. ``MAGSAC`` and
``LMEDS`` run a single-threshold fit with the same validation rules (finite
and well-conditioned matrix, convex in-bounds projection). Nothing here
changes default pipeline behavior.
"""

from __future__ import annotations

from time import perf_counter
from typing import Literal

import cv2
import numpy as np
from numpy.typing import NDArray

from visor.geometry import estimate_geometry
from visor.models import FeatureSet, GeometryResult, MatchSet, MatrixArray

RobustMethod = Literal["RANSAC", "MAGSAC", "LMEDS"]

_FLAG_FOR: dict[str, int] = {
    "RANSAC": cv2.RANSAC,
    "MAGSAC": cv2.USAC_MAGSAC,
    "LMEDS": cv2.LMEDS,
}


def _build_result(
    matrix: MatrixArray,
    inliers: tuple[bool, ...],
    count: int,
    src: NDArray[np.float32],
    dst: NDArray[np.float32],
    corners: NDArray[np.float32],
    reference_size: tuple[int, int],
    target_size: tuple[int, int] | None,
    label: str,
) -> GeometryResult:
    inlier_count = sum(inliers)
    transformed = cv2.perspectiveTransform(src, matrix)
    errors = np.linalg.norm(transformed - dst, axis=2).ravel()
    inlier_errors = errors[np.asarray(inliers, dtype=bool)]
    reprojection = float(np.mean(inlier_errors)) if inlier_errors.size else None
    projected = cv2.perspectiveTransform(corners, matrix).reshape(-1, 2)
    contour = projected.astype(np.float32).reshape(-1, 1, 2)
    if abs(float(cv2.contourArea(contour))) < 1.0 or not cv2.isContourConvex(contour):
        return GeometryResult(False, f"{label}: degenerate projection.", None, inliers,
                              inlier_count, count - inlier_count,
                              inlier_count / count if count else 0.0, reprojection, (), None)
    points = tuple((float(p[0]), float(p[1])) for p in projected)
    center = (float(projected.mean(axis=0)[0]), float(projected.mean(axis=0)[1]))
    return GeometryResult(
        True, f"{label} estimated under a planar-scene assumption.", matrix,
        inliers, inlier_count, count - inlier_count,
        inlier_count / count if count else 0.0, reprojection, points, center,
    )


def estimate_with_robust_method(
    reference: FeatureSet,
    target: FeatureSet,
    matches: MatchSet,
    reference_size: tuple[int, int],
    ransac_threshold: float = 4.0,
    target_size: tuple[int, int] | None = None,
    method: RobustMethod = "RANSAC",
) -> tuple[GeometryResult, float]:
    if method == "RANSAC":
        return estimate_geometry(
            reference, target, matches, reference_size, ransac_threshold, target_size, "Homography"
        )
    start = perf_counter()
    count = len(matches.matches)
    if count < 4:
        result, _ = estimate_geometry(
            reference, target, matches, reference_size, ransac_threshold, target_size, "Homography"
        )
        return result, (perf_counter() - start) * 1000
    src = np.array(
        [(reference.keypoints[m.query_index].x, reference.keypoints[m.query_index].y) for m in matches.matches],
        dtype=np.float32,
    ).reshape(-1, 1, 2)
    dst = np.array(
        [(target.keypoints[m.train_index].x, target.keypoints[m.train_index].y) for m in matches.matches],
        dtype=np.float32,
    ).reshape(-1, 1, 2)
    width, height = reference_size
    corners: NDArray[np.float32] = np.array(
        [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]], dtype=np.float32,
    ).reshape(-1, 1, 2)
    matrix, mask = cv2.findHomography(src, dst, _FLAG_FOR[method], ransac_threshold)
    elapsed = (perf_counter() - start) * 1000
    if (
        matrix is None or mask is None
        or not np.isfinite(matrix).all()
        or float(np.linalg.cond(np.asarray(matrix, dtype=np.float64))) > 1e12
    ):
        result, _ = estimate_geometry(
            reference, target, matches, reference_size, ransac_threshold, target_size, "Homography"
        )
        return result, elapsed
    matrix64 = np.asarray(matrix, dtype=np.float64)
    inliers = tuple(bool(v) for v in np.asarray(mask).ravel())
    if sum(inliers) < 4:
        result, _ = estimate_geometry(
            reference, target, matches, reference_size, ransac_threshold, target_size, "Homography"
        )
        return result, elapsed
    return _build_result(matrix64, inliers, count, src, dst, corners,
                         reference_size, target_size, method), elapsed
