"""Adapters de persistencia local."""

from .almacen_sqlite import SQLiteTaskRepository

__all__ = ["SQLiteTaskRepository"]
