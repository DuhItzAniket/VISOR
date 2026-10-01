"""Central registry mapping engine names to factories.

Classical SIFT/ORB factories live here so pipeline, benchmark, batch, and UI
resolve engines in one place instead of branching on names in five modules.
New engines (AKAZE, BRISK, learned) register here; SIFT/ORB entries never change.
"""

from __future__ import annotations

from collections.abc import Callable

from visor.engines import ORBConfiguration, ORBFeatureEngine, SIFTConfiguration, SIFTFeatureEngine
from visor.models import EngineName

Factory = Callable[[dict[str, object] | None], object]

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


REGISTRY: dict[str, Factory] = {
    "SIFT": _sift_factory,
    "ORB": _orb_factory,
}


def register_engine(name: str, factory: Factory) -> None:
    """Register (or override) an engine factory. Used by optional engine modules."""
    REGISTRY[name] = factory


def list_engines() -> tuple[str, ...]:
    return tuple(REGISTRY)


def create_engine(name: EngineName, config: dict[str, object] | None = None) -> object:
    try:
        factory = REGISTRY[name]
    except KeyError as exc:
        raise EngineUnavailable(f"Unknown engine: {name!r}.") from exc
    return factory(config)


def missing_opencv_message(name: str, reason: str) -> str:
    return _MISSING_OPENCV_ENGINE_MESSAGE.format(name=name, reason=reason)
