"""Installer checks refuse user machines and preserve evidence on test failures."""

import hashlib
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


@pytest.mark.parametrize("interfaces", [[(1, "lo")], [(1, "lo"), (2, "eth0")]])
def test_linux_install_requires_loopback_only(checker, monkeypatch, tmp_path, interfaces):
    monkeypatch.setattr(checker, "require_disposable_runner", lambda: None)
    monkeypatch.setattr(checker.platform, "system", lambda: "Linux")
    monkeypatch.setattr(checker.socket, "if_nameindex", lambda: interfaces)
    (tmp_path / "installers").mkdir()
    (tmp_path / "installers/visor.deb").write_bytes(b"Never executed")
    (tmp_path / "build-info.json").write_text(
        json.dumps({"version": "0.2.0", "system": "Linux", "source_revision": "a" * 40}), encoding="utf-8"
    )
    installed = []
    monkeypatch.setattr(checker, "check_linux", lambda *args: installed.append(args[0]))
    output = tmp_path / "installer-report.json"
    offline = interfaces == [(1, "lo")]
    assert checker.verify(tmp_path, output) == (0 if offline else 1)
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["success"] is offline
    assert bool(installed) is offline
    if offline:
        assert report["network"] == {"mode": "loopback_only", "interfaces": ["lo"]}
    else:
        assert report["network"] == {"mode": "unverified"}
        assert "eth0" in report["error"]


def test_linux_installed_notice_bytes_must_match(checker, tmp_path):
    installed = tmp_path / "installed"
    installed.mkdir()
    notice = installed / "copyright"
    notice.write_bytes(b"Example package notice\n")
    data = json.dumps({"files": [{"path": notice.name, "sha256": hashlib.sha256(notice.read_bytes()).hexdigest()}]})
    expected = tmp_path / "manifest.json"
    expected.write_text(data, encoding="utf-8")
    (installed / "manifest.json").write_text(data, encoding="utf-8")
    assert checker.verify_linux_notices(installed, expected) == 1
    notice.write_bytes(b"Changed notice\n")
    with pytest.raises(RuntimeError, match="differs from the build-host copy"):
        checker.verify_linux_notices(installed, expected)
