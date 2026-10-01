"""Extra LightGlue-paired engines: DISK and classical SIFT descriptors.

Both reuse the installed ``lightglue`` package — no new dependency. DISK is
the Apache-2.0-licensed alternative to SuperPoint; SIFT+LightGlue pairs the
frozen classical detector with a learned matcher, which makes it a useful
ablation between the classical and learned paths. Same guarded-import style
as :mod:`visor.learned_engines`; disabled in frozen EXE builds.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from time import perf_counter
from typing import Any, Literal

import numpy as np
from numpy.typing import NDArray

from visor.learned_engines import _keypoints_from_tensor
from visor.models import DescriptorArray, DescriptorInfo, FeatureSet


class LearnedEngineUnavailable(RuntimeError):
    """Raised when an extra learned engine cannot run here."""


def _ensure_usable(name: str, feature: Literal["disk", "sift"]) -> None:
    if getattr(sys, "frozen", False):
        raise LearnedEngineUnavailable(
            f"{name} is disabled in the packaged EXE. Run from the project venv."
        )
    try:
        import lightglue  # noqa: F401
    except ImportError as exc:
        raise LearnedEngineUnavailable(
            f"{name} needs the lightglue package: pip install git+https://github.com/cvg/LightGlue.git"
        ) from exc
    _ = feature


@dataclass(frozen=True)
class GenericLightGlueConfiguration:
    max_keypoints: int = 1024
    use_cuda: bool = True

    def __post_init__(self) -> None:
        if self.max_keypoints < 1:
            raise ValueError("max_keypoints must be positive.")


class _LightGluePairedEngine:
    """Shared extract + LightGlue-match loop for DISK and SIFT extractors."""

    extractor_name: str = ""
    lightglue_features: str = ""
    descriptor_dims: int = 0

    def __init__(self, config: GenericLightGlueConfiguration | None = None) -> None:
        _ensure_usable(self.name, self.lightglue_features)  # type: ignore[attr-defined]
        import torch
        from lightglue import DISK, SIFT, LightGlue

        self.config = config or GenericLightGlueConfiguration()
        self._device = torch.device(
            "cuda" if self.config.use_cuda and torch.cuda.is_available() else "cpu"
        )
        extractor_cls = DISK if self.lightglue_features == "disk" else SIFT
        self._extractor = extractor_cls(max_num_keypoints=self.config.max_keypoints).eval().to(self._device)
        self._matcher = LightGlue(features=self.lightglue_features).eval().to(self._device)

    def _prep(self, gray: NDArray[np.uint8]) -> Any:
        import torch

        rgb = np.stack([gray, gray, gray], axis=2)
        return torch.from_numpy(rgb).float().permute(2, 0, 1).unsqueeze(0).div(255.0).to(self._device)

    def _feature_set(self, raw: Any, elapsed: float) -> FeatureSet:
        from lightglue.utils import rbd

        feats = rbd(raw)
        keypoints = _keypoints_from_tensor(feats["keypoints"])
        descriptors: DescriptorArray = feats["descriptors"].cpu().numpy().astype(np.float32)
        dims = int(descriptors.shape[1]) if len(keypoints) else self.descriptor_dims
        info = DescriptorInfo(len(keypoints), dims, "FLOAT32", descriptors.nbytes, "L2")
        return FeatureSet(keypoints, descriptors, info, elapsed)

    def extract(self, gray: NDArray[np.uint8]) -> FeatureSet:
        import torch

        start = perf_counter()
        with torch.no_grad():
            raw = self._extractor.extract(self._prep(gray))
        return self._feature_set(raw, (perf_counter() - start) * 1000)

    def extract_and_match(
        self, ref_gray: NDArray[np.uint8], tgt_gray: NDArray[np.uint8]
    ) -> tuple[FeatureSet, FeatureSet, NDArray[np.int64]]:
        import torch
        from lightglue.utils import rbd

        start = perf_counter()
        with torch.no_grad():
            ref_raw = self._extractor.extract(self._prep(ref_gray))
            tgt_raw = self._extractor.extract(self._prep(tgt_gray))
            match_raw = self._matcher({"image0": ref_raw, "image1": tgt_raw})
        elapsed = (perf_counter() - start) * 1000
        ref_fs = self._feature_set(ref_raw, elapsed / 2)
        tgt_fs = self._feature_set(tgt_raw, elapsed / 2)
        matches: NDArray[np.int64] = rbd(match_raw)["matches"].cpu().numpy()
        return ref_fs, tgt_fs, matches


class DISKLightGlueEngine(_LightGluePairedEngine):
    name = "DISK+LightGlue"
    extractor_name = "DISK"
    lightglue_features = "disk"
    descriptor_dims = 128


class SIFTLightGlueEngine(_LightGluePairedEngine):
    name = "SIFT+LightGlue"
    extractor_name = "SIFT"
    lightglue_features = "sift"
    descriptor_dims = 128


def is_disk_available() -> bool:
    try:
        import lightglue  # noqa: F401
        from lightglue import DISK  # noqa: F401
        return True
    except ImportError:
        return False
