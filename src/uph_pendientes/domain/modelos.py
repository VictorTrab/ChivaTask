"""Modelos puros del dominio: cursos, tareas, credenciales y resultados."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256


class TaskBucket(str, Enum):
    OVERDUE = "vencida"
    UPCOMING = "proxima"
    UNDATED = "sin_fecha"
    SUBMITTED = "entregada"


@dataclass(frozen=True)
class StoredCredentials:
    username: str
    password: str
    token: str | None


@dataclass(frozen=True)
class Course:
    course_id: int
    shortname: str
    fullname: str
    visible: bool


@dataclass(frozen=True)
class Task:
    assignment_id: int
    course_id: int
    course_shortname: str
    course_fullname: str
    name: str
    due_at: int | None
    url: str | None
    submission_status: str
    content_hash: str | None = None
    snoozed_until: int | None = None

    @property
    def is_pending(self) -> bool:
        return self.submission_status in {"new", "reopened", "draft"}

    @property
    def stable_hash(self) -> str:
        if self.content_hash:
            return self.content_hash
        raw = "|".join(
            [
                str(self.assignment_id),
                str(self.course_id),
                self.name,
                str(self.due_at or ""),
                self.url or "",
                self.submission_status,
            ]
        )
        return sha256(raw.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class SyncResult:
    ok: bool
    pending_count: int
    course_count: int
    changed_pending: list[Task]
    error_code: str | None = None
