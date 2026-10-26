"""Offline desktop workflow check, usable from an installed standalone bundle."""

from __future__ import annotations

import json
import platform
import struct
import sys
import tempfile
import traceback
from pathlib import Path
from typing import Any, cast

import cv2
import numpy as np

from visor import __version__
from visor.opencv_runtime import validate_opencv_build


def run_smoke_check(report_path: Path) -> int:
    """Check Qt input/display, classical analysis, serialization and shutdown."""
    from PySide6.QtCore import QEventLoop, QMimeData, QPoint, QPointF, QSettings, Qt, QTimer, QUrl, qVersion
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
        if getattr(sys, "frozen", False):
            resource_root = getattr(sys, "_MEIPASS", None)
            if not resource_root:
                raise RuntimeError("Frozen application resource directory is unavailable.")
            resources = Path(resource_root)
            for name, expected in (("LICENSE", "Apache License"), ("NOTICE", "Apache-2.0")):
                if expected not in (resources / name).read_text(encoding="utf-8"):
                    raise RuntimeError(f"Project notice missing or unexpected: {name}")
            report["checks"].append("VISOR Apache-2.0 LICENSE/NOTICE files (project only)")
            from visor.distribution_audit import verify_notice_index

            count = verify_notice_index(resources / "third-party" / "notices.json", qt_version=qVersion())
            report["checks"].append(f"Third-party notice index and {count} file hashes (not compliance certification)")
            backend = validate_opencv_build(cv2.getBuildInformation(), opencv_version=cv2.__version__)
            report["checks"].append(f"OpenCV GUI backend {backend}; PySide6 supplies the desktop UI")
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
            for extension in (".jpg", ".bmp", ".tif", ".webp"):
                sample = folder / f"format{extension}"
                success, encoded = cv2.imencode(extension, image)
                if not success:
                    raise RuntimeError(f"Cannot encode image-format fixture: {extension}")
                encoded.tofile(sample)
                window.target_input.load_path(sample)
                if window.target_input.image_path != sample.resolve():
                    raise RuntimeError(f"Bundled Qt image format failed: {extension}")
            window.target_input.load_path(target)
            report["checks"].append("Qt PNG/JPEG/BMP/TIFF/WebP input decoding")
            # Hand-built EXIF avoids another runtime dependency for this check.
            success, encoded = cv2.imencode(".jpg", image)
            if not success:
                raise RuntimeError("Cannot encode orientation fixture.")
            tiff = (b"II" + struct.pack("<HIH", 42, 8, 1) + struct.pack("<HHI", 0x112, 3, 1)
                    + struct.pack("<H", 6) + b"\0\0" + struct.pack("<I", 0))
            app1 = b"Exif\0\0" + tiff
            raw = encoded.tobytes()
            rotated = folder / "orientation-6.jpg"
            rotated.write_bytes(raw[:2] + b"\xff\xe1" + struct.pack(">H", len(app1) + 2) + app1 + raw[2:])
            window.target_input.load_path(rotated)
            if "280 × 360 px" not in window.target_input.metadata_label.text():
                raise RuntimeError("Bundled input preview ignored EXIF orientation.")
            broken = folder / "unreadable.jpg"
            broken.write_bytes(b"not an image")
            if window.target_input.load_path(broken) or window.target_input.image_path != rotated.resolve():
                raise RuntimeError("Unreadable replacement lost the selected image.")
            unavailable = folder / "temporarily-unavailable.jpg"
            rotated.rename(unavailable)
            window.target_input._update_preview()
            if window.target_input.preview.pixmap().isNull():
                raise RuntimeError("Cached image preview was lost when the source became unavailable.")
            window.target_input.load_path(target)
            report["checks"].append("EXIF-oriented input, failed replacement recovery and cached preview")
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
            previous = window._latest_result
            window.localization_view.scale(2, 2)
            window.localization_view._auto_fit = False
            transform = window.localization_view.transform()
            for width in (3, 6, 12):
                window.feature_thickness_slider.setValue(width)
            window.feature_color_button.setChecked(True)
            if window._latest_result is not previous:
                raise RuntimeError("Overlay request synchronously replaced the analysis result.")
            loop, timeout = QEventLoop(), QTimer()
            timeout.setSingleShot(True)
            timeout.timeout.connect(loop.quit)
            window._overlay_renderer.idle.connect(loop.quit)
            timeout.start(10000)
            loop.exec()
            timeout.stop()
            window._overlay_renderer.idle.disconnect(loop.quit)
            styled = window._latest_result
            if (window._overlay_renderer.busy or styled is None or styled is previous
                    or styled.settings.feature_line_thickness != 12 or not styled.settings.rainbow_feature_colors
                    or window.localization_view.transform() != transform):
                raise RuntimeError("Background overlay/latest style/viewport check failed.")
            export_json(styled, folder / "styled.json")
            if json.loads((folder / "styled.json").read_text(encoding="utf-8"))["configuration"]["feature_line_thickness"] != 12:
                raise RuntimeError("Styled export does not describe the completed overlay.")
            report["checks"].append("Background overlay updates, latest style, preserved viewport and matching export")
            session = ProjectSession(str(reference), str(target), "ORB", AnalysisSettings(), SIFTConfiguration(), ORBConfiguration())
            save_project(session, folder / "session.visor")
            if load_project(folder / "session.visor").engine != "ORB":
                raise RuntimeError("Project round trip failed.")
            report["checks"].append("project round trip")
            from visor.video import track_reference_in_video

            video_path = folder / "clip.avi"
            writer = cv2.VideoWriter(str(video_path), cast(Any, cv2).VideoWriter_fourcc(*"MJPG"), 10.0, (360, 280))
            try:
                if not writer.isOpened():
                    raise RuntimeError("Cannot create the MJPEG video fixture.")
                for _ in range(3):
                    writer.write(image)
            finally:
                writer.release()
            video = track_reference_in_video(reference, video_path, engine="ORB")
            if len(video.frames) != 3 or not all(frame.geometry_valid for frame in video.frames):
                raise RuntimeError("Bundled MJPEG video decoding/tracking failed.")
            report["checks"].append("MJPEG file encode/decode and three-frame ORB tracking (not camera hardware)")
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
