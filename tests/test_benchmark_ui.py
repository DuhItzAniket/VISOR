import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from threading import Event

from PySide6.QtWidgets import QApplication

from visor.benchmark import _scenarios, run_benchmark
from visor.pipeline import AnalysisCancelled, analyze
from visor.ui.main_window import MainWindow


def test_benchmark_scenarios_have_known_transformations(textured_pair):
    _, _, image, _, _ = textured_pair
    scenarios = _scenarios(image)
    assert len(scenarios) == 9
    assert {row[0] for row in scenarios} >= {"Baseline", "Perspective", "Brightness", "Contrast", "Crop"}
    assert all(row[1].shape == image.shape for row in scenarios)


def test_benchmark_reports_both_engines_against_generated_truth(textured_pair):
    reference, _, _, _, _ = textured_pair
    report = run_benchmark(reference)
    assert len(report.rows) == 18
    assert {row.scenario for row in report.rows} >= {"Baseline", "Perspective", "Noise", "Crop"}
    assert {row.engine for row in report.rows} == {"SIFT", "ORB"}
    assert all(row.total_ms >= 0 for row in report.rows)


def test_pre_requested_cancellation_is_reported(textured_pair):
    reference, target, _, _, _ = textured_pair
    cancellation = Event()
    cancellation.set()
    try:
        analyze(reference, target, "SIFT", cancel_event=cancellation)
    except AnalysisCancelled:
        pass
    else:
        raise AssertionError("cancelled pipeline should stop at the next safe boundary")


def test_main_window_builds_drop_inputs_and_controls():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    assert window.reference_input.acceptDrops()
    assert window.target_input.acceptDrops()
    assert window.run_button.isEnabled() is False
    assert window.compare_button.isEnabled() is False
    assert window.benchmark_button.isEnabled() is False
    assert window.cancel_button.isEnabled() is False
    window.close()
    app.quit()
