"""Canvas uploads preserve color/ownership and overlay viewport state."""

import gc
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
from PySide6.QtWidgets import QApplication

from visor.ui.widgets.image_canvas import ImageCanvas


def test_canvas_owns_pixels_with_correct_bgr_order_and_noncontiguous_input():
    app = QApplication.instance() or QApplication([])
    canvas = ImageCanvas("empty")
    source = np.zeros((10, 20, 3), dtype=np.uint8)
    source[:] = (19, 73, 211)
    view = source[:, ::2]
    assert not view.flags.c_contiguous
    canvas.set_image(view)
    source[:] = 0
    del source, view
    gc.collect()
    pixel = canvas._item.pixmap().toImage().pixelColor(2, 2)
    assert pixel.getRgb() == (211, 73, 19, 255)
    canvas.close()
    app.processEvents()


def test_overlay_replacement_retains_zoom_and_scene_item_but_new_result_fits():
    app = QApplication.instance() or QApplication([])
    canvas = ImageCanvas("empty")
    canvas.resize(320, 240)
    image = np.zeros((300, 400, 3), np.uint8)
    canvas.set_image(image)
    canvas.scale(2, 2)
    canvas._auto_fit = False
    before = canvas.transform()
    item = canvas._item
    canvas.set_image(image + 10, preserve_view=True)
    assert canvas.transform() == before and canvas._item is item
    assert not canvas._auto_fit
    canvas.set_image(image)
    assert canvas._auto_fit and canvas.transform() != before
    canvas.set_image(image[:100, :100], preserve_view=True)
    assert canvas._image_size == (100, 100) and canvas._auto_fit
    canvas.close()
    app.processEvents()
