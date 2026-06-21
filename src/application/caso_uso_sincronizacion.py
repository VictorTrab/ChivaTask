"""Caso de uso que sincroniza Moodle, cache local y cambios notificables."""

from __future__ import annotations

from application.puertos import CampusGateway, CredentialRepository, TaskRepository
from domain.modelos import Course, SyncResult, Task
from domain.tiempo import now_ts
from shared.errores import CampusError, MissingCredentialsError


class SyncUseCase:
    def __init__(
        self,
        repository: TaskRepository,
        credentials: CredentialRepository,
        campus: CampusGateway,
    ) -> None:
        self.repository = repository
        self.credentials = credentials
        self.campus = campus

    def execute(self) -> SyncResult:
        self.repository.set_state("last_sync_at", now_ts())
        try:
            token = self._valid_token()
            site = self.campus.site_info(token)
            user_id = int(site["userid"])
            courses = self._visible_courses(self.campus.courses(token, user_id))
            tasks = self._load_tasks(token, {course.course_id: course for course in courses})
            with self.repository.transaction():
                self.repository.upsert_courses(courses)
                changed = self.repository.changed_pending_tasks(tasks)
                self.repository.upsert_tasks(tasks)
                self.repository.set_state("last_successful_sync_at", now_ts())
                self.repository.set_state("last_error_code", "")
            return SyncResult(
                ok=True,
                pending_count=len([task for task in tasks if task.is_pending]),
                course_count=len(courses),
                changed_pending=changed,
            )
        except (CampusError, MissingCredentialsError) as exc:
            code = exc.code
            self.repository.set_state("last_error_code", code)
            return SyncResult(
                ok=False,
                pending_count=len(self.repository.pending_tasks()),
                course_count=self.repository.count_courses(),
                changed_pending=[],
                error_code=code,
            )

    def _valid_token(self) -> str:
        stored = self.credentials.load()
        if stored.token:
            try:
                self.campus.site_info(stored.token)
                return stored.token
            except CampusError as exc:
                if exc.code != "invalidtoken":
                    raise
                self.credentials.clear_token()
        token = self.campus.login(stored.username, stored.password)
        self.credentials.save_token(token)
        return token

    def _visible_courses(self, raw_courses: list[dict]) -> list[Course]:
        return [
            Course(
                course_id=int(course["id"]),
                shortname=str(course.get("shortname") or ""),
                fullname=str(course.get("fullname") or ""),
                visible=bool(int(course.get("visible", 1))),
            )
            for course in raw_courses
            if bool(int(course.get("visible", 1)))
        ]

    def _load_tasks(self, token: str, courses: dict[int, Course]) -> list[Task]:
        tasks: list[Task] = []
        assignments: list[tuple[Course, dict]] = []
        for course_payload in self.campus.assignments(token):
            course_id = int(course_payload.get("id", 0))
            course = courses.get(course_id)
            if not course:
                continue
            for item in course_payload.get("assignments", []):
                assignments.append((course, item))
        status_by_assignment = self._submission_statuses(token, [int(item["id"]) for _course, item in assignments])
        for course, item in assignments:
            assignment_id = int(item["id"])
            status_payload = status_by_assignment.get(assignment_id, {})
            due_at = int(item["duedate"]) if item.get("duedate") else None
            tasks.append(
                Task(
                    assignment_id=assignment_id,
                    course_id=course.course_id,
                    course_shortname=course.shortname,
                    course_fullname=course.fullname,
                    name=str(item.get("name") or "Tarea sin titulo"),
                    due_at=due_at,
                    url=item.get("url"),
                    submission_status=self._submission_status(status_payload),
                )
            )
        return tasks

    def _submission_statuses(self, token: str, assignment_ids: list[int]) -> dict[int, dict]:
        if hasattr(self.campus, "submission_statuses"):
            return self.campus.submission_statuses(token, assignment_ids)
        return {
            assignment_id: self.campus.submission_status(token, assignment_id)
            for assignment_id in assignment_ids
        }

    def _submission_status(self, payload: dict) -> str:
        last_attempt = payload.get("lastattempt") if isinstance(payload, dict) else None
        submission = last_attempt.get("submission") if isinstance(last_attempt, dict) else None
        status = submission.get("status") if isinstance(submission, dict) else None
        return str(status or "new")
