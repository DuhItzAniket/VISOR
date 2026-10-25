"""Published summaries can be recomputed from their complete raw rows."""

import gzip
import hashlib
import json
from pathlib import Path

import pytest

from visor.evaluate import summarize
from visor.reliability_study import select_gates


@pytest.mark.parametrize("name,attempts,revision", [("synthetic-20261025.json.gz", 18, "b2c7f0b"),
                                                  ("hpatches-sample-20261025.json.gz", 72, "b2c7f0b"),
                                                  ("reliability-development-20261025.json.gz", 192, "dec9b33")])
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
