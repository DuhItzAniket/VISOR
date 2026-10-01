"""Multi-pair batch evaluation over a manifest of reference/target pairs.

A manifest is a small CSV with ``reference,target,scene`` columns, paths
resolved relative to the manifest file. :func:`run_batch` runs the frozen
single-pair :func:`visor.pipeline.analyze` for each pair and engine, so batch
results can never drift from interactive results.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from threading import Event
from time import perf_counter

from visor.engines import ORBConfiguration, SIFTConfiguration
from visor.models import AnalysisSettings, EngineName
from visor.pipeline import AnalysisCancelled, _check_cancel, analyze


@dataclass(frozen=True)
class BatchPair:
    reference: Path
    target: Path
    scene: str = ""


@dataclass(frozen=True)
class BatchRow:
    scene: str
    reference: str
    target: str
    engine: EngineName
    good_matches: int
    inliers: int
    inlier_ratio: float
    geometry_valid: bool
    localization_error_px: float | None
    total_ms: float


@dataclass(frozen=True)
class BatchReport:
    pairs: tuple[BatchPair, ...]
    rows: tuple[BatchRow, ...]
    duration_ms: float


def load_manifest(path: Path) -> tuple[BatchPair, ...]:
    """Read a manifest.csv with reference,target[,scene] columns."""
    base = path.parent
    pairs: list[BatchPair] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or not {"reference", "target"} <= set(reader.fieldnames):
            raise ValueError("Manifest needs at least 'reference' and 'target' columns.")
        for row in reader:
            pairs.append(BatchPair(
                reference=base / row["reference"].strip(),
                target=base / row["target"].strip(),
                scene=row.get("scene", "").strip(),
            ))
    if not pairs:
        raise ValueError("Manifest contains no pairs.")
    return tuple(pairs)


def run_batch(
    pairs: tuple[BatchPair, ...] | list[BatchPair],
    engines: tuple[EngineName, ...] = ("SIFT", "ORB"),
    settings: AnalysisSettings | None = None,
    sift_config: SIFTConfiguration | None = None,
    orb_config: ORBConfiguration | None = None,
    cancel_event: Event | None = None,
) -> BatchReport:
    if not pairs:
        raise ValueError("Need at least one pair for a batch run.")
    if not engines:
        raise ValueError("Choose at least one engine for a batch run.")
    settings = settings or AnalysisSettings()
    rows: list[BatchRow] = []
    start = perf_counter()
    for pair in pairs:
        for engine in engines:
            if cancel_event is not None and cancel_event.is_set():
                raise AnalysisCancelled("Batch cancelled.")
            result = analyze(pair.reference, pair.target, engine, settings, sift_config, orb_config, cancel_event)
            rows.append(BatchRow(
                scene=pair.scene,
                reference=str(pair.reference),
                target=str(pair.target),
                engine=engine,
                good_matches=result.match_set.good_count,
                inliers=result.geometry.inlier_count,
                inlier_ratio=result.geometry.inlier_ratio,
                geometry_valid=result.geometry.valid,
                localization_error_px=result.geometry.reprojection_error_px,
                total_ms=result.performance.total_ms,
            ))
    _check_cancel(cancel_event)
    return BatchReport(tuple(pairs), tuple(rows), (perf_counter() - start) * 1000)
