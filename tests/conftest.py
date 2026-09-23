from __future__ import annotations

import cv2
import numpy as np
import pytest


@pytest.fixture
def textured_pair(tmp_path):
    rng = np.random.default_rng(407)
    image = np.full((420, 560, 3), 235, dtype=np.uint8)
    for _ in range(180):
        x = int(rng.integers(8, image.shape[1] - 8))
        y = int(rng.integers(8, image.shape[0] - 8))
        color = tuple(int(v) for v in rng.integers(0, 200, size=3))
        radius = int(rng.integers(2, 9))
        cv2.circle(image, (x, y), radius, color, -1, cv2.LINE_AA)
    for index in range(12):
        cv2.putText(image, f"V{index}", (20 + (index % 4) * 130, 50 + (index // 4) * 120),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (15, 25, 35), 2, cv2.LINE_AA)
    transform = np.array([[1.0, 0.015, 22.0], [-0.012, 1.0, 17.0], [0.00002, -0.00001, 1.0]])
    target = cv2.warpPerspective(image, transform, (image.shape[1], image.shape[0]))
    reference_path, target_path = tmp_path / "reference.png", tmp_path / "target.png"
    cv2.imwrite(str(reference_path), image)
    cv2.imwrite(str(target_path), target)
    return reference_path, target_path, image, target, transform
