"""Published summaries can be recomputed from their complete raw rows."""

import gzip
import hashlib
import json
from pathlib import Path

import pytest

from visor.evaluate import summarize
from visor.reliability_study import report_frozen_gates, select_gates


@pytest.mark.parametrize("name,attempts,revision", [("synthetic-20261025.json.gz", 18, "b2c7f0b"),
                                                  ("hpatches-sample-20261025.json.gz", 72, "b2c7f0b"),
                                                  ("reliability-development-20261025.json.gz", 192, "dec9b33"),
                                                  ("reliability-reporting-20261025.json.gz", 72, "f85c7e0")])
def test_raw_evidence_summaries_agree(name, attempts, revision):
    path = Path(__file__).resolve().parents[1] / "docs/evaluation" / name
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        report = json.load(stream)
    assert len(report["rows"]) == attempts
    assert report["runtime"]["source_revision"].startswith(revision)
    assert report["runtime"]["source_dirty"] is False
    assert summarize(report["rows"]) == report["summary"]


def test_frozen_selection_recomputes_from_published_development_evidence():
    directory = Path(__file__).resolve().parents[1] / "docs/evaluation"
    path = directory / "reliability-development-20261025.json.gz"
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        report = json.load(stream)
    frozen = json.loads((directory / "reliability-selection-20261025.json").read_text())
    assert frozen["development_report_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    recomputed = select_gates(report)
    assert recomputed["engines"] == frozen["engines"]
    assert recomputed["development_pairs"] == frozen["development_pairs"]


def test_reporting_analysis_recomputes_without_retuning():
    directory = Path(__file__).resolve().parents[1] / "docs/evaluation"
    path = directory / "reliability-reporting-20261025.json.gz"
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        report = json.load(stream)
    selection_path = directory / "reliability-selection-20261025.json"
    frozen = json.loads(selection_path.read_text())
    published = json.loads((directory / "reliability-reporting-analysis-20261025.json").read_text())
    assert published["report_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert published["selection_sha256"] == hashlib.sha256(selection_path.read_bytes()).hexdigest()
    measured = report_frozen_gates(report, frozen)
    assert measured["engines"] == published["engines"]
    assert measured["decisions"] == published["decisions"]
    for engine in measured["engines"].values():
        assert engine["baseline"]["annotation_errors"] == 3
        assert engine["baseline"]["runtime_errors"] == 0
        assert engine["gated"]["policy_rejections"] == 0
