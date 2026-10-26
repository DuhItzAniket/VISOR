"""Capture build-host dpkg claims and exact notice bytes, without license conclusions."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import platform
import re
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Any

from visor.distribution_audit import digest, relative_path

PACKAGE = re.compile(r"[a-z0-9][a-z0-9+.-]*(?::[a-z0-9][a-z0-9-]*)?")
COMMON_LICENSE = re.compile(rb"/usr/share/common-licenses/([A-Za-z0-9][A-Za-z0-9+_.-]*)")


def _query(arguments: list[str]) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["LC_ALL"] = "C.UTF-8"
    return subprocess.run(["dpkg-query", *arguments], capture_output=True, text=True, env=environment, timeout=20, check=False)


@lru_cache(maxsize=512)
def _package_metadata(name: str) -> dict[str, Any]:
    if not PACKAGE.fullmatch(name):
        raise ValueError("Invalid package name in dpkg ownership output.")
    result = _query(["--show", "--showformat=${binary:Package}\t${Version}\t${source:Package}\t${source:Version}\t${db:Status-Status}", name])
    if result.returncode:
        raise RuntimeError(f"Cannot read dpkg metadata for {name}.")
    values = result.stdout.strip().split("\t")
    if len(values) != 5 or not PACKAGE.fullmatch(values[0]):
        raise ValueError("Unexpected dpkg package metadata.")
    return dict(zip(("name", "version", "source_package", "source_version", "status"), values, strict=True))


def dpkg_owners(source: Path) -> list[dict[str, Any]]:
    """Use literal, canonical-equivalent paths only; never search by basename."""
    actual = source.resolve()
    candidates = [actual]
    if actual.is_relative_to(Path("/usr/lib")):
        candidates.append(Path("/lib") / actual.relative_to("/usr/lib"))
    names = set()
    for candidate in candidates:
        if not candidate.is_file() or candidate.resolve() != actual:
            continue
        result = _query(["--search", str(candidate)])
        if result.returncode:
            continue
        for line in result.stdout.splitlines():
            owners, separator, path = line.rpartition(": ")
            if not separator or Path(path).resolve() != actual:
                continue
            for name in owners.split(", "):
                if PACKAGE.fullmatch(name):
                    names.add(name)
    return [_package_metadata(name) for name in sorted(names)]


def collect_system_review(toc: Path, build_info: dict[str, Any], output: Path, *, package_lookup=dpkg_owners,
                          roots: tuple[tuple[Path, str], ...] = ((Path("/usr/lib"), "usr/lib"), (Path("/lib"), "lib")),
                          doc_root: Path = Path("/usr/share/doc"),
                          common_root: Path = Path("/usr/share/common-licenses")) -> dict[str, Any]:
    """Write review evidence only; do not mutate the frozen app or its inventory."""
    if output.exists() or output.is_symlink():
        raise FileExistsError("System review output already exists.")
    entries = ast.literal_eval(toc.read_text(encoding="utf-8"))[0]
    selected = []
    for name, source, kind in entries:
        if kind not in ("BINARY", "EXTENSION"):
            continue
        path = Path(source).resolve()
        match = next(((root.resolve(), label) for root, label in roots if path.is_relative_to(root.resolve())), None)
        if match is None:
            continue
        if not path.is_file():
            raise ValueError("A collected system source file is no longer available on this host.")
        selected.append((relative_path(name).as_posix(), path, match))
    output.mkdir(parents=True)
    copied: dict[str, dict[str, Any]] = {}
    missing = []
    resolutions = []

    def copy_notice(source: Path, destination: str, area: str, source_relative: str) -> None:
        if destination in copied:
            return
        allowed = (doc_root.resolve(), common_root.resolve())
        if not any(source.resolve().is_relative_to(root) for root in allowed):
            raise ValueError("System notice link escapes the documentation/common-license roots.")
        data = source.read_bytes()
        target = output / str(relative_path(destination))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        copied[destination] = {"path": destination, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
                               "source_area": area, "source_relative_path": source_relative}
        # Preserve literal external license references; do not parse/select legal terms.
        for value in sorted(set(COMMON_LICENSE.findall(data))):
            filename = value.decode("ascii")
            notice = common_root / filename
            # Windows can treat a trailing period as an alias of the same file;
            # use the actual directory spelling to keep this rule portable.
            if filename.endswith(".") and filename not in {path.name for path in common_root.iterdir()}:
                candidate = filename.rstrip(".")
                if candidate and (common_root / candidate).is_file():
                    resolutions.append({"referenced_by": destination, "literal_token": filename,
                                        "copied_name": candidate, "rule": "existing_file_after_sentence_period_removed"})
                    filename, notice = candidate, common_root / candidate
            if notice.is_file():
                copy_notice(notice, f"common-licenses/{filename}", "common_licenses", filename)
            else:
                missing.append({"kind": "common_license", "name": filename, "referenced_by": destination})

    packages: dict[str, dict[str, Any]] = {}
    libraries = []
    for name, source, (root, label) in selected:
        claims = package_lookup(source)
        for package in claims:
            package_name = package["name"]
            if not PACKAGE.fullmatch(package_name):
                raise ValueError("Invalid package claim.")
            if package_name in packages:
                continue
            entry = {**package, "copyright_collected": False}
            copyright_path = doc_root / package_name.split(":", 1)[0] / "copyright"
            if copyright_path.is_file():
                destination = f"packages/{package_name.replace(':', '__')}/copyright"
                copy_notice(copyright_path, destination, "package_documentation",
                            copyright_path.relative_to(doc_root).as_posix())
                entry.update({"copyright_collected": True, "notice_path": destination})
            else:
                missing.append({"kind": "package_copyright", "name": package_name})
            packages[package_name] = entry
        libraries.append({"collection_path": name, "source_root": label,
                          "source_relative_path": source.relative_to(root).as_posix(),
                          "source_sha256_at_lookup": digest(source), "package_claims": [package["name"] for package in claims]})
    try:
        release = platform.freedesktop_os_release()
    except OSError:
        release = {}
    document = {"schema_version": 1, "kind": "build_host_system_notice_review",
                "source_revision": build_info["source_revision"], "system": build_info["system"],
                "architecture": build_info["architecture"], "collection_toc_sha256": digest(toc),
                "collector_code_sha256": digest(Path(__file__)),
                "artifact_inventory_sha256": build_info.get("artifact_inventory", {}).get("sha256"),
                "build_info_content_sha256": hashlib.sha256(json.dumps(build_info, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
                "github_run_id": os.environ.get("GITHUB_RUN_ID"),
                "os_release": {key: release[key] for key in ("ID", "VERSION_ID", "PRETTY_NAME") if key in release},
                "libraries": libraries, "packages": sorted(packages.values(), key=lambda package: package["name"]),
                "files": sorted(copied.values(), key=lambda entry: entry["path"]), "missing_notices": missing,
                "reference_resolutions": resolutions,
                "summary": {"collected_system_sources": len(libraries), "package_claims": len(packages),
                            "unclaimed_sources": sum(not row["package_claims"] for row in libraries),
                            "copied_notice_files": len(copied), "missing_notice_references": len(missing)},
                "scope": "dpkg database ownership claims and source-file hashes on the executing build host. "
                         "Exact package notices/literal common-license references are copied without choosing terms. "
                         "Review evidence is separate from installed notices; frozen app/inventory unchanged. "
                         "Not binary authenticity, complete native/subcomponent licensing, source-offer or compliance certification."}
    (output / "manifest.json").write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8", newline="\n")
    return document
