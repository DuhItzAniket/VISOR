"""Engine availability status dialog.

Shows each engine's availability, required packages, and install commands.
Accessible from Help menu or when a disabled engine is selected.
"""

from __future__ import annotations

import sys
from typing import NamedTuple

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class EngineEntry(NamedTuple):
    name: str
    available: bool
    category: str          # "Classical" | "Learned" | "Classical (optional)"
    requires: str          # human-readable dependency description
    install_cmd: str       # pip command to install, or "" if built-in


def _collect_entries() -> list[EngineEntry]:
    from visor.learned_engines import is_lightglue_available, is_xfeat_available
    from visor.model_runtime import LIGHTGLUE_REQUIREMENT

    entries: list[EngineEntry] = []

    # Classical built-ins — always available
    entries.append(EngineEntry("SIFT", True, "Classical", "opencv-contrib-python (installed)", ""))
    entries.append(EngineEntry("ORB", True, "Classical", "opencv-contrib-python (installed)", ""))

    # Classical optional — depend on OpenCV build
    try:
        import cv2
        akaze_ok = hasattr(cv2, "AKAZE_create")
        brisk_ok = hasattr(cv2, "BRISK_create")
    except ImportError:
        akaze_ok = brisk_ok = False

    entries.append(EngineEntry(
        "AKAZE", akaze_ok, "Classical (optional)",
        "OpenCV build with AKAZE support",
        "pip install opencv-contrib-python" if not akaze_ok else "",
    ))
    entries.append(EngineEntry(
        "BRISK", brisk_ok, "Classical (optional)",
        "OpenCV build with BRISK support",
        "pip install opencv-contrib-python" if not brisk_ok else "",
    ))

    # Learned — LightGlue family
    lg_ok = is_lightglue_available()
    lg_cmd = f"python -m pip install {LIGHTGLUE_REQUIREMENT}"
    for name in ("SuperPoint+LightGlue", "ALIKED+LightGlue", "DISK+LightGlue", "SIFT+LightGlue"):
        entries.append(EngineEntry(
            name, lg_ok, "Learned",
            "torch + lightglue",
            "" if lg_ok else lg_cmd,
        ))

    # XFeat
    xf_ok = is_xfeat_available()

    entries.append(EngineEntry(
        "XFeat", xf_ok, "Learned",
        "torch + tqdm + pinned source/weights cache",
        "" if xf_ok else "python -m visor.model_setup --xfeat",
    ))

    return entries


class EngineStatusDialog(QDialog):
    """Read-only dialog listing every engine with its availability and install command."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Engine Availability")
        self.setMinimumWidth(680)
        self.setMinimumHeight(420)
        self._build()

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 16, 18, 16)
        outer.setSpacing(10)

        frozen = getattr(sys, "frozen", False)
        if frozen:
            note = QLabel(
                "This desktop distribution includes SIFT and ORB. "
                "Additional learned engines are unavailable in this build."
            )
            note.setWordWrap(True)
            note.setObjectName("mutedText")
            outer.addWidget(note)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(scroll_area.Shape.NoFrame)
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(6)
        container_layout.setContentsMargins(0, 0, 0, 0)

        entries = _collect_entries()
        if frozen:
            entries = [entry._replace(available=False, install_cmd="") if entry.category == "Learned"
                       else entry._replace(install_cmd="") for entry in entries]
        current_category = ""
        for entry in entries:
            if entry.category != current_category:
                current_category = entry.category
                cat_label = QLabel(current_category)
                cat_label.setObjectName("sectionTitle")
                container_layout.addWidget(cat_label)

            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(8, 4, 8, 4)
            row_layout.setSpacing(10)

            status = "✓" if entry.available else "✗"
            status_label = QLabel(status)
            status_label.setFixedWidth(18)
            status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            status_label.setStyleSheet(
                "color: #5cb85c; font-weight: bold;" if entry.available
                else "color: #d9534f; font-weight: bold;"
            )

            name_label = QLabel(entry.name)
            name_label.setFixedWidth(200)

            req_label = QLabel(entry.requires)
            req_label.setObjectName("mutedText")
            req_label.setWordWrap(False)

            row_layout.addWidget(status_label)
            row_layout.addWidget(name_label)
            row_layout.addWidget(req_label, 1)

            if entry.install_cmd:
                copy_btn = QPushButton("Copy install cmd")
                copy_btn.setObjectName("secondaryButton")
                copy_btn.setFixedWidth(140)
                cmd = entry.install_cmd
                copy_btn.clicked.connect(lambda _=False, c=cmd: self._copy(c))
                row_layout.addWidget(copy_btn)

            container_layout.addWidget(row)

        container_layout.addStretch(1)
        scroll_area.setWidget(container)
        outer.addWidget(scroll_area)

        close_btn = QPushButton("Close")
        close_btn.setObjectName("secondaryButton")
        close_btn.clicked.connect(self.accept)
        outer.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignRight)

    @staticmethod
    def _copy(text: str) -> None:
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(text)
