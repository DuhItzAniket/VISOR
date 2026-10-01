"""Robustness sweeps reuse the benchmark's corner-RMSE method."""

from __future__ import annotations

from pathlib import Path

import pytest

from visor.benchmark import run_benchmark
from visor.sweeps import ROTATION_DEGREES, SCALE_FACTORS, run_robustness_sweep, sweep_scenarios


def test_sweep_scenarios_cover_angles_and_scales():
    import cv2

    image = cv2.imread(str(Path(__file__).parent / "data" / "golden_reference.png"))
    scenarios = sweep_scenarios(image)
    assert len(scenarios) == len(ROTATION_DEGREES) + len(SCALE_FACTORS)
    assert scenarios[0][0] == f"Rotation {ROTATION_DEGREES[0]:g}deg"


def test_sweep_reports_rows_per_engine_and_scenario():
    ref = Path(__file__).parent / "data" / "golden_reference.png"
    report = run_robustness_sweep(ref, engines=("SIFT",))
    assert len(report.rows) == len(ROTATION_DEGREES) + len(SCALE_FACTORS)
    assert all(row.engine == "SIFT" for row in report.rows)
    # Gentle 10-degree rotation must still localize on textured imagery.
    gentle = next(r for r in report.rows if r.scenario == "Rotation 10deg")
    assert gentle.geometry_valid and gentle.localization_error_px is not None


def test_classic_benchmark_untouched_by_sweeps():
    ref = Path(__file__).parent / "data" / "golden_reference.png"
    report = run_benchmark(ref, engines=("SIFT", "ORB"))
    assert len(report.rows) == 9 * 2
    assert report.rows[0].scenario == "Baseline"


def test_sweep_rejects_empty_engines():
    with pytest.raises(ValueError, match="at least one engine"):
        run_robustness_sweep(Path("x.png"), engines=())
