"""Video tracker localizes a reference across frames without Qt."""

from __future__ import annotations

from pathlib import Path
from threading import Event

import cv2
import numpy as np
import pytest

from visor.pipeline import AnalysisCancelled
from visor.video import annotate_frame, track_reference_in_frames, track_reference_in_video


def _frames(count: int = 6):
    rng = np.random.default_rng(11)
    base = np.full((300, 400, 3), 235, dtype=np.uint8)
    for _ in range(120):
        x, y = int(rng.integers(8, 392)), int(rng.integers(8, 292))
        cv2.circle(base, (x, y), int(rng.integers(2, 8)), tuple(int(v) for v in rng.integers(0, 200, size=3)), -1)
    frames = []
    for i in range(count):
        shift = np.float32([[1, 0, i * 6], [0, 1, i * 3]])
        frames.append(cv2.warpAffine(base, shift, (400, 300)))
    return cv2.cvtColor(base, cv2.COLOR_BGR2GRAY), frames


def test_tracker_follows_translating_reference():
    reference_gray, frames = _frames()
    tracks = track_reference_in_frames(reference_gray, frames, engine="ORB")
    assert len(tracks) == len(frames)
    assert tracks[0].geometry_valid
    assert tracks[0].center is not None
    # Center should drift right/down as the scene translates.
    assert tracks[-1].center[0] > tracks[0].center[0]


def test_tracker_reports_blank_frames_as_invalid():
    reference_gray, _ = _frames()
    blank = [np.zeros((300, 400, 3), dtype=np.uint8)]
    (track,) = track_reference_in_frames(reference_gray, blank, engine="ORB")
    assert not track.geometry_valid
    assert track.projected_corners == ()


def test_tracker_honors_cancel():
    reference_gray, frames = _frames()
    event = Event()
    event.set()
    with pytest.raises(AnalysisCancelled):
        track_reference_in_frames(reference_gray, frames, cancel_event=event)


def test_video_file_round_trip(tmp_path):
    reference_gray, frames = _frames(count=4)
    ref_path = tmp_path / "ref.png"
    video_path = tmp_path / "clip.avi"
    cv2.imwrite(str(ref_path), reference_gray)
    writer = cv2.VideoWriter(str(video_path), cv2.VideoWriter_fourcc(*"MJPG"), 10.0, (400, 300))
    for frame in frames:
        writer.write(frame)
    writer.release()
    report = track_reference_in_video(ref_path, video_path, engine="ORB")
    assert len(report.frames) == 4
    assert report.frames[0].geometry_valid
    annotated = annotate_frame(frames[0], report.frames[0])
    assert annotated.shape == frames[0].shape


def test_video_rejects_unreadable_file(tmp_path):
    ref = Path(__file__).parent / "data" / "golden_reference.png"
    with pytest.raises(ValueError, match="Could not open video"):
        track_reference_in_video(ref, tmp_path / "missing.avi")
