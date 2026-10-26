"""Measure local drawing and canvas uploads; never infer registration accuracy."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict, replace
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import cv2
import numpy as np
from PySide6.QtCore import qVersion
from PySide6.QtWidgets import QApplication

from visor.evaluate import runtime_versions
from visor.pipeline import analyze
from visor.ui.widgets.image_canvas import ImageCanvas
from visor.visualization import render_localization, render_match_canvas


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New JSON file; existing evidence is never overwritten")
    parser.add_argument("--scales", type=int, nargs="+", default=[1, 4, 7])
    parser.add_argument("--repetitions", type=int, default=5)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output already exists; choose a new evidence filename.")
    if not 1 <= args.repetitions <= 100 or any(not 1 <= scale <= 8 for scale in args.scales):
        parser.error("Repetitions must be 1..100 and scales 1..8.")
    app = QApplication.instance() or QApplication([])
    result = analyze(ROOT / "tests/data/golden_reference.png", ROOT / "tests/data/golden_target.png", "ORB")
    rows = []
    settings = replace(result.settings, feature_line_thickness=6, rainbow_feature_colors=True, show_keypoints=True)
    for scale in args.scales:
        reference = cv2.resize(result.reference_image, None, fx=scale, fy=scale)
        target = cv2.resize(result.target_image, None, fx=scale, fy=scale)
        ref_features = replace(result.reference_features, keypoints=tuple(
            replace(point, x=point.x * scale, y=point.y * scale) for point in result.reference_features.keypoints))
        target_features = replace(result.target_features, keypoints=tuple(
            replace(point, x=point.x * scale, y=point.y * scale) for point in result.target_features.keypoints))
        geometry = replace(result.geometry,
                           projected_corners=tuple((x * scale, y * scale) for x, y in result.geometry.projected_corners),
                           center=tuple(value * scale for value in result.geometry.center) if result.geometry.center else None)
        canvas = ImageCanvas("Rendering profile")
        samples = []
        for repeat in range(args.repetitions + 1):
            start = perf_counter()
            image = render_match_canvas(reference, target, ref_features, target_features, result.match_set, geometry, settings)
            match_ms = (perf_counter() - start) * 1000
            start = perf_counter()
            render_localization(target, target_features, geometry, settings)
            localization_ms = (perf_counter() - start) * 1000
            start = perf_counter()
            canvas.set_image(image)
            canvas_ms = (perf_counter() - start) * 1000
            if repeat:
                samples.append({"matches_ms": match_ms, "localization_ms": localization_ms, "canvas_ms": canvas_ms})
        canvas.close()
        rows.append({"input_size_px": [reference.shape[1], reference.shape[0]], "samples": samples,
                     "median_ms": {key: float(np.median([row[key] for row in samples])) for key in samples[0]},
                     "p95_ms": {key: float(np.percentile([row[key] for row in samples], 95)) for key in samples[0]}})
        app.processEvents()
    document = {"schema_version": 1, "kind": "local_rendering_profile", "runtime": runtime_versions(),
                "qt_version": qVersion(), "warmups": 1, "repetitions": args.repetitions,
                "settings": asdict(settings),
                "source_files_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in (
                    "scripts/profile_rendering.py", "src/visor/pipeline.py", "src/visor/visualization.py",
                    "src/visor/ui/widgets/image_canvas.py")},
                "input_files_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in (
                    "tests/data/golden_reference.png", "tests/data/golden_target.png")},
                "scope": "Uniformly scaled classical result; no feature redetection or accuracy measurement. "
                         "Offscreen timings are not native interaction latency or portable speed guarantees.", "rows": rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(document, stream, indent=2, allow_nan=False)
    print(json.dumps({"output": str(args.output), "medians": [row["median_ms"] for row in rows]}, indent=2))


if __name__ == "__main__":
    main()
