"""AKAZE/BRISK guard behavior on this OpenCV build (neither is shipped)."""

from __future__ import annotations

import pytest

import visor.engines_classical_extra as extra
from visor import engine_registry


@pytest.mark.skipif(extra.is_akaze_available(), reason="AKAZE present in this build")
def test_akaze_reports_unavailable_with_actionable_message():
    assert "AKAZE" in engine_registry.list_engines()
    with pytest.raises(engine_registry.EngineUnavailable, match="SIFT and ORB"):
        extra.AKAZEFeatureEngine()


@pytest.mark.skipif(extra.is_brisk_available(), reason="BRISK present in this build")
def test_brisk_reports_unavailable_with_actionable_message():
    assert "BRISK" in engine_registry.list_engines()
    with pytest.raises(engine_registry.EngineUnavailable, match="SIFT and ORB"):
        extra.BRISKFeatureEngine()


def test_akaze_config_validation_without_opencv():
    with pytest.raises(ValueError, match="threshold"):
        extra.AKAZEConfiguration(threshold=0)
    with pytest.raises(ValueError, match="diffusivity"):
        extra.AKAZEConfiguration(diffusivity="NOPE")


def test_brisk_config_validation_without_opencv():
    with pytest.raises(ValueError, match="pattern scale"):
        extra.BRISKConfiguration(pattern_scale=0)
