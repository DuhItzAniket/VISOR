"""Camera calibration and PnP helpers validated on synthetic projections."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest

from visor.calibration import (
    calibrate_camera,
    calibrate_from_chessboard_images,
    solve_pnp_pose,
)


def _chessboard_object_points(cols: int = 9, rows: int = 6, square: float = 25.0) -> np.ndarray:
    xs, ys = np.meshgrid(np.arange(cols), np.arange(rows))
    grid = np.stack([xs.ravel(), ys.ravel(), np.zeros(cols * rows)], axis=1).astype(np.float64)
    grid[:, :2] *= square
    return grid


def _project(points_3d: np.ndarray, rvec: np.ndarray, tvec: np.ndarray,
             camera: np.ndarray, dist: np.ndarray) -> np.ndarray:
    projected, _ = cv2.projectPoints(points_3d, rvec, tvec, camera, dist)
    return projected.reshape(-1, 2)


def test_calibrate_camera_recovers_known_intrinsics():
    rng = np.random.default_rng(7)
    camera = np.array([[800.0, 0.0, 320.0], [0.0, 800.0, 240.0], [0.0, 0.0, 1.0]])
    dist = np.zeros(5)
    obj = _chessboard_object_points()
    object_samples, image_samples = [], []
    for _ in range(8):
        rvec = rng.uniform(-0.4, 0.4, size=3)
        tvec = np.array([[rng.uniform(-60, 60)], [rng.uniform(-60, 60)], [600 + rng.uniform(0, 300)]])
        image_samples.append(_project(obj, rvec, tvec, camera, dist) + rng.normal(0, 0.3, size=(obj.shape[0], 2)))
        object_samples.append(obj)
    estimated_k, _, rms = calibrate_camera(object_samples, image_samples, (640, 480))
    assert rms < 1.0
    assert abs(estimated_k[0, 0] - 800.0) < 15.0
    assert abs(estimated_k[0, 2] - 320.0) < 8.0


def test_calibrate_camera_rejects_mismatched_samples():
    obj = _chessboard_object_points()
    with pytest.raises(ValueError, match="same number of samples"):
        calibrate_camera([obj], [], (640, 480))
    with pytest.raises(ValueError, match="At least one"):
        calibrate_camera([], [], (640, 480))


def test_solve_pnp_recovers_known_pose():
    camera = np.array([[800.0, 0.0, 320.0], [0.0, 800.0, 240.0], [0.0, 0.0, 1.0]])
    obj = _chessboard_object_points()
    rvec = np.array([[0.1], [0.2], [0.05]])
    tvec = np.array([[10.0], [-20.0], [700.0]])
    image = _project(obj, rvec, tvec, camera, np.zeros(5))
    solved = solve_pnp_pose(obj, image, camera)
    assert solved is not None
    solved_rvec, solved_tvec = solved
    assert np.allclose(solved_rvec.ravel(), rvec.ravel(), atol=1e-3)
    assert np.allclose(solved_tvec.ravel(), tvec.ravel(), atol=1e-1)


def test_solve_pnp_rejects_bad_shapes():
    camera = np.eye(3)
    with pytest.raises(ValueError, match="same number of entries"):
        solve_pnp_pose(np.zeros((4, 3)), np.zeros((5, 2)), camera)


def _write_chessboard(path: Path, cols: int = 9, rows: int = 6, square: int = 40) -> None:
    board = np.full(((rows + 1) * square, (cols + 1) * square), 255, dtype=np.uint8)
    for y in range(rows + 1):
        for x in range(cols + 1):
            if (x + y) % 2 == 0:
                board[y * square:(y + 1) * square, x * square:(x + 1) * square] = 0
    cv2.imwrite(str(path), board)


def test_calibrate_from_chessboard_images(tmp_path):
    base = tmp_path / "base.png"
    _write_chessboard(base)
    board = cv2.imread(str(base), cv2.IMREAD_GRAYSCALE)
    height, width = board.shape
    rng = np.random.default_rng(3)
    for i in range(8):
        src = np.float32([[0, 0], [width, 0], [width, height], [0, height]])
        jitter = rng.uniform(-18, 18, size=(4, 2)).astype(np.float32)
        warped = cv2.warpPerspective(board, cv2.getPerspectiveTransform(src, src + jitter), (width, height))
        cv2.imwrite(str(tmp_path / f"view_{i}.png"), warped)
    camera, _dist, rms, views = calibrate_from_chessboard_images(sorted(tmp_path.glob("view_*.png")))
    assert views >= 3
    assert camera.shape == (3, 3)
    assert rms >= 0


def test_calibrate_from_images_rejects_empty_folder(tmp_path):
    with pytest.raises(ValueError, match="No usable chessboard views"):
        calibrate_from_chessboard_images(list((tmp_path).glob("*.png")))
