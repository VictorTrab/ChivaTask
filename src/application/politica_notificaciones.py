"""Reglas para decidir si un cambio debe generar notificacion."""

from __future__ import annotations

from domain.modelos import Task
from domain.tiempo import now_ts


def should_notify_task(task: Task, last_hash: str | None, current_ts: int | None = None) -> bool:
    if not task.is_pending:
        return False
    if task.snoozed_until and task.snoozed_until > (current_ts or now_ts()):
        return False
    return last_hash != task.stable_hash
