"""Check the notice bytes staged for Linux users without invoking an installer."""

import tarfile
from pathlib import Path
from zipfile import ZipFile

from scripts import build_desktop

from visor import system_library_review


def test_linux_both_packages_carry_the_same_notice_collection(tmp_path, monkeypatch):
    bundle = tmp_path / "dist/VISOR"
    bundle.mkdir(parents=True)
    (bundle / "VISOR").write_bytes(b"Frozen executable fixture")
    (bundle.parent / "build-info.json").write_text('{"system": "Linux"}', encoding="utf-8")
    icon = tmp_path / "src/visor/assets/visor.svg"
    icon.parent.mkdir(parents=True)
    icon.write_text("<svg/>", encoding="utf-8")
    notice = b"Exact license bytes\r\n"
    manifest = b'{"files":[{"path":"copyright"}]}\n'

    def collect(toc, info, output):
        assert toc == tmp_path / "build/VISOR/COLLECT-00.toc"
        assert info == {"system": "Linux"}
        output.mkdir()
        (output / "copyright").write_bytes(notice)
        (output / "manifest.json").write_bytes(manifest)

    def verify_debian_stage(command):
        assert command[:3] == ["dpkg-deb", "--root-owner-group", "--build"]
        stage = Path(command[3])
        control = (stage / "DEBIAN/control").read_text(encoding="utf-8")
        dependencies = next(line.removeprefix("Depends: ") for line in control.splitlines()
                            if line.startswith("Depends: "))
        # QtGui requires libEGL even when the X11 smoke disables GL integration.
        assert "libegl1" in dependencies.split(", ")
        docs = stage / "usr/share/doc/visor/system-notices"
        assert (docs / "manifest.json").read_bytes() == manifest
        assert (docs / "copyright").read_bytes() == notice
        debian_checks.append(command[4])

    debian_checks = []
    monkeypatch.setattr(build_desktop, "ROOT", tmp_path)
    monkeypatch.setattr(build_desktop.platform, "system", lambda: "Linux")
    monkeypatch.setattr(system_library_review, "collect_system_review", collect)
    monkeypatch.setattr(build_desktop, "run", verify_debian_stage)
    build_desktop.package(bundle, "0.2.0", "x86_64")

    installers = bundle.parent / "installers"
    assert debian_checks == [str(installers / "VISOR-0.2.0-linux-x86_64.deb")]
    with tarfile.open(installers / "VISOR-0.2.0-linux-x86_64.tar.gz", "r:gz") as archive:
        assert archive.extractfile("VISOR/VISOR").read() == b"Frozen executable fixture"
        assert archive.extractfile("VISOR-system-notices/manifest.json").read() == manifest
        assert archive.extractfile("VISOR-system-notices/copyright").read() == notice
    with ZipFile(bundle.parent / "system-notices.zip") as archive:
        assert archive.read("manifest.json") == manifest
        assert archive.read("copyright") == notice
    assert (bundle.parent / "system-notice-manifest.json").read_bytes() == manifest
