"""Controlador del icono en la bandeja del sistema."""

from __future__ import annotations

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon, QWidget

from presentation.qt.logo import logo_icon
from shared.ajustes import APP_NAME

from .registro_iconos import IconRegistry


class TrayController:
    def __init__(self, parent: QWidget, icons: IconRegistry, show_window, sync_now) -> None:
        self._background_message_shown = False
        self.tray = QSystemTrayIcon(parent)
        self.tray.setIcon(logo_icon())
        menu = QMenu()
        open_action = QAction("Abrir ChivaTask", parent)
        open_action.triggered.connect(show_window)
        sync_action = QAction(icons.icon("refresh", "brand"), "Sincronizar ahora", parent)
        sync_action.triggered.connect(sync_now)
        quit_action = QAction("Salir", parent)
        quit_action.triggered.connect(QApplication.instance().quit)
        menu.addAction(open_action)
        menu.addAction(sync_action)
        menu.addSeparator()
        menu.addAction(quit_action)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(lambda reason: show_window() if reason == QSystemTrayIcon.DoubleClick else None)
        self.tray.show()

    def is_visible(self) -> bool:
        return self.tray.isVisible()

    def show_background_message(self) -> None:
        if self._background_message_shown:
            return
        self._background_message_shown = True
        self.tray.showMessage(APP_NAME, "La app sigue en segundo plano.", QSystemTrayIcon.Information, 2500)

    def reset_background_message(self) -> None:
        self._background_message_shown = False
