"""Build the standalone Qt app on its target OS; create optional native packages.

Run on Windows, macOS, or Linux with the project's build dependencies installed.
There is no cross-compilation or dependency installation inside this script.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str], *, isolate_native_path: bool = False) -> None:
    environment = os.environ.copy()
    if isolate_native_path and platform.system() == "Windows":
        # Avoid collecting unrelated DLLs from graphics/PDF tools on developer
        # PATH. Qt may need the Windows ICU DLL, not a same-named Poppler DLL.
        windows = Path(environment.get("SystemRoot", "C:/Windows"))
        environment["PATH"] = os.pathsep.join(str(path) for path in (
            Path(sys.executable).parent, Path(sys.base_prefix), Path(sys.base_prefix) / "DLLs",
            windows / "System32", windows,
        ))
    subprocess.run(command, cwd=ROOT, check=True, env=environment)


def build() -> tuple[Path, str, str]:
    version = importlib.metadata.version("visor-registration")
    system = platform.system()
    architecture = platform.machine().lower()
    assets = ROOT / "src" / "visor" / "assets"
    command = [
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--windowed",
        "--name", "VISOR", "--paths", str(ROOT / "src"),
        "--add-data", f"{assets}:visor/assets",
    ]
    # Standard desktop distribution is classical-only. Do not accidentally bundle
    # the developer machine's Torch/CUDA runtime or mutable optional model code.
    for module in ("torch", "torchvision", "lightglue", "xfeat"):
        command += ["--exclude-module", module]
    if system == "Windows":
        command += ["--icon", str(assets / "visor.ico")]
    elif system == "Darwin":
        from PIL import Image

        icon = ROOT / "build" / "visor.icns"
        icon.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(assets / "visor.ico") as image:
            image.convert("RGBA").resize((512, 512)).save(icon, format="ICNS")
        command += ["--icon", str(icon), "--osx-bundle-identifier", "org.visor.desktop"]
    elif system != "Linux":
        raise RuntimeError(f"Unsupported build host: {system}")
    command.append(str(ROOT / "src" / "visor" / "__main__.py"))
    run(command, isolate_native_path=True)
    bundle = ROOT / "dist" / ("VISOR.app" if system == "Darwin" else "VISOR")
    info = {
        "version": version, "system": system, "architecture": architecture,
        "python": platform.python_version(), "learned_engines_bundled": False,
        "dependencies": {
            name: importlib.metadata.version(name)
            for name in ("numpy", "opencv-contrib-python", "PySide6", "PyInstaller")
        },
    }
    (ROOT / "dist" / "build-info.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
    return bundle, version, architecture


def package(bundle: Path, version: str, architecture: str) -> None:
    system = platform.system()
    output = ROOT / "dist" / "installers"
    output.mkdir(parents=True, exist_ok=True)
    artifact = f"VISOR-{version}-{system.lower()}-{architecture}"
    if system == "Windows":
        shutil.make_archive(str(output / artifact), "zip", bundle.parent, bundle.name)
        compiler = shutil.which("iscc")
        if compiler is None:
            candidate = Path("C:/Program Files (x86)/Inno Setup 6/ISCC.exe")
            if candidate.is_file():
                compiler = str(candidate)
        if compiler is None:
            raise RuntimeError("Portable ZIP created. Inno Setup 6 is required to create the Windows installer.")
        run([compiler, f"/DAppVersion={version}", str(ROOT / "scripts" / "VISOR.iss")])
    elif system == "Darwin":
        import tempfile

        with tempfile.TemporaryDirectory(prefix="visor-dmg-") as temporary:
            stage = Path(temporary)
            shutil.copytree(bundle, stage / bundle.name, symlinks=True)
            (stage / "Applications").symlink_to("/Applications", target_is_directory=True)
            run(["hdiutil", "create", "-volname", "VISOR", "-srcfolder", str(stage),
                 "-ov", "-format", "UDZO", str(output / f"{artifact}.dmg")])
    else:
        import tempfile

        # A portable archive is also useful on distributions outside Debian.
        shutil.make_archive(str(output / artifact), "gztar", bundle.parent, bundle.name)
        deb_arch = {"x86_64": "amd64", "aarch64": "arm64"}.get(architecture)
        if deb_arch is None:
            raise RuntimeError(f"Unsupported Debian package architecture: {architecture}")
        with tempfile.TemporaryDirectory(prefix="visor-deb-") as temporary:
            stage = Path(temporary)
            shutil.copytree(bundle, stage / "opt" / "visor", symlinks=True)
            control = stage / "DEBIAN"
            control.mkdir()
            (control / "control").write_text(
                f"Package: visor\nVersion: {version}\nArchitecture: {deb_arch}\n"
                "Maintainer: VISOR project\nSection: graphics\nPriority: optional\n"
                "Depends: libgl1, libglib2.0-0, libxkbcommon-x11-0, libxcb-cursor0\n"
                "Description: Visual Object Registration and Analysis desktop application\n",
                encoding="utf-8",
            )
            applications = stage / "usr" / "share" / "applications"
            applications.mkdir(parents=True)
            (applications / "org.visor.desktop.desktop").write_text(
                "[Desktop Entry]\nType=Application\nName=VISOR\n"
                "Comment=Visual Object Registration and Analysis\n"
                "Exec=/opt/visor/VISOR\nIcon=visor\nTerminal=false\nCategories=Graphics;Science;\n",
                encoding="utf-8",
            )
            icons = stage / "usr" / "share" / "icons" / "hicolor" / "scalable" / "apps"
            icons.mkdir(parents=True)
            shutil.copy2(ROOT / "src" / "visor" / "assets" / "visor.svg", icons / "visor.svg")
            run(["dpkg-deb", "--root-owner-group", "--build", str(stage), str(output / f"{artifact}.deb")])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", action="store_true", help="Also create the host OS installer/package")
    args = parser.parse_args()
    bundle, version, architecture = build()
    if args.package:
        package(bundle, version, architecture)
    print(f"Desktop bundle ready: {bundle}")


if __name__ == "__main__":
    main()
