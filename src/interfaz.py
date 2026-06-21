"""Compatibilidad: reexporta clases principales de la UI Qt."""

from presentation.qt import MainWindow
from presentation.qt.dialogo_login import LoginDialog
from presentation.qt.trabajador_sincronizacion import SyncWorker

__all__ = ["LoginDialog", "MainWindow", "SyncWorker"]
