"""Image input widget with native picker and drag-and-drop support."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)
IMAGE_FILTER = "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp);;All files (*.*)"


class ImageDropWidget(QFrame):
    """A labeled image slot that accepts local image files by drop or picker."""

    image_changed = Signal(str, object)

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("imageDropWidget")
        self.setAcceptDrops(True)
        self.setMinimumHeight(230)
        self._image_path: Path | None = None
        self._title = title

        self.title_label = QLabel(title)
        self.title_label.setObjectName("sectionTitle")
        self.preview = QLabel("Drop an image here\nor choose a file")
        self.preview.setObjectName("imagePreview")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumHeight(145)
        self.preview.setAcceptDrops(False)
        self.preview.setWordWrap(True)

        self.metadata_label = QLabel("PNG, JPEG, BMP, TIFF, or WebP")
        self.metadata_label.setObjectName("mutedText")
        self.metadata_label.setWordWrap(True)
        self.browse_button = QPushButton("Choose image…")
        self.browse_button.setObjectName("secondaryButton")
        self.browse_button.clicked.connect(self._browse)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 13, 14, 13)
        layout.setSpacing(8)
        layout.addWidget(self.title_label)
        layout.addWidget(self.preview, 1)
        layout.addWidget(self.metadata_label)
        layout.addWidget(self.browse_button)

    @property
    def image_path(self) -> Path | None:
        return self._image_path

    def _browse(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(self, f"Choose {self._title}", "", IMAGE_FILTER)
        if filename:
            self.load_path(Path(filename))

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if self._dropped_image(event.mimeData().urls()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        paths = self._dropped_image(event.mimeData().urls())
        if paths:
            self.load_path(paths[0])
            event.acceptProposedAction()
        else:
            event.ignore()

    @staticmethod
    def _dropped_image(urls: list) -> list[Path]:
        accepted = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}
        return [Path(url.toLocalFile()) for url in urls if url.isLocalFile() and Path(url.toLocalFile()).suffix.lower() in accepted]

    def load_path(self, path: Path) -> None:
        """Load and preview an image, reporting a useful error for invalid files."""
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            self.metadata_label.setText("Could not read this image. Choose a supported image file.")
            self.metadata_label.setObjectName("errorText")
            self.metadata_label.style().unpolish(self.metadata_label)
            self.metadata_label.style().polish(self.metadata_label)
            logger.warning("Unable to load image for %s: %s", self._title, path)
            self.image_changed.emit(self._title, None)
            return

        self._image_path = path.resolve()
        self.preview.setPixmap(
            pixmap.scaled(
                self.preview.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        self.metadata_label.setObjectName("mutedText")
        self.metadata_label.setText(f"{path.name}  ·  {pixmap.width()} × {pixmap.height()} px")
        self.metadata_label.style().unpolish(self.metadata_label)
        self.metadata_label.style().polish(self.metadata_label)
        self.image_changed.emit(self._title, self._image_path)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._image_path:
            pixmap = QPixmap(str(self._image_path))
            self.preview.setPixmap(
                pixmap.scaled(
                    self.preview.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

