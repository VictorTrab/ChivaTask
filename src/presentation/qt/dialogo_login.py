"""Dialogo Qt para capturar credenciales del campus."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QWidget

from application.puertos import CredentialRepository
from shared.errores import CredentialError

from .animaciones import fade_in
from .componentes.botones import PrimaryButton, SecondaryButton
from .componentes.modales import BaseModal
from .logo import BrandLockup
from .tema import APP_DISPLAY_NAME


class LoginDialog(BaseModal):
    def __init__(self, credentials: CredentialRepository, parent: QWidget | None = None) -> None:
        super().__init__("Conecta tu campus", parent)
        self.credentials = credentials
        self.setMinimumWidth(420)
        self.username = QLineEdit()
        self.username.setPlaceholderText("usuario@uph.edu.hn")
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setPlaceholderText("Contraseña del campus")
        self.password_toggle = QPushButton("Mostrar")
        self.password_toggle.setObjectName("secondarySmallButton")
        self.password_toggle.setCheckable(True)
        self.password_toggle.clicked.connect(self._toggle_password)

        save = PrimaryButton("Conectar")
        save.setDefault(True)
        save.clicked.connect(self.save)
        cancel = SecondaryButton("Cancelar")
        cancel.clicked.connect(self.reject)

        form = QFormLayout()
        form.addRow("Usuario", self.username)
        password_row = QHBoxLayout()
        password_row.addWidget(self.password, 1)
        password_row.addWidget(self.password_toggle)
        form.addRow("Contraseña", password_row)

        title = QLabel("Conecta tu campus")
        title.setObjectName("detailTitle")
        subtitle = QLabel(f"{APP_DISPLAY_NAME} usa tus credenciales solo en este equipo.")
        subtitle.setWordWrap(True)
        subtitle.setObjectName("muted")
        info = QLabel("Tus credenciales se guardan en Windows Credential Manager, no en archivos del proyecto.")
        info.setWordWrap(True)
        info.setObjectName("settingsCard")

        self.layout.addWidget(BrandLockup())
        self.layout.addWidget(title)
        self.layout.addWidget(subtitle)
        self.layout.addLayout(form)
        self.layout.addWidget(info)
        actions = QHBoxLayout()
        actions.addWidget(cancel)
        actions.addWidget(save)
        self.layout.addLayout(actions)
        self.layout.setAlignment(Qt.AlignTop)
        self.username.setFocus()

    def showEvent(self, event):
        self._fade = fade_in(self)
        super().showEvent(event)

    def save(self) -> None:
        username = self.username.text().strip()
        password = self.password.text()
        if not username or not password:
            QMessageBox.warning(self, "Datos incompletos", "Ingresa usuario y contraseña.")
            return
        try:
            self.credentials.save_credentials(username, password)
            self.credentials.clear_token()
        except CredentialError as exc:
            QMessageBox.critical(self, "Credential Manager", str(exc))
            return
        self.accept()

    def _toggle_password(self) -> None:
        visible = self.password_toggle.isChecked()
        self.password.setEchoMode(QLineEdit.Normal if visible else QLineEdit.Password)
        self.password_toggle.setText("Ocultar" if visible else "Mostrar")
