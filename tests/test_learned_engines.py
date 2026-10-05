"""Tests for the SuperPoint+LightGlue learned engine."""

import cv2
import numpy as np
import pytest

from visor.learned_engines import (
    LearnedEngineUnavailable,
    SuperPointConfiguration,
    SuperPointLightGlueEngine,
    is_learned_available,
)

pytestmark = pytest.mark.skipif(
    not is_learned_available(),
    reason="lightglue not installed",
)


def _textured_gray(seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    img = np.full((320, 480), 200, dtype=np.uint8)
    for _ in range(60):
        x, y = int(rng.integers(8, 472)), int(rng.integers(8, 312))
        cv2.circle(img, (x, y), int(rng.integers(3, 12)), int(rng.integers(30, 180)), -1)
    cv2.putText(img, "VISOR", (60, 160), cv2.FONT_HERSHEY_SIMPLEX, 3, 40, 5)
    return img


def test_superpoint_extract_returns_feature_set():
    engine = SuperPointLightGlueEngine(SuperPointConfiguration(max_keypoints=256, use_cuda=False))
    gray = _textured_gray()
    result = engine.extract(gray)
    assert result.descriptor_info.dimensions == 256
    assert result.descriptor_info.dtype == "FLOAT32"
    assert result.descriptor_info.distance == "L2"
    assert result.extraction_ms >= 0
    assert len(result.keypoints) > 0
    assert result.descriptors is not None
    assert result.descriptors.shape == (len(result.keypoints), 256)


def test_superpoint_lightglue_matches_identical_images():
    engine = SuperPointLightGlueEngine(SuperPointConfiguration(max_keypoints=256, use_cuda=False))
    gray = _textured_gray()
    ref_fs, tgt_fs, matches = engine.extract_and_match(gray, gray)
    assert len(ref_fs.keypoints) > 0
    assert len(tgt_fs.keypoints) > 0
    # Self-match should produce many correspondences
    assert matches.shape[1] == 2
    assert len(matches) > 10


def test_superpoint_lightglue_pipeline_integration(textured_pair):
    """Full pipeline with SuperPoint+LightGlue on a synthetic transformed pair."""
    from visor.pipeline import analyze
    reference, target, _, _, _ = textured_pair
    result = analyze(reference, target, "SuperPoint+LightGlue")
    assert result.engine == "SuperPoint+LightGlue"
    assert result.match_set.matcher == "LightGlue"
    assert result.match_set.good_count >= 0
    assert result.performance.total_ms > 0
    assert len(result.matches_image.shape) == 3


def test_superpoint_config_rejects_invalid_values():
    with pytest.raises(ValueError):
        SuperPointConfiguration(max_keypoints=0)
    with pytest.raises(ValueError):
        SuperPointConfiguration(detection_threshold=1.5)


def test_learned_engine_unavailable_raises_clearly(monkeypatch):
    import visor.learned_engines as le
    monkeypatch.setattr(le, "_LIGHTGLUE_AVAILABLE", False)
    with pytest.raises(LearnedEngineUnavailable):
        SuperPointLightGlueEngine()


# ---------------------------------------------------------------------------
# ALIKED + LightGlue tests
# ---------------------------------------------------------------------------

def test_aliked_extract_returns_128d_feature_set():
    from visor.learned_engines import ALIKEDConfiguration, ALIKEDLightGlueEngine
    engine = ALIKEDLightGlueEngine(ALIKEDConfiguration(max_keypoints=256, use_cuda=False))
    gray = _textured_gray(seed=1)
    result = engine.extract(gray)
    assert result.descriptor_info.dimensions == 128
    assert result.descriptor_info.dtype == "FLOAT32"
    assert result.extraction_ms >= 0
    assert len(result.keypoints) > 0


def test_aliked_lightglue_matches_identical_images():
    from visor.learned_engines import ALIKEDConfiguration, ALIKEDLightGlueEngine
    engine = ALIKEDLightGlueEngine(ALIKEDConfiguration(max_keypoints=256, use_cuda=False))
    gray = _textured_gray(seed=2)
    ref_fs, tgt_fs, matches = engine.extract_and_match(gray, gray)
    assert len(ref_fs.keypoints) > 0
    assert matches.shape[1] == 2
    assert len(matches) > 5


def test_aliked_pipeline_integration(textured_pair):
    from visor.pipeline import analyze
    reference, target, _, _, _ = textured_pair
    result = analyze(reference, target, "ALIKED+LightGlue")
    assert result.engine == "ALIKED+LightGlue"
    assert result.match_set.matcher == "LightGlue"
    assert result.performance.total_ms > 0


def test_aliked_config_rejects_invalid():
    from visor.learned_engines import ALIKEDConfiguration
    with pytest.raises(ValueError):
        ALIKEDConfiguration(max_keypoints=0)
