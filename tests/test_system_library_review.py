"""Build-host notice evidence preserves exact bytes, database claims and gaps."""

import json
from types import SimpleNamespace

import pytest

from visor import system_library_review as review
from visor.distribution_audit import digest


@pytest.fixture
def inputs(tmp_path):
    system = tmp_path / "system"
    system.mkdir()
    binary = system / "libexample.so.1"
    binary.write_bytes(b"Native binary fixture; never loaded")
    outside = tmp_path / "wheel-library.so"
    outside.write_bytes(b"Package library outside OS scope")
    toc = tmp_path / "COLLECT-00.toc"
    toc.write_text(repr(([('libexample.so.1', str(binary), 'BINARY'), ('wheel.so', str(outside), 'BINARY')],)), encoding="utf-8")
    docs, common = tmp_path / "docs", tmp_path / "common"
    (docs / "libexample").mkdir(parents=True)
    common.mkdir()
    original = b"Copyright \xff exact bytes\r\nLicense text: /usr/share/common-licenses/MIT\r\n"
    (docs / "libexample/copyright").write_bytes(original)
    (common / "MIT").write_bytes(b"Common license fixture\n")
    package = {"name": "libexample:amd64", "version": "1.2-1", "source_package": "example", "source_version": "1.2-1", "status": "installed"}
    info = {"source_revision": "a" * 40, "system": "Linux", "architecture": "x86_64"}
    return system, binary, toc, docs, common, original, package, info


def collect(tmp_path, inputs, packages):
    system, _, toc, docs, common, _, _, info = inputs
    return review.collect_system_review(toc, info, tmp_path / "output", package_lookup=lambda path: packages,
                                        roots=((system, "system-fixture"),), doc_root=docs, common_root=common)


def test_exact_notice_bytes_common_reference_hashes_and_system_scope(tmp_path, inputs):
    _, binary, _, _, _, original, package, _ = inputs
    report = collect(tmp_path, inputs, [package])
    assert report["summary"] == {"collected_system_sources": 1, "package_claims": 1, "unclaimed_sources": 0,
                                 "copied_notice_files": 2, "missing_notice_references": 0}
    assert report["libraries"][0]["source_sha256_at_lookup"] == digest(binary)
    assert (tmp_path / "output/packages/libexample__amd64/copyright").read_bytes() == original
    for entry in report["files"]:
        assert digest(tmp_path / "output" / entry["path"]) == entry["sha256"]
    assert str(tmp_path) not in json.dumps(report)
    with pytest.raises(FileExistsError):
        collect(tmp_path, inputs, [package])


def test_missing_notices_and_unclaimed_sources_remain_explicit(tmp_path, inputs):
    _, _, _, docs, _, _, package, _ = inputs
    path = docs / "libexample/copyright"
    assert path.resolve().is_relative_to(tmp_path.resolve())
    path.unlink()
    report = collect(tmp_path, inputs, [package])
    assert report["packages"][0]["copyright_collected"] is False
    assert report["missing_notices"] == [{"kind": "package_copyright", "name": "libexample:amd64"}]
    other = tmp_path / "other"
    other.mkdir()
    report = collect(other, inputs, [])
    assert report["summary"]["unclaimed_sources"] == 1 and report["packages"] == []


def test_overlapping_package_claims_are_not_collapsed(tmp_path, inputs):
    package = inputs[6]
    report = collect(tmp_path, inputs, [package, {**package, "name": "libanother:amd64"}])
    assert report["libraries"][0]["package_claims"] == ["libexample:amd64", "libanother:amd64"]
    assert len(report["packages"]) == 2


def test_common_license_missing_reference_is_recorded(tmp_path, inputs):
    common = inputs[4]
    path = common / "MIT"
    assert path.resolve().is_relative_to(tmp_path.resolve())
    path.unlink()
    report = collect(tmp_path, inputs, [inputs[6]])
    assert report["missing_notices"][0]["kind"] == "common_license"
    assert report["missing_notices"][0]["referenced_by"] == "packages/libexample__amd64/copyright"


def test_notice_symlink_cannot_escape_documentation_roots(tmp_path, inputs):
    docs = inputs[3]
    path = docs / "libexample/copyright"
    assert path.resolve().is_relative_to(tmp_path.resolve())
    path.unlink()
    outside = tmp_path / "outside-copyright"
    outside.write_bytes(b"Outside approved notice roots")
    try:
        path.symlink_to(outside)
    except OSError:
        pytest.skip("Host does not permit unprivileged symlink creation")
    with pytest.raises(ValueError, match="escapes"):
        collect(tmp_path, inputs, [inputs[6]])


def test_dpkg_search_uses_exact_path_and_preserves_all_valid_database_claims(tmp_path, monkeypatch):
    binary = tmp_path / "lib.so"
    binary.write_bytes(b"never loaded")
    seen = []

    def query(arguments):
        seen.append(arguments)
        return SimpleNamespace(returncode=0, stdout=f"libfirst:amd64, libsecond:amd64: {binary.resolve()}\nlibwrong: /other\n")

    monkeypatch.setattr(review, "_query", query)
    monkeypatch.setattr(review, "_package_metadata", lambda name: {"name": name})
    assert review.dpkg_owners(binary) == [{"name": "libfirst:amd64"}, {"name": "libsecond:amd64"}]
    assert seen == [["--search", str(binary.resolve())]]
