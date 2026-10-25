"""Overlay editors agree with rendered and saved effective settings."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication, QFileDialog

from visor.exporting import load_project
from visor.pipeline import analyze
from visor.ui import main_window


@pytest.fixture
def overlay_workspace(textured_pair, monkeypatch):
    app = QApplication.instance() or QApplication([])
    window = main_window.MainWindow()
    reference, target = textured_pair[:2]
    window.reference_input.load_path(reference)
    window.target_input.load_path(target)
    window._show_result(analyze(reference, target, "SIFT"))
    rendered = []
    original = main_window.render_match_canvas

    def record_render(*args):
        rendered.append(args[-1])
        return original(*args)

    monkeypatch.setattr(main_window, "render_match_canvas", record_render)
    yield window, rendered
    window.close()
    app.processEvents()


@pytest.mark.parametrize("editor", ["feature_thickness_slider", "match_line_thickness"])
def test_width_edit_updates_both_controls_render_and_project(overlay_workspace, editor, tmp_path, monkeypatch):
    window, rendered = overlay_workspace
    for width in (3, 1, 12):
        rendered.clear()
        getattr(window, editor).setValue(width)
        assert window.feature_thickness_slider.value() == window.match_line_thickness.value() == width
        assert window.feature_thickness_value.text() == f"{width} px"
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
        assert len(rendered) == 1
        assert rendered[0].rainbow_feature_colors == expected
        assert window._latest_result.settings.rainbow_feature_colors == expected
        assert window._read_configurations()[0].rainbow_feature_colors == expected
