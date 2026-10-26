# Derived artifact origin review

Reviewed 2026-10-26 from the four hashed inventories at source 81e81da, [native run 40299138359](https://github.com/DuhItzAniket/VISOR/actions/runs/40299138359). This offline review follows exact internal file/directory links; it does not modify the original inventory or choose a component license.

| Target | Original unresolved entries | Links to exact recorded files | Directory layout links | Remaining unresolved regular files |
|---|---:|---:|---:|---:|
| Windows x64 | 0 | 0 | 0 | 0 |
| Linux x64 | 116 | 31 | 0 | 85 |
| macOS ARM64 | 197 | 181 | 14 | 2 |
| macOS Intel | 199 | 183 | 14 | 2 |

The Linux regular files have system source areas recorded by the collector. Their exact operating-system package/version, notices and redistribution obligations still require review. The two remaining regular paths on each Mac are `Contents/Info.plist` and `Contents/Resources/visor.icns`; no ownership claim is added from their names.

This explains why an original unresolved-entry count cannot be treated as a count of missing native-library licenses. Links can point to files with recorded package origins, and framework directory aliases are not extra libraries. Conversely, an OpenCV/Qt package origin does not identify every embedded/native subcomponent or satisfy its license/source obligations. Windows' zero unresolved origins also does not establish complete compliance.

The tool resolves directory prefixes as well as leaf links, validates containment, retains overlapping target claims, and leaves cycles, missing targets and unresolved targets explicit. It never guesses an owner by basename. Each derived report retains the original inventory SHA256, source/platform identity, trace-code hash, original unresolved origins and exact relationships:

- [Windows](origin-trace-81e81da-windows.json)
- [Linux](origin-trace-81e81da-linux.json)
- [Mac ARM64](origin-trace-81e81da-macos-arm64.json)
- [Mac Intel](origin-trace-81e81da-macos-intel.json)

Reproduce against the small audit artifact's files:

```text
python scripts/trace_artifact_origins.py --inventory artifact-inventory.json --build-info build-info.json --output origin-review-new.json
```

The input inventory must match build-info's hash. Output must be a new file. No Qt, model runtime, accelerator, network access or live-system package lookup is used. Package lookups on a different host would not prove original build-host ownership; capture that evidence on the actual build host in a future collection step.

## Linux build-host follow-up

The subsequent Linux-only [run 40305950475](https://github.com/DuhItzAniket/VISOR/actions/runs/40305950475), source c080dd5, captured 85 collected system sources with 78 package database claims, zero unclaimed sources and 91 exact notice files. All 78 package copyright files were collected, plus 13 common-license files. Core checks, installed workflow/removal and candidate preparation passed.

The [recorded manifest](system-notice-review-c080dd5-linux.json) anchors this distinct build's inventory, collector/collection hashes, OS/package/source versions and notice bytes. [Complete notice review artifact](https://github.com/DuhItzAniket/VISOR/actions/runs/40305950475/artifacts/12642293302). All 91 downloaded notice hashes were independently checked. This is c080dd5 build-host evidence, not a retroactive ownership assertion for older artifacts.

The first literal reference extractor recorded 18 unresolved common-license tokens: 12 include terminal sentence periods, and six use GPL-2.0/GPL-3.0 filenames absent from the captured common-license set. Standard GPL-2/GPL-3 texts are present, but no legal equivalence or coverage is inferred automatically. A source follow-up handles sentence punctuation only when the exact normalized file exists, records that interpretation and preserves original copyright bytes; unknown names remain explicit.

These review files are outside the frozen app. Installed notice integration, native/subcomponent terms, licensing routes and source-offer obligations remain open. The manifest's package database claims/source-file hashes do not authenticate binary contents or certify compliance.
