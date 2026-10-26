"""Real and controlled preview workers: responsiveness, stale delivery and close."""

import os
from pathlib import Path
from threading import Event

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QThread, QTimer
from PySide6.QtWidgets import QApplication, QFileDialog

from visor.ui import image_loader, main_window

IMAGE = Path(__file__).parent / "data/reference.png"


@pytest.fixture
def workspace(qt_wait):
    app = QApplication.instance() or QApplication([])
    window = main_window.MainWindow()
    releases = []
    yield app, window, releases
    for release in releases:
        release.set()
    window.close()
    qt_wait(lambda: not window._inputs_loading())
    app.processEvents()


def hold_first(widget, releases, *, stale_failure=False):
    started, release = Event(), Event()
    releases.append(release)
    calls = []

    class HeldWorker(image_loader.PreviewWorker):
        def run(self):
            started.set()
            release.wait(5)
            if stale_failure:
                self.failed.emit("Obsolete decode failure")
            else:
                # Deliberately ignore cancellation, like an indivisible codec
                # that finishes after the user has already changed selection.
                self.completed.emit(image_loader.decode_preview(self.request, Event()))

    def factory(request, cancellation):
        calls.append(request.path)
        return (HeldWorker if len(calls) == 1 else image_loader.PreviewWorker)(request, cancellation)

    widget._loader._factory = factory
    return started, release, calls


def test_picker_decodes_off_thread_and_applies_on_ui_thread(workspace, monkeypatch, qt_wait):
    app, window, _ = workspace
    threads, deliveries = [], []
    original = image_loader.decode_preview

    def decode(request, cancellation):
        threads.append(QThread.currentThread())
        return original(request, cancellation)

    monkeypatch.setattr(image_loader, "decode_preview", decode)
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(IMAGE.resolve()), ""))
    window.reference_input.image_changed.connect(lambda *_: deliveries.append(QThread.currentThread()))
    window.reference_input._browse()
    assert window.reference_input.loading
    assert window.reference_input.image_path is None
    qt_wait(lambda: not window.reference_input.loading)
    assert window.reference_input.image_path == IMAGE.resolve()
    assert len(threads) == 1 and threads[0] != app.thread()
    assert deliveries == [app.thread()]


@pytest.mark.parametrize("stale_failure", [False, True])
def test_latest_request_wins_without_queuing_every_file(workspace, tmp_path, qt_wait, stale_failure):
    _, window, releases = workspace
    widget = window.reference_input
    started, release, calls = hold_first(widget, releases, stale_failure=stale_failure)
    newest = tmp_path / "newest.png"
    newest.write_bytes(IMAGE.read_bytes())
    changes = []
    widget.image_changed.connect(lambda *args: changes.append(args))
    assert widget.request_path(IMAGE)
    qt_wait(started.is_set)
    assert widget.request_path(tmp_path / "superseded-missing.png")
    assert widget.request_path(newest)
    assert calls == [IMAGE]
    release.set()
    qt_wait(lambda: not widget.loading)
    assert calls == [IMAGE, newest]
    assert widget.image_path == newest.resolve() and len(changes) == 1
    assert "newest.png" in widget.metadata_label.text()


def test_cancel_is_observable_keeps_input_and_does_not_block_event_loop(workspace, qt_wait):
    _, window, releases = workspace
    widget = window.reference_input
    widget.load_path(IMAGE)
    window.target_input.load_path(IMAGE)
    started, release, _ = hold_first(widget, releases)
    changes, beats = [], []
    widget.image_changed.connect(lambda *args: changes.append(args))
    heartbeat = QTimer()
    heartbeat.timeout.connect(lambda: beats.append(True))
    heartbeat.start(5)
    try:
        widget.request_path(IMAGE)
        qt_wait(started.is_set)
        assert not window.run_button.isEnabled() and window.cancel_button.isEnabled()
        assert not window._job_can_start() and not window._overlay_export_ready()
        window._cancel_running()
        assert widget.loading and "Cancellation requested" in widget.metadata_label.text()
        assert widget._loader._jobs.active.cancellation.is_set()
        qt_wait(lambda: len(beats) >= 3)
        assert widget.image_path == IMAGE.resolve() and changes == []
        release.set()
        qt_wait(lambda: not widget.loading)
        assert "cancelled" in widget.metadata_label.text()
        assert widget.image_path == IMAGE.resolve() and changes == []
        assert window.run_button.isEnabled()
        assert "loading cancelled" in window.statusBar().currentMessage()
    finally:
        heartbeat.stop()


def test_close_waits_for_native_decode_without_applying_obsolete_result(workspace, qt_wait):
    _, window, releases = workspace
    widget = window.reference_input
    started, release, _ = hold_first(widget, releases)
    changes = []
    widget.image_changed.connect(lambda *args: changes.append(args))
    widget.request_path(IMAGE)
    qt_wait(started.is_set)
    assert not window.close()
    assert window._closing_requested and widget.loading
    assert "cancellation boundary" in window.statusBar().currentMessage()
    assert not widget.request_path(IMAGE)
    release.set()
    qt_wait(lambda: not window._inputs_loading())
    assert widget.image_path is None and changes == []


def test_clear_cancels_decode_and_releases_cached_image(workspace, qt_wait):
    _, window, releases = workspace
    widget = window.reference_input
    widget.load_path(IMAGE)
    started, release, _ = hold_first(widget, releases)
    widget.request_path(IMAGE)
    qt_wait(started.is_set)
    widget.clear_image()
    assert widget.image_path is None and widget._thumbnail.isNull()
    release.set()
    qt_wait(lambda: not widget.loading)
    assert widget.image_path is None and "Drop an image" in widget.preview.text()
    assert window.statusBar().currentMessage() == "Reference image cleared."


def test_pre_cancelled_decode_does_not_open_a_codec(monkeypatch):
    def unexpected_reader(*args):
        raise AssertionError("A cancelled request must not open its source")

    monkeypatch.setattr(image_loader, "QImageReader", unexpected_reader)
    cancellation = Event()
    cancellation.set()
    with pytest.raises(image_loader.PreviewCancelled):
        image_loader.decode_preview(image_loader.PreviewRequest(IMAGE), cancellation)
