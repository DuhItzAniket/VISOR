"""Reporting contracts run offline, including without torch or model weights."""

from contextlib import nullcontext
from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest

from visor import learned_pair, pipeline
from visor.engines import SIFTFeatureEngine
from visor.exporting import analysis_document
from visor.geometry import estimate_homography
from visor.geometry_robust import estimate_with_robust_method
from visor.matching import match_features
from visor.matching_strategies import MatchingOptions
from visor.models import MatchInfo, MatchSet, PairMatchResult


class Tensor:
    def __init__(self, data):
        self.data = np.asarray(data)

    def detach(self):
        return self

    def cpu(self):
        return self

    def numpy(self):
        return self.data


@pytest.fixture
def fake_lightglue(monkeypatch):
    import sys

    monkeypatch.setitem(sys.modules, "lightglue.utils", SimpleNamespace(rbd=lambda data: data))


def test_stage_timer_brackets_completed_work(monkeypatch):
    events = []
    clock = iter([10.0, 10.125])
    monkeypatch.setattr(learned_pair, "synchronize", lambda device: events.append(f"sync {device}"))
    monkeypatch.setattr(learned_pair, "perf_counter", lambda: next(clock))
    value, elapsed = learned_pair.measured("cpu", lambda: events.append("operation") or 7)
    assert value == 7 and elapsed == 125
    assert events == ["sync cpu", "operation", "sync cpu"]


def test_lightglue_scores_are_not_descriptor_distances(fake_lightglue):
    raw = {"matches": Tensor([[0, 1], [1, 0]]), "scores": Tensor([0.8, 0.7])}
    result = learned_pair.lightglue_match_set(raw, 2, 2, 0.1, 12.0)
    assert result.candidate_count is None
    assert result.duration_ms == 12.0 and result.threshold == 0.1
    assert all(match.distance is None and match.ratio is None for match in result.matches)
    assert [match.confidence for match in result.matches] == pytest.approx([0.8, 0.7])


@pytest.mark.parametrize("raw", [
    {"matches": Tensor([[0, 2]])},
    {"matches": Tensor([[-1, 0]])},
    {"matches": Tensor([[0.5, 0.0]])},
    {"matches": Tensor([[0, 0]]), "scores": Tensor([float("nan")])},
    {"matches": Tensor([[0, 0]]), "scores": Tensor([1.1])},
])
def test_invalid_learned_match_output_is_rejected(fake_lightglue, raw):
    with pytest.raises(ValueError):
        learned_pair.lightglue_match_set(raw, 2, 2, 0.1, 1.0)


def test_unavailable_keypoint_metadata_is_explicit(fake_lightglue):
    features = learned_pair.feature_set({
        "keypoints": Tensor([[2, 3]]), "descriptors": Tensor(np.ones((1, 128))),
    }, 7.5, 128)
    assert features.extraction_ms == 7.5
    assert features.keypoint_metadata == ()


def test_pair_result_preserves_separate_timing_and_scores(fake_lightglue, monkeypatch):
    import sys

    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(inference_mode=nullcontext))
    raw = {"keypoints": Tensor([[2, 3]]), "descriptors": Tensor(np.ones((1, 128)))}
    ref = learned_pair.feature_set(raw, 5.0, 128)
    tgt = replace(ref, extraction_ms=9.0)
    engine = learned_pair.LightGluePairEngine()
    engine._device = "cpu"
    outputs = iter([(raw, ref), (raw, tgt)])
    monkeypatch.setattr(engine, "_extract_raw", lambda gray: next(outputs))
    engine._matcher = lambda data: {"matches": Tensor([[0, 0]]), "scores": Tensor([0.9])}
    monkeypatch.setattr(learned_pair, "measured", lambda device, fn: (fn(), 17.0))
    result = engine.match_pair(np.zeros((4, 4), np.uint8), np.zeros((4, 4), np.uint8))
    assert result.reference.extraction_ms == 5 and result.target.extraction_ms == 9
    assert result.match_set.duration_ms == 17
    assert result.match_set.matches[0].confidence == 0.9


@pytest.mark.parametrize("method", ["RANSAC", "MAGSAC", "LMEDS"])
def test_learned_pipeline_honors_estimator_and_reports_runtime(textured_pair, monkeypatch, method):
    reference, target, image, warped, _ = textured_pair
    import cv2

    engine = SIFTFeatureEngine()
    ref = engine.extract(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY))
    tgt = engine.extract(cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY))
    matched = match_features(ref, tgt, "SIFT")
    matches = MatchSet(tuple(MatchInfo(m.query_index, m.train_index, None, None, 0.9) for m in matched.matches),
                       None, matched.good_count, "LightGlue", "assignment score", 0.1, 3.0)
    pair = PairMatchResult(replace(ref, extraction_ms=5.0), replace(tgt, extraction_ms=9.0), matches, "cpu")
    from visor.engine_registry import REGISTRY

    monkeypatch.setitem(REGISTRY, "SuperPoint+LightGlue", lambda cfg: SimpleNamespace(match_pair=lambda a, b: pair))
    result = pipeline.analyze(reference, target, "SuperPoint+LightGlue", robust_method=method)
    assert result.geometry.valid
    assert result.geometry.provenance.requested_method == method
    assert result.geometry.provenance.executed_method == method
    assert result.performance.matching_ms == 3
    assert result.performance.extraction_reference_ms == 5
    assert result.performance.extraction_target_ms == 9
    doc = analysis_document(result)
    assert doc["schema_version"] == 2 and doc["runtime"]["device"] == "cpu"
    assert doc["matching"]["correspondences"][0]["distance"] is None
    assert doc["geometry"]["provenance"]["executed_method"] == method


def test_learned_path_rejects_unsupported_matching_strategy(textured_pair):
    ref, tgt, *_ = textured_pair
    with pytest.raises(ValueError, match="Classical matching strategies"):
        pipeline.analyze(ref, tgt, "SuperPoint+LightGlue", matching_options=MatchingOptions(cross_check=True))


def test_adaptive_threshold_provenance_does_not_change_legacy_result(textured_pair):
    ref_path, tgt_path, *_ = textured_pair
    result = pipeline.analyze(ref_path, tgt_path, "SIFT")
    geometry = result.geometry
    assert geometry.provenance.threshold_policy == "legacy_adaptive"
    assert geometry.provenance.requested_threshold_px == 4.0
    assert geometry.provenance.attempted_thresholds_px[0] == 3.0
    assert geometry.provenance.effective_threshold_px in geometry.provenance.attempted_thresholds_px
    ref, tgt, matches = result.reference_features, result.target_features, result.match_set
    original, _ = estimate_homography(ref, tgt, matches, result.reference_size, target_size=result.target_size)
    assert geometry.inlier_mask == original.inlier_mask
    lmeds, _ = estimate_with_robust_method(ref, tgt, matches, result.reference_size, method="LMEDS")
    assert lmeds.provenance.effective_threshold_px is None
    assert lmeds.provenance.threshold_policy == "not_used"
