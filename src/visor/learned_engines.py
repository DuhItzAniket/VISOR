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
_XFEAT_AVAILABLE = False

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

try:
    if _TORCH_AVAILABLE:
        import xfeat  # noqa: F401
        _XFEAT_AVAILABLE = True
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
        if not _XFEAT_AVAILABLE:
            raise LearnedEngineUnavailable(
                "XFeat requires the optional xfeat package. Install it with: pip install xfeat"
            )
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

    def extract_and_match(
        self,
        ref_gray: NDArray[np.uint8],
        tgt_gray: NDArray[np.uint8],
    ) -> tuple[FeatureSet, FeatureSet, NDArray[np.int64]]:
        ref_features = self.extract(ref_gray)
        tgt_features = self.extract(tgt_gray)

        if ref_features.descriptors is None or tgt_features.descriptors is None:
            return ref_features, tgt_features, np.empty((0, 2), dtype=np.int64)

        matches = np.empty((0, 2), dtype=np.int64)
        if len(ref_features.keypoints) and len(tgt_features.keypoints):
            from sklearn.neighbors import NearestNeighbors  # type: ignore
            model = NearestNeighbors(n_neighbors=1)
            model.fit(tgt_features.descriptors)
            distances, indices = model.kneighbors(ref_features.descriptors, return_distance=True)
            matches = np.column_stack((np.arange(len(ref_features.keypoints), dtype=np.int64), indices.ravel().astype(np.int64)))
        return ref_features, tgt_features, matches


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


class ALIKEDLightGlueEngine:
    """ALIKED extractor + LightGlue matcher as a FeatureEngine.

    ALIKED produces 128-D descriptors and is designed for efficiency.
    LightGlue provides the joint matching step.
    """

    name = "ALIKED+LightGlue"

    def __init__(self, config: ALIKEDConfiguration | None = None) -> None:
        if not _LIGHTGLUE_AVAILABLE:
            raise LearnedEngineUnavailable(
                "ALIKED+LightGlue requires torch and lightglue. "
                "Install with: pip install git+https://github.com/cvg/LightGlue.git"
            )
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
                _off = torch.zeros(1, 18, 4, 4, device="cuda")
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
        self._matcher = LightGlue(features="aliked").eval().to(self._device)
        logger.info("ALIKED+LightGlue engine initialised on %s", self._device)

    def extract(self, gray: NDArray[np.uint8]) -> FeatureSet:
        """Extract ALIKED keypoints and descriptors (FeatureEngine protocol)."""
        import torch
        from lightglue.utils import rbd

        # ALIKED expects a 3-channel image; replicate grayscale to RGB
        rgb = np.stack([gray, gray, gray], axis=2)
        t = torch.from_numpy(rgb).float().permute(2, 0, 1).unsqueeze(0).div(255.0).to(self._device)
        start = perf_counter()
        with torch.no_grad():
            raw = self._extractor.extract(t)
        elapsed = (perf_counter() - start) * 1000

        feats = rbd(raw)
        keypoints = _keypoints_from_tensor(feats["keypoints"])
        descriptors: DescriptorArray = feats["descriptors"].cpu().numpy().astype(np.float32)
        count = len(keypoints)
        dims = int(descriptors.shape[1]) if count > 0 else 128
        info = DescriptorInfo(count, dims, "FLOAT32", descriptors.nbytes, "L2")
        return FeatureSet(keypoints, descriptors, info, elapsed)

    def extract_and_match(
        self,
        ref_gray: NDArray[np.uint8],
        tgt_gray: NDArray[np.uint8],
    ) -> tuple[FeatureSet, FeatureSet, NDArray[np.int64]]:
        """Extract ALIKED features from both images and run LightGlue matching."""
        import torch
        from lightglue.utils import rbd

        def _prep(g: NDArray[np.uint8]) -> Any:
            rgb = np.stack([g, g, g], axis=2)
            return torch.from_numpy(rgb).float().permute(2, 0, 1).unsqueeze(0).div(255.0).to(self._device)

        ref_t, tgt_t = _prep(ref_gray), _prep(tgt_gray)
        start = perf_counter()
        with torch.no_grad():
            ref_raw = self._extractor.extract(ref_t)
            tgt_raw = self._extractor.extract(tgt_t)
            match_raw = self._matcher({"image0": ref_raw, "image1": tgt_raw})
        elapsed = (perf_counter() - start) * 1000

        ref_feats, tgt_feats, match_data = rbd(ref_raw), rbd(tgt_raw), rbd(match_raw)
        ref_kp = _keypoints_from_tensor(ref_feats["keypoints"])
        tgt_kp = _keypoints_from_tensor(tgt_feats["keypoints"])
        ref_desc: DescriptorArray = ref_feats["descriptors"].cpu().numpy().astype(np.float32)
        tgt_desc: DescriptorArray = tgt_feats["descriptors"].cpu().numpy().astype(np.float32)
        ref_dims = int(ref_desc.shape[1]) if len(ref_kp) > 0 else 128
        tgt_dims = int(tgt_desc.shape[1]) if len(tgt_kp) > 0 else 128
        half = elapsed / 2
        ref_fs = FeatureSet(ref_kp, ref_desc, DescriptorInfo(len(ref_kp), ref_dims, "FLOAT32", ref_desc.nbytes, "L2"), half)
        tgt_fs = FeatureSet(tgt_kp, tgt_desc, DescriptorInfo(len(tgt_kp), tgt_dims, "FLOAT32", tgt_desc.nbytes, "L2"), half)
        matches: NDArray[np.int64] = match_data["matches"].cpu().numpy()
        return ref_fs, tgt_fs, matches


def is_xfeat_available() -> bool:
    """Return True if the optional XFeat dependency is importable."""
    return _XFEAT_AVAILABLE


def is_learned_available() -> bool:
    """Return True when any optional learned-engine dependency is importable."""
    return _LIGHTGLUE_AVAILABLE or _XFEAT_AVAILABLE
