"""Reproducible developer evaluation CLI: python -m visor.evaluate --help."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import subprocess
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any

import cv2
import numpy as np

from visor import __version__
from visor.engines import ORBConfiguration, SIFTConfiguration
from visor.evaluation_data import (
    EvaluationPair,
    _relative,
    load_evaluation_manifest,
    prepare_hpatches,
    prepare_synthetic,
)
from visor.exporting import analysis_document
from visor.learned_engines import SuperPointConfiguration, XFeatConfiguration
from visor.models import VALID_ENGINE_NAMES, AnalysisSettings, EngineName
from visor.pipeline import analyze


def sha256(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()
    except OSError:
        return None


def corner_errors(estimated, truth, size: tuple[int, int]) -> dict[str, float]:
    width, height = size
    corners = np.array([[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]],
                       dtype=np.float64).reshape(-1, 1, 2)
    # Reject truth with a projective horizon crossing this image.
    denominators = np.column_stack((corners.reshape(4, 2), np.ones(4))) @ truth[2]
    if not (np.all(denominators > 0) or np.all(denominators < 0)):
        raise ValueError("Ground-truth horizon crosses the reference image.")
    expected = cv2.perspectiveTransform(corners, truth)
    actual = cv2.perspectiveTransform(corners, estimated)
    values = np.linalg.norm(actual - expected, axis=2).ravel()
    if not np.isfinite(values).all():
        raise ValueError("Ground-truth corner projection is non-finite.")
    return {"corner_error_mean_px": float(np.mean(values)),
            "corner_error_rmse_px": float(np.sqrt(np.mean(values**2))),
            "corner_error_max_px": float(np.max(values))}


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary = {}
    for engine in dict.fromkeys(row["engine"] for row in rows):
        samples = [row for row in rows if row["engine"] == engine]
        truth = [row for row in samples if row["has_ground_truth"] and not row.get("annotation_error", False)]
        negatives = [row for row in samples if row["expected_match"] is False]
        durations = [row["wall_ms"] for row in samples]
        summary[engine] = {
            "attempts": len(samples), "errors": sum(row["error"] is not None for row in samples),
            "annotation_errors": sum(row.get("annotation_error", False) for row in samples),
            "fitted": sum(row["geometry_valid"] for row in samples),
            "fit_rate": sum(row["geometry_valid"] for row in samples) / len(samples),
            "ground_truth_attempts": len(truth),
            "accuracy_at_mean_corner_px": {
                str(threshold): None if not truth else sum(
                    row["corner_error_mean_px"] is not None and row["corner_error_mean_px"] <= threshold
                    for row in truth) / len(truth) for threshold in (1, 3, 5)
            },
            "negative_attempts": len(negatives),
            "false_accepts": sum(row["geometry_valid"] for row in negatives),
            "false_accept_rate": None if not negatives else sum(row["geometry_valid"] for row in negatives) / len(negatives),
            "wall_median_ms": float(np.median(durations)), "wall_p95_ms": float(np.percentile(durations, 95)),
        }
    return summary


def runtime_versions() -> dict[str, Any]:
    versions: dict[str, Any] = {"visor": __version__, "python": platform.python_version(),
                                "platform": platform.platform(), "architecture": platform.machine()}
    for name in ("numpy", "opencv-contrib-python", "PySide6", "torch", "torchvision", "lightglue"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    try:
        root = Path(__file__).resolve().parents[2]
        versions["source_revision"] = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, text=True).strip()
        versions["source_dirty"] = bool(subprocess.check_output(
            ["git", "-C", str(root), "status", "--porcelain"], stderr=subprocess.DEVNULL, text=True).strip())
    except (OSError, subprocess.CalledProcessError):
        versions["source_revision"] = None
        versions["source_dirty"] = None
    versions["evaluation_code_sha256"] = sha256(Path(__file__))
    return versions


def evaluate(manifest: Path, engines: tuple[EngineName, ...] = ("SIFT", "ORB"), *,
             repetitions: int = 3, warmup: int = 1, seed: int = 0,
             settings: AnalysisSettings | None = None, robust_method="RANSAC",
             feature_budget: int | None = None, device: str = "cpu") -> dict[str, Any]:
    if repetitions < 1 or warmup < 0 or not engines or len(set(engines)) != len(engines):
        raise ValueError("Choose distinct engines, positive repetitions and nonnegative warmup.")
    if any(engine not in VALID_ENGINE_NAMES for engine in engines) or not -(2**31) <= seed < 2**31:
        raise ValueError("Unsupported engine or seed outside the signed 32-bit range.")
    if feature_budget is not None and feature_budget < 1:
        raise ValueError("Feature budget must be positive.")
    if feature_budget is not None and any(engine in ("AKAZE", "BRISK") for engine in engines):
        raise ValueError("AKAZE/BRISK do not expose this feature budget; evaluate their native configurations separately.")
    if robust_method not in ("RANSAC", "MAGSAC", "LMEDS") or device not in ("cpu", "auto"):
        raise ValueError("Unsupported estimator or device policy.")
    document, pairs = load_evaluation_manifest(manifest)
    if len({pair.split for pair in pairs}) > 1:
        raise ValueError("Evaluate development and held-out splits separately; do not mix them in one run.")
    settings = settings or AnalysisSettings()
    hashes = {_relative(path, manifest.parent): sha256(path)
              for pair in pairs for path in (pair.reference, pair.target)}
    for row in document["pairs"]:
        if isinstance(row.get("homography"), str):
            path = (manifest.parent / row["homography"]).resolve()
            hashes[_relative(path, manifest.parent)] = sha256(path)
    report: dict[str, Any] = {
        "schema_version": 1, "created_utc": datetime.now(timezone.utc).isoformat(),
        "runtime": runtime_versions(), "manifest_sha256": sha256(manifest), "manifest": document,
        "input_sha256": hashes,
        "ground_truth_matrices": {pair.name: pair.homography.tolist() for pair in pairs if pair.homography is not None},
        "configuration": {"engines": engines, "repetitions": repetitions, "warmup": warmup, "seed": seed,
                          "settings": asdict(settings), "robust_method": robust_method,
                          "feature_budget": feature_budget, "device_policy": device},
        "latency_scope": "Fresh engine per call; decoding, model loading and rendering included. Warmup warms caches only.",
        "accuracy_scope": "Forward reference pixel-coordinate corners, mean/RMSE/max L2 error against ground truth; failures remain in denominators.",
        "warmup_rows": [], "rows": [],
    }
    use_cuda = device == "auto"
    for pair in pairs:
        for engine in engines:
            for iteration in range(warmup + repetitions):
                cv2.setRNGSeed(seed)
                row = _attempt(pair, engine, settings, robust_method, feature_budget, use_cuda, manifest.parent)
                row["iteration"] = iteration - warmup
                key = "warmup_rows" if iteration < warmup else "rows"
                report[key].append(row)
    report["summary"] = summarize(report["rows"])
    report["summary_by_condition"] = {
        condition: summarize([row for row in report["rows"] if row["condition"] == condition])
        for condition in sorted({pair.condition for pair in pairs})
    }
    return report


def _attempt(pair: EvaluationPair, engine: EngineName, settings: AnalysisSettings, method: str,
             budget: int | None, use_cuda: bool, base: Path) -> dict[str, Any]:
    row: dict[str, Any] = {
        "pair": pair.name, "split": pair.split, "condition": pair.condition,
        "engine": engine, "expected_match": pair.expected_match,
        "has_ground_truth": pair.homography is not None, "geometry_valid": False, "error": None,
        "corner_error_mean_px": None, "corner_error_rmse_px": None, "corner_error_max_px": None,
        "analysis": None,
    }
    start = perf_counter()
    try:
        result = analyze(pair.reference, pair.target, engine, settings,
                         SIFTConfiguration(max_features=budget or 0), ORBConfiguration(max_features=budget or 1500),
                         sp_config=SuperPointConfiguration(max_keypoints=budget or 1024, use_cuda=use_cuda),
                         xfeat_config=XFeatConfiguration(max_keypoints=budget or 1024, use_cuda=use_cuda),
                         robust_method=method)
        row["geometry_valid"] = result.geometry.valid
        row["analysis"] = analysis_document(result)
        row["analysis"]["inputs"]["reference_path"] = _relative(pair.reference, base)
        row["analysis"]["inputs"]["target_path"] = _relative(pair.target, base)
        if pair.homography is not None:
            try:
                corner_errors(pair.homography, pair.homography, result.reference_size)
            except ValueError:
                row["annotation_error"] = True
                raise
        if result.geometry.valid and pair.homography is not None:
            row.update(corner_errors(result.geometry.homography, pair.homography, result.reference_size))
    except Exception as exc:  # noqa: BLE001 -- every failed attempt must remain in the raw report
        row["error"] = f"{type(exc).__name__}: {exc}"
        row["geometry_valid"] = False
    row["wall_ms"] = (perf_counter() - start) * 1000
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    synthetic = commands.add_parser("make-synthetic")
    synthetic.add_argument("reference", type=Path)
    synthetic.add_argument("directory", type=Path)
    hpatches = commands.add_parser("make-hpatches")
    hpatches.add_argument("sequences", type=Path)
    hpatches.add_argument("manifest", type=Path)
    run = commands.add_parser("run")
    run.add_argument("manifest", type=Path)
    run.add_argument("output", type=Path)
    run.add_argument("--engines", nargs="+", choices=VALID_ENGINE_NAMES, default=["SIFT", "ORB"])
    run.add_argument("--repetitions", type=int, default=3)
    run.add_argument("--warmup", type=int, default=1)
    run.add_argument("--seed", type=int, default=0)
    run.add_argument("--estimator", choices=["RANSAC", "MAGSAC", "LMEDS"], default="RANSAC")
    run.add_argument("--feature-budget", type=int)
    run.add_argument("--device", choices=["cpu", "auto"], default="cpu")
    run.add_argument("--ratio", type=float, default=0.75)
    run.add_argument("--estimator-base", type=float, default=4.0)
    args = parser.parse_args()
    try:
        if args.command == "make-synthetic":
            print(prepare_synthetic(args.reference, args.directory))
        elif args.command == "make-hpatches":
            document = prepare_hpatches(args.sequences, args.manifest)
            print(f"Prepared {len(document['pairs'])} pairs; {len(document['skipped'])} missing pairs recorded.")
        else:
            args.manifest = args.manifest.resolve()
            _, pairs = load_evaluation_manifest(args.manifest)
            protected = {args.manifest, *(p.reference for p in pairs), *(p.target for p in pairs)}
            temporary = args.output.with_suffix(args.output.suffix + ".tmp")
            document, _ = load_evaluation_manifest(args.manifest)
            protected.update((args.manifest.parent / row["homography"]).resolve()
                             for row in document["pairs"] if isinstance(row.get("homography"), str))
            if args.output.resolve() in protected or temporary.resolve() in protected:
                raise ValueError("Evaluation output must not overwrite its manifest or input images.")
            report = evaluate(args.manifest, tuple(args.engines), repetitions=args.repetitions, warmup=args.warmup,
                              seed=args.seed, robust_method=args.estimator, feature_budget=args.feature_budget,
                              device=args.device, settings=AnalysisSettings(ratio_threshold=args.ratio,
                                                                           ransac_threshold=args.estimator_base))
            args.output.parent.mkdir(parents=True, exist_ok=True)
            temporary.write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
            temporary.replace(args.output)
            print(json.dumps(report["summary"], indent=2))
    except (OSError, ValueError, TypeError, KeyError) as exc:
        parser.exit(2, f"Evaluation failed: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
