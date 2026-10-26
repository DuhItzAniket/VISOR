"""Source-wheel checks reject tampering and incomplete packaging."""

import importlib.util
from pathlib import Path
from zipfile import ZipFile

import pytest

spec = importlib.util.spec_from_file_location("source_wheel_check", Path(__file__).parents[1] / "scripts/verify_source_wheel.py")
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


@pytest.fixture
def wheel_source(tmp_path):
    package = tmp_path / "src/visor"
    (package / "assets/icons").mkdir(parents=True)
    (package / "__init__.py").write_text('__version__ = "0.2.0"\n', encoding="utf-8")
    (package / "app.py").write_text('"""Original app module."""\n', encoding="utf-8")
    (package / "assets/icons/open.svg").write_text('<svg/>', encoding="utf-8")
    (tmp_path / "LICENSE").write_bytes(b"Complete project license fixture")
    (tmp_path / "NOTICE").write_bytes(b"Complete project notice fixture")
    return tmp_path


def make_wheel(root, changes=None):
    prefix = "visor_registration-0.2.0.dist-info/"
    files = {"visor/" + path.relative_to(root / "src/visor").as_posix(): path.read_bytes()
             for path in (root / "src/visor").rglob("*") if path.is_file()}
    files.update({prefix + "METADATA": b"Name: visor-registration\nVersion: 0.2.0\nLicense-Expression: Apache-2.0\nRequires-Dist: opencv-contrib-python-headless>=4.9\n\n",
                  prefix + "licenses/LICENSE": (root / "LICENSE").read_bytes(),
                  prefix + "licenses/NOTICE": (root / "NOTICE").read_bytes()})
    files.update(changes or {})
    wheel = root / "test.whl"
    with ZipFile(wheel, "w") as archive:
        for name, content in files.items():
            if content is not None:
                archive.writestr(name, content)
    return wheel


def test_actual_source_and_notice_bytes_are_verified_without_import(wheel_source):
    wheel = make_wheel(wheel_source)
    report = verifier.verify_source_wheel(wheel, wheel_source)
    assert report["source_modules"] == 2 and report["package_files"] == 3
    assert len(report["wheel_sha256"]) == 64


@pytest.mark.parametrize("changes,reason", [
    ({"visor/app.py": b"raise RuntimeError('tampered module must never run')"}, "bytes differ"),
    ({"visor/app.py": None}, "missing source"),
    ({"visor_registration-0.2.0.dist-info/licenses/NOTICE": b"Truncated"}, "NOTICE bytes"),
    ({"unexpected.pth": b"import arbitrary_module"}, "Unexpected wheel"),
    ({"../escaped": b"unsafe"}, "Unsafe wheel"),
    ({"visor_registration-0.2.0.dist-info/METADATA": b"Name: visor-registration\nVersion: 0.2.0\nLicense-Expression: Apache-2.0\nRequires-Dist: opencv-python\n\n"}, "single headless"),
    ({"visor_registration-0.2.0.dist-info/METADATA": b"Name: visor-registration\nName: another-package\nVersion: 0.2.0\nLicense-Expression: Apache-2.0\n\n"}, "unambiguous"),
])
def test_tampered_or_incomplete_wheels_are_rejected(wheel_source, changes, reason):
    with pytest.raises(ValueError, match=reason):
        verifier.verify_source_wheel(make_wheel(wheel_source, changes), wheel_source)


def test_cli_rejects_a_directory_with_multiple_wheels(wheel_source, monkeypatch):
    import sys

    wheel = make_wheel(wheel_source)
    (wheel_source / "stale.whl").write_bytes(wheel.read_bytes())
    monkeypatch.setattr(sys, "argv", ["verify_source_wheel", str(wheel_source), "--root", str(wheel_source)])
    with pytest.raises(SystemExit) as error:
        verifier.main()
    assert error.value.code == 2
