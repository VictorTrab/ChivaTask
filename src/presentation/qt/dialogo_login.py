"""Ventana Qt de acceso previo a ChivaTask."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QWidget

from application.puertos import CredentialRepository
from shared.errores import CredentialError

from .animaciones import fade_in
from .componentes.botones import PrimaryButton, SecondaryButton
from .logo import BrandLockup
from .tema import APP_DISPLAY_NAME


class LoginDialog(QDialog):
    def __init__(self, credentials: CredentialRepository, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.credentials = credentials
        self.setObjectName("accessWindow")
        self.setModal(True)
        self.setWindowTitle("Conecta tu campus")
        self.setMinimumSize(640, 500)
        self.resize(780, 540)

        root = QVBoxLayout(self)
        root.setContentsMargins(32, 32, 32, 32)
        root.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setObjectName("accessCard")
        card.setMaximumWidth(480)
        card.setMinimumWidth(440)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 28, 28, 28)
        card_layout.setSpacing(14)

        brand = BrandLockup(header=True)
        title = QLabel("Conecta tu campus")
        title.setObjectName("accessTitle")
        subtitle = QLabel(f"{APP_DISPLAY_NAME} usa tus credenciales solo en este equipo.")
        subtitle.setObjectName("accessSubtitle")
        subtitle.setWordWrap(True)

        self.error_label = QLabel("")
        self.error_label.setObjectName("accessError")
        self.error_label.setWordWrap(True)
        self.error_label.hide()

        user_label = QLabel("Usuario")
        user_label.setObjectName("accessFieldLabel")
        self.username = QLineEdit()
        self.username.setAccessibleName("Usuario del campus")
        self.username.setPlaceholderText("usuario@uph.edu.hn")
        self.username.setMinimumHeight(44)

        password_label = QLabel("Contraseña")
        password_label.setObjectName("accessFieldLabel")
        self.password = QLineEdit()
        self.password.setAccessibleName("Contraseña del campus")
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setPlaceholderText("Contraseña del campus")
        self.password.setMinimumHeight(44)
        self.password.returnPressed.connect(self.save)

        self.password_toggle = QPushButton("Mostrar")
        self.password_toggle.setObjectName("secondarySmallButton")
        self.password_toggle.setAccessibleName("Mostrar u ocultar contraseña")
        self.password_toggle.setCheckable(True)
        self.password_toggle.setMinimumHeight(44)
        self.password_toggle.clicked.connect(self._toggle_password)

        password_row = QHBoxLayout()
        password_row.setSpacing(8)
        password_row.addWidget(self.password, 1)
        password_row.addWidget(self.password_toggle)

        info = QLabel("Tus credenciales se guardan en Windows Credential Manager, no en archivos del proyecto.")
        info.setWordWrap(True)
        info.setObjectName("accessInfo")

        save = PrimaryButton("Conectar")
        save.setDefault(True)
        save.clicked.connect(self.save)
        cancel = SecondaryButton("Volver")
        cancel.clicked.connect(self.reject)

        actions = QHBoxLayout()
        actions.setSpacing(10)
        actions.addWidget(cancel)
        actions.addWidget(save)

        card_layout.addWidget(brand)
        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addWidget(self.error_label)
        card_layout.addWidget(user_label)
        card_layout.addWidget(self.username)
        card_layout.addWidget(password_label)
        card_layout.addLayout(password_row)
        card_layout.addWidget(info)
        card_layout.addLayout(actions)
        root.addWidget(card)
        self.username.setFocus()

    def showEvent(self, event):
        self._fade = fade_in(self)
        super().showEvent(event)

    def save(self) -> None:
        self._set_error("")
        username = self.username.text().strip()
        password = self.password.text()
        if not username or not password:
            self._set_error("Ingresa usuario y contraseña para continuar.")
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

    def _set_error(self, message: str) -> None:
        self.error_label.setText(message)
        self.error_label.setVisible(bool(message))
