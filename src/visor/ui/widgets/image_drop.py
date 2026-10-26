"""Image input widget with native picker and drag-and-drop support."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QSize, QStandardPaths, Qt, QUrl, Signal
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent, QImageIOHandler, QImageReader, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)
IMAGE_FILTER = "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp);;All files (*.*)"
PREVIEW_LIMIT = QSize(1024, 1024)


class ImageDropWidget(QFrame):
    """A labeled image slot that accepts local image files by drop or picker."""

    image_changed = Signal(str, object)

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("imageDropWidget")
        self.setAccessibleName(title)
        self.setAcceptDrops(True)
        self.setMinimumHeight(230)
        self.setMinimumWidth(260)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._image_path: Path | None = None
        self._thumbnail = QPixmap()
        self._browse_directory: Path | None = None
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
        self.metadata_label.setTextFormat(Qt.TextFormat.PlainText)
        self.metadata_label.setObjectName("mutedText")
        self.metadata_label.setWordWrap(True)
        self.browse_button = QPushButton("Choose image…")
        self.browse_button.setObjectName("secondaryButton")
        self.browse_button.setAccessibleName(f"Choose {title.lower()}")
        self.browse_button.clicked.connect(self._browse)

        self.clear_button = QPushButton("×")
        self.clear_button.setObjectName("secondaryButton")
        self.clear_button.setToolTip("Remove this image")
        self.clear_button.setAccessibleName(f"Remove {title.lower()}")
        self.clear_button.setFixedWidth(34)
        self.clear_button.clicked.connect(self.clear_image)
        self.clear_button.setVisible(False)

        action_row = QWidget()
        action_layout = QHBoxLayout(action_row)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(6)
        action_layout.addWidget(self.browse_button, 1)
        action_layout.addWidget(self.clear_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 13, 14, 13)
        layout.setSpacing(8)
        layout.addWidget(self.title_label)
        layout.addWidget(self.preview, 1)
        layout.addWidget(self.metadata_label)
        layout.addWidget(action_row)

    @property
    def image_path(self) -> Path | None:
        return self._image_path

    def clear_image(self) -> None:
        """Remove the current image and emit a clear notification to the app."""
        self._image_path = None
        self._thumbnail = QPixmap()
        self.preview.clear()
        self.preview.setText("Drop an image here\nor choose a file")
        self.metadata_label.setObjectName("mutedText")
        self.metadata_label.setText("PNG, JPEG, BMP, TIFF, or WebP")
        self.metadata_label.style().unpolish(self.metadata_label)
        self.metadata_label.style().polish(self.metadata_label)
        self.clear_button.setVisible(False)
        self.image_changed.emit(self._title, None)

    def _browse(self) -> None:
        directory = self._image_path.parent if self._image_path else self._browse_directory
        if directory is None:
            directory = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.PicturesLocation) or Path.home())
        filename, _ = QFileDialog.getOpenFileName(self, f"Choose {self._title}", str(directory), IMAGE_FILTER)
        if filename:
            self.load_path(Path(filename))

    def set_browse_directory(self, directory: Path) -> None:
        """Share the last image folder without changing the selected image."""
        self._browse_directory = directory

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        self._accept_image_drag(event)

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        self._accept_image_drag(event)

    def _accept_image_drag(self, event: QDropEvent) -> bool:
        if not event.possibleActions() & Qt.DropAction.CopyAction or not self._dropped_image(event.mimeData().urls()):
            event.ignore()
            return False
        # Opening an image must never tell Explorer or another drag source to
        # remove its original file, even when Shift proposes a move action.
        event.setDropAction(Qt.DropAction.CopyAction)
        event.accept()
        return True

    def dropEvent(self, event: QDropEvent) -> None:
        if not self._accept_image_drag(event):
            return
        if not self.load_path(self._dropped_image(event.mimeData().urls())[0]):
            event.ignore()

    @staticmethod
    def _dropped_image(urls: list[QUrl]) -> list[Path]:
        accepted = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}
        return [Path(url.toLocalFile()) for url in urls if url.isLocalFile() and Path(url.toLocalFile()).suffix.lower() in accepted]

    def load_path(self, path: str | Path, *, preserve_previous: bool = True) -> bool:
        """Load an upright, bounded preview; a bad replacement retains the input.

        Project replay can explicitly clear missing project images rather than
        silently using an unrelated image from the previous workspace.
        """
        normalized = Path(path)
        reader = QImageReader(str(normalized))
        reader.setAutoTransform(True)
        original_size = reader.size()
        oriented_size = QSize(original_size)
        if reader.transformation() & QImageIOHandler.Transformation.TransformationRotate90:
            oriented_size.transpose()
        if original_size.isValid() and (original_size.width() > PREVIEW_LIMIT.width()
                                        or original_size.height() > PREVIEW_LIMIT.height()):
            reader.setScaledSize(original_size.scaled(PREVIEW_LIMIT, Qt.AspectRatioMode.KeepAspectRatio))
        image = reader.read()
        if image.isNull():
            if not preserve_previous or self._image_path is None:
                self.clear_image()
            recovery = ("Current image retained. Choose another file." if self._image_path is not None
                        else "Choose a supported image file.")
            self.metadata_label.setText(f"Could not read this image. {recovery}")
            self.metadata_label.setObjectName("errorText")
            self.metadata_label.style().unpolish(self.metadata_label)
            self.metadata_label.style().polish(self.metadata_label)
            logger.warning("Unable to load image for %s: %s", self._title, normalized)
            return False

        self._image_path = normalized.resolve()
        if not oriented_size.isValid():
            oriented_size = image.size()
        # Some handlers cannot decode at the requested size. Bound retained
        # memory independently of their scaled-decoding support.
        self._thumbnail = QPixmap.fromImage(image.scaled(
            PREVIEW_LIMIT, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation,
        )) if image.width() > PREVIEW_LIMIT.width() or image.height() > PREVIEW_LIMIT.height() else QPixmap.fromImage(image)
        self._update_preview()
        self.metadata_label.setObjectName("mutedText")
        self.metadata_label.setText(f"{self._image_path.name}  ·  {oriented_size.width()} × {oriented_size.height()} px")
        self.metadata_label.style().unpolish(self.metadata_label)
        self.metadata_label.style().polish(self.metadata_label)
        self.clear_button.setVisible(True)
        self.image_changed.emit(self._title, self._image_path)
        return True

    def _update_preview(self) -> None:
        if self._thumbnail.isNull():
            return
        self.preview.setPixmap(
            self._thumbnail.scaled(
                self.preview.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update_preview()
