"""Create fixed CPU evaluation scenes; no engines, models or UI are invoked."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, cast

import cv2
import numpy as np
from numpy.typing import NDArray

SEEDS = (1301, 1302, 1303)
WIDTH, HEIGHT = 480, 360
TRANSFORM = np.array([[0.98, 0.025, 14], [-0.02, 1.01, 12], [0.00004, -0.00003, 1]], dtype=np.float64)


def textured_scene(seed: int) -> NDArray[np.uint8]:
    rng = np.random.default_rng(seed)
    image = np.full((HEIGHT, WIDTH, 3), 230, dtype=np.uint8)
    for _ in range(110):
        center = tuple(int(value) for value in rng.integers((12, 12), (WIDTH - 12, HEIGHT - 12)))
        color = tuple(int(value) for value in rng.integers(0, 200, 3))
        cv2.circle(image, center, int(rng.integers(3, 11)), color, -1, cv2.LINE_AA)
    for _ in range(30):
        points = rng.integers((5, 5), (WIDTH - 5, HEIGHT - 5), (2, 2))
        cv2.line(image, tuple(int(v) for v in points[0]), tuple(int(v) for v in points[1]),
                 (30, 30, 30), 1, cv2.LINE_AA)
    return image


def repeated_scene(seed: int) -> NDArray[np.uint8]:
    rng = np.random.default_rng(seed)
    tile = np.full((40, 48, 3), 225, dtype=np.uint8)
    color = tuple(int(value) for value in rng.integers(20, 120, 3))
    cv2.circle(tile, (15, 16), int(rng.integers(5, 10)), color, 2, cv2.LINE_AA)
    cv2.line(tile, (27, 8), (38, 29), color, 2, cv2.LINE_AA)
    return np.tile(tile, (HEIGHT // 40, WIDTH // 48, 1))


def low_texture_scene(seed: int) -> NDArray[np.uint8]:
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[:HEIGHT, :WIDTH]
    value = np.full((HEIGHT, WIDTH), 190.0)
    for _ in range(3):
        x, y = rng.uniform((50, 50), (WIDTH - 50, HEIGHT - 50))
        value -= 25 * np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * 55**2))
    return np.repeat(np.clip(value, 0, 255).astype(np.uint8)[:, :, None], 3, axis=2)


def create_manifest(directory: Path) -> Path:
    """Refuse existing output and emit only the preregistered 21 development pairs."""
    directory.mkdir(parents=True, exist_ok=False)
    pairs: list[dict[str, Any]] = []

    def write(name: str, image: NDArray[np.uint8]) -> str:
        success, encoded = cv2.imencode(".png", image)
        if not success:
            raise ValueError(f"Cannot encode {name}")
        encoded.tofile(directory / name)
        return name

    for seed in SEEDS:
        references = {"textured": textured_scene(seed), "repeated": repeated_scene(seed),
                      "low-texture": low_texture_scene(seed)}
        for condition, image in references.items():
            reference = write(f"{seed}-{condition}-reference.png", image)
            warped = cast(NDArray[np.uint8], cv2.warpPerspective(image, TRANSFORM, (WIDTH, HEIGHT)))
            target = write(f"{seed}-{condition}-target.png", warped)
            pairs.append({"id": f"{seed}/{condition}", "reference": reference, "target": target,
                          "homography": TRANSFORM.tolist(), "expected_match": True,
                          "split": "development", "condition": condition})
        reference = f"{seed}-textured-reference.png"
        occluded = cast(NDArray[np.uint8], cv2.warpPerspective(references["textured"], TRANSFORM, (WIDTH, HEIGHT)))
        occluded[:, WIDTH // 2:] = 160
        pairs.append({"id": f"{seed}/occlusion", "reference": reference,
                      "target": write(f"{seed}-occlusion-target.png", occluded),
                      "homography": TRANSFORM.tolist(), "expected_match": True,
                      "split": "development", "condition": "occlusion"})
        negatives = {"independent-scene": textured_scene(seed + 100000),
                     "independent-noise": np.random.default_rng(seed + 200000).integers(
                         0, 256, (HEIGHT, WIDTH, 3), dtype=np.uint8),
                     "blank": np.full((HEIGHT, WIDTH, 3), 180, dtype=np.uint8)}
        for condition, image in negatives.items():
            pairs.append({"id": f"{seed}/{condition}", "reference": reference,
                          "target": write(f"{seed}-{condition}-target.png", image),
                          "expected_match": False, "split": "development", "condition": condition})
    protocol = Path(__file__).resolve().parents[1] / "docs/evaluation/SYNTHETIC_STRESS_PROTOCOL.md"
    document = {"version": 1, "dataset": "VISOR synthetic stress development v1", "seeds": list(SEEDS),
                "dimensions": [WIDTH, HEIGHT], "target_occlusion_fraction": 0.5,
                "generator_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "protocol_sha256": hashlib.sha256(protocol.read_bytes()).hexdigest(),
                "scope": "Constructed development cases only; repetitions/seeds are not independent real-world scenes.",
                "pairs": pairs}
    path = directory / "manifest.json"
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8", newline="\n")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    print(create_manifest(parser.parse_args().directory))


if __name__ == "__main__":
    main()
