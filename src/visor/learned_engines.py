"""Learned feature engines backed by LightGlue extractors.

These engines are optional. They require ``torch`` and ``lightglue`` to be
installed (``pip install git+https://github.com/cvg/LightGlue.git``).
When the dependencies are absent the module still imports cleanly; the
engines raise ``LearnedEngineUnavailable`` on construction.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from math import isfinite
from time import perf_counter
from typing import Any

import numpy as np
from numpy.typing import NDArray

from visor.models import DescriptorArray, DescriptorInfo, FeatureSet, KeypointInfo

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Availability guard
# ---------------------------------------------------------------------------

_TORCH_AVAILABLE = False
_LIGHTGLUE_AVAILABLE = False

try:
    import torch  # noqa: F401
    _TORCH_AVAILABLE = True
except ImportError:
    pass

try:
    if _TORCH_AVAILABLE:
        import lightglue  # noqa: F401
        _LIGHTGLUE_AVAILABLE = True
except ImportError:
    pass


class LearnedEngineUnavailable(RuntimeError):
    """Raised when a learned engine is requested but its dependencies are missing."""


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _to_tensor(gray: NDArray[np.uint8]) -> Any:
    """Convert a uint8 grayscale image to a normalised (1,1,H,W) float tensor."""
    import torch
    return torch.from_numpy(gray).float().unsqueeze(0).unsqueeze(0).div(255.0)


def _keypoints_from_tensor(kp_tensor: Any) -> tuple[KeypointInfo, ...]:
    """Convert a (N,2) float tensor of (x,y) coordinates to KeypointInfo tuples."""
    pts = kp_tensor.cpu().numpy()
    return tuple(
        KeypointInfo(float(pt[0]), float(pt[1]), 1.0, 0.0, 0.0, 0, -1)
        for pt in pts
    )


# ---------------------------------------------------------------------------
# SuperPoint + LightGlue
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SuperPointConfiguration:
    max_keypoints: int = 1024
    detection_threshold: float = 0.005
    use_cuda: bool = True

    def __post_init__(self) -> None:
        if self.max_keypoints < 1:
            raise ValueError("max_keypoints must be positive.")
        if not isfinite(self.detection_threshold) or not 0 < self.detection_threshold < 1:
            raise ValueError("detection_threshold must be finite and between 0 and 1.")


class SuperPointLightGlueEngine:
    """SuperPoint extractor + LightGlue matcher as a FeatureEngine.

    The primary path is ``extract_and_match`` which fuses extraction and
    matching in one forward pass. ``extract`` is also provided for the
    FeatureEngine protocol (single-image use).
    """

    name = "SuperPoint+LightGlue"

    def __init__(self, config: SuperPointConfiguration | None = None) -> None:
        if not _LIGHTGLUE_AVAILABLE:
            raise LearnedEngineUnavailable(
                "SuperPoint+LightGlue requires torch and lightglue. "
                "Install with: pip install git+https://github.com/cvg/LightGlue.git"
            )
        import torch
        from lightglue import LightGlue, SuperPoint

        self.config = config or SuperPointConfiguration()
        self._device = torch.device(
            "cuda" if self.config.use_cuda and torch.cuda.is_available() else "cpu"
        )
        self._extractor = SuperPoint(
            max_num_keypoints=self.config.max_keypoints,
            detection_threshold=self.config.detection_threshold,
        ).eval().to(self._device)
        self._matcher = LightGlue(features="superpoint").eval().to(self._device)
        logger.info("SuperPoint+LightGlue engine initialised on %s", self._device)

    def extract(self, gray: NDArray[np.uint8]) -> FeatureSet:
        """Extract SuperPoint keypoints and descriptors (FeatureEngine protocol)."""
        import torch
        from lightglue.utils import rbd

        t = _to_tensor(gray).to(self._device)
        start = perf_counter()
        with torch.no_grad():
            raw = self._extractor.extract(t)
        elapsed = (perf_counter() - start) * 1000

        feats = rbd(raw)
        kp_tensor = feats["keypoints"]
        desc_tensor = feats["descriptors"]
        keypoints = _keypoints_from_tensor(kp_tensor)
        descriptors: DescriptorArray = desc_tensor.cpu().numpy().astype(np.float32)
        count = len(keypoints)
        dims = int(descriptors.shape[1]) if count > 0 else 256
        info = DescriptorInfo(count, dims, "FLOAT32", descriptors.nbytes, "L2")
        return FeatureSet(keypoints, descriptors, info, elapsed)

    def extract_and_match(
        self,
        ref_gray: NDArray[np.uint8],
        tgt_gray: NDArray[np.uint8],
    ) -> tuple[FeatureSet, FeatureSet, NDArray[np.int64]]:
        """Extract features from both images and run LightGlue matching.

        Returns (ref_features, tgt_features, matches) where matches is an
        (M, 2) array of (ref_index, tgt_index) pairs.
        """
        import torch
        from lightglue.utils import rbd

        ref_t = _to_tensor(ref_gray).to(self._device)
        tgt_t = _to_tensor(tgt_gray).to(self._device)

        start = perf_counter()
        with torch.no_grad():
            ref_raw = self._extractor.extract(ref_t)
            tgt_raw = self._extractor.extract(tgt_t)
            match_raw = self._matcher({"image0": ref_raw, "image1": tgt_raw})
        elapsed = (perf_counter() - start) * 1000

        ref_feats = rbd(ref_raw)
        tgt_feats = rbd(tgt_raw)
        match_data = rbd(match_raw)

        ref_kp = _keypoints_from_tensor(ref_feats["keypoints"])
        tgt_kp = _keypoints_from_tensor(tgt_feats["keypoints"])

        ref_desc: DescriptorArray = ref_feats["descriptors"].cpu().numpy().astype(np.float32)
        tgt_desc: DescriptorArray = tgt_feats["descriptors"].cpu().numpy().astype(np.float32)

        ref_dims = int(ref_desc.shape[1]) if len(ref_kp) > 0 else 256
        tgt_dims = int(tgt_desc.shape[1]) if len(tgt_kp) > 0 else 256

        ref_info = DescriptorInfo(len(ref_kp), ref_dims, "FLOAT32", ref_desc.nbytes, "L2")
        tgt_info = DescriptorInfo(len(tgt_kp), tgt_dims, "FLOAT32", tgt_desc.nbytes, "L2")

        half = elapsed / 2
        ref_feature_set = FeatureSet(ref_kp, ref_desc, ref_info, half)
        tgt_feature_set = FeatureSet(tgt_kp, tgt_desc, tgt_info, half)

        matches: NDArray[np.int64] = match_data["matches"].cpu().numpy()  # (M, 2)
        return ref_feature_set, tgt_feature_set, matches


def is_learned_available() -> bool:
    """Return True if torch and lightglue are importable."""
    return _LIGHTGLUE_AVAILABLE
