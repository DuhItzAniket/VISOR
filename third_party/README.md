# Vendored notice evidence

`qt-notices-6.11.2/` contains unmodified license texts, attribution records, referenced license files and reuse metadata from the Qt/PySide 6.11.2 source repositories. `sources.json` records immutable commit URLs and SHA256 for all 203 files. Every referenced `LicenseFile` found in those attribution records was resolved at preparation time.

This is a **source notice corpus**, including components/build tools/tests not necessarily linked into VISOR. It is not a list of everything shipped, a complete transitive SBOM, or a compliance certificate. Original terms remain in the copied files. Inspect the actual frozen-file inventory and compiled native dependencies separately; source-offer and redistribution obligations remain part of release review.

Maintainers may prepare a new snapshot with `python scripts/refresh_qt_notices.py`. That explicit network operation resolves version tags to commits and downloads only notice/attribution files; it never runs upstream source. Normal builds and validation use the checked-in snapshot offline and reject a mismatched Qt version or changed notice bytes. The refresh refuses to overwrite an existing snapshot.

The desktop build additionally copies installed Python/NumPy/OpenCV/PySide/Shiboken/PyInstaller notices from its actual environment. Those copies are generated under `build/` and packaged under `third-party/`; they are not committed caches. `notices.json` identifies versions, notice scope and hashes. The separate `artifact-inventory.json` hashes the frozen filesystem after build and explicitly marks unresolved/overlapping origins and opaque archives/native libraries.
