"""Estimator-independent validation of a planar transform and its support."""

from __future__ import annotations

import cv2
import numpy as np
from numpy.typing import NDArray

from visor.models import GeometryResult


def failed_geometry(message: str, count: int) -> GeometryResult:
    """Represent an unsuccessful fit without inventing a transform or residual."""
    return GeometryResult(False, message, None, (), 0, count, 0.0, None, (), None)


def validate_planar_fit(
    matrix: NDArray | None,
    mask: NDArray | None,
    source: NDArray,
    target: NDArray,
    reference_size: tuple[int, int],
    target_size: tuple[int, int] | None,
    label: str,
    required: int = 4,
) -> GeometryResult:
    """Accept only supported, finite projections with real target overlap.

    The estimator's inlier mask is preserved. Residuals are measured from the
    indexed correspondences; geometric validity is not a detection probability.
    """
    count = len(source)
    if matrix is None or mask is None:
        return failed_geometry(f"{label} could not find a stable transform.", count)
    h = np.asarray(matrix, dtype=np.float64)
    if h.shape != (3, 3) or not np.isfinite(h).all():
        return failed_geometry(f"{label}: non-finite or malformed transform.", count)
    if np.asarray(mask).size != count:
        return failed_geometry(f"{label}: invalid inlier mask length.", count)
    try:
        if np.linalg.cond(h) > 1e12:
            return failed_geometry(f"{label}: numerically degenerate transform.", count)
    except np.linalg.LinAlgError:
        return failed_geometry(f"{label}: singular transform.", count)

    inliers = tuple(bool(value) for value in np.asarray(mask).ravel())
    inlier_count = sum(inliers)
    ratio = inlier_count / count if count else 0.0

    def reject(message: str, residual: float | None = None) -> GeometryResult:
        return GeometryResult(
            False, f"{label}: {message}", None, inliers, inlier_count,
            count - inlier_count, ratio, residual, (), None,
        )

    if inlier_count < required:
        return reject(f"at least {required} inliers are required.")
    selected = np.asarray(inliers, dtype=bool)
    for points in (source, target):
        support = np.asarray(points, dtype=np.float32).reshape(-1, 2)[selected]
        if not np.isfinite(support).all() or abs(cv2.contourArea(cv2.convexHull(support))) < 1e-6:
            return reject("degenerate inlier support.")

    width, height = reference_size
    if width < 2 or height < 2:
        return reject("reference image has no projectable area.")
    corners = np.array([[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]], dtype=np.float64)
    denominators = np.column_stack((corners, np.ones(4))) @ h[2]
    # An affine function reaches its extrema on corners. Different signs mean
    # the projective horizon crosses the reference, even if corners look finite.
    tolerance = 1e-10 * max(float(np.max(np.abs(denominators))), float(np.finfo(float).tiny))
    if not (np.all(denominators > tolerance) or np.all(denominators < -tolerance)):
        return reject("projective horizon crosses the reference image.")

    projected = cv2.perspectiveTransform(corners.reshape(-1, 1, 2), h).reshape(-1, 2)
    if not np.isfinite(projected).all() or np.max(np.abs(projected)) > np.iinfo(np.int32).max / 4:
        return reject("non-finite or unrenderable projected corners.")
    contour = projected.astype(np.float32).reshape(-1, 1, 2)
    if abs(cv2.contourArea(contour)) < 1.0 or not cv2.isContourConvex(contour):
        return reject("degenerate projected reference polygon.")
    if target_size is not None:
        tw, th = target_size
        if tw < 2 or th < 2:
            return reject("target image has no projectable area.")
        target_polygon = np.array([[0, 0], [tw - 1, 0], [tw - 1, th - 1], [0, th - 1]], dtype=np.float32)
        overlap, _ = cv2.intersectConvexConvex(contour, target_polygon)
        if overlap <= 0:
            return reject("projected reference is completely outside the target image.")

    projected_support = cv2.perspectiveTransform(np.asarray(source, dtype=np.float64), h)
    errors = np.linalg.norm(projected_support - np.asarray(target, dtype=np.float64), axis=2).ravel()
    if not np.isfinite(errors[selected]).all():
        return reject("non-finite inlier reprojection residual.")
    residual = float(np.mean(errors[selected]))
    reference_center = np.array([[[(width - 1) / 2, (height - 1) / 2]]], dtype=np.float64)
    center = cv2.perspectiveTransform(reference_center, h).reshape(2)
    return GeometryResult(
        True, f"{label} estimated under a planar-scene assumption.", h, inliers,
        inlier_count, count - inlier_count, ratio, residual,
        tuple((float(point[0]), float(point[1])) for point in projected),
        (float(center[0]), float(center[1])),
    )
