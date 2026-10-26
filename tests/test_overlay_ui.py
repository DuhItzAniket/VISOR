"""Overlay editors agree with rendered and saved effective settings."""

import os
from threading import Event
from time import monotonic

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QThread, QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QFileDialog

from visor.exporting import load_project
from visor.pipeline import analyze
from visor.ui import main_window, overlay_renderer


def pump(app, condition):
    deadline = monotonic() + 4
    while not condition() and monotonic() < deadline:
        app.processEvents()
        QTest.qWait(5)
    assert condition()


@pytest.fixture
def overlay_workspace(textured_pair, monkeypatch):
    app = QApplication.instance() or QApplication([])
    window = main_window.MainWindow()
    reference, target = textured_pair[:2]
    window.reference_input.load_path(reference)
    window.target_input.load_path(target)
    window._show_result(analyze(reference, target, "SIFT"))
    rendered = []
    original = overlay_renderer.render_match_canvas

    def record_render(*args, **kwargs):
        rendered.append(args[-1])
        return original(*args, **kwargs)

    monkeypatch.setattr(overlay_renderer, "render_match_canvas", record_render)
    yield window, rendered
    window.close()
    pump(app, lambda: not window._overlay_renderer.busy)
    app.processEvents()


@pytest.mark.parametrize("editor", ["feature_thickness_slider", "match_line_thickness"])
def test_width_edit_updates_both_controls_render_and_project(overlay_workspace, editor, tmp_path, monkeypatch):
    window, rendered = overlay_workspace
    for width in (3, 1, 12):
        rendered.clear()
        getattr(window, editor).setValue(width)
        assert window.feature_thickness_slider.value() == window.match_line_thickness.value() == width
        assert window.feature_thickness_value.text() == f"{width} px"
        pump(QApplication.instance(), lambda: not window._overlay_renderer.busy)
        assert len(rendered) == 1
        assert rendered[0].feature_line_thickness == width
        assert window._latest_result.settings.feature_line_thickness == width
        assert window._read_configurations()[0].feature_line_thickness == width
    project = tmp_path / "overlay.visor"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args: (str(project), ""))
    window._save_project()
    assert load_project(project).settings.feature_line_thickness == 12
    window._reset_configuration()
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(project), ""))
    window._load_project()
    assert window.feature_thickness_slider.value() == window.match_line_thickness.value() == 12


def test_rainbow_can_be_enabled_and_disabled_from_either_control(overlay_workspace):
    window, rendered = overlay_workspace
    action = window.view_toggles["rainbow_feature_colors"]
    for change, expected in ((action.trigger, True), (window.feature_color_button.click, False),
                             (window.feature_color_button.click, True), (action.trigger, False)):
        rendered.clear()
        change()
        assert action.isChecked() == window.feature_color_button.isChecked() == expected
        pump(QApplication.instance(), lambda: not window._overlay_renderer.busy)
        assert len(rendered) == 1
        assert rendered[0].rainbow_feature_colors == expected
        assert window._latest_result.settings.rainbow_feature_colors == expected
        assert window._read_configurations()[0].rainbow_feature_colors == expected


def test_slider_burst_renders_only_the_latest_style_and_preserves_zoom(overlay_workspace):
    window, rendered = overlay_workspace
    view = window.localization_view
    view.scale(2, 2)
    view._auto_fit = False
    transform = view.transform()
    for width in (3, 6, 9, 12):
        window.feature_thickness_slider.setValue(width)
    assert window._overlay_renderer.busy
    pump(QApplication.instance(), lambda: not window._overlay_renderer.busy)
    assert len(rendered) == 1 and rendered[0].feature_line_thickness == 12
    assert view.transform() == transform and not view._auto_fit


def test_failed_overlay_preserves_analysis_and_restores_effective_controls(overlay_workspace, monkeypatch):
    window, _ = overlay_workspace
    previous = window._latest_result

    def fail(*args, **kwargs):
        raise RuntimeError("render failure fixture")

    monkeypatch.setattr(overlay_renderer, "render_match_canvas", fail)
    window.feature_thickness_slider.setValue(12)
    pump(QApplication.instance(), lambda: not window._overlay_renderer.busy)
    assert window._latest_result is previous
    assert window.match_line_thickness.value() == window.feature_thickness_slider.value() == 1
    assert "previous overlay is retained" in window.statusBar().currentMessage()


@pytest.fixture
def held_overlay(overlay_workspace, monkeypatch):
    window, rendered = overlay_workspace
    app = QApplication.instance()
    entered, release = Event(), Event()
    threads = []
    original = overlay_renderer.render_match_canvas

    def hold(*args, **kwargs):
        threads.append(QThread.currentThread())
        entered.set()
        assert release.wait(4), "Rendering fixture was not released"
        return original(*args, **kwargs)

    monkeypatch.setattr(overlay_renderer, "render_match_canvas", hold)
    window.feature_thickness_slider.setValue(3)
    pump(app, entered.is_set)
    try:
        yield app, window, release, threads, rendered
    finally:
        release.set()
        pump(app, lambda: not window._overlay_renderer.busy)


def test_drawing_runs_off_ui_thread_and_export_waits_for_consistent_snapshot(held_overlay, monkeypatch):
    app, window, release, threads, _ = held_overlay
    assert threads[0] != app.thread()
    ticks = []
    QTimer.singleShot(0, lambda: ticks.append(1))
    pump(app, lambda: bool(ticks))
    assert not release.is_set() and window._latest_result.settings.feature_line_thickness == 1

    def no_dialog(*args):
        raise AssertionError("An export dialog opened during an overlay update")

    monkeypatch.setattr(QFileDialog, "getSaveFileName", no_dialog)
    for export in (window._export_json, window._export_csv, window._export_html_report, window._export_visualization):
        export()
        assert "before exporting" in window.statusBar().currentMessage()
    release.set()
    pump(app, lambda: not window._overlay_renderer.busy)
    assert window._latest_result.settings.feature_line_thickness == 3


@pytest.mark.parametrize("action", ["cancel", "input", "close"])
def test_cancellation_invalidation_and_close_discard_active_overlay(held_overlay, action):
    app, window, release, _, _ = held_overlay
    previous = window._latest_result
    delivered = []
    window._overlay_renderer.completed.connect(delivered.append)
    if action == "cancel":
        window._cancel_running()
        assert window._latest_result is previous
        assert window.feature_thickness_slider.value() == 1
        assert "cancelled" in window.statusBar().currentMessage()
    elif action == "input":
        window.target_input.clear_image()
        assert window._latest_result is None
    else:
        window.close()
        assert window._closing_requested and window.isVisible()
        ticks = []
        QTimer.singleShot(0, lambda: ticks.append(1))
        pump(app, lambda: bool(ticks))
    release.set()
    pump(app, lambda: not window._overlay_renderer.busy)
    assert delivered == []
    if action == "close":
        pump(app, lambda: not window.isVisible())


def test_latest_style_replaces_pending_request_while_one_worker_is_active(held_overlay):
    app, window, release, _, rendered = held_overlay
    delivered = []
    window._overlay_renderer.completed.connect(delivered.append)
    active = window._overlay_renderer._worker
    for width in (6, 9, 12):
        window.feature_thickness_slider.setValue(width)
    assert window._overlay_renderer._worker is active
    assert window._overlay_renderer._pending.settings.feature_line_thickness == 12
    release.set()
    pump(app, lambda: not window._overlay_renderer.busy)
    assert len(delivered) == 1 and window._latest_result.settings.feature_line_thickness == 12
    assert [settings.feature_line_thickness for settings in rendered] == [3, 12]
