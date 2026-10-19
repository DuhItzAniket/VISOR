"""Windows/OpenCV snapshot regressions plus portable known-transform contracts.

These goldens were recorded from the deterministic synthetic pair in
tests/data/golden_*.png. New engines/matchers must not change these numbers
when default settings are used on the recorded Windows/OpenCV build. Native
runner evidence shows these counts are not portable to ARM/macOS or Linux.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

from visor.models import AnalysisSettings
from visor.pipeline import analyze

GOLDEN = json.loads((Path(__file__).parent / "data" / "golden_classical.json").read_text())


def _check(engine: str) -> None:
    ref = Path(__file__).parent / "data" / "golden_reference.png"
    tgt = Path(__file__).parent / "data" / "golden_target.png"
    result = analyze(ref, tgt, engine, AnalysisSettings())  # type: ignore[arg-type]
    expected = GOLDEN[engine]
    assert len(result.reference_features.keypoints) == expected["ref_kp"]
    assert len(result.target_features.keypoints) == expected["tgt_kp"]
    assert result.match_set.good_count == expected["good"]
    assert result.geometry.inlier_count == expected["inliers"]
    assert result.geometry.valid == expected["valid"]
    assert abs(result.geometry.inlier_ratio - expected["ratio"]) < 5e-3
    if expected["h00"] is not None:
        assert result.geometry.homography is not None
        assert abs(float(result.geometry.homography[0, 0]) - expected["h00"]) < 1e-3


@pytest.mark.skipif(sys.platform != "win32" or cv2.__version__ != "4.11.0", reason="Exact snapshot is Windows/OpenCV 4.11 only")
def test_sift_baseline_frozen():
    _check("SIFT")


@pytest.mark.skipif(sys.platform != "win32" or cv2.__version__ != "4.11.0", reason="Exact snapshot is Windows/OpenCV 4.11 only")
def test_orb_baseline_frozen():
    _check("ORB")


@pytest.mark.parametrize("engine", ["SIFT", "ORB"])
def test_portable_registration_matches_known_transform(textured_pair, engine):
    reference, target, image, _, truth = textured_pair
    result = analyze(reference, target, engine)
    assert result.geometry.valid
    assert result.geometry.homography is not None
    height, width = image.shape[:2]
    corners = np.array([[[0, 0]], [[width - 1, 0]], [[width - 1, height - 1]], [[0, height - 1]]], dtype=np.float64)
    expected = cv2.perspectiveTransform(corners, truth)
    actual = cv2.perspectiveTransform(corners, result.geometry.homography)
    # This fixture is a textured planar image with a mild known warp. Require
    # sub-3-pixel maximum corner error, independently of the fitted residual.
    assert float(np.max(np.linalg.norm(actual - expected, axis=2))) < 3.0
    assert result.geometry.inlier_count >= 20
    assert len(result.geometry.inlier_mask) == result.match_set.good_count
    assert sum(result.geometry.inlier_mask) == result.geometry.inlier_count
