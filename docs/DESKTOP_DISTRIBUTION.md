# Standalone desktop distribution

## Product requirement

VISOR is delivered as a desktop application. End users launch an installed app and do not install Python, pip, or a virtual environment. Qt provides the desktop widgets; the build bundles its Python runtime and libraries internally. This is still Python source software; it is not a C++ rewrite or a promise of single-binary native compilation.

PyInstaller's documented model supports self-contained bundles but requires building on each target OS. Qt documents Windows/macOS/Linux deployment paths. [PyInstaller operating model](https://pyinstaller.org/en/stable/operating-mode.html), [Qt deployment](https://doc.qt.io/qtforpython-6/deployment/index.html).

## Delivery matrix

| Target | Build artifact | User workflow | Current gate |
|---|---|---|---|
| Windows x64 | Setup EXE and portable ZIP | Install through wizard, launch from Start menu; uninstaller included | Native build and bundled workflow smoke check required |
| macOS Apple Silicon | `.app` inside DMG | Drag VISOR into Applications, launch in Finder | Native ARM build/check; public distribution also needs Developer ID signing and notarization |
| macOS Intel | Separate x86_64 build if required | Same app workflow | Not covered by the initial runner matrix; do not advertise universal binary support |
| Linux x86_64 | `.deb` plus portable tar archive | Install Debian package and launch from desktop menu | Native Ubuntu build/check; test each supported desktop/distribution |

Native build evidence (2026-10-19): [run 39300439636](https://github.com/DuhItzAniket/VISOR/actions/runs/39300439636), source `303ba33`, completed successfully on Windows x64, macOS ARM64, and Ubuntu x64. All three jobs produced packages and passed the bundled workflow check. Artifacts are named `VISOR-Windows-X64`, `VISOR-macOS-ARM64`, and `VISOR-Linux-X64`. These are unsigned validation builds, not a public production release or proof of install/uninstall behavior on every desktop.

Latest validation: [run 39301662952](https://github.com/DuhItzAniket/VISOR/actions/runs/39301662952) at `ba7e05d` also passed the full core regression suite and lint on each native runner before packaging. Windows: 91 passed/17 skipped; macOS and Linux: 89 passed/19 skipped. See [current status](IMPLEMENTATION_STATUS.md) for skip scope and release gates.

Artifacts from the latest run:

- [Windows x64 setup and portable ZIP](https://github.com/DuhItzAniket/VISOR/actions/runs/39301662952/artifacts/12212317478)
- [macOS Apple Silicon DMG](https://github.com/DuhItzAniket/VISOR/actions/runs/39301662952/artifacts/12211972533)
- [Linux x64 Debian and portable packages](https://github.com/DuhItzAniket/VISOR/actions/runs/39301662952/artifacts/12211237948)

GitHub may require sign-in to download Actions artifacts; artifacts also have a retention period. These links are validation downloads, not permanent public release URLs.

The runner architecture and dependency versions are recorded in `dist/build-info.json`. Linux artifacts are not guaranteed across every distribution/glibc version. macOS and Windows signing are not configured by the scripts. No package is called production-ready until install/uninstall and desktop behavior have been checked on its intended target system.

## Building (maintainers only)

Use a clean environment on the target OS with Python 3.11:

```text
python -m pip install -r requirements/desktop-build.txt
python -m pip install --no-deps .
python scripts/build_desktop.py --package
```

Windows packaging additionally requires Inno Setup 6 (`iscc` on PATH or installed in its standard directory). macOS uses `hdiutil`. Linux uses `dpkg-deb` and the standard build host tools. The application bundle can be built without the installer using `python scripts/build_desktop.py`.

The manual **Desktop bundles** GitHub Actions workflow runs separate Windows, macOS, and Linux jobs and uploads installers, provenance and smoke reports as artifacts. It does not publish a GitHub Release, sign artifacts, or modify the source checkout. GitHub documents separate native runner OS/architecture labels. [Runner reference](https://docs.github.com/en/actions/reference/runners/github-hosted-runners).

## Verification

Each bundle exposes a maintainer-only check:

```text
VISOR --smoke-check smoke-report.json
```

On Windows use `VISOR.exe`; on macOS use `VISOR.app/Contents/MacOS/VISOR`. CI sets `QT_QPA_PLATFORM=offscreen`. The check loads generated image inputs into the Qt window, localizes an identity pair with SIFT and ORB, renders results, exports JSON/CSV, saves/loads a project, and closes the window. A startup import failure is also recorded. This is stronger than checking that a process stays alive, but it does not replace mouse-driven testing, screen-reader checks, OS installation/uninstallation, or code-signature validation.

## Optional engines

The initial standard desktop bundles include SIFT/ORB and explicitly exclude Torch/LightGlue/XFeat to avoid packaging developer-installed GPU dependencies accidentally. Packaged UI hides pip installation controls and reports unavailable optional engines. A complete packaged learned-engine runtime remains work in I04/I05/I13; users should not be told to install Python to complete an advertised packaged feature.

Do not label an optional engine available simply because its Python module can be discovered. Weights, API compatibility and actual execution must be checked before packaging it. Maintain code/model licenses and notices before distributing additional weights.
