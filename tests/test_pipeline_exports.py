import json
from pathlib import Path

import pytest

from visor.engines import ORBConfiguration, SIFTConfiguration
from visor.exporting import (
    ProjectSession,
    export_csv,
    export_html_report,
    export_json,
    export_visualization,
    load_project,
    save_project,
)
from visor.models import AnalysisSettings
from visor.pipeline import analyze
from visor.visualization import render_match_canvas


def test_sift_and_orb_pipeline_localize_synthetic_pair(textured_pair):
    reference, target, _, _, _ = textured_pair
    for engine in ("SIFT", "ORB"):
        result = analyze(reference, target, engine)
        assert result.reference_size == (560, 420)
        assert result.match_set.matcher
        assert result.performance.total_ms >= result.performance.image_loading_ms
        assert len(result.matches_image.shape) == 3
        assert result.geometry.inlier_count >= 0
        assert result.performance.image_loading_ms > 0


def test_json_csv_and_project_round_trip(textured_pair, tmp_path):
    reference, target, _, _, _ = textured_pair
    result = analyze(reference, target, "ORB")
    json_path, csv_path, project_path = tmp_path / "result.json", tmp_path / "result.csv", tmp_path / "session.visor"
    export_json(result, json_path)
    export_csv(result, csv_path)
    assert json.loads(json_path.read_text(encoding="utf-8"))["engine"] == "ORB"
    assert "engine" in csv_path.read_text(encoding="utf-8-sig").splitlines()[0]
    session = ProjectSession(str(reference), str(target), "ORB", AnalysisSettings(), SIFTConfiguration(), ORBConfiguration())
    save_project(session, project_path)
    loaded = load_project(project_path)
    assert loaded.engine == "ORB"
    assert loaded.reference_path == str(reference)
    image_path = tmp_path / "localization.png"
    export_visualization(result.localization_image, image_path)
    assert image_path.is_file() and image_path.stat().st_size > 0


def test_visualization_filters_can_change_without_reanalysis(textured_pair):
    reference, target, _, _, _ = textured_pair
    result = analyze(reference, target, "ORB")
    settings = AnalysisSettings(show_match_lines=False, show_inliers=False, show_outliers=False, show_keypoints=True)
    overlay = render_match_canvas(
        result.reference_image, result.target_image, result.reference_features,
        result.target_features, result.match_set, result.geometry, settings,
    )
    assert overlay.shape == result.matches_image.shape
    assert not (overlay == result.matches_image).all()


def test_html_report_exports_analysis_summary(textured_pair, tmp_path):
    reference, target, _, _, _ = textured_pair
    result = analyze(reference, target, "ORB")
    report_path = tmp_path / "analysis_report.html"
    export_html_report(result, report_path)
    assert report_path.is_file() and report_path.stat().st_size > 0
    html = report_path.read_text(encoding="utf-8")
    assert "<html" in html.lower()
    assert "ORB" in html
    assert "geometry" in html.lower()


def test_windows_installer_manifest_is_present():
    installer = Path(__file__).resolve().parents[1] / "scripts" / "VISOR.iss"
    assert installer.exists()
    content = installer.read_text(encoding="utf-8")
    assert "AppName=VISOR" in content
    assert "OutputBaseFilename=VISOR-setup" in content
    assert "Source: \"dist\\VISOR\\VISOR.exe\"" in content


def test_invalid_engine_name_is_rejected(textured_pair):
    reference, target, _, _, _ = textured_pair
    with pytest.raises(ValueError, match="engine"):
        analyze(reference, target, "UnknownEngine")


def test_load_project_accepts_learned_engine_names(tmp_path):
    reference_path = tmp_path / "reference.png"
    target_path = tmp_path / "target.png"
    reference_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"fake")
    target_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"fake")
    project_path = tmp_path / "learned.visor"
    project_path.write_text(
        json.dumps({
            "format_version": 1,
            "application_version": "0.1.0",
            "reference_path": str(reference_path),
            "target_path": str(target_path),
            "engine": "SuperPoint+LightGlue",
            "settings": {},
            "sift": {},
            "orb": {},
        }),
        encoding="utf-8",
    )
    loaded = load_project(project_path)
    assert loaded.engine == "SuperPoint+LightGlue"
