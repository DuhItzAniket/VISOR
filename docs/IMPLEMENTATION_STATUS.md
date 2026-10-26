# Implementation status

Updated 2026-10-26. This is the current snapshot; chronological changes, prior checks and failed runs are preserved in [IMPLEMENTATION_LOG.md](IMPLEMENTATION_LOG.md) and Git history. Tasks and acceptance gates are in [IMPROVEMENT_PLAN.md](IMPROVEMENT_PLAN.md).

## Dependency-notice and artifact audit follow-up

Added offline collection of actual installed dependency/runtime notices and a checked-in, hash-pinned 203-file Qt/PySide notice corpus. The bundle validates the notice index against actual Qt version and file hashes. A separate frozen-file inventory records hashes, distribution/source origins, overlapping claims and unresolved entries, without publishing developer absolute paths or claiming full transitive compliance.

Native run [40227340916](https://github.com/DuhItzAniket/VISOR/actions/runs/40227340916) passed all four targets at **a6fc4fd**, including frozen startup, all notice hashes, PNG/JPEG/BMP/TIFF/WebP decoding and the classical workflows. Missing Qt wheel notices use an explicitly recorded version-matched pinned-source fallback; missing notices for other components still fail. Unused PDF-image/Qt Virtual Keyboard plugins and optional NumPy testing/F2PY/YAML dependencies are excluded; NumPy's implicit stdlib secrets import is explicitly retained.

Downloaded and inspected all four audit artifacts; each inventory hash matches build-info and each smoke report succeeds. Windows: 218 notice files, 423 filesystem entries, zero unresolved origins. Linux: 214/664/140; macOS ARM64: 214/766/197; macOS Intel: 214/769/199. Unresolved entries include native/system libraries and layout links; counts are not counts of missing licenses. A mapped filesystem origin also does not establish transitive/native/source-offer compliance. Linux includes OpenCV's additional Qt5 libraries; minimizing and tracing that dependency profile is tracked under I16.

## Current verification

I16 follow-up in progress: source/build requirements now select the headless contrib wheel at the same OpenCV 4.11.0.86 pin. Packaging rejects overlapping providers and unexpected HighGUI backends; frozen checks add MJPEG encoding/decoding and three-frame ORB tracking. An isolated Windows environment passed 226 core tests/5 skips/17 model deselections, including the original classical goldens. The full existing developer suite passed 243 tests/5 skips in 108.16s; 28 focused profile/installer/golden/image/video checks passed. Ruff and focused three-module Mypy passed. New native/optional lanes must pass before the download links are replaced.

LightGlue's pinned metadata requests opencv-python, so source setup now installs its explicitly declared inference dependencies first and the pinned adapter with --no-deps separately. This avoids installing another cv2 provider; the upstream package-name mismatch remains documented rather than hidden with false metadata. Optional installation failures stop the sequence and remain failures. Standard desktop bundles still exclude learned dependencies and models.

| Scope | Verified result |
|---|---|
| Full local source suite, including installed optional models | **227 passed, 5 skipped in 42.99s**; three skips are this Windows host's unprivileged symlink restriction. Focused audit/notice/version: 25 passed/3 skipped |
| Lint | Ruff passed for src, tests and shared desktop builder; whitespace check passed |
| Type checking | Focused modules passed, including result contracts, matching/geometry, runtime/setup, registry/pipeline, jobs, evaluation/study, video, image input and builder. No whole-UI Mypy pass is claimed |
| Source wheel | 0.2.0 wheel built in isolation; Apache-2.0 SPDX metadata and full project LICENSE/NOTICE verified inside the wheel |
| Latest completed native matrix | [40227340916](https://github.com/DuhItzAniket/VISOR/actions/runs/40227340916), source **a6fc4fd**: Windows x64, macOS ARM64, macOS Intel and Linux x64 passed core tests, lint, packaging and bundled workflows, including project/dependency notice checks |
| Native core test counts at a6fc4fd | Windows **213 passed, 2 skipped, 17 model tests deselected**; macOS/Linux each **211 passed, 4 skipped, 17 deselected** |
| Separate optional CPU lane | [40217775833](https://github.com/DuhItzAniket/VISOR/actions/runs/40217775833), c67936c: 17 real-model tests passed. Later full local suite also includes installed-model checks; CUDA is unverified |

The owner selected Apache-2.0. Source wheel and all four native bundles verified project notice inclusion. Local Windows build-info reports 0.2.0 from the frozen source and Apache-2.0; its expanded bundled check passed. See [desktop distribution](DESKTOP_DISTRIBUTION.md) for downloads, exact revisions and remaining release limits. Later documentation commits do not change the packaged application code.

The previous b926702 run 40221478271 failed one evidence-provenance assertion on Linux/both Macs while Windows passed. The assertion hashed original Windows CRLF JSON bytes against Git's LF checkout. The repaired canonical JSON-content hash, preserved original byte hash, LF evidence/output rules and LF/CRLF regression passed all four targets in 40222252759. No gate, result, metric or compressed raw report changed.

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

The helper rejects Explorer drag endpoints outside its source window, so physical shell dragging remains unverified. Qt-dispatched drop tests and bundled checks verify both roles, copy-only action semantics, Unicode paths and error recovery separately. A helper resize attempt did not change dimensions and contributes no native scaling evidence. No OS accessibility/security settings were changed.

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
