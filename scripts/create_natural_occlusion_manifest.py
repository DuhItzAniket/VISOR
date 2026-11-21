"""Prepare the frozen HPatches occlusion study from locally available sequences."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from visor.distribution_audit import digest
from visor.evaluation_data import valid_homography

SCENES = ("i_boutique", "i_bridger", "v_astronautis", "v_azzola")


def prepare(sequences: Path, output: Path) -> Path:
    output = output.resolve()
    source_files = [
        sequences / scene / name for scene in SCENES
        for name in ("1.ppm", "2.ppm", "6.ppm", "H_1_2", "H_1_6")
    ]
    hashes = {file.relative_to(sequences).as_posix(): digest(file) for file in source_files}
    output.mkdir(parents=True)
    pairs = []
    for scene in SCENES:
        reference = sequences / scene / "1.ppm"
        for index in (2, 6):
            target = sequences / scene / f"{index}.ppm"
            homography = valid_homography(np.loadtxt(sequences / scene / f"H_1_{index}"))
            image = cv2.imdecode(np.fromfile(target, dtype=np.uint8), cv2.IMREAD_COLOR)
            if image is None or image.shape[1] < 2:
                raise ValueError(f"Cannot decode the target for {scene}/1-{index}.")
            midpoint = image.shape[1] // 2
            for condition, columns in (("full", None), ("left_masked", slice(None, midpoint)),
                                       ("right_masked", slice(midpoint, None))):
                candidate = target
                if columns is not None:
                    masked = image.copy()
                    masked[:, columns] = 127
                    candidate = output / f"{scene}-{index}-{condition}.png"
                    ok, encoded = cv2.imencode(".png", masked)
                    if not ok:
                        raise ValueError(f"Cannot encode {candidate.name}.")
                    encoded.tofile(candidate)
                pairs.append({
                    "id": f"{scene}/1-{index}/{condition}",
                    "reference": Path(os.path.relpath(reference.resolve(), output)).as_posix(),
                    "target": Path(os.path.relpath(candidate.resolve(), output)).as_posix(),
                    "homography": homography.tolist(),
                    "expected_match": True,
                    "split": "natural_occlusion",
                    "condition": condition,
                })
    manifest = output / "manifest.json"
    manifest.write_text(json.dumps({
        "version": 1, "dataset": "HPatches full-image controlled occlusion", "source_files_sha256": hashes,
        "protocol_sha256": digest(ROOT / "docs/evaluation/NATURAL_OCCLUSION_PROTOCOL.md"), "pairs": pairs,
    }, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sequences", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(prepare(args.sequences, args.output))
