# Validation candidates and installed-artifact checks

I18 passed on Windows x64, Linux x64 and both Mac architectures at 81e81da in [run 40299138359](https://github.com/DuhItzAniket/VISOR/actions/runs/40299138359). Its native execution evidence is tracked in IMPLEMENTATION_STATUS.md. It does not publish a GitHub Release, sign software or establish complete dependency compliance.

The Desktop bundles workflow first runs source checks, freezes/packages the application and checks the frozen workflow. It then runs `scripts/verify_installer.py` on the disposable GitHub-hosted runner. The script refuses local/self-hosted environments and refuses to replace an existing VISOR installation or known Linux application files.

| Target | Installer check |
|---|---|
| Windows | Run the actual per-user Inno setup into a private temporary directory without shortcuts, application closing or restart; check registration/uninstaller; run the installed executable; invoke the actual uninstaller and verify removal |
| macOS, both architectures | Mount the actual DMG read-only, copy its app into an isolated Applications directory, run that copied app, detach the DMG and remove the test app |
| Linux | Confirm Debian package name/version and no prior installation, install through dpkg, check desktop entry/icon and system notice hashes, run the installed executable through X11, purge through dpkg and check removal |

Every installed executable must match the frozen executable hash. Its full smoke check runs with an empty directory as PATH and PYTHONHOME/PYTHONPATH removed, using the absolute app path. Reports retain installer bytes/hash, exact source/version, actual checks and failures. No local environment, certificate or model is installed by this tool.

The Linux lane uses a fresh [network namespace](https://manpages.ubuntu.com/manpages/jammy/man1/unshare.1.html) for install, smoke and purge. The verifier requires an interface list of just `lo`, reports it in `network`, and fails before touching the package database otherwise. The installed app runs through Qt's XCB plugin on an Xvfb display. The Windows/macOS checks use offscreen Qt with normal runner networking. Clean-desktop testing, physical shell drag, screen readers, scaling, native launchers, Gatekeeper and trusted signing still need separate evidence.

The separate clean Ubuntu 22.04 lane provisions declared Debian prerequisites and the Xvfb, Xauth and font test packages before disconnecting. It then installs the actual Debian package, runs the app as an unprivileged user, purges it and runs the portable archive with only loopback networking. The audit includes `clean-linux.log` with the base image digest, observed packages and file hashes. This exercises a minimal userspace and virtual X11 display. Manual desktop behavior is tracked in the native review procedure.

After success, `scripts/prepare_release.py` validates the matching build/inventory/smoke/installer reports and exact tested installer bytes. It rejects failed reports, another source/version/platform, stale/extra/missing package formats, files changed during staging and an existing destination. It writes a new `dist/release-candidate` directory containing flat assets:

- Original installer/archive filenames.
- Platform/architecture-prefixed build-info, inventory, smoke and installer reports.
- A prefixed validation manifest and SHA256SUMS text file covering those assets and the manifest.

Names can coexist across the four targets. `release_signing_verified` stays false; hashes do not assert trusted origin or signing. Failed checks keep small audit evidence and separately named failed-package artifacts, rather than successful candidate downloads.

To prepare already-verified local build evidence without installing software:

```text
python scripts/prepare_release.py --dist dist --output dist/release-candidate
```

The installer verifier is intended only for disposable hosted runners. Run the normal workflow for that evidence. Do not fake its environment variables to run it on a user's computer.

On Linux, validate the downloaded candidate's files with `sha256sum -c <prefix>-SHA256SUMS.txt`; on Mac use `shasum -a 256 -c <prefix>-SHA256SUMS.txt`. Windows users can compare `Get-FileHash -Algorithm SHA256 <installer>` with the checksum file. Keep the downloaded assets together for these comparisons.

Before public release, complete the open I12/I13/I14 obligations, choose the reviewed release notes/version, and verify final signed/notarized bytes. Signing or another transformation that changes frozen files/installers requires fresh inventories, workflow/installation checks and checksums. Current Actions artifacts expire and are validation downloads; permanent release publication is a separate step after those gates.

Use the [native desktop review procedure](NATIVE_RELEASE_REVIEW.md) to record actual package checks on each target, including offline launch, shell drop, keyboard, screen-reader and display-scaling behavior.

## Signing and notarization sequence

The release publisher needs an authorized Windows Authenticode signer and an Apple Developer ID Application signing identity with access to Apple's notary service. Use the publisher's secure key store or signing service. Signing keys and notary credentials stay outside the repository, build logs and package evidence.

- **Windows.** Sign and timestamp the built `VISOR.exe` before computing its final inventory or packing the portable ZIP and setup. Configure the Inno Setup signing tool during installer compilation so setup and the embedded uninstaller both receive signatures. Verify the setup, installed executable, and installed uninstaller against the expected publisher and timestamp using the Authenticode policy. Record the results before removing the test installation. [Microsoft SignTool](https://learn.microsoft.com/windows/win32/seccrypto/signtool) · [Inno Setup uninstaller signing](https://jrsoftware.org/inno-setup/documentation/topic_setup_signeduninstaller.htm)
- **macOS.** Sign the frozen app and nested code with Developer ID and hardened runtime before building each architecture's DMG. Submit the final distribution to the notary service, check the response and log, and staple and validate the ticket on the distribution. Check the copied app's signature and verify normal Gatekeeper behavior on the clean test desktop for each architecture. [Apple distribution packaging](https://developer.apple.com/documentation/xcode/packaging-mac-software-for-distribution) · [Apple notarization workflow](https://developer.apple.com/documentation/security/customizing-the-notarization-workflow)

Capture inventories after signing the application files. Compute distribution checksums after all signing, notarization and stapling steps. Tie the install, launch and report hashes to those final installers and their installed executables. The current build workflow produces validation artifacts with no trusted publisher configuration, so the release manifest's signing status remains false.

Primary references: [Inno setup flags](https://jrsoftware.org/ishelp/topic_setupcmdline.htm), [Inno uninstall flags](https://jrsoftware.org/ishelp/topic_uninstcmdline.htm), [dpkg operations](https://manpages.ubuntu.com/manpages/jammy/man1/dpkg.1.html), [GitHub runner environment variables](https://docs.github.com/en/actions/reference/workflows-and-actions/variables).

## Automatic source checks

The Core checks workflow runs on main pushes and pull requests, with an optional manual trigger. Windows/Linux use the pinned desktop dependency profile, offscreen Qt and CUDA visibility -1, run model-free regressions, lint all maintained scripts, check the declared type targets listed in pyproject.toml, build a source wheel in isolation and verify package/source bytes, project notices, identity/version and the headless OpenCV dependency. JUnit results are retained even on failure. This lane never builds/installs native packages or publishes a release; the separate four-target Desktop bundles workflow remains the native distribution check.

The wheel verifier reads the archive without importing it and accepts a wheel path or a directory containing exactly one wheel. It rejects duplicate/unsafe members, another package/version, ambiguous identity/license metadata, missing/tampered source/icons/notices and an unexpected OpenCV provider. A wheel directory with multiple versions fails instead of selecting an arbitrary file. Its report is source/project-metadata evidence, not a transitive native/model licensing certificate.

```text
python -m pip wheel --no-deps --wheel-dir build/source-wheel .
python scripts/verify_source_wheel.py build/source-wheel
```

The workflow uses read-only repository access and cancels superseded core runs on the same ref. GitHub documents [push/pull-request triggers](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows) and [per-ref concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency). It does not configure branch protection or make a check mandatory without an owner decision.

Run `python -m mypy --no-incremental` to reproduce the explicit type scope locally (currently 18 modules). It includes the main window plus calibration, video, matching and optional-adapter result contracts. Missing optional third-party model packages are allowed by module-specific overrides; VISOR's own errors are not suppressed. This does not assert typed internals for an absent model dependency or an entire-repository type pass.
