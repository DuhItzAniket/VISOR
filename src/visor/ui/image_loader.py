"""Bounded background image preview decoding; QPixmap stays on the UI thread."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import Event

from PySide6.QtCore import QObject, QSize, Qt, QThread, Signal
from PySide6.QtGui import QImage, QImageIOHandler, QImageReader

from visor.jobs import JobController, JobTicket
from visor.ui.job_relay import JobRelay

PREVIEW_LIMIT = QSize(1024, 1024)


class PreviewCancelled(Exception):
    """Cancellation observed before or after an indivisible native codec call."""


@dataclass(frozen=True)
class PreviewRequest:
    path: Path
    preserve_previous: bool = True


@dataclass(frozen=True)
class DecodedPreview:
    request: PreviewRequest
    image: QImage
    original_size: QSize


def decode_preview(request: PreviewRequest, cancellation: Event) -> DecodedPreview:
    def check() -> None:
        if cancellation.is_set():
            raise PreviewCancelled()

    check()
    request = PreviewRequest(request.path.resolve(), request.preserve_previous)
    reader = QImageReader(str(request.path))
    reader.setAutoTransform(True)
    original_size = reader.size()
    oriented_size = QSize(original_size)
    if reader.transformation() & QImageIOHandler.Transformation.TransformationRotate90:
        oriented_size.transpose()
    if original_size.isValid() and (original_size.width() > PREVIEW_LIMIT.width()
                                    or original_size.height() > PREVIEW_LIMIT.height()):
        reader.setScaledSize(original_size.scaled(PREVIEW_LIMIT, Qt.AspectRatioMode.KeepAspectRatio))
    check()
    image = reader.read()
    check()
    if image.isNull():
        raise ValueError("Could not read this image.")
    if not oriented_size.isValid():
        oriented_size = image.size()
    # Some handlers allocate the full image even with a requested decode size.
    # That allocation stays off the UI thread; retained memory is bounded here.
    if image.width() > PREVIEW_LIMIT.width() or image.height() > PREVIEW_LIMIT.height():
        image = image.scaled(PREVIEW_LIMIT, Qt.AspectRatioMode.KeepAspectRatio,
                             Qt.TransformationMode.SmoothTransformation)
    check()
    return DecodedPreview(request, image, oriented_size)


class PreviewWorker(QThread):
    completed = Signal(object)
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, request: PreviewRequest, cancellation: Event) -> None:
        super().__init__()
        self.request, self.cancellation = request, cancellation

    def run(self) -> None:
        try:
            self.completed.emit(decode_preview(self.request, self.cancellation))
        except PreviewCancelled:
            self.cancelled.emit()
        except Exception as exc:  # noqa: BLE001 — deliver codec failures on the UI thread
            self.failed.emit(str(exc))


class PreviewLoader(QObject):
    """One decoder and one replaceable pending request per image slot."""

    completed = Signal(object)
    failed = Signal(object, str)
    busy_changed = Signal(bool)
    idle = Signal()

    def __init__(self, parent: QObject, *, worker_factory=PreviewWorker) -> None:
        super().__init__(parent)
        self._factory = worker_factory
        self._jobs = JobController()
        self._worker: PreviewWorker | None = None
        self._pending: PreviewRequest | None = None
        self._busy = False

    @property
    def busy(self) -> bool:
        return self._worker is not None or self._pending is not None

    def request(self, request: PreviewRequest) -> bool:
        if self._jobs.closing:
            return False
        self._jobs.invalidate()
        self._pending = request
        self._start_next()
        self._publish_state()
        return True

    def cancel(self) -> None:
        self._jobs.invalidate()
        self._pending = None
        self._publish_state()

    def shutdown(self) -> None:
        self._jobs.shutdown()
        self.cancel()

    def _start_next(self) -> None:
        if self._worker is not None or self._pending is None or self._jobs.closing:
            return
        request, self._pending = self._pending, None
        ticket = self._jobs.begin()
        worker = self._factory(request, ticket.cancellation)
        self._worker = worker
        relay = JobRelay(self._jobs, ticket, self.completed.emit,
                         lambda message: self.failed.emit(request, message), lambda: None,
                         lambda: self._finished(worker, ticket), self)
        worker.completed.connect(relay.success)
        worker.failed.connect(relay.failure)
        worker.cancelled.connect(relay.cancelled)
        worker.finished.connect(relay.finished)
        worker.start()

    def _finished(self, worker: PreviewWorker, ticket: JobTicket) -> None:
        self._jobs.finish(ticket)
        self._worker = None
        worker.deleteLater()
        self._start_next()
        self._publish_state()

    def _publish_state(self) -> None:
        busy = self.busy
        if busy != self._busy:
            self._busy = busy
            self.busy_changed.emit(busy)
            if not busy:
                self.idle.emit()
