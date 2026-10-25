"""Offline diagnostic-gate study; never changes registration results or defaults."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from dataclasses import asdict, dataclass
from itertools import product
from math import inf, isfinite
from pathlib import Path
from typing import Any


def _number(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(value) else None


@dataclass(frozen=True)
class DiagnosticGate:
    minimum_inliers: int
    minimum_reference_support: float
    maximum_residual_p95_px: float | None

    def __post_init__(self) -> None:
        if isinstance(self.minimum_inliers, bool) or not isinstance(self.minimum_inliers, int) or self.minimum_inliers < 4:
            raise ValueError("Minimum inliers must be an integer of at least four.")
        support = _number(self.minimum_reference_support)
        cap = _number(self.maximum_residual_p95_px)
        if support is None or not 0 <= support <= 1:
            raise ValueError("Reference support must be finite and between zero and one.")
        if self.maximum_residual_p95_px is not None and (cap is None or cap <= 0):
            raise ValueError("Residual cap must be finite and positive, or null.")

    def retains(self, row: dict[str, Any]) -> bool:
        if row.get("geometry_valid") is not True or row.get("error") is not None:
            return False
        geometry = (row.get("analysis") or {}).get("geometry") or {}
        diagnostics = geometry.get("diagnostics") or {}
        inliers = _number(geometry.get("inliers"))
        support = _number(diagnostics.get("reference_support_hull_fraction"))
        residual = _number(diagnostics.get("p95_inlier_residual_px"))
        return (geometry.get("valid") is True and inliers is not None and inliers >= self.minimum_inliers
                and support is not None and support >= self.minimum_reference_support
                and (self.maximum_residual_p95_px is None
                     or residual is not None and residual <= self.maximum_residual_p95_px))


def gate_counts(rows: list[dict[str, Any]], gate: DiagnosticGate | None = None) -> dict[str, Any]:
    """Keep failed attempts in truth/negative denominators; no error becomes accuracy."""
    accepted = lambda row: (row.get("geometry_valid") is True and row.get("error") is None
                            and (gate is None or gate.retains(row)))
    truth = [row for row in rows if row.get("has_ground_truth") and not row.get("annotation_error")]
    negatives = [row for row in rows if row.get("expected_match") is False]

    def accurate(row, threshold):
        error = _number(row.get("corner_error_mean_px"))
        return accepted(row) and error is not None and error <= threshold

    return {
        "attempts": len(rows), "distinct_pairs": len({row["pair"] for row in rows}),
        "runtime_errors": sum(row.get("error") is not None and not row.get("annotation_error") for row in rows),
        "annotation_errors": sum(bool(row.get("annotation_error")) for row in rows),
        "truth_attempts": len(truth), "negative_attempts": len(negatives),
        "baseline_failed_attempts": sum(not row.get("geometry_valid") or row.get("error") is not None for row in rows),
        "accepted_fits": sum(accepted(row) for row in rows),
        "policy_rejections": sum(row.get("geometry_valid") is True and row.get("error") is None
                                  and not accepted(row) for row in rows),
        "accepted_negatives": sum(accepted(row) for row in negatives),
        "accepted_truth_mean_corner_le_3px": sum(accurate(row, 3) for row in truth),
        "accepted_truth_mean_corner_le_5px": sum(accurate(row, 5) for row in truth),
        "accepted_truth_mean_corner_gt_5px": sum(
            accepted(row) and (error := _number(row.get("corner_error_mean_px"))) is not None and error > 5
            for row in truth),
    }


def _rows(report: dict[str, Any], split: str) -> list[dict[str, Any]]:
    if report.get("schema_version") != 1 or not isinstance(report.get("rows"), list) or not report["rows"]:
        raise ValueError("Expected a nonempty evaluator schema-1 report.")
    rows = report["rows"]
    if {row.get("split") for row in rows} != {split}:
        raise ValueError(f"This operation requires only {split} rows.")
    return rows


def select_gates(report: dict[str, Any]) -> dict[str, Any]:
    rows = _rows(report, "development")
    gates = [DiagnosticGate(n, coverage, cap) for n, coverage, cap in
             product((10, 20, 40), (0.01, 0.05, 0.10), (3.0, 5.0, None))]
    result: dict[str, Any] = {"kind": "development_grid_selection", "schema_version": 1,
                              "execution_configuration": report.get("configuration"),
                              "development_pairs": sorted({row["pair"] for row in rows}),
                              "development_image_sha256": sorted({value for key, value in report.get("input_sha256", {}).items()
                                                                   if Path(key).suffix.lower() in {".ppm", ".png", ".jpg", ".jpeg"}}),
                              "engines": {}}
    for engine in sorted({row["engine"] for row in rows}):
        attempts = [row for row in rows if row["engine"] == engine]
        baseline = gate_counts(attempts)
        accurate_baseline = baseline["accepted_truth_mean_corner_le_3px"]
        candidates = [{"gate": asdict(gate), "counts": gate_counts(attempts, gate)} for gate in gates]
        eligible = [item for item in candidates if accurate_baseline > 0
                    and 4 * item["counts"]["accepted_truth_mean_corner_le_3px"] >= 3 * accurate_baseline]

        def rank(item):
            counts, gate = item["counts"], item["gate"]
            return (counts["accepted_negatives"], counts["accepted_truth_mean_corner_gt_5px"],
                    -counts["accepted_truth_mean_corner_le_3px"], -counts["accepted_truth_mean_corner_le_5px"],
                    gate["minimum_inliers"], gate["minimum_reference_support"],
                    -(gate["maximum_residual_p95_px"] or inf))

        chosen = min(eligible, key=rank) if eligible else None
        result["engines"][engine] = {"baseline": baseline, "candidates": candidates,
                                      "selected_gate": chosen["gate"] if chosen else None,
                                      "selected_counts": chosen["counts"] if chosen else None,
                                      "reason": "preregistered lexicographic rule" if chosen else
                                                "No candidate satisfies the nonzero accurate baseline and 75% retention requirement."}
    return result


def report_frozen_gates(report: dict[str, Any], selection: dict[str, Any]) -> dict[str, Any]:
    rows = _rows(report, "heldout")
    if selection.get("kind") != "development_grid_selection" or selection.get("schema_version") != 1:
        raise ValueError("Expected a frozen development selection.")
    if report.get("configuration") != selection.get("execution_configuration"):
        raise ValueError("Reporting execution configuration differs from the frozen development configuration.")
    if {row["pair"] for row in rows} & set(selection.get("development_pairs", [])):
        raise ValueError("Reporting pair ids overlap development pairs.")
    images = {value for key, value in report.get("input_sha256", {}).items()
              if Path(key).suffix.lower() in {".ppm", ".png", ".jpg", ".jpeg"}}
    if images & set(selection.get("development_image_sha256", [])):
        raise ValueError("Reporting images overlap development input hashes.")
    result: dict[str, Any] = {"kind": "frozen_gate_reporting", "schema_version": 1, "engines": {}, "decisions": []}
    for engine in sorted({row["engine"] for row in rows}):
        if engine not in selection["engines"]:
            raise ValueError(f"No frozen choice for {engine}.")
        definition = selection["engines"][engine]["selected_gate"]
        attempts = [row for row in rows if row["engine"] == engine]
        gate = DiagnosticGate(**definition) if definition is not None else None
        baseline = gate_counts(attempts)
        measured = gate_counts(attempts, gate) if gate else None
        retained = (measured["accepted_truth_mean_corner_le_3px"] / baseline["accepted_truth_mean_corner_le_3px"]
                    if measured and baseline["accepted_truth_mean_corner_le_3px"] else None)
        result["engines"][engine] = {"baseline": baseline, "gate": definition, "gated": measured,
                                      "accurate_positive_retention": retained,
                                      "retains_at_least_75_percent": retained >= 0.75 if retained is not None else None,
                                      "scope": "Small preregistered sample; not a production reliability claim."}
        result["decisions"].extend({"pair": row["pair"], "engine": engine, "iteration": row.get("iteration"),
                                     "baseline_valid": row.get("geometry_valid"),
                                     "retained_by_gate": gate.retains(row) if gate else None,
                                     "corner_error_mean_px": row.get("corner_error_mean_px"), "error": row.get("error")}
                                    for row in attempts)
    return result


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_content_sha256(document: dict[str, Any]) -> str:
    """Hash parsed JSON content independently of whitespace and checkout EOLs."""
    canonical = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _read(path: Path) -> dict[str, Any]:
    def reject(value):
        raise ValueError(f"Non-finite JSON number: {value}")
    with (gzip.open(path, "rt", encoding="utf-8") if path.suffix == ".gz" else path.open(encoding="utf-8")) as stream:
        return json.load(stream, parse_constant=reject)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    select = commands.add_parser("select")
    select.add_argument("development", type=Path)
    select.add_argument("output", type=Path)
    apply = commands.add_parser("report")
    apply.add_argument("heldout", type=Path)
    apply.add_argument("selection", type=Path)
    apply.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "select":
            result = select_gates(_read(args.development))
            result["development_report_sha256"] = _digest(args.development)
        else:
            selection = _read(args.selection)
            result = report_frozen_gates(_read(args.heldout), selection)
            result["report_sha256"] = _digest(args.heldout)
            result["selection_sha256"] = _digest(args.selection)
            result["selection_content_sha256"] = json_content_sha256(selection)
            result["selection_sha256_scope"] = "Original input bytes; checkout line endings may differ."
        result["analysis_code_sha256"] = _digest(Path(__file__))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(result, stream, indent=2, allow_nan=False)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(2, f"Study failed: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
