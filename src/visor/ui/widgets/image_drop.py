"""Image input widget with native picker and drag-and-drop support."""

from __future__ import annotations

import logging
from pathlib import Path
from threading import Event

from PySide6.QtCore import QStandardPaths, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent, QPixmap
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

from visor.ui.image_loader import DecodedPreview, PreviewLoader, PreviewRequest, decode_preview

logger = logging.getLogger(__name__)
IMAGE_FILTER = "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp);;All files (*.*)"


class ImageDropWidget(QFrame):
    """A labeled image slot that accepts local image files by drop or picker."""

    image_changed = Signal(str, object)
    image_load_failed = Signal(str, str)
    image_load_started = Signal(str)
    loading_changed = Signal(bool)
    loading_cancelled = Signal(str)
    loading_idle = Signal()

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
        self._loader = PreviewLoader(self)
        self._loader.completed.connect(self._apply_preview)
        self._loader.failed.connect(self._load_failed)
        self._loader.busy_changed.connect(self.loading_changed.emit)
        self._loader.idle.connect(self._loading_finished)
        self._cancel_requested = False
        self._closing_requested = False
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
        self._loader.cancel()
        self._cancel_requested = False
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
            self.request_path(Path(filename))

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
        # Acceptance acknowledges a queued open request, not a completed decode.
        if not self.request_path(self._dropped_image(event.mimeData().urls())[0]):
            event.ignore()

    @staticmethod
    def _dropped_image(urls: list[QUrl]) -> list[Path]:
        accepted = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}
        return [Path(url.toLocalFile()) for url in urls if url.isLocalFile() and Path(url.toLocalFile()).suffix.lower() in accepted]

    @property
    def loading(self) -> bool:
        return self._loader.busy

    def request_path(self, path: str | Path, *, preserve_previous: bool = True) -> bool:
        """Queue a user selection; only the latest successful decode is applied."""
        request = PreviewRequest(Path(path), preserve_previous)
        if not self._loader.request(request):
            return False
        self.image_load_started.emit(self._title)
        self._cancel_requested = False
        self._set_metadata(f"Loading {request.path.name}…")
        self.clear_button.setVisible(True)
        return True

    def cancel_loading(self) -> None:
        self._cancel_requested = self.loading
        self._loader.cancel()
        if self.loading:
            self._set_metadata("Cancellation requested; waiting for the image decoder…")

    def shutdown(self) -> None:
        self._loader.shutdown()

    def _loading_finished(self) -> None:
        if self._cancel_requested:
            retained = " Current image retained." if self._image_path is not None else " Choose an image."
            self._set_metadata(f"Image loading cancelled.{retained}")
            self.clear_button.setVisible(self._image_path is not None)
            self.loading_cancelled.emit(self._title)
        self.loading_idle.emit()
        if self._closing_requested:
            QTimer.singleShot(0, self.close)

    def closeEvent(self, event) -> None:
        self._closing_requested = True
        self.shutdown()
        if self.loading:
            event.ignore()
            return
        super().closeEvent(event)

    def load_path(self, path: str | Path, *, preserve_previous: bool = True) -> bool:
        """Synchronous helper for controlled checks; user workflows use request_path."""
        self._loader.cancel()
        request = PreviewRequest(Path(path), preserve_previous)
        try:
            preview = decode_preview(request, Event())
        except (OSError, ValueError) as exc:
            self._load_failed(request, str(exc))
            return False
        self._apply_preview(preview)
        return True

    def _load_failed(self, request: PreviewRequest, message: str) -> None:
        if not request.preserve_previous or self._image_path is None:
            self.clear_image()
        recovery = ("Current image retained. Choose another file." if self._image_path is not None
                    else "Choose a supported image file.")
        self._set_metadata(f"Could not read this image. {recovery}", error=True)
        self.clear_button.setVisible(self._image_path is not None)
        logger.warning("Unable to load image for %s: %s (%s)", self._title, request.path, message)
        self.image_load_failed.emit(self._title, recovery)

    def _apply_preview(self, preview: DecodedPreview) -> None:
        self._image_path = preview.request.path
        self._thumbnail = QPixmap.fromImage(preview.image)
        self._update_preview()
        size = preview.original_size
        self._set_metadata(f"{self._image_path.name}  ·  {size.width()} × {size.height()} px")
        self.clear_button.setVisible(True)
        self.image_changed.emit(self._title, self._image_path)

    def _set_metadata(self, text: str, *, error: bool = False) -> None:
        self.metadata_label.setObjectName("errorText" if error else "mutedText")
        self.metadata_label.setText(text)
        self.metadata_label.style().unpolish(self.metadata_label)
        self.metadata_label.style().polish(self.metadata_label)

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
