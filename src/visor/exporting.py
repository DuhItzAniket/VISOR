"""Machine-readable analysis exports and portable project sessions."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from visor.benchmark import BenchmarkReport
from visor.engines import ORBConfiguration, SIFTConfiguration
from visor.models import AnalysisResult, AnalysisSettings, ComparisonResult, EngineName

APP_VERSION = "0.1.0"
PROJECT_FORMAT_VERSION = 1


@dataclass(frozen=True)
class ProjectSession:
    reference_path: str
    target_path: str
    engine: EngineName
    settings: AnalysisSettings
    sift: SIFTConfiguration
    orb: ORBConfiguration


def analysis_document(result: AnalysisResult) -> dict[str, Any]:
    geometry = result.geometry
    return {
        "schema_version": 1,
        "application_version": APP_VERSION,
        "inputs": {
            "reference_path": str(result.reference_path),
            "target_path": str(result.target_path),
            "reference_size_px": list(result.reference_size),
            "target_size_px": list(result.target_size),
        },
        "engine": result.engine,
        "engine_configuration": result.engine_configuration,
        "configuration": asdict(result.settings),
        "features": {
            "reference_count": len(result.reference_features.keypoints),
            "target_count": len(result.target_features.keypoints),
            "descriptor": asdict(result.reference_features.descriptor_info),
        },
        "matching": {
            "matcher": result.match_set.matcher,
            "filter": result.match_set.filter_name,
            "threshold": result.match_set.threshold,
            "candidate_pairs": result.match_set.candidate_count,
            "good_matches": result.match_set.good_count,
            "duration_ms": result.match_set.duration_ms,
        },
        "geometry": {
            "valid": geometry.valid,
            "message": geometry.message,
            "inliers": geometry.inlier_count,
            "outliers": geometry.outlier_count,
            "inlier_ratio": geometry.inlier_ratio,
            "mean_inlier_reprojection_error_px": geometry.reprojection_error_px,
            "projected_corners_px": geometry.projected_corners,
            "center_px": geometry.center,
            "homography": None if geometry.homography is None else geometry.homography.tolist(),
        },
        "performance_ms": asdict(result.performance),
    }


def export_json(result: AnalysisResult, path: Path) -> None:
    path.write_text(json.dumps(analysis_document(result), indent=2), encoding="utf-8")


def export_csv(result: AnalysisResult, path: Path) -> None:
    geometry = result.geometry
    fields = {
        "engine": result.engine,
        "reference_path": str(result.reference_path),
        "target_path": str(result.target_path),
        "reference_keypoints": len(result.reference_features.keypoints),
        "target_keypoints": len(result.target_features.keypoints),
        "candidate_pairs": result.match_set.candidate_count,
        "good_matches": result.match_set.good_count,
        "inliers": geometry.inlier_count,
        "outliers": geometry.outlier_count,
        "inlier_ratio": geometry.inlier_ratio,
        "homography_valid": geometry.valid,
        "mean_reprojection_error_px": geometry.reprojection_error_px,
        "center_x_px": None if geometry.center is None else geometry.center[0],
        "center_y_px": None if geometry.center is None else geometry.center[1],
        "image_loading_ms": result.performance.image_loading_ms,
        "extraction_reference_ms": result.performance.extraction_reference_ms,
        "extraction_target_ms": result.performance.extraction_target_ms,
        "matching_ms": result.performance.matching_ms,
        "geometry_ms": result.performance.geometry_ms,
        "total_ms": result.performance.total_ms,
    }
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields.keys())
        writer.writeheader()
        writer.writerow(fields)


def export_comparison_csv(result: ComparisonResult, path: Path) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        fields = ["engine", "reference_keypoints", "target_keypoints", "good_matches", "inliers",
                  "outliers", "inlier_ratio", "geometry_valid", "reprojection_error_px", "total_ms"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for analysis in (result.sift, result.orb):
            writer.writerow({
                "engine": analysis.engine,
                "reference_keypoints": len(analysis.reference_features.keypoints),
                "target_keypoints": len(analysis.target_features.keypoints),
                "good_matches": analysis.match_set.good_count,
                "inliers": analysis.geometry.inlier_count,
                "outliers": analysis.geometry.outlier_count,
                "inlier_ratio": analysis.geometry.inlier_ratio,
                "geometry_valid": analysis.geometry.valid,
                "reprojection_error_px": analysis.geometry.reprojection_error_px,
                "total_ms": analysis.performance.total_ms,
            })


def export_benchmark_csv(result: BenchmarkReport, path: Path) -> None:
    if not result.rows:
        raise ValueError("The benchmark contains no result rows.")
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(result.rows[0].__dataclass_fields__))
        writer.writeheader()
        for row in result.rows:
            writer.writerow(asdict(row))


def export_visualization(image: np.ndarray, path: Path) -> None:
    suffix = path.suffix.lower() or ".png"
    success, encoded = cv2.imencode(suffix, image)
    if not success:
        raise ValueError(f"Could not encode visualization as {suffix}.")
    encoded.tofile(path)


def save_project(session: ProjectSession, path: Path) -> None:
    data = {
        "format_version": PROJECT_FORMAT_VERSION,
        "application_version": APP_VERSION,
        "reference_path": session.reference_path,
        "target_path": session.target_path,
        "engine": session.engine,
        "settings": asdict(session.settings),
        "sift": asdict(session.sift),
        "orb": asdict(session.orb),
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_project(path: Path) -> ProjectSession:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("format_version") != PROJECT_FORMAT_VERSION:
        raise ValueError("This project file version is unsupported.")
    reference = Path(data["reference_path"])
    target = Path(data["target_path"])
    if not reference.is_file() or not target.is_file():
        raise ValueError("The project references an image file that cannot be found.")
    engine = data.get("engine")
    if engine not in ("SIFT", "ORB"):
        raise ValueError("The project file contains an unknown feature engine.")
    return ProjectSession(
        str(reference), str(target), engine,
        AnalysisSettings(**data.get("settings", {})),
        SIFTConfiguration(**data.get("sift", {})),
        ORBConfiguration(**data.get("orb", {})),
    )
