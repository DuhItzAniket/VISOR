"""Robust estimators and decomposition stay consistent with the frozen path."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest

from visor.engines import ORBFeatureEngine, SIFTFeatureEngine
from visor.geometry import estimate_homography
from visor.geometry_decompose import (
    classify_failure,
    decompose_homography_estimate,
    reprojection_histogram,
)
from visor.geometry_robust import estimate_with_robust_method
from visor.matching import match_features


def _sets(engine: str = "SIFT"):
    ref = cv2.imread(str(Path(__file__).parent / "data" / "golden_reference.png"), cv2.IMREAD_GRAYSCALE)
    tgt = cv2.imread(str(Path(__file__).parent / "data" / "golden_target.png"), cv2.IMREAD_GRAYSCALE)
    extractor = SIFTFeatureEngine() if engine == "SIFT" else ORBFeatureEngine()
    ref_set, tgt_set = extractor.extract(ref), extractor.extract(tgt)
    return ref_set, tgt_set, match_features(ref_set, tgt_set, engine)


def test_ransac_delegates_to_frozen_geometry():
    ref, tgt, matches = _sets()
    size = (560, 420)
    expected, _ = estimate_homography(ref, tgt, matches, size)
    actual, _ = estimate_with_robust_method(ref, tgt, matches, size, method="RANSAC")
    assert actual.valid == expected.valid
    assert actual.inlier_count == expected.inlier_count


@pytest.mark.parametrize("method", ["MAGSAC", "LMEDS"])
def test_alternative_estimators_produce_valid_geometry(method):  # type: ignore[no-untyped-def]
    ref, tgt, matches = _sets()
    result, ms = estimate_with_robust_method(ref, tgt, matches, (560, 420), method=method)  # type: ignore[arg-type]
    assert ms >= 0
    assert result.valid  # synthetic pair localizes under every robust flag
    assert result.inlier_count >= 4


def test_decompose_recovers_known_similarity():
    angle, scale = 17.0, 0.9
    rad = np.deg2rad(angle)
    known = np.array([
        [scale * np.cos(rad), -scale * np.sin(rad), 22.0],
        [scale * np.sin(rad), scale * np.cos(rad), 17.0],
        [0, 0, 1],
    ])
    estimate = decompose_homography_estimate(known)
    assert estimate.is_similarity
    assert abs(abs(estimate.rotation_deg) - angle) < 0.5
    assert abs(estimate.scale - scale) < 1e-6
    assert "planar" in estimate.note


def test_decompose_flags_perspective_as_non_similarity():
    perspective = np.array([[1.2, 0.3, 5.0], [0.1, 0.9, 3.0], [0.0004, -0.0002, 1.0]])
    assert not decompose_homography_estimate(perspective).is_similarity


def test_histogram_and_failure_taxonomy():
    edges, counts = reprojection_histogram(np.array([0.1, 0.2, 0.3, 5.0]), bins=2)
    assert len(edges) == 3 and sum(counts) == 4
    assert reprojection_histogram([]) == ((), ())
    assert classify_failure("At least 4 good matches are required for homography.") == "too_few_matches"
    assert classify_failure("The projected reference is completely outside the target image.") == "outside_target"
    assert classify_failure("RANSAC could not find a stable homography transform.") == "unstable_fit"
    assert classify_failure("Homography estimated with adaptive RANSAC under a planar-scene assumption.") == "ok"
