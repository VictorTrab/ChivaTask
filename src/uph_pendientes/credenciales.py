"""Compatibilidad: reexporta el adapter de credenciales."""

from .domain.modelos import StoredCredentials
from .infrastructure.security import WindowsCredentialRepository
from .shared.errores import CredentialError

CredentialStore = WindowsCredentialRepository

__all__ = ["CredentialError", "CredentialStore", "StoredCredentials"]
