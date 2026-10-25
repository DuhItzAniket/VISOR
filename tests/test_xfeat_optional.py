"""Real cached XFeat inference; absent source/weights are skipped explicitly."""

import cv2
import numpy as np
import pytest

from visor.learned_engines import XFeatConfiguration, XFeatEngine, is_xfeat_available
from visor.model_runtime import XFEAT_REVISION
from visor.pipeline import analyze

pytestmark = [pytest.mark.optional_model, pytest.mark.skipif(not is_xfeat_available(), reason="Pinned XFeat cache absent")]


def test_xfeat_cpu_extract_and_self_match(textured_pair):
    _, _, reference, _, _ = textured_pair
    gray = cv2.cvtColor(reference, cv2.COLOR_BGR2GRAY)
    engine = XFeatEngine(XFeatConfiguration(max_keypoints=512, use_cuda=False))
    result = engine.match_pair(gray, gray)
    assert result.device == "cpu" and engine._extractor.dev.type == "cpu"
    assert result.reference.descriptor_info.dimensions == 64
    assert result.match_set.good_count > 10
    assert result.reference.extraction_ms > 0 and result.match_set.duration_ms > 0
    assert all(m.distance is not None and m.confidence is None for m in result.match_set.matches)


def test_xfeat_known_warp_pipeline(textured_pair):
    reference, target, _, _, expected_h = textured_pair
    result = analyze(reference, target, "XFeat", xfeat_config=XFeatConfiguration(max_keypoints=512, use_cuda=False),
                     robust_method="MAGSAC")
    assert result.geometry.valid
    assert result.engine_configuration["upstream_revision"] == XFEAT_REVISION
    corners = np.array([[0, 0], [560, 0], [560, 420], [0, 420]], np.float32).reshape(-1, 1, 2)
    expected = cv2.perspectiveTransform(corners, expected_h)
    actual = cv2.perspectiveTransform(corners, result.geometry.homography)
    assert np.linalg.norm(actual - expected, axis=2).max() < 3
