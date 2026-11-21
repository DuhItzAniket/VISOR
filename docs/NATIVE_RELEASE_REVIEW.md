# Native desktop release review

Use this procedure on a disposable desktop or test machine. Record a separate result for Windows x64, Linux x64, macOS Apple Silicon and macOS Intel. Repeat against the final release bytes after signing or repackaging. Hosted installer checks and software-rendered screenshots are recorded separately in [Implementation Status](IMPLEMENTATION_STATUS.md).

Before starting, record the package filename, SHA-256, source revision, OS and build, CPU architecture, desktop environment, display resolution, scaling and assistive technology version. Use the platform's normal install and launch paths with a fresh user profile. Fetch the package and [reference](../tests/data/golden_reference.png) and [target](../tests/data/golden_target.png) files before disconnecting the test desktop. Put the images in a writable test folder. For recovery, create an empty file named `unreadable.png`. Use only these test files when saving or exporting.

| Check | Procedure and expected observation |
|---|---|
| Install and first launch | Use the Windows setup wizard and Start menu, Finder and the DMG's Applications link, or the Linux package and desktop menu. Record trust prompts verbatim and whether the application starts offline. Record any prerequisite the normal installation asks for. |
| Shell drop and recovery | Drag the two images from Explorer, Finder or the Linux file manager into their respective inputs. Confirm both previews, filenames and dimensions appear, and confirm the originals are still on disk. Replace one with the unreadable image. The error should name the failed input and leave the good pair available. |
| Keyboard only | Use the File menu or the shortcuts displayed by the installed app to select both roles, then run SIFT and reach the result, parameters and export controls. Track Tab and Shift+Tab order for the main workflow. Record inaccessible controls, focus traps, or ambiguous labels. |
| Screen reader | Repeat the keyboard path with Narrator, VoiceOver, or Orca as appropriate. Record the actual announcements for image roles, focus, unavailable controls, analysis status, completion and errors. Compare the announcement with the visible state. |
| Display scaling | At 100%, 150% and 200%, or the closest native settings the desktop exposes, shrink the window to its minimum size. Test long filenames, expanded history, parameter editing and zoom controls. Record which scale was used and whether essential actions remain reachable. |
| Save, open and export offline | Save a project with images beside it, export a result, close and reopen VISOR, then open the saved project and run again. Confirm selections and settings restore, the result can be rerun and the export opens. Cancel a picker and confirm the selections persist. |
| Remove | Use the registered uninstaller, remove the copied Mac app, or purge the Linux package. Confirm the launcher and application files are gone and user-created images, projects and exports survive. Record whether platform settings remain in the test profile. |

Mark each row Pass, Fail, or Not run. For failures, include the action, observed result and a screenshot or announcement transcript where appropriate. Record whether networking was disconnected during the install and workflow, or only after installation. Keep the test result attached to the exact package checksum.
