"""Reglas para decidir si una tarea esta pendiente y como clasificarla."""

from __future__ import annotations

from .modelos import Task, TaskBucket
from .tiempo import now_ts


PENDING_STATUSES = {"new", "reopened", "draft"}


def is_pending_status(status: str) -> bool:
    return status in PENDING_STATUSES


def classify_task(task: Task, current_ts: int | None = None) -> TaskBucket:
    if not task.is_pending:
        return TaskBucket.SUBMITTED
    if task.due_at is None or task.due_at == 0:
        return TaskBucket.UNDATED
    if task.due_at < (current_ts or now_ts()):
        return TaskBucket.OVERDUE
    return TaskBucket.UPCOMING


def sort_pending(tasks: list[Task]) -> list[Task]:
    def key(task: Task) -> tuple[int, int, str]:
        priority = {
            TaskBucket.OVERDUE: 0,
            TaskBucket.UPCOMING: 1,
            TaskBucket.UNDATED: 2,
            TaskBucket.SUBMITTED: 3,
        }[classify_task(task)]
        return priority, task.due_at or 4_102_444_800, task.name.lower()

    return sorted([task for task in tasks if task.is_pending], key=key)
