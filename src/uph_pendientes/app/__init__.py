"""Punto de entrada y composition root de la aplicacion."""

from __future__ import annotations

import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from uph_pendientes.presentation.qt import MainWindow

from .arranque import build_runtime


def main() -> int:
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    app.setQuitOnLastWindowClosed(False)
    runtime = build_runtime()
    window = MainWindow(
        repository=runtime.task_repository,
        credentials=runtime.credential_repository,
        notifier=runtime.notifier,
        autostart=runtime.autostart,
        run_sync=runtime.run_sync,
        sync_interval_seconds=runtime.sync_interval_seconds,
    )
    window.show()
    return app.exec()
