"""Consultas de lectura para que la UI no conozca la persistencia."""

from __future__ import annotations

from datetime import datetime

from uph_pendientes.application.puertos import TaskRepository
from uph_pendientes.domain.modelos import Task, TaskBucket
from uph_pendientes.domain.politica_tareas import classify_task, sort_pending
from uph_pendientes.domain.tiempo import now_ts


class TaskQueries:
    def __init__(self, repository: TaskRepository) -> None:
        self.repository = repository

    def pending_sorted(self) -> list[Task]:
        return sort_pending(self.repository.pending_tasks())

    def next_deadline(self) -> Task | None:
        dated = [task for task in self.pending_sorted() if task.due_at is not None and task.due_at >= now_ts()]
        return dated[0] if dated else None

    def overdue_tasks(self) -> list[Task]:
        return [task for task in self.pending_sorted() if classify_task(task) == TaskBucket.OVERDUE]

    def undated_tasks(self) -> list[Task]:
        return [task for task in self.pending_sorted() if classify_task(task) == TaskBucket.UNDATED]

    def tasks_due_within(self, days: int) -> list[Task]:
        current = now_ts()
        limit = current + days * 86400
        return [
            task
            for task in self.pending_sorted()
            if task.due_at is not None and current <= task.due_at <= limit
        ]

    def urgent_tasks(self) -> list[Task]:
        ids = {task.assignment_id for task in self.overdue_tasks()}
        urgent = self.overdue_tasks()
        for task in self.tasks_due_within(3):
            if task.assignment_id not in ids:
                urgent.append(task)
        return sort_pending(urgent)

    def pending_filtered(
        self,
        bucket: TaskBucket | str | None = None,
        search: str = "",
        sort_by: str = "fecha",
        snoozed_only: bool = False,
    ) -> list[Task]:
        tasks = self.pending_sorted()
        query = search.strip().lower()
        if snoozed_only:
            tasks = [task for task in tasks if task.snoozed_until]
        elif bucket:
            wanted = bucket if isinstance(bucket, TaskBucket) else TaskBucket(bucket)
            tasks = [task for task in tasks if classify_task(task) == wanted]
        if query:
            tasks = [
                task
                for task in tasks
                if query in task.name.lower()
                or query in task.course_shortname.lower()
                or query in task.course_fullname.lower()
            ]
        if sort_by == "curso":
            return sorted(tasks, key=lambda task: (task.course_shortname, task.name))
        if sort_by == "estado":
            return sorted(tasks, key=lambda task: (classify_task(task).value, task.due_at or 9_999_999_999, task.name))
        return sort_pending(tasks)

    def task_counts(self) -> dict[str, int]:
        tasks = self.repository.pending_tasks()
        counts = {
            "todas": len(tasks),
            "vencidas": 0,
            "sin_entrega": 0,
            "sin_fecha": 0,
            "pospuestas": 0,
        }
        for task in tasks:
            bucket = classify_task(task)
            if bucket == TaskBucket.OVERDUE:
                counts["vencidas"] += 1
            elif bucket == TaskBucket.UPCOMING:
                counts["sin_entrega"] += 1
            elif bucket == TaskBucket.UNDATED:
                counts["sin_fecha"] += 1
            if task.snoozed_until:
                counts["pospuestas"] += 1
        return counts

    def grouped_by_course(self, tasks: list[Task]) -> list[tuple[str, list[Task]]]:
        grouped: dict[str, list[Task]] = {}
        for task in tasks:
            grouped.setdefault(task.course_shortname or task.course_fullname, []).append(task)
        return [(course, grouped[course]) for course in sorted(grouped)]

    def course_summaries(self) -> list[dict[str, object]]:
        pending = self.repository.pending_tasks()
        all_tasks = self.repository.all_tasks()
        by_course: dict[int, dict[str, object]] = {}
        for task in all_tasks:
            summary = by_course.setdefault(
                task.course_id,
                {
                    "course_id": task.course_id,
                    "shortname": task.course_shortname,
                    "fullname": task.course_fullname,
                    "pending": 0,
                    "submitted": 0,
                    "total": 0,
                    "tasks": [],
                },
            )
            summary["total"] = int(summary["total"]) + 1
            if task.is_pending:
                summary["tasks"].append(task)
            else:
                summary["submitted"] = int(summary["submitted"]) + 1
        pending_by_id = {task.assignment_id for task in pending}
        for summary in by_course.values():
            tasks = [task for task in summary["tasks"] if task.assignment_id in pending_by_id]
            summary["tasks"] = sort_pending(tasks)
            summary["pending"] = len(tasks)
        return sorted(by_course.values(), key=lambda item: str(item["shortname"]))

    def global_progress(self) -> dict[str, int]:
        tasks = self.repository.all_tasks()
        total = len(tasks)
        submitted = len([task for task in tasks if not task.is_pending])
        pending = len([task for task in tasks if task.is_pending])
        overdue = len([task for task in tasks if classify_task(task) == TaskBucket.OVERDUE])
        percent = int((submitted / total) * 100) if total else 0
        return {
            "total": total,
            "submitted": submitted,
            "pending": pending,
            "overdue": overdue,
            "percent": percent,
        }

    def calendar_marks(self, year: int, month: int) -> dict[int, str]:
        marks: dict[int, str] = {}
        for task in self.pending_sorted():
            if not task.due_at:
                continue
            due = datetime.fromtimestamp(task.due_at)
            if due.year != year or due.month != month:
                continue
            bucket = classify_task(task)
            if bucket == TaskBucket.OVERDUE:
                marks[due.day] = "overdue"
            elif marks.get(due.day) != "overdue":
                marks[due.day] = "pending"
        return marks

    def course_count(self) -> int:
        return self.repository.count_courses()

    def last_successful_sync(self) -> str | None:
        return self.repository.get_state("last_successful_sync_at")
