"""Bundled validation requires project notices without asserting third-party completeness."""

import json
import os
import shutil
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import qVersion

from visor.distribution_audit import digest
from visor.smoke_check import run_smoke_check


def test_frozen_smoke_fails_when_project_notice_files_are_absent(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    report = tmp_path / "report.json"
    assert run_smoke_check(report) == 1
    data = json.loads(report.read_text())
    assert data["success"] is False and "LICENSE" in data["error"]


def test_frozen_project_notices_and_classical_workflow_pass(tmp_path, monkeypatch):
    root = Path(__file__).resolve().parents[1]
    for name in ("LICENSE", "NOTICE"):
        shutil.copyfile(root / name, tmp_path / name)
    notices = tmp_path / "third-party"
    notices.mkdir()
    (notices / "fixture.txt").write_bytes(b"A notice-integrity fixture")
    (notices / "notices.json").write_text(json.dumps({"schema_version": 1, "kind": "collected_notices", "qt_version": qVersion(), "files": [
        {"path": "fixture.txt", "sha256": digest(notices / "fixture.txt"), "bytes": (notices / "fixture.txt").stat().st_size}]}))
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    report = tmp_path / "report.json"
    assert run_smoke_check(report) == 0
    data = json.loads(report.read_text())
    assert data["success"] is True
    assert "VISOR Apache-2.0 LICENSE/NOTICE files (project only)" in data["checks"]
    assert "project round trip" in data["checks"]
