"""Learned feature engines backed by LightGlue extractors.

These engines are optional. They require ``torch`` and ``lightglue`` to be
installed (``pip install git+https://github.com/cvg/LightGlue.git``).
When the dependencies are absent the module still imports cleanly; the
engines raise ``LearnedEngineUnavailable`` on construction.
"""

from __future__ import annotations

import importlib.util
import logging
import sys
from dataclasses import dataclass
from math import isfinite
from time import perf_counter
from typing import Any

import numpy as np
from numpy.typing import NDArray

from visor.learned_pair import LightGluePairEngine
from visor.models import DescriptorInfo, FeatureSet, KeypointInfo, MatchInfo, MatchSet, PairMatchResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Availability guard
# ---------------------------------------------------------------------------

_TORCH_AVAILABLE = False
_LIGHTGLUE_AVAILABLE = False
_XFEAT_AVAILABLE = False

try:
    import torch  # noqa: F401
    _TORCH_AVAILABLE = True
except ImportError:
    pass

if _TORCH_AVAILABLE:
    _LIGHTGLUE_AVAILABLE = importlib.util.find_spec("lightglue") is not None
    _XFEAT_AVAILABLE = importlib.util.find_spec("xfeat") is not None


class LearnedEngineUnavailable(RuntimeError):
    """Raised when a learned engine is requested but its dependencies are missing."""


def _ensure_runtime_usable(engine_name: str) -> None:
    """Guard against the PyInstaller/TorchScript incompatibility in packaged builds."""
    if getattr(sys, "frozen", False):
        raise LearnedEngineUnavailable(
            f"{engine_name} is disabled in the packaged EXE because PyInstaller cannot load "
            "TorchScript-backed LightGlue/Kornia modules. Run the app from the project venv to use learned engines."
        )
    if not _LIGHTGLUE_AVAILABLE and engine_name != "XFeat":
        raise LearnedEngineUnavailable(
            f"{engine_name} requires torch and lightglue. Install with: "
            "pip install git+https://github.com/cvg/LightGlue.git"
        )
    if engine_name == "XFeat" and not _XFEAT_AVAILABLE:
        raise LearnedEngineUnavailable(
            "XFeat requires the optional xfeat package. Install it with: pip install xfeat"
        )


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


class SuperPointLightGlueEngine(LightGluePairEngine):
    """SuperPoint extractor + LightGlue matcher as a FeatureEngine.

    The primary path is ``extract_and_match`` which measures extraction and
    matching in separate completed stages. ``extract`` is also provided for the
    FeatureEngine protocol (single-image use).
    """

    name = "SuperPoint+LightGlue"
    _dimensions = 256

    def __init__(self, config: SuperPointConfiguration | None = None) -> None:
        _ensure_runtime_usable(self.name)
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
        self._matcher = LightGlue(features="superpoint", filter_threshold=self._match_threshold).eval().to(self._device)
        logger.info("SuperPoint+LightGlue engine initialised on %s", self._device)



# ---------------------------------------------------------------------------
# XFeat
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class XFeatConfiguration:
    max_keypoints: int = 1024
    detection_threshold: float = 0.005
    use_cuda: bool = True

    def __post_init__(self) -> None:
        if self.max_keypoints < 1:
            raise ValueError("max_keypoints must be positive.")
        if not isfinite(self.detection_threshold) or not 0 < self.detection_threshold < 1:
            raise ValueError("detection_threshold must be finite and between 0 and 1.")


class XFeatEngine:
    """Optional XFeat feature extractor + matcher wrapper.

    The package is not required for the classical project pipeline, but when the
    dependency is installed this engine follows the same FeatureEngine protocol as
    the other learned engines.
    """

    name = "XFeat"

    def __init__(self, config: XFeatConfiguration | None = None) -> None:
        _ensure_runtime_usable(self.name)
        import torch

        self.config = config or XFeatConfiguration()
        self._device = torch.device(
            "cuda" if self.config.use_cuda and torch.cuda.is_available() else "cpu"
        )

    def extract(self, gray: NDArray[np.uint8]) -> FeatureSet:
        import torch

        try:
            from xfeat import Extractor
        except ImportError as exc:  # pragma: no cover - optional dependency path
            raise LearnedEngineUnavailable("XFeat is not available in this environment.") from exc

        if not hasattr(self, "_extractor"):
            self._extractor = Extractor(
                max_keypoints=self.config.max_keypoints,
                detection_threshold=self.config.detection_threshold,
            ).to(self._device)
        t = _to_tensor(gray).to(self._device)
        start = perf_counter()
        with torch.no_grad():
            raw = self._extractor(t)
        elapsed = (perf_counter() - start) * 1000

        if isinstance(raw, tuple):
            keypoints, descriptors = raw[0], raw[1]
        elif isinstance(raw, dict):
            keypoints = raw.get("keypoints")
            descriptors = raw.get("descriptors")
        else:
            raise LearnedEngineUnavailable("Unexpected XFeat output format.")

        if keypoints is None or descriptors is None:
            return FeatureSet((), None, DescriptorInfo(0, 0, "FLOAT32", 0, "L2"), elapsed)

        if hasattr(keypoints, "cpu"):
            keypoints = keypoints.cpu().numpy()
        if hasattr(descriptors, "cpu"):
            descriptors = descriptors.cpu().numpy()

        pts = np.asarray(keypoints, dtype=np.float32)
        desc = np.asarray(descriptors, dtype=np.float32)
        feature_keypoints = tuple(
            KeypointInfo(float(pt[0]), float(pt[1]), 1.0, 0.0, 0.0, 0, -1) for pt in pts.reshape(-1, 2)
        )
        dims = int(desc.shape[1]) if desc.ndim > 1 and desc.shape else 0
        info = DescriptorInfo(len(feature_keypoints), dims, "FLOAT32", int(desc.nbytes), "L2")
        return FeatureSet(feature_keypoints, desc, info, elapsed)

    def match_pair(self, ref_gray: NDArray[np.uint8], tgt_gray: NDArray[np.uint8]) -> PairMatchResult:
        import cv2

        ref = self.extract(ref_gray)
        tgt = self.extract(tgt_gray)
        start = perf_counter()
        pairs = ()
        if ref.descriptors is not None and tgt.descriptors is not None and len(ref.keypoints) and len(tgt.keypoints):
            raw = cv2.BFMatcher(cv2.NORM_L2, crossCheck=True).match(ref.descriptors, tgt.descriptors)
            pairs = tuple(MatchInfo(m.queryIdx, m.trainIdx, float(m.distance), None)
                          for m in sorted(raw, key=lambda m: m.queryIdx))
        matches = MatchSet(pairs, len(ref.keypoints) if len(tgt.keypoints) else 0, len(pairs),
                           "Brute force / L2", "mutual nearest neighbor", None, (perf_counter() - start) * 1000)
        return PairMatchResult(ref, tgt, matches, str(self._device))

    extract_and_match = LightGluePairEngine.extract_and_match


# ---------------------------------------------------------------------------
# ALIKED + LightGlue
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ALIKEDConfiguration:
    max_keypoints: int = 1024
    detection_threshold: float = 0.01
    use_cuda: bool = True

    def __post_init__(self) -> None:
        if self.max_keypoints < 1:
            raise ValueError("max_keypoints must be positive.")
        if not isfinite(self.detection_threshold) or not 0 < self.detection_threshold < 1:
            raise ValueError("detection_threshold must be finite and between 0 and 1.")


class ALIKEDLightGlueEngine(LightGluePairEngine):
    """ALIKED extractor + LightGlue matcher as a FeatureEngine.

    ALIKED produces 128-D descriptors and is designed for efficiency.
    LightGlue provides the joint matching step.
    """

    name = "ALIKED+LightGlue"
    _dimensions = 128
    _rgb = True

    def __init__(self, config: ALIKEDConfiguration | None = None) -> None:
        _ensure_runtime_usable(self.name)
        import torch
        from lightglue import ALIKED, LightGlue

        self.config = config or ALIKEDConfiguration()
        # ALIKED uses deform_conv2d which requires a CUDA-compiled torchvision;
        # fall back to CPU when the CUDA kernel is unavailable.
        cuda_ok = self.config.use_cuda and torch.cuda.is_available()
        if cuda_ok:
            try:
                import torchvision
                torchvision.ops.deform_conv2d  # noqa: B018 — probe availability
                # Quick probe: create a tiny tensor and run deform_conv2d on CUDA
                _t = torch.zeros(1, 1, 4, 4, device="cuda")
                _off = torch.zeros(1, 18, 2, 2, device="cuda")
                _w = torch.zeros(1, 1, 3, 3, device="cuda")
                torchvision.ops.deform_conv2d(_t, _off, _w)
            except (NotImplementedError, RuntimeError):
                cuda_ok = False
                logger.warning("ALIKED: deform_conv2d CUDA kernel unavailable, falling back to CPU.")
        self._device = torch.device("cuda" if cuda_ok else "cpu")
        self._extractor = ALIKED(
            max_num_keypoints=self.config.max_keypoints,
            detection_threshold=self.config.detection_threshold,
        ).eval().to(self._device)
        self._matcher = LightGlue(features="aliked", filter_threshold=self._match_threshold).eval().to(self._device)
        logger.info("ALIKED+LightGlue engine initialised on %s", self._device)



def is_lightglue_available() -> bool:
    """Return True if LightGlue is importable."""
    return _LIGHTGLUE_AVAILABLE and not getattr(sys, "frozen", False)


def is_xfeat_available() -> bool:
    """Return True if the optional XFeat dependency is importable."""
    return _XFEAT_AVAILABLE and not getattr(sys, "frozen", False)


def is_learned_available() -> bool:
    """Return True when any optional learned-engine dependency is importable."""
    return _LIGHTGLUE_AVAILABLE or _XFEAT_AVAILABLE
