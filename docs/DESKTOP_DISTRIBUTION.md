# Standalone desktop distribution

## Product requirement

VISOR is delivered as a desktop application. End users launch an installed app and do not install Python, pip, or a virtual environment. Qt provides the desktop widgets; the build bundles its Python runtime and libraries internally. This is still Python source software; it is not a C++ rewrite or a promise of single-binary native compilation.

PyInstaller's documented model supports self-contained bundles but requires building on each target OS. Qt documents Windows/macOS/Linux deployment paths. [PyInstaller operating model](https://pyinstaller.org/en/stable/operating-mode.html), [Qt deployment](https://doc.qt.io/qtforpython-6/deployment/index.html).

## Delivery matrix

| Target | Build artifact | User workflow | Current gate |
|---|---|---|---|
| Windows x64 | Setup EXE and portable ZIP | Install through wizard, launch from Start menu; uninstaller included | Native build/check passed; clean installation and signing remain |
| macOS Apple Silicon | `.app` inside DMG | Drag VISOR into Applications, launch in Finder | Native ARM build/check passed; manual review, signing and notarization remain |
| macOS Intel | Separate x86_64 app/DMG | Same app workflow | Native Intel build/check passed; manual review, signing and notarization remain. Separate architecture, not a universal binary |
| Linux x86_64 | `.deb` plus portable tar archive | Install Debian package and launch from desktop menu | Native Ubuntu build/check passed; supported-desktop/distribution review remains |

Native build evidence (2026-10-19): [run 39300439636](https://github.com/DuhItzAniket/VISOR/actions/runs/39300439636), source `303ba33`, completed successfully on Windows x64, macOS ARM64, and Ubuntu x64. All three jobs produced packages and passed the bundled workflow check. Artifacts are named `VISOR-Windows-X64`, `VISOR-macOS-ARM64`, and `VISOR-Linux-X64`. These are unsigned validation builds, not a public production release or proof of install/uninstall behavior on every desktop.

Current validation (recorded 2026-10-26): [run 40311819086](https://github.com/DuhItzAniket/VISOR/actions/runs/40311819086) at `ce68a2c` passed all four target suites, lint, packaging, actual installed workflow/removal and candidate preparation. Windows: 305 passed/2 skipped/17 optional deselections; both Macs/Linux: 303 passed/4 skipped/17 deselected. Bundled/installed checks cover project/dependency notices, actual OpenCV backend, five image formats, background EXIF-oriented input/replacement recovery/cached previews, copy-only Qt drop events, SIFT/ORB, async overlays/style/viewport/export consistency, projects and MJPEG/ORB tracking. All four downloaded audit identities/inventory hashes and successful reports were independently checked, plus all 91 Linux system-notice hashes. Installer assets/checksums are prepared and checked in CI; the earlier 81e81da cohort also had all 26 downloaded candidate checksums rechecked locally. This cohort includes I22 background image loading. Full local candidate checksum downloads are in progress; no partial download is called verified. These are validation builds; signing, complete notices/source obligations and physical desktop review remain open.

Artifacts from this completed validation run:

- [Windows x64 setup and portable ZIP](https://github.com/DuhItzAniket/VISOR/actions/runs/40311819086/artifacts/12645281341)
- [macOS Apple Silicon DMG](https://github.com/DuhItzAniket/VISOR/actions/runs/40311819086/artifacts/12644259417)
- [macOS Intel DMG](https://github.com/DuhItzAniket/VISOR/actions/runs/40311819086/artifacts/12644444683)
- [Linux x64 Debian and portable packages](https://github.com/DuhItzAniket/VISOR/actions/runs/40311819086/artifacts/12645590415)

GitHub may require sign-in to download Actions artifacts; artifacts also have a retention period. These links are validation downloads, not permanent public release URLs. The ZIP contents are flat: packages plus platform-prefixed evidence, a manifest and SHA256SUMS. Keep the files together when checking checksums.

The runner architecture and dependency versions are recorded in `dist/build-info.json`. Linux artifacts are not guaranteed across every distribution/glibc version. macOS and Windows signing are not configured by the scripts. No package is called production-ready until install/uninstall and desktop behavior have been checked on its intended target system.

Build/package versions come from the literal `src/visor/__init__.py` version in the source being frozen. An older VISOR wheel installed in a developer environment must not relabel that source's artifact. `build-info.json` records the version source; invalid/missing source versions fail before invoking the packager.

## Building (maintainers only)

Use a clean environment on the target OS with Python 3.11:

```text
python -m pip install -r requirements/desktop-build.txt
python -m pip install --no-deps .
python scripts/build_desktop.py --package
```

Windows packaging additionally requires Inno Setup 6 (`iscc` on PATH or installed in its standard directory). macOS uses `hdiutil`. Linux uses `dpkg-deb` and the standard build host tools. The application bundle can be built without the installer using `python scripts/build_desktop.py`.

The verified I16 build profile pins `opencv-contrib-python-headless==4.11.0.86` because PySide6 supplies the desktop UI. The builder rejects missing, regular or overlapping OpenCV distributions and unexpected compiled GUI backends. The pinned Mac wheel retains Cocoa, explicitly documented upstream and recorded in build-info; Windows/Linux require NONE. No bundled Qt5 libraries are allowed. Recreate old build environments instead of installing two providers of `cv2` together. The downloads above use this verified profile. VISOR remains a Qt desktop application.

The manual **Desktop bundles** GitHub Actions workflow runs separate Windows, macOS, and Linux jobs and uploads installers, provenance and smoke reports as artifacts. It does not publish a GitHub Release, sign artifacts, or modify the source checkout. GitHub documents separate native runner OS/architecture labels. [Runner reference](https://docs.github.com/en/actions/reference/runners/github-hosted-runners).

## Verification

Each bundle exposes a maintainer-only check:

```text
VISOR --smoke-check smoke-report.json
```

On Windows use `VISOR.exe`; on macOS use `VISOR.app/Contents/MacOS/VISOR`. CI sets `QT_QPA_PLATFORM=offscreen`. The check verifies project LICENSE/NOTICE inclusion, dispatches Qt URL drop events with copy semantics, loads generated image inputs into the Qt window, localizes an identity pair with SIFT and ORB, renders results, exports JSON/CSV, saves/loads a project, checks all indexed dependency notices/actual Qt version, decodes PNG/JPEG/BMP/TIFF/WebP, encodes/decodes an MJPEG fixture and tracks three frames with ORB, then closes the window. The event check is separate from physical native shell dragging. A startup import failure is also recorded. The check does not replace mouse-driven testing, screen-reader checks, OS installation/uninstallation, code-signature validation or complete third-party notice review.

## Dependency notices and file inventory

New audit builds include `third-party/notices.json` and its referenced exact notice files in frozen resources (`_internal/third-party` on Windows/Linux; macOS resources are arranged by PyInstaller). Frozen checks validate their hashes and Qt version. [Source corpus and maintainer refresh](../third_party/README.md) describe provenance; normal builds do not download notices.

The Actions artifact also supplies `artifact-inventory.json`, containing actual frozen file hashes and best-effort collection origins, and `build-info.json` records its hash. The inventory stays outside the app to avoid post-build signature changes. It covers the frozen filesystem before installer wrapping/signing, with embedded/native contents explicitly opaque. Re-audit after any signing or packaging transformation that changes those files. Complete component/source-offer/native-library license review remains separate from successful collection.

New workflow runs also upload small `VISOR-<OS>-<ARCH>-audit` artifacts with only build-info, inventory and smoke results, so maintainers can inspect evidence without downloading every installer.

## Candidate preparation

The I18 [candidate preparation and installed-artifact workflow](RELEASE_PREPARATION.md) passed on all four targets at 81e81da. It supplies actual disposable-runner installer/copy/workflow/removal evidence and flat checksum-linked assets. This does not close clean-user-desktop/offline-network, signing or native-interaction gates.

## Optional engines

The standard desktop bundles validate SIFT/ORB and explicitly exclude Torch/LightGlue/XFeat to avoid packaging developer-installed GPU dependencies accidentally. Registry-supported additional classical engines are enabled when the bundled OpenCV API provides them. Packaged UI hides pip installation controls and reports unavailable learned engines. Source learned adapters are repaired, but a complete packaged learned runtime and its model notices remain I12/I13 work; users should not be told to install Python to complete an advertised packaged feature.

Do not label an optional engine available simply because its Python module can be discovered. Weights, API compatibility and actual execution must be checked before packaging it. Maintain code/model licenses and notices before distributing additional weights.
