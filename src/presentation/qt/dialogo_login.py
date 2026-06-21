"""Dialogo Qt para capturar credenciales del campus."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFormLayout, QLabel, QLineEdit, QMessageBox, QVBoxLayout, QWidget

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
        self.password.setPlaceholderText("Contrasena del campus")

        save = PrimaryButton("Conectar")
        save.clicked.connect(self.save)
        cancel = SecondaryButton("Cancelar")
        cancel.clicked.connect(self.reject)

        form = QFormLayout()
        form.addRow("Usuario", self.username)
        form.addRow("Contrasena", self.password)

        title = QLabel("Conecta tu campus")
        title.setObjectName("detailTitle")
        subtitle = QLabel(f"{APP_DISPLAY_NAME} usa tus credenciales solo en este equipo.")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #64748B;")
        info = QLabel("Tus credenciales se guardan en Windows Credential Manager, no en archivos del proyecto.")
        info.setWordWrap(True)
        info.setStyleSheet("color: #64748B;")

        self.layout.addWidget(BrandLockup())
        self.layout.addWidget(title)
        self.layout.addWidget(subtitle)
        self.layout.addLayout(form)
        self.layout.addWidget(info)
        self.layout.addWidget(save)
        self.layout.addWidget(cancel)
        self.layout.setAlignment(Qt.AlignTop)

    def showEvent(self, event):
        self._fade = fade_in(self)
        super().showEvent(event)

    def save(self) -> None:
        username = self.username.text().strip()
        password = self.password.text()
        if not username or not password:
            QMessageBox.warning(self, "Datos incompletos", "Ingresa usuario y contrasena.")
            return
        try:
            self.credentials.save_credentials(username, password)
            self.credentials.clear_token()
        except CredentialError as exc:
            QMessageBox.critical(self, "Credential Manager", str(exc))
            return
        self.accept()
