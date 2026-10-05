"""DISK+LightGlue and SIFT+LightGlue reuse the installed lightglue package."""

import cv2
import numpy as np
import pytest

from visor.learned_extra import (
    DISKLightGlueEngine,
    GenericLightGlueConfiguration,
    SIFTLightGlueEngine,
    is_disk_available,
)

pytestmark = pytest.mark.skipif(
    not is_disk_available(),
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


def test_disk_extract_returns_feature_set():
    engine = DISKLightGlueEngine(GenericLightGlueConfiguration(max_keypoints=256, use_cuda=False))
    result = engine.extract(_textured_gray())
    assert result.descriptor_info.dtype == "FLOAT32"
    assert len(result.keypoints) > 0
    assert result.descriptors is not None


def test_disk_lightglue_matches_identical_images():
    engine = DISKLightGlueEngine(GenericLightGlueConfiguration(max_keypoints=256, use_cuda=False))
    gray = _textured_gray(seed=3)
    _, _, matches = engine.extract_and_match(gray, gray)
    assert matches.shape[1] == 2
    assert len(matches) > 5


def test_sift_lightglue_matches_identical_images():
    engine = SIFTLightGlueEngine(GenericLightGlueConfiguration(max_keypoints=256, use_cuda=False))
    gray = _textured_gray(seed=4)
    _, _, matches = engine.extract_and_match(gray, gray)
    assert matches.shape[1] == 2
    assert len(matches) > 5


def test_disk_pipeline_integration(textured_pair):
    from visor.pipeline import analyze
    reference, target, _, _, _ = textured_pair
    result = analyze(reference, target, "DISK+LightGlue")  # type: ignore[arg-type]
    assert result.engine == "DISK+LightGlue"
    assert result.match_set.matcher == "LightGlue"


def test_generic_config_rejects_invalid():
    with pytest.raises(ValueError, match="positive"):
        GenericLightGlueConfiguration(max_keypoints=0)
