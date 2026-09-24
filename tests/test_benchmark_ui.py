import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from threading import Event

from PySide6.QtWidgets import QApplication, QLabel

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
    assert hasattr(window, "feature_color_button")
    assert hasattr(window, "feature_thickness_slider")
    assert hasattr(window, "engine_console")
    assert hasattr(window, "log_engine_event")
    assert hasattr(window, "install_learned_button")
    label_texts = [label.text() for label in window.findChildren(QLabel)]
    assert "Planar feature analysis" not in label_texts
    assert "Image inputs" not in label_texts
    assert window.run_button.isHidden() is False
    assert window.compare_button.isHidden() is False
    assert window.benchmark_button.isHidden() is False
    assert window.cancel_button.isHidden() is False
    assert window.run_button.isEnabled() is False
    assert window.compare_button.isEnabled() is False
    assert window.benchmark_button.isEnabled() is False
    assert window.cancel_button.isEnabled() is False

    window.reference_input.load_path(__file__.replace("test_benchmark_ui.py", "data/reference.png"))
    assert window.reference_input.clear_button.isVisible() is True
    window.log_engine_event("status", "UI test trace")
    assert "UI test trace" in window.engine_console.toPlainText()

    window.close()
    app.quit()
