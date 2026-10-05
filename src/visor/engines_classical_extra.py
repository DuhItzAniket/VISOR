"""Optional classical engines: AKAZE, BRISK, KAZE.

These wrap ``cv2.AKAZE_create`` / ``cv2.BRISK_create`` when the OpenCV build
provides them. The pinned ``opencv-contrib-python 5.0`` wheel in this repo
does NOT ship them, so the factories raise :class:`EngineUnavailable` with an
actionable message instead of failing halfway through a run. If a future
environment provides them (e.g. opencv 4.9), they light up with no pipeline
changes — SIFT/ORB paths are untouched.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

import cv2

from visor import engine_registry
from visor.models import DescriptorArray, DescriptorInfo, FeatureSet, KeypointInfo


def _opencv_has(name: str) -> bool:
    return hasattr(cv2, name)


@dataclass(frozen=True)
class AKAZEConfiguration:
    threshold: float = 0.001
    octaves: int = 4
    diffusivity: str = "PM_G2"

    def __post_init__(self) -> None:
        if not isfinite(self.threshold) or self.threshold <= 0:
            raise ValueError("AKAZE threshold must be finite and positive.")
        if self.octaves < 1:
            raise ValueError("AKAZE octaves must be positive.")
        if self.diffusivity not in ("PM_G1", "PM_G2", "WEICKERT", "CHARBONNIER"):
            raise ValueError("Unknown AKAZE diffusivity.")


@dataclass(frozen=True)
class BRISKConfiguration:
    threshold: int = 30
    octaves: int = 3
    pattern_scale: float = 1.0

    def __post_init__(self) -> None:
        if self.threshold < 0 or self.octaves < 1:
            raise ValueError("BRISK threshold/octaves out of range.")
        if not isfinite(self.pattern_scale) or self.pattern_scale <= 0:
            raise ValueError("BRISK pattern scale must be finite and positive.")


def is_akaze_available() -> bool:
    return _opencv_has("AKAZE_create")


def is_brisk_available() -> bool:
    return _opencv_has("BRISK_create")


def _missing(name: str) -> engine_registry.EngineUnavailable:
    return engine_registry.EngineUnavailable(
        engine_registry.missing_opencv_message(name, "this wheel exposes only SIFT/ORB/Fast")
        + " Either install an OpenCV build with features2d extras or keep using SIFT/ORB."
    )


class AKAZEFeatureEngine:
    name = "AKAZE"

    def __init__(self, config: AKAZEConfiguration | None = None) -> None:
        if not is_akaze_available():
            raise _missing(self.name)
        self.config = config or AKAZEConfiguration()

    def extract(self, gray) -> FeatureSet:  # type: ignore[no-untyped-def]
        import time

        diffusivity = getattr(cv2, f"KAZE_DIFF_{self.config.diffusivity}", 1)
        detector = cv2.AKAZE_create(  # type: ignore[attr-defined]
            threshold=self.config.threshold,
            nOctaves=self.config.octaves,
            diffusivity=diffusivity,
        )
        start = time.perf_counter()
        points, descriptors = detector.detectAndCompute(gray, None)
        elapsed = (time.perf_counter() - start) * 1000
        infos = tuple(
            KeypointInfo(p.pt[0], p.pt[1], p.size, p.angle, p.response, p.octave, p.class_id)
            for p in points
        )
        array: DescriptorArray | None = descriptors
        count = 0 if array is None else int(array.shape[0])
        info = DescriptorInfo(count, 61, "MLDB / BINARY", 0 if array is None else array.nbytes, "HAMMING")
        return FeatureSet(infos, array, info, elapsed)


class BRISKFeatureEngine:
    name = "BRISK"

    def __init__(self, config: BRISKConfiguration | None = None) -> None:
        if not is_brisk_available():
            raise _missing(self.name)
        self.config = config or BRISKConfiguration()

    def extract(self, gray) -> FeatureSet:  # type: ignore[no-untyped-def]
        import time

        detector = cv2.BRISK_create(  # type: ignore[attr-defined]
            thresh=self.config.threshold,
            octaves=self.config.octaves,
            patternScale=self.config.pattern_scale,
        )
        start = time.perf_counter()
        points, descriptors = detector.detectAndCompute(gray, None)
        elapsed = (time.perf_counter() - start) * 1000
        infos = tuple(
            KeypointInfo(p.pt[0], p.pt[1], p.size, p.angle, p.response, p.octave, p.class_id)
            for p in points
        )
        array = descriptors
        count = 0 if array is None else int(array.shape[0])
        info = DescriptorInfo(count, 64, "BRISK / BINARY", 0 if array is None else array.nbytes, "HAMMING")
        return FeatureSet(infos, array, info, elapsed)


def _akaze_factory(config: dict[str, object] | None) -> AKAZEFeatureEngine:
    cfg = AKAZEConfiguration(**config) if config else None  # type: ignore[arg-type]
    return AKAZEFeatureEngine(cfg)


def _brisk_factory(config: dict[str, object] | None) -> BRISKFeatureEngine:
    cfg = BRISKConfiguration(**config) if config else None  # type: ignore[arg-type]
    return BRISKFeatureEngine(cfg)


engine_registry.register_engine("AKAZE", _akaze_factory)
engine_registry.register_engine("BRISK", _brisk_factory)
