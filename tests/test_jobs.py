"""A cancelled, superseded or closing job cannot deliver a new result."""

from threading import Event

import pytest

from visor.jobs import JobController


def test_revision_change_cancels_and_rejects_old_result():
    jobs = JobController()
    signal = Event()
    ticket = jobs.begin(signal)
    assert jobs.accepts(ticket)
    jobs.invalidate()
    assert signal.is_set()
    assert not jobs.is_current(ticket) and not jobs.accepts(ticket)
    with pytest.raises(RuntimeError):
        jobs.begin()
    assert jobs.finish(ticket)
    assert jobs.accepts(jobs.begin())


def test_cancel_rejects_even_a_success_signal():
    jobs = JobController()
    ticket = jobs.begin()
    jobs.cancel()
    assert jobs.is_current(ticket)
    assert not jobs.accepts(ticket)


def test_late_finish_cannot_clear_a_newer_job():
    jobs = JobController()
    old = jobs.begin()
    jobs.finish(old)
    current = jobs.begin()
    assert not jobs.finish(old)
    assert jobs.accepts(current)


def test_shutdown_cancels_and_prevents_new_work():
    jobs = JobController()
    ticket = jobs.begin()
    jobs.shutdown()
    assert ticket.cancellation.is_set() and not jobs.accepts(ticket)
    jobs.finish(ticket)
    with pytest.raises(RuntimeError):
        jobs.begin()


def test_calibration_checks_cancellation_before_reading_images():
    from visor.calibration import calibrate_from_chessboard_images

    def cancelled():
        raise RuntimeError("cancelled before decoding")

    with pytest.raises(RuntimeError, match="cancelled before decoding"):
        calibrate_from_chessboard_images([], cancel_check=cancelled)
