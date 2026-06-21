"""Funciones pequenas para normalizar respuestas de Moodle."""

from __future__ import annotations


def submission_status(payload: dict) -> str:
    last_attempt = payload.get("lastattempt") if isinstance(payload, dict) else None
    submission = last_attempt.get("submission") if isinstance(last_attempt, dict) else None
    status = submission.get("status") if isinstance(submission, dict) else None
    return str(status or "new")
