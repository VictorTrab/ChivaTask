"""Worker Qt que ejecuta sincronizacion fuera del hilo de UI."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QObject, Signal

from uph_pendientes.domain.modelos import SyncResult


class SyncWorker(QObject):
    finished = Signal(object)

    def __init__(self, run_sync: Callable[[], SyncResult]) -> None:
        super().__init__()
        self.run_sync = run_sync

    def run(self) -> None:
        self.finished.emit(self.run_sync())
