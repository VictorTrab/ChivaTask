"""Objeto con dependencias listas para ejecutar la app."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from uph_pendientes.application.puertos import AutostartManager, CredentialRepository, DesktopNotifier, TaskRepository
from uph_pendientes.domain.modelos import SyncResult


@dataclass(frozen=True)
class AppRuntime:
    task_repository: TaskRepository
    credential_repository: CredentialRepository
    notifier: DesktopNotifier
    autostart: AutostartManager
    sync_interval_seconds: int
    run_sync: Callable[[], SyncResult]
