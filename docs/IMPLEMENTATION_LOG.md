# Implementation Log

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

