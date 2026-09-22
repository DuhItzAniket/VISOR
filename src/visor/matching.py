"""Descriptor-type-aware matching and Lowe ratio filtering."""

from __future__ import annotations

from time import perf_counter

import cv2

from visor.models import FeatureSet, MatchInfo, MatchSet


def match_features(
    reference: FeatureSet,
    target: FeatureSet,
    engine: str,
    ratio_threshold: float = 0.75,
) -> MatchSet:
    if not 0.0 < ratio_threshold < 1.0:
        raise ValueError("Ratio threshold must be between zero and one.")
    start = perf_counter()
    if reference.descriptors is None or target.descriptors is None:
        return MatchSet((), 0, 0, "BF / " + reference.descriptor_info.distance, "Lowe ratio", ratio_threshold, (perf_counter() - start) * 1000)
    norm = cv2.NORM_L2 if engine == "SIFT" else (
        cv2.NORM_HAMMING2 if reference.descriptor_info.distance == "HAMMING2" else cv2.NORM_HAMMING
    )
    matcher = cv2.BFMatcher(norm, crossCheck=False)
    pairs = matcher.knnMatch(reference.descriptors, target.descriptors, k=2)
    candidates = [pair for pair in pairs if len(pair) == 2]
    accepted: list[MatchInfo] = []
    for nearest, second in candidates:
        ratio = float(nearest.distance / second.distance) if second.distance > 0 else 0.0
        if ratio < ratio_threshold:
            accepted.append(MatchInfo(nearest.queryIdx, nearest.trainIdx, float(nearest.distance), ratio))
    elapsed = (perf_counter() - start) * 1000
    return MatchSet(
        tuple(accepted), len(candidates), len(accepted), f"Brute force / {reference.descriptor_info.distance}",
        "Lowe ratio test", ratio_threshold, elapsed,
    )

