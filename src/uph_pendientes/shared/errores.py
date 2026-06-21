"""Errores compartidos entre aplicacion e infraestructura."""

from __future__ import annotations


class AppError(RuntimeError):
    code = "app_error"


class CredentialError(AppError):
    code = "credential_error"


class MissingCredentialsError(CredentialError):
    code = "missing_credentials"


class CampusError(AppError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
