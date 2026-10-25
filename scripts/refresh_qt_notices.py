"""Maintainer-only network refresh of immutable Qt source notices, never build-time."""

from __future__ import annotations

import hashlib
import json
import posixpath
import subprocess
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path, PurePosixPath
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
VERSION = "6.11.2"
REPOSITORIES = ("qt/qtbase", "qt/qtsvg", "qt/qtimageformats", "pyside/pyside-setup")


def github(path: str):
    return json.loads(subprocess.check_output(["gh", "api", path], text=True))


def fetch(repo: str, revision: str, path: str) -> bytes:
    if PurePosixPath(path).is_absolute() or ".." in PurePosixPath(path).parts:
        raise ValueError("Unsafe upstream notice path")
    with urlopen(f"https://raw.githubusercontent.com/{repo}/{revision}/{path}", timeout=40) as stream:
        data = stream.read(2 * 1024 * 1024 + 1)
    if len(data) > 2 * 1024 * 1024:
        raise ValueError("Unexpectedly large notice")
    return data


def main() -> None:
    destination = ROOT / "third_party" / f"qt-notices-{VERSION}"
    if destination.exists():
        raise ValueError("Notice snapshot already exists; review updates in a separate directory.")
    document = {"schema_version": 1, "qt_version": VERSION, "repositories": [], "files": [],
                "scope": "Upstream source notice corpus; not proof every listed component is linked or obligations are complete."}
    for repo in REPOSITORIES:
        revision = github(f"repos/{repo}/commits/v{VERSION}")["sha"]
        tree = github(f"repos/{repo}/git/trees/{revision}?recursive=1")
        if tree.get("truncated"):
            raise RuntimeError(f"Incomplete source tree for {repo}")
        blobs = {entry["path"] for entry in tree["tree"] if entry["type"] == "blob"}
        selected = {path for path in blobs if path.startswith("LICENSES/")
                    or path.endswith("qt_attribution.json") or path in (".reuse/dep5", "REUSE.toml")}
        with ThreadPoolExecutor(max_workers=6) as executor:
            data = dict(zip(sorted(selected), executor.map(partial(fetch, repo, revision), sorted(selected)), strict=True))
        missing = []
        for path, content in list(data.items()):
            if not path.endswith("qt_attribution.json"):
                continue
            # Preserve bytes exactly. Some upstream attribution descriptions
            # contain literal newlines inside strings, accepted by Qt's tools.
            entries = json.loads(content, strict=False)
            for entry in entries if isinstance(entries, list) else [entries]:
                references = entry.get("LicenseFile", [])
                for reference in [references] if isinstance(references, str) else references:
                    candidate = posixpath.normpath(posixpath.join(posixpath.dirname(path), reference))
                    if candidate not in blobs and reference in blobs:
                        candidate = reference
                    if candidate not in blobs:
                        missing.append({"attribution": path, "reference": reference})
                    elif candidate not in data:
                        data[candidate] = fetch(repo, revision, candidate)
        slug = repo.replace("/", "-")
        for path, content in sorted(data.items()):
            relative = f"{slug}/{path}"
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            document["files"].append({"path": relative, "sha256": hashlib.sha256(content).hexdigest(),
                                       "source_url": f"https://raw.githubusercontent.com/{repo}/{revision}/{path}"})
        document["repositories"].append({"repository": repo, "tag": f"v{VERSION}", "revision": revision,
                                          "unresolved_license_references": missing})
        print(f"Prepared {repo}: {len(data)} notice/attribution files; {len(missing)} unresolved references", flush=True)
    (destination / "sources.json").write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
