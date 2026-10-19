# VISOR product quality standard

Established 2026-10-20 in response to the user's requirement for a professional desktop application. This standard applies to implementation, documentation and release review. Progress is tracked as I14 in [IMPROVEMENT_PLAN.md](IMPROVEMENT_PLAN.md).

## Product purpose

VISOR is a desktop workspace for inspecting feature correspondences and planar image registration. The primary workflow is: choose or drop a reference and target, select an available engine, run, inspect the evidence, then save or export. Interface space and terminology should serve that workflow.

## Design and interaction requirements

- Give the result canvas the largest useful area. Keep image inputs identifiable and diagnostics available in a separate dock. Panels must resize or scroll without obscuring essential controls.
- Use restrained surfaces, consistent spacing, platform fonts and one primary action color. Color has a defined purpose: selection, interaction, error, or image-overlay semantics. Avoid decorative gradients, glow, oversized marketing headings and animation that delays work.
- Keep engine names short. Explain dependency or device limitations through availability details and tooltips. End-user distributions must not instruct users to run Python or pip.
- Retain native file dialogs, predictable menus, conventional shortcuts and persistent dock layouts. Every icon-only action needs an accessible name and tooltip; every editable control needs a label. Keyboard focus must be visible.
- Provide drag-and-drop and file-picker paths for both images. Identify each role, show filename and pixel dimensions, preserve aspect ratio, and explain unreadable inputs with a recovery action.
- Show parameters only for the selected engine. Controls must describe their units and effective behavior. Unsupported settings must not look active or quietly take effect elsewhere.
- Make idle, running, cancellation requested, cancelled, failed and completed states distinguishable in text. Processing must remain responsive; messages must identify what happened and what the user can do next.
- Preserve the user's inputs and configuration after recoverable failures. Keep detailed diagnostics discoverable; expose errors without requiring the user to find a hidden log.

## Scientific and engineering requirements

- Display measured quantities with units and definitions. Separate matched points, inliers, fit residual and accuracy against independent ground truth.
- Never invent confidence scores, stage timings or success rates. An unavailable metric must be labeled unavailable. A successful fit alone does not establish correct localization.
- Show the executed engine, matcher, estimator, effective settings and runtime provenance in results and exports. Unsupported engines must not silently route to a different algorithm.
- Keep optional model downloads and dependencies explicit. Core image registration and project/export workflows must work offline in standard desktop bundles.
- Treat documentation, reproducibility, dependency notices and installation behavior as product features. Mark unverified platform behavior as pending; configuration files alone are not evidence of a working release.

## Current interface review

Review method: source inspection and local Qt offscreen renders using the Windows Segoe UI font at 1280 × 820 and 1040 × 680. These renders assess layout; they do not establish native screen-reader behavior, monitor scaling or installation quality.

| Finding | Change / remaining gate |
|---|---|
| Side-by-side input cards and permanent console consumed most of the workspace | Stack inputs in a narrow, scrollable sidebar; move console into a hideable Diagnostics dock; keep result area flexible |
| Dependency instructions made engine labels unnecessarily long | Compact unavailable labels with explanatory tooltips; retain disabled unavailable choices |
| Recent-pair disclosure was inside its own hidden panel | Keep the disclosure visible; show the history and save/clear actions when expanded |
| Inconsistent light controls interrupted the dark workspace | Apply consistent list, button, spinbox, slider and scrollbar surfaces, with explicit focus and disabled states |
| Input picker and clear actions lacked role-specific accessible names | Add reference/target names; add a labeled engine selector and thickness control |
| Optional engine selection could retain the preceding classical parameter form | Hide SIFT/ORB forms for other engines; complete capability-specific forms under I09 |
| Filename text was interpolated into rich-text overview markup | Escape filenames before displaying them |

## Release review gates

Track evidence for each target OS and architecture. Do not mark these complete based only on an offscreen render or an automated bundle check.

1. Review empty, loaded, successful, failed, busy and cancelled workflows with real image pairs; confirm that result overlays remain legible and exports match the displayed result.
2. Review the minimum window size and 100%, 150% and 200% monitor scaling, including long filenames, expanded history and parameter forms. Require usable controls without clipped action labels or inaccessible content.
3. Complete the main workflow by keyboard. Check focus order, shortcuts, control names, and screen-reader announcements on each supported desktop platform. Verify readable text/disabled states and do not encode a result solely by color.
4. Check cancellation, input/configuration changes during work, repeated runs, error recovery and shutdown. Cover stale results and thread lifetime under I10.
5. Install, launch offline, open/save/export and uninstall the actual distribution on a clean desktop. Review dependency/model notices and signing/notarization under I12/I13.

Acceptance means useful, reliable workflows with recorded evidence. A visual refresh alone cannot close the remaining correctness and release tasks.
