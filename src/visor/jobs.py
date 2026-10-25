"""Cooperative job ownership and result invalidation, independent of Qt."""

from __future__ import annotations

from dataclasses import dataclass
from threading import Event


@dataclass(frozen=True)
class JobTicket:
    sequence: int
    revision: int
    cancellation: Event


class JobController:
    def __init__(self) -> None:
        self.revision = 0
        self._sequence = 0
        self.active: JobTicket | None = None
        self.closing = False

    def begin(self, cancellation: Event | None = None) -> JobTicket:
        if self.active is not None or self.closing:
            raise RuntimeError("A job is active or shutdown has started.")
        self._sequence += 1
        ticket = JobTicket(self._sequence, self.revision, cancellation or Event())
        self.active = ticket
        return ticket

    def is_current(self, ticket: JobTicket) -> bool:
        return self.active is ticket and ticket.revision == self.revision and not self.closing

    def accepts(self, ticket: JobTicket) -> bool:
        return self.is_current(ticket) and not ticket.cancellation.is_set()

    def invalidate(self) -> None:
        self.revision += 1
        self.cancel()

    def cancel(self) -> None:
        if self.active is not None:
            self.active.cancellation.set()

    def finish(self, ticket: JobTicket) -> bool:
        if self.active is not ticket:
            return False
        self.active = None
        return True

    def shutdown(self) -> None:
        self.closing = True
        self.cancel()
