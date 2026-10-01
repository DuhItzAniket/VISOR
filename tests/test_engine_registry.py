"""Registry resolves the same SIFT/ORB constructors the pipeline uses."""

from __future__ import annotations

import cv2
import numpy as np

from visor import engine_registry
from visor.engines import ORBFeatureEngine, SIFTFeatureEngine


def _gray() -> np.ndarray:
    image = np.zeros((160, 160), dtype=np.uint8)
    cv2.putText(image, "VISOR", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 1.7, 255, 3)
    return image


def test_registry_lists_classical_engines():
    assert "SIFT" in engine_registry.list_engines()
    assert "ORB" in engine_registry.list_engines()


def test_registry_sift_matches_direct_construction():
    gray = _gray()
    assert isinstance(engine_registry.create_engine("SIFT"), SIFTFeatureEngine)
    assert (
        engine_registry.create_engine("SIFT").extract(gray).descriptor_info.dimensions
        == SIFTFeatureEngine().extract(gray).descriptor_info.dimensions
    )


def test_registry_orb_matches_direct_construction():
    gray = _gray()
    assert isinstance(engine_registry.create_engine("ORB"), ORBFeatureEngine)
    assert (
        engine_registry.create_engine("ORB").extract(gray).descriptor_info.distance
        == ORBFeatureEngine().extract(gray).descriptor_info.distance
    )


def test_registry_unknown_engine_raises_helpful_error():
    try:
        engine_registry.create_engine("SURF")  # type: ignore[arg-type]
    except engine_registry.EngineUnavailable as exc:
        assert "Unknown engine" in str(exc)
    else:
        raise AssertionError("unknown engine should raise EngineUnavailable")
