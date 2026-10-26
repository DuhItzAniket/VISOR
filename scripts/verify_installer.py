"""Exercise host installers only on disposable GitHub-hosted runners.

This is installed-artifact evidence, not clean-user-desktop, Gatekeeper,
screen-reader, offline-network or code-signing certification.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from visor.distribution_audit import digest


def require_disposable_runner() -> None:
    if os.environ.get("GITHUB_ACTIONS") != "true" or os.environ.get("RUNNER_ENVIRONMENT") != "github-hosted":
        raise RuntimeError("Installer checks require a disposable GitHub-hosted runner; local/self-hosted execution is refused.")


def run(command: list[str], *, env: dict[str, str] | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    flags = subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
    return subprocess.run(command, check=check, timeout=240, env=env, capture_output=True, text=True, creationflags=flags)


def smoke(executable: Path, expected: Path, folder: Path, info: dict, report: dict) -> None:
    if not executable.is_file() or digest(executable) != digest(expected):
        raise RuntimeError("Installed executable differs from the verified frozen source executable.")
    environment = os.environ.copy()
    environment["QT_QPA_PLATFORM"] = "offscreen"
    # The child is the actual frozen app; no Python executable is on its PATH.
    empty_path = folder / "empty-bin"
    empty_path.mkdir()
    environment["PATH"] = str(empty_path)
    environment.pop("PYTHONHOME", None)
    environment.pop("PYTHONPATH", None)
    output = folder / "installed-smoke.json"
    run([str(executable), "--smoke-check", str(output)], env=environment)
    data = json.loads(output.read_text(encoding="utf-8"))
    if data.get("success") is not True or data.get("version") != info["version"]:
        raise RuntimeError("Installed artifact workflow did not succeed with the expected version.")
    report["installed_smoke"] = data
    report["checks"].append("Installed executable hash and full frozen workflow with restricted PATH")


def windows_registered() -> bool:
    import winreg

    key = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\org.visor.desktop_is1"
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        for view in (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
            try:
                with winreg.OpenKey(hive, key, 0, winreg.KEY_READ | view):
                    return True
            except FileNotFoundError:
                pass
    return False


def check_windows(artifact: Path, dist: Path, folder: Path, info: dict, report: dict) -> None:
    if windows_registered():
        raise RuntimeError("An existing VISOR installation is registered; refusing to replace it.")
    destination = folder / "installed"
    uninstaller = destination / "unins000.exe"
    try:
        run([str(artifact), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/SP-", "/NOICONS",
             "/TASKS=", "/NOCLOSEAPPLICATIONS", "/NORESTARTAPPLICATIONS", "/RESTARTEXITCODE=3010",
             f"/DIR={destination}"])
        if not windows_registered() or not uninstaller.is_file():
            raise RuntimeError("Installer did not register VISOR and provide its uninstaller.")
        report["checks"].append("Actual per-user Inno installer into an isolated directory, no shortcuts/restart")
        smoke(destination / "VISOR.exe", dist / "VISOR/VISOR.exe", folder, info, report)
    finally:
        if uninstaller.is_file():
            run([str(uninstaller), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"])
    if (destination / "VISOR.exe").exists() or windows_registered():
        raise RuntimeError("Uninstall left the executable or VISOR registration behind.")
    report["checks"].append("Actual uninstaller removed executable and registration")


def check_macos(artifact: Path, dist: Path, folder: Path, info: dict, report: dict) -> None:
    mount = folder / "mounted"
    mount.mkdir()
    destination = folder / "Applications/VISOR.app"
    destination.parent.mkdir()
    mounted = False
    try:
        run(["hdiutil", "attach", str(artifact), "-readonly", "-nobrowse", "-mountpoint", str(mount)])
        mounted = True
        run(["ditto", str(mount / "VISOR.app"), str(destination)])
        report["checks"].append("Actual read-only DMG mount and app copy into isolated Applications directory")
        smoke(destination / "Contents/MacOS/VISOR", dist / "VISOR.app/Contents/MacOS/VISOR", folder, info, report)
    finally:
        if mounted:
            run(["hdiutil", "detach", str(mount)])
    if not destination.resolve().is_relative_to(folder.resolve()):
        raise RuntimeError("Installed app escaped the owned test directory.")
    shutil.rmtree(destination)
    if destination.exists():
        raise RuntimeError("The copied app was not removed.")
    report["checks"].append("DMG detached and isolated installed app removed")


def linux_registered() -> bool:
    status = run(["dpkg-query", "-W", "-f=${Status}", "visor"], check=False)
    return status.returncode == 0 and status.stdout.strip() != "unknown ok not-installed"


def check_linux(artifact: Path, dist: Path, folder: Path, info: dict, report: dict) -> None:
    paths = (Path("/opt/visor"), Path("/usr/share/applications/org.visor.desktop.desktop"),
             Path("/usr/share/icons/hicolor/scalable/apps/visor.svg"))
    if linux_registered() or any(path.exists() or path.is_symlink() for path in paths):
        raise RuntimeError("Existing VISOR package/files found; refusing to overwrite them.")
    for field, expected in (("Package", "visor"), ("Version", info["version"])):
        if run(["dpkg-deb", "--field", str(artifact), field]).stdout.strip() != expected:
            raise RuntimeError(f"Debian installer {field} differs from the expected package.")
    try:
        run(["sudo", "-n", "dpkg", "--install", str(artifact)])
        if not linux_registered() or not all(path.exists() for path in paths):
            raise RuntimeError("Debian installation did not register the package and desktop assets.")
        report["checks"].append("Actual Debian package installation, desktop entry and icon")
        smoke(paths[0] / "VISOR", dist / "VISOR/VISOR", folder, info, report)
    finally:
        if linux_registered():
            run(["sudo", "-n", "dpkg", "--purge", "visor"])
    if linux_registered() or any(path.exists() for path in paths):
        raise RuntimeError("Debian removal left package registration or owned application files.")
    report["checks"].append("Actual Debian package purge removed application and desktop assets")


def verify(dist: Path, output: Path) -> int:
    require_disposable_runner()
    info = json.loads((dist / "build-info.json").read_text(encoding="utf-8"))
    system = platform.system()
    patterns = {"Windows": "*-windows-setup.exe", "Darwin": "*.dmg", "Linux": "*.deb"}
    if system not in patterns or info["system"] != system:
        raise RuntimeError("Installer/build host mismatch.")
    artifacts = list((dist / "installers").glob(patterns[system]))
    if len(artifacts) != 1:
        raise RuntimeError("Expected exactly one host installer; refusing ambiguous/stale artifacts.")
    artifact = artifacts[0].resolve()
    if not artifact.is_relative_to(dist.resolve()):
        raise RuntimeError("Installer path escapes the distribution directory.")
    report = {"schema_version": 1, "kind": "host_installer_check", "system": system, "version": info["version"],
              "source_revision": info["source_revision"], "success": False, "checks": [],
              "installer": {"file": artifact.name, "sha256": digest(artifact), "bytes": artifact.stat().st_size},
              "scope": "Disposable hosted runner install/copy, workflow and removal. Network is not disabled. "
                       "Not clean-user-desktop, native interaction, signing or Gatekeeper certification."}
    try:
        with tempfile.TemporaryDirectory(prefix="visor-installer-") as stage:
            folder = Path(stage).resolve()
            if not folder.is_relative_to(Path(tempfile.gettempdir()).resolve()):
                raise RuntimeError("Installer staging directory escaped the intended temporary root.")
            {"Windows": check_windows, "Darwin": check_macos, "Linux": check_linux}[system](
                artifact, dist, folder, info, report)
        report["success"] = True
    except Exception as exc:  # noqa: BLE001 — retain failed installation evidence
        report["error"] = f"{type(exc).__name__}: {exc}"
        if isinstance(exc, subprocess.CalledProcessError):
            report["command_output"] = ((exc.stderr or "") + (exc.stdout or ""))[-4000:]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"success": report["success"], "checks": report["checks"], "error": report.get("error")}))
    return 0 if report["success"] else 1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, default=ROOT / "dist")
    parser.add_argument("--report", type=Path, default=ROOT / "dist/installer-report.json")
    args = parser.parse_args()
    raise SystemExit(verify(args.dist, args.report))


if __name__ == "__main__":
    main()
