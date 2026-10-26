"""Prepare flat validation assets only from matching successful artifact evidence."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any

from visor.distribution_audit import digest


def prepare_candidate(dist: Path, output: Path) -> dict[str, Any]:
    """Validate provenance before staging any assets; never overwrite a candidate."""
    root = dist.resolve()
    if output.exists() or output.is_symlink():
        raise FileExistsError("Candidate output already exists; choose a new directory.")
    documents = {}
    evidence_hashes = {}
    evidence = ("build-info.json", "artifact-inventory.json", "smoke-report.json", "installer-report.json")
    for name in evidence:
        path = dist / name
        if not path.resolve().is_relative_to(root):
            raise ValueError("Evidence escapes the distribution directory.")
        raw = path.read_bytes()
        documents[name] = json.loads(raw.decode("utf-8"))
        evidence_hashes[name] = hashlib.sha256(raw).hexdigest()
    info, inventory, smoke, installed = (documents[name] for name in evidence)
    version, system, architecture = info["version"], info["system"], info["architecture"]
    if (not re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?", version)
            or system not in ("Windows", "Darwin", "Linux")
            or not re.fullmatch(r"[A-Za-z0-9_]+", architecture)
            or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", info.get("source_revision") or "")):
        raise ValueError("Invalid version, platform or source identity in build evidence.")
    if (inventory.get("kind") != "frozen_filesystem_inventory"
            or evidence_hashes["artifact-inventory.json"] != info["artifact_inventory"]["sha256"]):
        raise ValueError("Frozen inventory does not match the recorded build hash.")
    if (smoke.get("success") is not True or smoke.get("version") != version or smoke.get("system") != system
            or installed.get("kind") != "host_installer_check" or installed.get("success") is not True
            or installed.get("source_revision") != info["source_revision"]
            or installed.get("version") != version or installed.get("system") != system):
        raise ValueError("Workflow/installer evidence failed or belongs to another build.")
    installers = sorted((dist / "installers").iterdir())
    suffixes = {"Windows": (".exe", ".zip"), "Darwin": (".dmg",), "Linux": (".deb", ".tar.gz")}[system]
    if not installers or any(not path.is_file() or not path.name.startswith(f"VISOR-{version}-")
                             or not path.name.endswith(suffixes) or path.stat().st_size == 0
                             or not path.resolve().is_relative_to(root) for path in installers):
        raise ValueError("Installer directory contains absent, stale or unexpected assets.")
    if any(sum(path.name.endswith(suffix) for path in installers) != 1 for suffix in suffixes):
        raise ValueError("Expected exactly one installer/archive of each platform format.")
    checked = installed["installer"]
    checked_file = next((path for path in installers if path.name == checked["file"]), None)
    if checked_file is None or digest(checked_file) != checked["sha256"] or checked_file.stat().st_size != checked["bytes"]:
        raise ValueError("The tested installer differs from the candidate installer bytes.")
    prefix = f"VISOR-{version}-{system.lower()}-{architecture.lower()}"
    inputs = [(path, path.name, "package", checked["sha256"] if path == checked_file else digest(path))
              for path in installers]
    inputs.extend((dist / name, f"{prefix}-{name}", "evidence", evidence_hashes[name]) for name in evidence)
    if len({name.casefold() for _, name, _, _ in inputs}) != len(inputs):
        raise ValueError("Candidate asset filenames collide.")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="release-prep-", dir=output.parent) as temporary:
        stage = Path(temporary).resolve()
        if not stage.is_relative_to(output.parent.resolve()):
            raise ValueError("Candidate staging directory escaped its intended parent.")
        files: list[dict[str, Any]] = []
        for source, name, role, expected_hash in inputs:
            target = stage / name
            shutil.copyfile(source, target)
            if digest(source) != expected_hash or digest(target) != expected_hash:
                raise ValueError("Asset bytes changed while preparing the candidate.")
            files.append({"file": name, "role": role, "sha256": expected_hash, "bytes": target.stat().st_size})
        checksum_name = f"{prefix}-SHA256SUMS.txt"
        manifest = {"schema_version": 1, "kind": "validation_release_candidate", "version": version,
                    "system": system, "architecture": architecture, "source_revision": info["source_revision"],
                    "files": files, "checksum_file": checksum_name, "release_signing_verified": False,
                    "scope": "Successful frozen and hosted-runner installer checks. Not public-release approval, "
                             "complete dependency compliance, signing, clean-desktop or offline-network certification."}
        manifest_path = stage / f"{prefix}-release-manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
        checksummed = [stage / row["file"] for row in files] + [manifest_path]
        (stage / checksum_name).write_text("".join(f"{digest(path)}  {path.name}\n" for path in checksummed),
                                           encoding="utf-8", newline="\n")
        if output.exists() or output.is_symlink():
            raise FileExistsError("Candidate output appeared during preparation.")
        # Move only this verified, uniquely owned stage, within its checked parent.
        stage.rename(output)
    return manifest
