"""Objeto con dependencias listas para ejecutar la app."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from application.puertos import (
    AutostartManager,
    CredentialRepository,
    DesktopNavigator,
    DesktopNotifier,
    TaskRepository,
)
from domain.modelos import SyncResult


@dataclass(frozen=True)
class AppRuntime:
    task_repository: TaskRepository
    credential_repository: CredentialRepository
    notifier: DesktopNotifier
    navigator: DesktopNavigator
    autostart: AutostartManager
    sync_interval_seconds: int
    run_sync: Callable[[], SyncResult]
