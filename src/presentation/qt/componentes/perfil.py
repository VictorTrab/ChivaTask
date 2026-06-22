"""Boton y menu de perfil local."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMenu, QToolButton, QVBoxLayout, QWidget

from application.puertos import CredentialRepository
from presentation.qt.registro_iconos import IconRegistry


def _display_name(username: str | None) -> str:
    if not username:
        return "Sin perfil"
    return username.split("@", 1)[0].replace(".", " ").strip().title() or username


def _initials(username: str | None) -> str:
    name = _display_name(username)
    parts = [part for part in name.replace("_", " ").split() if part]
    if not parts or name == "Sin perfil":
        return "?"
    return "".join(part[0] for part in parts[:2]).upper()


class ProfileButton(QToolButton):
    def __init__(self, icons: IconRegistry, credentials: CredentialRepository, on_change_profile, on_logout) -> None:
        super().__init__()
        self.setObjectName("profileButton")
        self.setCursor(Qt.PointingHandCursor)
        self.setAccessibleName("Perfil local")
        self.setToolTip("Perfil local")
        self.setPopupMode(QToolButton.InstantPopup)
        self.setArrowType(Qt.NoArrow)
        self.setMinimumHeight(42)
        self.setMinimumWidth(170)
        self.setMaximumWidth(230)
        self.credentials = credentials
        self.menu = ProfileMenu(icons, credentials, on_change_profile, on_logout)
        self.setMenu(self.menu)
        self.pressed.connect(self.refresh_user)

        content = QWidget()
        content.setObjectName("profileButtonContent")
        layout = QHBoxLayout(content)
        layout.setContentsMargins(4, 3, 8, 3)
        layout.setSpacing(8)
        self.avatar = QLabel("?")
        self.avatar.setObjectName("profileAvatar")
        self.avatar.setAlignment(Qt.AlignCenter)
        self.avatar.setFixedSize(30, 30)
        text_box = QVBoxLayout()
        text_box.setContentsMargins(0, 0, 0, 0)
        text_box.setSpacing(0)
        self.name_label = QLabel("Sin perfil")
        self.name_label.setObjectName("profileName")
        self.name_label.setMaximumWidth(135)
        self.name_label.setTextInteractionFlags(Qt.NoTextInteraction)
        self.caption_label = QLabel("Campus")
        self.caption_label.setObjectName("profileCaption")
        text_box.addWidget(self.name_label)
        text_box.addWidget(self.caption_label)
        layout.addWidget(self.avatar)
        layout.addLayout(text_box)
        self.setLayout(QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(content)
        self.refresh_user()

    def _show_menu(self) -> None:
        self.showMenu()

    def refresh_user(self) -> None:
        username = getattr(self.credentials, "get_username", lambda: None)()
        name = _display_name(username)
        self.avatar.setText(_initials(username))
        self.name_label.setText(name)
        self.name_label.setToolTip(username or "Sin perfil")
        self.menu.refresh_user()


class ProfileMenu(QMenu):
    def __init__(self, icons: IconRegistry, credentials: CredentialRepository, on_change_profile, on_logout) -> None:
        super().__init__()
        self.credentials = credentials
        self.user_action = QAction("Sin perfil", self)
        self.user_action.setEnabled(False)
        change_action = QAction(icons.icon("user_switch"), "Cambiar perfil", self)
        change_action.triggered.connect(on_change_profile)
        logout_action = QAction(icons.icon("logout"), "Cerrar sesión local", self)
        logout_action.triggered.connect(on_logout)
        self.addAction(self.user_action)
        self.addSeparator()
        self.addAction(change_action)
        self.addAction(logout_action)

    def refresh_user(self) -> None:
        username = getattr(self.credentials, "get_username", lambda: None)()
        self.user_action.setText(username or "Sin perfil")
