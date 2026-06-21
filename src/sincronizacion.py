"""Compatibilidad: expone el caso de uso de sincronizacion."""

from application.caso_uso_sincronizacion import SyncUseCase
from infrastructure.moodle import MoodleCampusGateway


class SyncService(SyncUseCase):
    def __init__(self, db, credentials, client=None) -> None:
        super().__init__(db, credentials, client or MoodleCampusGateway())

    def sync(self):
        return self.execute()
