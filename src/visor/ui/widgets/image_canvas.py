"""Zoomable image canvas with cursor coordinates and click inspection."""

from __future__ import annotations

import numpy as np
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QImage, QMouseEvent, QPainter, QPixmap, QWheelEvent
from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsScene, QGraphicsView


class ImageCanvas(QGraphicsView):
    cursor_position = Signal(float, float)
    image_clicked = Signal(float, float)

    def __init__(self, placeholder: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("resultImage")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setBackgroundBrush(Qt.GlobalColor.black)
        self.setMouseTracking(True)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self._item: QGraphicsPixmapItem | None = None
        self._image_size = (0, 0)
        self._placeholder = placeholder
        self._auto_fit = True
        self.set_image(None)

    def set_image(self, bgr: np.ndarray | None) -> None:
        self._scene.clear()
        self._item = None
        if bgr is None:
            self._scene.setSceneRect(0, 0, 640, 480)
            text = self._scene.addText(self._placeholder)
            text.setDefaultTextColor(Qt.GlobalColor.lightGray)
            text.setTextWidth(420)
            text.setPos(110, 220)
            self._image_size = (0, 0)
            self.resetTransform()
            self._auto_fit = True
            return
        rgb = np.ascontiguousarray(bgr[:, :, ::-1])
        height, width, _ = rgb.shape
        qimage = QImage(rgb.data, width, height, 3 * width, QImage.Format.Format_RGB888).copy()
        self._item = self._scene.addPixmap(QPixmap.fromImage(qimage))
        self._image_size = (width, height)
        self._scene.setSceneRect(self._item.boundingRect())
        self._auto_fit = True
        self.fit_image()

    def set_placeholder(self, message: str) -> None:
        self._placeholder = message
        self.set_image(None)

    def fit_image(self) -> None:
        if self._item is not None:
            self.fitInView(self._item, Qt.AspectRatioMode.KeepAspectRatio)
            self._auto_fit = True

    def wheelEvent(self, event: QWheelEvent) -> None:
        if self._item is None:
            return
        scale = 1.2 if event.angleDelta().y() > 0 else 1 / 1.2
        self.scale(scale, scale)
        self._auto_fit = False
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        self._emit_position(event)
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            position = self._image_position(event)
            if position is not None:
                self.image_clicked.emit(*position)
        super().mousePressEvent(event)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._auto_fit:
            self.fit_image()

    def _image_position(self, event: QMouseEvent) -> tuple[float, float] | None:
        if self._item is None:
            return None
        point = self.mapToScene(event.position().toPoint())
        if not self._item.contains(point):
            return None
        x, y = point.x(), point.y()
        width, height = self._image_size
        if 0 <= x < width and 0 <= y < height:
            return x, y
        return None

    def _emit_position(self, event: QMouseEvent) -> None:
        position = self._image_position(event)
        if position is not None:
            self.cursor_position.emit(*position)
