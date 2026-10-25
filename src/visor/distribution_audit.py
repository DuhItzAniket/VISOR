"""Offline notice collection and frozen-filesystem evidence, not legal certification."""

from __future__ import annotations

import ast
import hashlib
import json
import re
import sys
import sysconfig
from importlib import metadata
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

COMPONENTS = ("numpy", "opencv-contrib-python", "PySide6", "PySide6_Essentials", "PySide6_Addons", "shiboken6", "pyinstaller")
QT_COMPONENTS = {"PySide6", "PySide6_Essentials", "PySide6_Addons", "shiboken6"}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def relative_path(value: str) -> PurePosixPath:
    normalized = value.replace("\\", "/")
    path = PurePosixPath(normalized)
    if not normalized or path.is_absolute() or PureWindowsPath(normalized).drive or ".." in path.parts:
        raise ValueError(f"Unsafe notice path: {value}")
    return path


def _write_json(path: Path, document: dict[str, Any]) -> None:
    path.write_text(json.dumps(document, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def _is_notice(value: str) -> bool:
    name = PurePosixPath(value.replace("\\", "/")).name.upper()
    return name.startswith(("LICENSE", "LICENCE", "COPYING", "NOTICE", "COPYRIGHT")) and not name.endswith((".PY", ".PYC", ".XML"))


def python_notice() -> Path:
    locations = (Path(sys.base_prefix), Path(sysconfig.get_path("stdlib")))
    for directory in locations:
        for name in ("LICENSE.txt", "LICENSE"):
            candidate = directory / name
            if candidate.is_file():
                return candidate
    raise RuntimeError("Python runtime license was not found in the interpreter or stdlib directory.")


def stage_notices(destination: Path, qt_snapshot: Path, *, distribution=metadata.distribution,
                  runtime_notice: Path | None = None) -> dict[str, Any]:
    """Copy exact local distribution notices and a hash-verified pinned Qt corpus."""
    destination.mkdir(parents=True, exist_ok=True)
    files: list[dict[str, Any]] = []
    corpus = json.loads((qt_snapshot / "sources.json").read_text(encoding="utf-8"))
    actual_qt = distribution("PySide6_Essentials").version
    if corpus["qt_version"] != actual_qt:
        raise RuntimeError(f"Qt notice corpus {corpus['qt_version']} does not match installed PySide6 {actual_qt}.")
    qt_fallback_files = {"pyside-pyside-setup/LICENSES/LGPL-3.0-only.txt", "pyside-pyside-setup/LICENSES/GPL-3.0-only.txt"}
    has_qt_fallback = qt_fallback_files <= {entry["path"] for entry in corpus["files"]}

    def copy_notice(source: Path, relative: str, component: str) -> None:
        safe = relative_path(relative)
        target = destination / str(safe)
        if target.exists():
            raise ValueError(f"Duplicate staged notice: {safe}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        files.append({"path": safe.as_posix(), "sha256": digest(target), "bytes": target.stat().st_size,
                      "component": component})

    components = []
    for name in COMPONENTS:
        package = distribution(name)
        slug = re.sub(r"[-_.]+", "-", name).lower()
        candidates = [file for file in package.files or [] if _is_notice(str(file))]
        source_fallback = not candidates and name in QT_COMPONENTS and package.version == actual_qt and has_qt_fallback
        if not candidates and not source_fallback:
            raise RuntimeError(f"No installed license/notice files found for {name}.")
        for file in candidates:
            copy_notice(Path(package.locate_file(file)), f"installed/{slug}/{relative_path(str(file))}", name)
        components.append({"name": package.metadata.get("Name", name), "version": package.version,
                           "license_expression": package.metadata.get("License-Expression"),
                           "license_metadata": package.metadata.get("License"), "collected_notice_count": len(candidates),
                           "notice_source": "Pinned PySide source corpus; wheel has no separate notice file." if source_fallback
                                            else "Installed distribution files plus pinned Qt corpus where applicable.",
                           "scope": "Installed distribution notices; not proof all package files are bundled."})
    copy_notice(runtime_notice or python_notice(), "python/LICENSE.txt", "CPython")
    for entry in corpus["files"]:
        relative = relative_path(entry["path"])
        source = qt_snapshot / str(relative)
        if not source.resolve().is_relative_to(qt_snapshot.resolve()) or digest(source) != entry["sha256"]:
            raise ValueError(f"Qt notice snapshot integrity mismatch: {relative}")
        copy_notice(source, f"qt-upstream/{relative}", "Qt source notice corpus")
    copy_notice(qt_snapshot / "sources.json", "qt-upstream/sources.json", "Qt source notice corpus")
    document = {"schema_version": 1, "kind": "collected_notices", "python_version": sys.version.split()[0],
                "components": components, "qt_version": actual_qt, "qt_repositories": corpus["repositories"],
                "files": sorted(files, key=lambda entry: entry["path"]),
                "review_status": "Component/source-offer and redistribution obligations require artifact-specific review.",
                "scope": "Exact installed notice bytes plus upstream source corpus. Not a compliance certificate or complete SBOM."}
    _write_json(destination / "notices.json", document)
    (destination / "README.txt").write_text(
        "Third-party notices\n\nnotices.json records versions, copied notice hashes and pinned Qt source provenance.\n"
        "installed/ contains package-provided notices; python/ contains the actual interpreter license;\n"
        "qt-upstream/ contains a source notice corpus, including components not necessarily linked.\n"
        "VISOR's Apache-2.0 license does not replace these terms. Component/source-offer obligations\n"
        "still require review against the separate artifact-inventory.json.\n", encoding="utf-8", newline="\n")
    return document


def verify_notice_index(index: Path, *, qt_version: str | None = None) -> int:
    # Resolve the index first: macOS PyInstaller may symlink resource files from
    # Frameworks to Resources. Verify against their actual data directory.
    index = index.resolve()
    root = index.parent
    document = json.loads(index.read_text(encoding="utf-8"))
    if document.get("schema_version") != 1 or document.get("kind") != "collected_notices" or not document.get("files"):
        raise ValueError("Invalid or empty third-party notice index.")
    if qt_version is not None and document.get("qt_version") != qt_version:
        raise ValueError("Bundled Qt runtime does not match the notice corpus version.")
    seen = set()
    for entry in document["files"]:
        relative = relative_path(entry["path"])
        path = root / str(relative)
        if str(relative) in seen or not path.resolve().is_relative_to(root):
            raise ValueError("Duplicate or escaping notice path.")
        seen.add(str(relative))
        if path.stat().st_size != entry["bytes"] or digest(path) != entry["sha256"]:
            raise ValueError(f"Bundled notice integrity mismatch: {relative}")
    return len(seen)


def artifact_inventory(bundle: Path, toc_path: Path, output: Path, *, project_root: Path,
                       distribution=metadata.distribution) -> dict[str, Any]:
    """Hash actual frozen files, preserving unresolved/opaque ownership explicitly."""
    root = bundle.resolve()
    owners: dict[str, list[dict[str, Any]]] = {}
    for name in COMPONENTS:
        package = distribution(name)
        for file in package.files or []:
            owners.setdefault(str(Path(package.locate_file(file)).resolve()), []).append({
                "kind": "installed_distribution", "component": name, "package_path": str(file).replace("\\", "/")})
    entries = ast.literal_eval(toc_path.read_text(encoding="utf-8"))[0]
    origins: dict[str, dict[str, Any]] = {}
    for name, source, kind in entries:
        path = Path(source).resolve()
        claims = owners.get(str(path), [])
        origin = (claims[0] if len(claims) == 1 else {"kind": "overlapping_distribution_records", "claims": claims}
                  if claims else None)
        if origin is None:
            if path.is_relative_to(project_root.resolve() / "src"):
                origin = {"kind": "project_source", "path": path.relative_to(project_root).as_posix()}
            elif path.is_relative_to(Path(sys.base_prefix).resolve()) and not path.is_relative_to(Path(sysconfig.get_path("purelib")).resolve()):
                origin = {"kind": "python_runtime", "path": path.relative_to(Path(sys.base_prefix).resolve()).as_posix()}
            elif path.is_relative_to(project_root.resolve() / "build"):
                origin = {"kind": "generated_or_staged", "name": path.name}
            elif path.parent == project_root.resolve() and path.name in ("LICENSE", "NOTICE"):
                origin = {"kind": "project_notice", "name": path.name}
            else:
                origin = {"kind": "unresolved", "name": path.name}
        origins[str(name).replace("\\", "/")] = {**origin, "collection_type": kind}
    records: list[dict[str, Any]] = []
    for path in sorted(bundle.rglob("*")):
        if not path.is_file() and not path.is_symlink():
            continue
        if not path.resolve().is_relative_to(root):
            raise ValueError("Frozen artifact contains an escaping symlink.")
        if path.is_symlink() and path.readlink().is_absolute():
            raise ValueError("Frozen artifact contains a non-portable absolute symlink.")
        relative = path.relative_to(bundle).as_posix()
        aliases = [relative]
        for prefix in ("_internal/", "Contents/Resources/", "Contents/Frameworks/", "Contents/MacOS/"):
            if relative.startswith(prefix):
                aliases.append(relative.removeprefix(prefix))
        origin = next((origins[alias] for alias in aliases if alias in origins), {"kind": "unresolved"})
        record: dict[str, Any] = {"path": relative, "origin": origin}
        if path.is_file():
            record.update({"sha256": digest(path), "bytes": path.stat().st_size})
        if path.is_symlink():
            record["symlink_target"] = path.readlink().as_posix()
        records.append(record)
    forbidden = [row["path"] for row in records if any(name in row["path"].lower()
                  for name in ("qt6virtualkeyboard", "qtvirtualkeyboard.framework", "qtvirtualkeyboardplugin", "qpdf.", "qt6pdf.", "qtpdf.framework"))]
    if forbidden:
        raise RuntimeError(f"Unused excluded Qt modules remain bundled: {forbidden}")
    document = {"schema_version": 1, "kind": "frozen_filesystem_inventory", "files": records,
                "file_count": len(records), "unresolved_origin_count": sum(row["origin"]["kind"] == "unresolved" for row in records),
                "scope": "Hashes frozen filesystem entries after build, before installer wrapping/signing. Archives and native libraries remain opaque.",
                "review_status": "Origins are evidence, not a transitive license conclusion or complete SBOM. Review embedded/native dependencies separately."}
    _write_json(output, document)
    return document
