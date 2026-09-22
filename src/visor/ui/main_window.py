"""Main application window for the initial image-input milestone."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from visor.ui.widgets.image_drop import ImageDropWidget


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("VISOR — Visual Object Registration & Analysis")
        self.setMinimumSize(1040, 680)
        self.resize(1280, 820)
        self._paths: dict[str, Path] = {}
        self._build_menu()
        self._build_workspace()
        self.setStatusBar(QStatusBar(self))
        self.statusBar().showMessage("Ready — add a reference and target image to begin.")
        self._apply_theme()

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        for title, shortcut, callback in (
            ("Open Reference…", "Ctrl+1", lambda: self.reference_input._browse()),
            ("Open Target…", "Ctrl+2", lambda: self.target_input._browse()),
        ):
            action = QAction(title, self)
            action.setShortcut(shortcut)
            action.triggered.connect(callback)
            file_menu.addAction(action)
        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        help_menu = self.menuBar().addMenu("&Help")
        about_action = QAction("About VISOR", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _build_workspace(self) -> None:
        root = QWidget()
        root.setObjectName("workspace")
        outer = QVBoxLayout(root)
        outer.setContentsMargins(22, 18, 22, 20)
        outer.setSpacing(18)

        header = QHBoxLayout()
        brand = QVBoxLayout()
        eyebrow = QLabel("VISUAL OBJECT REGISTRATION & ANALYSIS")
        eyebrow.setObjectName("eyebrow")
        heading = QLabel("Image workspace")
        heading.setObjectName("pageTitle")
        subheading = QLabel("Load a reference and a target image to prepare an analysis.")
        subheading.setObjectName("mutedText")
        brand.addWidget(eyebrow)
        brand.addWidget(heading)
        brand.addWidget(subheading)
        header.addLayout(brand)
        header.addStretch(1)
        version = QLabel("CLASSICAL FEATURES  ·  SIFT / ORB")
        version.setObjectName("badge")
        header.addWidget(version, 0, Qt.AlignmentFlag.AlignTop)
        outer.addLayout(header)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        input_panel = QWidget()
        input_panel.setObjectName("inputPanel")
        input_layout = QVBoxLayout(input_panel)
        input_layout.setContentsMargins(18, 18, 18, 18)
        input_layout.setSpacing(14)
        panel_title = QLabel("Image inputs")
        panel_title.setObjectName("sectionTitle")
        input_hint = QLabel("Drop a local image into either area, or browse to select it.")
        input_hint.setObjectName("mutedText")
        input_hint.setWordWrap(True)
        self.reference_input = ImageDropWidget("Reference image")
        self.target_input = ImageDropWidget("Target image")
        self.reference_input.image_changed.connect(self._on_image_changed)
        self.target_input.image_changed.connect(self._on_image_changed)
        input_layout.addWidget(panel_title)
        input_layout.addWidget(input_hint)
        input_layout.addWidget(self.reference_input, 1)
        input_layout.addWidget(self.target_input, 1)

        welcome = QWidget()
        welcome.setObjectName("welcomePanel")
        welcome_layout = QVBoxLayout(welcome)
        welcome_layout.setContentsMargins(28, 28, 28, 28)
        welcome_layout.addStretch(1)
        canvas_mark = QLabel("VISOR")
        canvas_mark.setObjectName("canvasMark")
        canvas_mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_layout.addWidget(canvas_mark)
        welcome_title = QLabel("Planar feature analysis")
        welcome_title.setObjectName("welcomeTitle")
        welcome_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_layout.addWidget(welcome_title)
        welcome_body = QLabel(
            "Add two images to prepare a comparison. VISOR will use local features and, when supported by the image pair, estimate a planar mapping."
        )
        welcome_body.setObjectName("mutedText")
        welcome_body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_body.setWordWrap(True)
        welcome_body.setMaximumWidth(440)
        welcome_layout.addWidget(welcome_body, 0, Qt.AlignmentFlag.AlignHCenter)
        assumption = QLabel("Homography estimates apply to planar scenes; they do not recover general 3D pose.")
        assumption.setObjectName("assumption")
        assumption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        assumption.setWordWrap(True)
        welcome_layout.addWidget(assumption, 0, Qt.AlignmentFlag.AlignHCenter)
        welcome_layout.addStretch(1)

        splitter.addWidget(input_panel)
        splitter.addWidget(welcome)
        splitter.setSizes([390, 770])
        outer.addWidget(splitter, 1)
        self.setCentralWidget(root)

    def _on_image_changed(self, role: str, path: object) -> None:
        if isinstance(path, Path):
            self._paths[role] = path
            self.statusBar().showMessage(f"Loaded {role.lower()}: {path.name}")
        else:
            self._paths.pop(role, None)
            self.statusBar().showMessage(f"Unable to load {role.lower()} image.")

    def _show_about(self) -> None:
        self.statusBar().showMessage("VISOR 0.1.0 — classical image feature registration workspace")

    def _apply_theme(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget#workspace { background: #11151b; color: #e6eaf0; }
            QMenuBar { background: #171c23; color: #cbd2dc; padding: 5px; }
            QMenuBar::item:selected, QMenu::item:selected { background: #293240; }
            QMenu { background: #1b222c; color: #e6eaf0; border: 1px solid #303947; }
            QStatusBar { background: #171c23; color: #aeb7c4; border-top: 1px solid #29313b; }
            QWidget#inputPanel, QWidget#welcomePanel { background: #171c23; border: 1px solid #29313b; border-radius: 8px; }
            QFrame#imageDropWidget { background: #1b222c; border: 1px solid #303947; border-radius: 7px; }
            QFrame#imageDropWidget:hover { border-color: #6589b8; }
            QLabel#pageTitle { font-size: 25px; font-weight: 600; color: #f2f5f8; }
            QLabel#sectionTitle { font-size: 15px; font-weight: 600; color: #e6eaf0; }
            QLabel#eyebrow { font-size: 10px; letter-spacing: 1.5px; color: #8394aa; }
            QLabel#mutedText { color: #929eae; }
            QLabel#errorText { color: #f08b86; }
            QLabel#imagePreview { color: #758396; background: #141920; border: 1px dashed #394555; border-radius: 5px; }
            QLabel#badge { color: #aebfd4; background: #222c39; border: 1px solid #344355; border-radius: 4px; padding: 7px 9px; font-size: 10px; }
            QLabel#canvasMark { color: #52769e; font-size: 44px; font-weight: 700; letter-spacing: 5px; }
            QLabel#welcomeTitle { color: #e7ebf1; font-size: 20px; font-weight: 600; padding: 8px; }
            QLabel#assumption { color: #8290a2; font-size: 11px; padding-top: 18px; }
            QPushButton#secondaryButton { color: #dce3ec; background: #293545; border: 1px solid #3c4c61; border-radius: 5px; padding: 8px; }
            QPushButton#secondaryButton:hover { background: #34465c; }
            QSplitter::handle { background: #11151b; width: 10px; }
            """
        )

