"""Boton y menu de perfil local."""

from __future__ import annotations

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu

from application.puertos import CredentialRepository
from presentation.qt.componentes.botones import IconButton
from presentation.qt.registro_iconos import IconRegistry


class ProfileButton(IconButton):
    def __init__(self, icons: IconRegistry, credentials: CredentialRepository, on_change_profile, on_logout) -> None:
        super().__init__(icons.icon("user"), "Cambiar perfil")
        self.credentials = credentials
        self.menu = ProfileMenu(icons, credentials, on_change_profile, on_logout)
        self.clicked.connect(self._show_menu)

    def _show_menu(self) -> None:
        self.menu.refresh_user()
        self.menu.exec(self.mapToGlobal(self.rect().bottomRight()))


class ProfileMenu(QMenu):
    def __init__(self, icons: IconRegistry, credentials: CredentialRepository, on_change_profile, on_logout) -> None:
        super().__init__()
        self.credentials = credentials
        self.user_action = QAction("Sin perfil", self)
        self.user_action.setEnabled(False)
        change_action = QAction(icons.icon("user_switch"), "Cambiar perfil", self)
        change_action.triggered.connect(on_change_profile)
        logout_action = QAction(icons.icon("logout"), "Cerrar sesion local", self)
        logout_action.triggered.connect(on_logout)
        self.addAction(self.user_action)
        self.addSeparator()
        self.addAction(change_action)
        self.addAction(logout_action)

    def refresh_user(self) -> None:
        username = getattr(self.credentials, "get_username", lambda: None)()
        self.user_action.setText(username or "Sin perfil")

