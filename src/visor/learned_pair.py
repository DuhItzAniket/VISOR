"""Shared, measured pair-matching contract for optional LightGlue engines.

Importing this module does not import torch or download model weights.
"""

from __future__ import annotations

from collections.abc import Callable
from time import perf_counter
from typing import Any, TypeVar

import numpy as np
from numpy.typing import NDArray

from visor.models import (
    DescriptorInfo,
    FeatureSet,
    KeypointInfo,
    MatchInfo,
    MatchSet,
    PairMatchResult,
)

T = TypeVar("T")


def synchronize(device: Any) -> None:
    if getattr(device, "type", str(device)) == "cuda":
        import torch

        torch.cuda.synchronize(device)


def measured(device: Any, operation: Callable[[], T]) -> tuple[T, float]:
    """Measure completed work, including device synchronization when needed."""
    synchronize(device)
    start = perf_counter()
    result = operation()
    synchronize(device)
    return result, (perf_counter() - start) * 1000


def feature_set(raw: Any, elapsed_ms: float, dimensions: int, *, batched: bool = True) -> FeatureSet:
    if batched:
        from lightglue.utils import rbd

        raw = rbd(raw)
    points = raw["keypoints"].detach().cpu().numpy()
    descriptors = raw["descriptors"].detach().cpu().numpy().astype(np.float32)
    scores = raw.get("keypoint_scores", raw.get("scores"))
    responses = None if scores is None else scores.detach().cpu().numpy().reshape(-1)
    if points.ndim != 2 or points.shape[1] != 2:
        raise ValueError("Extractor returned malformed keypoints.")
    if descriptors.ndim != 2 or descriptors.shape != (len(points), dimensions):
        raise ValueError("Extractor returned descriptors that do not align with its keypoints.")
    if not np.isfinite(points).all() or not np.isfinite(descriptors).all():
        raise ValueError("Extractor returned non-finite features.")
    if responses is not None and (len(responses) != len(points) or not np.isfinite(responses).all()):
        raise ValueError("Extractor returned invalid keypoint scores.")
    keypoints = tuple(
        KeypointInfo(float(point[0]), float(point[1]), 1.0, 0.0,
                     float(responses[index]) if responses is not None else 0.0, 0, -1)
        for index, point in enumerate(points)
    )
    info = DescriptorInfo(len(points), dimensions, "FLOAT32", descriptors.nbytes, "L2")
    return FeatureSet(keypoints, descriptors, info, elapsed_ms,
                      ("response",) if responses is not None else ())


def lightglue_match_set(raw: Any, reference_count: int, target_count: int,
                       threshold: float, elapsed_ms: float) -> MatchSet:
    """Preserve assignment scores; a learned score is not descriptor distance."""
    from lightglue.utils import rbd

    data = rbd(raw)
    pairs = data["matches"].detach().cpu().numpy()
    score_tensor = data.get("scores")
    scores = None if score_tensor is None else score_tensor.detach().cpu().numpy().reshape(-1)
    if pairs.ndim != 2 or pairs.shape[1] != 2 or not np.issubdtype(pairs.dtype, np.integer):
        raise ValueError("LightGlue returned malformed match indices.")
    if len(pairs) and (pairs.min() < 0 or pairs[:, 0].max() >= reference_count
                       or pairs[:, 1].max() >= target_count):
        raise ValueError("LightGlue returned out-of-range match indices.")
    if scores is not None and (len(scores) != len(pairs) or not np.isfinite(scores).all()
                               or np.any((scores < 0) | (scores > 1))):
        raise ValueError("LightGlue returned invalid assignment scores.")
    matches = tuple(
        MatchInfo(int(pair[0]), int(pair[1]), None, None,
                  None if scores is None else float(scores[index]))
        for index, pair in enumerate(pairs)
    )
    return MatchSet(matches, None, len(matches), "LightGlue", "assignment score", threshold, elapsed_ms)


class LightGluePairEngine:
    """Mixin measuring extraction and matching as distinct completed stages."""

    _device: Any
    _extractor: Any
    _matcher: Any
    _dimensions: int = 128
    _rgb: bool = False
    _match_threshold: float = 0.1
    runtime_revision: str | None = None

    def _extract_raw(self, gray: NDArray[np.uint8]) -> tuple[Any, FeatureSet]:
        import torch

        def operation() -> tuple[Any, FeatureSet]:
            tensor = torch.from_numpy(np.ascontiguousarray(gray)).float().unsqueeze(0)
            if self._rgb:
                tensor = tensor.expand(3, -1, -1)
            tensor = tensor.unsqueeze(0).div(255.0).to(self._device)
            raw = self._extractor.extract(tensor)
            return raw, feature_set(raw, 0.0, self._dimensions)

        from dataclasses import replace

        with torch.inference_mode():
            (raw, features), elapsed = measured(self._device, operation)
        return raw, replace(features, extraction_ms=elapsed)

    def extract(self, gray: NDArray[np.uint8]) -> FeatureSet:
        return self._extract_raw(gray)[1]

    def match_pair(self, reference: NDArray[np.uint8], target: NDArray[np.uint8]) -> PairMatchResult:
        from dataclasses import replace

        import torch

        reference_raw, ref = self._extract_raw(reference)
        target_raw, tgt = self._extract_raw(target)

        def operation() -> MatchSet:
            raw = self._matcher({"image0": reference_raw, "image1": target_raw})
            return lightglue_match_set(raw, len(ref.keypoints), len(tgt.keypoints), self._match_threshold, 0.0)

        with torch.inference_mode():
            matches, elapsed = measured(self._device, operation)
        return PairMatchResult(ref, tgt, replace(matches, duration_ms=elapsed), str(self._device))

    def extract_and_match(self, reference: NDArray[np.uint8], target: NDArray[np.uint8]
                          ) -> tuple[FeatureSet, FeatureSet, NDArray[np.int64]]:
        """Compatibility wrapper; new callers should use the typed match_pair."""
        result = self.match_pair(reference, target)
        indices = np.asarray([(m.query_index, m.train_index) for m in result.match_set.matches],
                             dtype=np.int64).reshape(-1, 2)
        return result.reference, result.target, indices
