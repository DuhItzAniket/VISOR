"""Native pickers start in user folders and remember successful destinations."""

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QStandardPaths
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from visor.pipeline import analyze
from visor.ui import main_window


@pytest.fixture
def dialog_workspace(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    paths = {name: tmp_path / name for name in ("pictures", "documents", "videos")}
    for path in paths.values():
        path.mkdir()
    locations = {QStandardPaths.StandardLocation.PicturesLocation: paths["pictures"],
                 QStandardPaths.StandardLocation.DocumentsLocation: paths["documents"],
                 QStandardPaths.StandardLocation.MoviesLocation: paths["videos"]}
    monkeypatch.setattr(QStandardPaths, "writableLocation", lambda kind: str(locations.get(kind, paths["documents"])))
    window = main_window.MainWindow()
    yield app, window, paths
    window.close()
    app.processEvents()


def _inputs(window):
    image = Path(__file__).parent / "data/reference.png"
    window.reference_input.load_path(image)
    window.target_input.load_path(image)
    return image


def test_initial_images_and_projects_use_platform_user_folders(dialog_workspace, monkeypatch):
    _, window, paths = dialog_workspace
    opened, saved = [], []
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (opened.append(args[2]) or "", ""))
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args: (saved.append(args[2]) or "", ""))
    window.reference_input._browse()
    window._load_project()
    _inputs(window)
    window._save_project()
    assert opened == [str(paths["pictures"]), str(paths["documents"])]
    assert saved == [str(paths["documents"] / "analysis.visor")]
    assert window._dialog_directory("videos") == paths["videos"]
    assert window._window_settings.value("paths/projects") is None  # cancel does not record a destination
    window._window_settings.setValue("paths/projects", "../application-folder")
    assert window._dialog_directory("projects") == paths["documents"]


def test_loaded_image_directory_is_shared_and_persists_between_windows(dialog_workspace, monkeypatch):
    app, window, _ = dialog_workspace
    image = _inputs(window)
    calls = []
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (calls.append(args[2]) or "", ""))
    window.target_input.clear_image()
    window.target_input._browse()
    other = main_window.MainWindow()
    try:
        other.reference_input._browse()
        assert calls == [str(image.resolve().parent)] * 2
        assert other.reference_input.image_path is None
    finally:
        other.close()
        app.processEvents()


def test_project_save_and_load_reuse_selected_filename(dialog_workspace, tmp_path, monkeypatch):
    _, window, _ = dialog_workspace
    _inputs(window)
    project = tmp_path / "selected-name.visor"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args: (str(project), ""))
    window._save_project()
    assert project.exists() and window._project_path == project
    captured = []
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args: (captured.append(args[2]) or "", ""))
    window._save_project()
    assert captured == [str(project)]
    window._project_path = None
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(project), ""))
    window._load_project()
    assert window._project_path == project
    assert window._dialog_directory("projects") == project.parent


def test_unreadable_project_image_does_not_reuse_a_previous_workspace_input(dialog_workspace, tmp_path, monkeypatch):
    import json

    _, window, _ = dialog_workspace
    previous = _inputs(window)
    project = tmp_path / "missing-image.visor"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args: (str(project), ""))
    window._save_project()
    session = json.loads(project.read_text(encoding="utf-8"))
    broken = tmp_path / "broken.png"
    broken.write_bytes(b"not an image")
    session["target_path"] = str(broken)
    project.write_text(json.dumps(session), encoding="utf-8")
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(project), ""))
    window._load_project()
    assert window.reference_input.image_path == previous.resolve()
    assert window.target_input.image_path is None
    assert not window.run_button.isEnabled()
    assert "could not be decoded" in window.statusBar().currentMessage()


def test_exports_remember_only_successful_destinations(dialog_workspace, tmp_path, monkeypatch):
    _, window, _ = dialog_workspace
    image = _inputs(window)
    window._show_result(analyze(image, image, "SIFT"))
    directory = tmp_path / "exported"
    directory.mkdir()
    output = directory / "report.json"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args: (str(output), ""))
    window._export_json()
    assert output.exists()
    assert window._suggested_export("metrics.csv") == str(directory / "metrics.csv")
    messages = []
    monkeypatch.setattr(QMessageBox, "critical", lambda *args: messages.append(args[2]))
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args: (str(tmp_path / "failed.json"), ""))

    def failed_export(*args):
        raise OSError("Destination unavailable")

    window._export_analysis(failed_export, "JSON files (*.json)", "analysis.json")
    assert messages == ["Destination unavailable"]
    assert window._dialog_directory("exports") == directory
