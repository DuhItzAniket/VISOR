"""Qt delivery/lifetime regressions use a controllable worker, never models."""

import os
from pathlib import Path
from threading import Event
from time import monotonic

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QSettings, QThread, QTimer, Signal
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from visor.ui import main_window


class HeldWorker(QThread):
    completed = Signal(object)
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.release = Event()

    def run(self):
        self.release.wait(3)
        # Deliberately ignore cancellation to simulate a native call finishing.
        self.completed.emit("old result")
        self.failed.emit("old failure")


def _pump(app, condition):
    deadline = monotonic() + 3
    while not condition() and monotonic() < deadline:
        app.processEvents()
        QTest.qWait(10)
    assert condition()


@pytest.fixture
def workspace(monkeypatch, tmp_path):
    app = QApplication.instance() or QApplication([])
    settings = QSettings(str(tmp_path / "window.ini"), QSettings.Format.IniFormat)
    monkeypatch.setattr(main_window, "QSettings", lambda *args: settings)
    monkeypatch.setattr(main_window, "AnalysisWorker", HeldWorker)
    window = main_window.MainWindow()
    image = Path(__file__).parent / "data/reference.png"
    window.reference_input.load_path(image)
    window.target_input.load_path(image)
    successes, failures = [], []
    window._show_result = successes.append
    window._show_error = failures.append
    yield app, window, successes, failures
    if window._worker is not None:
        window._worker.release.set()
        _pump(app, lambda: window._worker is None)
    if window._install_worker is not None:
        window._install_worker.release.set()
        _pump(app, lambda: window._install_worker is None)
    window.close()
    app.processEvents()


@pytest.mark.parametrize("change", ["image", "parameter", "cancel"])
def test_obsolete_signals_are_ignored(workspace, change):
    app, window, successes, failures = workspace
    window._start_analysis()
    worker = window._worker
    cancellation = window._cancel_event
    if change == "image":
        window.target_input.clear_image()
    elif change == "parameter":
        window.ransac_control.setValue(5)
    else:
        window._cancel_running()
    assert cancellation.is_set()
    worker.release.set()
    _pump(app, lambda: window._worker is None)
    assert successes == failures == []
    assert window.cancel_button.isEnabled() is False


def test_current_job_delivers_and_reenables_actions(workspace):
    app, window, successes, failures = workspace
    window._start_analysis()
    window._worker.release.set()
    _pump(app, lambda: window._worker is None)
    assert successes == ["old result"] and failures == []
    assert window.run_button.isEnabled()


def test_close_remains_responsive_and_waits_without_blocking(workspace):
    app, window, successes, failures = workspace
    window._start_analysis()
    worker = window._worker
    window.close()
    assert window._closing_requested and window.isVisible()
    ticks = []
    QTimer.singleShot(0, lambda: ticks.append(1))
    _pump(app, lambda: bool(ticks))
    assert not window._job_can_start()
    worker.release.set()
    _pump(app, lambda: window._worker is None and not window.isVisible())
    assert successes == failures == []


def test_installation_owns_lifetime_and_blocks_competing_work(workspace):
    app, window, successes, failures = workspace
    worker = HeldWorker()
    window._install_worker = worker
    worker.finished.connect(window._on_install_finished)
    worker.start()
    window._start_analysis()
    assert window._worker is None
    window.close()
    assert window.isVisible() and window._closing_requested
    worker.release.set()
    _pump(app, lambda: window._install_worker is None and not window.isVisible())
    assert successes == failures == []
