"""Optional DISK and SIFT extractors paired with the measured LightGlue loop."""

from __future__ import annotations

from dataclasses import dataclass

from visor.learned_engines import LearnedEngineUnavailable, _ensure_runtime_usable, is_lightglue_available
from visor.learned_pair import LightGluePairEngine

__all__ = [
    "DISKLightGlueEngine",
    "GenericLightGlueConfiguration",
    "LearnedEngineUnavailable",
    "SIFTLightGlueEngine",
    "is_disk_available",
]


@dataclass(frozen=True)
class GenericLightGlueConfiguration:
    max_keypoints: int = 1024
    use_cuda: bool = True

    def __post_init__(self) -> None:
        if self.max_keypoints < 1:
            raise ValueError("max_keypoints must be positive.")


class _LightGluePairedEngine(LightGluePairEngine):
    name = ""
    lightglue_features = ""
    _rgb = True

    def __init__(self, config: GenericLightGlueConfiguration | None = None) -> None:
        _ensure_runtime_usable(self.name)
        import torch
        from lightglue import DISK, SIFT, LightGlue

        self.config = config or GenericLightGlueConfiguration()
        self._device = torch.device("cuda" if self.config.use_cuda and torch.cuda.is_available() else "cpu")
        extractor_cls = DISK if self.lightglue_features == "disk" else SIFT
        self._extractor = extractor_cls(max_num_keypoints=self.config.max_keypoints).eval().to(self._device)
        self._matcher = LightGlue(features=self.lightglue_features, filter_threshold=self._match_threshold).eval().to(self._device)


class DISKLightGlueEngine(_LightGluePairedEngine):
    name = "DISK+LightGlue"
    lightglue_features = "disk"


class SIFTLightGlueEngine(_LightGluePairedEngine):
    name = "SIFT+LightGlue"
    lightglue_features = "sift"


def is_disk_available() -> bool:
    return is_lightglue_available()
