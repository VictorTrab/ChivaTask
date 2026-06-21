"""Adapter de Windows Credential Manager mediante keyring."""

from __future__ import annotations

from uph_pendientes.domain.modelos import StoredCredentials
from uph_pendientes.shared.errores import CredentialError, MissingCredentialsError
from uph_pendientes.shared.ajustes import APP_ID


class WindowsCredentialRepository:
    def __init__(self, service: str = APP_ID) -> None:
        self.service = service

    def _keyring(self):
        try:
            import keyring
        except ImportError as exc:
            raise CredentialError("Instala keyring para usar Windows Credential Manager.") from exc
        return keyring

    def has_credentials(self) -> bool:
        return bool(self.get_username() and self.get_password())

    def get_username(self) -> str | None:
        return self._keyring().get_password(self.service, "moodle_username")

    def get_password(self) -> str | None:
        return self._keyring().get_password(self.service, "moodle_password")

    def get_token(self) -> str | None:
        return self._keyring().get_password(self.service, "moodle_token")

    def load(self) -> StoredCredentials:
        username = self.get_username()
        password = self.get_password()
        if not username or not password:
            raise MissingCredentialsError("Credenciales no configuradas.")
        return StoredCredentials(username=username, password=password, token=self.get_token())

    def save_credentials(self, username: str, password: str) -> None:
        kr = self._keyring()
        kr.set_password(self.service, "moodle_username", username.strip())
        kr.set_password(self.service, "moodle_password", password)

    def save_token(self, token: str) -> None:
        self._keyring().set_password(self.service, "moodle_token", token)

    def clear_token(self) -> None:
        self._delete("moodle_token")

    def clear_all(self) -> None:
        for account in ("moodle_username", "moodle_password", "moodle_token"):
            self._delete(account)

    def _delete(self, account: str) -> None:
        try:
            self._keyring().delete_password(self.service, account)
        except Exception:
            pass
