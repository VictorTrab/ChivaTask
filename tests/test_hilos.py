"""Prueba que cada hilo use su propia conexion SQLite."""

import tempfile
import threading
import unittest
from pathlib import Path

from domain.modelos import Course
from infrastructure.persistence import SQLiteTaskRepository


class ThreadingTests(unittest.TestCase):
    def test_worker_uses_its_own_sqlite_connection_for_same_cache_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cache.db"
            main_db = SQLiteTaskRepository(path)
            errors: list[BaseException] = []

            def worker() -> None:
                try:
                    worker_db = SQLiteTaskRepository(path)
                    worker_db.set_state("last_sync_at", 123)
                    worker_db.upsert_courses([Course(1, "IS", "Curso", True)])
                    worker_db.close()
                except BaseException as exc:
                    errors.append(exc)

            thread = threading.Thread(target=worker)
            thread.start()
            thread.join(timeout=5)

            self.assertFalse(errors)
            self.assertEqual(main_db.get_state("last_sync_at"), "123")
            self.assertEqual(main_db.count_courses(), 1)
            main_db.close()


if __name__ == "__main__":
    unittest.main()
