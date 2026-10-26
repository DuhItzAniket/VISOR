"""Image previews match decoded orientation and survive recoverable selection failures."""

import os
import struct

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import cv2
import numpy as np
import pytest
from PySide6.QtCore import QSize
from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import QApplication

from visor.pipeline import _read_image
from visor.ui.widgets.image_drop import ImageDropWidget


def oriented_jpeg(path, orientation=6):
    image = np.zeros((40, 80, 3), np.uint8)
    image[:20, :40] = (0, 0, 255)
    image[:20, 40:] = (0, 255, 0)
    image[20:, :40] = (255, 0, 0)
    image[20:, 40:] = (255, 255, 255)
    success, encoded = cv2.imencode(".jpg", image)
    assert success
    tiff = (b"II" + struct.pack("<HI", 42, 8) + struct.pack("<H", 1)
            + struct.pack("<HHI", 0x112, 3, 1) + struct.pack("<H", orientation) + b"\0\0" + struct.pack("<I", 0))
    app1 = b"Exif\0\0" + tiff
    raw = encoded.tobytes()
    path.write_bytes(raw[:2] + b"\xff\xe1" + struct.pack(">H", len(app1) + 2) + app1 + raw[2:])
    return path


@pytest.mark.parametrize("orientation", range(1, 9))
@pytest.mark.parametrize("title", ["Reference image", "Target image"])
def test_preview_matches_analysis_orientation_dimensions_and_corner_colors(tmp_path, orientation, title):
    app = QApplication.instance() or QApplication([])
    widget = ImageDropWidget(title)
    image = oriented_jpeg(tmp_path / "rotated.jpg", orientation)
    decoded = _read_image(image)
    assert widget.load_path(image)
    assert f"{decoded.shape[1]} × {decoded.shape[0]} px" in widget.metadata_label.text()
    preview = widget._thumbnail.toImage()
    assert (preview.width(), preview.height()) == (decoded.shape[1], decoded.shape[0])
    for x, y in [(5, 5), (preview.width() - 6, 5), (5, preview.height() - 6),
                 (preview.width() - 6, preview.height() - 6)]:
        color = preview.pixelColor(x, y)
        np.testing.assert_allclose((color.blue(), color.green(), color.red()), decoded[y, x], atol=3)
    widget.close()
    app.processEvents()


def test_failed_replacement_retains_the_current_image_and_emits_no_clear(tmp_path):
    app = QApplication.instance() or QApplication([])
    widget = ImageDropWidget("Reference image")
    image = oriented_jpeg(tmp_path / "good.jpg", 1)
    widget.load_path(image)
    changes = []
    widget.image_changed.connect(lambda *args: changes.append(args))
    broken = tmp_path / "broken.jpg"
    broken.write_bytes(b"Not an image")
    assert not widget.load_path(broken)
    assert widget.image_path == image.resolve() and changes == []
    assert "Could not read" in widget.metadata_label.text()
    assert "Current image retained" in widget.metadata_label.text()
    widget.close()
    app.processEvents()


def test_large_preview_is_bounded_but_metadata_retains_source_dimensions(tmp_path):
    app = QApplication.instance() or QApplication([])
    widget = ImageDropWidget("Reference image")
    image = tmp_path / "large.png"
    success, encoded = cv2.imencode(".png", np.zeros((1800, 2700, 3), np.uint8))
    assert success
    encoded.tofile(image)
    assert widget.load_path(image)
    assert "2700 × 1800 px" in widget.metadata_label.text()
    assert widget._thumbnail.width() == 1024 and widget._thumbnail.height() <= 1024
    widget.clear_image()
    assert widget._thumbnail.isNull() and widget.image_path is None
    widget.close()
    app.processEvents()


def test_resizing_does_not_reread_the_source_file(tmp_path):
    app = QApplication.instance() or QApplication([])
    widget = ImageDropWidget("Reference image")
    image = oriented_jpeg(tmp_path / "loaded.jpg", 1)
    widget.load_path(image)
    moved = tmp_path / "temporarily-unavailable.jpg"
    assert image.resolve().is_relative_to(tmp_path.resolve()) and moved.resolve().is_relative_to(tmp_path.resolve())
    image.rename(moved)
    widget.resizeEvent(QResizeEvent(QSize(420, 330), QSize(300, 230)))
    assert widget.preview.pixmap() is not None and not widget.preview.pixmap().isNull()
    assert widget.image_path == image.resolve()
    widget.close()
    app.processEvents()
