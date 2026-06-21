"""Pruebas del adapter SQLite y su cache minimo."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from domain.modelos import Course, Task
from infrastructure.persistence import SQLiteTaskRepository


class SQLiteTaskRepositoryTests(unittest.TestCase):
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

    def test_sqlite_connection_uses_runtime_pragmas(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = SQLiteTaskRepository(Path(tmp) / "cache.db")

            self.assertEqual(db.conn.execute("PRAGMA foreign_keys").fetchone()[0], 1)
            self.assertEqual(db.conn.execute("PRAGMA busy_timeout").fetchone()[0], 5000)
            self.assertEqual(db.conn.execute("PRAGMA journal_mode").fetchone()[0], "wal")

            db.close()

    def test_changed_pending_tasks_reads_notification_state_in_bulk(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = SQLiteTaskRepository(Path(tmp) / "cache.db")
            tasks = [
                Task(10, 1, "IS", "Curso", "Tarea 1", None, None, "new"),
                Task(11, 1, "IS", "Curso", "Tarea 2", None, None, "new"),
                Task(12, 1, "IS", "Curso", "Tarea 3", None, None, "submitted"),
            ]
            db.mark_notified([tasks[0]])
            statements = []
            db.conn.set_trace_callback(statements.append)

            changed = db.changed_pending_tasks(tasks)

            db.conn.set_trace_callback(None)
            notification_selects = [
                statement
                for statement in statements
                if "FROM notification_state" in statement and "SELECT" in statement
            ]
            self.assertEqual([task.assignment_id for task in changed], [11])
            self.assertEqual(len(notification_selects), 1)
            db.close()

    def test_transaction_rolls_back_grouped_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = SQLiteTaskRepository(Path(tmp) / "cache.db")

            with self.assertRaises(RuntimeError):
                with db.transaction():
                    db.upsert_courses([Course(1, "IS", "Curso", True)])
                    raise RuntimeError("fail")

            self.assertEqual(db.count_courses(), 0)
            db.close()


if __name__ == "__main__":
    unittest.main()
