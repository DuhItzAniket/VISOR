# Validation candidates and installed-artifact checks

I18 adds a reproducible preparation path; its native execution evidence is tracked in IMPLEMENTATION_STATUS.md. It does not publish a GitHub Release, sign software or establish complete dependency compliance.

The Desktop bundles workflow first runs source checks, freezes/packages the application and checks the frozen workflow. It then runs `scripts/verify_installer.py` on the disposable GitHub-hosted runner. The script refuses local/self-hosted environments and refuses to replace an existing VISOR installation or known Linux application files.

| Target | Installer check |
|---|---|
| Windows | Run the actual per-user Inno setup into a private temporary directory without shortcuts, application closing or restart; check registration/uninstaller; run the installed executable; invoke the actual uninstaller and verify removal |
| macOS, both architectures | Mount the actual DMG read-only, copy its app into an isolated Applications directory, run that copied app, detach the DMG and remove the test app |
| Linux | Confirm Debian package name/version and no prior installation, install through dpkg, check desktop entry/icon, run the installed executable, purge through dpkg and check removal |

Every installed executable must match the frozen executable hash. Its full smoke check runs with an empty directory as PATH and PYTHONHOME/PYTHONPATH removed, using the absolute app path. Reports retain installer bytes/hash, exact source/version, actual checks and failures. No local environment, certificate or model is installed by this tool.

This is runner evidence. Network is not disabled, and the runner has development tools/system libraries. Clean-user-desktop offline use, physical shell drag, screen readers/scaling, native launchers, Gatekeeper and trusted signing remain separate gates. A copied Mac app check does not simulate every Finder/quarantine behavior.

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

Primary references: [Inno setup flags](https://jrsoftware.org/ishelp/topic_setupcmdline.htm), [Inno uninstall flags](https://jrsoftware.org/ishelp/topic_uninstcmdline.htm), [dpkg operations](https://manpages.ubuntu.com/manpages/jammy/man1/dpkg.1.html), [GitHub runner environment variables](https://docs.github.com/en/actions/reference/workflows-and-actions/variables).
