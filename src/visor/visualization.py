"""Render diagnostic overlays from structured analysis results."""

from __future__ import annotations

from collections.abc import Callable

import cv2
import numpy as np

from visor.models import AnalysisSettings, ByteArray, FeatureSet, GeometryResult, MatchSet


def _rainbow_color(index: int, total: int) -> tuple[int, int, int]:
    if total <= 1:
        hue = 120
    else:
        hue = round((index / max(total - 1, 1)) * 179.0)
    hue = max(0, min(179, hue))
    hsv = np.asarray([[[hue, 255, 255]]], dtype=np.uint8)
    bgr = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)[0, 0]
    return int(bgr[0]), int(bgr[1]), int(bgr[2])


def render_match_canvas(
    reference_image: np.ndarray,
    target_image: np.ndarray,
    reference_features: FeatureSet,
    target_features: FeatureSet,
    matches: MatchSet,
    geometry: GeometryResult,
    settings: AnalysisSettings,
    maximum_drawn: int = 1500,
    *,
    cancel_check: Callable[[], None] | None = None,
) -> ByteArray:
    if cancel_check is not None:
        cancel_check()
    ref_h, ref_w = reference_image.shape[:2]
    target_h, target_w = target_image.shape[:2]
    canvas = np.zeros((max(ref_h, target_h), ref_w + target_w, 3), dtype=np.uint8)
    canvas[:ref_h, :ref_w] = reference_image
    canvas[:target_h, ref_w:ref_w + target_w] = target_image
    if settings.show_keypoints:
        for feature_set, offset in ((reference_features, 0), (target_features, ref_w)):
            for index, point in enumerate(feature_set.keypoints[:maximum_drawn]):
                if cancel_check is not None and index % 64 == 0:
                    cancel_check()
                cv2.circle(canvas, (round(point.x) + offset, round(point.y)), 2, (175, 135, 70), 1, cv2.LINE_AA)
    selected = list(enumerate(matches.matches))
    if len(selected) > maximum_drawn:
        selected = sorted(selected, key=lambda pair: (
            pair[1].distance if pair[1].distance is not None else float("inf"),
            -pair[1].confidence if pair[1].confidence is not None else 0.0,
        ))[:maximum_drawn]
    for drawn_index, (index, match) in enumerate(selected):
        if cancel_check is not None and drawn_index % 16 == 0:
            cancel_check()
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
        if settings.rainbow_feature_colors:
            color = _rainbow_color(index, max(1, len(selected)))
        else:
            color = (70, 205, 135) if is_inlier else (80, 95, 220) if is_known else (190, 180, 65)
        line_width = max(1, round(settings.feature_line_thickness))
        if settings.show_match_lines:
            cv2.line(canvas, start, end, color, line_width, cv2.LINE_AA)
        cv2.circle(canvas, start, max(2, line_width), color, -1, cv2.LINE_AA)
        cv2.circle(canvas, end, max(2, line_width), color, -1, cv2.LINE_AA)
    if len(matches.matches) > maximum_drawn:
        cv2.putText(canvas, f"Showing {maximum_drawn:,} best of {len(matches.matches):,} good matches",
                    (12, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (235, 240, 245), 1, cv2.LINE_AA)
    if cancel_check is not None:
        cancel_check()
    return canvas


def render_localization(
    target_image: np.ndarray,
    target_features: FeatureSet,
    geometry: GeometryResult,
    settings: AnalysisSettings,
    *,
    cancel_check: Callable[[], None] | None = None,
) -> ByteArray:
    if cancel_check is not None:
        cancel_check()
    canvas = target_image.copy()
    if settings.show_keypoints:
        for index, point in enumerate(target_features.keypoints[:3000]):
            if cancel_check is not None and index % 64 == 0:
                cancel_check()
            cv2.circle(canvas, (round(point.x), round(point.y)), 2, (175, 135, 70), 1, cv2.LINE_AA)
    if settings.show_geometry and geometry.valid and geometry.projected_corners:
        polygon = np.round(np.asarray(geometry.projected_corners)).astype(np.int32).reshape(-1, 1, 2)
        outline_width = max(2, round(settings.feature_line_thickness * 1.5))
        overlay = canvas.copy()
        cv2.fillPoly(overlay, [polygon], (38, 118, 220))
        cv2.addWeighted(overlay, 0.12, canvas, 0.88, 0, canvas)
        cv2.polylines(canvas, [polygon], True, (64, 210, 146), outline_width, cv2.LINE_AA)
        x_values = np.asarray([point[0] for point in geometry.projected_corners], dtype=np.float32)
        y_values = np.asarray([point[1] for point in geometry.projected_corners], dtype=np.float32)
        x1, y1 = int(np.floor(x_values.min())), int(np.floor(y_values.min()))
        x2, y2 = int(np.ceil(x_values.max())), int(np.ceil(y_values.max()))
        cv2.rectangle(canvas, (x1, y1), (x2, y2), (36, 180, 255), outline_width, cv2.LINE_AA)
        if geometry.center:
            cv2.circle(canvas, tuple(round(value) for value in geometry.center), max(5, outline_width + 2), (50, 180, 255), -1, cv2.LINE_AA)
            cv2.putText(canvas, "Object", tuple(round(value) for value in geometry.center), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    if cancel_check is not None:
        cancel_check()
    return canvas
