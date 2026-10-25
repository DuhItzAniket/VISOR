"""Portable evaluation manifests and explicit synthetic/HPatches preparation."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class EvaluationPair:
    name: str
    reference: Path
    target: Path
    homography: NDArray[np.float64] | None
    expected_match: bool | None
    split: str
    condition: str = "unspecified"


def _reject_nonfinite(value: str) -> Any:
    raise ValueError(f"Manifest contains non-finite JSON number {value}.")


def valid_homography(value: Any) -> NDArray[np.float64]:
    matrix = np.asarray(value, dtype=np.float64)
    if matrix.shape != (3, 3) or not np.isfinite(matrix).all() or np.linalg.matrix_rank(matrix) != 3:
        raise ValueError("Ground-truth homography must be a finite invertible 3×3 matrix.")
    return matrix


def load_evaluation_manifest(path: Path) -> tuple[dict[str, Any], tuple[EvaluationPair, ...]]:
    document = json.loads(path.read_text(encoding="utf-8"), parse_constant=_reject_nonfinite)
    if not isinstance(document, dict) or document.get("version") != 1 or not isinstance(document.get("pairs"), list):
        raise ValueError("Expected evaluation manifest version 1 with a pairs list.")
    pairs = []
    names = set()
    for index, row in enumerate(document["pairs"]):
        if not isinstance(row, dict) or not all(isinstance(row.get(key), str) and row[key].strip() for key in ("reference", "target")):
            raise ValueError(f"Pair {index} needs nonempty reference/target paths.")
        name = row.get("id", str(index))
        if not isinstance(name, str) or not name or name in names:
            raise ValueError("Pair ids must be nonempty unique strings.")
        names.add(name)
        expected = row.get("expected_match")
        if expected is not None and not isinstance(expected, bool):
            raise ValueError(f"Pair {name}: expected_match must be true, false or null.")
        truth = row.get("homography")
        if isinstance(truth, str):
            truth = np.loadtxt(path.parent / truth)
        matrix = None if truth is None else valid_homography(truth)
        if expected is False and matrix is not None:
            raise ValueError(f"Pair {name}: a negative pair cannot also have a ground-truth mapping.")
        split = row.get("split", "unspecified")
        if not isinstance(split, str):
            raise TypeError(f"Pair {name}: split must be a string.")
        condition = row.get("condition", "unspecified")
        if not isinstance(condition, str):
            raise TypeError(f"Pair {name}: condition must be a string.")
        pairs.append(EvaluationPair(name, (path.parent / row["reference"]).resolve(),
                                    (path.parent / row["target"]).resolve(), matrix, expected, split, condition))
    if not pairs:
        raise ValueError("Evaluation manifest contains no pairs.")
    return document, tuple(pairs)


def _relative(path: Path, base: Path) -> str:
    return Path(os.path.relpath(path.resolve(), base.resolve())).as_posix()


def prepare_hpatches(sequences: Path, manifest: Path) -> dict[str, Any]:
    """List available full-image 1→2..6 pairs; report absent files explicitly."""
    if not sequences.is_dir():
        raise ValueError("HPatches full-image sequences directory is absent. No dataset was evaluated.")
    if manifest.exists():
        raise ValueError("Choose a new manifest filename; existing files are preserved.")
    pairs, skipped = [], []
    for sequence in sorted(sequences.iterdir()):
        if not sequence.is_dir() or not sequence.name.startswith(("i_", "v_")):
            continue
        for target_index in range(2, 7):
            reference = sequence / "1.ppm"
            target = sequence / f"{target_index}.ppm"
            truth_path = sequence / f"H_1_{target_index}"
            name = f"{sequence.name}/1-{target_index}"
            if not all(file.is_file() for file in (reference, target, truth_path)):
                skipped.append({"id": name, "reason": "missing image or ground-truth file"})
                continue
            matrix = valid_homography(np.loadtxt(truth_path))
            pairs.append({"id": name, "reference": _relative(reference, manifest.parent),
                          "target": _relative(target, manifest.parent), "homography": matrix.tolist(),
                          "expected_match": True, "split": "heldout",
                          "condition": "illumination" if sequence.name.startswith("i_") else "viewpoint"})
    if not pairs:
        raise ValueError("No full-image HPatches pairs found; patch crops/scaffolding are not the sequence dataset.")
    document = {"version": 1, "dataset": "HPatches full-image sequences", "skipped": skipped, "pairs": pairs}
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(document, indent=2), encoding="utf-8")
    return document


def prepare_synthetic(reference: Path, directory: Path, seed: int = 407) -> Path:
    """Prepare development-only known warp and unrelated/blank negatives."""
    if directory.exists():
        raise ValueError("Synthetic output directory already exists; choose a new directory.")
    encoded = np.fromfile(reference, dtype=np.uint8)
    image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    if image is None or min(image.shape[:2]) < 32:
        raise ValueError("Synthetic preparation needs a readable image at least 32×32 pixels.")
    height, width = image.shape[:2]
    matrix = np.array([[1, 0.015, width * 0.04], [-0.012, 1, height * 0.04],
                       [0.00002, -0.00001, 1]], dtype=np.float64)
    rng = np.random.default_rng(seed)
    images = {"reference.png": image, "warp.png": cv2.warpPerspective(image, matrix, (width, height)),
              "unrelated.png": rng.integers(0, 256, image.shape, dtype=np.uint8),
              "blank.png": np.full_like(image, 180)}
    directory.mkdir(parents=True)
    for name, value in images.items():
        ok, content = cv2.imencode(".png", value)
        if not ok:
            raise ValueError(f"Could not encode {name}.")
        content.tofile(directory / name)
    pairs = [{"id": "known-warp", "reference": "reference.png", "target": "warp.png",
              "homography": matrix.tolist(), "expected_match": True, "split": "development"}]
    for name in ("unrelated", "blank"):
        pairs.append({"id": name, "reference": "reference.png", "target": f"{name}.png",
                      "expected_match": False, "split": "development"})
    manifest = directory / "manifest.json"
    manifest.write_text(json.dumps({"version": 1, "dataset": "synthetic development fixtures", "seed": seed,
                                    "pairs": pairs}, indent=2), encoding="utf-8")
    return manifest
