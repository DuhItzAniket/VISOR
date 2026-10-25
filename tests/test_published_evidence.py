"""Published summaries can be recomputed from their complete raw rows."""

import gzip
import json
from pathlib import Path

import pytest

from visor.evaluate import summarize


@pytest.mark.parametrize("name,attempts", [("synthetic-20261025.json.gz", 18),
                                         ("hpatches-sample-20261025.json.gz", 72)])
def test_raw_evidence_summaries_agree(name, attempts):
    path = Path(__file__).resolve().parents[1] / "docs/evaluation" / name
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        report = json.load(stream)
    assert len(report["rows"]) == attempts
    assert report["runtime"]["source_revision"].startswith("b2c7f0b")
    assert report["runtime"]["source_dirty"] is False
    assert summarize(report["rows"]) == report["summary"]
