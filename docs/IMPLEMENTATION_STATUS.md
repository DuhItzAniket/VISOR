# Implementation status

Updated 2026-10-26. This is the current snapshot; chronological changes, prior checks and failed runs are preserved in [IMPLEMENTATION_LOG.md](IMPLEMENTATION_LOG.md) and Git history. Tasks and acceptance gates are in [IMPROVEMENT_PLAN.md](IMPROVEMENT_PLAN.md).

## Dependency-notice and artifact audit follow-up

Added offline collection of actual installed dependency/runtime notices and a checked-in, hash-pinned 203-file Qt/PySide notice corpus. The bundle validates the notice index against actual Qt version and file hashes. A separate frozen-file inventory records hashes, distribution/source origins, overlapping claims and unresolved entries, without publishing developer absolute paths or claiming full transitive compliance.

Native run [40292319995](https://github.com/DuhItzAniket/VISOR/actions/runs/40292319995) passed all four targets at **8fe7dfa**, including frozen startup, all notice hashes, PNG/JPEG/BMP/TIFF/WebP decoding and the classical workflows. Missing Qt wheel notices use an explicitly recorded version-matched pinned-source fallback; missing notices for other components still fail. Unused PDF-image/Qt Virtual Keyboard plugins and optional NumPy testing/F2PY/YAML dependencies are excluded; NumPy's implicit stdlib secrets import is explicitly retained.

Downloaded and inspected all four audit artifacts; each inventory hash matches build-info and each smoke report succeeds. Windows: 218 notice files, 423 filesystem entries, zero unresolved origins. Linux: 214/608/116; macOS ARM64: 214/766/197; macOS Intel: 214/769/199. Unresolved entries include native/system libraries and layout links; counts are not counts of missing licenses. A mapped filesystem origin also does not establish transitive/native/source-offer compliance. I16 removed OpenCV's additional Qt5 runtime: Linux filesystem entries fell from 664 to 608. All four inventories contain zero Qt5 files. The pinned Mac headless wheel retains Cocoa as explicitly documented upstream; build-info and frozen reports record COCOA on both Macs and NONE on Windows/Linux.

## Current verification

I16's headless-contrib profile is verified at the unchanged OpenCV 4.11.0.86 pin. Packaging rejects overlapping cv2 providers, unexpected GUI backends and Qt5 libraries. Actual frozen checks protect image codecs, classical registration and MJPEG encode/decode with three-frame ORB tracking. Classical golden fixtures are unchanged; no vision algorithm or acceptance policy changed.

LightGlue's pinned metadata requests opencv-python, so source setup now installs its explicitly declared inference dependencies first and the pinned adapter with --no-deps separately. This avoids installing another cv2 provider; the upstream package-name mismatch remains documented rather than hidden with false metadata. Optional installation failures stop the sequence and remain failures. Standard desktop bundles still exclude learned dependencies and models.

| Scope | Verified result |
|---|---|
| Full local source suite, including installed optional models | **249 passed, 5 skipped in 66.39s** in the existing developer environment; three skips are the host's unprivileged symlink restriction. This is regression evidence, not a speed benchmark |
| Isolated headless Windows core suite | **232 passed, 5 skipped, 17 optional-model tests deselected in 18.01s**; original Windows/OpenCV goldens retained |
| Lint | Ruff passed for src, tests and shared desktop builder; whitespace check passed |
| Type checking | Focused modules passed, including result contracts, matching/geometry, runtime/setup, registry/pipeline, jobs, evaluation/study, video, image input and builder. No whole-UI Mypy pass is claimed |
| Source wheel | 0.2.0 wheel built in isolation; Apache-2.0 SPDX metadata and full project LICENSE/NOTICE plus the headless OpenCV dependency identity verified inside the wheel |
| Latest completed native matrix | [40292319995](https://github.com/DuhItzAniket/VISOR/actions/runs/40292319995), source **8fe7dfa**: Windows x64, macOS ARM64, macOS Intel and Linux x64 passed core tests, lint, packaging and bundled workflows, including project/dependency notices, actual GUI backend, five image formats and MJPEG video tracking |
| Native core test counts at 8fe7dfa | Windows **235 passed, 2 skipped, 17 model tests deselected**; macOS/Linux each **233 passed, 4 skipped, 17 deselected** |
| Separate optional CPU lane | [40291591958](https://github.com/DuhItzAniket/VISOR/actions/runs/40291591958), c17e855: **17 real-model tests passed** with headless contrib and a one-provider check. Later 8fe7dfa only refines the Mac GUI guard; CUDA remains unverified |

The owner selected Apache-2.0. Source wheel and all four native bundles verified project notice inclusion. Local Windows build-info reports 0.2.0 from the frozen source and Apache-2.0; its expanded bundled check passed. See [desktop distribution](DESKTOP_DISTRIBUTION.md) for downloads, exact revisions and remaining release limits. Later documentation commits do not change the packaged application code.

## Delivered application

- Standalone Qt desktop builds for Windows x64, macOS Apple Silicon/Intel and Linux x64. End users do not need Python, pip or a terminal. The source remains Python; no native-language rewrite is claimed.
- Reference/target image pickers and drop inputs, filename/dimensions/previews, image canvases, comparison, synthetic benchmark, robustness sweep, batch, SIFT/ORB streaming video and camera calibration.
- SIFT/ORB use their actual descriptor norms and retained classical golden fixtures. One capability registry resolves nine genuine factories, including available AKAZE/BRISK; unavailable engines never silently substitute ORB/SIFT.
- Optional source engines use pinned LightGlue/XFeat integration, explicit source/weight setup and offline validated caches. CPU inference is verified. Standard bundles deliberately exclude learned dependencies/weights and hide developer pip controls.
- Independent typed vision results; common geometric validity checks; failed fits stay failures. Fit residual, assignment score, solver validity and truth-backed corner accuracy remain distinct claims. Measured stages record executed matcher/device/estimator and effective threshold policy.
- Match/inlier inspection, reference/target support hulls, residual quantiles and projected-area diagnostics. These are measured fit evidence, not calibrated confidence or general accuracy.
- Worker revision/cancellation guards discard stale results/errors and defer shutdown without blocking the event loop. File video processing streams decoded frames and releases capture on exit. Presentation overlay redraw still runs on the UI thread and needs large-result profiling.
- Project format 2 preserves relative image references and matching/estimator/overlay choices; version 1 remains readable. Missing project engines are reported rather than substituted. JSON analysis schema 2, CSV, HTML and image export retain actual result semantics.
- Restrained image-first workspace, accessible control names, visible focus, first-result image display, explicit no-fit state, synchronized overlay controls and platform user-folder dialogs. Image/project/export locations are remembered after successful choices; cancellation/failure preserves destination preferences.
- Owner-selected **Apache-2.0** for original VISOR source, root LICENSE/NOTICE, SPDX wheel metadata and project notice inclusion/validation in the desktop builder. This does not replace third-party/model terms or establish complete artifact notice compliance.

## Windows native review

Actual locally built executables were operated with native Windows input, file dialogs, screenshots and UI Automation. Reviewed SIFT/ORB image loading, shortcuts, first-result display, match rendering/PNG export, fit/no-fit text, parameter-change invalidation, project replay in a fresh process, both width editors, Pictures/Documents picker defaults, cancellation of dialogs and normal close. [Detailed evidence and limits](WINDOWS_REVIEW.md).

The latest headless executable exposed its native idle window and accessible control names, but helper activation failed twice; no new keyboard/picker interaction is claimed. The helper rejects Explorer drag endpoints outside its source window, so physical shell dragging remains unverified. Qt-dispatched drop tests and bundled checks verify both roles, copy-only action semantics, Unicode paths and error recovery separately. A helper resize attempt did not change dimensions and contributes no native scaling evidence. No OS accessibility/security settings were changed.

## Research and independent evidence

- Portable evaluation records manifests/input/truth hashes, runtime/source revision and dirty state, actual settings/results, raw failures, warmups and repetitions. Ground-truth corner error uses the documented pixel-extent convention; unannotated accuracy stays unavailable.
- Original [published evidence](evaluation/README.md), clean b2c7f0b: 18 synthetic development attempts and 72 attempts on two HPatches reporting scenes. Adverse valid fits are retained, including ORB's approximately 305 px corner-error example. The sample establishes neither engine ranking nor general false-positive rates.
- I15 [preregistered study](RELIABILITY_STUDY.md): four disjoint development scenes, two reserved reporting scenes, fixed grid/selection rule. Published 192 development and 72 reporting attempts, exact frozen choices and every reporting decision. Selection was pushed before reserved-scene performance was inspected. [Findings and raw evidence](evaluation/RELIABILITY_FINDINGS.md).
- Frozen inlier/support gates improved the development sample but rejected no additional reporting fits. SIFT retained a 9.88 px-error fit with 343 inliers. **Neither gate was promoted into desktop defaults; no reporting-set retuning occurred.**
- One reserved truth transform crosses the reference horizon under the whole-image corner metric. Six repeated annotation-error rows remain visible and are excluded from accuracy denominators; no pair was replaced. Reporting had no runtime failures. Per engine, 27 evaluable positive/six negative attempts represent nine/two distinct pairs. Repetitions are not independent scenes.

## Remaining release gates and limits

1. Clean-desktop install/launch/offline workflow/uninstall of each actual installer; native macOS/Linux interaction. Runner packaging and bundled checks do not prove these manual gates.
2. Physical shell drag/drop, complete keyboard/screen-reader announcements and 100%/150%/200% native monitor scaling/minimum-window review. Current Windows interaction review is partial.
3. Complete per-artifact dependency/native-library notices and licensing-route review. Project-license choice is closed; [third-party inventory](THIRD_PARTY_INVENTORY.md) records remaining work.
4. Windows signing and macOS signing/notarization for a public distribution. Existing validation builds are unsigned; no public production release is claimed.
5. Packaged learned runtime/model redistribution review, exact weight notices and GPU verification before advertising those packaged capabilities.
6. Broader user-relevant negatives, occlusion/repeated texture/low texture and stability/overlap studies before a general localization-reliability claim. The application remains a planar-registration workbench, not general 3D pose recovery.

These gates remain open in the ledger. Completed source tasks and successful builds do not silently mark the whole release production-ready.
