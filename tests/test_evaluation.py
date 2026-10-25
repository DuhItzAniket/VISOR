"""Evaluation preserves failures and separates truth-backed error from fit residual."""

import json
from pathlib import Path

import numpy as np
import pytest

from visor.evaluate import corner_errors, evaluate, summarize
from visor.evaluation_data import load_evaluation_manifest, prepare_hpatches, prepare_synthetic


def test_corner_error_convention():
    errors = corner_errors(np.array([[1, 0, 3], [0, 1, 4], [0, 0, 1]], float), np.eye(3), (100, 80))
    assert errors == {"corner_error_mean_px": 5, "corner_error_rmse_px": 5, "corner_error_max_px": 5}
    with pytest.raises(ValueError, match="horizon"):
        corner_errors(np.eye(3), np.array([[1, 0, 0], [0, 1, 0], [-0.02, 0, 1]]), (100, 80))


def test_synthetic_runner_records_raw_attempts_and_portable_provenance(tmp_path):
    source = Path(__file__).parent / "data/golden_reference.png"
    manifest = prepare_synthetic(source, tmp_path / "development")
    report = evaluate(manifest, repetitions=2, warmup=1, feature_budget=1000)
    assert len(report["warmup_rows"]) == 6 and len(report["rows"]) == 12
    assert len(report["input_sha256"]) == 4
    assert all(value and len(value) == 64 for value in report["input_sha256"].values())
    assert report["manifest_sha256"]
    for row in report["rows"]:
        assert row["error"] is None
        if row["pair"] == "known-warp":
            assert row["corner_error_max_px"] < 3
            assert row["analysis"]["geometry"]["mean_inlier_reprojection_error_px"] is not None
        else:
            assert row["corner_error_mean_px"] is None
        assert not Path(row["analysis"]["inputs"]["reference_path"]).is_absolute()
    assert report["summary"]["SIFT"]["ground_truth_attempts"] == 2
    assert report["summary"]["ORB"]["negative_attempts"] == 4
    json.dumps(report, allow_nan=False)


def test_runtime_failure_is_a_row_in_the_denominator(tmp_path):
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps({"version": 1, "pairs": [{"id": "missing", "reference": "no.png",
                           "target": "missing.png", "homography": np.eye(3).tolist()}]}))
    report = evaluate(path, engines=("SIFT",), repetitions=2, warmup=0)
    assert len(report["rows"]) == 2
    assert all(row["error"] for row in report["rows"])
    assert report["summary"]["SIFT"]["attempts"] == 2
    assert report["summary"]["SIFT"]["accuracy_at_mean_corner_px"]["3"] == 0


def test_failed_fits_and_runtime_errors_are_not_removed_from_accuracy():
    rows = []
    for valid, error, corner in [(True, None, 1.0), (False, None, None), (False, "missing runtime", None)]:
        rows.append({"engine": "SIFT", "geometry_valid": valid, "error": error,
                     "corner_error_mean_px": corner, "has_ground_truth": True, "expected_match": True, "wall_ms": 1.0})
    summary = summarize(rows)["SIFT"]
    assert summary["accuracy_at_mean_corner_px"]["3"] == pytest.approx(1 / 3)
    assert summary["fit_rate"] == pytest.approx(1 / 3)
    assert summary["false_accept_rate"] is None


@pytest.mark.parametrize("change", [
    {"homography": [[1, 0], [0, 1]]}, {"homography": np.zeros((3, 3)).tolist()},
    {"expected_match": "false"}, {"homography": np.eye(3).tolist(), "expected_match": False},
])
def test_bad_annotations_are_rejected(tmp_path, change):
    pair = {"reference": "a.png", "target": "b.png", **change}
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps({"version": 1, "pairs": [pair]}))
    with pytest.raises(ValueError):
        load_evaluation_manifest(path)


def test_splits_cannot_be_mixed_in_one_summary(tmp_path):
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps({"version": 1, "pairs": [
        {"id": split, "reference": "a.png", "target": "b.png", "split": split}
        for split in ("development", "heldout")]}))
    with pytest.raises(ValueError, match="separately"):
        evaluate(path)


def test_hpatches_loader_reports_absent_pairs(tmp_path):
    sequence = tmp_path / "sequences/i_example"
    sequence.mkdir(parents=True)
    for name in ("1.ppm", "2.ppm"):
        (sequence / name).write_bytes(b"fixture only; loader does not infer image content")
    np.savetxt(sequence / "H_1_2", np.eye(3))
    manifest = tmp_path / "manifest.json"
    document = prepare_hpatches(sequence.parent, manifest)
    assert len(document["pairs"]) == 1 and len(document["skipped"]) == 4
    _, pairs = load_evaluation_manifest(manifest)
    assert pairs[0].split == "heldout" and pairs[0].condition == "illumination"
    assert pairs[0].reference == sequence / "1.ppm"
    with pytest.raises(ValueError, match="absent"):
        prepare_hpatches(tmp_path / "missing", tmp_path / "other.json")


def test_cli_refuses_overwriting_inputs(tmp_path, monkeypatch):
    import sys

    from visor.evaluate import main

    path = tmp_path / "manifest.json"
    text = json.dumps({"version": 1, "pairs": [{"reference": "a.png", "target": "b.png"}]})
    path.write_text(text)
    monkeypatch.setattr(sys, "argv", ["evaluate", "run", str(path), str(path)])
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2 and path.read_text() == text
