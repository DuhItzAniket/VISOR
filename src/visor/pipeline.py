"""End-to-end classical image registration pipeline."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from threading import Event
from time import perf_counter
from typing import cast

import cv2
import numpy as np

from visor.engines import ORBConfiguration, ORBFeatureEngine, SIFTConfiguration, SIFTFeatureEngine
from visor.geometry import estimate_homography
from visor.learned_engines import (
    ALIKEDConfiguration,
    ALIKEDLightGlueEngine,
    SuperPointConfiguration,
    SuperPointLightGlueEngine,
    XFeatConfiguration,
    XFeatEngine,
)
from visor.matching import match_features
from visor.models import (
    AnalysisResult,
    AnalysisSettings,
    ByteArray,
    ComparisonResult,
    EngineName,
    MatchInfo,
    MatchSet,
    PerformanceMetrics,
    VALID_ENGINE_NAMES,
)
from visor.visualization import render_localization, render_match_canvas


class AnalysisCancelled(Exception):
    """Raised at safe pipeline boundaries after the user requests cancellation."""


def _check_cancel(cancel_event: Event | None) -> None:
    if cancel_event is not None and cancel_event.is_set():
        raise AnalysisCancelled("Analysis cancelled.")


def _read_image(path: Path) -> ByteArray:
    try:
        encoded = np.fromfile(path, dtype=np.uint8)
    except OSError as exc:
        raise ValueError(f"Could not read image: {path.name}") from exc
    image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    if image is None or image.size == 0:
        raise ValueError(f"Could not decode image: {path.name}")
    return cast(ByteArray, image)


def _validate_engine_name(engine_name: str) -> EngineName:
    if engine_name not in VALID_ENGINE_NAMES:
        valid = ", ".join(VALID_ENGINE_NAMES)
        raise ValueError(f"Unsupported engine name: {engine_name!r}. Choose from: {valid}.")
    return cast(EngineName, engine_name)


def analyze(
    reference_path: Path,
    target_path: Path,
    engine_name: EngineName,
    settings: AnalysisSettings | None = None,
    sift_config: SIFTConfiguration | None = None,
    orb_config: ORBConfiguration | None = None,
    cancel_event: Event | None = None,
) -> AnalysisResult:
    engine_name = _validate_engine_name(engine_name)
    settings = settings or AnalysisSettings()
    load_start = perf_counter()
    reference_image = _read_image(reference_path)
    target_image = _read_image(target_path)
    _check_cancel(cancel_event)
    loading_ms = (perf_counter() - load_start) * 1000
    return analyze_images(reference_path, target_path, reference_image, target_image, engine_name, settings, sift_config, orb_config, loading_ms, cancel_event)


def analyze_images(
    reference_path: Path,
    target_path: Path,
    reference_image: ByteArray,
    target_image: ByteArray,
    engine_name: EngineName,
    settings: AnalysisSettings | None = None,
    sift_config: SIFTConfiguration | None = None,
    orb_config: ORBConfiguration | None = None,
    image_loading_ms: float = 0.0,
    cancel_event: Event | None = None,
    sp_config: SuperPointConfiguration | None = None,
    xfeat_config: XFeatConfiguration | None = None,
) -> AnalysisResult:
    engine_name = _validate_engine_name(engine_name)
    settings = settings or AnalysisSettings()
    total_start = perf_counter()
    reference_gray = cast(ByteArray, cv2.cvtColor(reference_image, cv2.COLOR_BGR2GRAY))
    target_gray = cast(ByteArray, cv2.cvtColor(target_image, cv2.COLOR_BGR2GRAY))

    if engine_name in ("SuperPoint+LightGlue", "XFeat", "ALIKED+LightGlue"):
        return _analyze_learned(
            reference_path, target_path, reference_image, target_image,
            reference_gray, target_gray, settings, engine_name, sp_config, xfeat_config, image_loading_ms,
            total_start, cancel_event,
        )

    engine = SIFTFeatureEngine(sift_config) if engine_name == "SIFT" else ORBFeatureEngine(orb_config)
    _check_cancel(cancel_event)
    reference_features = engine.extract(reference_gray)
    _check_cancel(cancel_event)
    target_features = engine.extract(target_gray)
    _check_cancel(cancel_event)
    match_set = match_features(reference_features, target_features, engine_name, settings.ratio_threshold)
    _check_cancel(cancel_event)
    geometry, geometry_ms = estimate_homography(
        reference_features, target_features, match_set,
        (reference_image.shape[1], reference_image.shape[0]), settings.ransac_threshold,
        (target_image.shape[1], target_image.shape[0]),
    )
    matches_image = render_match_canvas(reference_image, target_image, reference_features, target_features, match_set, geometry, settings)
    localization_image = render_localization(target_image, target_features, geometry, settings)
    warped_image = None
    if geometry.valid and geometry.projected_corners:
        # H maps reference coordinates into target coordinates; invert it to rectify target into reference dimensions.
        assert geometry.homography is not None
        warped_image = cast(ByteArray, cv2.warpPerspective(
            target_image, np.linalg.inv(geometry.homography),
            (reference_image.shape[1], reference_image.shape[0]),
        ))
    total_ms = (perf_counter() - total_start) * 1000 + image_loading_ms
    performance = PerformanceMetrics(
        image_loading_ms, reference_features.extraction_ms, target_features.extraction_ms,
        match_set.duration_ms, geometry_ms, total_ms,
    )
    return AnalysisResult(
        engine_name, reference_path, target_path,
        (reference_image.shape[1], reference_image.shape[0]),
        (target_image.shape[1], target_image.shape[0]), reference_features, target_features,
        match_set, geometry, performance, matches_image, localization_image, warped_image,
        settings,
        asdict(engine.config),
        reference_image,
        target_image,
    )


def _analyze_learned(
    reference_path: Path,
    target_path: Path,
    reference_image: ByteArray,
    target_image: ByteArray,
    reference_gray: ByteArray,
    target_gray: ByteArray,
    settings: AnalysisSettings,
    engine_name: EngineName,
    sp_config: SuperPointConfiguration | None,
    xfeat_config: XFeatConfiguration | None,
    image_loading_ms: float,
    total_start: float,
    cancel_event: Event | None,
) -> AnalysisResult:
    """Pipeline branch for learned feature engines (SuperPoint+LightGlue, XFeat, ALIKED+LightGlue)."""
    from dataclasses import asdict as _asdict
    if engine_name == "ALIKED+LightGlue":
        aliked_cfg = ALIKEDConfiguration(
            max_keypoints=sp_config.max_keypoints if sp_config else 1024,
            use_cuda=sp_config.use_cuda if sp_config else True,
        )
        engine_obj: SuperPointLightGlueEngine | XFeatEngine | ALIKEDLightGlueEngine = ALIKEDLightGlueEngine(aliked_cfg)
        engine_config: dict[str, object] = _asdict(aliked_cfg)
    elif engine_name == "XFeat":
        xfeat_cfg = xfeat_config or XFeatConfiguration()
        engine_obj = XFeatEngine(xfeat_cfg)
        engine_config = _asdict(xfeat_cfg)
    else:
        engine_obj = SuperPointLightGlueEngine(sp_config)
        engine_config = _asdict(sp_config) if sp_config is not None else _asdict(SuperPointConfiguration())
    _check_cancel(cancel_event)
    ref_features, tgt_features, raw_matches = engine_obj.extract_and_match(reference_gray, target_gray)
    _check_cancel(cancel_event)

    # Build a MatchSet from LightGlue's (M,2) index pairs
    match_infos = tuple(
        MatchInfo(int(m[0]), int(m[1]), 0.0, None)
        for m in raw_matches
    )
    match_set = MatchSet(
        match_infos, len(ref_features.keypoints), len(match_infos),
        "LightGlue", "confidence threshold", 0.0,
        ref_features.extraction_ms + tgt_features.extraction_ms,
    )
    _check_cancel(cancel_event)

    geometry, geometry_ms = estimate_homography(
        ref_features, tgt_features, match_set,
        (reference_image.shape[1], reference_image.shape[0]), settings.ransac_threshold,
        (target_image.shape[1], target_image.shape[0]),
    )
    matches_image = render_match_canvas(
        reference_image, target_image, ref_features, tgt_features, match_set, geometry, settings,
    )
    localization_image = render_localization(target_image, tgt_features, geometry, settings)
    warped_image = None
    if geometry.valid and geometry.projected_corners:
        assert geometry.homography is not None
        warped_image = cast(ByteArray, cv2.warpPerspective(
            target_image, np.linalg.inv(geometry.homography),
            (reference_image.shape[1], reference_image.shape[0]),
        ))
    total_ms = (perf_counter() - total_start) * 1000 + image_loading_ms
    performance = PerformanceMetrics(
        image_loading_ms, ref_features.extraction_ms, tgt_features.extraction_ms,
        match_set.duration_ms, geometry_ms, total_ms,
    )
    return AnalysisResult(
        engine_name, reference_path, target_path,
        (reference_image.shape[1], reference_image.shape[0]),
        (target_image.shape[1], target_image.shape[0]),
        ref_features, tgt_features, match_set, geometry, performance,
        matches_image, localization_image, warped_image, settings, engine_config,
        reference_image, target_image,
    )


def compare_engines(
    reference_path: Path,
    target_path: Path,
    settings: AnalysisSettings | None = None,
    sift_config: SIFTConfiguration | None = None,
    orb_config: ORBConfiguration | None = None,
    cancel_event: Event | None = None,
) -> ComparisonResult:
    """Run both classical engines over the same image pair and settings."""
    settings = settings or AnalysisSettings()
    load_start = perf_counter()
    reference = _read_image(reference_path)
    target = _read_image(target_path)
    _check_cancel(cancel_event)
    loading_ms = (perf_counter() - load_start) * 1000
    sift = analyze_images(reference_path, target_path, reference, target, "SIFT", settings, sift_config, orb_config, loading_ms, cancel_event)
    orb = analyze_images(reference_path, target_path, reference, target, "ORB", settings, sift_config, orb_config, loading_ms, cancel_event)
    return ComparisonResult(sift, orb)
