"""Adversarial regressions for false-success and inconsistent estimator results."""

import cv2
import numpy as np
import pytest

from visor.geometry import estimate_homography
from visor.geometry_robust import estimate_with_robust_method
from visor.geometry_validation import validate_planar_fit
from visor.models import DescriptorInfo, FeatureSet, KeypointInfo, MatchInfo, MatchSet


def correspondences():
    source = np.array([[5, 5], [90, 5], [90, 90], [5, 90], [40, 55], [65, 45]], dtype=np.float32).reshape(-1, 1, 2)
    target = source + np.array([10, 8], dtype=np.float32)

    def features(points):
        return FeatureSet(
            tuple(KeypointInfo(float(x), float(y), 1, 0, 1, 0, -1) for x, y in points.reshape(-1, 2)),
            None, DescriptorInfo(len(points), 128, "FLOAT32", 0, "L2"), 0,
        )

    matches = MatchSet(tuple(MatchInfo(i, i, 1, 0.1) for i in range(len(source))), 6, 6, "BF", "ratio", 0.75, 0)
    return features(source), features(target), matches, source, target


@pytest.mark.parametrize("method", ["RANSAC", "MAGSAC", "LMEDS"])
def test_failed_solver_never_manufactures_translation_success(monkeypatch, method):
    ref, tgt, matches, _, _ = correspondences()
    monkeypatch.setattr(cv2, "findHomography", lambda *args, **kwargs: (None, None))
    result, _ = estimate_with_robust_method(ref, tgt, matches, (100, 100), method=method)
    assert not result.valid
    assert result.homography is None
    assert result.reprojection_error_px is None
    assert result.inlier_count == 0


@pytest.mark.parametrize("method", ["RANSAC", "MAGSAC", "LMEDS"])
def test_every_estimator_rejects_projection_outside_target(monkeypatch, method):
    ref, tgt, matches, _, _ = correspondences()
    matrix = np.array([[1, 0, 500], [0, 1, 500], [0, 0, 1]], dtype=float)
    monkeypatch.setattr(cv2, "findHomography", lambda *args, **kwargs: (matrix, np.ones((6, 1))))
    result, _ = estimate_with_robust_method(ref, tgt, matches, (100, 100), target_size=(100, 100), method=method)
    assert not result.valid
    assert "outside the target" in result.message


def test_failed_optional_method_does_not_invoke_ransac(monkeypatch):
    ref, tgt, matches, _, _ = correspondences()
    flags = []

    def fail(source, target, flag, threshold):
        flags.append(flag)
        return None, None

    monkeypatch.setattr(cv2, "findHomography", fail)
    result, _ = estimate_with_robust_method(ref, tgt, matches, (100, 100), method="LMEDS")
    assert not result.valid
    assert flags == [cv2.LMEDS]


def test_horizon_crossing_is_rejected_even_with_finite_corners():
    _, _, _, source, target = correspondences()
    matrix = np.array([[1, 0, 0], [0, 1, 0], [-0.02, 0, 1]], dtype=float)
    result = validate_planar_fit(matrix, np.ones((6, 1)), source, target, (100, 100), None, "test")
    assert not result.valid
    assert "horizon" in result.message


def test_polygon_overlap_rejects_bounding_box_only_overlap():
    _, _, _, source, _ = correspondences()
    # Triangle-like placement with a bounding box that overlaps the target,
    # while the transformed square lies entirely above/right of its corner.
    matrix = np.array([[1, 1, 60], [-1, 1, -60], [0, 0, 1]], dtype=float)
    target = cv2.perspectiveTransform(source, matrix)
    result = validate_planar_fit(matrix, np.ones((6, 1)), source, target, (100, 100), (100, 100), "test")
    assert not result.valid


def test_center_is_projected_reference_center_not_average_of_projected_corners():
    _, _, _, source, _ = correspondences()
    matrix = np.array([[1, 0.1, 10], [0.05, 1, 8], [0.005, 0.001, 1]], dtype=float)
    target = cv2.perspectiveTransform(source, matrix)
    result = validate_planar_fit(matrix, np.ones((6, 1)), source, target, (100, 100), (200, 200), "test")
    expected = cv2.perspectiveTransform(np.array([[[49.5, 49.5]]]), matrix).reshape(2)
    assert result.valid
    assert np.allclose(result.center, expected)
    assert not np.allclose(result.center, np.mean(result.projected_corners, axis=0))
    assert result.reprojection_error_px < 1e-4


def test_mask_and_collinear_support_fail_validation():
    _, _, _, source, target = correspondences()
    result = validate_planar_fit(np.eye(3), np.ones((3, 1)), source, target, (100, 100), None, "test")
    assert not result.valid
    line = np.array([[[i, i]] for i in range(6)], dtype=float)
    result = validate_planar_fit(np.eye(3), np.ones((6, 1)), line, line, (100, 100), None, "test")
    assert not result.valid


def test_actual_collinear_correspondences_fail_without_mocking():
    ref, tgt, matches, _, _ = correspondences()
    points = tuple(KeypointInfo(float(i), float(i), 1, 0, 1, 0, -1) for i in range(6))
    ref = FeatureSet(points, None, ref.descriptor_info, 0)
    tgt = FeatureSet(points, None, tgt.descriptor_info, 0)
    result, _ = estimate_homography(ref, tgt, matches, (100, 100))
    assert not result.valid
