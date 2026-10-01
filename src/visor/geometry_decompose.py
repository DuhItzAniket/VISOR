"""Planar homography decomposition into human-readable estimates.

A homography is only a full similarity transform (rotation + uniform scale +
translation) when the scene is planar and viewed without perspective tilt.
:func:`decompose_homography_estimate` extracts those components from the
affine part of H and always labels them estimates. Callers must surface the
``planar assumption`` wording in the UI.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class SimilarityEstimate:
    rotation_deg: float
    scale: float
    scale_x: float
    scale_y: float
    translate_x: float
    translate_y: float
    is_similarity: bool
    note: str = (
        "Image-space estimate under a planar-scene assumption; "
        "not a 3D pose measurement."
    )


def decompose_homography_estimate(matrix: NDArray[np.float64]) -> SimilarityEstimate:
    """Split H into rotation/scale/translation estimates from its affine block."""
    h = np.asarray(matrix, dtype=np.float64).reshape(3, 3)
    if abs(h[2, 2]) > 1e-12:
        h = h / h[2, 2]
    a, b = float(h[0, 0]), float(h[0, 1])
    c, d = float(h[1, 0]), float(h[1, 1])
    scale_x = math.hypot(a, c)
    scale_y = math.hypot(b, d)
    scale = (scale_x + scale_y) / 2.0
    rotation = math.degrees(math.atan2(c, a)) if scale_x > 1e-12 else 0.0
    # Similarity check: columns near-orthogonal with equal norm.
    dot = a * b + c * d
    denom = max(1e-12, scale_x * scale_y)
    is_similarity = abs(dot) / denom < 0.05 and (
        abs(scale_x - scale_y) / max(scale, 1e-12) < 0.05
    )
    return SimilarityEstimate(
        rotation_deg=rotation,
        scale=scale,
        scale_x=scale_x,
        scale_y=scale_y,
        translate_x=float(h[0, 2]),
        translate_y=float(h[1, 2]),
        is_similarity=bool(is_similarity),
    )


def reprojection_histogram(
    errors: NDArray[np.float64] | list[float], bins: int = 10
) -> tuple[tuple[float, ...], tuple[int, ...]]:
    """Bin per-match reprojection errors for the details panel; no Qt needed."""
    values = np.asarray(errors, dtype=np.float64).ravel()
    if values.size == 0 or bins < 1:
        return (), ()
    edges = np.histogram_bin_edges(values, bins=bins)
    counts, _ = np.histogram(values, bins=edges)
    return tuple(float(e) for e in edges), tuple(int(c) for c in counts)


def classify_failure(message: str) -> str:
    """Map a geometry message to a stable failure kind for UI/reporting."""
    text = message.lower()
    if "at least" in text and "required" in text:
        return "too_few_matches"
    if "outside the target" in text:
        return "outside_target"
    if "stable" in text and ("ransac" in text or "transform" in text):
        return "unstable_fit"
    if "degenerate" in text:
        return "degenerate_projection"
    if "translation fallback" in text:
        return "translation_fallback"
    if "estimated" in text:
        return "ok"
    return "unknown"
