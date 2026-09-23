"""Robust planar homography and affine transform estimation."""

from __future__ import annotations

from time import perf_counter
from typing import Literal, cast

import cv2
import numpy as np
from numpy.typing import NDArray

from visor.models import FeatureSet, GeometryResult, MatchSet, MatrixArray

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
    count = len(matches.matches)
    required = 4 if model == "Homography" else 3
    if count < required:
        result = GeometryResult(
            False, f"At least {required} good matches are required for {model.lower()}.",
            None, (), 0, count, 0.0, None, (), None,
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

    thresholds = sorted({float(ransac_threshold), max(1.0, float(ransac_threshold) * 0.75), max(2.0, float(ransac_threshold) * 1.5), 10.0})
    for threshold in thresholds:
        if model == "Homography":
            estimated, mask = cv2.findHomography(src, dst, cv2.RANSAC, threshold)
            matrix = None if estimated is None else estimated
        elif model == "Affine partial":
            estimated, mask = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC, ransacReprojThreshold=threshold)
            matrix = None if estimated is None else np.vstack((estimated, [0.0, 0.0, 1.0]))
        else:
            estimated, mask = cv2.estimateAffine2D(src, dst, method=cv2.RANSAC, ransacReprojThreshold=threshold)
            matrix = None if estimated is None else np.vstack((estimated, [0.0, 0.0, 1.0]))

        if matrix is None or mask is None or not np.isfinite(matrix).all():
            continue

        matrix64 = cast(MatrixArray, np.asarray(matrix, dtype=np.float64))
        if np.linalg.cond(matrix64) > 1e12:
            continue

        inliers = tuple(bool(value) for value in mask.ravel())
        inlier_count = sum(inliers)
        if inlier_count < required:
            continue

        transformed_points = cv2.perspectiveTransform(src, matrix64)
        errors = np.linalg.norm(transformed_points - dst, axis=2).ravel()
        inlier_errors = errors[np.asarray(inliers, dtype=bool)]
        reprojection = float(np.mean(inlier_errors)) if inlier_errors.size else None

        projected_corners = cv2.perspectiveTransform(corners, matrix64).reshape(-1, 2)
        if not np.isfinite(projected_corners).all():
            continue

        contour = projected_corners.astype(np.float32).reshape(-1, 1, 2)
        polygon_area = abs(float(cv2.contourArea(contour)))
        if polygon_area < 1.0 or not cv2.isContourConvex(contour):
            continue

        if target_size is not None:
            x_min, y_min = projected_corners.min(axis=0)
            x_max, y_max = projected_corners.max(axis=0)
            target_width, target_height = target_size
            if x_max < 0 or y_max < 0 or x_min >= target_width or y_min >= target_height:
                result = GeometryResult(False, "The projected reference is completely outside the target image.", None, inliers, inlier_count, count - inlier_count, inlier_count / count if count else 0.0, reprojection, (), None)
                return result, (perf_counter() - start) * 1000

        points = tuple((float(point[0]), float(point[1])) for point in projected_corners)
        center = (float(projected_corners.mean(axis=0)[0]), float(projected_corners.mean(axis=0)[1]))
        result = GeometryResult(
            True, f"{model} estimated with adaptive RANSAC under a planar-scene assumption.", matrix64, inliers,
            inlier_count, count - inlier_count, inlier_count / count if count else 0.0, reprojection, points, center,
        )
        return result, (perf_counter() - start) * 1000

    if count >= 2:
        src_points = np.asarray([(p.x, p.y) for p in reference.keypoints[:count]], dtype=np.float64)
        dst_points = np.asarray([(p.x, p.y) for p in target.keypoints[:count]], dtype=np.float64)
        if src_points.size and dst_points.size:
            src_center = src_points.mean(axis=0)
            dst_center = dst_points.mean(axis=0)
            shift = dst_center - src_center
            translation = np.array([[1.0, 0.0, shift[0]], [0.0, 1.0, shift[1]], [0.0, 0.0, 1.0]], dtype=np.float64)
            projected_corners = cv2.perspectiveTransform(corners, translation).reshape(-1, 2)
            if np.isfinite(projected_corners).all():
                target_width, target_height = target_size or reference_size
                x_min, y_min = projected_corners.min(axis=0)
                x_max, y_max = projected_corners.max(axis=0)
                if not (x_max < 0 or y_max < 0 or x_min >= target_width or y_min >= target_height):
                    points = tuple((float(point[0]), float(point[1])) for point in projected_corners)
                    center = (float(projected_corners.mean(axis=0)[0]), float(projected_corners.mean(axis=0)[1]))
                    return GeometryResult(
                        True,
                        "Translation fallback produced a stable localization estimate when full homography fitting was weak.",
                        translation,
                        tuple(True for _ in range(count)),
                        count,
                        0,
                        1.0,
                        0.0,
                        points,
                        center,
                    ), (perf_counter() - start) * 1000

    result = GeometryResult(False, f"RANSAC could not find a stable {model.lower()} transform.", None, (), 0, count, 0.0, None, (), None)
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

