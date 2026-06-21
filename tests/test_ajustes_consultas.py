"""Pruebas de settings y consultas usadas por la UI."""

import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from application.consultas_tareas import TaskQueries
from application.servicio_ajustes import SettingsService
from domain.modelos import Course, Task, TaskBucket
from domain.tiempo import now_ts
from infrastructure.persistence import SQLiteTaskRepository


class FakeAutostart:
    def __init__(self) -> None:
        self.value = False

    def enabled(self) -> bool:
        return self.value

    def set_enabled(self, enabled: bool) -> None:
        self.value = enabled


class SettingsAndQueriesTests(unittest.TestCase):
    def test_settings_validate_supported_values(self):
        repo = SQLiteTaskRepository(":memory:")
        settings = SettingsService(repo, FakeAutostart())

        settings.set_sync_interval_seconds(3600)
        settings.set_notification_mode("resumen_diario")
        settings.set_ui_density("compacta")
        settings.set_visual_mode("oscuro")
        settings.set_onboarding_completed(True)

        self.assertEqual(settings.sync_interval_seconds(), 3600)
        self.assertEqual(settings.notification_mode(), "resumen_diario")
        self.assertEqual(settings.ui_density(), "compacta")
        self.assertEqual(settings.visual_mode(), "oscuro")
        self.assertTrue(settings.onboarding_completed())

        settings.set_sync_interval_seconds(123)
        settings.set_notification_mode("ruidoso")
        settings.set_ui_density("gigante")
        settings.set_visual_mode("sepia")

        self.assertEqual(settings.sync_interval_seconds(), 21600)
        self.assertEqual(settings.notification_mode(), "solo_nuevos")
        self.assertEqual(settings.ui_density(), "comoda")
        self.assertEqual(settings.visual_mode(), "claro")
        repo.close()

    def test_settings_use_injected_autostart_manager(self):
        repo = SQLiteTaskRepository(":memory:")
        autostart = FakeAutostart()
        settings = SettingsService(repo, autostart)

        self.assertFalse(settings.autostart_enabled())
        settings.set_autostart(True)
        self.assertTrue(settings.autostart_enabled())
        repo.close()

    def test_task_queries_filter_sort_and_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = SQLiteTaskRepository(Path(tmp) / "cache.db")
            repo.upsert_courses(
                [
                    Course(1, "IS", "Ingenieria", True),
                    Course(2, "MAT", "Matematica", True),
                ]
            )
            repo.upsert_tasks(
                [
                    Task(1, 1, "IS", "Ingenieria", "Proyecto", 10, None, "new"),
                    Task(2, 2, "MAT", "Matematica", "Guia", None, None, "new"),
                    Task(3, 1, "IS", "Ingenieria", "Entregada", 20, None, "submitted"),
                ]
            )
            repo.snooze(2, 9_999_999_999)
            queries = TaskQueries(repo)

            self.assertEqual(queries.task_counts()["todas"], 2)
            self.assertEqual(queries.task_counts()["sin_fecha"], 1)
            self.assertEqual(queries.task_counts()["pospuestas"], 1)
            self.assertEqual(len(queries.pending_filtered(TaskBucket.UNDATED)), 1)
            self.assertEqual(queries.pending_filtered(search="proyecto")[0].assignment_id, 1)
            self.assertEqual(queries.pending_filtered(snoozed_only=True)[0].assignment_id, 2)
            self.assertEqual(len(queries.course_summaries()), 2)
            repo.close()

    def test_dashboard_queries_deadlines_progress_and_calendar(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = SQLiteTaskRepository(Path(tmp) / "cache.db")
            try:
                current = now_ts()
                repo.upsert_courses([Course(1, "IS", "Ingenieria", True)])
                repo.upsert_tasks(
                    [
                        Task(1, 1, "IS", "Ingenieria", "Vencida", current - 86400, None, "new"),
                        Task(2, 1, "IS", "Ingenieria", "Proxima", current + 86400, None, "new"),
                        Task(3, 1, "IS", "Ingenieria", "Sin fecha", None, None, "new"),
                        Task(4, 1, "IS", "Ingenieria", "Lista", current + 172800, None, "submitted"),
                    ]
                )
                queries = TaskQueries(repo)
                next_task = queries.next_deadline()
                progress = queries.global_progress()

                self.assertIsNotNone(next_task)
                self.assertEqual(next_task.assignment_id, 2)
                self.assertEqual(len(queries.overdue_tasks()), 1)
                self.assertEqual(len(queries.tasks_due_within(7)), 1)
                self.assertEqual(len(queries.undated_tasks()), 1)
                self.assertEqual(progress["total"], 4)
                self.assertEqual(progress["submitted"], 1)
                self.assertEqual(progress["percent"], 25)

                month = datetime.fromtimestamp(current + 86400)
                marks = queries.calendar_marks(month.year, month.month)
                self.assertIn(month.day, marks)
            finally:
                repo.close()


if __name__ == "__main__":
    unittest.main()
