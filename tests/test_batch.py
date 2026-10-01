"""Batch runner matches single-pair results and parses manifests."""

from __future__ import annotations

from pathlib import Path
from threading import Event

import pytest

from visor.batch import BatchPair, load_manifest, run_batch
from visor.pipeline import AnalysisCancelled, analyze


def test_load_manifest_resolves_relative_paths(tmp_path):
    manifest = tmp_path / "manifest.csv"
    manifest.write_text("reference,target,scene\na.png,b.png,room\n", encoding="utf-8")
    (pair,) = load_manifest(manifest)
    assert pair.reference == tmp_path / "a.png"
    assert pair.scene == "room"


def test_load_manifest_rejects_bad_header(tmp_path):
    manifest = tmp_path / "manifest.csv"
    manifest.write_text("foo,bar\n", encoding="utf-8")
    with pytest.raises(ValueError, match="reference"):
        load_manifest(manifest)


def test_batch_matches_single_pair_analysis():
    data = Path(__file__).parent / "data"
    pairs = (BatchPair(data / "golden_reference.png", data / "golden_target.png", "golden"),)
    report = run_batch(pairs, engines=("SIFT", "ORB"))
    assert len(report.rows) == 2
    for row in report.rows:
        single = analyze(Path(row.reference), Path(row.target), row.engine)  # type: ignore[arg-type]
        assert row.good_matches == single.match_set.good_count
        assert row.inliers == single.geometry.inlier_count
        assert row.geometry_valid


def test_batch_validates_inputs_and_cancels():
    with pytest.raises(ValueError, match="at least one pair"):
        run_batch(())
    with pytest.raises(ValueError, match="at least one engine"):
        run_batch((BatchPair(Path("a"), Path("b")),), engines=())
    event = Event()
    event.set()
    with pytest.raises(AnalysisCancelled):
        run_batch((BatchPair(Path("a"), Path("b")),), cancel_event=event)


def test_example_manifest_loads():
    pairs = load_manifest(Path(__file__).parent.parent / "Sample" / "manifest.example.csv")
    assert len(pairs) == 2
    assert pairs[0].scene == "synthetic-shift"
