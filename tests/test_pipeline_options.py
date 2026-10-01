"""Pipeline options threading: defaults frozen, opt-ins work end to end."""

from __future__ import annotations

from pathlib import Path

from visor.matching_strategies import MatchingOptions
from visor.pipeline import analyze, compare_engines, compare_n_engines

DATA = Path(__file__).parent / "data"
REF = DATA / "golden_reference.png"
TGT = DATA / "golden_target.png"


def test_default_options_reproduce_golden_counts():
    import json

    golden = json.loads((DATA / "golden_classical.json").read_text())
    for engine in ("SIFT", "ORB"):
        result = analyze(REF, TGT, engine)  # type: ignore[arg-type]
        assert result.match_set.good_count == golden[engine]["good"]
        assert result.geometry.inlier_count == golden[engine]["inliers"]


def test_cross_check_option_flows_through_pipeline():
    default = analyze(REF, TGT, "SIFT")
    crossed = analyze(REF, TGT, "SIFT", matching_options=MatchingOptions(cross_check=True))
    assert crossed.match_set.matcher == "Brute force cross-check"
    assert crossed.match_set.good_count > 0
    assert crossed.geometry.valid == default.geometry.valid


def test_magsac_option_flows_through_pipeline():
    result = analyze(REF, TGT, "ORB", robust_method="MAGSAC")
    assert result.geometry.valid
    assert result.geometry.inlier_count >= 4


def test_compare_n_matches_legacy_compare():
    legacy = compare_engines(REF, TGT)
    n_way = compare_n_engines(REF, TGT, engines=("SIFT", "ORB"))
    assert len(n_way) == 2
    assert n_way[0].match_set.good_count == legacy.sift.match_set.good_count
    assert n_way[1].match_set.good_count == legacy.orb.match_set.good_count
