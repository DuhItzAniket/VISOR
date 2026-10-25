"""Package evidence preserves notice bytes, actual origins and unresolved cases."""

import json
import runpy
import sys
from pathlib import Path, PurePosixPath
from types import ModuleType, SimpleNamespace

import pytest

from visor.distribution_audit import (
    COMPONENTS,
    artifact_inventory,
    digest,
    relative_path,
    stage_notices,
    verify_notice_index,
)


@pytest.fixture
def audit_inputs(tmp_path):
    packages = {}
    for name in COMPONENTS:
        root = tmp_path / "installed" / name
        root.mkdir(parents=True)
        (root / "LICENSE.txt").write_bytes(b"Copyright and license\r\nVerbatim bytes\r\n")
        packages[name] = SimpleNamespace(
            version="6.11.2", metadata={"Name": name, "License": "test declaration"},
            files=[PurePosixPath("LICENSE.txt")], locate_file=lambda path, root=root: root / str(path))
    snapshot = tmp_path / "snapshot"
    (snapshot / "qt/LICENSES").mkdir(parents=True)
    notice = snapshot / "qt/LICENSES/LGPL.txt"
    notice.write_bytes(b"Upstream license bytes\n")
    source = {"qt_version": "6.11.2", "repositories": [], "files": [
        {"path": "qt/LICENSES/LGPL.txt", "sha256": digest(notice), "source_url": "https://example.invalid/pinned"}]}
    (snapshot / "sources.json").write_text(json.dumps(source))
    runtime = tmp_path / "python-LICENSE.txt"
    runtime.write_bytes(b"Python runtime license\n")
    return packages, snapshot, runtime


def test_stage_and_verify_notices_offline_without_optional_models(tmp_path, audit_inputs):
    packages, snapshot, runtime = audit_inputs
    seen = []

    def distribution(name):
        seen.append(name)
        return packages[name]

    target = tmp_path / "staged"
    document = stage_notices(target, snapshot, distribution=distribution, runtime_notice=runtime)
    assert set(seen) == set(COMPONENTS)  # no Torch, model setup or network probe
    assert verify_notice_index(target / "notices.json") == len(document["files"]) == 10
    with pytest.raises(ValueError, match="runtime does not match"):
        verify_notice_index(target / "notices.json", qt_version="different")
    assert (target / "installed/numpy/LICENSE.txt").read_bytes() == b"Copyright and license\r\nVerbatim bytes\r\n"
    assert document["review_status"] and "not a compliance certificate" in document["scope"].lower()
    (target / "installed/numpy/LICENSE.txt").write_bytes(b"changed")
    with pytest.raises(ValueError, match="integrity mismatch"):
        verify_notice_index(target / "notices.json")


@pytest.mark.parametrize("value", ["../secret", "C:/secret", "/absolute", "folder/../../secret", "\\\\host\\share"])
def test_manifest_paths_cannot_escape(value):
    with pytest.raises(ValueError, match="Unsafe"):
        relative_path(value)


def test_qt_snapshot_version_and_integrity_mismatches_fail(tmp_path, audit_inputs):
    packages, snapshot, runtime = audit_inputs
    packages["PySide6_Essentials"].version = "different"
    with pytest.raises(RuntimeError, match="does not match"):
        stage_notices(tmp_path / "version", snapshot, distribution=packages.__getitem__, runtime_notice=runtime)
    packages["PySide6_Essentials"].version = "6.11.2"
    (snapshot / "qt/LICENSES/LGPL.txt").write_bytes(b"changed upstream text")
    with pytest.raises(ValueError, match="snapshot integrity"):
        stage_notices(tmp_path / "corrupt", snapshot, distribution=packages.__getitem__, runtime_notice=runtime)


def test_missing_distribution_notices_cannot_appear_complete(tmp_path, audit_inputs):
    packages, snapshot, runtime = audit_inputs
    packages["numpy"].files = []
    with pytest.raises(RuntimeError, match="No installed license"):
        stage_notices(tmp_path / "missing", snapshot, distribution=packages.__getitem__, runtime_notice=runtime)


def test_file_inventory_matches_actual_bytes_and_keeps_unknown_origin(tmp_path, audit_inputs):
    packages, _, _ = audit_inputs
    source = Path(packages["numpy"].locate_file("demo.dll"))
    source.write_bytes(b"a native library")
    packages["numpy"].files.append(PurePosixPath("demo.dll"))
    bundle = tmp_path / "dist/VISOR"
    (bundle / "_internal").mkdir(parents=True)
    (bundle / "_internal/demo.dll").write_bytes(source.read_bytes())
    (bundle / "VISOR.exe").write_bytes(b"opaque generated executable")
    toc = tmp_path / "collect.toc"
    toc.write_text(repr(([('demo.dll', str(source), 'BINARY')],)))
    output = tmp_path / "inventory.json"
    result = artifact_inventory(bundle, toc, output, project_root=tmp_path, distribution=packages.__getitem__)
    library = next(row for row in result["files"] if row["path"].endswith("demo.dll"))
    assert library["sha256"] == digest(source)
    assert library["origin"]["component"] == "numpy"
    assert result["file_count"] == 2 and result["unresolved_origin_count"] == 1
    assert str(tmp_path) not in output.read_text()  # no developer filesystem paths published
    (bundle / "_internal/Qt6VirtualKeyboard.dll").write_bytes(b"unwanted plugin")
    with pytest.raises(RuntimeError, match="Unused excluded Qt"):
        artifact_inventory(bundle, toc, output, project_root=tmp_path, distribution=packages.__getitem__)


def test_notice_index_rejects_duplicate_paths(tmp_path, audit_inputs):
    packages, snapshot, runtime = audit_inputs
    target = tmp_path / "staged"
    document = stage_notices(target, snapshot, distribution=packages.__getitem__, runtime_notice=runtime)
    document["files"].append(document["files"][0])
    (target / "notices.json").write_text(json.dumps(document))
    with pytest.raises(ValueError, match="Duplicate"):
        verify_notice_index(target / "notices.json")


def test_overlapping_distribution_records_preserve_both_claims(tmp_path, audit_inputs):
    packages, _, _ = audit_inputs
    source = Path(packages["numpy"].locate_file("shared.dll"))
    source.write_bytes(b"shared runtime")
    packages["numpy"].files.append(PurePosixPath("shared.dll"))
    packages["opencv-contrib-python"].files = [PurePosixPath("shared.dll")]
    packages["opencv-contrib-python"].locate_file = packages["numpy"].locate_file
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "shared.dll").write_bytes(source.read_bytes())
    toc = tmp_path / "collect.toc"
    toc.write_text(repr(([('shared.dll', str(source), 'BINARY')],)))
    result = artifact_inventory(bundle, toc, tmp_path / "inventory.json", project_root=tmp_path,
                                distribution=packages.__getitem__)
    origin = result["files"][0]["origin"]
    assert origin["kind"] == "overlapping_distribution_records"
    assert {claim["component"] for claim in origin["claims"]} == {"numpy", "opencv-contrib-python"}


@pytest.mark.parametrize("kind", ["relative-internal", "absolute-internal", "escaping"])
def test_inventory_symlinks_are_portable_and_stay_inside_bundle(tmp_path, audit_inputs, kind):
    packages, _, _ = audit_inputs
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "real.bin").write_bytes(b"runtime")
    (tmp_path / "outside.bin").write_bytes(b"outside")
    target = Path("real.bin") if kind == "relative-internal" else bundle / "real.bin" if kind == "absolute-internal" else tmp_path / "outside.bin"
    try:
        (bundle / "alias.bin").symlink_to(target)
    except OSError:
        pytest.skip("Host does not permit unprivileged symlink creation")
    toc = tmp_path / "collect.toc"
    toc.write_text(repr(([],)))
    if kind == "relative-internal":
        result = artifact_inventory(bundle, toc, tmp_path / "inventory.json", project_root=tmp_path,
                                    distribution=packages.__getitem__)
        assert next(row for row in result["files"] if row["path"] == "alias.bin")["symlink_target"] == "real.bin"
    else:
        with pytest.raises(ValueError, match="symlink"):
            artifact_inventory(bundle, toc, tmp_path / "inventory.json", project_root=tmp_path,
                               distribution=packages.__getitem__)


@pytest.mark.parametrize("prefix,extension", [("", "dll"), ("lib", "so"), ("lib", "dylib")])
def test_custom_qt_hook_excludes_unused_plugins_and_keeps_image_decoders(monkeypatch, prefix, extension):
    names = ["qpdf", "qtvirtualkeyboardplugin", "qjpeg", "qtiff", "qwebp", "qsvg", "qibusplatforminputcontextplugin"]
    binaries = [(f"plugins/{prefix}{name}.{extension}", "plugins") for name in names]
    qt = ModuleType("PyInstaller.utils.hooks.qt")
    qt.add_qt6_dependencies = lambda path: (["PySide6.QtCore"], binaries, [])
    monkeypatch.setitem(sys.modules, "PyInstaller.utils.hooks.qt", qt)
    hook = Path(__file__).resolve().parents[1] / "scripts/pyinstaller_hooks/hook-PySide6.QtGui.py"
    result = runpy.run_path(str(hook))
    assert result["binaries"] == binaries[2:]
    assert result["hiddenimports"] == ["PySide6.QtCore"]
