"""Installer checks refuse user machines and preserve evidence on test failures."""

import importlib.util
import json
from pathlib import Path

import pytest


@pytest.fixture
def checker():
    path = Path(__file__).resolve().parents[1] / "scripts/verify_installer.py"
    spec = importlib.util.spec_from_file_location("visor_installer_check", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("actions,environment", [("false", "github-hosted"), ("true", "self-hosted"), ("true", "")])
def test_local_and_self_hosted_installation_is_refused(checker, monkeypatch, actions, environment):
    monkeypatch.setenv("GITHUB_ACTIONS", actions)
    monkeypatch.setenv("RUNNER_ENVIRONMENT", environment)
    with pytest.raises(RuntimeError, match="disposable"):
        checker.require_disposable_runner()


@pytest.mark.parametrize("system", ["Windows", "Linux"])
def test_existing_installations_are_never_replaced(checker, monkeypatch, tmp_path, system):
    calls = []
    monkeypatch.setattr(checker, "run", lambda *args, **kwargs: calls.append(args))
    monkeypatch.setattr(checker, "windows_registered" if system == "Windows" else "linux_registered", lambda: True)
    function = checker.check_windows if system == "Windows" else checker.check_linux
    with pytest.raises(RuntimeError, match="refusing"):
        function(tmp_path / "installer", tmp_path, tmp_path, {}, {})
    assert calls == []


def test_failed_installed_workflow_is_recorded_as_failure(checker, monkeypatch, tmp_path):
    monkeypatch.setattr(checker, "require_disposable_runner", lambda: None)
    monkeypatch.setattr(checker.platform, "system", lambda: "Windows")
    (tmp_path / "installers").mkdir()
    (tmp_path / "installers/VISOR-0.2.0-windows-setup.exe").write_bytes(b"Never executed")
    (tmp_path / "build-info.json").write_text(json.dumps({"version": "0.2.0", "system": "Windows", "source_revision": "a" * 40}),
                                            encoding="utf-8")

    def fail(*args):
        raise RuntimeError("Failed installed fixture")

    monkeypatch.setattr(checker, "check_windows", fail)
    report = tmp_path / "installer-report.json"
    assert checker.verify(tmp_path, report) == 1
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["success"] is False and "Failed installed fixture" in data["error"]
