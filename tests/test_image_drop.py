"""Qt drop-event contracts; these do not replace native Explorer review."""

import os
import shutil
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QMimeData, QPoint, QPointF, Qt, QUrl
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent
from PySide6.QtWidgets import QApplication

from visor.ui import main_window


@pytest.fixture
def drop_workspace():
    app = QApplication.instance() or QApplication([])
    window = main_window.MainWindow()
    window.show()
    app.processEvents()
    yield app, window
    window.close()
    app.processEvents()


def _mime(urls):
    data = QMimeData()
    data.setUrls(urls)
    return data


def _enter(widget, mime, actions):
    event = QDragEnterEvent(QPoint(50, 50), actions, mime, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.ShiftModifier)
    QApplication.sendEvent(widget, event)
    return event


@pytest.mark.parametrize("role", ["reference_input", "target_input"])
def test_image_drop_overrides_move_with_copy_and_preserves_source(drop_workspace, tmp_path, role, qt_wait):
    _, window = drop_workspace
    image = tmp_path / "reference with spaces — 图像.PNG"
    shutil.copyfile(Path(__file__).parent / "data/reference.png", image)
    original = image.read_bytes()
    widget = getattr(window, role)
    changes = []
    widget.image_changed.connect(lambda *args: changes.append(args))
    mime = _mime([QUrl.fromLocalFile(str(image))])
    actions = Qt.DropAction.CopyAction | Qt.DropAction.MoveAction
    enter = _enter(widget, mime, actions)
    assert enter.proposedAction() == Qt.DropAction.MoveAction
    assert enter.isAccepted() and enter.dropAction() == Qt.DropAction.CopyAction
    move = QDragMoveEvent(QPoint(70, 70), actions, mime,
                          Qt.MouseButton.LeftButton, Qt.KeyboardModifier.ShiftModifier)
    QApplication.sendEvent(widget, move)
    assert move.isAccepted() and move.dropAction() == Qt.DropAction.CopyAction
    drop = QDropEvent(QPointF(70, 70), actions, mime,
                      Qt.MouseButton.LeftButton, Qt.KeyboardModifier.ShiftModifier)
    QApplication.sendEvent(widget, drop)
    assert drop.isAccepted() and drop.dropAction() == Qt.DropAction.CopyAction
    qt_wait(lambda: not widget.loading)
    assert widget.image_path == image.resolve()
    assert len(changes) == 1 and changes[0][1] == image.resolve()
    assert window._paths[widget.accessibleName()] == image.resolve()
    assert image.name in widget.metadata_label.text() and "px" in widget.metadata_label.text()
    assert image.read_bytes() == original


@pytest.mark.parametrize("urls,actions", [
    ([QUrl("https://example.invalid/image.png")], Qt.DropAction.CopyAction),
    ([QUrl.fromLocalFile("C:/unsupported.txt")], Qt.DropAction.CopyAction),
    ([], Qt.DropAction.CopyAction),
])
def test_non_image_or_remote_drag_is_rejected(drop_workspace, urls, actions):
    _, window = drop_workspace
    event = _enter(window.reference_input, _mime(urls), actions)
    assert not event.isAccepted()
    assert window.reference_input.image_path is None


def test_move_only_source_is_rejected_without_reading_or_changing_input(drop_workspace):
    _, window = drop_workspace
    image = Path(__file__).parent / "data/reference.png"
    event = _enter(window.reference_input, _mime([QUrl.fromLocalFile(str(image.resolve()))]), Qt.DropAction.MoveAction)
    assert not event.isAccepted()
    assert not window._paths


def test_unreadable_drop_queues_open_then_reports_decode_failure(drop_workspace, tmp_path, qt_wait):
    _, window = drop_workspace
    image = tmp_path / "broken.png"
    image.write_bytes(b"not an image")
    mime = _mime([QUrl.fromLocalFile(str(image))])
    assert _enter(window.target_input, mime, Qt.DropAction.CopyAction).isAccepted()
    drop = QDropEvent(QPointF(50, 50), Qt.DropAction.CopyAction, mime,
                      Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    QApplication.sendEvent(window.target_input, drop)
    assert drop.isAccepted() and drop.dropAction() == Qt.DropAction.CopyAction
    qt_wait(lambda: not window.target_input.loading)
    assert window.target_input.image_path is None
    assert "Could not read" in window.target_input.metadata_label.text()
    assert not window.run_button.isEnabled()
    assert image.read_bytes() == b"not an image"


def test_failed_replacement_drop_retains_the_pair_after_queued_decode_failure(drop_workspace, tmp_path, qt_wait):
    _, window = drop_workspace
    previous = (Path(__file__).parent / "data/reference.png").resolve()
    window.reference_input.load_path(previous)
    window.target_input.load_path(previous)
    image = tmp_path / "broken.jpg"
    image.write_bytes(b"not an image")
    mime = _mime([QUrl.fromLocalFile(str(image))])
    assert _enter(window.target_input, mime, Qt.DropAction.CopyAction).isAccepted()
    drop = QDropEvent(QPointF(50, 50), Qt.DropAction.CopyAction, mime,
                      Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    QApplication.sendEvent(window.target_input, drop)
    assert drop.isAccepted() and drop.dropAction() == Qt.DropAction.CopyAction
    assert not window.run_button.isEnabled()
    qt_wait(lambda: not window.target_input.loading)
    assert window.target_input.image_path == previous
    assert window._paths["Target image"] == previous and window.run_button.isEnabled()
    assert "Current image retained" in window.target_input.metadata_label.text()
