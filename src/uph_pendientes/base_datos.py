"""Compatibilidad: expone el repositorio SQLite como CacheDB."""

from .infrastructure.persistence import SQLiteTaskRepository


class CacheDB(SQLiteTaskRepository):
    def upsert_assignments(self, assignments):
        self.upsert_tasks(assignments)
