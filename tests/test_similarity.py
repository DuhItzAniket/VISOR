"""Similarity estimates ride along with every analysis result."""

from __future__ import annotations

from pathlib import Path

from visor.exporting import analysis_document
from visor.pipeline import analyze

DATA = Path(__file__).parent / "data"


def test_similarity_present_on_valid_geometry():
    result = analyze(DATA / "golden_reference.png", DATA / "golden_target.png", "SIFT")  # type: ignore[arg-type]
    assert result.geometry.valid
    assert result.similarity is not None
    # Golden pair is near-translation: scale ~1, rotation near 0.
    assert abs(result.similarity.scale - 1.0) < 0.05
    assert abs(result.similarity.rotation_deg) < 5.0
    assert abs(result.similarity.translate_x - 22.0) < 8.0
    assert "planar" in result.similarity.note


def test_similarity_exported_in_json_document():
    result = analyze(DATA / "golden_reference.png", DATA / "golden_target.png", "ORB")  # type: ignore[arg-type]
    doc = analysis_document(result)
    estimates = doc["geometry"]["similarity_estimates"]
    assert estimates is not None
    assert estimates["scope"].startswith("planar-scene")
    assert isinstance(estimates["is_similarity"], bool)


def test_similarity_none_when_geometry_invalid(tmp_path):
    import cv2
    import numpy as np

    blank = np.zeros((100, 100, 3), dtype=np.uint8)
    ref, tgt = tmp_path / "a.png", tmp_path / "b.png"
    cv2.imwrite(str(ref), blank)
    cv2.imwrite(str(tgt), blank)
    result = analyze(ref, tgt, "SIFT")
    assert not result.geometry.valid
    assert result.similarity is None
    assert analysis_document(result)["geometry"]["similarity_estimates"] is None
