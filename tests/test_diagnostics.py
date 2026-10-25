"""Fit diagnostics describe measured support/residuals, never confidence."""

import os

import numpy as np
import pytest

from visor.exporting import analysis_document, export_csv
from visor.geometry_validation import validate_planar_fit
from visor.pipeline import analyze


def _fit(*, outlier=False, target_size=(200, 200)):
    source = np.array([[5, 5], [90, 5], [90, 90], [5, 90], [40, 55], [65, 45]],
                      dtype=np.float64).reshape(-1, 1, 2)
    target = source + np.array([10, 8])
    target[-1, 0, 0] += 1
    mask = np.ones(6, np.uint8)
    if outlier:
        mask[-1] = 0
    matrix = np.array([[1, 0, 10], [0, 1, 8], [0, 0, 1]], dtype=np.float64)
    return validate_planar_fit(matrix, mask, source, target, (100, 100), target_size, "test")


def test_hull_area_and_residual_quantiles_are_measured():
    geometry = _fit()
    assert geometry.valid
    diagnostic = geometry.diagnostics
    assert diagnostic.reference_support_hull_fraction == pytest.approx(85**2 / 99**2)
    assert diagnostic.target_support_hull_fraction == pytest.approx(85**2 / 199**2)
    assert diagnostic.projected_area_px2 == 99**2
    assert diagnostic.projected_area_target_fraction == pytest.approx(99**2 / 199**2)
    assert diagnostic.median_inlier_residual_px == 0
    assert diagnostic.p95_inlier_residual_px == pytest.approx(0.75)
    assert diagnostic.maximum_inlier_residual_px == 1


def test_outliers_do_not_contaminate_inlier_residuals():
    geometry = _fit(outlier=True, target_size=None)
    assert geometry.valid
    assert geometry.diagnostics.maximum_inlier_residual_px == 0
    assert geometry.diagnostics.target_support_hull_fraction is None
    assert geometry.diagnostics.projected_area_target_fraction is None


def test_exported_diagnostics_are_defined_and_not_confidence(textured_pair, tmp_path):
    reference, target, *_ = textured_pair
    result = analyze(reference, target, "SIFT")
    diagnostic = analysis_document(result)["geometry"]["diagnostics"]
    assert diagnostic["maximum_inlier_residual_px"] >= diagnostic["p95_inlier_residual_px"]
    assert not any("confidence" in key or "accuracy" in key for key in diagnostic)
    path = tmp_path / "result.csv"
    export_csv(result, path)
    assert "p95_inlier_residual_px" in path.read_text(encoding="utf-8-sig")


def test_selected_target_keypoint_exposes_correspondence_membership(textured_pair, tmp_path, monkeypatch):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import QApplication

    from visor.ui import main_window

    app = QApplication.instance() or QApplication([])
    settings = QSettings(str(tmp_path / "window.ini"), QSettings.Format.IniFormat)
    monkeypatch.setattr(main_window, "QSettings", lambda *args: settings)
    reference, target, *_ = textured_pair
    result = analyze(reference, target, "SIFT")
    window = main_window.MainWindow()
    try:
        window._show_result(result)
        match_index = next(i for i, flag in enumerate(result.geometry.inlier_mask) if flag)
        match = result.match_set.matches[match_index]
        point = result.target_features.keypoints[match.train_index]
        window._inspect_keypoint(point.x, point.y)
        fields = window.details_panel._keypoints_data[-1][1]
        assert any("solver inlier" in value for _, value in fields)
        assert any(label == "Descriptor distance" for label, _ in fields)
    finally:
        window.close()
        app.processEvents()
