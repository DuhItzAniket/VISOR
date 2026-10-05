"""Planar reference tracking across video frames.

Each frame is treated as an independent target image for the frozen
single-pair machinery: extract reference features once, then match +
estimate homography per frame. No temporal filtering — a frame either
localizes the reference polygon or reports why not. All Qt-free; the UI
reads frames with OpenCV on a worker thread and displays :class:`TrackReport`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import Event
from time import perf_counter

import cv2
import numpy as np

from visor.engines import ORBConfiguration, SIFTConfiguration
from visor.geometry import estimate_homography
from visor.matching import match_features
from visor.models import ByteArray, EngineName
from visor.pipeline import _check_cancel, _read_image


@dataclass(frozen=True)
class FrameTrack:
    frame_index: int
    good_matches: int
    inliers: int
    inlier_ratio: float
    geometry_valid: bool
    center: tuple[float, float] | None
    projected_corners: tuple[tuple[float, float], ...]
    track_ms: float


@dataclass(frozen=True)
class TrackReport:
    reference_path: Path
    video_path: Path
    engine: EngineName
    frames: tuple[FrameTrack, ...]
    duration_ms: float


def track_reference_in_frames(
    reference_gray: ByteArray,
    frames: list[ByteArray],
    engine: EngineName = "ORB",
    ratio_threshold: float = 0.75,
    ransac_threshold: float = 4.0,
    sift_config: SIFTConfiguration | None = None,
    orb_config: ORBConfiguration | None = None,
    cancel_event: Event | None = None,
) -> tuple[FrameTrack, ...]:
    """Track a grayscale reference across already-decoded BGR frames."""
    from visor.engines import ORBFeatureEngine, SIFTFeatureEngine

    extractor = SIFTFeatureEngine(sift_config) if engine == "SIFT" else ORBFeatureEngine(orb_config)
    reference_features = extractor.extract(reference_gray)
    height, width = reference_gray.shape[:2]
    tracks: list[FrameTrack] = []
    for index, frame in enumerate(frames):
        _check_cancel(cancel_event)
        start = perf_counter()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        target_features = extractor.extract(gray)
        match_set = match_features(reference_features, target_features, engine, ratio_threshold)
        geometry, _ = estimate_homography(
            reference_features, target_features, match_set, (width, height),
            ransac_threshold, (frame.shape[1], frame.shape[0]),
        )
        tracks.append(FrameTrack(
            frame_index=index,
            good_matches=match_set.good_count,
            inliers=geometry.inlier_count,
            inlier_ratio=geometry.inlier_ratio,
            geometry_valid=geometry.valid,
            center=geometry.center,
            projected_corners=geometry.projected_corners,
            track_ms=(perf_counter() - start) * 1000,
        ))
    return tuple(tracks)


def track_reference_in_video(
    reference_path: Path,
    video_path: Path,
    engine: EngineName = "ORB",
    ratio_threshold: float = 0.75,
    ransac_threshold: float = 4.0,
    max_frames: int = 300,
    cancel_event: Event | None = None,
) -> TrackReport:
    """Open a video file with OpenCV and track the reference image in it."""
    reference = _read_image(reference_path)
    reference_gray = cv2.cvtColor(reference, cv2.COLOR_BGR2GRAY)
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise ValueError(f"Could not open video: {video_path.name}")
    frames: list[ByteArray] = []
    try:
        while len(frames) < max_frames:
            _check_cancel(cancel_event)
            ok, frame = capture.read()
            if not ok or frame is None:
                break
            frames.append(frame)
    finally:
        capture.release()
    if not frames:
        raise ValueError(f"No decodable frames in video: {video_path.name}")
    start = perf_counter()
    tracks = track_reference_in_frames(
        reference_gray, frames, engine, ratio_threshold, ransac_threshold,
        cancel_event=cancel_event,
    )
    return TrackReport(reference_path, video_path, engine, tracks, (perf_counter() - start) * 1000)


def annotate_frame(frame: ByteArray, track: FrameTrack) -> ByteArray:
    """Draw the projected reference polygon and frame status onto a copy."""
    out = frame.copy()
    if track.projected_corners and len(track.projected_corners) == 4:
        color = (60, 200, 90) if track.geometry_valid else (70, 90, 230)
        pts = np.array(track.projected_corners, dtype=np.int32).reshape(-1, 1, 2)
        cv2.polylines(out, [pts], True, color, 2, cv2.LINE_AA)
    label = f"#{track.frame_index} inliers={track.inliers} valid={track.geometry_valid}"
    cv2.putText(out, label, (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (240, 240, 240), 2, cv2.LINE_AA)
    return out
