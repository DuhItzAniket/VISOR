"""Session replay preserves effective matching/estimation and portable inputs."""

import json
import os
import shutil
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from visor.engines import ORBConfiguration, SIFTConfiguration
from visor.exporting import ProjectSession, load_project, save_project
from visor.matching_strategies import MatchingOptions
from visor.models import AnalysisSettings
from visor.ui import main_window


def _session(reference, target):
    return ProjectSession(str(reference), str(target), "ORB",
                          AnalysisSettings(ratio_threshold=0.8, rainbow_feature_colors=True, feature_line_thickness=3),
                          SIFTConfiguration(), ORBConfiguration(), MatchingOptions(ratio_threshold=0.8, symmetric_ratio=True),
                          "MAGSAC")


def test_project_v2_survives_directory_move(tmp_path):
    directory = tmp_path / "original"
    (directory / "images").mkdir(parents=True)
    reference = directory / "images/reference.png"
    reference.write_bytes(b"fixture")
    path = directory / "session.visor"
    save_project(_session(reference, reference), path)
    data = json.loads(path.read_text())
    assert data["format_version"] == 2 and data["reference_path"] == "images/reference.png"
    relocated = tmp_path / "relocated"
    shutil.copytree(directory, relocated)
    loaded = load_project(relocated / path.name)
    assert loaded.reference_path == str(relocated / "images/reference.png")
    assert loaded.matching.symmetric_ratio and loaded.matching.ratio_threshold == 0.8
    assert loaded.robust_method == "MAGSAC"


def test_v1_migrates_matching_ratio_and_estimator(tmp_path):
    image = tmp_path / "image.png"
    image.write_bytes(b"fixture")
    path = tmp_path / "legacy.visor"
    path.write_text(json.dumps({"format_version": 1, "reference_path": str(image), "target_path": str(image),
                                "engine": "SIFT", "settings": {"ratio_threshold": 0.9}}))
    loaded = load_project(path)
    assert loaded.matching.ratio_threshold == 0.9
    assert loaded.robust_method == "RANSAC"


def test_ui_load_restores_strategy_estimator_and_overlay(tmp_path, monkeypatch, qt_wait):
    app = QApplication.instance() or QApplication([])
    settings = QSettings(str(tmp_path / "window.ini"), QSettings.Format.IniFormat)
    monkeypatch.setattr(main_window, "QSettings", lambda *args: settings)
    image = Path(__file__).parent / "data/reference.png"
    path = tmp_path / "session.visor"
    save_project(_session(image, image), path)
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(path), ""))
    window = main_window.MainWindow()
    try:
        window._load_project()
        qt_wait(lambda: not window._inputs_loading())
        assert window.matcher_strategy.currentText() == "Symmetric ratio"
        assert window.robust_estimator.currentText() == "MAGSAC"
        assert window.feature_thickness_slider.value() == 3
        assert window.feature_color_button.isChecked()
        assert window._read_configurations()[3].symmetric_ratio
    finally:
        window.close()
        app.processEvents()


def test_missing_project_engine_is_not_substituted(tmp_path, monkeypatch):
    from dataclasses import replace

    app = QApplication.instance() or QApplication([])
    settings = QSettings(str(tmp_path / "window.ini"), QSettings.Format.IniFormat)
    monkeypatch.setattr(main_window, "QSettings", lambda *args: settings)
    image = Path(__file__).parent / "data/reference.png"
    path = tmp_path / "session.visor"
    save_project(replace(_session(image, image), engine="XFeat"), path)
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(path), ""))
    messages = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: messages.append(args[2]))
    window = main_window.MainWindow()
    try:
        index = window.engine_selector.findText("XFeat")
        if index >= 0:
            window.engine_selector.model().item(index).setEnabled(False)
        window._load_project()
        assert messages and "substitute" in messages[0]
        assert not window._paths
    finally:
        window.close()
        app.processEvents()
