"""Central registry mapping engine names to factories.

Classical SIFT/ORB factories live here so pipeline, benchmark, batch, and UI
resolve engines in one place instead of branching on names in five modules.
New engines (AKAZE, BRISK, learned) register here; SIFT/ORB entries never change.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, fields
from functools import partial
from importlib import import_module
from typing import Any, Protocol, cast

import cv2

from visor.engines import FeatureEngine, ORBConfiguration, ORBFeatureEngine, SIFTConfiguration, SIFTFeatureEngine
from visor.models import VALID_ENGINE_NAMES, ByteArray, EngineName, PairMatchResult


class ConfiguredEngine(FeatureEngine, Protocol):
    @property
    def config(self) -> Any: ...


class PairEngine(ConfiguredEngine, Protocol):
    _device: Any
    runtime_revision: str | None

    def match_pair(self, reference: ByteArray, target: ByteArray) -> PairMatchResult: ...


Factory = Callable[[dict[str, object] | None], ConfiguredEngine]

_MISSING_OPENCV_ENGINE_MESSAGE = (
    "{name} is not provided by this OpenCV build ({reason}). "
    "The engine stays listed but disabled; SIFT and ORB are unaffected."
)


class EngineUnavailable(RuntimeError):
    """Raised when a registered engine cannot run in this environment."""


def _sift_factory(config: dict[str, object] | None) -> SIFTFeatureEngine:
    cfg = SIFTConfiguration(**config) if config else None  # type: ignore[arg-type]
    return SIFTFeatureEngine(cfg)


def _orb_factory(config: dict[str, object] | None) -> ORBFeatureEngine:
    cfg = ORBConfiguration(**config) if config else None  # type: ignore[arg-type]
    return ORBFeatureEngine(cfg)


def _optional_factory(module: str, engine_class: str, config_class: str, config: dict[str, object] | None) -> ConfiguredEngine:
    imported = import_module(module)
    configuration = getattr(imported, config_class)(**config) if config else None
    return cast(ConfiguredEngine, getattr(imported, engine_class)(configuration))


REGISTRY: dict[str, Factory] = {
    "SIFT": _sift_factory,
    "ORB": _orb_factory,
}
_CONFIGURATION_TYPES = {"SIFT": ("visor.engines", "SIFTConfiguration"),
                        "ORB": ("visor.engines", "ORBConfiguration")}
for _name, _module, _engine, _config in (
    ("SuperPoint+LightGlue", "learned_engines", "SuperPointLightGlueEngine", "SuperPointConfiguration"),
    ("XFeat", "learned_engines", "XFeatEngine", "XFeatConfiguration"),
    ("ALIKED+LightGlue", "learned_engines", "ALIKEDLightGlueEngine", "ALIKEDConfiguration"),
    ("DISK+LightGlue", "learned_extra", "DISKLightGlueEngine", "GenericLightGlueConfiguration"),
    ("SIFT+LightGlue", "learned_extra", "SIFTLightGlueEngine", "GenericLightGlueConfiguration"),
    ("AKAZE", "engines_classical_extra", "AKAZEFeatureEngine", "AKAZEConfiguration"),
    ("BRISK", "engines_classical_extra", "BRISKFeatureEngine", "BRISKConfiguration"),
):
    REGISTRY[_name] = partial(_optional_factory, f"visor.{_module}", _engine, _config)
    _CONFIGURATION_TYPES[_name] = (f"visor.{_module}", _config)


@dataclass(frozen=True)
class EngineCapability:
    name: EngineName
    category: str
    available: bool
    reason: str
    matcher: str
    readiness: str
    classical_matching: bool
    configuration_fields: tuple[str, ...]


def engine_capabilities() -> tuple[EngineCapability, ...]:
    """Probe dependencies without constructing a model or downloading weights."""
    from visor.learned_engines import is_lightglue_available, is_xfeat_available

    result = []
    for name in VALID_ENGINE_NAMES:
        classical = name in ("SIFT", "ORB", "AKAZE", "BRISK")
        if classical:
            available = hasattr(cv2, f"{name}_create")
            reason = "OpenCV implementation available; uses CPU." if available else f"This OpenCV build does not provide {name}."
            readiness = "ready" if available else "missing implementation"
            matcher = "descriptor matching"
        elif name == "XFeat":
            available = is_xfeat_available()
            reason = "Pinned source/weights cache present; integrity checked at use." if available else "Needs torch, tqdm and pinned source/weights setup under Diagnostics."
            readiness = "cache present" if available else "runtime unavailable"
            matcher = "mutual L2 nearest neighbor"
        else:
            available = is_lightglue_available()
            reason = "Dependencies present; weights and device are checked at use. First use may download weights." if available else "LightGlue runtime unavailable; see Diagnostics or distribution limitations."
            readiness = "dependencies present; weights unverified" if available else "runtime unavailable"
            matcher = "LightGlue assignment"
        module, config_class = _CONFIGURATION_TYPES[name]
        configuration_fields = tuple(field.name for field in fields(getattr(import_module(module), config_class)))
        result.append(EngineCapability(name, "Classical" if classical else "Learned", available,
                                       reason, matcher, readiness, classical, configuration_fields))
    return tuple(result)


def capability(name: EngineName) -> EngineCapability:
    return next(item for item in engine_capabilities() if item.name == name)


def register_engine(name: str, factory: Factory) -> None:
    """Register (or override) an engine factory. Used by optional engine modules."""
    REGISTRY[name] = factory


def list_engines() -> tuple[str, ...]:
    return tuple(REGISTRY)


def create_engine(name: EngineName, config: dict[str, object] | None = None) -> ConfiguredEngine:
    try:
        factory = REGISTRY[name]
    except KeyError as exc:
        raise EngineUnavailable(f"Unknown engine: {name!r}.") from exc
    return factory(config)


def missing_opencv_message(name: str, reason: str) -> str:
    return _MISSING_OPENCV_ENGINE_MESSAGE.format(name=name, reason=reason)
