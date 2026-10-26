# Implementation Log

## 2026-10-26 — Repair the type contracts found on fresh hosted runners

- Run 40338832093 at 506a4c9 passed full core and lint on both hosts (Windows 316 passed/2 skipped/17 deselected; Linux 314 passed/4 skipped/17 deselected), then failed the new type step on 30 pre-existing errors in nine imported modules. It is not recorded as a successful overall workflow. Local explicit-eight-file checking had not reported those imported-module errors; the fresh runner exposed the gap.
- The repository now lists 17 explicit type-check targets so local/CI scope is consistent, including those nine modules. Fixed accurate float32/float64 calibration input annotations, byte-preserving OpenCV result casts, FLANN parameter dictionary invariance, the learned match tuple's element type, actual combo-model/signal interfaces, validated estimator narrowing and distinct numeric/selection control loop variables. Optional Torch/torchvision/LightGlue imports may be absent in core checks; only missing external imports receive that override, not VISOR errors. No check is skipped and no matching norm, pixel arithmetic, solver, threshold, fit membership, metric or golden fixture changed.
- Cold Mypy passed all 17 selected files, all-source/script Ruff passed and 44 focused calibration/video/sweep/matching/classical/UI lifecycle/loader checks passed in 5.51s. Fresh automatic full-core/type/wheel verification follows this commit. Current native installers remain the ce68a2c validation cohort; no new physical desktop/signing/GPU claim follows from annotation repairs.

## 2026-10-26 — Repair checkout metadata exposed by automatic core CI

- First automatic run 40338166624 at 51362ab failed on both runners before tests: checkout's immediate credential cleanup encountered the orphaned 160000 gitlink Sample/Dataset/HPatches with no .gitmodules URL. Repository fetch succeeded; no test failure/pass is inferred from this run.
- Removed only the orphan gitlink from the Git index using git rm --cached and confirmed the local dataset directory remains present. Ignored the complete external HPatches folder instead of only its sequences child; no dataset file was deleted or modified, no replacement URL/ownership was invented, and no source algorithm/build byte changed. Fresh checkouts obtain no implicit dataset/submodule, consistent with the explicit evaluation preparation workflow.
- Verified there were no other gitlinks and the existing source checks/wheel audit remain valid; fresh automatic Windows/Linux core verification follows this metadata repair. No GPU work or local interactive app launch.

## 2026-10-26 — Add automatic model-free checks and verify source wheels

- Added push/main, pull-request and manual core checks on Windows/Linux with read-only checkout, per-ref supersession, pinned desktop dependencies, offscreen Qt and accelerator mask -1. Runs core regressions without model downloads, all-source/script Ruff, focused types and an isolated source-wheel build/byte audit. JUnit evidence is retained. Native installers/four-target packaging and public release gates remain separate; no branch-protection setting is changed.
- The wheel auditor reads without importing and verifies actual source modules/icons/package bytes, source-declared identity/version, unambiguous Apache-2.0 metadata, complete LICENSE/NOTICE bytes and one headless-contrib OpenCV provider. It rejects duplicates/unsafe paths, unrelated packages, missing/changed inputs and ambiguous multi-wheel directories. Nine focused tamper/incomplete/identity/directory regressions passed; all-source/script Ruff and focused eight-module Mypy passed. A real isolated 0.2.0 wheel passed: 46 source modules/57 package files, SHA256 8cffd79ec8592608fba6346d28f114d15a1fe6efbd872a46b83e2da09122d441. This is project/source packaging evidence, not complete dependency/model licensing certification.
- The broad local core attempt aborted with Windows access violation exit 0xC0000005 while creating a pytest temporary directory, another differing site; no pass/JUnit report was recorded. A subsequent source-wheel/evaluator/generator focus passed 22 tests in 2.74s. Session application ownership has not established or resolved the cause of these intermittent local native aborts. The first fresh hosted-runner full-suite evidence follows before this workflow is called verified. All local operations use CPU; no GPU probe, model downloads or interactive app launch. Native ce68a2c downloads continue into owned resumable archives; no partial candidate is declared complete.

## 2026-10-26 — Retire the private-folder evaluator path

- Replaced the old script's hardcoded developer Windows path, implicit learned engines, accelerator preference and silently skipped CSV inputs with a compatibility entry point for the canonical portable evaluator. Dataset/output/engine choices are explicit, CPU is the default and raw failure/truth/provenance semantics are shared. The old private CSV summary is intentionally retired and migration is documented.
- Both help paths and an actual generated three-pair ORB report passed through the compatibility script with no explicit device flag; requested/actual device was CPU and no learned engine ran. The 13 generator/evaluator regressions passed in 3.23s, Ruff passed and focused four-module Mypy passed after aligning the estimator annotation with the existing validated RobustMethod contract. No estimator/algorithm/default changed; older raw reports retain their exact recorded source/code hashes.
- Initial full candidate downloads were interrupted across the turn boundary before extraction. No local checksum pass was claimed. Retrying into owned, resumable partial ZIP files with CRC/path checks; credentials and signed URLs are never logged. All four ce68a2c native jobs and their small audit hashes/reports already passed independently. GPU work remains deferred; no local interactive application launch.

## 2026-10-26 — Publish the frozen CPU stress probe, including the adverse negative

- Evaluated the unchanged preregistered construction/settings at clean c79b950 on CPU, with no installed Torch/LightGlue. Retained every 126 measured attempt and 42 warmups, no runtime/annotation errors. Verified every actual device is CPU and published exact compressed raw report bytes, their SHA256, per-condition denominators and limitations. Protocol/generator hashes and all input/truth hashes are embedded.
- Each engine fit 18/36 truth-backed positives within 3 px; both failed all repeated-tile and low-texture positives. SIFT accepted one independent-scene negative on all three repetitions with nine inliers and ~0.327 px residual; ORB accepted none in this small constructed sample. Repeats are not independent scenes, and low residual/support is not object-presence proof. No reporting-set retuning, gate promotion, engine ranking or general reliability/speed claim; desktop algorithms/defaults/goldens are unchanged.
- Current full CPU core after the generator addition passed 303 tests/6 skips/17 optional deselections in 18.10s. Generator/evaluator focus 13 tests, Ruff/focused generator types passed. The separately running native image-loader matrix 40311819086 at ce68a2c also passed all four targets; downloaded all four small audits and verified identities, inventory hashes, actual bundled/installed background-input smoke success and all 91 Linux notice hashes. Full candidate checksum downloads are in progress; no new manual desktop/GPU review is implied.

## 2026-10-26 — Freeze broader synthetic development cases before measurement

- Added a deterministic CPU-only preparation tool for textured, repeated-tile, smooth low-texture and half-occluded positives with known mappings, plus independent-scene/noise/blank negatives. The frozen protocol fixes three seeds, 21 pairs, exact settings, one warmup/three measured repetitions, denominators and reporting rules before engine results are inspected. It does not tune I15's reserved reporting sample or change algorithms/defaults.
- Generator/protocol hashes and exact truth are in the portable manifest. Existing output is refused. Two generator reproducibility/annotation/overwrite regressions plus the existing evaluator suite passed 13 tests in 2.30s; Ruff and focused generator Mypy passed. No engine performance was measured in preparation tests. Measurement follows only after this protocol/generator commit is pushed; synthetic counts will not support a general localization/false-positive/speed claim. No GPU, model download or local interactive application used.

## 2026-10-26 — Move image selection decoding off the UI thread

- Picker, drop, history and project replay now queue per-slot workers for path/header access, native decode, orientation and thumbnail scaling. QImage values transfer by guarded signals; QPixmap/widget work stays on the GUI thread. There is at most one active decoder and one replaceable pending request per role. Shared vision algorithms/results are unchanged. The synchronous load_path helper remains for controlled checks; user flows use request_path.
- Revision tickets discard stale success/error delivery; clear/cancel/shutdown invalidate pending work. Cancellation is observable before/after an indivisible native codec call; close remains event-driven and waits for worker ownership to end. Analysis/project-save/result-export actions wait for input loading. Project replay reports completion only after both slots finish and does not substitute old inputs after an unreadable project image. History records only settled pairs. Failure preserves existing picker/drop input.
- Copy drop acceptance now acknowledges a queued open request, not completed decoding. Decode failures are reported asynchronously in the input. This intentionally replaces synchronous unreadable-drop rejection; Move-only/remote/unsupported payloads stay rejected and source files are untouched. Qt upstream rationale/limitations are recorded in RESEARCH_REVIEW.md. Bounded retained thumbnails do not guarantee bounded codec peak memory or instant cancellation.
- Controlled and actual-decoder tests cover worker/UI thread identity, GUI heartbeat, bounded latest requests, stale success/errors, cancellation tokens, clear and deferred close. Focused input/project/overlay checks passed 52 tests, then the additional pre-cancel regression and lifecycle set passed 41 tests; the final targeted worker/install/actual offscreen smoke checks passed 16 tests. Complete CPU core passed 301/6 skipped/17 deselected in 16.44s. A later broad run aborted in Qt image decoding rather than OpenCV; no pass is recorded for it. The test harness now holds one QApplication for the complete session instead of allowing its wrapper lifetime to vary between tests. The final core then passed 301/6 skipped/17 deselected in 16.69s; this stabilizes test ownership but does not establish the native-crash cause. Ruff and focused loader/widget/smoke Mypy passed. No local interactive app launch, GPU tests or model downloads; physical native/accessibility/scaling review remains separate. An initial no-isolation wheel attempt failed because the core environment has an older setuptools than the declared build requirement; the normal isolated wheel build then passed. Exact loader/widget/main/smoke source bytes, SPDX Apache-2.0, headless dependency identity and LICENSE/NOTICE bytes were verified inside the wheel. The application was not launched.
- The preceding a4293b0 native matrix 40309675591 passed all four targets: Windows 298/2 skipped/17 deselected, others 296/4 skipped/17 deselected, actual installed workflow/removal and candidate preparation. Independently checked all four downloaded audit identities/inventory hashes and bundled/installed success, plus all 91 Linux notice hashes. Its refreshed manifest records 12 sentence-period interpretations and six unresolved filename references. This is the prior synchronous-input cohort; a new native asynchronous-input matrix follows. Earlier local OpenCV crashes remain recorded without an invented cause.

## 2026-10-26 — Correct image orientation and preserve recoverable input state

- Reproduced three failures before changing product code: EXIF-rotated preview metadata disagreed with OpenCV analysis, an unreadable replacement cleared a good input, and resizing reopened the original file. Explicit Qt auto-transform now matches analysis; retained thumbnails are bounded to 1024 pixels per side and resize uses that cache. Original dimensions are reported independently of thumbnail size. Analysis decoding/geometry/goldens are unchanged.
- Failed picker/drop replacements retain the selected image and emit no input-change event; a rejected drop stays rejected. Recovery text explicitly identifies the retained image. Project replay explicitly clears an unreadable project image rather than silently substituting an old workspace input. Clear releases the cached thumbnail. Initial loading still performs decoding synchronously; moving initial decode off the UI thread remains an explicit responsiveness follow-up, especially for formats without scaled decoding.
- 32 focused checks passed in 1.34s, including all eight JPEG EXIF values on both roles, corner colors/dimensions against the real analysis decoder, bounded retained memory, resize after source rename, failed-drop acceptance/state and unreadable project replay. Complete headless CPU core passed 294 tests/6 skips/17 optional deselections in 16.55s. The two earlier native OpenCV crashes did not recur in this run; no root-cause resolution is claimed. Ruff and focused widget/smoke Mypy passed.
- Extended the frozen smoke check for oriented JPEG, replacement failure and source-independent preview; native matrix evidence follows. No local interactive app launch, physical desktop/scaling/screen-reader review or GPU verification is claimed. CUDA mask -1 retained throughout local tests; no model downloads used.

## 2026-10-26 — Validate build-host notice evidence and review literal references

- Linux-only run 40305950475 at c080dd5 passed core 274 tests/4 skips/17 deselected, bundle checks, actual Debian install/run/purge and candidate preparation. The original host supplied 85 collected system sources, 78 package database claims, zero unclaimed sources and 91 copied notices (78 package copyright files/13 common-license files). Downloaded the review/audit and checked every notice hash plus source/run/inventory identity. Published its manifest; this does not retroactively assign ownership to older builds or change installed notices.
- Its strict literal extractor recorded 18 reference gaps, including 12 sentence-ending periods and six GPL-2.0/GPL-3.0 path spellings. Added a narrow, recorded punctuation interpretation only when an actual normalized common-license filename exists; no license alias/term is selected. Windows' trailing-period filename alias required checking actual directory spelling. Focused default-CPU parser/benchmark/classical checks passed (15 passed/one host symlink skip); Ruff/focused Mypy passed. A further isolated parser/benchmark/sweep/classical run passed 19 tests with one host symlink skip in 3.91s. Native punctuation-refresh evidence follows with the next relevant build.
- One broad local core attempt aborted in OpenCV's native SIFT extraction during an existing benchmark; no pass was recorded and no vision code had changed. The focused benchmark/classical rerun passed unchanged. A complete test-process-only single-thread CPU rerun also aborted, later in native ORB extraction during an existing robustness sweep; it did not produce a passing suite or JUnit report. The differing crash sites remain under investigation. Native CI and isolated regressions will be used to distinguish source defects from local runtime instability; no cause is yet established. Owner's GPU-training process was not inspected or modified.

## 2026-10-26 — Capture Linux system notice evidence on the original build host

- Added exact canonical-equivalent dpkg file queries, preserving multiple/unclaimed package database claims and actual package/source versions/status. Source hashes are recorded at lookup time; these claims are not binary authenticity or native licensing conclusions. No basename package guessing or legal-term selection occurs.
- The collector copies exact package copyright bytes and literal common-license references, with contained paths, hashes, missing-reference records and source/code/collection identities. It refuses to overwrite evidence. Review output stays outside the frozen application; installed notices/inventory are unchanged. Linux CI uploads the review texts separately and its manifest in the small audit artifact.
- Added a Linux-only workflow target for this platform-specific review. Five focused copy/provenance/overlap/missing/path checks passed; one local Windows symlink test skipped because the host does not allow it. Ruff and focused three-module Mypy passed. Current isolated core: 272 passed/6 skipped/17 deselected in 15.11s. Native Linux refresh follows. All work remains CPU-only, with no local app launch or GPU inspection.

## 2026-10-26 — Trace actual internal aliases without replacing inventory claims

- Added a CPU-only/offline derived origin tool. It verifies input inventory SHA256 against build-info, follows exact internal leaf and directory links, retains overlapping claims, and preserves cycles/missing/unknown targets. Escaping paths and missing origin kinds fail. Original inventories are unchanged; no filename-based ownership or license is invented.
- Published all four derived reports with inventory/source/platform/code hashes. Linux's 116 original unresolved entries comprise 31 exact file links and 85 regular system files. ARM/Intel Macs have 181/183 exact file links, 14 directory aliases each, and two regular paths each (Info.plist/visor.icns). This is structural evidence, not complete native-component/license/source-offer compliance. Next OS-package evidence must come from the actual build host.
- Eight focused regressions, Ruff and focused three-module Mypy passed; current isolated core 267 passed/5 skipped/17 deselected in 14.78s. This maintainer-only module/CLI does not change the packaged application's rendering or vision algorithms and requires no native bundle refresh. No GPU or local app launch used. The refreshed explicit CPU workflow 40302703042 at 87551fc also passed 17 optional tests/264 deselected in 52.26s with accelerator mask -1.

## 2026-10-26 — Verify all installed candidates and downloaded checksum sets

- Run 40299138359 at 81e81da passed source checks, packaging, frozen workflows, actual hosted-runner installer/app-copy/workflow/removal and candidate preparation on Windows x64, Linux x64 and both Mac architectures. Core: Windows 262 passed/2 skipped/17 deselected; other targets 260 passed/4 skipped/17 deselected. Installed apps ran with an empty PATH directory and removed Python path variables. Network-disabled clean-desktop use, native interaction and trusted signing remain separate.
- Downloaded all four small audits: source identity and inventory SHA256 match, bundled/installed smoke reports succeed, exact installers and their byte hashes are recorded. Also downloaded all four complete candidates and independently rechecked all 26 package/evidence/manifest SHA256 values, including setup/ZIP, deb/tar and both DMGs. Metadata remains explicitly signing-unverified. Updated all four validation download links.
- Current isolated core: 259 passed/5 skipped/17 deselected in 15.36s; masked full source 276 passed/5 skipped in 78.69s; final explicit-CPU optional tests 17 passed/264 deselected. Rebuilt source wheel and verified exact current overlay/candidate/canvas module bytes, headless dependency identity and full project license notices. A separate isolated Windows source build at 81e81da completed; it was not launched after the owner requested avoiding GPU work. No local user installation or OS setting was changed.

## 2026-10-26 — Keep optional test inference on CPU

- An unrestricted local optional-model run stalled and was stopped without recording a pass. The subsequent masked full run passed 276 tests/5 skips in 78.69s. No CUDA result is inferred from it.
- The owner then requested no GPU use while another project trains. Found three pipeline tests inheriting the application's accelerator preference; changed them to explicit CPU configuration and asserted actual result device. Application defaults are unchanged. Optional CI/local CPU commands use the nonempty CUDA visibility mask -1. Focused optional CPU suite: 17 passed/264 deselected in 62.12s with that mask; Ruff passed. No further local GPU tests or interactive app launches were performed.

## 2026-10-26 — Verify I17 native delivery and prepare installed-artifact release checks

- Run 40296839880 at 9085c12 passed Windows x64, Linux x64 and both Mac architectures after the test event-loop repair. Core: Windows 246 passed/2 skipped/17 deselected; other targets 244 passed/4 skipped/17 deselected. Downloaded all four audits and checked source identity, inventory SHA256, successful frozen reports and the new background/latest-style/viewport/styled-export check. Notice/files/unresolved counts are unchanged from the verified headless profile. Updated validation download links. The first failed run remains recorded; no assertion/deadline was removed.
- Added CI-only actual installer/app-copy, installed workflow and removal checks. They refuse local/self-hosted machines and existing installs. Installed executables must match frozen hashes and run with an empty PATH directory and removed Python path variables. Windows uses per-user Inno setup/uninstall; Linux installs/purges its Debian package; Macs mount/read/copy/detach actual DMGs into private staging. This does not establish a clean-user-desktop, network-disabled, signing, Gatekeeper or native interaction gate.
- Added atomic preparation of flat, platform-prefixed evidence, manifests and SHA256SUMS. Candidate creation rejects failed/stale/mismatched evidence and changed installer/evidence bytes; it never overwrites an existing candidate. Signing remains explicitly unverified. Sixteen focused runner-guard/provenance/tamper checks, Ruff and focused four-module Mypy passed. Final isolated core: 259 passed/5 skipped/17 deselected in 20.83s. Native installer refresh follows; full optional CPU checks run separately. See RELEASE_PREPARATION.md for commands and boundaries.

## 2026-10-26 — Investigate native overlay test delivery

- Run 40295997052 at 891e899 exposed four overlay test wait failures on Linux and both Macs, despite local source success; the old verified downloads are unchanged. The tests repeatedly called C++ QTest.qWait rather than entering the real application event loop, which can starve Python drawing of the GIL on native builds.
- Changed the overlay test wait helper to a real nested QEventLoop with poll/deadline timers, retaining the same four-second deadline and every assertion. Production smoke already uses that event-loop model. Focused source checks: 23 passed in 5.49s; isolated full core: 243 passed/5 skipped/17 deselected in 19.98s; Ruff passed. Native refresh follows; this hypothesis is not treated as resolved until it passes. Windows job of the original run passed packaging and the expanded frozen workflow.

## 2026-10-26 — Bound overlay work and preserve the inspected viewport

- Local profiling of the scaled classical fixture exposed UI-thread drawing and repeated RGB uploads. Added a reusable maintainer profile with runtime/source/input hashes, raw samples, warmups and explicit scope: scaled existing features, not high-resolution extraction, accuracy or portable native latency. It refuses to overwrite evidence. Final clean-source profiles follow.
- Added one background overlay worker with one replaceable pending request, 40 ms input coalescing, cooperative drawing checks and ticket-guarded main-thread delivery. New input/result/cancel/close invalidates old work. Failures retain the existing result and restore effective controls; image/JSON/CSV/HTML export waits for a completed consistent snapshot. Close remains event-driven until the worker finishes. No solver, correspondence, accuracy or algorithm timing changes.
- Canvas upload uses Qt's BGR888 support and owns copied bytes; noncontiguous input/color/lifetime tests passed. Same-size overlay updates replace pixmaps without resetting zoom, and unchanged rectified images are not uploaded again. Added actual background/latest-style/viewport/styled-export checks to the frozen workflow. Native interaction/scaling remains separately unverified.
- Focused canvas/overlay/pure cancellation/job checks: 21 passed; expanded notice/smoke repair: 2 passed. Isolated core: 243 passed/5 skipped/17 deselected in 24.77s. Ruff and focused rendering/canvas/coordinator Mypy passed. Full source: 260 passed/5 skipped in 67.42s (single-thread OMP/MKL test process). Native refresh follows. Initial smoke fixture required marking simulated zoom as manual, matching actual wheel behavior; no product check was removed.

## 2026-10-26 — Verify and publish the four-target headless profile evidence

- Run 40292319995 at 8fe7dfa succeeded on Windows x64, Linux x64 and macOS ARM64/Intel. Native core: Windows 235 passed/2 skipped/17 deselected; other targets 233 passed/4 skipped/17 deselected. Every packaged workflow passed actual notice hashes/Qt version, OpenCV backend policy, five image codecs, Qt copy-drop events, SIFT/ORB, exports/project replay, MJPEG encode/decode with three tracked ORB frames and shutdown. Existing classical goldens remain unchanged.
- Downloaded all four small audit artifacts and independently checked inventory SHA256 against build-info, source revision, successful smoke reports and absence of Qt5 files. Notice/files/unresolved counts: Windows 218/423/0, Linux 214/608/116, ARM Mac 214/766/197, Intel Mac 214/769/199. Actual backend NONE on Windows/Linux and COCOA on both Macs is retained. Linux fell from 664 to 608 entries; unresolved origins and native/source-offer obligations remain explicit.
- Separate optional CPU lane 40291591958 at c17e855 passed 17 real-model tests with one headless provider. 8fe7dfa subsequently changes only the Mac backend validation/provenance and its tests/docs. Updated current status, ledger, inventory and all four validation download links. I16 GUI dependency reduction is verified; I12/I13 complete transitive notices/source offers, signing and manual desktop gates remain open. No new visual/native interaction gate is inferred from the offscreen checks or failed helper activation.

## 2026-10-26 — Final source/profile checks and native helper limitation

- Final full existing developer suite: 249 passed/5 skipped in 66.39s (OMP/MKL threads limited to one in this test process; not a performance benchmark). Isolated headless core: 232 passed/5 skipped/17 deselected in 18.01s. Source wheel built in isolation and verified headless provider requirement, Apache-2.0 SPDX metadata and both project notices. No environment/model/build files committed.
- Rebuilt clean 8fe7dfa Windows executable in the isolated headless environment; actual frozen notice/image/video/classical/export/project/shutdown workflow passed. Inventory: 423 entries, zero unresolved origins and no Qt5; actual GUI backend NONE is recorded.
- Computer Use captured the native idle window/control tree but could not activate it, including after fresh selection. Stopped input after the failed recovery. Record this helper boundary separately in WINDOWS_REVIEW.md; no new keyboard/picker, scaling, clean-install or screen-reader gate is closed. Final native CI refresh is tracked separately.

## 2026-10-26 — Record the pinned Mac wheel's Cocoa backend honestly

- Run 40291588173 at c17e855 exposed an over-strict NONE-only assumption on both Macs: the correctly selected headless OpenCV 4.11 wheel reports COCOA. Upstream build tag 86 (commit 255564a37c4a23275485e827abbe19031347d458) explicitly documents retaining Cocoa in headless Mac wheels while disabling Qt/GTK/Win32UI. Windows local frozen image/video workflow passed. Failed Mac jobs are not promoted.
- Narrowed the exception to Darwin/OpenCV 4.11.0/COCOA; other versions, platforms and Qt backends still fail. Build-info and frozen reports retain the actual backend rather than calling Cocoa NONE. Added six cross-platform/version cases: focused checks 37 passed/3 host-symlink skips; isolated full core 232 passed/5 skipped/17 deselected in 18.01s; Ruff/focused Mypy passed. Final native refresh follows. The native Qt5 artifact exclusion remains mandatory.
- Optional CPU run 40291591958 at c17e855 passed all 17 real-model tests and the one-provider check using headless contrib. Windows/Linux jobs of 40291588173 passed packaged image/video workflows; both Macs failed the original over-strict guard. Preliminary Linux inventory dropped from 664 to 608 entries and contains zero Qt5 files, retaining explicit unresolved-origin review.

## 2026-10-26 — Isolate OpenCV from the desktop GUI runtime

- Actual Linux audit showed regular OpenCV's Qt5 libraries alongside PySide6. Changed source/desktop dependency to opencv-contrib-python-headless at the unchanged desktop pin 4.11.0.86, following upstream guidance for applications using another GUI toolkit. No VISOR HighGUI calls exist. Builder rejects missing/wrong/multiple cv2 providers, checks compiled GUI backend NONE and forbids bundled Qt5 libraries. Evaluation records all four possible distribution names without relabeling historical evidence.
- Added actual MJPEG encode/decode and three-frame ORB tracking to the frozen workflow. Retained all classical goldens, image codecs and Qt workflows. A separate ignored environment supplies headless OpenCV without altering the existing developer interpreter. Isolated core: 222 passed/5 skipped/17 deselected before four final installer tests; 28 focused installer/profile/golden/image/video checks passed. Ruff and focused audit/runtime/builder Mypy passed. Global source before the final installer change: 239 passed/5 skipped in 75.85s. Final source full suite: 243 passed/5 skipped in 108.16s; isolated headless core: 226 passed/5 skipped/17 deselected in 13.62s. Native checks follow.
- Reviewed installed pinned LightGlue metadata and found its opencv-python requirement would introduce a second cv2 provider. Split explicit inference dependencies from pinned --no-deps adapter installation in worker, docs and optional CI. Four mocked-process cases verify setup ordering and that dependency/adapter/cache failure stops progress. Documented the upstream package-name mismatch; no metadata shim or fabricated pip-check success. Standard bundles remain model-free. Native downloads stay at verified a6fc4fd until refresh succeeds.

## 2026-10-26 — Verify final dependency audit across four native targets

- Run 40227340916 at a6fc4fd passed packaging, lint, core tests and the expanded frozen workflow on Windows x64, macOS ARM64/Intel and Linux x64. Windows core: 213 passed/2 skipped/17 deselected; other targets: 211 passed/4 skipped/17 deselected. Local full source: 227 passed/5 skipped in 42.99s, including installed optional models; three skips reflect host symlink permissions. Focused audit/notice/version: 25 passed/3 skipped. Ruff and focused audit/builder Mypy passed.
- Downloaded all four small audit artifacts. Inventory hashes match build-info; source identity is a6fc4fd and every smoke report succeeds. Notice/files/unresolved counts: Windows 218/423/0; Linux 214/664/140; ARM Mac 214/766/197; Intel Mac 214/769/199. Each frozen check verified all notice hashes and Qt version, five image codecs, copy-only Qt event drops, SIFT/ORB, exports, project replay and shutdown. Local Windows bundle passed the same workflow. Updated verified download links.
- Unresolved native/system/link entries stay explicit. Successful source mapping is not a transitive license certificate. Actual Linux inventory includes a second Qt runtime supplied by OpenCV; added I16 to test the same-version headless contrib package using an isolated environment, upstream guidance and retained algorithm/native gates. No global OpenCV uninstall or visual change is part of this completed batch.

## 2026-10-26 — Verify the audit bundles and refine relocated-file evidence

- Run 40226712653 completed successfully at db573a2 on all four native targets, including third-party notice hashes/Qt version, all five input formats, classical workflows, exports/project replay and shutdown. The explicit NumPy stdlib import repaired the previous startup failure.
- Downloaded small audit artifacts from each platform. Initial origin gaps included platform relocation and framework layout/signature metadata, as well as genuine system/native dependency gaps. Refined mapping only when a collected filename has one unique source; ambiguous filenames remain unresolved. Layout symlinks and signature metadata are identified without claiming library ownership. System/Homebrew source areas are recorded without developer-private paths.
- Focused relocated/ambiguous mapping regressions passed; full focused audit/notice/version set: 25 passed/3 Windows host-symlink skips. Ruff and focused audit/builder Mypy passed. A final native metadata refresh follows. These records do not certify transitive component/source-offer compliance.

## 2026-10-26 — Preserve NumPy's implicit standard-library dependency

- Run 40226317768 passed notice staging/building but its bundled startup check exposed NumPy 1.26's Cython random extension importing stdlib secrets implicitly. Removing optional NumPy test dependencies also removed the incidental import edge that had collected it.
- Added an explicit hidden import for that required stdlib module; optional testing/YAML/F2PY exclusions remain. The actual bundled bootstrap/workflow check is the regression gate. No vision algorithm or seeding policy changed. Small audit artifacts supplied the precise bootstrap trace without downloading installers.
- Full local source at 8f34325: 225 passed/5 skipped in 48.39s; three skips reflect this host's symlink restriction. Ruff and focused audit/builder Mypy passed. Native verification follows the fix; failed startup builds are not promoted.

## 2026-10-26 — Handle fresh Qt wheel notices explicitly

- Native run 40225818839 failed during notice staging on all four targets because fresh PySide6 wheels omit the standalone license-reference file present in the local environment. Core source checks were not replaced with fabricated packaging success.
- Permit that specific Qt/PySide/Shiboken case only through matching, hash-verified pinned PySide LGPL/GPL source texts. Each component records its zero wheel-file count and source fallback. Missing notices for other distributions still fail. Added a clean-wheel regression and an incomplete-fallback rejection case. Focused checks: 23 passed/3 host-symlink skips; Ruff and focused audit/builder Mypy passed.
- Added separately downloadable small audit artifacts so the per-platform inventory can be inspected without downloading full installers. Last local committed-source build: 218 notice files, 423 frozen filesystem entries, no unresolved or overlapping distribution-file origins. Opaque/native/source-offer obligations remain open despite that origin count. Full local suite at 6dea02f: 224 passed/5 skipped in 45.83s (three symlink cases cannot run on this Windows host).

## 2026-10-26 — Collect dependency notices and audit actual frozen files

- Inspected PyInstaller's real collection table and found unused PDF-image and Qt Virtual Keyboard plugins. Added a small QtGui hook using the upstream collector while filtering those plugins, with an artifact guard against their return. Excluded optional NumPy testing/F2PY/YAML dependencies uncovered in the collection cross-reference.
- Prepared 203 unmodified Qt/PySide 6.11.2 source notice/attribution/reference files using immutable commit URLs and SHA256; no unresolved LicenseFile references. Kept original bytes with Git binary attributes. The maintainer refresh is explicit; normal builds validate and copy the snapshot offline.
- Added installed-package/interpreter notice staging, exact byte hashes and Qt version verification in frozen checks. Added an external frozen-filesystem inventory, package/source origin mapping, overlapping/unknown-origin preservation, hash linkage in build-info and CI artifact upload. No developer absolute paths or model downloads are published. Inventory scope explicitly leaves opaque/transitive/source-offer review open.
- Preliminary Windows packaging passed the expanded workflow: 218 notice hashes, PNG/JPEG/BMP/TIFF/WebP decoding, classical localization, exports, project replay and shutdown; unwanted Qt modules absent. Final committed-source native refresh follows the last exclusions/overlap refinement.
- Focused audit/notice/version suite: 22 passed. Full source: 224 passed/2 skipped in 40.80s. Ruff and focused audit/builder Mypy passed. Exact corpus provenance and remaining review are documented in THIRD_PARTY_INVENTORY.md; collection is not a compliance certificate.
- Final inventory refinement rejects escaping and absolute symlinks instead of publishing non-portable/developer paths. Focused follow-up: 22 passed/3 skipped; this Windows host does not permit unprivileged symlink creation, so those three filesystem cases await Linux/macOS CI. No OS setting was changed to bypass that limit.

## 2026-10-26 — Final Apache-licensed four-target validation

- Run 40222886823 completed successfully at 1f76d41 on Windows x64, macOS ARM64, macOS Intel and Linux x64. Windows core: 193 passed/2 skipped/17 model tests deselected; other targets: 191 passed/4 skipped/17 deselected. Every target passed lint, packaging and the full bundled workflow, including project LICENSE/NOTICE and copy-only Qt drops. Updated all artifact links with exact revision/run identities.
- Local Windows rebuild also passed the expanded check and reports version 0.2.0/source 1f76d41/Apache-2.0 in build-info. Project notices are present in the real frozen resources. Full local source suite remains 210 passed/2 skipped in 35.96s; source wheel licensing was independently checked. No generated bundles or environment/model files are committed.
- Documented accepted licensing, source-version and JSON-provenance decisions, plus the decision against promoting unconfirmed reliability gates. Standard bundles remain classical-only and unsigned validation artifacts. Manual platform/accessibility/scaling/install and complete third-party notice gates stay open.

## 2026-10-26 — Apply owner-selected Apache-2.0 and consolidate current status

- The owner explicitly selected Apache-2.0. Added the official full license and project NOTICE, SPDX package metadata/license files and setuptools>=77 for PEP 639 support. Original VISOR code is covered; dependency/model/dataset terms remain separate.
- Desktop builder now includes project LICENSE/NOTICE as data and records them in build-info. Frozen workflow validation verifies their presence/content without claiming third-party notice completeness. Added absent/present-notice workflow regressions.
- Source wheel built in isolation: 0.2.0 metadata declares Apache-2.0 and contains both license files. Eight focused notice/version checks passed; full local suite **210 passed, 2 skipped in 35.96s**; Ruff and focused builder Mypy passed. New native licensing refresh follows.
- Pre-licensing repair run 40222252759 passed all four targets at 601bee5. Windows core: 191 passed/2 skipped/17 deselected; other targets: 189 passed/4 skipped/17 deselected. Source-based build version is now correctly 0.2.0. This confirms the portable evidence-hash repair, including non-Windows platforms.
- Replaced the accumulated status chronology with a current verification/delivery/research/gates snapshot; historical evidence remains in this log and Git. License choice is closed; complete third-party artifact notices, signing and manual platform gates remain explicit.

## 2026-10-26 — Use frozen source version in desktop build provenance

- Local build-info incorrectly used the developer environment's old installed VISOR 0.1.0 metadata while freezing 0.2.0 application source. Builder now parses the source's literal __version__ without importing/executing the app, fails clearly on invalid/missing versions, and records version_source. Packaging uses that same returned version.
- Six version regressions plus evidence/study checks passed (24 focused); focused builder Mypy passed. Full-source/native refresh follows. No registration algorithm, diagnostics or frozen policy changed.
- Full local suite: 208 passed, 2 skipped in 31.91s; Ruff and focused builder Mypy passed. Rebuild source version is 0.2.0 despite installed developer metadata remaining 0.1.0. The new native run must pass before replacing artifact links.

## 2026-10-26 — Repair platform-dependent evidence hash checks

- Native matrix 40221478271 exposed a Linux/macOS regression in the published reporting provenance assertion: original Windows CRLF file-byte hash differs from Git's LF checkout. Preserved the failed-run evidence and did not label that matrix successful.
- Added canonical parsed-JSON content hashing, explicitly scoped original-byte hashes and LF output/evidence attributes. Published JSON provenance now includes the canonical hash and a repair note; frozen definitions, every candidate/count/decision and binary compressed raw reports are unchanged. Eighteen focused checks include LF/CRLF round trips and rejection of changed content; study Mypy passed. Broader/native checks follow.
- Rebuilt local Windows picker review confirmed platform Pictures/Documents defaults, cancellation without changed inputs and normal close. Final local bundled SIFT/ORB/drop/export/project/shutdown check passed.
- Repair verification: full local 202 passed/2 skipped in 32.64s, Ruff and focused study Mypy passed. Run 40221478271 completed with Windows success and Linux/both Mac jobs failing the same single evidence-hash assertion. Fresh native validation follows the repair; no failure was hidden.

## 2026-10-25 — Use platform user folders in native file dialogs

- Corrected the application-folder starting location observed during Windows review. Qt platform locations now supply Pictures/Documents/Movies defaults; per-category successful choices persist in existing local app settings. Both image slots share the last image folder, including after restart. Project Save suggests the current project filename; exports remember successful destinations, leaving preferences unchanged after cancellation or an export error.
- Updated README to lead with the actual standalone user workflow and explicitly scope learned engines/source setup to developers. Kept standard native dialogs and documented Qt location behavior in the product review.
- Added four focused dialog-location regressions; eighteen focused dialog/input/session/overlay checks passed. Full local suite 201 passed/2 skipped in 32.28s; Ruff, focused image-widget Mypy and whitespace checks passed. Native rebuild/real picker review follows.

## 2026-10-25 — Report reserved scenes without retuning and decline gate promotion

- After publishing the selection at f85c7e0, evaluated reserved i_books/v_artisans using identical settings from that clean revision: 72 measured rows/24 warmups. First-image previews confirm books and mosaic are distinct; both negative directions retained. No runtime failures.
- v_artisans/1-5 ground-truth horizon crosses the full reference rectangle; three rows per engine remain recorded as annotation errors and excluded from truth denominators. No replacement selected. Remaining truth attempts: 27 per engine; negatives: six per engine, representing nine/two distinct pairs.
- Applying only the frozen choices rejected no additional reporting fits. SIFT still accepted v_artisans/1-4 at 9.88 px mean corner error, 343 inliers and support fraction 0.359. Both gates retained all baseline ≤3 px positives, but the predeclared independent-benefit condition was not met. Declined promotion into desktop defaults; no retuning. Published raw reporting evidence and per-attempt decisions with recomputation checks.

## 2026-10-25 — Publish development evidence before reserved reporting

- Evaluated the preregistered four development scenes from clean dec9b33: 32 pairs, two engines, three measured repetitions/one warmup, 192 measured rows and 64 warmups, no runtime/annotation errors. Kept raw data and every candidate; recomputation regressions verify summary and selection consistency.
- Fixed selection chooses SIFT ≥20 inliers and ORB ≥40, each with reference support ≥0.01 and no residual cap. Development preserves baseline ≤3 px positives while removing accepted >5 px fits; SIFT's one distinct negative acceptance is rejected. ORB also rejects one distinct ≤5 px positive. Published the exact selection and hashes before reserved-scene measurement. No desktop estimator/default changed.

## 2026-10-25 — Complete drop build matrix and add independent study analysis

- Native run 40219803747 passed Windows/macOS ARM64/macOS Intel/Linux at 7bf73d6, including copy-only Qt URL event checks, classical full workflows, lint and packaging. Windows: 165 passed/2 skipped/17 deselected; other targets: 163 passed/4 skipped/17 deselected. Refreshed download links. Local Windows build and expanded smoke check passed.
- Added a pure offline diagnostic study module with fixed 27-candidate selection, explicit 75% retention, least-restrictive exact ties, immutable baseline results, frozen reporting, input-hash/pair/configuration overlap guards and report/code hashes. Reporting retains per-attempt gate decisions. This is research tooling, not an application rejection policy.
- Twenty-two focused study/evaluation regressions and full local suite passed (193 passed, 2 skipped in 32.02s); Ruff and focused study Mypy passed. Downloaded four development sequences using ~29.6 MB bounded ranges and verified ZIP CRC and SHA256 records. First-image previews show four distinct scenes; all twelve directed cross-scene negatives are retained before evaluation. Reserved reporting images/results have not been used for selection.

## 2026-10-25 — Preregister I15 reliability study

- Selected i_autannes/i_bologna/v_adam/v_apprentices for development and reserved i_books/v_artisans for reporting using only bounded ZIP directory metadata, alphabetic order and completeness/size rules. Excluded the two original published scenes.
- Recorded the candidate grid, 75% accurate-positive retention requirement, tie-breaking order, independent reporting step and limits before reading new scene performance. No shipping geometry or acceptance policy changed. See RELIABILITY_STUDY.md.

## 2026-10-25 — Copy-only image drop contracts

- Attempted native Explorer-to-VISOR drag; helper rejected its endpoint outside the Explorer window. Recorded this as incomplete native verification, without treating it as an application failure. A resize attempt did not change dimensions and adds no scaling evidence.
- Compared the Qt drop-action contract and Microsoft's drop-effect definitions. Input handlers now force allowed Copy actions during enter/move/drop, reject move-only sources and ignore unreadable drops. Opening images must not request source removal. No actual file loss was observed or claimed.
- Seven new Qt-dispatched cases cover both roles, Shift-proposed Move, Unicode/spaced uppercase paths, source bytes, invalid/remote payloads and corrupt images. The bundled workflow check now dispatches URL drop events with explicit copy semantics. Strengthened overlay replay coverage to preserve the 12 px boundary through UI save/load.
- Fourteen focused checks and full local suite passed (182 passed, 2 skipped in 33.26s); Ruff and focused image-widget Mypy passed. Source workflow check passed all steps. A broader follow-import smoke-module type traversal was stopped without completion; it is not counted as verification. Native packaging refresh follows the commit.

## 2026-10-25 — Resume Windows review and unify overlay editors

- Confirmed final c67936c native runs on Windows/macOS ARM/Linux and the separate 33ab883 Intel Mac extension all passed core regressions, lint, packaging and bundled workflow checks. Windows: 155 passed/2 skipped/17 deselected; other targets: 153 passed/4 skipped/17 deselected. Optional CPU models: 17 passed/157 deselected at c67936c. Updated distribution links with exact artifacts.
- Resumed native Windows input after user authorization. Verified the first successful result opens Localization, a changed estimator clears the old result, and a saved project restores relative inputs, symmetric-ratio matching, MAGSAC, rainbow and 3 px overlays in a fresh executable process. Replayed analysis returned 348 good matches/339 inliers.
- Found that canvas width edits left the Parameters slider stale, parameter width edits could render with the old canvas value, and menu/button rainbow states could disagree. Unified paired controls with blocked feedback and one redraw per change; both width editors use the existing parameter range of 1–12 px. The rainbow setting can now be turned off from either control, including after project load.
- Added focused regressions covering both editing directions, maximum width, actual result/render settings, saved width and alternating menu/button toggles. Fourteen focused checks passed; full local suite 175 passed/2 skipped in 35.77s; Ruff and whitespace checks passed. Refreshed local packaging/native follow-up is recorded separately.
- Local Windows rebuild and bundled SIFT/ORB/render/export/project/shutdown checks succeeded. Native input confirmed both width controls agree when editing canvas to 12 px and Parameters to 2 px. Featureless-target analysis displayed no valid mapping, zero matches/inliers and Feature Matches, with no invented polygon. Normal close succeeded.

## 2026-10-25 — Extend native matrix to Intel Macs

- Checked GitHub's current standard runner documentation and added macos-15-intel with an Intel-only manual dispatch option to avoid repeating completed target builds unnecessarily.
- Source application code is unchanged; native Intel validation must complete before support is claimed. Replay/video refresh and optional CPU checks run at c67936c independently.

## 2026-10-25 — Stream video decoding and reject unsupported tracking engines

- Replaced eager decoded-frame accumulation with an iterable pipeline, keeping one decoded frame in processing rather than an entire clip. Preserved feature extraction reuse and per-frame algorithm results.
- Validate SIFT/ORB scope explicitly before reading, check cancellation before reference work, and release capture on every exit. Total tracking time now includes decoding; UI counts valid fits without implying independent accuracy.
- Added iterator/lazy-decode/capture-release and unsupported-engine regressions. Twenty focused video/job checks passed; focused video Mypy and Ruff passed. Native/full follow-up evidence is recorded separately.

## 2026-10-25 — Source verification after replay and review fixes

- Full local suite: 169 passed, 2 skipped in 32.63s. Ruff and focused exporting/matcher Mypy passed. Follow-up core suite also exercised isolated Qt preferences; native refresh follows the commit.
- Added an autouse fixture that isolates the application's QSettings only when the UI module is already imported, keeping scientific-only tests independent of Qt imports and preventing test runs from changing the developer's native layout.

## 2026-10-25 — Native Windows interaction and project replay correctness

- Rebuilt the actual standalone Windows executable and exercised native pickers (Ctrl+1/Ctrl+2), F5 SIFT/ORB, match rendering, PNG export, engine-change invalidation and Ctrl+Q. Control names were exposed through UI Automation. Kept the native review scope separate from offscreen CI and full accessibility/install gates.
- Fixed issues observed during review: first result visibility, accepted/no-fit status, stale retry results, clipped engine choices and unwrapped/rich-text detail values.
- Added project format 2 with matching strategy, robust method and overlay replay, relative image references and version-1 migration. Missing engines now produce an explicit message rather than a substitute engine. Undecodable referenced images remain visible as input recovery states.
- Corrected an additional nondefault symmetric-matcher double count; cross-check threshold is null and conflicting strategy flags fail clearly. Focused session/matching/UI checks passed; final full/native checks are recorded separately.
- Full suite before these follow-ups and including raw evidence consistency checks: 161 passed, 2 skipped in 51.41s.

## 2026-10-25 — Native release evidence and raw dataset reporting

- Three-platform run 40213846401 passed at fe5ec16. Windows core: 131 passed, 2 skipped, 17 model tests deselected; macOS/Linux: 129 passed, 4 skipped, 17 deselected. All lint, package and bundled workflow checks passed. Recorded new artifact links and retained the unsigned/manual-validation limits.
- Evaluator b2c7f0b core follow-up: 142 passed, 2 skipped, 17 deselected in 12.66s. Evaluated synthetic fixtures (18 measured attempts) and a preselected bounded HPatches sample (72 attempts) from a clean evaluator checkout. Downloaded only selected archive ranges (~17.7 MB), kept images outside Git, and published full raw compressed reports with manifests/hashes.
- HPatches reporting sample consists of i_ajuntament/v_abstract (five positive pairs each) and two visually inspected cross-scene negatives. SIFT: 21/30 positive fits, 9/30 within 3 px mean corner error; ORB: 30/30 fits, 12/30 within 3 px. Both rejected six repeated negative attempts. No runtime/annotation errors; scene/sample size limits prohibit broad ranking or reliability claims.
- Added I15 from the observed wrong-but-valid fits, retaining this reporting set unchanged and requiring separate development scenes for policy tuning. Added a fact-based third-party notice inventory and explicit unresolved owner/release decisions.

## 2026-10-25 — I07 reproducible runner and I08 dataset preparation

- Added JSON manifest validation, relative-path synthetic/HPatches preparation and a developer evaluation CLI. Records input/truth hashes, actual matrices, source/dirty state, versions/settings/device, fresh-engine timing scope and every warmup/measured attempt.
- Summaries preserve failed fits and runtime failures, distinguish annotation errors, report corner mean/RMSE/max separately from fit residual and count false acceptance only on labeled negative pairs. Prevented mixing development/held-out splits and overwriting input files.
- Added eleven focused tests for metrics, missing inputs, denominator handling, invalid truth, split separation, portable reports, HPatches missing files and CLI output protection. All passed; targeted evaluator/data Mypy passed. Synthetic trial: 18 measured attempts with no runtime errors; raw publication follows after the evaluator commit.
- Native desktop matrix at fe5ec16 runs independently of these new developer evaluation modules.

## 2026-10-25 — I11 measured fit diagnostics and correspondence inspection

- Added typed valid-fit diagnostics for source/target support hulls, inlier residual median/p95/maximum, projected area and its target-area ratio. Exports/UI define them as fit evidence, not detection confidence or truth accuracy.
- Target keypoint inspection now lists accepted correspondence membership, reference index and available distance/score. Unmatched points are identified explicitly.
- Tests check area conventions, linear residual quantiles, exclusion of outliers, missing target size, exports and UI membership inspection. Diagnostic/geometry/golden set: 20 passed. Validator focused Mypy and Ruff passed.
- Pre-diagnostic source ac28f47 full suite: 144 passed, 2 skipped in 66.04s. Added hidden-import discovery for registry-loaded wrappers before the next native bundle matrix.

## 2026-10-25 — I09 shared factory and capability discovery

- Unified all nine built-in factories with typed configured/pair engine protocols and dataclass configuration metadata. Pipeline construction now uses the registry; UI selector and availability dialog share its probes/reasons.
- Distinguish installed dependencies/cache presence from weights/device verified at use. Probes neither import Torch nor download models. Added readable availability text and tooltips for available engines as well as missing dependencies.
- Corrected AKAZE/BRISK advertised availability versus pipeline rejection and removed their inaccurate wheel-version docstring. Both real classical paths passed known-pair checks on this environment; SIFT/ORB goldens were retained.
- Verification: 27 focused registry/reporting/classical checks passed, followed by 25 capability/reporting/UI checks. Focused registry/pipeline Mypy passed. Broader source/native evidence is tracked separately.

## 2026-10-25 — I10 stale-job protection and responsive close

- Added a Qt-independent revision/ticket controller and main-thread QObject signal relay for all seven analysis worker types. Superseded/cancelled results and errors are ignored, terminal delivery is single-use, and finishing an old ticket cannot release a newer job.
- Algorithm/input changes clear old analysis/details and request cooperative cancellation. Analysis menus cannot start competing work during installation or shutdown.
- Removed blocking QThread.wait from closeEvent. Close now requests cancellation and defers window destruction via the event loop until workers finish; source installation is allowed to finish with visible status. Finished workers/relays are deleted safely.
- Added calibration cancellation boundaries and controlled worker regressions for input/config change, cancellation, competing work, install lifetime and responsive close. Focused lifecycle/UI/calibration checks passed; subsequent core/native verification is recorded separately.
- Optional CPU GitHub run 40212401735 passed 17 checks (113 deselected) in 53.06s at 7214553. That evidence is separate from the newer job changes.

## 2026-10-25 — I05 pinned XFeat API and optional runtime separation

- Confirmed the upstream repository has no setup.py and exposes modules.xfeat.XFeat.detectAndCompute rather than xfeat.Extractor. Pinned XFeat source/weights to e92685f and LightGlue setup to eb42fee.
- Added explicit developer setup, platform cache and SHA-256 manifest checks. Analysis runs offline against the installed cache. Adapter initializes the pinned inference state on the requested device, rejects generic modules namespace collisions and uses weights-only loading. Kept downloaded code/weights outside the repository.
- Repaired source setup/status commands, separated optional-model markers and added a manually triggered CPU inference workflow. Core desktop jobs exclude model tests; packaged application installation guards remain.
- CPU real-model evidence: 512 identity matches; on the controlled warp, 348 mutual matches / 328 inliers and maximum corner error 2.29 px. Added identity/known-transform optional regressions plus offline cache-integrity/reuse/namespace/mutual-matching tests.
- Full local suite: 128 passed, 2 skipped in 54.20s. Focused new runtime checks and Ruff passed; targeted Mypy passed for runtime/setup modules. New CI execution and device/platform expansion follow separately.

## 2026-10-25 — I04/I06 measured pair results and estimator provenance

- Added typed PairMatchResult and one shared LightGlue extraction/matching loop. Timed stages include completed device operations and CPU conversion; initialization and visualization are separate from matching. Preserved the legacy tuple adapter for existing callers.
- Kept actual LightGlue assignment scores, left unmeasured descriptor distances/candidate counts null, and exposed unavailable keypoint metadata. XFeat matching now uses mutual L2 nearest neighbors with measured distances; its extraction API repair follows under I05.
- Learned results now honor selected RANSAC/MAGSAC/LMEDS. Added method/model/threshold provenance, explicitly retaining the legacy adaptive RANSAC sequence and recording that LMEDS does not use a pixel threshold. Classical golden values were unchanged.
- Added analysis schema 2, extended CSV/HTML and UI reporting, disabled inapplicable classical matcher controls for learned choices, and documented migration/timing scope in RESULT_CONTRACT.md.
- Verification: 52 focused tests passed; full local suite 120 passed, 2 skipped in 52.34s. Ruff passed; focused Mypy passed on models/pair module. Dedicated GPU profiling, XFeat real-model verification and new native bundles remain pending.

## 2026-10-20 — I14 professional product standard and workspace refinement

- Recorded the user's professional-product requirement as a durable design, scientific reporting and release review standard; linked it from development rules and the improvement ledger.
- Reviewed the existing interface through source and offscreen Windows-font renders. Moved inputs to a vertical scrollable sidebar and the console to a hideable Diagnostics dock, preserving space for result inspection. Kept Run/Cancel in the main action row and comparison/benchmark beside inputs.
- Fixed the unreachable recent-pair toggle; shortened unavailable engine labels and moved guidance to tooltips; added accessible control names, explicit focus/disabled styling and consistent dark control surfaces. Parameters scroll; optional engines no longer display a preceding classical form. Escaped filenames in overview rich text.
- Reviewed empty layouts at 1280×820 and 1040×680, loaded inputs/expanded history and parameter layouts. Ruff and diff whitespace checks passed. No automated tests or native package rebuild was run in this follow-up; existing three-platform package evidence applies to ba7e05d.
- Native DPI, keyboard/screen-reader and complete workflow reviews remain pending. Generated review images are local ignored build artifacts.

## 2026-10-19 — Research and improvement planning

- Audited current v0.2.0 source, geometry/matching/learned paths, UI orchestration, batch evaluation, packaging and existing documentation.
- Consulted upstream OpenCV USAC, LightGlue, XFeat source/API, Glue Factory evaluation, HPatches, Qt thread lifecycle and Setuptools build documentation.
- Added dated research review, prioritized improvement ledger and restored repository development rules.
- Reproduced a wheel backend import failure and baseline Ruff findings; prior handoff/status snapshots are now explicitly historical.

## 2026-10-19 — I01 package construction

- Replaced invalid `setuptools.backends.legacy:build` backend with documented `setuptools.build_meta`.
- Analysis/project export version now follows `visor.__version__` instead of stale v0.1.0.
- Wheel build passed without installing into or replacing the active environment. Inspected archive: UI, icon, and launcher metadata present.
- Original full-suite baseline: 90 passed, 2 skipped. No generated wheel/build directory is committed.
- User added standalone Windows/macOS/Linux distribution requirement; tracked as I13 with native OS validation gates.

## 2026-10-19 — I02/I03 trustworthy geometry and metric naming

- Added common transform validator for all robust estimators; removed false-success centroid translation and silent MAGSAC/LMEDS fallback.
- Checks include numerical validity, mask/support consistency, horizon crossing, convex area and real polygon intersection with target. Center is projected through the transform.
- Preserved successful SIFT/ORB golden counts. Added adversarial solver failure, off-image projection, horizon, collinearity, invalid-mask and perspective-center regressions.
- Batch localization accuracy is unavailable without ground truth; added separately named reprojection residual and updated UI field.
- Focused verification: 34 passed in 5.16s (geometry validation, classical goldens, robust estimators, batch and exports).

## 2026-10-19 — I13 standalone desktop build path

- Added a shared native-host builder and versioned Windows ZIP/setup, macOS app/DMG, Linux portable/Debian packaging branches. Updated the Windows wrapper to use it.
- Added manual GitHub native runner matrix with artifact uploads and bundled offline workflow checks; no automatic public release.
- Added `--smoke-check` diagnostics including bootstrap import failure capture; checks UI input, both classical engines, rendering, JSON/CSV exports, project session and shutdown.
- Found a real Windows bundle startup failure: PyInstaller collected an incompatible Poppler ICU DLL from developer PATH. Isolated the native build PATH; rebuilt bundle now passes the workflow check.
- Packaged UI hides developer dependency installation controls. Standard desktop builds explicitly exclude optional Torch/model packages; packaged learned support remains a separate improvement gate.
- Corrected pre-existing lint issues encountered in touched code; updated a brittle installer string test for the new versioned recipe. Targeted follow-up: 28 passed in 4.98s. Full-suite validation and platform jobs follow.

## 2026-10-19 — Native platform validation and core CI

- Native GitHub run 39300439636 at `303ba33` passed on Windows x64, macOS ARM64 and Ubuntu x64, including bundle workflow checks and installer/package artifacts.
- Local full suite passed: 102 tests, 2 skips in 36.78s. Added two frozen-runtime regressions, both passed. Ruff passed; targeted new-module Mypy passed (3 files, imported modules skipped).
- Added source revision to future build-info reports, an explicit optional-runtime guard for the previously unguarded real-model test, and core test/lint steps in the native build workflow. This allows validating the ordinary desktop build without installing learned dependencies.
- Public release, signing/notarization, clean-desktop installation/uninstallation and packaged learned-runtime support remain explicitly unverified.

## 2026-10-19 — Correct native regression expectations

- Follow-up local suite: 104 passed, 2 skipped in 36.41s.
- Adding the core suite to native runners exposed nonportable Windows snapshot counts (run 39301243754). Linux ORB inliers: 744; macOS ARM ORB: 580; Windows recorded baseline: 731. macOS SIFT reference count: 842 vs recorded Windows 843.
- Kept the original golden values unchanged and scoped exact snapshots to their recorded Windows/OpenCV 4.11 environment. Added independent known-transform accuracy contracts on every platform (maximum corner error under 3 px on the textured mild-warp fixture), inlier consistency, and platform-local default-configuration equivalence.
- Focused validation: 8 passed in 4.23s; Ruff passed. This replaces a universal-count assumption with mathematical accuracy checks, not a new performance claim.

## 2026-10-19 — Final native validation at ba7e05d

- GitHub run 39301662952 succeeded on Windows x64, macOS ARM64 and Ubuntu x64.
- Windows source core tests: 91 passed, 17 skipped. macOS and Linux source core tests: 89 passed, 19 skipped. Lint passed on all three.
- All native packages built and bundled workflow checks passed. Artifacts contain Windows setup/portable ZIP, macOS app/DMG and Linux Debian/portable packages, build provenance and smoke reports.
- Canonical implementation status now summarizes current evidence and preserves the superseded Phase 1 snapshot separately. Desktop guide links the validation artifacts and states signing, manual installation and optional-engine limits.
- Work is pushed on main; remaining research-driven tasks stay open in the improvement ledger. No signed or production release has been represented as complete.

## M0 — Repository foundation

- Added project plan, architecture, status, development rules, and ignore patterns.
- Initialized an isolated Git repository on `main`; configured and pushed `origin`.
- Verified the remote had no existing branch refs before the first push.

## M1 — Desktop shell and image input

- Added setuptools packaging metadata and `python -m visor` entry point.
- Added a restrained dark PySide6 main window and image input widgets.
- Each input supports a native file picker and drag-and-drop of PNG, JPEG, BMP, TIFF, and WebP.
- Image previews show filename and pixel dimensions; unreadable files produce visible feedback and a log entry.
- Analysis actions are not exposed until the underlying analysis pipeline exists.

## M2–M5 — Classical registration pipeline

- Added typed result records and separate SIFT, ORB, matching, geometry, and pipeline modules.
- SIFT descriptors use brute-force L2 matching; ORB descriptors use Hamming or Hamming2 according to `WTA_K`. Both paths use KNN candidates and ratio filtering.
- RANSAC estimates a planar homography, inlier mask, projected reference corners, center, and mean inlier reprojection error. Numerically degenerate transforms and insufficient matches are reported as failures.
- Added worker-thread analysis, match visualization, localized target polygon, optional rectification, and measured timing/engine details in the UI.

## M6 — Comparison, benchmark, and exports

- Added `compare_engines` pipeline function that decodes images once and runs both engines.
- Added `ComparisonWorker` and comparison display in the main window.
- Added `benchmark.run_benchmark` with nine deterministic synthetic transformations (baseline, rotation+scale, perspective, brightness, contrast, blur, noise, crop, resolution reduction) and ground-truth corner RMSE.
- Added `BenchmarkWorker` and a results dialog with a sortable table.
- Added cancellation via `threading.Event` checked at safe pipeline boundaries.
- Added `exporting` module: JSON analysis documents, CSV metrics, comparison CSV, benchmark CSV, PNG/JPEG visualization, and `.visor` project session save/load.
- Added PyInstaller `build_windows.ps1` script and multi-resolution `.ico` generator.
- Added 16 automated tests covering engines, matching, geometry edge cases, pipeline integration, exports, and benchmark.

## M7 — Algorithm-specific details panel

- Added `AnalysisDetailsPanel` widget with tab and tree view modes.
- SIFT tab shows: configuration (max features, octave layers, contrast threshold, edge threshold, sigma), keypoint statistics (count, mean size, mean response, mean angle, octave distribution), descriptor info (128-D FLOAT32, L2, memory).
- ORB tab shows: configuration (all 9 parameters), keypoint statistics, descriptor info (32-byte BINARY, Hamming/Hamming2, memory).
- Geometry tab shows: homography status, inlier/outlier counts, inlier ratio, mean reprojection error, projected corners, center.
- Performance tab shows per-stage timing.
- Keypoint inspection: clicking the Localization view appends the nearest target keypoint's full record to a Selected Keypoints tab.
- Comparison mode calls `populate_comparison` to show both engines' structured results.

## M8 — Toolbar, packaging, and release

- Added `QToolBar` with SVG icon actions: Open Reference, Open Target, Run, Compare, Benchmark, Cancel, Export, Fit View.
- Added `assets/icons/` to `pyproject.toml` package data and PyInstaller `--add-data`.
- Fixed `_icon()` to resolve `visor/assets/icons/` correctly under PyInstaller `_MEIPASS`.
- Built and verified `dist/VISOR/VISOR.exe` one-folder distribution; all 9 SVG icons confirmed present in `_internal/visor/assets/icons/`.
- Updated README with full feature list, keyboard shortcuts, architecture overview, export table, and troubleshooting guide.
- Updated ARCHITECTURE.md with full module map, data flow diagram, threading model, and extension model.
- Tagged v0.1.0.

## Phase 1 — Install flow fix and repo restoration (v0.2.0)

- Restored `pyproject.toml` (was missing from disk; only egg-info remained).
- Restored `README.md` with accurate install and learned-engine instructions.
- Added `.gitignore` and initialized the Git repository.
- Added `InstallWorker` QThread — runs pip in a background thread with live line-by-line output to the engine console so the UI never freezes during install.
- Fixed `_install_learned_engines()`:
  - Now targets `sys.executable` (the running interpreter) instead of creating/overwriting a `.venv`.
  - Corrected XFeat package name from `xfeat` (does not exist on PyPI) to `git+https://github.com/verlab/accelerated_features.git#subdirectory=.`.
  - LightGlue install command unchanged (`git+https://github.com/cvg/LightGlue.git`).
- Added `_refresh_engine_selector()` — re-evaluates engine availability after install and updates the combo box items live.
- Added soft `importlib.reload()` of learned engine modules after install for same-session activation.
- Fixed `XFeatEngine.extract_and_match()` — replaced `sklearn.NearestNeighbors` with pure-numpy L2 nearest-neighbour (no sklearn dependency).
- Updated golden regression baseline for `opencv-contrib-python 4.11` (ORB inliers: 760 → 731).
- Loosened frozen test ratio tolerance from 1e-4 to 5e-3 to accommodate minor floating-point differences across opencv patch versions.
- Verified: **90 passed, 2 skipped** with system Python 3.11.9.
