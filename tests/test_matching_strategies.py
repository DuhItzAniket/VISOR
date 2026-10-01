"""Optional matching strategies don't shift the frozen default path."""

from __future__ import annotations

from pathlib import Path

import pytest

from visor.engines import ORBFeatureEngine, SIFTFeatureEngine
from visor.matching import match_features
from visor.matching_strategies import (
    MatchingOptions,
    match_cross_check,
    match_symmetric_ratio,
    match_with_flann,
    match_with_options,
)
from visor.pipeline import analyze


def _features(engine: str):
    import cv2

    ref = cv2.imread(str(Path(__file__).parent / "data" / "golden_reference.png"), cv2.IMREAD_GRAYSCALE)
    tgt = cv2.imread(str(Path(__file__).parent / "data" / "golden_target.png"), cv2.IMREAD_GRAYSCALE)
    extractor = SIFTFeatureEngine() if engine == "SIFT" else ORBFeatureEngine()
    return extractor.extract(ref), extractor.extract(tgt)


@pytest.mark.parametrize("engine", ["SIFT", "ORB"])
def test_default_options_reproduce_frozen_matching(engine: str):
    ref, tgt = _features(engine)
    assert match_with_options(ref, tgt, engine).good_count == match_features(ref, tgt, engine).good_count


@pytest.mark.parametrize("engine", ["SIFT", "ORB"])
def test_cross_check_returns_sane_match_set(engine: str):
    # Cross-check skips the ratio test, so counts aren't comparable to the
    # default path — just require a non-empty, internally consistent set.
    ref, tgt = _features(engine)
    matched = match_cross_check(ref, tgt, engine)
    assert matched.good_count > 0
    assert matched.good_count == matched.candidate_count == len(matched.matches)
    assert matched.filter_name == "mutual nearest"


@pytest.mark.parametrize("engine", ["SIFT", "ORB"])
def test_flann_and_symmetric_run_cleanly(engine: str):
    ref, tgt = _features(engine)
    assert match_with_flann(ref, tgt, engine).good_count >= 0
    assert match_symmetric_ratio(ref, tgt, engine).good_count <= match_features(ref, tgt, engine).good_count


def test_full_pipeline_still_matches_golden_with_defaults():
    import json

    golden = json.loads((Path(__file__).parent / "data" / "golden_classical.json").read_text())
    for engine in ("SIFT", "ORB"):
        result = analyze(
            Path(__file__).parent / "data" / "golden_reference.png",
            Path(__file__).parent / "data" / "golden_target.png",
            engine,  # type: ignore[arg-type]
        )
        assert result.match_set.good_count == golden[engine]["good"]


def test_options_reject_bad_threshold():
    with pytest.raises(ValueError, match="between zero and one"):
        MatchingOptions(ratio_threshold=1.5)
