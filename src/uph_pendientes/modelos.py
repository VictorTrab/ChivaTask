"""Compatibilidad: reexporta modelos desde la capa de dominio."""

from .domain.modelos import Course, StoredCredentials, SyncResult, Task, TaskBucket
from .domain.tiempo import now_ts, unix_to_local_text

Assignment = Task
CachedTask = Task

__all__ = [
    "Assignment",
    "CachedTask",
    "Course",
    "StoredCredentials",
    "SyncResult",
    "Task",
    "TaskBucket",
    "now_ts",
    "unix_to_local_text",
]
