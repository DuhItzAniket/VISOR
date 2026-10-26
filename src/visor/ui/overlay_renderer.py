"""Bounded background overlay rendering with latest-request delivery."""

from __future__ import annotations

from dataclasses import dataclass, replace
from threading import Event

from PySide6.QtCore import QObject, QThread, QTimer, Signal

from visor.jobs import JobController, JobTicket
from visor.models import AnalysisResult, AnalysisSettings
from visor.ui.job_relay import JobRelay
from visor.visualization import render_localization, render_match_canvas


class OverlayCancelled(Exception):
    """An obsolete overlay stops at a cooperative drawing boundary."""


@dataclass(frozen=True)
class OverlayRequest:
    source: AnalysisResult
    settings: AnalysisSettings


@dataclass(frozen=True)
class OverlayUpdate:
    source: AnalysisResult
    rendered: AnalysisResult


class OverlayWorker(QThread):
    completed = Signal(object)
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, request: OverlayRequest, cancellation: Event) -> None:
        super().__init__()
        self.request = request
        self.cancellation = cancellation

    def _check_cancel(self) -> None:
        if self.cancellation.is_set():
            raise OverlayCancelled()

    def run(self) -> None:
        try:
            source, settings = self.request.source, self.request.settings
            matches = render_match_canvas(
                source.reference_image, source.target_image, source.reference_features,
                source.target_features, source.match_set, source.geometry, settings,
                cancel_check=self._check_cancel,
            )
            localization = render_localization(
                source.target_image, source.target_features, source.geometry, settings,
                cancel_check=self._check_cancel,
            )
            self._check_cancel()
            self.completed.emit(OverlayUpdate(source, replace(
                source, settings=settings, matches_image=matches, localization_image=localization,
            )))
        except OverlayCancelled:
            self.cancelled.emit()
        except Exception as exc:  # noqa: BLE001 — report presentation failures without losing analysis
            self.failed.emit(str(exc))


class OverlayRenderer(QObject):
    """Own one worker and one replaceable pending request; never queue full renders."""

    completed = Signal(object)
    failed = Signal(str)
    busy_changed = Signal(bool)
    idle = Signal()

    def __init__(self, parent: QObject, *, worker_factory=OverlayWorker) -> None:
        super().__init__(parent)
        self._factory = worker_factory
        self._jobs = JobController()
        self._worker: OverlayWorker | None = None
        self._pending: OverlayRequest | None = None
        self._busy = False
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(40)
        self._timer.timeout.connect(self._start_next)

    @property
    def busy(self) -> bool:
        return self._worker is not None or self._pending is not None

    def request(self, source: AnalysisResult, settings: AnalysisSettings) -> None:
        if self._jobs.closing:
            return
        self._jobs.invalidate()
        self._pending = OverlayRequest(source, settings)
        self._timer.start()
        self._publish_state()

    def invalidate(self) -> None:
        self._jobs.invalidate()
        self._pending = None
        self._timer.stop()
        self._publish_state()

    def shutdown(self) -> None:
        self._jobs.shutdown()
        self.invalidate()

    def _start_next(self) -> None:
        if self._worker is not None or self._pending is None or self._jobs.closing:
            return
        request, self._pending = self._pending, None
        ticket = self._jobs.begin()
        worker = self._factory(request, ticket.cancellation)
        self._worker = worker
        relay = JobRelay(self._jobs, ticket, self.completed.emit, self.failed.emit, lambda: None,
                         lambda: self._finished(worker, ticket), self)
        worker.completed.connect(relay.success)
        worker.failed.connect(relay.failure)
        worker.cancelled.connect(relay.cancelled)
        worker.finished.connect(relay.finished)
        worker.start()

    def _finished(self, worker: OverlayWorker, ticket: JobTicket) -> None:
        self._jobs.finish(ticket)
        self._worker = None
        worker.deleteLater()
        if self._pending is not None and not self._jobs.closing:
            self._timer.start()
        self._publish_state()

    def _publish_state(self) -> None:
        busy = self.busy
        if busy != self._busy:
            self._busy = busy
            self.busy_changed.emit(busy)
            if not busy:
                self.idle.emit()
