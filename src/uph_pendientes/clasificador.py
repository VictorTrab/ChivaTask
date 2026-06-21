"""Compatibilidad: reexporta politicas de clasificacion de tareas."""

from .domain.politica_tareas import classify_task, is_pending_status, sort_pending

__all__ = ["classify_task", "is_pending_status", "sort_pending"]
