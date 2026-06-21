"""Caso de uso que sincroniza Moodle, cache local y cambios notificables."""

from __future__ import annotations

from uph_pendientes.application.puertos import CampusGateway, CredentialRepository, TaskRepository
from uph_pendientes.domain.modelos import Course, SyncResult, Task
from uph_pendientes.domain.tiempo import now_ts
from uph_pendientes.shared.errores import CampusError, MissingCredentialsError


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
            self.repository.upsert_courses(courses)
            tasks = self._load_tasks(token, {course.course_id: course for course in courses})
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
        for course_payload in self.campus.assignments(token):
            course_id = int(course_payload.get("id", 0))
            course = courses.get(course_id)
            if not course:
                continue
            for item in course_payload.get("assignments", []):
                assignment_id = int(item["id"])
                status_payload = self.campus.submission_status(token, assignment_id)
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

    def _submission_status(self, payload: dict) -> str:
        last_attempt = payload.get("lastattempt") if isinstance(payload, dict) else None
        submission = last_attempt.get("submission") if isinstance(last_attempt, dict) else None
        status = submission.get("status") if isinstance(submission, dict) else None
        return str(status or "new")
