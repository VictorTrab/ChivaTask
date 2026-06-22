"""Priorizacion academica explicable basada solo en datos locales."""

from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata

from .modelos import Task
from .politica_tareas import classify_task
from .modelos import TaskBucket
from .tiempo import now_ts


EXAM_KEYWORDS = {"examen", "parcial", "prueba", "quiz", "evaluacion"}


@dataclass(frozen=True)
class TaskRecommendation:
    task: Task
    score: int
    level: str
    primary_reason: str
    secondary_reason: str | None
    suggested_action: str
    is_possible_exam: bool


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text.lower())
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


def is_possible_exam(task_name: str) -> bool:
    normalized = normalize_text(task_name)
    words = set(re.findall(r"[a-z0-9]+", normalized))
    return bool(words & EXAM_KEYWORDS)


def recommend_tasks(tasks: list[Task], current_ts: int | None = None, limit: int = 3) -> list[TaskRecommendation]:
    current = current_ts or now_ts()
    pending = [task for task in tasks if task.is_pending and not _is_snoozed(task, current)]
    pending_by_course: dict[int, int] = {}
    for task in pending:
        pending_by_course[task.course_id] = pending_by_course.get(task.course_id, 0) + 1
    recommendations = [_recommend(task, pending_by_course.get(task.course_id, 0), current) for task in pending]
    return sorted(
        recommendations,
        key=lambda item: (
            _bucket_rank(classify_task(item.task, current)),
            -item.score,
            item.task.due_at or 4_102_444_800,
            item.task.name.lower(),
        ),
    )[:limit]


def academic_alerts(tasks: list[Task], current_ts: int | None = None) -> list[str]:
    current = current_ts or now_ts()
    pending = [task for task in tasks if task.is_pending and not _is_snoozed(task, current)]
    overdue = [task for task in pending if classify_task(task, current) == TaskBucket.OVERDUE]
    next_three = [
        task
        for task in pending
        if task.due_at is not None and current <= task.due_at <= current + 3 * 86400
    ]
    undated = [task for task in pending if classify_task(task, current) == TaskBucket.UNDATED]
    exams = [task for task in pending if is_possible_exam(task.name)]
    alerts: list[str] = []
    if overdue:
        alerts.append(
            f"Tienes {len(overdue)} tarea{'s' if len(overdue) != 1 else ''} vencida"
            f"{'s' if len(overdue) != 1 else ''}. Atender primero reduce pendientes acumulados."
        )
    if next_three:
        alerts.append(
            f"Tienes {len(next_three)} entrega{'s' if len(next_three) != 1 else ''} en los proximos 3 dias. "
            "Conviene distribuirlas desde hoy."
        )
    if undated:
        alerts.append(
            f"Hay {len(undated)} actividad{'es' if len(undated) != 1 else ''} sin fecha. "
            "Revisa Moodle para confirmar si requieren entrega."
        )
    if exams:
        nearest = min((task.due_at for task in exams if task.due_at), default=None)
        if nearest:
            days = max(0, int((nearest - current) / 86400))
            alerts.append(f"Posible evaluacion en {days} dias. Confirma indicaciones y reserva tiempo de estudio.")
        else:
            alerts.append("Posible evaluacion sin fecha registrada. Confirma indicaciones en Moodle.")
    if not alerts:
        alerts.append("No hay entregas urgentes. Puedes adelantar la proxima actividad.")
    return alerts[:4]


def _recommend(task: Task, course_pending_count: int, current_ts: int) -> TaskRecommendation:
    bucket = classify_task(task, current_ts)
    score = _date_score(task, current_ts)
    possible_exam = is_possible_exam(task.name)
    if possible_exam:
        score += 25
    if course_pending_count >= 4:
        score += 10
    level = "alta" if score >= 80 else "media" if score >= 40 else "planifica"
    reason = _primary_reason(task, bucket, current_ts, level)
    secondary: str | None = None
    if possible_exam:
        secondary = "Posible evaluacion detectada. Confirma fecha e indicaciones en Moodle."
    elif course_pending_count >= 4:
        secondary = f"Este curso tiene {course_pending_count} pendientes."
    return TaskRecommendation(
        task=task,
        score=score,
        level=level,
        primary_reason=reason,
        secondary_reason=secondary,
        suggested_action=_suggested_action(bucket, possible_exam),
        is_possible_exam=possible_exam,
    )


def _date_score(task: Task, current_ts: int) -> int:
    if not task.due_at:
        return 10
    diff = task.due_at - current_ts
    if diff < 0:
        return 100
    days = diff / 86400
    if days < 1:
        return 80
    if days <= 3:
        return 60
    if days <= 7:
        return 40
    if days <= 14:
        return 20
    return 0


def _bucket_rank(bucket: TaskBucket) -> int:
    return {
        TaskBucket.OVERDUE: 0,
        TaskBucket.UPCOMING: 1,
        TaskBucket.UNDATED: 2,
        TaskBucket.SUBMITTED: 3,
    }[bucket]


def _primary_reason(task: Task, bucket: TaskBucket, current_ts: int, level: str) -> str:
    prefix = f"Prioridad {level}"
    if bucket == TaskBucket.OVERDUE and task.due_at:
        days = max(1, int((current_ts - task.due_at) / 86400))
        return f"{prefix} porque vencio hace {days} dia{'s' if days != 1 else ''}."
    if bucket == TaskBucket.UPCOMING and task.due_at:
        days = max(0, int((task.due_at - current_ts) / 86400))
        if days == 0:
            return f"{prefix} porque vence hoy."
        if days == 1:
            return f"{prefix} porque vence manana."
        return f"{prefix} porque vence en {days} dias."
    if bucket == TaskBucket.UNDATED:
        return "Conviene planificarla porque no tiene fecha registrada."
    return f"Prioridad {level} por estado academico pendiente."


def _suggested_action(bucket: TaskBucket, possible_exam: bool) -> str:
    if possible_exam:
        return "Confirma fecha, modalidad e indicaciones en Moodle."
    if bucket == TaskBucket.UNDATED:
        return "Revisa Moodle y confirma si requiere entrega."
    return "Revisa instrucciones, prepara la entrega y sincroniza despues de enviar."


def _is_snoozed(task: Task, current_ts: int) -> bool:
    return bool(task.snoozed_until and task.snoozed_until > current_ts)
