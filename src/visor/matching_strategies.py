"""Optional matching strategies around the frozen BF + Lowe-ratio default.

``match_features`` in :mod:`visor.matching` keeps its exact default behavior.
Everything here is opt-in via :class:`MatchingOptions` and is exercised through
``match_with_options``, which the pipeline calls once the UI exposes the toggles.
"""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

import cv2
import numpy as np

from visor.matching import match_features
from visor.models import FeatureSet, MatchInfo, MatchSet


@dataclass(frozen=True)
class MatchingOptions:
    ratio_threshold: float = 0.75
    cross_check: bool = False
    symmetric_ratio: bool = False
    use_flann: bool = False

    def __post_init__(self) -> None:
        if not 0.0 < self.ratio_threshold < 1.0:
            raise ValueError("Ratio threshold must be between zero and one.")


def _norm_for(features: FeatureSet, engine: str) -> int:
    if engine == "SIFT" or features.descriptor_info.distance == "L2":
        return cv2.NORM_L2
    if features.descriptor_info.distance == "HAMMING2":
        return cv2.NORM_HAMMING2
    return cv2.NORM_HAMMING


def _is_binary(features: FeatureSet) -> bool:
    return features.descriptor_info.distance in ("HAMMING", "HAMMING2")


def match_cross_check(reference: FeatureSet, target: FeatureSet, engine: str) -> MatchSet:
    """Mutual-nearest-neighbor matching without a ratio test."""
    start = perf_counter()
    if reference.descriptors is None or target.descriptors is None:
        return MatchSet((), 0, 0, "BF cross-check", "mutual nearest", 0.0, 0.0)
    matcher = cv2.BFMatcher(_norm_for(reference, engine), crossCheck=True)
    pairs = matcher.match(reference.descriptors, target.descriptors)
    accepted = tuple(
        MatchInfo(p.queryIdx, p.trainIdx, float(p.distance), None) for p in pairs
    )
    elapsed = (perf_counter() - start) * 1000
    return MatchSet(accepted, len(pairs), len(accepted), "Brute force cross-check", "mutual nearest", 0.0, elapsed)


def match_with_flann(
    reference: FeatureSet, target: FeatureSet, engine: str, ratio_threshold: float = 0.75
) -> MatchSet:
    """FLANN matching: LSH for binary descriptors, KD-tree for float.

    Falls back to brute force when FLANN cannot index the descriptors.
    """
    start = perf_counter()
    if reference.descriptors is None or target.descriptors is None:
        return MatchSet((), 0, 0, "FLANN", "Lowe ratio", ratio_threshold, 0.0)
    try:
        if _is_binary(reference):
            params = {"algorithm": 6, "table_number": 6, "key_size": 12, "multi_probe_level": 1}
        else:
            params = {"algorithm": 1, "trees": 5}
        matcher = cv2.FlannBasedMatcher(params, {"checks": 50})
        pairs = matcher.knnMatch(
            np.ascontiguousarray(reference.descriptors),
            np.ascontiguousarray(target.descriptors),
            k=2,
        )
    except cv2.error:
        return match_features(reference, target, engine, ratio_threshold)
    accepted: list[MatchInfo] = []
    candidates = 0
    for pair in pairs:
        if len(pair) != 2:
            continue
        candidates += 1
        nearest, second = pair
        ratio = float(nearest.distance / second.distance) if second.distance > 0 else float("inf")
        if ratio < ratio_threshold:
            accepted.append(MatchInfo(nearest.queryIdx, nearest.trainIdx, float(nearest.distance), ratio))
    elapsed = (perf_counter() - start) * 1000
    kind = "LSH" if _is_binary(reference) else "KD-tree"
    return MatchSet(
        tuple(accepted), candidates, len(accepted),
        f"FLANN {kind}", "Lowe ratio test", ratio_threshold, elapsed,
    )


def match_symmetric_ratio(
    reference: FeatureSet, target: FeatureSet, engine: str, ratio_threshold: float = 0.75
) -> MatchSet:
    """Ratio test in both directions, keeping only mutually consistent pairs."""
    start = perf_counter()
    forward = match_features(reference, target, engine, ratio_threshold)
    reverse = match_features(target, reference, engine, ratio_threshold)
    reverse_lookup = {(m.query_index, m.train_index) for m in reverse.matches}
    kept = tuple(m for m in forward.matches if (m.train_index, m.query_index) in reverse_lookup)
    elapsed = (perf_counter() - start) * 1000 + forward.duration_ms + reverse.duration_ms
    return MatchSet(
        kept, forward.candidate_count, len(kept),
        forward.matcher, "symmetric Lowe ratio", ratio_threshold, elapsed,
    )


def match_with_options(
    reference: FeatureSet, target: FeatureSet, engine: str, options: MatchingOptions | None = None
) -> MatchSet:
    """Dispatch to the requested strategy; defaults reproduce ``match_features``."""
    options = options or MatchingOptions()
    if options.cross_check:
        return match_cross_check(reference, target, engine)
    if options.use_flann:
        return match_with_flann(reference, target, engine, options.ratio_threshold)
    if options.symmetric_ratio:
        return match_symmetric_ratio(reference, target, engine, options.ratio_threshold)
    return match_features(reference, target, engine, options.ratio_threshold)
