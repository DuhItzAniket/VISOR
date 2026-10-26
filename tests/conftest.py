from __future__ import annotations

import os
import sys

import cv2
import numpy as np
import pytest


@pytest.fixture(scope="session", autouse=True)
def application_lifetime():
    """Keep one application alive until every test-owned Qt object is done.

    Individual tests may exit nested event loops, but must not repeatedly
    construct/destroy the process-wide application between native checks.
    """
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app
    app.processEvents()


@pytest.fixture
def qt_wait():
    """Run the application's event loop while waiting for a bounded condition."""
    from PySide6.QtCore import QEventLoop, QTimer

    def wait(condition, timeout_ms=4000):
        if condition():
            return
        loop, poll, timeout = QEventLoop(), QTimer(), QTimer()
        timeout.setSingleShot(True)
        poll.timeout.connect(lambda: loop.quit() if condition() else None)
        timeout.timeout.connect(loop.quit)
        poll.start(5)
        timeout.start(timeout_ms)
        loop.exec()
        poll.stop()
        timeout.stop()
        assert condition(), "Qt operation did not finish before its deadline"

    return wait


@pytest.fixture(autouse=True)
def isolated_window_settings(monkeypatch, tmp_path):
    """UI checks must not restore or overwrite the developer's real layout."""
    module = sys.modules.get("visor.ui.main_window")
    if module is not None:
        from PySide6.QtCore import QSettings

        settings = QSettings(str(tmp_path / "qt-window-settings.ini"), QSettings.Format.IniFormat)
        monkeypatch.setattr(module, "QSettings", lambda *args: settings)


@pytest.fixture
def textured_pair(tmp_path):
    rng = np.random.default_rng(407)
    image = np.full((420, 560, 3), 235, dtype=np.uint8)
    for _ in range(180):
        x = int(rng.integers(8, image.shape[1] - 8))
        y = int(rng.integers(8, image.shape[0] - 8))
        color = tuple(int(v) for v in rng.integers(0, 200, size=3))
        radius = int(rng.integers(2, 9))
        cv2.circle(image, (x, y), radius, color, -1, cv2.LINE_AA)
    for index in range(12):
        cv2.putText(image, f"V{index}", (20 + (index % 4) * 130, 50 + (index // 4) * 120),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (15, 25, 35), 2, cv2.LINE_AA)
    transform = np.array([[1.0, 0.015, 22.0], [-0.012, 1.0, 17.0], [0.00002, -0.00001, 1.0]])
    target = cv2.warpPerspective(image, transform, (image.shape[1], image.shape[0]))
    reference_path, target_path = tmp_path / "reference.png", tmp_path / "target.png"
    cv2.imwrite(str(reference_path), image)
    cv2.imwrite(str(target_path), target)
    return reference_path, target_path, image, target, transform
