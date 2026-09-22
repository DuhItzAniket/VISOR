"""Main application window for the initial image-input milestone."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QAction, QImage, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDockWidget,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from visor.models import AnalysisResult, EngineName
from visor.pipeline import analyze
from visor.ui.widgets.image_drop import ImageDropWidget


class AnalysisWorker(QThread):
    completed = Signal(object)
    failed = Signal(str)

    def __init__(self, reference: Path, target: Path, engine: EngineName) -> None:
        super().__init__()
        self.reference = reference
        self.target = target
        self.engine = engine

    def run(self) -> None:
        try:
            self.completed.emit(analyze(self.reference, self.target, self.engine))
        except Exception as exc:
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("VISOR — Visual Object Registration & Analysis")
        self.setMinimumSize(1040, 680)
        self.resize(1280, 820)
        self._paths: dict[str, Path] = {}
        self._worker: AnalysisWorker | None = None
        self._result_arrays: dict[QLabel, object] = {}
        self._build_menu()
        self._build_workspace()
        self._build_details_dock()
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

        analysis_menu = self.menuBar().addMenu("&Analysis")
        run_action = QAction("Run Analysis", self)
        run_action.setShortcut("F5")
        run_action.triggered.connect(self._start_analysis)
        analysis_menu.addAction(run_action)

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
        self.engine_selector = QComboBox()
        self.engine_selector.addItems(["SIFT", "ORB"])
        self.engine_selector.setToolTip("Feature extraction and descriptor matching engine")
        header.addWidget(self.engine_selector, 0, Qt.AlignmentFlag.AlignTop)
        self.run_button = QPushButton("Run analysis")
        self.run_button.setObjectName("primaryButton")
        self.run_button.setEnabled(False)
        self.run_button.clicked.connect(self._start_analysis)
        header.addWidget(self.run_button, 0, Qt.AlignmentFlag.AlignTop)
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

        self.result_tabs = QTabWidget()
        self.result_tabs.addTab(welcome, "Overview")
        self.matches_view = self._image_view("Run an analysis to inspect feature correspondences.")
        self.localization_view = self._image_view("A projected reference outline appears when a valid planar mapping is found.")
        self.warped_view = self._image_view("Rectified view is available after a valid homography.")
        self.result_tabs.addTab(self.matches_view, "Feature Matches")
        self.result_tabs.addTab(self.localization_view, "Localization")
        self.result_tabs.addTab(self.warped_view, "Warped / Rectified")
        splitter.addWidget(input_panel)
        splitter.addWidget(self.result_tabs)
        splitter.setSizes([390, 770])
        outer.addWidget(splitter, 1)
        self.setCentralWidget(root)

    @staticmethod
    def _image_view(message: str) -> QLabel:
        view = QLabel(message)
        view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        view.setWordWrap(True)
        view.setMinimumSize(300, 240)
        view.setObjectName("resultImage")
        return view

    def _build_details_dock(self) -> None:
        dock = QDockWidget("Analysis Details", self)
        dock.setObjectName("analysisDetailsDock")
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setPlaceholderText("Run an analysis to see engine, matching, geometry, and timing details.")
        dock.setWidget(self.details_text)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
        dock.setMinimumWidth(275)

    def _start_analysis(self) -> None:
        reference = self._paths.get("Reference image")
        target = self._paths.get("Target image")
        if reference is None or target is None or self._worker is not None:
            return
        engine = EngineName(self.engine_selector.currentText())
        self.run_button.setEnabled(False)
        self.statusBar().showMessage(f"Running {engine} feature analysis…")
        self._worker = AnalysisWorker(reference, target, engine)
        self._worker.completed.connect(self._show_result)
        self._worker.failed.connect(self._show_error)
        self._worker.finished.connect(self._worker_finished)
        self._worker.start()

    def _worker_finished(self) -> None:
        self._worker = None
        self.run_button.setEnabled("Reference image" in self._paths and "Target image" in self._paths)

    def _show_error(self, message: str) -> None:
        self.statusBar().showMessage(f"Analysis failed: {message}")
        self.details_text.setPlainText(f"Analysis could not be completed.\n\n{message}")

    def _show_result(self, result: AnalysisResult) -> None:
        self._result_arrays = {
            self.matches_view: result.matches_image,
            self.localization_view: result.localization_image,
        }
        self._refresh_result_views()
        if result.warped_image is not None:
            self._result_arrays[self.warped_view] = result.warped_image
            self._refresh_one_view(self.warped_view)
        else:
            self._result_arrays.pop(self.warped_view, None)
            self.warped_view.setPixmap(QPixmap())
            self.warped_view.setText("Rectified view is unavailable because no valid homography was found.")
        ref = result.reference_features
        target = result.target_features
        g = result.geometry
        p = result.performance
        corners = "\n".join(f"  {name}: ({x:.1f}, {y:.1f}) px" for name, (x, y) in zip(("Top-left", "Top-right", "Bottom-right", "Bottom-left"), g.projected_corners)) or "  Unavailable"
        reprojection = f"{g.reprojection_error_px:.2f} px" if g.reprojection_error_px is not None else "unavailable"
        self.details_text.setPlainText(
            f"{result.engine} ENGINE\n"
            f"Reference keypoints: {len(ref.keypoints):,}\nTarget keypoints: {len(target.keypoints):,}\n"
            f"Descriptor: {ref.descriptor_info.dimensions} dimensions · {ref.descriptor_info.dtype} · {ref.descriptor_info.distance}\n\n"
            f"MATCHING\nMatcher: {result.match_set.matcher}\nFilter: {result.match_set.filter_name} ({result.match_set.threshold:.2f})\n"
            f"KNN candidate pairs: {result.match_set.candidate_count:,}\nGood matches: {result.match_set.good_count:,}\n\n"
            f"GEOMETRY\nStatus: {g.message}\nInliers: {g.inlier_count:,} · Outliers: {g.outlier_count:,}\n"
            f"Inlier ratio: {g.inlier_ratio:.1%}\nMean inlier reprojection error: {reprojection}\n"
        )
        # Replace the compact initial geometry block with complete location and timing details.
        self.details_text.append(
            f"Projected corners:\n{corners}\n\nPERFORMANCE\n"
            f"Extraction reference: {p.extraction_reference_ms:.1f} ms\n"
            f"Extraction target: {p.extraction_target_ms:.1f} ms\nMatching: {p.matching_ms:.1f} ms\n"
            f"Geometry: {p.geometry_ms:.1f} ms\nTotal: {p.total_ms:.1f} ms\n\n"
            "Geometry values are image-space estimates under a planar homography assumption."
        )
        self.statusBar().showMessage(
            f"{result.engine} complete — {len(ref.keypoints):,}/{len(target.keypoints):,} keypoints, "
            f"{result.match_set.good_count:,} good matches, {g.inlier_count:,} inliers · {p.total_ms:.0f} ms"
        )

    def _refresh_result_views(self) -> None:
        for label in self._result_arrays:
            self._refresh_one_view(label)

    def _refresh_one_view(self, label: QLabel) -> None:
        image = self._result_arrays.get(label)
        if image is None:
            return
        rgb = image[:, :, ::-1].copy()
        height, width, _ = rgb.shape
        qimage = QImage(rgb.data, width, height, 3 * width, QImage.Format.Format_RGB888).copy()
        label.setPixmap(QPixmap.fromImage(qimage).scaled(
            label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation,
        ))
        label.setText("")

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._refresh_result_views()

    def _on_image_changed(self, role: str, path: object) -> None:
        if isinstance(path, Path):
            self._paths[role] = path
            self.statusBar().showMessage(f"Loaded {role.lower()}: {path.name}")
        else:
            self._paths.pop(role, None)
            self.statusBar().showMessage(f"Unable to load {role.lower()} image.")
        if hasattr(self, "run_button"):
            self.run_button.setEnabled("Reference image" in self._paths and "Target image" in self._paths and self._worker is None)

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
            QPushButton#primaryButton { color: #f1f6fc; background: #356ba5; border: 1px solid #477fb9; border-radius: 5px; padding: 8px 14px; font-weight: 600; }
            QPushButton#primaryButton:hover { background: #407bb8; }
            QPushButton#primaryButton:disabled { color: #788493; background: #27303b; border-color: #333d49; }
            QComboBox { color: #dce3ec; background: #202a36; border: 1px solid #3c4c61; border-radius: 5px; padding: 7px 9px; }
            QTabWidget::pane { border: 1px solid #29313b; background: #171c23; }
            QTabBar::tab { color: #aeb7c4; background: #1b222c; padding: 8px 14px; border: 1px solid #29313b; }
            QTabBar::tab:selected { color: #edf2f8; background: #293545; }
            QLabel#resultImage { background: #141920; color: #8290a2; }
            QDockWidget { color: #dce3ec; }
            QTextEdit { color: #c8d1dd; background: #171c23; border: 1px solid #29313b; font-family: Consolas; font-size: 11px; }
            QSplitter::handle { background: #11151b; width: 10px; }
            """
        )
