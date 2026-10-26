"""Opening a project must not replace a workspace until both images decode."""

import os
from pathlib import Path
from threading import Event

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication, QFileDialog

from visor.engines import ORBConfiguration, SIFTConfiguration
from visor.exporting import ProjectSession, save_project
from visor.models import AnalysisSettings
from visor.ui import image_loader, main_window


@pytest.fixture
def workspace(tmp_path, qt_wait):
    app = QApplication.instance() or QApplication([])
    window = main_window.MainWindow()
    old = (Path(__file__).parent / "data/reference.png").resolve()
    window.reference_input.load_path(old)
    window.target_input.load_path(old)
    window._project_path = tmp_path / "previous.visor"
    releases = []
    yield window, old, releases
    for release in releases:
        release.set()
    qt_wait(lambda: not window._inputs_loading())
    window.close()
    app.processEvents()


def new_project(tmp_path, old, *, broken=False):
    reference, target = tmp_path / "new-reference.png", tmp_path / "new-target.png"
    reference.write_bytes(old.read_bytes())
    target.write_bytes(b"not an image" if broken else old.read_bytes())
    session = ProjectSession(str(reference), str(target), "ORB", AnalysisSettings(ratio_threshold=0.9),
                             SIFTConfiguration(max_features=987), ORBConfiguration(max_features=789))
    project = tmp_path / "replacement.visor"
    save_project(session, project)
    return project, reference, target


def hold_reference(monkeypatch, releases, role="reference"):
    started, release = Event(), Event()
    releases.append(release)
    original = image_loader.decode_preview

    def held(request, cancellation):
        if request.path.name == f"new-{role}.png":
            started.set()
            release.wait(5)
        return original(request, cancellation)

    monkeypatch.setattr(image_loader, "decode_preview", held)
    return started, release


def test_failed_project_preserves_images_configuration_and_document_identity(workspace, tmp_path, monkeypatch, qt_wait):
    window, old, _ = workspace
    previous_path, previous_config = window._project_path, window._read_configurations()
    project, _, _ = new_project(tmp_path, old, broken=True)
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(project), ""))
    window._load_project()
    qt_wait(lambda: not window._inputs_loading())
    assert window._project_path == previous_path
    assert window.engine_selector.currentText() == "SIFT"
    assert window._read_configurations() == previous_config
    assert window.reference_input.image_path == window.target_input.image_path == old
    assert window.run_button.isEnabled()
    assert "previous workspace" in window.statusBar().currentMessage().lower()


@pytest.mark.parametrize("role", ["reference", "target"])
def test_cancelled_project_preserves_previous_workspace(workspace, tmp_path, monkeypatch, qt_wait, role):
    window, old, releases = workspace
    previous_path, previous_config = window._project_path, window._read_configurations()
    project, _, _ = new_project(tmp_path, old)
    started, release = hold_reference(monkeypatch, releases, role)
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(project), ""))
    window._load_project()
    qt_wait(started.is_set)
    window._cancel_running()
    release.set()
    qt_wait(lambda: not window._inputs_loading())
    assert window._project_path == previous_path
    assert window.engine_selector.currentText() == "SIFT"
    assert window._read_configurations() == previous_config
    assert window.reference_input.image_path == window.target_input.image_path == old
    assert window.run_button.isEnabled()
    assert "cancelled" in window.statusBar().currentMessage().lower()


def test_project_commits_both_images_and_settings_only_after_decode(workspace, tmp_path, monkeypatch, qt_wait):
    window, old, releases = workspace
    previous_path, previous_config = window._project_path, window._read_configurations()
    project, reference, target = new_project(tmp_path, old)
    started, release = hold_reference(monkeypatch, releases)
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(project), ""))
    window._load_project()
    qt_wait(started.is_set)
    assert window._project_path == previous_path and window._read_configurations() == previous_config
    assert window.reference_input.image_path == window.target_input.image_path == old
    release.set()
    qt_wait(lambda: not window._inputs_loading())
    assert window._project_path == project.resolve()
    assert window.engine_selector.currentText() == "ORB" and window.ratio_control.value() == 0.9
    assert window.reference_input.image_path == reference.resolve()
    assert window.target_input.image_path == target.resolve()
    assert window._pair_history[-1] == (reference.resolve(), target.resolve())
    assert (reference.resolve(), old) not in window._pair_history
    assert (old, target.resolve()) not in window._pair_history
    assert window.statusBar().currentMessage() == "Project loaded: replacement.visor"


def test_latest_project_replaces_the_pending_request_without_mixed_images(workspace, tmp_path, monkeypatch, qt_wait):
    window, old, releases = workspace
    first = tmp_path / "first"
    middle = tmp_path / "middle"
    latest = tmp_path / "latest"
    for directory in (first, middle, latest):
        directory.mkdir()
    projects = [new_project(directory, old) for directory in (first, middle, latest)]
    started, release = hold_reference(monkeypatch, releases)
    selected = [projects[0][0]]
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(selected[0]), ""))
    window._load_project()
    qt_wait(started.is_set)
    selected[0] = projects[1][0]
    window._load_project()
    selected[0] = projects[2][0]
    window._load_project()
    release.set()
    qt_wait(lambda: not window._inputs_loading())
    assert window._project_path == projects[2][0].resolve()
    assert window.reference_input.image_path == projects[2][1].resolve()
    assert window.target_input.image_path == projects[2][2].resolve()
    assert all(pair[0].parent != middle for pair in window._pair_history)


def test_manual_selection_supersedes_a_staged_project(workspace, tmp_path, monkeypatch, qt_wait):
    window, old, releases = workspace
    previous_path, previous_config = window._project_path, window._read_configurations()
    project, _, _ = new_project(tmp_path, old)
    started, release = hold_reference(monkeypatch, releases, "target")
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(project), ""))
    window._load_project()
    qt_wait(started.is_set)
    manual = tmp_path / "manual.png"
    manual.write_bytes(old.read_bytes())
    window.reference_input.request_path(manual)
    release.set()
    qt_wait(lambda: not window._inputs_loading())
    assert window._project_path == previous_path and window._read_configurations() == previous_config
    assert window.reference_input.image_path == manual.resolve() and window.target_input.image_path == old


def test_failed_history_pair_does_not_replace_either_selected_image(workspace, tmp_path, qt_wait):
    window, old, _ = workspace
    previous_path, previous_config = window._project_path, window._read_configurations()
    _, reference, target = new_project(tmp_path, old, broken=True)
    window._pair_history.append((reference, target))
    window._sync_pair_list()
    window._load_selected_pair(window.pair_list.item(window.pair_list.count() - 1))
    qt_wait(lambda: not window._inputs_loading())
    assert window._project_path == previous_path and window._read_configurations() == previous_config
    assert window.reference_input.image_path == window.target_input.image_path == old
    assert "Could not load image pair" in window.statusBar().currentMessage()


def test_close_cancels_staging_and_waits_for_its_decoder(workspace, tmp_path, monkeypatch, qt_wait):
    window, old, releases = workspace
    previous_path = window._project_path
    project, _, _ = new_project(tmp_path, old)
    started, release = hold_reference(monkeypatch, releases, "target")
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(project), ""))
    window._load_project()
    qt_wait(started.is_set)
    assert not window.close()
    assert window._closing_requested and window._project_loader.busy
    release.set()
    qt_wait(lambda: not window._inputs_loading())
    assert window._project_path == previous_path
    assert window.reference_input.image_path == window.target_input.image_path == old
