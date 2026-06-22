"""Punto de entrada y composition root de la aplicacion."""

from __future__ import annotations

import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QDialog

from application.servicio_ajustes import SettingsService
from presentation.qt import MainWindow
from presentation.qt.dialogo_login import LoginDialog
from presentation.qt.estilos import app_stylesheet

from .arranque import build_runtime


def main() -> int:
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    app.setQuitOnLastWindowClosed(False)
    runtime = build_runtime()
    settings = SettingsService(runtime.task_repository, runtime.autostart)
    settings.cleanup_legacy_settings()
    app.setStyleSheet(app_stylesheet(settings.visual_mode()))
    if not runtime.credential_repository.has_credentials():
        login = LoginDialog(runtime.credential_repository)
        login.setStyleSheet(app.styleSheet())
        if login.exec() != QDialog.Accepted:
            runtime.task_repository.close()
            return 0
        settings.set_onboarding_completed(True)
    window = MainWindow(
        repository=runtime.task_repository,
        credentials=runtime.credential_repository,
        notifier=runtime.notifier,
        navigator=runtime.navigator,
        autostart=runtime.autostart,
        run_sync=runtime.run_sync,
        sync_interval_seconds=runtime.sync_interval_seconds,
    )
    window.show()
    return app.exec()
