"""Main-thread delivery of worker signals, guarded by a job ticket."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, Slot

from visor.jobs import JobController, JobTicket


class JobRelay(QObject):
    def __init__(self, controller: JobController, ticket: JobTicket,
                 success: Callable[[Any], None], failure: Callable[[str], None],
                 cancelled: Callable[[], None], finished: Callable[[], None], parent: QObject) -> None:
        super().__init__(parent)
        self.controller = controller
        self.ticket = ticket
        self._success = success
        self._failure = failure
        self._cancelled = cancelled
        self._finished = finished
        self._terminal = False

    @Slot(object)
    def success(self, result: object) -> None:
        if not self._terminal and self.controller.accepts(self.ticket):
            self._terminal = True
            self._success(result)

    @Slot(str)
    def failure(self, message: str) -> None:
        if not self._terminal and self.controller.accepts(self.ticket):
            self._terminal = True
            self._failure(message)

    @Slot()
    def cancelled(self) -> None:
        if not self._terminal and self.controller.is_current(self.ticket):
            self._terminal = True
            self._cancelled()

    @Slot()
    def finished(self) -> None:
        if not self._terminal and self.controller.is_current(self.ticket) and self.ticket.cancellation.is_set():
            self._terminal = True
            self._cancelled()
        self._finished()
        self.deleteLater()
