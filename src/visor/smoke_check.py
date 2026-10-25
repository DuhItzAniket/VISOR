"""Offline desktop workflow check, usable from an installed standalone bundle."""

from __future__ import annotations

import json
import platform
import tempfile
import traceback
from pathlib import Path

import cv2
import numpy as np

from visor import __version__


def run_smoke_check(report_path: Path) -> int:
    """Check Qt input/display, classical analysis, serialization and shutdown."""
    from PySide6.QtCore import QMimeData, QPoint, QPointF, QSettings, Qt, QUrl
    from PySide6.QtGui import QDragEnterEvent, QDropEvent
    from PySide6.QtWidgets import QApplication

    from visor.engines import ORBConfiguration, SIFTConfiguration
    from visor.exporting import ProjectSession, export_csv, export_json, load_project, save_project
    from visor.models import AnalysisSettings
    from visor.pipeline import analyze
    from visor.ui.main_window import MainWindow

    report: dict = {"version": __version__, "system": platform.system(), "checks": [], "success": False}
    app = QApplication.instance() or QApplication(["VISOR smoke check"])
    window = None
    try:
        with tempfile.TemporaryDirectory(prefix="visor-smoke-") as temporary:
            folder = Path(temporary)
            rng = np.random.default_rng(2026)
            image = rng.integers(0, 256, (280, 360, 3), dtype=np.uint8)
            reference, target = folder / "reference.png", folder / "target.png"
            for path in (reference, target):
                success, encoded = cv2.imencode(".png", image)
                if not success:
                    raise RuntimeError("Cannot encode smoke image.")
                encoded.tofile(path)
            window = MainWindow()
            # Preserve user layout/settings by using an isolated settings file.
            window._window_settings = QSettings(str(folder / "smoke.ini"), QSettings.Format.IniFormat)
            window.show()
            mime = QMimeData()
            mime.setUrls([QUrl.fromLocalFile(str(reference))])
            actions = Qt.DropAction.CopyAction | Qt.DropAction.MoveAction
            enter = QDragEnterEvent(QPoint(40, 40), actions, mime,
                                    Qt.MouseButton.LeftButton, Qt.KeyboardModifier.ShiftModifier)
            QApplication.sendEvent(window.reference_input, enter)
            drop = QDropEvent(QPointF(40, 40), actions, mime,
                              Qt.MouseButton.LeftButton, Qt.KeyboardModifier.ShiftModifier)
            QApplication.sendEvent(window.reference_input, drop)
            if (not enter.isAccepted() or not drop.isAccepted() or drop.dropAction() != Qt.DropAction.CopyAction
                    or window.reference_input.image_path != reference.resolve() or not reference.exists()):
                raise RuntimeError("Qt image drop did not load the input with copy semantics.")
            report["checks"].append("Qt URL drop events with copy semantics (not native shell drag)")
            window.target_input.load_path(target)
            app.processEvents()
            if not window.run_button.isEnabled():
                raise RuntimeError("Image loading did not enable analysis.")
            report["checks"].append("Qt window and image inputs")
            for engine in ("SIFT", "ORB"):
                result = analyze(reference, target, engine)
                if not result.geometry.valid or result.geometry.inlier_count < 4:
                    raise RuntimeError(f"{engine} identity pair failed localization.")
                window._show_result(result)
                app.processEvents()
                export_json(result, folder / "analysis.json")
                export_csv(result, folder / "analysis.csv")
                if json.loads((folder / "analysis.json").read_text(encoding="utf-8"))["engine"] != engine:
                    raise RuntimeError("Exported engine does not match selected engine.")
                report["checks"].append(f"{engine} localization, rendering, JSON/CSV export")
            session = ProjectSession(str(reference), str(target), "ORB", AnalysisSettings(), SIFTConfiguration(), ORBConfiguration())
            save_project(session, folder / "session.visor")
            if load_project(folder / "session.visor").engine != "ORB":
                raise RuntimeError("Project round trip failed.")
            report["checks"].append("project round trip")
            window.close()
            app.processEvents()
            window = None
            report["checks"].append("window shutdown")
            report["success"] = True
    except Exception:  # noqa: BLE001 — persist diagnostics even in a windowed executable
        report["error"] = traceback.format_exc()
    finally:
        if window is not None:
            window.close()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0 if report["success"] else 1
