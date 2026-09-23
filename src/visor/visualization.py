"""Render diagnostic overlays from structured analysis results."""

from __future__ import annotations

import cv2
import numpy as np

from visor.models import AnalysisSettings, ByteArray, FeatureSet, GeometryResult, MatchSet


def render_match_canvas(
    reference_image: np.ndarray,
    target_image: np.ndarray,
    reference_features: FeatureSet,
    target_features: FeatureSet,
    matches: MatchSet,
    geometry: GeometryResult,
    settings: AnalysisSettings,
    maximum_drawn: int = 1500,
) -> ByteArray:
    ref_h, ref_w = reference_image.shape[:2]
    target_h, target_w = target_image.shape[:2]
    canvas = np.zeros((max(ref_h, target_h), ref_w + target_w, 3), dtype=np.uint8)
    canvas[:ref_h, :ref_w] = reference_image
    canvas[:target_h, ref_w:ref_w + target_w] = target_image
    if settings.show_keypoints:
        for feature_set, offset in ((reference_features, 0), (target_features, ref_w)):
            for point in feature_set.keypoints[:maximum_drawn]:
                cv2.circle(canvas, (round(point.x) + offset, round(point.y)), 2, (175, 135, 70), 1, cv2.LINE_AA)
    selected = list(enumerate(matches.matches))
    if len(selected) > maximum_drawn:
        selected = sorted(selected, key=lambda pair: pair[1].distance)[:maximum_drawn]
    for index, match in selected:
        is_known = len(geometry.inlier_mask) == len(matches.matches)
        is_inlier = is_known and geometry.inlier_mask[index]
        if is_known and is_inlier and not settings.show_inliers:
            continue
        if is_known and not is_inlier and not settings.show_outliers:
            continue
        first = reference_features.keypoints[match.query_index]
        second = target_features.keypoints[match.train_index]
        start = (round(first.x), round(first.y))
        end = (round(second.x) + ref_w, round(second.y))
        color = (70, 205, 135) if is_inlier else (80, 95, 220) if is_known else (190, 180, 65)
        if settings.show_match_lines:
            cv2.line(canvas, start, end, color, 1, cv2.LINE_AA)
        cv2.circle(canvas, start, 3, color, -1, cv2.LINE_AA)
        cv2.circle(canvas, end, 3, color, -1, cv2.LINE_AA)
    if len(matches.matches) > maximum_drawn:
        cv2.putText(canvas, f"Showing {maximum_drawn:,} best of {len(matches.matches):,} good matches",
                    (12, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (235, 240, 245), 1, cv2.LINE_AA)
    return canvas


def render_localization(
    target_image: np.ndarray,
    target_features: FeatureSet,
    geometry: GeometryResult,
    settings: AnalysisSettings,
) -> ByteArray:
    canvas = target_image.copy()
    if settings.show_keypoints:
        for point in target_features.keypoints[:3000]:
            cv2.circle(canvas, (round(point.x), round(point.y)), 2, (175, 135, 70), 1, cv2.LINE_AA)
    if settings.show_geometry and geometry.valid and geometry.projected_corners:
        polygon = np.round(np.asarray(geometry.projected_corners)).astype(np.int32).reshape(-1, 1, 2)
        cv2.polylines(canvas, [polygon], True, (64, 210, 146), 3, cv2.LINE_AA)
        if geometry.center:
            cv2.circle(canvas, tuple(round(value) for value in geometry.center), 6, (50, 180, 255), -1, cv2.LINE_AA)
    return canvas
