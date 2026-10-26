"""Stage both images before a project or history pair can replace the workspace."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from visor.exporting import ProjectSession
from visor.ui.image_loader import DecodedPreview, PreviewLoader, PreviewRequest


@dataclass(frozen=True)
class ProjectRequest:
    session: ProjectSession
    document: Path | None = None


@dataclass(frozen=True)
class LoadedProject:
    request: ProjectRequest
    reference: DecodedPreview
    target: DecodedPreview


class ProjectLoader(QObject):
    """Reuse one bounded decoder; no visible selection changes during staging."""

    completed = Signal(object)
    failed = Signal(object, str)
    busy_changed = Signal(bool)
    idle = Signal()

    def __init__(self, parent: QObject) -> None:
        super().__init__(parent)
        self._decoder = PreviewLoader(self)
        self._request: ProjectRequest | None = None
        self._reference: DecodedPreview | None = None
        self._decoder.completed.connect(self._decoded)
        self._decoder.failed.connect(self._failed)
        self._decoder.busy_changed.connect(self.busy_changed.emit)
        self._decoder.idle.connect(self.idle.emit)

    @property
    def busy(self) -> bool:
        return self._decoder.busy

    @property
    def cancellable(self) -> bool:
        return self._request is not None

    def request(self, request: ProjectRequest) -> bool:
        self._request = request
        self._reference = None
        accepted = self._decoder.request(PreviewRequest(Path(request.session.reference_path)))
        if not accepted:
            self._request = None
        return accepted

    def cancel(self) -> None:
        self._request = None
        self._reference = None
        self._decoder.cancel()

    def shutdown(self) -> None:
        self._request = None
        self._reference = None
        self._decoder.shutdown()

    def _decoded(self, preview: DecodedPreview) -> None:
        request = self._request
        if request is None:
            return
        if self._reference is None:
            self._reference = preview
            self._decoder.request(PreviewRequest(Path(request.session.target_path)))
            return
        result = LoadedProject(request, self._reference, preview)
        self._request = None
        self._reference = None
        self.completed.emit(result)

    def _failed(self, preview: PreviewRequest, message: str) -> None:
        request = self._request
        if request is None:
            return
        role = "reference" if self._reference is None else "target"
        self._request = None
        self._reference = None
        self.failed.emit(request, f"Could not decode {role} image {preview.path.name}. {message}")
