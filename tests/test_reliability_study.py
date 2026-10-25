"""Study policies cannot invent fits, lose failures, or tune on reporting rows."""

import copy
import gzip
import hashlib
import json
import sys

import pytest

from visor.reliability_study import DiagnosticGate, gate_counts, main, report_frozen_gates, select_gates


def _row(name="good", *, inliers=12, support=0.2, residual=1, corner=1, negative=False, split="development"):
    return {"pair": name, "split": split, "engine": "ORB", "geometry_valid": True, "error": None,
            "has_ground_truth": not negative, "expected_match": not negative, "corner_error_mean_px": corner,
            "analysis": {"geometry": {"valid": True, "inliers": inliers, "diagnostics": {
                "reference_support_hull_fraction": support, "p95_inlier_residual_px": residual}}}}


def _report(rows):
    return {"schema_version": 1, "rows": rows, "configuration": {"seed": 0}, "input_sha256": {"dev.ppm": "hash-dev"}}


@pytest.mark.parametrize("field,value", [("inliers", None), ("inliers", True),
                                          ("reference_support_hull_fraction", None),
                                          ("reference_support_hull_fraction", float("nan")),
                                          ("p95_inlier_residual_px", float("inf"))])
def test_required_unavailable_diagnostics_cannot_pass(field, value):
    row = _row(inliers=10, support=0.1, residual=3)
    gate = DiagnosticGate(10, 0.1, 3)
    assert gate.retains(row)  # inclusive boundaries
    geometry = row["analysis"]["geometry"]
    (geometry if field == "inliers" else geometry["diagnostics"])[field] = value
    assert not gate.retains(row)


def test_gate_never_converts_failed_fit_or_runtime_error_to_acceptance():
    gate = DiagnosticGate(10, 0.01, None)
    row = _row()
    row["geometry_valid"] = False
    assert not gate.retains(row)
    row["geometry_valid"] = True
    row["error"] = "native failure"
    assert not gate.retains(row)


def test_selection_uses_development_only_and_least_restrictive_exact_tie():
    report = _report([_row(), _row("wrong", inliers=8, corner=100),
                      _row("negative", support=0.001, negative=True, corner=None)])
    original = copy.deepcopy(report)
    selected = select_gates(report)["engines"]["ORB"]
    assert len(selected["candidates"]) == 27
    assert selected["selected_gate"] == {"minimum_inliers": 10, "minimum_reference_support": 0.01,
                                          "maximum_residual_p95_px": None}
    assert selected["selected_counts"]["accepted_negatives"] == 0
    assert selected["selected_counts"]["accepted_truth_mean_corner_gt_5px"] == 0
    assert report == original
    report["rows"][0]["split"] = "heldout"
    with pytest.raises(ValueError, match="development"):
        select_gates(report)


def test_retention_requirement_is_inclusive_and_zero_accurate_baseline_has_no_choice():
    rows = [_row(f"good-{index}", inliers=50 if index < 3 else 12) for index in range(4)]
    rows.append(_row("wrong", inliers=25, corner=100))
    selected = select_gates(_report(rows))["engines"]["ORB"]
    assert selected["selected_gate"]["minimum_inliers"] == 40
    assert selected["selected_counts"]["accepted_truth_mean_corner_le_3px"] == 3
    selected = select_gates(_report([_row(corner=100)]))["engines"]["ORB"]
    assert selected["selected_gate"] is None and selected["selected_counts"] is None


def test_failure_denominators_and_annotation_errors_remain_distinct():
    failed, runtime, annotation = _row("failed"), _row("runtime"), _row("bad-truth")
    for row in (failed, runtime, annotation):
        row["geometry_valid"] = False
        row["corner_error_mean_px"] = None
    runtime["error"] = "missing input"
    annotation["error"], annotation["annotation_error"] = "invalid truth", True
    counts = gate_counts([_row(), failed, runtime, annotation])
    assert counts["truth_attempts"] == 3 and counts["accepted_truth_mean_corner_le_3px"] == 1
    assert counts["runtime_errors"] == counts["annotation_errors"] == 1
    assert counts["negative_attempts"] == 0


def test_reporting_uses_frozen_choice_and_rejects_overlap_or_changed_execution():
    selection = select_gates(_report([_row()]))
    heldout = _report([_row("new-good", split="heldout"), _row("new-wrong", inliers=8, corner=100, split="heldout")])
    heldout["input_sha256"] = {"heldout.ppm": "hash-heldout"}
    result = report_frozen_gates(heldout, selection)
    counts = result["engines"]["ORB"]
    assert counts["accurate_positive_retention"] == 1
    assert counts["gated"]["truth_attempts"] == 2
    assert [item["retained_by_gate"] for item in result["decisions"]] == [True, False]
    heldout["rows"][0]["pair"] = "good"
    with pytest.raises(ValueError, match="pair ids overlap"):
        report_frozen_gates(heldout, selection)
    heldout["rows"][0]["pair"] = "new-good"
    heldout["input_sha256"]["heldout.ppm"] = "hash-dev"
    with pytest.raises(ValueError, match="images overlap"):
        report_frozen_gates(heldout, selection)
    heldout["configuration"] = {"seed": 1}
    with pytest.raises(ValueError, match="configuration"):
        report_frozen_gates(heldout, selection)


def test_cli_reads_compressed_evidence_records_hash_and_refuses_overwrite(tmp_path, monkeypatch):
    source, output = tmp_path / "development.json.gz", tmp_path / "selection.json"
    source.write_bytes(gzip.compress(json.dumps(_report([_row()])).encode()))
    monkeypatch.setattr(sys, "argv", ["study", "select", str(source), str(output)])
    assert main() == 0
    selected = json.loads(output.read_text())
    assert selected["development_report_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    original = output.read_bytes()
    with pytest.raises(SystemExit) as failure:
        main()
    assert failure.value.code == 2 and output.read_bytes() == original
