"""Robust planar homography estimation and localization."""

from __future__ import annotations

from time import perf_counter

import cv2
import numpy as np

from visor.models import FeatureSet, GeometryResult, MatchSet


def estimate_homography(
    reference: FeatureSet,
    target: FeatureSet,
    matches: MatchSet,
    reference_size: tuple[int, int],
    ransac_threshold: float = 4.0,
) -> tuple[GeometryResult, float]:
    start = perf_counter()
    count = len(matches.matches)
    if count < 4:
        return GeometryResult(False, "At least four good matches are required for homography.", None, (), 0, count, 0.0, None, (), None), (perf_counter() - start) * 1000
    src = np.float32(
        [(reference.keypoints[m.query_index].x, reference.keypoints[m.query_index].y) for m in matches.matches]
    ).reshape(-1, 1, 2)
    dst = np.float32(
        [(target.keypoints[m.train_index].x, target.keypoints[m.train_index].y) for m in matches.matches]
    ).reshape(-1, 1, 2)
    matrix, mask = cv2.findHomography(src, dst, cv2.RANSAC, ransac_threshold)
    if matrix is None or mask is None or not np.isfinite(matrix).all():
        return GeometryResult(False, "RANSAC could not find a stable homography.", None, (), 0, count, 0.0, None, (), None), (perf_counter() - start) * 1000
    if np.linalg.cond(matrix) > 1e12:
        return GeometryResult(False, "The estimated homography is numerically degenerate.", None, (), 0, count, 0.0, None, (), None), (perf_counter() - start) * 1000
    inliers = tuple(bool(value) for value in mask.ravel())
    inlier_count = sum(inliers)
    ratio = inlier_count / count if count else 0.0
    projected = cv2.perspectiveTransform(src, matrix)
    errors = np.linalg.norm(cv2.perspectiveTransform(src, matrix) - dst, axis=2).ravel()
    inlier_errors = errors[np.asarray(inliers, dtype=bool)]
    reprojection = float(np.mean(inlier_errors)) if inlier_errors.size else None
    width, height = reference_size
    corners = np.float32([[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]]).reshape(-1, 1, 2)
    projected_corners = cv2.perspectiveTransform(corners, matrix).reshape(-1, 2)
    polygon_area = abs(float(cv2.contourArea(projected_corners.astype(np.float32))))
    if not np.isfinite(projected_corners).all() or inlier_count < 4 or polygon_area < 1.0:
        return GeometryResult(False, "The estimated transform is degenerate.", None, inliers, inlier_count, count - inlier_count, ratio, reprojection, (), None), (perf_counter() - start) * 1000
    points = tuple((float(p[0]), float(p[1])) for p in projected_corners)
    center_array = projected_corners.mean(axis=0)
    result = GeometryResult(
        True, "Planar homography estimated with RANSAC.", matrix.astype(np.float64), inliers,
        inlier_count, count - inlier_count, ratio, reprojection, points,
        (float(center_array[0]), float(center_array[1])),
    )
    return result, (perf_counter() - start) * 1000
