"""Candidate assets must match successful evidence and exact tested package bytes."""

import json
import shutil

import pytest

from visor.distribution_audit import digest
from visor.release_preparation import prepare_candidate


@pytest.fixture
def release_inputs(tmp_path):
    dist = tmp_path / "dist"
    (dist / "installers").mkdir(parents=True)
    installer = dist / "installers/VISOR-0.2.0-windows-setup.exe"
    installer.write_bytes(b"Installer-bytes fixture; never executed")
    (dist / "installers/VISOR-0.2.0-windows-amd64.zip").write_bytes(b"Portable-bytes fixture")
    inventory = dist / "artifact-inventory.json"
    inventory.write_text(json.dumps({"kind": "frozen_filesystem_inventory", "files": []}), encoding="utf-8")
    info = {"version": "0.2.0", "system": "Windows", "architecture": "AMD64", "source_revision": "a" * 40,
            "artifact_inventory": {"sha256": digest(inventory)}}
    (dist / "build-info.json").write_text(json.dumps(info), encoding="utf-8")
    (dist / "smoke-report.json").write_text(json.dumps({"success": True, "version": "0.2.0", "system": "Windows"}),
                                           encoding="utf-8")
    (dist / "installer-report.json").write_text(json.dumps({
        "kind": "host_installer_check", "success": True, "version": "0.2.0", "system": "Windows",
        "source_revision": "a" * 40,
        "installer": {"file": installer.name, "sha256": digest(installer), "bytes": installer.stat().st_size},
    }), encoding="utf-8")
    return dist


def test_candidate_is_flat_complete_and_all_checksums_match(release_inputs, tmp_path):
    output = tmp_path / "candidate"
    manifest = prepare_candidate(release_inputs, output)
    assert manifest["release_signing_verified"] is False and manifest["kind"] == "validation_release_candidate"
    assert len(manifest["files"]) == 6
    assert all((output / row["file"]).is_file() and digest(output / row["file"]) == row["sha256"]
               for row in manifest["files"])
    for line in (output / manifest["checksum_file"]).read_text(encoding="utf-8").splitlines():
        expected, name = line.split("  ", 1)
        assert digest(output / name) == expected
    assert len(list(output.iterdir())) == 8  # packages, evidence, manifest, checksums
    with pytest.raises(FileExistsError):
        prepare_candidate(release_inputs, output)


@pytest.mark.parametrize("change", ["failed_smoke", "failed_install", "other_source", "inventory_tamper",
                                    "installer_tamper", "stale_asset", "missing_archive", "unsafe_version"])
def test_unverified_or_stale_assets_never_produce_a_candidate(release_inputs, tmp_path, change):
    dist = release_inputs
    if change == "inventory_tamper":
        (dist / "artifact-inventory.json").write_text("{}", encoding="utf-8")
    elif change == "installer_tamper":
        (dist / "installers/VISOR-0.2.0-windows-setup.exe").write_bytes(b"Changed after the installation check")
    elif change == "stale_asset":
        (dist / "installers/VISOR-0.1.0-windows-setup.exe").write_bytes(b"Old installer")
    elif change == "missing_archive":
        path = dist / "installers/VISOR-0.2.0-windows-amd64.zip"
        assert path.resolve().is_relative_to(tmp_path.resolve())
        path.unlink()
    else:
        name = "smoke-report.json" if change == "failed_smoke" else "build-info.json" if change == "unsafe_version" else "installer-report.json"
        path = dist / name
        data = json.loads(path.read_text(encoding="utf-8"))
        if change.startswith("failed"):
            data["success"] = False
        elif change == "other_source":
            data["source_revision"] = "b" * 40
        else:
            data["version"] = "../../outside"
        path.write_text(json.dumps(data), encoding="utf-8")
    output = tmp_path / "candidate"
    with pytest.raises(ValueError):
        prepare_candidate(dist, output)
    assert not output.exists()


def test_evidence_changed_during_staging_is_rejected_atomically(release_inputs, tmp_path, monkeypatch):
    original = shutil.copyfile

    def change(source, target):
        if source.name == "build-info.json":
            source.write_text("{}", encoding="utf-8")
        return original(source, target)

    monkeypatch.setattr(shutil, "copyfile", change)
    output = tmp_path / "candidate"
    with pytest.raises(ValueError, match="bytes changed"):
        prepare_candidate(release_inputs, output)
    assert not output.exists() and not list(tmp_path.glob("release-prep-*"))
