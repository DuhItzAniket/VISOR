"""Camera calibration and pose estimation utilities for non-planar scenes."""

from __future__ import annotations

from typing import Sequence

import cv2
import numpy as np
from numpy.typing import NDArray


def calibrate_camera(
    object_points: Sequence[NDArray[np.float64]] | NDArray[np.float64],
    image_points: Sequence[NDArray[np.float64]] | NDArray[np.float64],
    image_size: tuple[int, int],
    flags: int = cv2.CALIB_ZERO_TANGENT_DIST,
) -> tuple[NDArray[np.float64], NDArray[np.float64], float]:
    """Calibrate a camera from object/image correspondences.

    This helper accepts either a single point matrix or a sequence of point sets,
    and returns the intrinsic matrix, distortion coefficients, and RMS
    reprojection error.
    """
    if isinstance(object_points, np.ndarray):
        object_points = [np.asarray(object_points, dtype=np.float64).reshape(-1, 3)]
    if isinstance(image_points, np.ndarray):
        image_points = [np.asarray(image_points, dtype=np.float64).reshape(-1, 2)]

    object_list = [np.asarray(points, dtype=np.float32).reshape(-1, 3) for points in object_points]
    image_list = [np.asarray(points, dtype=np.float32).reshape(-1, 2) for points in image_points]

    if len(object_list) != len(image_list):
        raise ValueError("object_points and image_points must have the same number of samples.")
    if not object_list:
        raise ValueError("At least one calibration sample is required.")

    camera_matrix = np.eye(3, dtype=np.float64)
    dist_coeffs = np.zeros(5, dtype=np.float64)
    rms, camera_matrix, dist_coeffs, _, _ = cv2.calibrateCamera(
        object_list,
        image_list,
        image_size,
        camera_matrix,
        dist_coeffs,
        flags=flags,
    )
    return camera_matrix, dist_coeffs, float(rms)


def solve_pnp_pose(
    object_points: NDArray[np.float64],
    image_points: NDArray[np.float64],
    camera_matrix: NDArray[np.float64],
    dist_coeffs: NDArray[np.float64] | None = None,
) -> tuple[NDArray[np.float64], NDArray[np.float64]] | None:
    """Solve the 3D-to-2D pose via SOLVEPNP and return (rvec, tvec)."""
    if object_points.shape[0] != image_points.shape[0]:
        raise ValueError("object_points and image_points must have the same number of entries.")
    if object_points.shape[1] != 3:
        raise ValueError("object_points must be an array of shape (N, 3).")
    if image_points.shape[1] != 2:
        raise ValueError("image_points must be an array of shape (N, 2).")

    dist = np.zeros(5, dtype=np.float64) if dist_coeffs is None else np.asarray(dist_coeffs, dtype=np.float64)
    object_array = np.asarray(object_points, dtype=np.float64)
    image_array = np.asarray(image_points, dtype=np.float64)
    success, rvec, tvec = cv2.solvePnP(
        object_array,
        image_array,
        np.asarray(camera_matrix, dtype=np.float64),
        dist,
        flags=cv2.SOLVEPNP_ITERATIVE,
    )
    if not success:
        return None
    return rvec, tvec
