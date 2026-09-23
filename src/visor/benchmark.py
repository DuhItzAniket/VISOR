"""Controlled, repeatable image-pair perturbations for engine benchmarking."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import Event
from time import perf_counter
from typing import Literal

import cv2
import numpy as np
from numpy.typing import NDArray

from visor.engines import ORBConfiguration, SIFTConfiguration
from visor.models import AnalysisSettings, ByteArray, EngineName
from visor.pipeline import _check_cancel, _read_image, analyze_images

ScenarioName = Literal[
    "Baseline", "Rotation + scale", "Perspective", "Brightness", "Contrast",
    "Blur", "Noise", "Crop", "Resolution reduction",
]


@dataclass(frozen=True)
class BenchmarkRow:
    engine: EngineName
    scenario: ScenarioName
    keypoints_reference: int
    keypoints_target: int
    good_matches: int
    inliers: int
    inlier_ratio: float
    geometry_valid: bool
    localization_error_px: float | None
    total_ms: float


@dataclass(frozen=True)
class BenchmarkReport:
    reference_path: Path
    rows: tuple[BenchmarkRow, ...]
    duration_ms: float


def _scenarios(image: ByteArray) -> list[tuple[ScenarioName, ByteArray, np.ndarray]]:
    height, width = image.shape[:2]
    corners: NDArray[np.float32] = np.array(
        [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]], dtype=np.float32,
    )
    scenarios: list[tuple[ScenarioName, np.ndarray, np.ndarray]] = [("Baseline", image.copy(), np.eye(3))]

    affine = cv2.getRotationMatrix2D((width / 2, height / 2), 17.0, 0.9)
    affine_h = np.vstack([affine, [0.0, 0.0, 1.0]])
    scenarios.append(("Rotation + scale", cv2.warpAffine(image, affine, (width, height)), affine_h))

    margin_x, margin_y = width * 0.08, height * 0.08
    destination: NDArray[np.float32] = np.array([
        [margin_x, margin_y], [width - margin_x, 0],
        [width - 1 - margin_x, height - margin_y], [0, height - 1 - margin_y],
    ], dtype=np.float32)
    perspective = cv2.getPerspectiveTransform(corners, destination)
    scenarios.append(("Perspective", cv2.warpPerspective(image, perspective, (width, height)), perspective))
    scenarios.append(("Brightness", cv2.convertScaleAbs(image, alpha=1.0, beta=32), np.eye(3)))
    scenarios.append(("Contrast", cv2.convertScaleAbs(image, alpha=1.25, beta=0), np.eye(3)))
    scenarios.append(("Blur", cv2.GaussianBlur(image, (7, 7), 1.6), np.eye(3)))
    noise = np.random.default_rng(2026).normal(0.0, 12.0, image.shape).astype(np.float32)
    noisy = np.clip(image.astype(np.float32) + noise, 0, 255).astype(np.uint8)
    scenarios.append(("Noise", noisy, np.eye(3)))
    reduced = cv2.resize(image, (max(1, width // 2), max(1, height // 2)), interpolation=cv2.INTER_AREA)
    restored = cv2.resize(reduced, (width, height), interpolation=cv2.INTER_LINEAR)
    scenarios.append(("Resolution reduction", restored, np.eye(3)))

    if width > 8 and height > 8:
        crop_x, crop_y = max(1, int(width * 0.08)), max(1, int(height * 0.08))
        cropped = image[crop_y:height - crop_y, crop_x:width - crop_x]
        crop_target = cv2.resize(cropped, (width, height), interpolation=cv2.INTER_LINEAR)
        crop_h = np.array([
            [width / cropped.shape[1], 0, -crop_x * width / cropped.shape[1]],
            [0, height / cropped.shape[0], -crop_y * height / cropped.shape[0]],
            [0, 0, 1],
        ], dtype=np.float64)
        scenarios.append(("Crop", crop_target, crop_h))
    return scenarios


def run_benchmark(
    reference_path: Path,
    engines: tuple[EngineName, ...] = ("SIFT", "ORB"),
    settings: AnalysisSettings | None = None,
    sift_config: SIFTConfiguration | None = None,
    orb_config: ORBConfiguration | None = None,
    cancel_event: Event | None = None,
) -> BenchmarkReport:
    if not engines:
        raise ValueError("Choose at least one engine for a benchmark.")
    image = _read_image(reference_path)
    settings = settings or AnalysisSettings()
    height, width = image.shape[:2]
    corners: NDArray[np.float32] = np.array(
        [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]], dtype=np.float32,
    ).reshape(-1, 1, 2)
    rows: list[BenchmarkRow] = []
    start = perf_counter()
    for scenario, target_image, truth_matrix in _scenarios(image):
        _check_cancel(cancel_event)
        target_path = reference_path.with_name(f"{reference_path.stem}-benchmark-{scenario.lower().replace(' ', '-')}{reference_path.suffix}")
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
                engine, scenario, len(result.reference_features.keypoints),
                len(result.target_features.keypoints), result.match_set.good_count,
                result.geometry.inlier_count, result.geometry.inlier_ratio,
                result.geometry.valid, error, result.performance.total_ms,
            ))
    return BenchmarkReport(reference_path, tuple(rows), (perf_counter() - start) * 1000)
