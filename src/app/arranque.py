"""Composition root: arma adapters concretos y casos de uso."""

from __future__ import annotations

from application.caso_uso_sincronizacion import SyncUseCase
from infrastructure.desktop import SafeDesktopNavigator, WindowsAutostartManager, WindowsDesktopNotifier
from infrastructure.moodle import MoodleCampusGateway
from infrastructure.persistence import SQLiteTaskRepository
from infrastructure.security import WindowsCredentialRepository
from shared.ajustes import DEFAULT_SYNC_INTERVAL_SECONDS

from .tiempo_ejecucion import AppRuntime


def build_runtime() -> AppRuntime:
    repository = SQLiteTaskRepository()
    credentials = WindowsCredentialRepository()
    notifier = WindowsDesktopNotifier()
    navigator = SafeDesktopNavigator()
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
        navigator=navigator,
        autostart=autostart,
        sync_interval_seconds=int(interval or DEFAULT_SYNC_INTERVAL_SECONDS),
        run_sync=run_sync,
    )
