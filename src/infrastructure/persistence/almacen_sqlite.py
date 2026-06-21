"""Adapter SQLite que guarda cache local sin secretos."""

from __future__ import annotations

from contextlib import contextmanager
import sqlite3
from collections.abc import Iterator
from pathlib import Path

from domain.modelos import Course, Task
from domain.tiempo import now_ts
from shared.ajustes import db_path

from .esquema import LEGACY_MIGRATION_SQL, SCHEMA_SQL


class SQLiteTaskRepository:
    def __init__(self, path: Path | str | None = None) -> None:
        self.path = path or db_path()
        if self.path != ":memory:":
            self.path = Path(self.path)
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self._transaction_depth = 0
        self.wal_enabled = False
        self.synchronous_normal_enabled = False
        self._configure_connection()
        self.migrate()

    def close(self) -> None:
        self.conn.close()

    def _configure_connection(self) -> None:
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA busy_timeout = 5000")
        if self.path != ":memory:":
            try:
                self.conn.execute("PRAGMA journal_mode = WAL")
                self.wal_enabled = True
            except sqlite3.OperationalError:
                self.wal_enabled = False
        try:
            self.conn.execute("PRAGMA synchronous = NORMAL")
            self.synchronous_normal_enabled = True
        except sqlite3.OperationalError:
            self.synchronous_normal_enabled = False

    @contextmanager
    def transaction(self) -> Iterator[None]:
        outermost = self._transaction_depth == 0
        self._transaction_depth += 1
        try:
            if outermost:
                self.conn.execute("BEGIN")
            yield
            if outermost:
                self.conn.commit()
        except Exception:
            if outermost:
                self.conn.rollback()
            raise
        finally:
            self._transaction_depth -= 1

    def _commit(self) -> None:
        if self._transaction_depth == 0:
            self.conn.commit()

    def migrate(self) -> None:
        self.conn.executescript(SCHEMA_SQL)
        try:
            self.conn.executescript(LEGACY_MIGRATION_SQL)
        except sqlite3.OperationalError:
            pass
        self._commit()

    def upsert_courses(self, courses: list[Course]) -> None:
        seen = now_ts()
        self.conn.executemany(
            """
            INSERT INTO courses (course_id, shortname, fullname, visible, last_seen_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(course_id) DO UPDATE SET
                shortname=excluded.shortname,
                fullname=excluded.fullname,
                visible=excluded.visible,
                last_seen_at=excluded.last_seen_at
            """,
            [(c.course_id, c.shortname, c.fullname, int(c.visible), seen) for c in courses],
        )
        self._commit()

    def upsert_tasks(self, tasks: list[Task]) -> None:
        seen = now_ts()
        self.conn.executemany(
            """
            INSERT INTO tasks (
                assignment_id, course_id, course_shortname, course_fullname,
                name, due_at, url, submission_status, content_hash, last_seen_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(assignment_id) DO UPDATE SET
                course_id=excluded.course_id,
                course_shortname=excluded.course_shortname,
                course_fullname=excluded.course_fullname,
                name=excluded.name,
                due_at=excluded.due_at,
                url=excluded.url,
                submission_status=excluded.submission_status,
                content_hash=excluded.content_hash,
                last_seen_at=excluded.last_seen_at
            """,
            [
                (
                    task.assignment_id,
                    task.course_id,
                    task.course_shortname,
                    task.course_fullname,
                    task.name,
                    task.due_at,
                    task.url,
                    task.submission_status,
                    task.stable_hash,
                    seen,
                )
                for task in tasks
            ],
        )
        self._commit()

    def pending_tasks(self) -> list[Task]:
        rows = self.conn.execute(
            """
            SELECT t.*, n.snoozed_until
            FROM tasks t
            LEFT JOIN notification_state n ON n.assignment_id = t.assignment_id
            WHERE t.submission_status IN ('new', 'reopened', 'draft')
            """
        ).fetchall()
        return [self._task_from_row(row) for row in rows]

    def all_tasks(self) -> list[Task]:
        rows = self.conn.execute(
            """
            SELECT t.*, n.snoozed_until
            FROM tasks t
            LEFT JOIN notification_state n ON n.assignment_id = t.assignment_id
            """
        ).fetchall()
        return [self._task_from_row(row) for row in rows]

    def count_courses(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) AS c FROM courses WHERE visible = 1").fetchone()
        return int(row["c"])

    def changed_pending_tasks(self, tasks: list[Task]) -> list[Task]:
        changed: list[Task] = []
        current = now_ts()
        pending_tasks = [task for task in tasks if task.is_pending]
        if not pending_tasks:
            return []
        placeholders = ",".join("?" for _ in pending_tasks)
        rows = self.conn.execute(
            f"""
            SELECT assignment_id, last_notified_hash, snoozed_until
            FROM notification_state
            WHERE assignment_id IN ({placeholders})
            """,
            [task.assignment_id for task in pending_tasks],
        ).fetchall()
        state_by_assignment = {int(row["assignment_id"]): row for row in rows}
        for task in pending_tasks:
            row = state_by_assignment.get(task.assignment_id)
            last_hash = row["last_notified_hash"] if row else None
            snoozed_until = row["snoozed_until"] if row else None
            if snoozed_until and int(snoozed_until) > current:
                continue
            if last_hash != task.stable_hash:
                changed.append(
                    Task(
                        assignment_id=task.assignment_id,
                        course_id=task.course_id,
                        course_shortname=task.course_shortname,
                        course_fullname=task.course_fullname,
                        name=task.name,
                        due_at=task.due_at,
                        url=task.url,
                        submission_status=task.submission_status,
                        content_hash=task.stable_hash,
                        snoozed_until=snoozed_until,
                    )
                )
        return changed

    def mark_notified(self, tasks: list[Task]) -> None:
        self.conn.executemany(
            """
            INSERT INTO notification_state (assignment_id, last_notified_hash, snoozed_until)
            VALUES (?, ?, NULL)
            ON CONFLICT(assignment_id) DO UPDATE SET
                last_notified_hash=excluded.last_notified_hash
            """,
            [(task.assignment_id, task.stable_hash) for task in tasks],
        )
        self._commit()

    def snooze(self, assignment_id: int, until_ts: int) -> None:
        self.conn.execute(
            """
            INSERT INTO notification_state (assignment_id, snoozed_until)
            VALUES (?, ?)
            ON CONFLICT(assignment_id) DO UPDATE SET snoozed_until=excluded.snoozed_until
            """,
            (assignment_id, until_ts),
        )
        self._commit()

    def clear_academic_cache(self) -> None:
        """Elimina datos academicos cacheados sin tocar ajustes locales."""
        self.conn.execute("DELETE FROM notification_state")
        self.conn.execute("DELETE FROM tasks")
        self.conn.execute("DELETE FROM courses")
        self.conn.execute("DELETE FROM app_state")
        self._commit()

    def clear_all_local_cache(self) -> None:
        """Elimina cache academica y conserva solo preferencias de app."""
        self.clear_academic_cache()

    def set_state(self, key: str, value: str | int | None) -> None:
        self.conn.execute(
            """
            INSERT INTO app_state (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value
            """,
            (key, None if value is None else str(value)),
        )
        self._commit()

    def get_state(self, key: str) -> str | None:
        row = self.conn.execute("SELECT value FROM app_state WHERE key = ?", (key,)).fetchone()
        return None if row is None else row["value"]

    def set_setting(self, key: str, value: str | int | bool) -> None:
        normalized = "1" if value is True else "0" if value is False else str(value)
        self.conn.execute(
            """
            INSERT INTO settings (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value
            """,
            (key, normalized),
        )
        self._commit()

    def get_setting(self, key: str, default: str | None = None) -> str | None:
        row = self.conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return default if row is None else row["value"]

    def _task_from_row(self, row: sqlite3.Row) -> Task:
        return Task(
            assignment_id=int(row["assignment_id"]),
            course_id=int(row["course_id"]),
            course_shortname=str(row["course_shortname"]),
            course_fullname=str(row["course_fullname"]),
            name=str(row["name"]),
            due_at=row["due_at"],
            url=row["url"],
            submission_status=str(row["submission_status"]),
            content_hash=str(row["content_hash"]),
            snoozed_until=row["snoozed_until"],
        )
