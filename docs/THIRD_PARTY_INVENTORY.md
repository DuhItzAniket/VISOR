# Dependency and model notice inventory

Reviewed 2026-10-25; project-license decision updated 2026-10-26. The owner selected Apache-2.0 for VISOR's original source; root LICENSE/NOTICE and package metadata record that choice. This inventory records observed third-party declarations and upstream notices. It does not establish that a distribution has satisfied every dependency notice/source obligation; release checks remain open under I12/I13.

## Standard desktop components

| Component observed locally | Declaration / notice evidence | Remaining distribution work |
|---|---|---|
| Python 3.11 runtime | Python distribution license files | Include the exact runtime's notices in each native bundle |
| NumPy 1.26.4 | Installed distribution LICENSE.txt and additional component licenses | Retain notices for the libraries actually bundled, including third-party numerical components |
| OpenCV contrib 4.11.0.86 | Package metadata declares Apache 2.0; LICENSE.txt and LICENSE-3RD-PARTY.txt present | Include both primary and bundled third-party notices |
| PySide6, Essentials, Addons, Shiboken6 6.11.2 | Package metadata declares LGPL/GPL alternatives; commercial license reference file is also present | Review the selected licensing route, actual Qt modules/native dependencies and their complete notices for each artifact |
| PyInstaller 6.22.3 / bootloader | Package declares GPL with its distribution exception; COPYING.txt present | Preserve applicable notices; do not infer VISOR's own project license from its build tool |

Qt documents separate third-party contributions and points to Qt's component-level license information: [Qt for Python license notices](https://doc.qt.io/qtforpython-6/licenses.html). A package's headline declaration alone is not a complete inventory of a frozen application's native libraries.

## Optional source runtime

| Component | Observed declaration / primary source | Scope |
|---|---|---|
| Torch 2.5.1+cu121 | Installed metadata declares BSD-3-Clause; LICENSE and NOTICE present | Source environment only; CUDA/native dependency notices need their own inventory before bundling |
| Torchvision 0.20.1+cu121 | Installed metadata declares BSD; LICENSE present | Source environment only |
| LightGlue at supported pin | Upstream states Apache-2.0 for its code and matcher weights | Does not cover every feature extractor; see upstream distinctions below |
| DISK | LightGlue's upstream notice identifies Apache-2.0 | Verify exact extractor/weights provenance before redistribution |
| ALIKED | LightGlue's upstream notice identifies BSD-3-Clause | Retain the exact upstream notices and weight provenance |
| SuperPoint | Upstream explicitly identifies a separate restrictive license covering weights and inference file | Do not treat installing LightGlue as blanket redistribution permission; review before any packaged SuperPoint offering |
| XFeat at supported pin | Cached repository contains its Apache-2.0 LICENSE | Keep source/weight provenance and notices; packaged redistribution remains unapproved |

Primary distinctions are in [LightGlue's pinned license section](https://github.com/cvg/LightGlue/blob/eb42fee2d71449efb0aa5c10549752b5d75384d8/README.md#license) and [XFeat's pinned repository license](https://github.com/verlab/accelerated_features/blob/e92685f57f8318b18725c5c8c0bd28c7fe188d9a/LICENSE). Standard validation bundles exclude these learned runtimes and weights.

## Dataset evidence

HPatches image/transform files are downloaded separately for local evaluation and are not copied into this repository's application artifacts. The evidence directory contains measurements and source hashes. Follow the [dataset's original-source/citation guidance](https://github.com/hpatches/hpatches-dataset) when using or publishing research results.

## Project decision and remaining release work

- VISOR's own source is Apache-2.0 by the owner's 2026-10-26 choice. Source wheels and new desktop builds include LICENSE/NOTICE. This closes the project-license choice; third-party/model distribution review remains separate.
- Generate and inspect a per-artifact inventory and include complete notices before a public release. The table above does not certify the current unsigned validation artifacts as notice-complete.
- Review exact model/weight terms before offering learned models inside desktop distributions. Maintain source, revision, weight hashes and required notices together.
