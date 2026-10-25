# Windows desktop review — 2026-10-25

## Scope and environment

Reviewed the actual one-folder `dist/VISOR/VISOR.exe` through native Windows input, shell file dialogs, screenshots and UI Automation. The reviewed executable was rebuilt locally from b2c7f0b's desktop code; no separate Python interpreter was launched to operate it. This is a local desktop review, separate from native CI's offscreen bundled checks.

## Observed workflow

| Step | Observation |
|---|---|
| Launch | Main window opened, with recognizable input, canvas and details areas |
| Accessible names | Engine selector, reference/target pickers, removal actions, line-thickness slider and Diagnostics log exposed meaningful names |
| Reference input | Ctrl+1 opened the native picker; selecting the checked-in reference loaded filename, 560×420 dimensions and preview |
| Target input | Ctrl+2 loaded the target; Run became available when both inputs were present |
| SIFT run | F5 ran analysis and returned 843/982 keypoints, 395 matches and 356 inliers on the recorded fixture |
| Rendering/export | Feature Matches rendered; native Save dialog exported a 378,330-byte PNG to an ignored local build path |
| Engine change | Keyboard selection of ORB cleared the previous details/result; learned choices were visibly disabled in the standard bundle |
| ORB run | F5 returned 1,490/1,486 keypoints, 846 matches and 731 inliers, consistent with the Windows classical baseline |
| Close | Ctrl+Q closed the review session normally |

The native dialog helper exposed a stale focused-element description while screenshots and filename values showed the actual filename field. Input was confirmed from the visible field and resulting value; this is not evidence of complete screen-reader behavior.

## Issues found and source follow-up

- Initial completion stayed on Overview instead of showing an image result. Source now opens Localization on a valid first fit, or Matches on a failed first fit, while preserving an already-selected result view on later runs.
- Completion/status text did not clearly distinguish an accepted fit from no valid mapping. Source now states that distinction and explains in Overview that fit validity is not independent accuracy.
- Engine popup labels could be clipped; its view now has more room while the main selector remains compact.
- Detailed values needed wrapping and plain-text treatment. Source now wraps rows/values and makes values selectable without interpreting filenames as markup.
- Reopening a session did not restore every matching/estimator/overlay control. Project format 2 now preserves those choices, supports relative image references and reads version 1. Unavailable engines are reported rather than silently substituted.
- Repeated analysis now clears the previous primary result before work, so a failed retry does not retain a previous success as the current analysis.

These follow-up changes have focused source regressions and require the final refreshed bundle evidence recorded in IMPLEMENTATION_STATUS.md. This document does not claim the original reviewed executable already contained the follow-ups.

## Resumed review of refreshed application

The c67936c application code was reviewed again after the user resumed Computer Use. Native Ctrl+1/Ctrl+2 pickers and F5 produced the same SIFT fixture counts and opened Localization automatically. Changing to MAGSAC cleared the previous result and asked for another run.

Ctrl+S saved a format-2 project with symmetric-ratio matching, MAGSAC, rainbow colors, 3 px lines and relative image paths. After normal Ctrl+Q close and a fresh executable launch, Ctrl+O restored both images and all those controls; F5 returned 348 matches/339 inliers and opened Localization. This confirms replay behavior in the actual bundle, separately from the automated project tests.

The review also found that editing the canvas width left the Parameters width stale. Source follow-up synchronizes both directions before one render, uses a shared 1–12 px range and keeps rainbow menu/button state consistent. Focused source regressions cover actual rendered/result settings and switching rainbow off from either editor.

After rebuilding the standalone executable with that fix, native review confirmed that setting the canvas slider to 12 updated both editors to 12, and setting the Parameters slider to 2 updated both to 2. A featureless target then produced 843/0 keypoints, zero matches/inliers, explicit **no valid mapping** status and the Feature Matches view. No localization polygon was invented. Ctrl+Q closed normally. This follow-up executable contains the overlay fix on top of 33ab883; the preceding CI artifacts still identify their recorded revisions.

## Remaining native gates

An actual Explorer-to-VISOR drag was attempted with the fixture directory open. The automation helper rejected the destination outside Explorer's bounds before completing the drag. This is a helper boundary, not evidence of a VISOR failure or a successful native file drop. No source file was moved or deleted. Qt-dispatched drag/drop regressions and the bundled workflow check now verify copy semantics separately; physical shell dragging remains pending. A helper-driven window resize did not change the observed dimensions, so it adds no minimum-size or scaling evidence.

Install/uninstall on clean desktops, monitor changes and 150%/200% scaling, Narrator/other screen readers, full mouse/keyboard-only paths, real drag-and-drop from Explorer, and native macOS/Linux interaction remain separate gates. No operating-system accessibility or security settings were changed during this review.
