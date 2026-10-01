"""Frozen SIFT/ORB baseline — fails on any drift in the classical pipeline.

These goldens were recorded from the deterministic synthetic pair in
tests/data/golden_*.png. New engines/matchers must not change these numbers
when default settings are used.
"""

from __future__ import annotations

import json
from pathlib import Path

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
    assert abs(result.geometry.inlier_ratio - expected["ratio"]) < 1e-4
    if expected["h00"] is not None:
        assert result.geometry.homography is not None
        assert abs(float(result.geometry.homography[0, 0]) - expected["h00"]) < 1e-3


def test_sift_baseline_frozen():
    _check("SIFT")


def test_orb_baseline_frozen():
    _check("ORB")
