"""Main application window."""

from __future__ import annotations

import math
from dataclasses import replace
from pathlib import Path
from threading import Event
from typing import cast

import numpy as np
from PySide6.QtCore import QByteArray, QSettings, Qt, QThread, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDockWidget,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from visor.benchmark import BenchmarkReport, run_benchmark
from visor.engines import ORBConfiguration, SIFTConfiguration
from visor.exporting import (
    ProjectSession,
    export_benchmark_csv,
    export_comparison_csv,
    export_csv,
    export_json,
    export_visualization,
    load_project,
    save_project,
)
from visor.models import AnalysisResult, AnalysisSettings, ComparisonResult, EngineName
from visor.pipeline import AnalysisCancelled, analyze, compare_engines
from visor.ui.widgets.details_panel import AnalysisDetailsPanel
from visor.ui.widgets.image_canvas import ImageCanvas
from visor.ui.widgets.image_drop import ImageDropWidget
from visor.visualization import render_localization, render_match_canvas

_ICONS_DIR = Path(__file__).parent.parent / "assets" / "icons"


def _icon(name: str) -> QIcon:
    # Support both normal install and PyInstaller one-folder bundle.
    import sys
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent.parent))
    path = base / "assets" / "icons" / f"{name}.svg"
    if not path.exists():
        path = _ICONS_DIR / f"{name}.svg"
    return QIcon(str(path)) if path.exists() else QIcon()


class AnalysisWorker(QThread):
    completed = Signal(object)
    failed = Signal(str)
    cancelled = Signal()

    def __init__(
        self, reference: Path, target: Path, engine: EngineName,
        settings: AnalysisSettings, sift: SIFTConfiguration, orb: ORBConfiguration,
        cancel_event: Event,
    ) -> None:
        super().__init__()
        self.reference = reference
        self.target = target
        self.engine = engine
        self.settings = settings
        self.sift = sift
        self.orb = orb
        self.cancel_event = cancel_event

    def run(self) -> None:
        try:
            self.completed.emit(analyze(self.reference, self.target, self.engine, self.settings, self.sift, self.orb, self.cancel_event))
        except AnalysisCancelled:
            self.cancelled.emit()
        except Exception as exc:  # noqa: BLE001 — keep worker failures on the UI thread
            self.failed.emit(str(exc))


class ComparisonWorker(QThread):
    completed = Signal(object)
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, reference: Path, target: Path, settings: AnalysisSettings,
                 sift: SIFTConfiguration, orb: ORBConfiguration, cancel_event: Event) -> None:
        super().__init__()
        self.reference, self.target = reference, target
        self.settings, self.sift, self.orb = settings, sift, orb
        self.cancel_event = cancel_event

    def run(self) -> None:
        try:
            self.completed.emit(compare_engines(self.reference, self.target, self.settings, self.sift, self.orb, self.cancel_event))
        except AnalysisCancelled:
            self.cancelled.emit()
        except Exception as exc:  # noqa: BLE001 — keep worker failures on the UI thread
            self.failed.emit(str(exc))


class BenchmarkWorker(QThread):
    completed = Signal(object)
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, reference: Path, settings: AnalysisSettings,
                 sift: SIFTConfiguration, orb: ORBConfiguration, cancel_event: Event) -> None:
        super().__init__()
        self.reference, self.settings, self.sift, self.orb = reference, settings, sift, orb
        self.cancel_event = cancel_event

    def run(self) -> None:
        try:
            self.completed.emit(run_benchmark(self.reference, ("SIFT", "ORB"), self.settings, self.sift, self.orb, self.cancel_event))
        except AnalysisCancelled:
            self.cancelled.emit()
        except Exception as exc:  # noqa: BLE001 — keep worker failures on the UI thread
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("VISOR — Visual Object Registration & Analysis")
        self.setMinimumSize(1040, 680)
        self.resize(1280, 820)
        self._paths: dict[str, Path] = {}
        self._worker: QThread | None = None
        self._cancel_event: Event | None = None
        self._result_arrays: dict[ImageCanvas, np.ndarray] = {}
        self._latest_result: AnalysisResult | None = None
        self._latest_comparison: ComparisonResult | None = None
        self._latest_benchmark: BenchmarkReport | None = None
        self._default_window_state: QByteArray | None = None
        self._build_menu()
        self._build_toolbar()
        self._build_workspace()
        self._build_details_dock()
        self.setStatusBar(QStatusBar(self))
        window_menu = self.window_menu
        window_menu.addAction(self.details_dock.toggleViewAction())
        reset_action = QAction("Reset layout", self)
        reset_action.triggered.connect(self._reset_layout)
        window_menu.addAction(reset_action)
        self._default_window_state = self.saveState()
        self._window_settings = QSettings("VISOR", "VISOR")
        self._restore_window_settings()
        self.statusBar().showMessage("Ready — add a reference and target image to begin.")
        self._apply_theme()

    def _build_toolbar(self) -> None:
        tb = QToolBar("Main toolbar", self)
        tb.setObjectName("mainToolbar")
        tb.setMovable(False)
        tb.setIconSize(__import__("PySide6.QtCore", fromlist=["QSize"]).QSize(20, 20))
        self.addToolBar(tb)
        for icon_name, label, shortcut, slot in (
            ("open_reference", "Open Reference", "Ctrl+1", lambda: self.reference_input._browse()),
            ("open_target", "Open Target", "Ctrl+2", lambda: self.target_input._browse()),
            ("run", "Run Analysis", "F5", self._start_analysis),
            ("compare", "Compare SIFT / ORB", "", self._start_comparison),
            ("benchmark", "Benchmark", "", self._start_benchmark),
            ("cancel", "Cancel", "", self._cancel_running),
            ("export", "Export", "", self._export_visualization),
            ("fit_view", "Fit View", "0", self._fit_images),
        ):
            action = QAction(_icon(icon_name), label, self)
            action.setToolTip(label)
            if shortcut:
                action.setShortcut(shortcut)
            action.triggered.connect(slot)
            tb.addAction(action)
            setattr(self, f"_tb_{icon_name.replace('-', '_')}", action)

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
        for title, shortcut, callback in (
            ("Open Project…", "Ctrl+O", self._load_project),
            ("Save Project…", "Ctrl+S", self._save_project),
        ):
            action = QAction(title, self)
            action.setShortcut(shortcut)
            action.triggered.connect(callback)
            file_menu.addAction(action)
        export_menu = file_menu.addMenu("Export")
        for title, callback in (
            ("Analysis as JSON…", self._export_json),
            ("Metrics as CSV…", self._export_csv),
            ("SIFT vs ORB comparison CSV…", self._export_comparison_csv),
            ("Benchmark results CSV…", self._export_benchmark_csv),
            ("Current visualization…", self._export_visualization),
        ):
            action = QAction(title, self)
            action.triggered.connect(callback)
            export_menu.addAction(action)
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
        benchmark_action = QAction("Benchmark Lab", self)
        benchmark_action.triggered.connect(self._start_benchmark)
        analysis_menu.addAction(benchmark_action)

        view_menu = self.menuBar().addMenu("&View")
        self.view_toggles = {}
        for title, setting_name, checked in (
            ("Match lines", "show_match_lines", True),
            ("Inliers", "show_inliers", True),
            ("Outliers", "show_outliers", True),
            ("Keypoints", "show_keypoints", False),
            ("Localization geometry", "show_geometry", True),
        ):
            action = QAction(title, self)
            action.setCheckable(True)
            action.setChecked(checked)
            action.toggled.connect(self._refresh_visualization)
            view_menu.addAction(action)
            self.view_toggles[setting_name] = action
        view_menu.addSeparator()
        fit_action = QAction("Fit images to view", self)
        fit_action.setShortcut("0")
        fit_action.triggered.connect(self._fit_images)
        view_menu.addAction(fit_action)

        tools_menu = self.menuBar().addMenu("&Tools")
        preset_action = QAction("Restore algorithm defaults", self)
        preset_action.triggered.connect(self._reset_configuration)
        tools_menu.addAction(preset_action)

        self.window_menu = self.menuBar().addMenu("&Window")

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
        self.engine_selector.currentIndexChanged.connect(self._engine_changed)
        header.addWidget(self.engine_selector, 0, Qt.AlignmentFlag.AlignTop)
        self.run_button = QPushButton("Run analysis")
        self.run_button.setObjectName("primaryButton")
        self.run_button.setEnabled(False)
        self.run_button.clicked.connect(self._start_analysis)
        header.addWidget(self.run_button, 0, Qt.AlignmentFlag.AlignTop)
        self.compare_button = QPushButton("Compare SIFT / ORB")
        self.compare_button.setObjectName("secondaryButton")
        self.compare_button.setEnabled(False)
        self.compare_button.clicked.connect(self._start_comparison)
        header.addWidget(self.compare_button, 0, Qt.AlignmentFlag.AlignTop)
        self.benchmark_button = QPushButton("Benchmark")
        self.benchmark_button.setObjectName("secondaryButton")
        self.benchmark_button.setEnabled(False)
        self.benchmark_button.clicked.connect(self._start_benchmark)
        header.addWidget(self.benchmark_button, 0, Qt.AlignmentFlag.AlignTop)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setObjectName("secondaryButton")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self._cancel_running)
        header.addWidget(self.cancel_button, 0, Qt.AlignmentFlag.AlignTop)
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

    def _image_view(self, message: str) -> ImageCanvas:
        view = ImageCanvas(message)
        view.setMinimumSize(300, 240)
        view.cursor_position.connect(
            lambda x, y: self.statusBar().showMessage(f"Image coordinate: ({x:.1f}, {y:.1f}) px")
        )
        return view

    def _build_details_dock(self) -> None:
        dock = QDockWidget("Analysis Details", self)
        dock.setObjectName("analysisDetailsDock")
        self.details_panel = AnalysisDetailsPanel()
        self.details_tabs = QTabWidget()
        self.details_tabs.addTab(self.details_panel, "Results")
        self.details_tabs.addTab(self._configuration_panel(), "Parameters")
        dock.setWidget(self.details_tabs)
        self.details_dock = dock
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
        dock.setMinimumWidth(300)
        self.localization_view.image_clicked.connect(self._inspect_keypoint)

    @staticmethod
    def _int_control(minimum: int, maximum: int, value: int) -> QSpinBox:
        field = QSpinBox()
        field.setRange(minimum, maximum)
        field.setValue(value)
        return field

    @staticmethod
    def _float_control(minimum: float, maximum: float, value: float, decimals: int = 2) -> QDoubleSpinBox:
        field = QDoubleSpinBox()
        field.setRange(minimum, maximum)
        field.setDecimals(decimals)
        field.setSingleStep(0.01 if decimals > 1 else 0.1)
        field.setValue(value)
        return field

    def _configuration_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        common = QGroupBox("Matching and geometry")
        common_form = QFormLayout(common)
        self.ratio_control = self._float_control(0.50, 0.99, 0.75)
        self.ransac_control = self._float_control(0.5, 20.0, 4.0)
        common_form.addRow("Ratio threshold", self.ratio_control)
        common_form.addRow("RANSAC threshold (px)", self.ransac_control)
        layout.addWidget(common)

        self.engine_settings = QStackedWidget()
        sift_panel = QWidget()
        sift_form = QFormLayout(sift_panel)
        self.sift_features = self._int_control(0, 100000, 0)
        self.sift_layers = self._int_control(1, 10, 3)
        self.sift_contrast = self._float_control(0.001, 1.0, 0.04, 3)
        self.sift_edge = self._float_control(1.0, 100.0, 10.0)
        self.sift_sigma = self._float_control(0.1, 10.0, 1.6)
        sift_form.addRow("Max features (0 = all)", self.sift_features)
        sift_form.addRow("Octave layers", self.sift_layers)
        sift_form.addRow("Contrast threshold", self.sift_contrast)
        sift_form.addRow("Edge threshold", self.sift_edge)
        sift_form.addRow("Sigma", self.sift_sigma)
        orb_panel = QWidget()
        orb_form = QFormLayout(orb_panel)
        self.orb_features = self._int_control(100, 50000, 1500)
        self.orb_scale = self._float_control(1.01, 2.0, 1.2)
        self.orb_levels = self._int_control(1, 32, 8)
        self.orb_edge = self._int_control(0, 128, 31)
        self.orb_first_level = self._int_control(0, 10, 0)
        self.orb_wta = QComboBox()
        self.orb_wta.addItems(["2", "3", "4"])
        self.orb_score = QComboBox()
        self.orb_score.addItems(["HARRIS", "FAST"])
        self.orb_patch = self._int_control(2, 100, 31)
        self.orb_fast = self._int_control(0, 255, 20)
        for label, control in (("Max features", self.orb_features), ("Scale factor", self.orb_scale),
                               ("Pyramid levels", self.orb_levels), ("Edge threshold", self.orb_edge),
                               ("First level", self.orb_first_level), ("WTA_K", self.orb_wta),
                               ("Score type", self.orb_score), ("Patch size", self.orb_patch),
                               ("FAST threshold", self.orb_fast)):
            orb_form.addRow(label, control)
        self.engine_settings.addWidget(sift_panel)
        self.engine_settings.addWidget(orb_panel)
        layout.addWidget(self.engine_settings)
        layout.addStretch(1)
        return panel

    def _engine_changed(self, index: int) -> None:
        if hasattr(self, "engine_settings"):
            self.engine_settings.setCurrentIndex(index)

    def _reset_configuration(self) -> None:
        self.ratio_control.setValue(0.75)
        self.ransac_control.setValue(4.0)
        self.sift_features.setValue(0)
        self.sift_layers.setValue(3)
        self.sift_contrast.setValue(0.04)
        self.sift_edge.setValue(10.0)
        self.sift_sigma.setValue(1.6)
        self.orb_features.setValue(1500)
        self.orb_scale.setValue(1.2)
        self.orb_levels.setValue(8)
        self.orb_edge.setValue(31)
        self.orb_first_level.setValue(0)
        self.orb_wta.setCurrentText("2")
        self.orb_score.setCurrentText("HARRIS")
        self.orb_patch.setValue(31)
        self.orb_fast.setValue(20)
        self.statusBar().showMessage("SIFT, ORB, matching, and geometry parameters restored to defaults.")

    def _read_configurations(self) -> tuple[AnalysisSettings, SIFTConfiguration, ORBConfiguration]:
        settings = AnalysisSettings(
            self.ratio_control.value(), self.ransac_control.value(),
            self.view_toggles["show_match_lines"].isChecked(),
            self.view_toggles["show_inliers"].isChecked(),
            self.view_toggles["show_outliers"].isChecked(),
            self.view_toggles["show_keypoints"].isChecked(),
            self.view_toggles["show_geometry"].isChecked(),
        )
        sift = SIFTConfiguration(
            self.sift_features.value(), self.sift_layers.value(), self.sift_contrast.value(),
            self.sift_edge.value(), self.sift_sigma.value(),
        )
        orb = ORBConfiguration(
            self.orb_features.value(), self.orb_scale.value(), self.orb_levels.value(),
            self.orb_edge.value(), self.orb_first_level.value(), int(self.orb_wta.currentText()),
            self.orb_score.currentText(), self.orb_patch.value(), self.orb_fast.value(),
        )
        return settings, sift, orb

    def _start_analysis(self) -> None:
        reference = self._paths.get("Reference image")
        target = self._paths.get("Target image")
        if reference is None or target is None or self._worker is not None:
            return
        engine = cast(EngineName, self.engine_selector.currentText())
        settings, sift, orb = self._read_configurations()
        self.run_button.setEnabled(False)
        self.compare_button.setEnabled(False)
        self.benchmark_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.statusBar().showMessage(f"Running {engine} feature analysis…")
        self._cancel_event = Event()
        self._worker = AnalysisWorker(reference, target, engine, settings, sift, orb, self._cancel_event)
        self._worker.completed.connect(self._show_result)
        self._worker.failed.connect(self._show_error)
        self._worker.cancelled.connect(self._show_cancelled)
        self._worker.finished.connect(self._worker_finished)
        self._worker.start()

    def _start_comparison(self) -> None:
        reference = self._paths.get("Reference image")
        target = self._paths.get("Target image")
        if reference is None or target is None or self._worker is not None:
            return
        settings, sift, orb = self._read_configurations()
        self.run_button.setEnabled(False)
        self.compare_button.setEnabled(False)
        self.benchmark_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.statusBar().showMessage("Comparing SIFT and ORB on the same image pair…")
        self._cancel_event = Event()
        self._worker = ComparisonWorker(reference, target, settings, sift, orb, self._cancel_event)
        self._worker.completed.connect(self._show_comparison)
        self._worker.failed.connect(self._show_error)
        self._worker.cancelled.connect(self._show_cancelled)
        self._worker.finished.connect(self._worker_finished)
        self._worker.start()

    def _worker_finished(self) -> None:
        self._worker = None
        ready = "Reference image" in self._paths and "Target image" in self._paths
        self.run_button.setEnabled(ready)
        self.compare_button.setEnabled(ready)
        self.benchmark_button.setEnabled("Reference image" in self._paths)
        self.cancel_button.setEnabled(False)
        self._cancel_event = None

    def _show_error(self, message: str) -> None:
        self.statusBar().showMessage(f"Analysis failed: {message}")
        self.details_text.setPlainText(f"Analysis could not be completed.\n\n{message}")

    def _show_cancelled(self) -> None:
        self.statusBar().showMessage("Analysis cancelled at a safe processing boundary.")

    def _cancel_running(self) -> None:
        if self._cancel_event is not None:
            self._cancel_event.set()
            self.cancel_button.setEnabled(False)
            self.statusBar().showMessage("Cancellation requested; waiting for the active OpenCV operation to finish…")

    def _show_result(self, result: AnalysisResult) -> None:
        self._latest_result = result
        self._latest_comparison = None
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
            self.warped_view.set_placeholder("Rectified view is unavailable because no valid homography was found.")
        self.details_panel.populate(result)
        self.details_tabs.setCurrentIndex(0)
        ref = result.reference_features
        target = result.target_features
        g = result.geometry
        p = result.performance
        self.statusBar().showMessage(
            f"{result.engine} complete — {len(ref.keypoints):,}/{len(target.keypoints):,} keypoints, "
            f"{result.match_set.good_count:,} good matches, {g.inlier_count:,} inliers · {p.total_ms:.0f} ms"
        )

    def _show_comparison(self, comparison: ComparisonResult) -> None:
        self._show_result(comparison.orb)
        self.details_panel.populate_comparison(comparison)
        self.details_tabs.setCurrentIndex(0)
        self._latest_comparison = comparison
        sift, orb = comparison.sift, comparison.orb
        self.statusBar().showMessage(
            f"Comparison complete — SIFT {sift.geometry.inlier_count} inliers/{sift.performance.total_ms:.0f} ms; "
            f"ORB {orb.geometry.inlier_count} inliers/{orb.performance.total_ms:.0f} ms"
        )

    def _start_benchmark(self) -> None:
        reference = self._paths.get("Reference image")
        if reference is None or self._worker is not None:
            self.statusBar().showMessage("Load a reference image before running the benchmark lab.")
            return
        settings, sift, orb = self._read_configurations()
        self.run_button.setEnabled(False)
        self.compare_button.setEnabled(False)
        self.benchmark_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.statusBar().showMessage("Benchmarking SIFT and ORB across controlled image transformations…")
        self._cancel_event = Event()
        self._worker = BenchmarkWorker(reference, settings, sift, orb, self._cancel_event)
        self._worker.completed.connect(self._show_benchmark)
        self._worker.failed.connect(self._show_error)
        self._worker.cancelled.connect(self._show_cancelled)
        self._worker.finished.connect(self._worker_finished)
        self._worker.start()

    def _show_benchmark(self, report: BenchmarkReport) -> None:
        self._latest_benchmark = report
        dialog = QDialog(self)
        dialog.setWindowTitle("VISOR Benchmark Lab")
        dialog.resize(950, 440)
        layout = QVBoxLayout(dialog)
        note = QLabel(
            f"Generated transformations from {report.reference_path.name}. Localization error is corner RMSE against known synthetic geometry. "
            f"Benchmark time: {report.duration_ms:.0f} ms."
        )
        note.setWordWrap(True)
        layout.addWidget(note)
        headers = ["Engine", "Scenario", "Ref kp", "Target kp", "Good", "Inliers", "Inlier %", "Valid", "Corner RMSE px", "Time ms"]
        table = QTableWidget(len(report.rows), len(headers))
        table.setHorizontalHeaderLabels(headers)
        for row_index, row in enumerate(report.rows):
            values = [row.engine, row.scenario, str(row.keypoints_reference), str(row.keypoints_target),
                      str(row.good_matches), str(row.inliers), f"{row.inlier_ratio:.1%}",
                      "Yes" if row.geometry_valid else "No",
                      "—" if row.localization_error_px is None else f"{row.localization_error_px:.2f}",
                      f"{row.total_ms:.1f}"]
            for column, value in enumerate(values):
                table.setItem(row_index, column, QTableWidgetItem(value))
        table.resizeColumnsToContents()
        layout.addWidget(table)
        dialog.exec()

    def _refresh_result_views(self) -> None:
        for label in self._result_arrays:
            self._refresh_one_view(label)

    def _refresh_visualization(self) -> None:
        result = self._latest_result
        if result is None or not hasattr(self, "view_toggles"):
            return
        settings = replace(
            result.settings,
            show_match_lines=self.view_toggles["show_match_lines"].isChecked(),
            show_inliers=self.view_toggles["show_inliers"].isChecked(),
            show_outliers=self.view_toggles["show_outliers"].isChecked(),
            show_keypoints=self.view_toggles["show_keypoints"].isChecked(),
            show_geometry=self.view_toggles["show_geometry"].isChecked(),
        )
        result = replace(
            result,
            settings=settings,
            matches_image=render_match_canvas(
                result.reference_image, result.target_image, result.reference_features,
                result.target_features, result.match_set, result.geometry, settings,
            ),
            localization_image=render_localization(
                result.target_image, result.target_features, result.geometry, settings,
            ),
        )
        self._latest_result = result
        self._result_arrays[self.matches_view] = result.matches_image
        self._result_arrays[self.localization_view] = result.localization_image
        self._refresh_result_views()

    def _fit_images(self) -> None:
        for view in (self.matches_view, self.localization_view, self.warped_view):
            view.fit_image()

    def _reset_layout(self) -> None:
        if self._default_window_state is not None:
            self.restoreState(self._default_window_state)

    def _restore_window_settings(self) -> None:
        geometry = self._window_settings.value("window/geometry")
        state = self._window_settings.value("window/state")
        if geometry is not None:
            self.restoreGeometry(geometry)
        if state is not None:
            self.restoreState(state)

    def closeEvent(self, event) -> None:
        if self._cancel_event is not None:
            self._cancel_event.set()
        if self._worker is not None and self._worker.isRunning():
            self._worker.wait()
        self._window_settings.setValue("window/geometry", self.saveGeometry())
        self._window_settings.setValue("window/state", self.saveState())
        super().closeEvent(event)

    def _refresh_one_view(self, label: ImageCanvas) -> None:
        image = self._result_arrays.get(label)
        label.set_image(image)

    def _inspect_keypoint(self, x: float, y: float) -> None:
        if self._latest_result is None:
            return
        points = self._latest_result.target_features.keypoints
        if not points:
            self.statusBar().showMessage("The target image has no keypoints to inspect.")
            return
        index, point = min(enumerate(points), key=lambda item: (item[1].x - x) ** 2 + (item[1].y - y) ** 2)
        distance = math.hypot(point.x - x, point.y - y)
        if distance > 30:
            self.statusBar().showMessage("No target keypoint is within 30 px of the selected coordinate.")
            return
        self.details_tabs.setCurrentIndex(0)
        self.details_panel.append_keypoint(self._latest_result.engine, index, point)
        self.statusBar().showMessage(f"Selected {self._latest_result.engine} target keypoint #{index} at ({point.x:.1f}, {point.y:.1f}) px")

    def _on_image_changed(self, role: str, path: object) -> None:
        if isinstance(path, Path):
            self._paths[role] = path
            self._latest_result = None
            self._latest_comparison = None
            self._latest_benchmark = None
            self.statusBar().showMessage(f"Loaded {role.lower()}: {path.name}")
        else:
            self._paths.pop(role, None)
            self.statusBar().showMessage(f"Unable to load {role.lower()} image.")
        if hasattr(self, "run_button"):
            ready = "Reference image" in self._paths and "Target image" in self._paths and self._worker is None
            self.run_button.setEnabled(ready)
            self.compare_button.setEnabled(ready)
            self.benchmark_button.setEnabled("Reference image" in self._paths and self._worker is None)

    def _save_project(self) -> None:
        if len(self._paths) != 2:
            self.statusBar().showMessage("Add both images before saving a project.")
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Save VISOR project", "analysis.visor", "VISOR project (*.visor)")
        if not filename:
            return
        settings, sift, orb = self._read_configurations()
        session = ProjectSession(
            str(self._paths["Reference image"]), str(self._paths["Target image"]),
            cast(EngineName, self.engine_selector.currentText()), settings, sift, orb,
        )
        try:
            save_project(session, Path(filename))
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, "Could not save project", str(exc))
            return
        self.statusBar().showMessage(f"Project saved: {Path(filename).name}")

    def _load_project(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(self, "Open VISOR project", "", "VISOR project (*.visor)")
        if not filename:
            return
        try:
            session = load_project(Path(filename))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            QMessageBox.critical(self, "Could not open project", str(exc))
            return
        self.engine_selector.setCurrentIndex(0 if session.engine == "SIFT" else 1)
        self.ratio_control.setValue(session.settings.ratio_threshold)
        self.ransac_control.setValue(session.settings.ransac_threshold)
        for name, action in self.view_toggles.items():
            action.setChecked(getattr(session.settings, name))
        self.sift_features.setValue(session.sift.max_features)
        self.sift_layers.setValue(session.sift.octave_layers)
        self.sift_contrast.setValue(session.sift.contrast_threshold)
        self.sift_edge.setValue(session.sift.edge_threshold)
        self.sift_sigma.setValue(session.sift.sigma)
        self.orb_features.setValue(session.orb.max_features)
        self.orb_scale.setValue(session.orb.scale_factor)
        self.orb_levels.setValue(session.orb.levels)
        self.orb_edge.setValue(session.orb.edge_threshold)
        self.orb_first_level.setValue(session.orb.first_level)
        self.orb_wta.setCurrentText(str(session.orb.wta_k))
        self.orb_score.setCurrentText(session.orb.score_type)
        self.orb_patch.setValue(session.orb.patch_size)
        self.orb_fast.setValue(session.orb.fast_threshold)
        self.reference_input.load_path(Path(session.reference_path))
        self.target_input.load_path(Path(session.target_path))
        self.statusBar().showMessage(f"Project loaded: {Path(filename).name}")

    def _export_json(self) -> None:
        self._export_analysis(export_json, "JSON files (*.json)", "analysis.json")

    def _export_csv(self) -> None:
        self._export_analysis(export_csv, "CSV files (*.csv)", "metrics.csv")

    def _export_comparison_csv(self) -> None:
        comparison = getattr(self, "_latest_comparison", None)
        if comparison is None:
            self.statusBar().showMessage("Run Compare SIFT / ORB before exporting comparison metrics.")
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Export comparison", "comparison.csv", "CSV files (*.csv)")
        if not filename:
            return
        try:
            export_comparison_csv(comparison, Path(filename))
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, "Export failed", str(exc))
            return
        self.statusBar().showMessage(f"Comparison exported: {Path(filename).name}")

    def _export_benchmark_csv(self) -> None:
        report = getattr(self, "_latest_benchmark", None)
        if report is None:
            self.statusBar().showMessage("Run the benchmark lab before exporting benchmark metrics.")
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Export benchmark", "benchmark.csv", "CSV files (*.csv)")
        if not filename:
            return
        try:
            export_benchmark_csv(report, Path(filename))
        except (OSError, ValueError, IndexError) as exc:
            QMessageBox.critical(self, "Export failed", str(exc))
            return
        self.statusBar().showMessage(f"Benchmark exported: {Path(filename).name}")

    def _export_analysis(self, exporter, file_filter: str, default_name: str) -> None:
        if self._latest_result is None:
            self.statusBar().showMessage("Run an analysis before exporting results.")
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Export analysis", default_name, file_filter)
        if not filename:
            return
        try:
            exporter(self._latest_result, Path(filename))
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, "Export failed", str(exc))
            return
        self.statusBar().showMessage(f"Exported: {Path(filename).name}")

    def _export_visualization(self) -> None:
        if self._latest_result is None:
            self.statusBar().showMessage("Run an analysis before exporting a visualization.")
            return
        views = {
            1: self._latest_result.matches_image,
            2: self._latest_result.localization_image,
            3: self._latest_result.warped_image,
        }
        image = views.get(self.result_tabs.currentIndex())
        if image is None:
            self.statusBar().showMessage("Choose Feature Matches, Localization, or Warped / Rectified first.")
            return
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export visualization", "visor-result.png", "PNG (*.png);;JPEG (*.jpg *.jpeg)",
        )
        if not filename:
            return
        try:
            export_visualization(image, Path(filename))
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, "Export failed", str(exc))
            return
        self.statusBar().showMessage(f"Visualization exported: {Path(filename).name}")

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
            QGraphicsView#resultImage { background: #141920; color: #8290a2; border: 0; }
            QDockWidget { color: #dce3ec; }
            QToolBar { background: #171c23; border-bottom: 1px solid #29313b; spacing: 4px; padding: 3px 6px; }
            QToolBar QToolButton { color: #cbd2dc; background: transparent; border: 1px solid transparent; border-radius: 4px; padding: 4px 6px; }
            QToolBar QToolButton:hover { background: #293240; border-color: #3c4c61; }
            QToolBar QToolButton:pressed { background: #1e2a38; }
            QSplitter::handle { background: #11151b; width: 10px; }
            """
        )
