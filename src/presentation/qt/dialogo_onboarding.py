"""Ventana de onboarding inicial separada de la ventana principal."""

from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QMessageBox, QStackedWidget, QVBoxLayout, QWidget

from application.puertos import CredentialRepository
from shared.errores import CredentialError

from .componentes.botones import PrimaryButton, SecondaryButton
from .componentes.modales import BaseModal
from .logo import BrandLockup


class OnboardingDialog(BaseModal):
    def __init__(self, credentials: CredentialRepository, parent: QWidget | None = None) -> None:
        super().__init__("Bienvenido a ChivaTask", parent)
        self.credentials = credentials
        self.setMinimumWidth(440)
        self.stack = QStackedWidget()
        self.stack.addWidget(self._welcome_page())
        self.stack.addWidget(self._login_page())
        self.stack.addWidget(self._ready_page())
        self.layout.addWidget(self.stack)

    def _welcome_page(self) -> QWidget:
        page = QWidget()
        layout = QHBoxLayout(page)
        content = QWidget()
        content_layout = self._page_layout(content)
        content_layout.addWidget(BrandLockup())
        title = QLabel("Tu campus académico, sin excusas.")
        title.setObjectName("detailTitle")
        text = QLabel("ChivaTask detecta tareas sin entrega en Moodle, sincroniza en segundo plano y te avisa cuando hay cambios importantes.")
        text.setWordWrap(True)
        text.setObjectName("muted")
        start = PrimaryButton("Comenzar")
        start.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        content_layout.addWidget(title)
        content_layout.addWidget(text)
        content_layout.addWidget(start)
        layout.addWidget(content)
        return page

    def _login_page(self) -> QWidget:
        page = QWidget()
        layout = self._page_layout(page)
        title = QLabel("Conecta tu campus")
        title.setObjectName("detailTitle")
        self.username = QLineEdit()
        self.username.setPlaceholderText("usuario@uph.edu.hn")
        self.password = QLineEdit()
        self.password.setPlaceholderText("Contraseña del campus")
        self.password.setEchoMode(QLineEdit.Password)
        info = QLabel("Tus credenciales se guardan en Windows Credential Manager, no en archivos del proyecto.")
        info.setWordWrap(True)
        info.setObjectName("settingsCard")
        connect = PrimaryButton("Conectar")
        connect.clicked.connect(self._save_credentials)
        back = SecondaryButton("Volver")
        back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        actions = QHBoxLayout()
        actions.addWidget(back)
        actions.addWidget(connect)
        layout.addWidget(title)
        layout.addWidget(self.username)
        layout.addWidget(self.password)
        layout.addWidget(info)
        layout.addLayout(actions)
        return page

    def _ready_page(self) -> QWidget:
        page = QWidget()
        layout = self._page_layout(page)
        title = QLabel("Todo listo")
        title.setObjectName("detailTitle")
        text = QLabel("La primera sincronización se ejecutará al entrar a ChivaTask.")
        text.setWordWrap(True)
        text.setObjectName("muted")
        done = PrimaryButton("Ir a ChivaTask")
        done.clicked.connect(self.accept)
        layout.addWidget(title)
        layout.addWidget(text)
        layout.addWidget(done)
        return page

    def _save_credentials(self) -> None:
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
        self.stack.setCurrentIndex(2)

    def _page_layout(self, page: QWidget):
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        return layout
