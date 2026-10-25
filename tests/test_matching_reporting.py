"""Nondefault matcher timing and configuration remain unambiguous."""

import pytest

from visor import matching_strategies
from visor.models import MatchSet


def test_symmetric_timer_does_not_add_nested_durations(monkeypatch):
    clock = iter([10.0, 10.125])
    monkeypatch.setattr(matching_strategies, "perf_counter", lambda: next(clock))
    matched = MatchSet((), 0, 0, "BF", "ratio", 0.75, 50.0)
    monkeypatch.setattr(matching_strategies, "match_features", lambda *args: matched)
    result = matching_strategies.match_symmetric_ratio(None, None, "SIFT")
    assert result.duration_ms == 125.0


def test_conflicting_matching_strategies_are_rejected():
    with pytest.raises(ValueError, match="only one"):
        matching_strategies.MatchingOptions(cross_check=True, use_flann=True)
    with pytest.raises(TypeError, match="booleans"):
        matching_strategies.MatchingOptions(cross_check="false")
