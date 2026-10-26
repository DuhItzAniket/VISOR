"""Derive exact internal link relationships without inventing library ownership."""

from __future__ import annotations

import hashlib
import json
import posixpath
from collections import Counter
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

from visor.distribution_audit import relative_path


def _link_destination(parent: str, target: str, remainder: tuple[str, ...]) -> str:
    target = target.replace("\\", "/")
    if not target or PureWindowsPath(target).drive or target.startswith("/"):
        raise ValueError("Inventory link has an absolute/empty target.")
    resolved = posixpath.normpath(posixpath.join(parent, target, *remainder))
    if resolved == ".." or resolved.startswith("../"):
        raise ValueError("Inventory link escapes the frozen root.")
    return resolved


def trace_inventory(raw: bytes, build_info: dict[str, Any]) -> dict[str, Any]:
    fingerprint = hashlib.sha256(raw).hexdigest()
    if fingerprint != build_info["artifact_inventory"]["sha256"]:
        raise ValueError("Inventory hash does not match build-info.")
    inventory = json.loads(raw.decode("utf-8"))
    if inventory.get("kind") != "frozen_filesystem_inventory" or inventory.get("schema_version") != 1:
        raise ValueError("Unsupported inventory kind/schema.")
    records = {}
    for row in inventory["files"]:
        name = relative_path(row["path"]).as_posix()
        if (name in records or name == "." or not isinstance(row["origin"], dict)
                or not isinstance(row["origin"].get("kind"), str) or not row["origin"]["kind"]):
            raise ValueError("Duplicate or invalid inventory entry.")
        records[name] = row
    links = {name: row["symlink_target"] for name, row in records.items() if "symlink_target" in row}
    # Validate every target, even links whose original collection origin is known.
    for name, target in links.items():
        _link_destination(posixpath.dirname(name), target, ())

    def resolve_link(name: str) -> dict[str, Any]:
        current = name
        visited = set()
        for _ in range(64):
            if current in visited:
                return {"relationship": "unresolved_link", "reason": "cycle"}
            visited.add(current)
            parts = PurePosixPath(current).parts
            prefix = next((posixpath.join(*parts[:index]) for index in range(1, len(parts) + 1)
                           if posixpath.join(*parts[:index]) in links), None)
            if prefix is None:
                target_row = records.get(current)
                if target_row is not None:
                    known = target_row["origin"].get("kind") != "unresolved"
                    return {"relationship": "exact_file_target" if known else "exact_file_target_unresolved",
                            "target_path": current, "target_origin": target_row["origin"]}
                directory_prefix = "" if current == "." else current + "/"
                descendants = sum(path.startswith(directory_prefix) for path in records)
                if descendants:
                    return {"relationship": "directory_layout", "target_path": current,
                            "inventoried_descendants": descendants}
                return {"relationship": "unresolved_link", "reason": "target_not_inventoried", "target_path": current}
            suffix = parts[len(PurePosixPath(prefix).parts):]
            current = _link_destination(posixpath.dirname(prefix), links[prefix], suffix)
        return {"relationship": "unresolved_link", "reason": "hop_limit"}

    unresolved = {name: row for name, row in records.items() if row["origin"].get("kind") == "unresolved"}
    relationships = [{"path": name, "original_origin": row["origin"], **resolve_link(name)}
                     for name, row in unresolved.items() if name in links]
    regular = [row for name, row in unresolved.items() if name not in links]
    return {"schema_version": 1, "kind": "derived_inventory_origin_review", "inventory_sha256": fingerprint,
            "source_revision": build_info.get("source_revision"), "system": build_info["system"],
            "architecture": build_info["architecture"],
            "trace_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "summary": {"frozen_entries": len(records), "original_unresolved_entries": len(unresolved),
                        "unresolved_regular_files": len(regular), "unresolved_link_entries": len(relationships),
                        "link_relationships": dict(Counter(row["relationship"] for row in relationships)),
                        "regular_source_areas": dict(Counter(row["origin"].get("source_area", "unspecified") for row in regular))},
            "link_relationships": relationships, "unresolved_regular_files": regular,
            "scope": "Exact lexical link targets within hashed inventory metadata. Original origins are unchanged. "
                     "Target package ownership is not subcomponent licensing; native/embedded internals remain opaque. "
                     "Directory links do not establish library ownership. Not a complete SBOM or compliance conclusion."}
