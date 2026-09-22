"""Application startup and logging configuration."""

from __future__ import annotations

import logging
import sys

from PySide6.QtWidgets import QApplication

from visor.ui.main_window import MainWindow


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main() -> int:
    configure_logging()
    app = QApplication(sys.argv)
    app.setApplicationName("VISOR")
    app.setOrganizationName("VISOR")
    app.setApplicationVersion("0.1.0")
    window = MainWindow()
    window.show()
    return app.exec()

