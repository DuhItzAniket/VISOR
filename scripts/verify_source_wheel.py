"""Verify source-wheel bytes, metadata and project notices without importing it."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from email.parser import BytesParser
from pathlib import Path, PurePosixPath
from zipfile import BadZipFile, ZipFile


def verify_source_wheel(wheel: Path, root: Path) -> dict[str, str | int]:
    package = root / "src/visor"
    tree = ast.parse((package / "__init__.py").read_text(encoding="utf-8"))
    versions = [node.value.value for node in tree.body if isinstance(node, ast.Assign)
                and any(isinstance(target, ast.Name) and target.id == "__version__" for target in node.targets)
                and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)]
    if len(versions) != 1:
        raise ValueError("Source must declare one literal __version__.")
    version = versions[0]
    prefix = f"visor_registration-{version}.dist-info/"
    with ZipFile(wheel) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate wheel archive member.")
        for name in names:
            path = PurePosixPath(name)
            if path.is_absolute() or ".." in path.parts or "\\" in name or ":" in name:
                raise ValueError("Unsafe wheel member path.")
            if not name.startswith(("visor/", prefix)):
                raise ValueError("Unexpected wheel package or metadata directory.")
        metadata = BytesParser().parsebytes(archive.read(prefix + "METADATA"))
        if any(len(metadata.get_all(field, [])) != 1 for field in ("Name", "Version", "License-Expression")):
            raise ValueError("Wheel identity and license fields must be unambiguous.")
        if metadata["Name"] != "visor-registration" or metadata["Version"] != version:
            raise ValueError("Wheel identity does not match this source.")
        if metadata["License-Expression"] != "Apache-2.0":
            raise ValueError("Wheel project license expression is missing or unexpected.")
        requirements = [re.match(r"[\w.-]+", value) for value in metadata.get_all("Requires-Dist", [])]
        providers = {match[0].lower().replace("_", "-") for match in requirements
                     if match and match[0].lower().replace("_", "-").startswith("opencv-")}
        if providers != {"opencv-contrib-python-headless"}:
            raise ValueError("Wheel must request the single headless-contrib OpenCV provider.")
        for notice in ("LICENSE", "NOTICE"):
            if archive.read(prefix + "licenses/" + notice) != (root / notice).read_bytes():
                raise ValueError(f"Wheel project {notice} bytes differ from source.")
        required = {"visor/" + file.relative_to(package).as_posix() for file in package.rglob("*.py")}
        required.update("visor/" + file.relative_to(package).as_posix() for file in (package / "assets/icons").glob("*.svg"))
        if not required.issubset(names):
            raise ValueError("Wheel is missing source modules or application icons.")
        package_files = [name for name in names if name.startswith("visor/") and not name.endswith("/")]
        for name in package_files:
            original = root / "src" / name
            if not original.is_file() or archive.read(name) != original.read_bytes():
                raise ValueError(f"Wheel package bytes differ from source: {name}")
        if archive.testzip() is not None:
            raise ValueError("Wheel ZIP CRC check failed.")
    return {"version": version, "source_modules": sum(name.endswith(".py") for name in required),
            "package_files": len(package_files), "wheel_sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
            "scope": "Source bytes and project metadata/notices only; no native/model/transitive license certification."}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", type=Path)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        if args.wheel.is_dir():
            candidates = list(args.wheel.glob("*.whl"))
            if len(candidates) != 1:
                raise ValueError("Wheel directory must contain exactly one wheel.")
            args.wheel = candidates[0]
        print(json.dumps(verify_source_wheel(args.wheel, args.root), indent=2))
    except (OSError, ValueError, KeyError, BadZipFile) as exc:
        parser.exit(2, f"Source wheel verification failed: {exc}\n")


if __name__ == "__main__":
    main()
