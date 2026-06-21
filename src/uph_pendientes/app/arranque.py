"""Composition root: arma adapters concretos y casos de uso."""

from __future__ import annotations

from uph_pendientes.application.caso_uso_sincronizacion import SyncUseCase
from uph_pendientes.infrastructure.desktop import WindowsAutostartManager, WindowsDesktopNotifier
from uph_pendientes.infrastructure.moodle import MoodleCampusGateway
from uph_pendientes.infrastructure.persistence import SQLiteTaskRepository
from uph_pendientes.infrastructure.security import WindowsCredentialRepository
from uph_pendientes.shared.ajustes import DEFAULT_SYNC_INTERVAL_SECONDS

from .tiempo_ejecucion import AppRuntime


def build_runtime() -> AppRuntime:
    repository = SQLiteTaskRepository()
    credentials = WindowsCredentialRepository()
    notifier = WindowsDesktopNotifier()
    autostart = WindowsAutostartManager()

    def run_sync():
        worker_repository = SQLiteTaskRepository(repository.path)
        try:
            return SyncUseCase(worker_repository, credentials, MoodleCampusGateway()).execute()
        finally:
            worker_repository.close()

    interval = repository.get_setting("sync_interval_seconds", str(DEFAULT_SYNC_INTERVAL_SECONDS))
    return AppRuntime(
        task_repository=repository,
        credential_repository=credentials,
        notifier=notifier,
        autostart=autostart,
        sync_interval_seconds=int(interval or DEFAULT_SYNC_INTERVAL_SECONDS),
        run_sync=run_sync,
    )
