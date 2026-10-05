"""Rotation/scale robustness sweeps complementing the nine-scenario benchmark.

:func:`run_benchmark` keeps its exact scenario set. This module adds denser
single-parameter sweeps (rotation angle, scale factor) so presentations can
plot inlier-ratio curves per engine. Same ground-truth corner-RMSE method.
"""

from __future__ import annotations

from pathlib import Path
from threading import Event
from time import perf_counter

import cv2
import numpy as np
from numpy.typing import NDArray

from visor.benchmark import BenchmarkReport, BenchmarkRow
from visor.engines import ORBConfiguration, SIFTConfiguration
from visor.models import AnalysisSettings, ByteArray, EngineName
from visor.pipeline import _check_cancel, _read_image, analyze_images

ROTATION_DEGREES: tuple[float, ...] = (10.0, 20.0, 30.0, 45.0, 60.0, 90.0)
SCALE_FACTORS: tuple[float, ...] = (0.5, 0.75, 1.25, 1.5)


def sweep_scenarios(image: ByteArray) -> list[tuple[str, ByteArray, np.ndarray]]:
    """Build rotation and scale variants with known homographies."""
    height, width = image.shape[:2]
    out: list[tuple[str, ByteArray, np.ndarray]] = []
    for angle in ROTATION_DEGREES:
        affine = cv2.getRotationMatrix2D((width / 2, height / 2), angle, 1.0)
        affine_h = np.vstack([affine, [0.0, 0.0, 1.0]])
        out.append((f"Rotation {angle:g}deg", cv2.warpAffine(image, affine, (width, height)), affine_h))
    for factor in SCALE_FACTORS:
        affine = cv2.getRotationMatrix2D((width / 2, height / 2), 0.0, factor)
        affine_h = np.vstack([affine, [0.0, 0.0, 1.0]])
        out.append((f"Scale {factor:g}x", cv2.warpAffine(image, affine, (width, height)), affine_h))
    return out


def run_robustness_sweep(
    reference_path: Path,
    engines: tuple[EngineName, ...] = ("SIFT", "ORB"),
    settings: AnalysisSettings | None = None,
    sift_config: SIFTConfiguration | None = None,
    orb_config: ORBConfiguration | None = None,
    cancel_event: Event | None = None,
) -> BenchmarkReport:
    if not engines:
        raise ValueError("Choose at least one engine for a sweep.")
    image = _read_image(reference_path)
    settings = settings or AnalysisSettings()
    height, width = image.shape[:2]
    corners: NDArray[np.float32] = np.array(
        [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]], dtype=np.float32,
    ).reshape(-1, 1, 2)
    rows: list[BenchmarkRow] = []
    start = perf_counter()
    for scenario, target_image, truth_matrix in sweep_scenarios(image):
        _check_cancel(cancel_event)
        target_path = reference_path.with_name(f"{reference_path.stem}-sweep-{scenario.lower().replace(' ', '-')}{reference_path.suffix}")
        truth = cv2.perspectiveTransform(corners, truth_matrix).reshape(-1, 2)
        for engine in engines:
            _check_cancel(cancel_event)
            result = analyze_images(
                reference_path, target_path, image, target_image, engine, settings,
                sift_config, orb_config,
            )
            error = None
            if result.geometry.valid:
                estimated = np.asarray(result.geometry.projected_corners, dtype=np.float64)
                error = float(np.sqrt(np.mean(np.sum((estimated - truth) ** 2, axis=1))))
            rows.append(BenchmarkRow(
                engine, scenario, len(result.reference_features.keypoints),  # type: ignore[arg-type]
                len(result.target_features.keypoints), result.match_set.good_count,
                result.geometry.inlier_count, result.geometry.inlier_ratio,
                result.geometry.valid, error, result.performance.total_ms,
            ))
    return BenchmarkReport(reference_path, tuple(rows), (perf_counter() - start) * 1000)
