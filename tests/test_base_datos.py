"""Pruebas del adapter SQLite y su cache minimo."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from uph_pendientes.domain.modelos import Course, Task
from uph_pendientes.infrastructure.persistence import SQLiteTaskRepository


class CacheDBTests(unittest.TestCase):
    def test_cache_stores_minimum_task_data_without_secret_columns(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = SQLiteTaskRepository(Path(tmp) / "cache.db")
            db.upsert_courses([Course(1, "IS", "Curso", True)])
            assignment = Task(10, 1, "IS", "Curso", "Tarea", None, None, "new")
            db.upsert_tasks([assignment])
            self.assertEqual(len(db.pending_tasks()), 1)

            columns = {
                row[1]
                for row in db.conn.execute("PRAGMA table_info(tasks)").fetchall()
            }
            self.assertNotIn("password", columns)
            self.assertNotIn("token", columns)
            db.close()

    def test_changed_pending_ignores_snoozed_tasks(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = SQLiteTaskRepository(Path(tmp) / "cache.db")
            assignment = Task(10, 1, "IS", "Curso", "Tarea", None, None, "new")
            db.snooze(10, 9_999_999_999)
            self.assertEqual(db.changed_pending_tasks([assignment]), [])
            db.close()

    def test_clear_academic_cache_preserves_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = SQLiteTaskRepository(Path(tmp) / "cache.db")
            db.set_setting("sync_interval_seconds", 21600)
            db.upsert_courses([Course(1, "IS", "Curso", True)])
            db.upsert_tasks([Task(10, 1, "IS", "Curso", "Tarea", None, None, "new")])
            db.snooze(10, 9_999_999_999)

            db.clear_academic_cache()

            self.assertEqual(db.pending_tasks(), [])
            self.assertEqual(db.count_courses(), 0)
            self.assertEqual(db.get_setting("sync_interval_seconds"), "21600")
            db.close()


if __name__ == "__main__":
    unittest.main()
