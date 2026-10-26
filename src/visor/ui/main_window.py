"""Main application window."""

from __future__ import annotations

import math
import sys
from dataclasses import replace
from html import escape
from pathlib import Path
from threading import Event
from typing import cast

import numpy as np
from PySide6.QtCore import QByteArray, QSettings, QSignalBlocker, QStandardPaths, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QAction, QIcon, QTextCursor
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
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSlider,
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

from visor.batch import BatchReport, load_manifest, run_batch
from visor.benchmark import BenchmarkReport, run_benchmark
from visor.engine_registry import engine_capabilities
from visor.engines import ORBConfiguration, SIFTConfiguration
from visor.exporting import (
    ProjectSession,
    export_batch_csv,
    export_benchmark_csv,
    export_comparison_csv,
    export_csv,
    export_html_report,
    export_json,
    export_visualization,
    load_project,
    save_project,
)
from visor.geometry_robust import RobustMethod
from visor.jobs import JobController, JobTicket
from visor.learned_engines import is_lightglue_available, is_xfeat_available
from visor.matching_strategies import MatchingOptions
from visor.model_runtime import LIGHTGLUE_REQUIREMENT
from visor.models import (
    VALID_ENGINE_NAMES,
    AnalysisResult,
    AnalysisSettings,
    ComparisonResult,
    EngineName,
)
from visor.pipeline import AnalysisCancelled, _check_cancel, analyze, compare_engines
from visor.sweeps import run_robustness_sweep
from visor.ui.job_relay import JobRelay
from visor.ui.widgets.details_panel import AnalysisDetailsPanel
from visor.ui.widgets.image_canvas import ImageCanvas
from visor.ui.widgets.image_drop import ImageDropWidget
from visor.visualization import render_localization, render_match_canvas

_ICONS_DIR = Path(__file__).parent.parent / "assets" / "icons"


def _icon(name: str) -> QIcon:
    # Support both normal install and PyInstaller one-folder bundle.
    import sys
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass is not None:
        path = Path(meipass) / "visor" / "assets" / "icons" / f"{name}.svg"
    else:
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
        matching_options: MatchingOptions | None = None,
        robust_method: RobustMethod = "RANSAC",
    ) -> None:
        super().__init__()
        self.reference = reference
        self.target = target
        self.engine = engine
        self.settings = settings
        self.sift = sift
        self.orb = orb
        self.cancel_event = cancel_event
        self.matching_options = matching_options
        self.robust_method = robust_method

    def run(self) -> None:
        try:
            self.completed.emit(analyze(
                self.reference, self.target, self.engine, self.settings, self.sift, self.orb,
                self.cancel_event, None, None, self.matching_options, self.robust_method,
            ))
        except AnalysisCancelled:
            self.cancelled.emit()
        except Exception as exc:  # noqa: BLE001 — keep worker failures on the UI thread
            self.failed.emit(str(exc))


class ComparisonWorker(QThread):
    completed = Signal(object)
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, reference: Path, target: Path, settings: AnalysisSettings,
                 sift: SIFTConfiguration, orb: ORBConfiguration, cancel_event: Event,
                 matching_options: MatchingOptions | None = None,
                 robust_method: RobustMethod = "RANSAC") -> None:
        super().__init__()
        self.reference, self.target = reference, target
        self.settings, self.sift, self.orb = settings, sift, orb
        self.cancel_event = cancel_event
        self.matching_options = matching_options
        self.robust_method = robust_method

    def run(self) -> None:
        try:
            self.completed.emit(compare_engines(
                self.reference, self.target, self.settings, self.sift, self.orb,
                self.cancel_event, self.matching_options, self.robust_method,
            ))
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


class SweepWorker(QThread):
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
            self.completed.emit(run_robustness_sweep(
                self.reference, ("SIFT", "ORB"), self.settings, self.sift, self.orb, self.cancel_event,
            ))
        except AnalysisCancelled:
            self.cancelled.emit()
        except Exception as exc:  # noqa: BLE001 — keep worker failures on the UI thread
            self.failed.emit(str(exc))


class CalibrationWorker(QThread):
    completed = Signal(object)
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, images: list[Path], cancel_event: Event) -> None:
        super().__init__()
        self.images = images
        self.cancel_event = cancel_event

    def run(self) -> None:
        try:
            from visor.calibration import calibrate_from_chessboard_images
            camera, dist, rms, views = calibrate_from_chessboard_images(
                self.images, cancel_check=lambda: _check_cancel(self.cancel_event),
            )
            self.completed.emit((camera, dist, rms, views))
        except AnalysisCancelled:
            self.cancelled.emit()
        except Exception as exc:  # noqa: BLE001 — keep worker failures on the UI thread
            self.failed.emit(str(exc))


class InstallWorker(QThread):
    """Runs pip installs for learned-engine dependencies off the UI thread."""
    progress = Signal(str)
    completed = Signal(bool, str)  # success, message

    # Correct install commands for each optional learned-engine dependency.
    # LightGlue: official CVG repo (covers SuperPoint, ALIKED, DISK, SIFT+LG)
    # accelerated-features: the real XFeat package from verlab
    LIGHTGLUE_CMD = ("torch>=2.0", "torchvision>=0.15", "kornia>=0.6.11", "matplotlib")
    XFEAT_CMD = ("torch>=2.0", "tqdm>=4.66")

    def __init__(self, python_exe: str, install_lightglue: bool, install_xfeat: bool) -> None:
        super().__init__()
        self.python_exe = python_exe
        self.install_lightglue = install_lightglue
        self.install_xfeat = install_xfeat

    def run(self) -> None:
        import subprocess
        packages: list[str] = []
        if self.install_lightglue:
            packages.extend(self.LIGHTGLUE_CMD)
        if self.install_xfeat:
            packages.extend(self.XFEAT_CMD)
        if not packages:
            self.completed.emit(True, "Nothing to install.")
            return
        commands = [[self.python_exe, "-m", "pip", "install", "--upgrade"] + packages]
        if self.install_lightglue:
            # Upstream names opencv-python, but VISOR supplies the same cv2 API
            # through headless contrib. Never install a second provider over it.
            commands.append([self.python_exe, "-m", "pip", "install", "--no-deps", LIGHTGLUE_REQUIREMENT])
        try:
            for cmd in commands:
                self.progress.emit(f"Running: {' '.join(cmd)}")
                proc = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
                )
                assert proc.stdout is not None
                for line in proc.stdout:
                    self.progress.emit(line.rstrip())
                proc.wait()
                if proc.returncode != 0:
                    self.completed.emit(False, f"pip exited with code {proc.returncode}. Check Diagnostics for details.")
                    return
            if self.install_xfeat:
                self.progress.emit("Preparing the pinned XFeat source and weights…")
                setup = subprocess.Popen([self.python_exe, "-m", "visor.model_setup", "--xfeat"],
                                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                assert setup.stdout is not None
                for line in setup.stdout:
                    self.progress.emit(line.rstrip())
                setup.wait()
                if setup.returncode != 0:
                    self.completed.emit(False, "Pinned XFeat setup failed. See Diagnostics for details.")
                    return
            self.completed.emit(True, "Learned engine dependencies installed successfully.")
        except Exception as exc:  # noqa: BLE001
            self.completed.emit(False, str(exc))


class VideoWorker(QThread):
    completed = Signal(object)
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, reference: Path, video: Path, engine: EngineName,
                 settings: AnalysisSettings, cancel_event: Event) -> None:
        super().__init__()
        self.reference, self.video = reference, video
        self.engine, self.settings = engine, settings
        self.cancel_event = cancel_event

    def run(self) -> None:
        try:
            from visor.video import track_reference_in_video
            self.completed.emit(track_reference_in_video(
                self.reference, self.video, self.engine,
                self.settings.ratio_threshold, self.settings.ransac_threshold,
                cancel_event=self.cancel_event,
            ))
        except AnalysisCancelled:
            self.cancelled.emit()
        except Exception as exc:  # noqa: BLE001 — keep worker failures on the UI thread
            self.failed.emit(str(exc))


class BatchWorker(QThread):
    completed = Signal(object)
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, manifest: Path, settings: AnalysisSettings,
                 sift: SIFTConfiguration, orb: ORBConfiguration, cancel_event: Event) -> None:
        super().__init__()
        self.manifest, self.settings, self.sift, self.orb = manifest, settings, sift, orb
        self.cancel_event = cancel_event

    def run(self) -> None:
        try:
            pairs = load_manifest(self.manifest)
            self.completed.emit(run_batch(
                pairs, ("SIFT", "ORB"), self.settings, self.sift, self.orb, self.cancel_event,
            ))
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
        self._project_path: Path | None = None
        self._worker: QThread | None = None
        self._jobs = JobController()
        self._closing_requested = False
        self._cancel_event: Event | None = None
        self._result_arrays: dict[ImageCanvas, np.ndarray] = {}
        self._latest_result: AnalysisResult | None = None
        self._latest_comparison: ComparisonResult | None = None
        self._latest_benchmark: BenchmarkReport | None = None
        self._latest_batch: BatchReport | None = None
        self._pair_history: list[tuple[Path, Path]] = []
        self._install_worker: InstallWorker | None = None
        self._default_window_state: QByteArray | None = None
        self._build_menu()
        self._build_workspace()
        self._build_details_dock()
        self._build_diagnostics_dock()
        self._connect_configuration_changes()
        self.setStatusBar(QStatusBar(self))
        window_menu = self.window_menu
        window_menu.addAction(self.details_dock.toggleViewAction())
        window_menu.addAction(self.diagnostics_dock.toggleViewAction())
        reset_action = QAction("Reset layout", self)
        reset_action.triggered.connect(self._reset_layout)
        window_menu.addAction(reset_action)
        self._default_window_state = self.saveState()
        self._window_settings = QSettings("VISOR", "VISOR")
        self._restore_window_settings()
        self._update_learned_install_visibility()
        self.show()
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
            ("Analysis report (HTML)…", self._export_html_report),
            ("Metrics as CSV…", self._export_csv),
            ("SIFT vs ORB comparison CSV…", self._export_comparison_csv),
            ("Benchmark results CSV…", self._export_benchmark_csv),
            ("Batch results CSV…", self._export_batch_csv),
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
        sweep_action = QAction("Robustness Sweep", self)
        sweep_action.triggered.connect(self._start_sweep)
        analysis_menu.addAction(sweep_action)
        batch_action = QAction("Run Batch from Manifest…", self)
        batch_action.triggered.connect(self._start_batch)
        analysis_menu.addAction(batch_action)
        video_action = QAction("Track Reference in Video…", self)
        video_action.triggered.connect(self._start_video_tracking)
        analysis_menu.addAction(video_action)
        calibration_action = QAction("Calibrate Camera…", self)
        calibration_action.triggered.connect(self._start_calibration)
        analysis_menu.addAction(calibration_action)

        view_menu = self.menuBar().addMenu("&View")
        self.view_toggles = {}
        for title, setting_name, checked in (
            ("Match lines", "show_match_lines", True),
            ("Inliers", "show_inliers", True),
            ("Outliers", "show_outliers", True),
            ("Keypoints", "show_keypoints", False),
            ("Localization geometry", "show_geometry", True),
            ("Rainbow feature lines", "rainbow_feature_colors", False),
        ):
            action = QAction(title, self)
            action.setCheckable(True)
            action.setChecked(checked)
            action.toggled.connect(
                self._set_rainbow_colors if setting_name == "rainbow_feature_colors" else self._refresh_visualization
            )
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
        engine_status_action = QAction("Engine Availability…", self)
        engine_status_action.triggered.connect(self._show_engine_status)
        help_menu.addAction(engine_status_action)
        help_menu.addSeparator()
        about_action = QAction("About VISOR", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _build_workspace(self) -> None:
        root = QWidget()
        root.setObjectName("workspace")
        outer = QVBoxLayout(root)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(12)

        header = QHBoxLayout()
        engine_label = QLabel("&Engine")
        engine_label.setObjectName("mutedText")
        self.engine_selector = QComboBox()
        self.engine_selector.addItems(["SIFT", "ORB"])
        self.engine_selector.setAccessibleName("Analysis engine")
        self.engine_selector.setMinimumContentsLength(20)
        self.engine_selector.view().setMinimumWidth(340)
        self.engine_selector.view().setAccessibleName("Engine choices")
        self.engine_selector.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        engine_label.setBuddy(self.engine_selector)
        self.run_button = QPushButton("Run analysis")
        self.run_button.setObjectName("primaryButton")
        self.run_button.setEnabled(False)
        self.run_button.clicked.connect(self._start_analysis)
        self.compare_button = QPushButton("Compare SIFT / ORB")
        self.compare_button.setObjectName("secondaryButton")
        self.compare_button.setEnabled(False)
        self.compare_button.clicked.connect(self._start_comparison)
        self.benchmark_button = QPushButton("Benchmark")
        self.benchmark_button.setObjectName("secondaryButton")
        self.benchmark_button.setEnabled(False)
        self.benchmark_button.clicked.connect(self._start_benchmark)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setObjectName("secondaryButton")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self._cancel_running)
        for entry in engine_capabilities()[2:]:
            self._add_engine_entry(entry.name, entry.available, entry.reason)
        self.engine_selector.setToolTip("Feature extraction and descriptor matching engine")
        self.engine_selector.currentIndexChanged.connect(self._engine_changed)
        self.install_learned_button = QPushButton("Install learned engines")
        self.install_learned_button.setObjectName("secondaryButton")
        self.install_learned_button.clicked.connect(self._install_learned_engines)
        self.install_learned_button.setVisible(False)
        header.addWidget(engine_label)
        header.addWidget(self.engine_selector)
        header.addWidget(self.run_button)
        header.addWidget(self.cancel_button)
        header.addStretch(1)
        self.fit_view_button = QPushButton("Fit View")
        self.fit_view_button.setObjectName("secondaryButton")
        self.fit_view_button.clicked.connect(self._fit_images)
        header.addWidget(self.fit_view_button)
        self.export_button = QPushButton("Export")
        self.export_button.setObjectName("secondaryButton")
        self.export_button.clicked.connect(self._export_visualization)
        header.addWidget(self.export_button)
        outer.addLayout(header)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        input_panel = QWidget()
        input_panel.setObjectName("inputPanel")
        input_layout = QVBoxLayout(input_panel)
        input_layout.setContentsMargins(12, 12, 12, 12)
        input_layout.setSpacing(10)
        self.reference_input = ImageDropWidget("Reference image")
        self.target_input = ImageDropWidget("Target image")
        self.reference_input.image_changed.connect(self._on_image_changed)
        self.target_input.image_changed.connect(self._on_image_changed)

        image_row = QWidget()
        image_row_layout = QVBoxLayout(image_row)
        image_row_layout.setContentsMargins(0, 0, 0, 0)
        image_row_layout.setSpacing(10)
        self.reference_input.setMinimumWidth(220)
        self.target_input.setMinimumWidth(220)
        self.reference_input.setMinimumHeight(200)
        self.target_input.setMinimumHeight(200)
        self.reference_input.preview.setMinimumHeight(90)
        self.target_input.preview.setMinimumHeight(90)
        image_row_layout.addWidget(self.reference_input, 1)
        image_row_layout.addWidget(self.target_input, 1)
        image_row_layout.setStretch(0, 1)
        image_row_layout.setStretch(1, 1)
        input_layout.addWidget(image_row, 1)

        secondary_actions = QHBoxLayout()
        secondary_actions.addWidget(self.compare_button)
        secondary_actions.addWidget(self.benchmark_button)
        input_layout.addLayout(secondary_actions)

        self.recent_pairs_toggle = QPushButton("Recent pairs")
        self.recent_pairs_toggle.setObjectName("secondaryButton")
        self.recent_pairs_toggle.setCheckable(True)
        self.recent_pairs_toggle.setChecked(False)
        self.recent_pairs_toggle.setToolTip("Show or hide recently used image pairs")
        self.recent_pairs_toggle.toggled.connect(self._toggle_recent_pairs)
        input_layout.addWidget(self.recent_pairs_toggle)

        pair_panel = QWidget()
        self.recent_pairs_panel = pair_panel
        pair_panel.setObjectName("pairHistoryPanel")
        pair_panel.setMinimumHeight(70)
        pair_panel.setMaximumHeight(170)
        pair_layout = QVBoxLayout(pair_panel)
        pair_layout.setContentsMargins(0, 6, 0, 0)
        pair_layout.setSpacing(4)
        pair_header = QHBoxLayout()
        self.add_pair_button = QPushButton("Save current pair")
        self.add_pair_button.setObjectName("secondaryButton")
        self.add_pair_button.clicked.connect(self._add_current_pair_to_history)
        self.clear_pair_button = QPushButton("Clear")
        self.clear_pair_button.setObjectName("secondaryButton")
        self.clear_pair_button.clicked.connect(self._clear_pair_history)
        pair_header.addWidget(self.add_pair_button)
        pair_header.addWidget(self.clear_pair_button)
        pair_layout.addLayout(pair_header)
        self.pair_list = QListWidget()
        self.pair_list.setAccessibleName("Recent reference and target pairs")
        self.pair_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.pair_list.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.pair_list.setMinimumHeight(70)
        self.pair_list.setMaximumHeight(130)
        self.pair_list.setToolTip("Select a saved image pair to reload it for inspection")
        self.pair_list.itemDoubleClicked.connect(self._load_selected_pair)
        pair_layout.addWidget(self.pair_list)
        pair_panel.setVisible(False)
        input_layout.addWidget(pair_panel)

        overlay_controls = QWidget()
        overlay_controls.setObjectName("overlayControls")
        overlay_layout = QHBoxLayout(overlay_controls)
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        overlay_layout.setSpacing(10)
        overlay_label = QLabel("Overlay")
        overlay_label.setObjectName("mutedText")
        self.feature_color_button = QPushButton("Rainbow")
        self.feature_color_button.setObjectName("secondaryButton")
        self.feature_color_button.setCheckable(True)
        self.feature_color_button.setChecked(False)
        self.feature_color_button.setToolTip("Toggle rainbow feature colors")
        self.feature_color_button.toggled.connect(self._set_rainbow_colors)
        self.feature_thickness_slider = QSlider(Qt.Orientation.Horizontal)
        self.feature_thickness_slider.setRange(1, 12)
        self.feature_thickness_slider.setValue(1)
        self.feature_thickness_slider.setToolTip("Feature line thickness")
        self.feature_thickness_slider.setAccessibleName("Feature line thickness in pixels")
        self.feature_thickness_slider.valueChanged.connect(self._set_feature_line_thickness)
        self.feature_thickness_value = QLabel("1 px")
        self.feature_thickness_value.setObjectName("mutedText")
        overlay_layout.addWidget(overlay_label)
        overlay_layout.addWidget(self.feature_color_button)
        thickness_label = QLabel("&Thickness")
        thickness_label.setBuddy(self.feature_thickness_slider)
        overlay_layout.addWidget(thickness_label)
        overlay_layout.addWidget(self.feature_thickness_slider, 1)
        overlay_layout.addWidget(self.feature_thickness_value)

        self.overview_panel = QWidget()
        self.overview_panel.setObjectName("welcomePanel")
        overview_layout = QVBoxLayout(self.overview_panel)
        overview_layout.setContentsMargins(18, 18, 18, 18)
        overview_layout.setSpacing(10)
        self.overview_summary = QLabel()
        self.overview_summary.setObjectName("mutedText")
        self.overview_summary.setWordWrap(True)
        self.overview_summary.setAlignment(Qt.AlignmentFlag.AlignTop)
        overview_layout.addWidget(self.overview_summary)
        overview_layout.addStretch(1)
        self._update_overview_summary()

        self.result_tabs = QTabWidget()
        self.result_tabs.addTab(self.overview_panel, "Overview")
        self.matches_view = self._image_view("Run an analysis to inspect feature correspondences.")
        self.localization_view = self._image_view("A projected reference outline appears when a valid planar mapping is found.")
        self.warped_view = self._image_view("Rectified view is available after a valid homography.")
        self.result_tabs.addTab(self.matches_view, "Feature Matches")
        self.result_tabs.addTab(self.localization_view, "Localization")
        self.result_tabs.addTab(self.warped_view, "Warped / Rectified")
        input_scroll = QScrollArea()
        input_scroll.setObjectName("inputScroll")
        input_scroll.setWidgetResizable(True)
        input_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        input_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        input_scroll.setMinimumWidth(260)
        input_scroll.setWidget(input_panel)
        result_panel = QWidget()
        result_layout = QVBoxLayout(result_panel)
        result_layout.setContentsMargins(0, 0, 0, 0)
        result_layout.setSpacing(8)
        result_layout.addWidget(self.result_tabs, 1)
        result_layout.addWidget(overlay_controls)
        splitter.addWidget(input_scroll)
        splitter.addWidget(result_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([280, 680])
        outer.addWidget(splitter, 1)
        self.setCentralWidget(root)

    def _toggle_recent_pairs(self, checked: bool) -> None:
        if hasattr(self, "recent_pairs_panel"):
            self.recent_pairs_panel.setVisible(checked)

    def _add_engine_entry(self, name: str, available: bool, hint: str) -> None:
        """Keep engine names compact; put dependency guidance in the tooltip."""
        self.engine_selector.addItem(name if available else f"{name} (unavailable)")
        index = self.engine_selector.count() - 1
        item = self.engine_selector.model().item(index)  # type: ignore[union-attr]
        item.setEnabled(available)
        reason = "Not included in this desktop distribution." if not available and getattr(sys, "frozen", False) else hint
        self.engine_selector.setItemData(index, reason, Qt.ItemDataRole.ToolTipRole)

    def _build_diagnostics_dock(self) -> None:
        self.engine_console = QPlainTextEdit()
        self.engine_console.setObjectName("engineConsole")
        self.engine_console.setAccessibleName("Diagnostic activity log")
        self.engine_console.setReadOnly(True)
        self.engine_console.setMaximumBlockCount(200)
        self.engine_console.setPlaceholderText("Processing messages and engine diagnostics appear here.")
        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(self.install_learned_button, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.engine_console)
        self.diagnostics_dock = QDockWidget("Diagnostics", self)
        self.diagnostics_dock.setObjectName("diagnosticsDock")
        self.diagnostics_dock.setWidget(body)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.diagnostics_dock)
        self.diagnostics_dock.hide()
        self.log_engine_event("INFO", "SIFT/ORB ready. Optional engine status is available under Help > Engine Availability.")

    def log_engine_event(self, level: str, message: str) -> None:
        text = self.engine_console.toPlainText().strip()
        if text:
            body = f"{text}\n[{level.upper()}] {message}"
        else:
            body = f"[{level.upper()}] {message}"
        self.engine_console.setPlainText(body)
        cursor = self.engine_console.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.engine_console.setTextCursor(cursor)
        if level.upper() == "ERROR" and hasattr(self, "diagnostics_dock"):
            self.diagnostics_dock.show()

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
        configuration_scroll = QScrollArea()
        configuration_scroll.setWidgetResizable(True)
        configuration_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        configuration_scroll.setWidget(self._configuration_panel())
        self.details_tabs.addTab(configuration_scroll, "Parameters")
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
        common_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        self.ratio_control = self._float_control(0.50, 0.99, 0.75)
        self.ransac_control = self._float_control(0.5, 20.0, 4.0)
        self.match_line_thickness = QSlider(Qt.Orientation.Horizontal)
        self.match_line_thickness.setRange(1, 12)
        self.match_line_thickness.setValue(1)
        self.match_line_thickness.setToolTip("Adjust the visible thickness of feature match lines.")
        self.match_line_thickness.valueChanged.connect(self._set_feature_line_thickness)
        common_form.addRow("Ratio threshold", self.ratio_control)
        self.ransac_control.setToolTip(
            "RANSAC uses the recorded legacy adaptive threshold sequence around this base. "
            "MAGSAC uses it as an upper bound; LMEDS does not use this threshold. "
            "Results record the thresholds actually attempted."
        )
        common_form.addRow("Estimator base (px)", self.ransac_control)
        common_form.addRow("Feature line thickness", self.match_line_thickness)
        self.matcher_strategy = QComboBox()
        self.matcher_strategy.addItems(["Default ratio test", "Cross-check", "FLANN", "Symmetric ratio"])
        self.matcher_strategy.setToolTip("Optional matching strategy. Default reproduces the frozen SIFT/ORB path.")
        self.robust_estimator = QComboBox()
        self.robust_estimator.addItems(["RANSAC", "MAGSAC", "LMEDS"])
        self.robust_estimator.setToolTip("Robust homography estimator. RANSAC is the frozen default.")
        common_form.addRow("Matcher strategy", self.matcher_strategy)
        common_form.addRow("Robust estimator", self.robust_estimator)
        layout.addWidget(common)

        self.engine_settings = QStackedWidget()
        sift_panel = QWidget()
        sift_form = QFormLayout(sift_panel)
        sift_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
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
        orb_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
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
            name = self.engine_selector.itemText(index)
            self.engine_settings.setVisible(name in ("SIFT", "ORB"))
            classical = any(item.name == name and item.classical_matching for item in engine_capabilities())
            self.ratio_control.setEnabled(classical)
            self.matcher_strategy.setEnabled(classical)
            self.engine_settings.setCurrentIndex(0 if name == "SIFT" else 1 if name == "ORB" else self.engine_settings.currentIndex())
        self._update_overview_summary()

    def _sync_overlay_controls(self) -> None:
        self._set_feature_line_thickness(self.match_line_thickness.value())
        self._set_rainbow_colors(self.view_toggles["rainbow_feature_colors"].isChecked())

    def _set_feature_line_thickness(self, value: int) -> None:
        # Both editors represent one setting. Block feedback so a single user
        # change renders once, after both controls contain the effective value.
        for slider in (self.feature_thickness_slider, self.match_line_thickness):
            with QSignalBlocker(slider):
                slider.setValue(value)
        self._update_feature_thickness_label()
        self._refresh_visualization()

    def _set_rainbow_colors(self, enabled: bool) -> None:
        for control in (self.feature_color_button, self.view_toggles["rainbow_feature_colors"]):
            with QSignalBlocker(control):
                control.setChecked(enabled)
        self._refresh_visualization()

    def _update_feature_thickness_label(self) -> None:
        if hasattr(self, "feature_thickness_value") and hasattr(self, "feature_thickness_slider"):
            self.feature_thickness_value.setText(f"{self.feature_thickness_slider.value()} px")

    def _reset_configuration(self) -> None:
        self.ratio_control.setValue(0.75)
        self.ransac_control.setValue(4.0)
        self.match_line_thickness.setValue(1)
        self.feature_thickness_slider.setValue(1)
        self.feature_color_button.setChecked(False)
        self.view_toggles["rainbow_feature_colors"].setChecked(False)
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
        self.matcher_strategy.setCurrentText("Default ratio test")
        self.robust_estimator.setCurrentText("RANSAC")
        self.statusBar().showMessage("SIFT, ORB, matching, and geometry parameters restored to defaults.")

    def _read_configurations(
        self,
    ) -> tuple[AnalysisSettings, SIFTConfiguration, ORBConfiguration, MatchingOptions, RobustMethod]:
        rainbow_checked = self.view_toggles["rainbow_feature_colors"].isChecked()
        settings = AnalysisSettings(
            self.ratio_control.value(), self.ransac_control.value(),
            self.view_toggles["show_match_lines"].isChecked(),
            self.view_toggles["show_inliers"].isChecked(),
            self.view_toggles["show_outliers"].isChecked(),
            self.view_toggles["show_keypoints"].isChecked(),
            self.view_toggles["show_geometry"].isChecked(),
            rainbow_checked,
            float(self.feature_thickness_slider.value() if hasattr(self, "feature_thickness_slider") else self.match_line_thickness.value()),
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
        strategy = self.matcher_strategy.currentText() if hasattr(self, "matcher_strategy") else "Default ratio test"
        matching_options = MatchingOptions(
            ratio_threshold=self.ratio_control.value(),
            cross_check=strategy == "Cross-check" and self.matcher_strategy.isEnabled(),
            symmetric_ratio=strategy == "Symmetric ratio" and self.matcher_strategy.isEnabled(),
            use_flann=strategy == "FLANN" and self.matcher_strategy.isEnabled(),
        )
        robust_text = self.robust_estimator.currentText() if hasattr(self, "robust_estimator") else "RANSAC"
        robust_method: RobustMethod = robust_text if robust_text in ("RANSAC", "MAGSAC", "LMEDS") else "RANSAC"
        return settings, sift, orb, matching_options, robust_method

    def _start_analysis(self) -> None:
        if not self._job_can_start():
            return
        reference = self._paths.get("Reference image")
        target = self._paths.get("Target image")
        if reference is None or target is None or self._worker is not None:
            return
        engine_text = self.engine_selector.currentText()
        if engine_text not in VALID_ENGINE_NAMES:
            self.statusBar().showMessage("Selected engine is not available. Install the required optional dependencies to use it.")
            return
        engine = cast(EngineName, engine_text)
        settings, sift, orb, matching_options, robust_method = self._read_configurations()
        self._clear_result_views()
        self._update_overview_summary()
        self.run_button.setEnabled(False)
        self.compare_button.setEnabled(False)
        self.benchmark_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.statusBar().showMessage(f"Running {engine} feature analysis…")
        self.log_engine_event("INFO", f"Running {engine} feature analysis on {reference.name} ↔ {target.name}.")
        self._cancel_event = Event()
        self._worker = AnalysisWorker(
            reference, target, engine, settings, sift, orb, self._cancel_event,
            matching_options, robust_method,
        )
        self._connect_worker(self._show_result)
        self._worker.start()

    def _start_comparison(self) -> None:
        if not self._job_can_start():
            return
        reference = self._paths.get("Reference image")
        target = self._paths.get("Target image")
        if reference is None or target is None or self._worker is not None:
            return
        settings, sift, orb, matching_options, robust_method = self._read_configurations()
        self._clear_result_views()
        self._update_overview_summary()
        self.run_button.setEnabled(False)
        self.compare_button.setEnabled(False)
        self.benchmark_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.statusBar().showMessage("Comparing SIFT and ORB on the same image pair…")
        self.log_engine_event("INFO", f"Comparing classical SIFT and ORB on {reference.name} ↔ {target.name}.")
        self._cancel_event = Event()
        self._worker = ComparisonWorker(
            reference, target, settings, sift, orb, self._cancel_event,
            matching_options, robust_method,
        )
        self._connect_worker(self._show_comparison)
        self._worker.start()

    def _connect_worker(self, callback) -> None:
        """Bind this worker once, using main-thread slots and a revision ticket."""
        worker = self._worker
        assert worker is not None and self._cancel_event is not None
        ticket = self._jobs.begin(self._cancel_event)
        relay = JobRelay(self._jobs, ticket, callback, self._show_error, self._show_cancelled,
                         lambda: self._worker_finished(worker, ticket), self)
        worker.completed.connect(relay.success)
        worker.failed.connect(relay.failure)
        worker.cancelled.connect(relay.cancelled)
        worker.finished.connect(relay.finished)

    def _worker_finished(self, worker: QThread, ticket: JobTicket) -> None:
        if not self._jobs.finish(ticket):
            worker.deleteLater()
            return
        self._worker = None
        ready = "Reference image" in self._paths and "Target image" in self._paths and not self._closing_requested
        self.run_button.setEnabled(ready)
        self.compare_button.setEnabled(ready)
        self.benchmark_button.setEnabled("Reference image" in self._paths and not self._closing_requested)
        self.cancel_button.setEnabled(False)
        self._cancel_event = None
        worker.deleteLater()
        self._finish_deferred_close()

    def _job_can_start(self) -> bool:
        installing = self._install_worker is not None and self._install_worker.isRunning()
        if self._worker is not None or installing or self._closing_requested:
            self.statusBar().showMessage("Wait for the current operation to finish.")
            return False
        return True

    def _connect_configuration_changes(self) -> None:
        for control in (self.ratio_control, self.ransac_control, self.sift_features, self.sift_layers,
                        self.sift_contrast, self.sift_edge, self.sift_sigma, self.orb_features,
                        self.orb_scale, self.orb_levels, self.orb_edge, self.orb_first_level,
                        self.orb_patch, self.orb_fast):
            control.valueChanged.connect(self._invalidate_analysis)
        for control in (self.engine_selector, self.orb_wta, self.orb_score,
                        self.matcher_strategy, self.robust_estimator):
            control.currentIndexChanged.connect(self._invalidate_analysis)

    def _invalidate_analysis(self, *_args) -> None:
        self._jobs.invalidate()
        self._clear_result_views()
        self._latest_benchmark = None
        self._latest_batch = None
        if self._worker is not None:
            self.statusBar().showMessage("Inputs or parameters changed; cancelling the previous run and discarding its result.")
        elif not self._closing_requested:
            self.statusBar().showMessage("Inputs or parameters changed. Run analysis to generate a new result.")
        self._update_overview_summary()

    def _finish_deferred_close(self) -> None:
        installing = self._install_worker is not None and self._install_worker.isRunning()
        if self._closing_requested and self._worker is None and not installing:
            QTimer.singleShot(0, self.close)

    def _clear_result_views(self) -> None:
        self._result_arrays = {}
        self._latest_result = None
        self._latest_comparison = None
        if hasattr(self, "details_panel"):
            self.details_panel.clear()
        for view in (self.matches_view, self.localization_view, self.warped_view):
            view.set_placeholder("No analysis loaded for this viewport yet.")

    def _add_current_pair_to_history(self) -> None:
        if "Reference image" not in self._paths or "Target image" not in self._paths:
            return
        reference = self._paths["Reference image"]
        target = self._paths["Target image"]
        pair = (reference, target)
        if pair in self._pair_history:
            self._sync_pair_list()
            return
        self._pair_history.append(pair)
        self._sync_pair_list()
        self.statusBar().showMessage(f"Saved pair: {reference.name} ↔ {target.name}")

    def _sync_pair_list(self) -> None:
        self.pair_list.clear()
        for reference, target in self._pair_history:
            label = f"{reference.name}  ↔  {target.name}"
            item = QListWidgetItem(label)
            item.setToolTip(f"Reference: {reference}\nTarget: {target}")
            self.pair_list.addItem(item)

    def _clear_pair_history(self) -> None:
        self._pair_history.clear()
        self.pair_list.clear()
        self.statusBar().showMessage("Pair history cleared.")

    def _load_selected_pair(self, item: QListWidgetItem) -> None:
        index = self.pair_list.row(item)
        if not 0 <= index < len(self._pair_history):
            return
        reference, target = self._pair_history[index]
        self.reference_input.load_path(reference)
        self.target_input.load_path(target)
        self.statusBar().showMessage(f"Loaded pair from history: {reference.name} ↔ {target.name}")

    def _show_error(self, message: str) -> None:
        self.statusBar().showMessage(f"Analysis failed: {message}")
        self.log_engine_event("ERROR", message)
        if hasattr(self, "details_panel"):
            self.details_panel.clear()
            self.details_panel.set_mode("tree")
            self.details_panel._data = [
                ("Error", [("Message", [("Details", message)])]),
            ]
            self.details_panel._render()
            self.details_tabs.setCurrentIndex(0)

    def _show_cancelled(self) -> None:
        self.statusBar().showMessage("Analysis cancelled at a safe processing boundary.")
        self.log_engine_event("INFO", "Analysis cancelled at a safe processing boundary.")

    def _cancel_running(self) -> None:
        if self._cancel_event is not None:
            self._jobs.cancel()
            self._cancel_event.set()
            self.cancel_button.setEnabled(False)
            self.statusBar().showMessage("Cancellation requested; waiting for the active OpenCV operation to finish…")

    def _update_overview_summary(self) -> None:
        if not hasattr(self, "overview_summary"):
            return
        reference = self._paths.get("Reference image")
        target = self._paths.get("Target image")
        engine = self.engine_selector.currentText() if hasattr(self, "engine_selector") else "SIFT"
        summary_lines = [
            "<b>Session summary</b>",
            f"Reference: {escape(reference.name) if reference else 'Not selected'}",
            f"Target: {escape(target.name) if target else 'Not selected'}",
            f"Selected engine: {escape(engine)}",
            "Quick actions: load a reference and target image, run the analysis, then export or fit the view when needed.",
        ]
        if self._latest_result is not None:
            result = self._latest_result
            summary_lines.append(
                "Planar fit accepted; accuracy requires independent ground truth."
                if result.geometry.valid else f"No valid mapping: {escape(result.geometry.message)}"
            )
            summary_lines.append(
                f"Last run: {result.engine} | {len(result.reference_features.keypoints):,} / {len(result.target_features.keypoints):,} keypoints | "
                f"{result.match_set.good_count:,} good matches | {result.geometry.inlier_count:,} inliers"
            )
        self.overview_summary.setText("<br>".join(summary_lines))

    def _show_result(self, result: AnalysisResult) -> None:
        self._latest_result = result
        self._latest_comparison = None
        self._update_overview_summary()
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
        if self.result_tabs.currentIndex() == 0:
            self.result_tabs.setCurrentWidget(self.localization_view if result.geometry.valid else self.matches_view)
        ref = result.reference_features
        target = result.target_features
        g = result.geometry
        p = result.performance
        summary = (
            f"{result.engine}: {'fit accepted' if g.valid else 'no valid mapping'} — {len(ref.keypoints):,}/{len(target.keypoints):,} keypoints, "
            f"{result.match_set.good_count:,} good matches, {g.inlier_count:,} inliers · {p.total_ms:.0f} ms"
        )
        self.statusBar().showMessage(summary)
        self.log_engine_event("OK" if g.valid else "INFO", summary)

    def _show_comparison(self, comparison: ComparisonResult) -> None:
        self._show_result(comparison.orb)
        self.details_panel.populate_comparison(comparison)
        self.details_tabs.setCurrentIndex(0)
        self._latest_comparison = comparison
        sift, orb = comparison.sift, comparison.orb
        summary = (
            f"Comparison complete — SIFT {sift.geometry.inlier_count} inliers/{sift.performance.total_ms:.0f} ms; "
            f"ORB {orb.geometry.inlier_count} inliers/{orb.performance.total_ms:.0f} ms"
        )
        self.statusBar().showMessage(summary)
        self.log_engine_event("OK", summary)

    def _start_benchmark(self) -> None:
        if not self._job_can_start():
            return
        reference = self._paths.get("Reference image")
        if reference is None or self._worker is not None:
            self.statusBar().showMessage("Load a reference image before running the benchmark lab.")
            return
        settings, sift, orb, _, _ = self._read_configurations()
        self.run_button.setEnabled(False)
        self.compare_button.setEnabled(False)
        self.benchmark_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.statusBar().showMessage("Benchmarking SIFT and ORB across controlled image transformations…")
        self.log_engine_event("INFO", f"Benchmarking image transformations from {reference.name}.")
        self._cancel_event = Event()
        self._worker = BenchmarkWorker(reference, settings, sift, orb, self._cancel_event)
        self._connect_worker(self._show_benchmark)
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

    def _start_sweep(self) -> None:
        if not self._job_can_start():
            return
        reference = self._paths.get("Reference image")
        if reference is None or self._worker is not None:
            self.statusBar().showMessage("Load a reference image before running the robustness sweep.")
            return
        settings, sift, orb, _, _ = self._read_configurations()
        self.run_button.setEnabled(False)
        self.compare_button.setEnabled(False)
        self.benchmark_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.statusBar().showMessage("Sweeping rotation and scale across SIFT and ORB…")
        self.log_engine_event("INFO", f"Running rotation/scale sweep from {reference.name}.")
        self._cancel_event = Event()
        self._worker = SweepWorker(reference, settings, sift, orb, self._cancel_event)
        self._connect_worker(self._show_sweep)
        self._worker.start()

    def _show_sweep(self, report: BenchmarkReport) -> None:
        self._latest_benchmark = report
        dialog = QDialog(self)
        dialog.setWindowTitle("VISOR Robustness Sweep")
        dialog.resize(950, 440)
        layout = QVBoxLayout(dialog)
        note = QLabel(
            f"Rotation/scale sweep from {report.reference_path.name}. Corner RMSE against known synthetic geometry. "
            f"Sweep time: {report.duration_ms:.0f} ms."
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

    def _start_batch(self) -> None:
        if not self._job_can_start():
            return
        if self._worker is not None:
            return
        filename, _ = QFileDialog.getOpenFileName(self, "Open batch manifest", str(self._dialog_directory("manifests")), "CSV manifest (*.csv)")
        if not filename:
            return
        self._remember_file_location("manifests", filename)
        settings, sift, orb, _, _ = self._read_configurations()
        self.run_button.setEnabled(False)
        self.compare_button.setEnabled(False)
        self.benchmark_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.statusBar().showMessage(f"Running batch from {Path(filename).name}…")
        self.log_engine_event("INFO", f"Running batch from manifest {Path(filename).name}.")
        self._cancel_event = Event()
        self._worker = BatchWorker(Path(filename), settings, sift, orb, self._cancel_event)
        self._connect_worker(self._show_batch)
        self._worker.start()

    def _show_batch(self, report: BatchReport) -> None:
        self._latest_batch = report
        dialog = QDialog(self)
        dialog.setWindowTitle("VISOR Batch Results")
        dialog.resize(950, 440)
        layout = QVBoxLayout(dialog)
        note = QLabel(
            f"{len(report.pairs)} pairs × engines in {report.duration_ms:.0f} ms. "
            "Batch reuses the single-pair pipeline, so numbers match interactive runs."
        )
        note.setWordWrap(True)
        layout.addWidget(note)
        headers = ["Scene", "Reference", "Target", "Engine", "Good", "Inliers", "Inlier %", "Valid", "Reproj px", "Time ms"]
        table = QTableWidget(len(report.rows), len(headers))
        table.setHorizontalHeaderLabels(headers)
        for row_index, row in enumerate(report.rows):
            values = [row.scene, Path(row.reference).name, Path(row.target).name, row.engine,
                      str(row.good_matches), str(row.inliers), f"{row.inlier_ratio:.1%}",
                      "Yes" if row.geometry_valid else "No",
                      "—" if row.reprojection_error_px is None else f"{row.reprojection_error_px:.2f}",
                      f"{row.total_ms:.1f}"]
            for column, value in enumerate(values):
                table.setItem(row_index, column, QTableWidgetItem(value))
        table.resizeColumnsToContents()
        layout.addWidget(table)
        save_button = QPushButton("Save batch CSV…")
        save_button.clicked.connect(lambda: self._export_batch_csv(report))
        layout.addWidget(save_button)
        dialog.exec()

    def _start_video_tracking(self) -> None:
        if not self._job_can_start():
            return
        reference = self._paths.get("Reference image")
        if reference is None or self._worker is not None:
            self.statusBar().showMessage("Load a reference image before tracking video.")
            return
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open video file", str(self._dialog_directory("videos")), "Video files (*.avi *.mp4 *.mov *.mkv);;All files (*)",
        )
        if not filename:
            return
        engine_text = self.engine_selector.currentText()
        if engine_text not in ("SIFT", "ORB"):
            self.statusBar().showMessage("Video tracking supports the SIFT and ORB engines.")
            return
        self._remember_file_location("videos", filename)
        settings, _, _, _, _ = self._read_configurations()
        self.run_button.setEnabled(False)
        self.compare_button.setEnabled(False)
        self.benchmark_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.statusBar().showMessage(f"Tracking reference in {Path(filename).name}…")
        self.log_engine_event("INFO", f"Tracking reference {reference.name} in {Path(filename).name}.")
        self._cancel_event = Event()
        self._worker = VideoWorker(
            reference, Path(filename), cast(EngineName, engine_text), settings, self._cancel_event,
        )
        self._connect_worker(self._show_track_report)
        self._worker.start()

    def _show_track_report(self, report) -> None:  # type: ignore[no-untyped-def]
        dialog = QDialog(self)
        dialog.setWindowTitle("VISOR Video Tracking")
        dialog.resize(800, 440)
        layout = QVBoxLayout(dialog)
        valid = sum(1 for frame in report.frames if frame.geometry_valid)
        note = QLabel(
            f"{report.engine} tracked {report.reference_path.name} in {report.video_path.name}: "
            f"{valid}/{len(report.frames)} frames have valid planar fits in {report.duration_ms:.0f} ms, including decoding. "
            "No ground-truth accuracy was measured."
        )
        note.setWordWrap(True)
        layout.addWidget(note)
        headers = ["Frame", "Good", "Inliers", "Inlier %", "Valid fit", "Center px"]
        table = QTableWidget(len(report.frames), len(headers))
        table.setHorizontalHeaderLabels(headers)
        for row_index, frame in enumerate(report.frames):
            values = [str(frame.frame_index), str(frame.good_matches), str(frame.inliers),
                      f"{frame.inlier_ratio:.1%}", "Yes" if frame.geometry_valid else "No",
                      "—" if frame.center is None else f"({frame.center[0]:.0f}, {frame.center[1]:.0f})"]
            for column, value in enumerate(values):
                table.setItem(row_index, column, QTableWidgetItem(value))
        table.resizeColumnsToContents()
        layout.addWidget(table)
        dialog.exec()

    def _start_calibration(self) -> None:
        if not self._job_can_start():
            return
        if self._worker is not None:
            return
        folder = QFileDialog.getExistingDirectory(self, "Open folder with chessboard images", str(self._dialog_directory("images")))
        if not folder:
            return
        images = sorted(
            [path for ext in ("*.png", "*.jpg", "*.jpeg", "*.bmp", "*.tiff")
             for path in Path(folder).glob(ext)]
        )
        if not images:
            self.statusBar().showMessage("No images found in the selected folder.")
            return
        self.run_button.setEnabled(False)
        self.compare_button.setEnabled(False)
        self.benchmark_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.statusBar().showMessage(f"Calibrating from {len(images)} images…")
        self.log_engine_event("INFO", f"Calibrating camera from {len(images)} images in {Path(folder).name}.")
        self._cancel_event = Event()
        self._worker = CalibrationWorker(images, self._cancel_event)
        self._connect_worker(self._show_calibration)
        self._worker.start()

    def _show_calibration(self, result: tuple) -> None:
        import numpy as np

        camera, dist, rms, views = result
        dialog = QDialog(self)
        dialog.setWindowTitle("VISOR Camera Calibration")
        dialog.resize(560, 320)
        layout = QVBoxLayout(dialog)
        note = QLabel(
            f"Calibrated from {views} chessboard views. RMS reprojection error: {rms:.2f} px. "
            "Use these intrinsics for PnP experiments on non-planar scenes."
        )
        note.setWordWrap(True)
        layout.addWidget(note)
        matrix_text = "\n".join("  ".join(f"{value:10.2f}" for value in row) for row in np.asarray(camera))
        for title, body in (("Camera matrix", matrix_text),
                            ("Distortion", "  ".join(f"{value:.4f}" for value in np.asarray(dist).ravel()))):
            layout.addWidget(QLabel(title))
            box = QPlainTextEdit()
            box.setReadOnly(True)
            box.setPlainText(body)
            layout.addWidget(box)
        dialog.exec()

    def _refresh_result_views(self) -> None:
        for label in self._result_arrays:
            self._refresh_one_view(label)

    def _refresh_visualization(self) -> None:
        result = self._latest_result
        if result is None or not hasattr(self, "view_toggles"):
            return
        rainbow_checked = self.view_toggles["rainbow_feature_colors"].isChecked()
        settings = replace(
            result.settings,
            show_match_lines=self.view_toggles["show_match_lines"].isChecked(),
            show_inliers=self.view_toggles["show_inliers"].isChecked(),
            show_outliers=self.view_toggles["show_outliers"].isChecked(),
            show_keypoints=self.view_toggles["show_keypoints"].isChecked(),
            show_geometry=self.view_toggles["show_geometry"].isChecked(),
            rainbow_feature_colors=rainbow_checked,
            feature_line_thickness=float(self.feature_thickness_slider.value() if hasattr(self, "feature_thickness_slider") else self.match_line_thickness.value()),
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

    @staticmethod
    def _find_repo_root() -> Path | None:
        search_roots = [Path.cwd()]
        current = Path.cwd()
        while True:
            search_roots.append(current)
            if (current / "pyproject.toml").exists() and (current / "src" / "visor").exists():
                return current
            if current.parent == current:
                break
            current = current.parent
        for path in search_roots:
            if (path / "pyproject.toml").exists() and (path / "src" / "visor").exists():
                return path
        return None

    def _update_learned_install_visibility(self) -> None:
        if not hasattr(self, "install_learned_button"):
            return
        if getattr(sys, "frozen", False):
            self.install_learned_button.setVisible(False)
            return
        missing = not is_lightglue_available() or not is_xfeat_available()
        self.install_learned_button.setVisible(missing)

    def _install_learned_engines(self) -> None:
        """Install learned-engine dependencies into the current Python environment.

        Uses the running interpreter so packages land in the active venv.
        Runs pip in a background thread so the UI stays responsive.
        Shows live output in the engine console.
        """
        if getattr(sys, "frozen", False):
            self.statusBar().showMessage("Additional learned engines are unavailable in this desktop distribution.")
            return
        if self._worker is not None:
            self.statusBar().showMessage("An analysis is already running. Wait for it to finish before installing.")
            return
        if not self._job_can_start():
            return

        python_exe = sys.executable
        install_lightglue = not is_lightglue_available()
        install_xfeat = not is_xfeat_available()

        if not install_lightglue and not install_xfeat:
            self.statusBar().showMessage("All learned-engine dependencies are already installed.")
            self._update_learned_install_visibility()
            return

        self.install_learned_button.setEnabled(False)
        self.run_button.setEnabled(False)
        self.compare_button.setEnabled(False)
        self.benchmark_button.setEnabled(False)
        self.cancel_button.setEnabled(False)

        what: list[str] = []
        if install_lightglue:
            what.append("LightGlue (SuperPoint / ALIKED / DISK / SIFT+LG)")
        if install_xfeat:
            what.append("XFeat (accelerated-features)")
        self.log_engine_event("INFO", f"Installing: {', '.join(what)}. This may take several minutes…")
        self.diagnostics_dock.show()
        self.statusBar().showMessage("Installing learned-engine dependencies — see Diagnostics for progress…")

        self._install_worker = InstallWorker(python_exe, install_lightglue, install_xfeat)
        self._install_worker.progress.connect(lambda msg: self.log_engine_event("PIP", msg))
        self._install_worker.completed.connect(self._on_install_completed)
        self._install_worker.finished.connect(self._on_install_finished)
        self._install_worker.start()

    def _on_install_completed(self, success: bool, message: str) -> None:
        level = "OK" if success else "ERROR"
        self.log_engine_event(level, message)
        if self._closing_requested:
            return
        ready = "Reference image" in self._paths and "Target image" in self._paths
        self.run_button.setEnabled(ready)
        self.compare_button.setEnabled(ready)
        self.benchmark_button.setEnabled("Reference image" in self._paths)
        if success:
            self.statusBar().showMessage(
                "Learned engines installed. Restart the app (python -m visor) to activate them in the engine selector."
            )
            # Attempt a soft reload of availability flags without full restart
            import importlib

            import visor.learned_engines as _le
            import visor.learned_extra as _lx
            try:
                importlib.reload(_le)
                importlib.reload(_lx)
            except Exception as exc:  # noqa: BLE001
                self.log_engine_event("WARNING", f"Engine discovery refresh failed: {exc}")
            self._update_learned_install_visibility()
            self._refresh_engine_selector()
        else:
            self.statusBar().showMessage(f"Install failed: {message}")
            self.install_learned_button.setEnabled(True)

    def _on_install_finished(self) -> None:
        if self._install_worker is not None:
            self._install_worker.deleteLater()
            self._install_worker = None
        self._finish_deferred_close()

    def _refresh_engine_selector(self) -> None:
        """Re-evaluate optional engine availability and update the selector items."""
        selected = self.engine_selector.currentText()
        self.engine_selector.blockSignals(True)
        # Remove all optional items (keep SIFT=0, ORB=1)
        while self.engine_selector.count() > 2:
            self.engine_selector.removeItem(2)
        for entry in engine_capabilities()[2:]:
            self._add_engine_entry(entry.name, entry.available, entry.reason)
        selected_index = self.engine_selector.findText(selected)
        self.engine_selector.setCurrentIndex(max(selected_index, 0))
        self.engine_selector.blockSignals(False)
        self._engine_changed(self.engine_selector.currentIndex())

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
        directory = self._dialog_directory("images")
        self.reference_input.set_browse_directory(directory)
        self.target_input.set_browse_directory(directory)

    def _dialog_directory(self, category: str) -> Path:
        stored = self._window_settings.value(f"paths/{category}")
        if isinstance(stored, str) and stored and Path(stored).is_absolute():
            return Path(stored)
        location = {"images": QStandardPaths.StandardLocation.PicturesLocation,
                    "videos": QStandardPaths.StandardLocation.MoviesLocation}.get(
                        category, QStandardPaths.StandardLocation.DocumentsLocation)
        return Path(QStandardPaths.writableLocation(location) or Path.home())

    def _suggested_export(self, name: str) -> str:
        return str(self._dialog_directory("exports") / name)

    def _remember_file_location(self, category: str, filename: str) -> None:
        self._window_settings.setValue(f"paths/{category}", str(Path(filename).resolve().parent))

    def closeEvent(self, event) -> None:
        installing = self._install_worker is not None and self._install_worker.isRunning()
        if self._worker is not None or installing:
            self._closing_requested = True
            self._jobs.shutdown()
            if self._cancel_event is not None:
                self._cancel_event.set()
            self.run_button.setEnabled(False)
            self.compare_button.setEnabled(False)
            self.benchmark_button.setEnabled(False)
            self.cancel_button.setEnabled(False)
            self.statusBar().showMessage(
                "Closing after dependency installation finishes…" if installing else
                "Closing after the active operation reaches a cancellation boundary…"
            )
            event.ignore()
            return
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
        result = self._latest_result
        match_fields: list[tuple[str, str]] = []
        for match_index, match in enumerate(result.match_set.matches):
            if match.train_index != index:
                continue
            mask = result.geometry.inlier_mask
            membership = "not classified" if match_index >= len(mask) else ("solver inlier" if mask[match_index] else "solver outlier")
            match_fields.append((f"Correspondence #{match_index}", f"Reference keypoint #{match.query_index}; {membership}"))
            if match.distance is not None:
                match_fields.append(("Descriptor distance", f"{match.distance:.5g}"))
            if match.confidence is not None:
                match_fields.append(("Assignment score", f"{match.confidence:.5g} (not calibrated accuracy)"))
        if not match_fields:
            match_fields.append(("Correspondences", "This target keypoint has no accepted correspondence."))
        self.details_panel.append_keypoint(self._latest_result.engine, index, point,
                                           self._latest_result.target_features.keypoint_metadata, tuple(match_fields))
        self.statusBar().showMessage(f"Selected {self._latest_result.engine} target keypoint #{index} at ({point.x:.1f}, {point.y:.1f}) px")

    def _on_image_changed(self, role: str, path: object) -> None:
        self._invalidate_analysis()
        if isinstance(path, Path):
            self._paths[role] = path
            self._remember_file_location("images", str(path))
            self.reference_input.set_browse_directory(path.parent)
            self.target_input.set_browse_directory(path.parent)
            self._clear_result_views()
            self._latest_benchmark = None
            self.statusBar().showMessage(f"Loaded {role.lower()}: {path.name}")
            if "Reference image" in self._paths and "Target image" in self._paths:
                self._add_current_pair_to_history()
        else:
            self._paths.pop(role, None)
            self._clear_result_views()
            self.statusBar().showMessage(f"Unable to load {role.lower()} image.")
        self._update_overview_summary()
        if self._worker is not None:
            self.statusBar().showMessage("Image inputs changed; cancelling and discarding the previous run.")
        if hasattr(self, "run_button"):
            installing = self._install_worker is not None and self._install_worker.isRunning()
            idle = self._worker is None and not installing and not self._closing_requested
            ready = "Reference image" in self._paths and "Target image" in self._paths and idle
            self.run_button.setEnabled(ready)
            self.compare_button.setEnabled(ready)
            self.benchmark_button.setEnabled("Reference image" in self._paths and idle)

    def _save_project(self) -> None:
        if len(self._paths) != 2:
            self.statusBar().showMessage("Add both images before saving a project.")
            return
        suggested = self._project_path or self._dialog_directory("projects") / "analysis.visor"
        filename, _ = QFileDialog.getSaveFileName(self, "Save VISOR project", str(suggested), "VISOR project (*.visor)")
        if not filename:
            return
        settings, sift, orb, matching, method = self._read_configurations()
        session = ProjectSession(
            str(self._paths["Reference image"]), str(self._paths["Target image"]),
            cast(EngineName, self.engine_selector.currentText()), settings, sift, orb, matching, method,
        )
        try:
            save_project(session, Path(filename))
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, "Could not save project", str(exc))
            return
        self._project_path = Path(filename).resolve()
        self._remember_file_location("projects", filename)
        self.statusBar().showMessage(f"Project saved: {Path(filename).name}")

    def _load_project(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(self, "Open VISOR project", str(self._dialog_directory("projects")), "VISOR project (*.visor)")
        if not filename:
            return
        try:
            session = load_project(Path(filename))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            QMessageBox.critical(self, "Could not open project", str(exc))
            return
        engine_index = self.engine_selector.findText(session.engine)
        if engine_index < 0 or not self.engine_selector.model().item(engine_index).isEnabled():
            QMessageBox.warning(self, "Project engine unavailable",
                                f"{session.engine} is unavailable in this runtime. The project was not loaded with a substitute engine.")
            return
        self.engine_selector.setCurrentIndex(engine_index)
        self.ratio_control.setValue(session.settings.ratio_threshold)
        self.ransac_control.setValue(session.settings.ransac_threshold)
        matching = session.matching or MatchingOptions(ratio_threshold=session.settings.ratio_threshold)
        strategy = ("Cross-check" if matching.cross_check else "FLANN" if matching.use_flann
                    else "Symmetric ratio" if matching.symmetric_ratio else "Default ratio test")
        self.matcher_strategy.setCurrentText(strategy)
        self.ratio_control.setValue(matching.ratio_threshold)
        self.robust_estimator.setCurrentText(session.robust_method)
        for name, action in self.view_toggles.items():
            action.setChecked(getattr(session.settings, name))
        self.match_line_thickness.setValue(round(session.settings.feature_line_thickness))
        self._sync_overlay_controls()
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
        self._project_path = Path(filename).resolve()
        self._remember_file_location("projects", filename)
        if self.reference_input.image_path is None or self.target_input.image_path is None:
            self.statusBar().showMessage("Project settings loaded, but an image could not be decoded. Choose a replacement image.")
        else:
            self.statusBar().showMessage(f"Project loaded: {Path(filename).name}")

    def _export_json(self) -> None:
        self._export_analysis(export_json, "JSON files (*.json)", "analysis.json")

    def _export_html_report(self) -> None:
        if self._latest_result is None:
            self.statusBar().showMessage("Run an analysis before exporting a report.")
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Export HTML report", self._suggested_export("analysis_report.html"), "HTML files (*.html)")
        if not filename:
            return
        try:
            export_html_report(self._latest_result, Path(filename))
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, "Export failed", str(exc))
            return
        self._remember_file_location("exports", filename)
        self.statusBar().showMessage(f"HTML report exported: {Path(filename).name}")

    def _export_csv(self) -> None:
        self._export_analysis(export_csv, "CSV files (*.csv)", "metrics.csv")

    def _export_comparison_csv(self) -> None:
        comparison = getattr(self, "_latest_comparison", None)
        if comparison is None:
            self.statusBar().showMessage("Run Compare SIFT / ORB before exporting comparison metrics.")
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Export comparison", self._suggested_export("comparison.csv"), "CSV files (*.csv)")
        if not filename:
            return
        try:
            export_comparison_csv(comparison, Path(filename))
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, "Export failed", str(exc))
            return
        self._remember_file_location("exports", filename)
        self.statusBar().showMessage(f"Comparison exported: {Path(filename).name}")

    def _export_benchmark_csv(self) -> None:
        report = getattr(self, "_latest_benchmark", None)
        if report is None:
            self.statusBar().showMessage("Run the benchmark lab before exporting benchmark metrics.")
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Export benchmark", self._suggested_export("benchmark.csv"), "CSV files (*.csv)")
        if not filename:
            return
        try:
            export_benchmark_csv(report, Path(filename))
        except (OSError, ValueError, IndexError) as exc:
            QMessageBox.critical(self, "Export failed", str(exc))
            return
        self._remember_file_location("exports", filename)
        self.statusBar().showMessage(f"Benchmark exported: {Path(filename).name}")

    def _export_batch_csv(self, report: BatchReport | None = None) -> None:
        report = report if report is not None else self._latest_batch
        if report is None:
            self.statusBar().showMessage("Run a batch from a manifest before exporting batch metrics.")
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Export batch", self._suggested_export("batch.csv"), "CSV files (*.csv)")
        if not filename:
            return
        try:
            export_batch_csv(report, Path(filename))
        except (OSError, ValueError, IndexError) as exc:
            QMessageBox.critical(self, "Export failed", str(exc))
            return
        self._remember_file_location("exports", filename)
        self.statusBar().showMessage(f"Batch exported: {Path(filename).name}")

    def _export_analysis(self, exporter, file_filter: str, default_name: str) -> None:
        if self._latest_result is None:
            self.statusBar().showMessage("Run an analysis before exporting results.")
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Export analysis", self._suggested_export(default_name), file_filter)
        if not filename:
            return
        try:
            exporter(self._latest_result, Path(filename))
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, "Export failed", str(exc))
            return
        self._remember_file_location("exports", filename)
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
            self, "Export visualization", self._suggested_export("visor-result.png"), "PNG (*.png);;JPEG (*.jpg *.jpeg)",
        )
        if not filename:
            return
        try:
            export_visualization(image, Path(filename))
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, "Export failed", str(exc))
            return
        self._remember_file_location("exports", filename)
        self.statusBar().showMessage(f"Visualization exported: {Path(filename).name}")

    def _show_engine_status(self) -> None:
        from visor.ui.engine_status import EngineStatusDialog
        dlg = EngineStatusDialog(self)
        dlg.exec()

    def _show_about(self) -> None:
        self.statusBar().showMessage("VISOR 0.2.0 — classical + learned image feature registration workspace")

    def _apply_theme(self) -> None:
        self.setStyleSheet(
            """
            QWidget { color: #dce3ec; }
            QMainWindow, QWidget#workspace { background: #11151b; color: #e6eaf0; }
            QScrollArea, QScrollArea > QWidget > QWidget { background: #171c23; }
            QListWidget { background: #1b222c; color: #dce3ec; border: 1px solid #3c4c61; }
            QListWidget::item { padding: 5px; }
            QListWidget::item:selected { background: #304d6e; color: #edf2f8; }
            QScrollBar:vertical { background: #171c23; width: 12px; margin: 0; }
            QScrollBar::handle:vertical { background: #46566b; min-height: 24px; border-radius: 3px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: #171c23; }
            QMenuBar { background: #171c23; color: #cbd2dc; padding: 5px; }
            QMenuBar::item:selected, QMenu::item:selected { background: #293240; }
            QMenu { background: #1b222c; color: #e6eaf0; border: 1px solid #303947; }
            QStatusBar { background: #171c23; color: #aeb7c4; border-top: 1px solid #29313b; }
            QWidget#inputPanel, QWidget#welcomePanel { background: #171c23; border: 1px solid #29313b; border-radius: 8px; }
            QFrame#imageDropWidget { background: #1b222c; border: 1px solid #303947; border-radius: 7px; }
            QFrame#imageDropWidget:hover { border-color: #6589b8; }
            QLabel#sectionTitle { font-size: 15px; font-weight: 600; color: #e6eaf0; }
            QLabel#mutedText { color: #a9b4c2; }
            QLabel#errorText { color: #f08b86; }
            QLabel#imagePreview { color: #758396; background: #141920; border: 1px dashed #394555; border-radius: 5px; }
            QPushButton { color: #dce3ec; background: #293545; border: 1px solid #3c4c61; border-radius: 4px; padding: 7px 9px; }
            QPushButton:hover { background: #34465c; }
            QPushButton:checked { background: #304d6e; border-color: #6589b8; }
            QPushButton:disabled { color: #788493; background: #27303b; border-color: #333d49; }
            QPushButton#primaryButton { color: #f1f6fc; background: #356ba5; border: 1px solid #477fb9; border-radius: 5px; padding: 8px 14px; font-weight: 600; }
            QPushButton#primaryButton:hover { background: #407bb8; }
            QPushButton#primaryButton:disabled { color: #788493; background: #27303b; border-color: #333d49; }
            QComboBox { color: #dce3ec; background: #202a36; border: 1px solid #3c4c61; border-radius: 5px; padding: 7px 9px; }
            QComboBox QAbstractItemView { background: #202a36; color: #dce3ec; selection-background-color: #304d6e; }
            QComboBox QAbstractItemView::item:disabled { color: #788493; }
            QSpinBox, QDoubleSpinBox { color: #dce3ec; background: #202a36; border: 1px solid #3c4c61; border-radius: 3px; padding: 4px; }
            QSlider::groove:horizontal { height: 4px; background: #394555; border-radius: 2px; }
            QSlider::handle:horizontal { width: 12px; margin: -5px 0; background: #aebfd4; border: 1px solid #536980; border-radius: 3px; }
            QPushButton:focus, QPushButton#primaryButton:focus, QComboBox:focus,
            QSpinBox:focus, QDoubleSpinBox:focus { border: 1px solid #9dc6f5; }
            QSlider::handle:horizontal:focus { background: #9dc6f5; border-color: #e0edff; }
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
            QPlainTextEdit#engineConsole {
                background: #10161d;
                color: #dfe8f6;
                border: 1px solid #303947;
                border-radius: 6px;
                font-family: Consolas, "SFMono-Regular", monospace;
                font-size: 11px;
            }
            """
        )
