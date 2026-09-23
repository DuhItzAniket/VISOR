import json

from visor.engines import ORBConfiguration, SIFTConfiguration
from visor.exporting import (
    ProjectSession,
    export_csv,
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
