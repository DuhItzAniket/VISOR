from __future__ import annotations

import csv
import json
from pathlib import Path

from visor.models import AnalysisSettings
from visor.pipeline import analyze

REPO = Path(r"c:\Users\Luikz\Downloads\VISOR")
MANIFEST = REPO / "Sample" / "Dataset" / "pairs_manifest.csv"
OUT = REPO / "Sample" / "Dataset" / "pair_eval_summary.json"
ENGINES = ["SIFT", "ORB", "SuperPoint+LightGlue", "ALIKED+LightGlue"]


def main() -> None:
    if not MANIFEST.exists():
        raise FileNotFoundError(f"Manifest not found: {MANIFEST}")

    rows = list(csv.DictReader(MANIFEST.open("r", newline="", encoding="utf-8")))
    summary = []
    settings = AnalysisSettings(ratio_threshold=0.75, ransac_threshold=4.0)

    for row in rows:
        ref = REPO / row["reference"]
        tgt = REPO / row["target"]
        if not ref.exists() or not tgt.exists():
            print(f"Skipping missing pair: {row['scene']} -> {ref} / {tgt}")
            continue

        scene_summary = {"scene": row["scene"], "reference": str(ref), "target": str(tgt), "engines": {}}
        for engine in ENGINES:
            try:
                result = analyze(ref, tgt, engine, settings=settings)
                scene_summary["engines"][engine] = {
                    "valid": bool(result.geometry.valid),
                    "inlier_count": int(result.geometry.inlier_count),
                    "good_matches": int(result.match_set.good_count),
                    "total_ms": round(float(result.performance.total_ms), 2),
                }
            except Exception as exc:  # pragma: no cover - runtime benchmark tool
                scene_summary["engines"][engine] = {
                    "valid": False,
                    "error": f"{type(exc).__name__}: {exc}",
                }
        summary.append(scene_summary)

    OUT.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
