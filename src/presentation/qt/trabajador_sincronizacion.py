"""Worker Qt que ejecuta sincronizacion fuera del hilo de UI."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QObject, Signal

from domain.modelos import SyncResult


class SyncWorker(QObject):
    finished = Signal(object)

    def __init__(self, run_sync: Callable[[], SyncResult]) -> None:
        super().__init__()
        self.run_sync = run_sync

    def run(self) -> None:
        try:
            self.finished.emit(self.run_sync())
        except Exception:
            self.finished.emit(SyncResult(False, 0, 0, [], "unexpected_error"))
