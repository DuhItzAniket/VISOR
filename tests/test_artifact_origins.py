"""Trace exact link targets, preserving unknown and overlapping ownership evidence."""

import copy
import hashlib
import json

import pytest

from visor.artifact_origins import trace_inventory


def trace(files):
    raw = json.dumps({"schema_version": 1, "kind": "frozen_filesystem_inventory", "files": files}).encode()
    return trace_inventory(raw, {"artifact_inventory": {"sha256": hashlib.sha256(raw).hexdigest()},
                                 "source_revision": "a" * 40, "system": "Darwin", "architecture": "arm64"})


def test_framework_directory_alias_resolves_to_exact_record_without_changing_origins():
    owner = {"kind": "installed_distribution", "component": "PySide6_Essentials", "package_path": "QtCore"}
    files = [{"path": "QtCore.framework/QtCore", "origin": {"kind": "unresolved"}, "symlink_target": "Versions/Current/QtCore"},
             {"path": "QtCore.framework/Versions/Current", "origin": {"kind": "unresolved"}, "symlink_target": "A"},
             {"path": "QtCore.framework/Versions/A/QtCore", "origin": owner}]
    before = copy.deepcopy(files)
    result = trace(files)
    assert files == before
    file_link, directory_link = result["link_relationships"]
    assert file_link["target_path"] == "QtCore.framework/Versions/A/QtCore" and file_link["target_origin"] == owner
    assert directory_link["relationship"] == "directory_layout" and "target_origin" not in directory_link
    assert result["summary"]["original_unresolved_entries"] == 2
    assert result["summary"]["unresolved_regular_files"] == 0


@pytest.mark.parametrize("target", ["../../outside", "/absolute", "C:/outside", "\\\\server\\share"])
def test_link_escapes_are_rejected(target):
    with pytest.raises(ValueError, match="link"):
        trace([{"path": "lib/alias", "origin": {"kind": "unresolved"}, "symlink_target": target}])


def test_unknown_files_missing_targets_and_cycles_never_gain_an_owner():
    files = [{"path": "system.so", "origin": {"kind": "unresolved", "source_area": "system"}},
             {"path": "alias", "origin": {"kind": "unresolved"}, "symlink_target": "system.so"},
             {"path": "missing", "origin": {"kind": "unresolved"}, "symlink_target": "absent"},
             {"path": "a", "origin": {"kind": "unresolved"}, "symlink_target": "b"},
             {"path": "b", "origin": {"kind": "unresolved"}, "symlink_target": "a"}]
    result = trace(files)
    assert result["summary"]["unresolved_regular_files"] == 1
    assert result["summary"]["regular_source_areas"] == {"system": 1}
    assert result["link_relationships"][0]["relationship"] == "exact_file_target_unresolved"
    assert {row.get("reason") for row in result["link_relationships"][1:]} == {"target_not_inventoried", "cycle"}


def test_overlapping_claims_are_retained_and_wrong_inventory_hash_is_rejected():
    origin = {"kind": "overlapping_distribution_records", "claims": [{"component": "first"}, {"component": "second"}]}
    result = trace([{"path": "native.dylib", "origin": origin},
                    {"path": "alias", "origin": {"kind": "unresolved"}, "symlink_target": "native.dylib"}])
    assert result["link_relationships"][0]["target_origin"] == origin
    with pytest.raises(ValueError, match="hash"):
        trace_inventory(b"{}", {"artifact_inventory": {"sha256": "wrong"}})


def test_missing_origin_kind_cannot_appear_resolved():
    with pytest.raises(ValueError, match="invalid"):
        trace([{"path": "unknown", "origin": {}}])
